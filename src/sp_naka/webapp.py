"""Lokale Browseroberfläche für Konfiguration, Läufe und Feedback."""

from __future__ import annotations

import csv
import html
import json
import os
import secrets
import threading
from collections import Counter
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from .csv_io import read_rows
from .errors import AnalysisError
from .pipeline import run_analysis


MAX_POST_BYTES = 1024 * 1024


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv_replace(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(
            {
                key: "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value
                for key, value in row.items()
            }
            for row in rows
        )
    temporary.replace(path)


def _safe_run_dir(output_root: Path, run_id: str) -> Path | None:
    if not run_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for char in run_id):
        return None
    root = output_root.resolve()
    candidate = (root / run_id).resolve()
    return candidate if candidate.parent == root and candidate.is_dir() else None


class WebApplication:
    def __init__(self, project_root: Path) -> None:
        self.root = project_root.resolve()
        self.local_root = self.root / "data" / "local"
        self.web_config_path = self.local_root / "web_config.json"
        self.local_parameters_path = self.local_root / "analysis_parameters.json"
        self.customers_path = self.local_root / "master_data" / "accepted_negative_customers.csv"
        self.feedback_path = self.local_root / "feedback" / "performance_feedback.csv"
        self.rules_path = self.root / "config" / "rules.json"
        self.csrf_token = secrets.token_urlsafe(32)
        self._state_lock = threading.Lock()
        self._running: dict[str, object] = {"active": False, "message": "Bereit"}
        self._ensure_local_files()
        threading.Thread(target=self._scheduler_loop, daemon=True).start()

    def _defaults(self) -> dict[str, object]:
        return {
            "standard_data_dir": str(self.local_root / "CSV_Original"),
            "training_data_dir": str(self.local_root / "CSV_TestDataSet"),
            "reference_data_dir": str(self.local_root / "CSV_Original"),
            "output_dir": str(self.root / "output" / "runs"),
            "schedule_enabled": False,
            "schedule_time": "02:00",
            "schedule_process": "standard",
            "last_scheduled_date": "",
        }

    def _ensure_local_files(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        if not self.web_config_path.is_file():
            self._save_config(self._defaults())
        bundled_parameters = json.loads(
            (self.root / "config" / "analysis_parameters.json").read_text(encoding="utf-8")
        )
        local_parameters: dict[str, object] = {}
        if self.local_parameters_path.is_file():
            try:
                local_parameters = json.loads(self.local_parameters_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                local_parameters = {}
        if local_parameters.get("version") != bundled_parameters.get("version"):
            local_performance = local_parameters.get("performance", {})
            for key in (
                "minimum_peer_group_size", "robust_z_warning_threshold", "robust_z_threshold"
            ):
                if key in local_performance:
                    bundled_parameters["performance"][key] = local_performance[key]
            old_levels = local_parameters.get("raw_material_quantity_check", {}).get("levels")
            if isinstance(old_levels, list) and len(old_levels) == 3:
                bundled_parameters["raw_material_quantity_check"]["levels"] = old_levels
            self.local_parameters_path.write_text(
                json.dumps(bundled_parameters, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        if not self.customers_path.is_file():
            _write_csv_replace(
                self.customers_path,
                ["customer_key", "active_from", "active_until", "reason", "approved_by", "approved_at"],
                [],
            )

    def config(self) -> dict[str, object]:
        try:
            loaded = json.loads(self.web_config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            loaded = {}
        merged = {**self._defaults(), **loaded}
        if os.environ.get("SP_NAKA_CONTAINER") == "1":
            defaults = self._defaults()
            for field in (
                "standard_data_dir", "training_data_dir", "reference_data_dir", "output_dir"
            ):
                if not Path(str(merged[field])).exists():
                    merged[field] = defaults[field]
        return merged

    def parameters(self) -> dict[str, object]:
        return json.loads(self.local_parameters_path.read_text(encoding="utf-8"))

    def _save_config(self, config: dict[str, object]) -> None:
        self.web_config_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.web_config_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.web_config_path)

    def _save_parameters(self, parameters: dict[str, object]) -> None:
        temporary = self.local_parameters_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(parameters, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.local_parameters_path)

    def output_root(self) -> Path:
        return Path(str(self.config()["output_dir"])).expanduser().resolve()

    def run_history(self, limit: int = 10) -> list[dict[str, object]]:
        root = self.output_root()
        if not root.is_dir():
            return []
        runs = []
        for manifest_path in root.glob("*/run_manifest.json"):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            runs.append({"dir": manifest_path.parent, "manifest": manifest})
        runs.sort(
            key=lambda item: str(item["manifest"].get("completed_at_utc", "")),
            reverse=True,
        )
        return runs[:limit]

    def run_state(self) -> dict[str, object]:
        with self._state_lock:
            return dict(self._running)

    def start_process(self, process: str, scheduled: bool = False) -> tuple[bool, str]:
        if process not in {"standard", "training"}:
            return False, "Unbekannter Prozess."
        with self._state_lock:
            if self._running.get("active"):
                return False, "Es läuft bereits eine Analyse."
            self._running = {
                "active": True,
                "process": process,
                "started": datetime.now().isoformat(timespec="seconds"),
                "message": "Analyse läuft",
            }
        threading.Thread(
            target=self._run_worker, args=(process, scheduled), daemon=True
        ).start()
        return True, "Analyse wurde gestartet."

    def _run_worker(self, process: str, scheduled: bool) -> None:
        config = self.config()
        data_key = "standard_data_dir" if process == "standard" else "training_data_dir"
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        run_id = f"web-{process}-{timestamp}"
        try:
            result = run_analysis(
                Path(str(config[data_key])),
                Path(str(config["output_dir"])),
                self.rules_path,
                run_id=run_id,
                reference_data_dir=Path(str(config["reference_data_dir"])),
                analysis_parameters_path=self.local_parameters_path,
                accepted_customers_path=self.customers_path,
            )
            state = {
                "active": False,
                "process": process,
                "completed": datetime.now().isoformat(timespec="seconds"),
                "message": f"Erfolgreich abgeschlossen: {result.name}",
                "run_id": result.name,
            }
            if scheduled:
                config["last_scheduled_date"] = datetime.now().date().isoformat()
                self._save_config(config)
        except Exception as exc:
            state = {
                "active": False,
                "process": process,
                "completed": datetime.now().isoformat(timespec="seconds"),
                "message": f"Fehler: {exc}",
            }
        with self._state_lock:
            self._running = state

    def _scheduler_loop(self) -> None:
        import time

        while True:
            time.sleep(30)
            config = self.config()
            if not config.get("schedule_enabled"):
                continue
            now = datetime.now()
            if (
                now.strftime("%H:%M") == str(config.get("schedule_time"))
                and config.get("last_scheduled_date") != now.date().isoformat()
            ):
                self.start_process(str(config.get("schedule_process", "standard")), scheduled=True)

    def save_settings(self, form: dict[str, list[str]]) -> None:
        config = self.config()
        for field in ("standard_data_dir", "training_data_dir", "reference_data_dir", "output_dir"):
            value = form.get(field, [""])[0].strip()
            if not value:
                raise AnalysisError(f"{field} darf nicht leer sein.")
            config[field] = str(Path(value).expanduser().resolve())
        for field in ("standard_data_dir", "training_data_dir", "reference_data_dir"):
            if not Path(str(config[field])).is_dir():
                raise AnalysisError(f"Datenverzeichnis nicht gefunden: {config[field]}")
        schedule_time = form.get("schedule_time", ["02:00"])[0]
        try:
            datetime.strptime(schedule_time, "%H:%M")
        except ValueError as exc:
            raise AnalysisError("Planzeit muss HH:MM entsprechen.") from exc
        config["schedule_enabled"] = form.get("schedule_enabled", [""])[0] == "on"
        config["schedule_time"] = schedule_time
        process = form.get("schedule_process", ["standard"])[0]
        if process not in {"standard", "training"}:
            raise AnalysisError("Ungültiger geplanter Prozess.")
        config["schedule_process"] = process

        parameters = self.parameters()
        performance = parameters["performance"]
        performance["minimum_peer_group_size"] = int(form.get("minimum_peer_group_size", ["5"])[0])
        performance["robust_z_warning_threshold"] = float(form.get("robust_z_warning_threshold", ["2.0"])[0])
        performance["robust_z_threshold"] = float(form.get("robust_z_threshold", ["3.5"])[0])
        if (
            performance["minimum_peer_group_size"] < 3
            or performance["robust_z_warning_threshold"] <= 0
            or performance["robust_z_threshold"] <= performance["robust_z_warning_threshold"]
        ):
            raise AnalysisError("Peer-Parameter sind nicht plausibel abgestuft.")
        levels = parameters["raw_material_quantity_check"]["levels"]
        for index, name in enumerate(("raw_hint", "raw_review", "raw_critical")):
            levels[index]["minimum_ratio"] = float(form.get(name, [str(levels[index]["minimum_ratio"])])[0])
        raw_values = [float(level["minimum_ratio"]) for level in levels]
        if raw_values[0] <= 1 or raw_values != sorted(set(raw_values)):
            raise AnalysisError("Rohwarenfaktoren müssen größer 1 und streng aufsteigend sein.")

        keys = [value.strip() for value in form.get("accepted_customers", [""])[0].replace(",", "\n").splitlines() if value.strip()]
        existing = {row["customer_key"]: row for row in _read_csv(self.customers_path)}
        rows = []
        for key in dict.fromkeys(keys):
            if any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789|-_." for char in key):
                raise AnalysisError(f"Ungültige Kundennummer: {key}")
            rows.append(existing.get(key, {
                "customer_key": key,
                "active_from": "",
                "active_until": "",
                "reason": "Auslastungskunde",
                "approved_by": "",
                "approved_at": "",
            }))
        self._save_config(config)
        self._save_parameters(parameters)
        _write_csv_replace(
            self.customers_path,
            ["customer_key", "active_from", "active_until", "reason", "approved_by", "approved_at"],
            rows,
        )

    def save_feedback(self, form: dict[str, list[str]]) -> None:
        fields = [
            "run_id", "order_number", "decision", "confirmed_reason_codes",
            "changed_reason", "correction_required", "comment", "reviewed_by", "reviewed_at",
        ]
        run_id = form.get("run_id", [""])[0].strip()
        order = form.get("order_number", [""])[0].strip()
        if _safe_run_dir(self.output_root(), run_id) is None or not order:
            raise AnalysisError("Ungültiger Feedbackbezug.")
        decision = form.get("decision", [""])[0]
        allowed = {"CONFIRMED", "CHANGED", "NO_CORRECTION", "DATA_ERROR", "RULE_CHANGE_NEEDED"}
        if decision not in allowed:
            raise AnalysisError("Bitte eine gültige Feedbackentscheidung wählen.")
        rows = _read_csv(self.feedback_path)
        record = {
            "run_id": run_id,
            "order_number": order,
            "decision": decision,
            "confirmed_reason_codes": form.get("confirmed_reason_codes", [""])[0].strip(),
            "changed_reason": form.get("changed_reason", [""])[0].strip(),
            "correction_required": "YES" if form.get("correction_required", [""])[0] == "on" else "NO",
            "comment": form.get("comment", [""])[0].strip(),
            "reviewed_by": form.get("reviewed_by", [""])[0].strip(),
            "reviewed_at": datetime.now().isoformat(timespec="seconds"),
        }
        rows = [row for row in rows if not (row.get("run_id") == run_id and row.get("order_number") == order)]
        rows.append(record)
        _write_csv_replace(self.feedback_path, fields, rows)


def _layout(title: str, active: str, content: str, state: dict[str, object]) -> str:
    menus = [
        ("dashboard", "/", "Übersicht"),
        ("runs", "/runs", "Laufhistorie"),
        ("orders", "/orders", "Auftragsbewertung"),
        ("review", "/review", "Prüfung & Feedback"),
        ("parameters", "/parameters", "Parametrierung"),
    ]
    nav = "".join(
        f'<a class="nav-item {"active" if key == active else ""}" href="{url}">{html.escape(label)}</a>'
        for key, url, label in menus
    )
    run_class = "running" if state.get("active") else "ready"
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · SP_Naka</title><link rel="stylesheet" href="/static/style.css"></head>
<body><header class="topbar"><div class="brand"><span class="brand-mark">SP</span><strong>NAKA</strong></div>
<div class="top-title">Nachkalkulation & Auftragsanalyse</div><div class="run-state {run_class}">{html.escape(str(state.get("message", "Bereit")))}</div></header>
<div class="workspace"><aside class="sidebar"><div class="menu-title">PROGRAMME</div>{nav}
<div class="sidebar-note">Lokale Analyse<br>Quelldaten nur lesend</div></aside>
<main><div class="page-head"><h1>{html.escape(title)}</h1><span>{datetime.now().strftime('%d.%m.%Y %H:%M')}</span></div>{content}</main></div></body></html>"""


def _card(title: str, body: str, cls: str = "") -> str:
    return f'<section class="card {cls}"><div class="card-title">{html.escape(title)}</div><div class="card-body">{body}</div></section>'


def _formatted_number(value: str, kind: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    if kind == "money":
        rendered = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return rendered + " EUR"
    if kind == "ratio":
        return f"{number * 100:.2f}".replace(".", ",") + " %"
    return f"{number:.2f}".replace(".", ",")


def _latest_run(app: WebApplication, requested: str = "") -> tuple[str, Path | None]:
    if requested:
        return requested, _safe_run_dir(app.output_root(), requested)
    history = app.run_history(1)
    return (history[0]["dir"].name, history[0]["dir"]) if history else ("", None)


def _dashboard(app: WebApplication) -> str:
    history = app.run_history(10)
    latest = history[0] if history else None
    manifest = latest["manifest"] if latest else {}
    controls = manifest.get("control_totals", {})
    perf = manifest.get("performance_analysis") or {}
    cards = '<div class="metrics">'
    for label, value in (
        ("Läufe vorhanden", len(app.run_history(1000))),
        ("Aufträge letzter Lauf", controls.get("orders_processed", 0)),
        ("Statische Abweichungen", controls.get("order_status_counts", {}).get("ABWEICHUNG", 0)),
        ("Performance-Prüfungen", controls.get("performance_reviews_created", 0)),
    ):
        cards += f'<div class="metric"><span>{html.escape(label)}</span><strong>{value}</strong></div>'
    cards += "</div>"
    actions = f"""<form method="post" action="/run/standard" class="inline-form"><input type="hidden" name="csrf" value="{app.csrf_token}"><button class="primary">Standardprozess starten</button></form>
<form method="post" action="/run/training" class="inline-form"><input type="hidden" name="csrf" value="{app.csrf_token}"><button>Anlern-/Testprozess starten</button></form>"""
    statuses = perf.get("status_counts", {})
    status_rows = "".join(f"<tr><td>{html.escape(str(key))}</td><td>{value}</td></tr>" for key, value in statuses.items()) or '<tr><td colspan="2">Noch kein Performance-Lauf</td></tr>'
    return cards + '<div class="grid two">' + _card("Prozesssteuerung", actions) + _card("Letzte Performancebewertung", f'<table><tbody>{status_rows}</tbody></table>') + "</div>"


def _parameters_page(app: WebApplication, message: str = "") -> str:
    config = app.config()
    params = app.parameters()
    perf = params["performance"]
    levels = params["raw_material_quantity_check"]["levels"]
    customer_keys = "\n".join(row.get("customer_key", "") for row in _read_csv(app.customers_path))
    notice = f'<div class="notice">{html.escape(message)}</div>' if message else ""
    checked = "checked" if config.get("schedule_enabled") else ""
    form = f"""{notice}<form method="post" action="/parameters" class="form-grid">
<input type="hidden" name="csrf" value="{app.csrf_token}">
<fieldset><legend>Datenpfade</legend>
<label>Standarddaten<input name="standard_data_dir" value="{html.escape(str(config['standard_data_dir']))}"></label>
<label>Test-/Anlerndaten<input name="training_data_dir" value="{html.escape(str(config['training_data_dir']))}"></label>
<label>Historische Referenz<input name="reference_data_dir" value="{html.escape(str(config['reference_data_dir']))}"></label>
<label>Ausgabeverzeichnis<input name="output_dir" value="{html.escape(str(config['output_dir']))}"></label></fieldset>
<fieldset><legend>Peer- und Materialparameter</legend>
<label>Mindestgruppengröße<input type="number" min="3" name="minimum_peer_group_size" value="{perf['minimum_peer_group_size']}"></label>
<label>Auffälligkeitsgrenze<input type="number" step="0.1" name="robust_z_warning_threshold" value="{perf['robust_z_warning_threshold']}"></label>
<label>Sehr auffällig<input type="number" step="0.1" name="robust_z_threshold" value="{perf['robust_z_threshold']}"></label>
<div class="three"><label>Rohware Hinweis<input type="number" step="0.01" name="raw_hint" value="{levels[0]['minimum_ratio']}"></label>
<label>Rohware prüfen<input type="number" step="0.01" name="raw_review" value="{levels[1]['minimum_ratio']}"></label>
<label>Rohware kritisch<input type="number" step="0.01" name="raw_critical" value="{levels[2]['minimum_ratio']}"></label></div></fieldset>
<fieldset><legend>Auslastungskunden</legend><label>Eine Kundennummer je Zeile<textarea name="accepted_customers" rows="8">{html.escape(customer_keys)}</textarea></label>
<p class="hint">Aufträge bleiben vollständig prüfpflichtig; nur ein negatives Ergebnis wird als grundsätzlich zulässig markiert.</p></fieldset>
<fieldset><legend>Aufgabe planen</legend><label class="check"><input type="checkbox" name="schedule_enabled" {checked}> Täglich ausführen, solange die Anwendung läuft</label>
<label>Uhrzeit<input type="time" name="schedule_time" value="{html.escape(str(config['schedule_time']))}"></label>
<label>Prozess<select name="schedule_process"><option value="standard" {"selected" if config['schedule_process']=='standard' else ''}>Standardprozess</option><option value="training" {"selected" if config['schedule_process']=='training' else ''}>Anlern-/Testprozess</option></select></label></fieldset>
<div class="form-actions"><button class="primary">Parameter lokal speichern</button></div></form>"""
    return _card("Lokale Parametrierung", form)


def _run_frequency(run_dir: Path) -> Counter[str]:
    counter: Counter[str] = Counter()
    for file_name, field, statuses in (
        ("rule_results.csv", "rule_id", {"ABWEICHUNG"}),
        ("performance_assessments.csv", "reason_codes", None),
    ):
        for row in _read_csv(run_dir / file_name):
            if statuses and row.get("status") not in statuses:
                continue
            for code in row.get(field, "").split("|"):
                if code:
                    counter[code] += 1
    return counter


def _runs_page(app: WebApplication) -> str:
    rows = []
    combined: Counter[str] = Counter()
    for item in app.run_history(10):
        manifest = item["manifest"]
        control = manifest.get("control_totals", {})
        frequency = _run_frequency(item["dir"])
        combined.update(frequency)
        top = ", ".join(f"{code} ({count})" for code, count in frequency.most_common(3)) or "keine"
        run_id = item["dir"].name
        rows.append(f"<tr><td><a href=\"/orders?{urlencode({'run': run_id})}\">{html.escape(run_id)}</a></td><td>{html.escape(str(manifest.get('completed_at_utc',''))[:19])}</td><td>{control.get('orders_processed',0)}</td><td>{control.get('performance_reviews_created',0)}</td><td>{html.escape(top)}</td></tr>")
    history_table = '<table><thead><tr><th>Lauf</th><th>Abschluss</th><th>Aufträge</th><th>Prüffälle</th><th>Häufigste Hinweise</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>"
    combined_rows = "".join(f"<tr><td>{html.escape(code)}</td><td>{count}</td></tr>" for code, count in combined.most_common(10)) or '<tr><td colspan="2">Keine Daten</td></tr>'
    return _card("Letzte 10 Läufe", history_table) + _card("Häufigste Hinweise der letzten 10 Läufe", f"<table><tbody>{combined_rows}</tbody></table>")


def _order_rows(app: WebApplication, run_dir: Path, only_review: bool, query: str = "") -> list[dict[str, str]]:
    performance = {row["order_number"]: row for row in _read_csv(run_dir / "performance_assessments.csv")}
    static = {row["order_number"]: row for row in _read_csv(run_dir / "order_assessments.csv")}
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    source = Path(manifest.get("configuration", {}).get("source_directory", ""))
    descriptions = {}
    if source.is_dir() and (source / "Auftragskopf.csv").is_file():
        descriptions = {row["BelegNummer"].strip(): row.get("Zusatztext", "").strip() for row in read_rows(source, "Auftragskopf.csv")}
    orders = sorted(set(performance).union(static))
    result = []
    for order in orders:
        p, s = performance.get(order, {}), static.get(order, {})
        if only_review and not (p.get("manual_review_required") == "True" or s.get("manual_review_required") == "True"):
            continue
        haystack = " ".join((order, descriptions.get(order, ""), p.get("reason_explanation", ""))).casefold()
        if query and query.casefold() not in haystack:
            continue
        result.append({**s, **p, "order_number": order, "description": descriptions.get(order, "")})
    return result


def _orders_page(app: WebApplication, params: dict[str, list[str]], only_review: bool = False) -> str:
    run_id, run_dir = _latest_run(app, params.get("run", [""])[0])
    if not run_dir:
        return _card("Keine Ergebnisse", "Noch kein vollständiger Lauf vorhanden.")
    query = params.get("q", [""])[0].strip()
    rows = _order_rows(app, run_dir, only_review, query)[:500]
    table_rows = "".join(
        f'<tr><td><a href="/order?{urlencode({"run":run_id,"order":row["order_number"]})}">{html.escape(row["order_number"])}</a></td>'
        f'<td>{html.escape(row.get("description", ""))}</td><td><span class="status {html.escape(row.get("performance_status", "").lower())}">{html.escape(row.get("performance_status", ""))}</span></td>'
        f'<td>{html.escape(row.get("overall_status", ""))}</td><td>{html.escape(row.get("reason_explanation", row.get("reasons", "")))}</td></tr>'
        for row in rows
    ) or '<tr><td colspan="5">Keine passenden Aufträge</td></tr>'
    search = f'<form method="get" class="search"><input type="hidden" name="run" value="{html.escape(run_id)}"><input name="q" value="{html.escape(query)}" placeholder="Auftrag oder Beschreibung"><button>Suchen</button></form>'
    return _card(f"Lauf {run_id}", search + f'<table><thead><tr><th>Auftrag</th><th>Zusatzbeschreibung</th><th>Performance</th><th>Statisch</th><th>Begründung</th></tr></thead><tbody>{table_rows}</tbody></table>')


def _order_detail(app: WebApplication, params: dict[str, list[str]]) -> str:
    run_id, run_dir = _latest_run(app, params.get("run", [""])[0])
    order = params.get("order", [""])[0]
    if not run_dir or not order:
        return _card("Auftrag nicht gefunden", "Ungültiger Auftrag oder Lauf.")
    rows = [row for row in _order_rows(app, run_dir, False) if row["order_number"] == order]
    if not rows:
        return _card("Auftrag nicht gefunden", "Keine Bewertung vorhanden.")
    row = rows[0]
    detail_fields = (
        ("Auftrag", "order_number", "text"), ("Zusatzbeschreibung", "description", "text"),
        ("Performance", "performance_status", "text"), ("Ergebnis", "absolute_result", "text"),
        ("Erlöse", "revenue_eur", "money"), ("Kosten", "cost_eur", "money"),
        ("Marge", "margin_eur", "money"),
        ("Papier/Karton-Faktor zu Erlös", "paper_cardboard_share_of_revenue", "ratio"),
        ("Gesamtmaterial-Faktor zu Erlös", "total_material_share_of_revenue", "ratio"),
            ("Rohwarenstufe", "raw_material_quantity_status", "text"),
            ("Rückmeldestatus", "reason_review_status", "text"),
        ("Begründungscodes", "reason_codes", "text"),
        ("Begründung", "reason_explanation", "text"),
    )
    details = "".join(
        f"<tr><th>{html.escape(label)}</th><td>{html.escape(_formatted_number(str(row.get(field,'')), kind) if kind != 'text' else str(row.get(field,'')))}</td></tr>"
        for label, field, kind in detail_fields
    )
    feedback = f"""<form method="post" action="/feedback" class="form-grid compact"><input type="hidden" name="csrf" value="{app.csrf_token}"><input type="hidden" name="run_id" value="{html.escape(run_id)}"><input type="hidden" name="order_number" value="{html.escape(order)}">
<label>Entscheidung<select name="decision" required><option value="">Bitte wählen</option><option>CONFIRMED</option><option>CHANGED</option><option>NO_CORRECTION</option><option>DATA_ERROR</option><option>RULE_CHANGE_NEEDED</option></select></label>
<label>Bestätigte Codes<input name="confirmed_reason_codes" value="{html.escape(row.get('reason_codes',''))}"></label>
<label>Geänderte Begründung<textarea name="changed_reason" rows="3"></textarea></label>
<label class="check"><input type="checkbox" name="correction_required"> Korrektur erforderlich</label>
<label>Kommentar<textarea name="comment" rows="3"></textarea></label><label>Geprüft von<input name="reviewed_by"></label><button class="primary">Feedback lokal speichern</button></form>"""
    return '<div class="grid two">' + _card("Bewertungsdetails", f"<table class=\"details\">{details}</table>") + _card("Prüfung und Feedback", feedback) + "</div>"


def make_handler(app: WebApplication):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, body: str, status: int = 200, content_type: str = "text/html; charset=utf-8") -> None:
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(payload)

        def _redirect(self, path: str) -> None:
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", path)
            self.end_headers()

        def _form(self) -> dict[str, list[str]]:
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_POST_BYTES:
                raise AnalysisError("Formular ist zu groß.")
            return parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            if parsed.path == "/static/style.css":
                self._send((app.root / "src" / "sp_naka" / "web" / "style.css").read_text(encoding="utf-8"), content_type="text/css; charset=utf-8")
                return
            state = app.run_state()
            routes = {
                "/": ("dashboard", "Übersicht", lambda: _dashboard(app)),
                "/runs": ("runs", "Laufhistorie", lambda: _runs_page(app)),
                "/orders": ("orders", "Auftragsbewertung", lambda: _orders_page(app, params)),
                "/review": ("review", "Prüfung & Feedback", lambda: _orders_page(app, params, True)),
                "/order": ("orders", "Auftragsdetails", lambda: _order_detail(app, params)),
                "/parameters": ("parameters", "Parametrierung", lambda: _parameters_page(app, params.get("message", [""])[0])),
            }
            route = routes.get(parsed.path)
            if not route:
                self._send("Nicht gefunden", 404, "text/plain; charset=utf-8")
                return
            self._send(_layout(route[1], route[0], route[2](), state))

        def do_POST(self) -> None:
            try:
                form = self._form()
                if not secrets.compare_digest(form.get("csrf", [""])[0], app.csrf_token):
                    raise AnalysisError("Ungültige Formularsitzung. Seite bitte neu laden.")
                if self.path == "/parameters":
                    app.save_settings(form)
                    self._redirect("/parameters?message=Parameter+gespeichert")
                elif self.path in {"/run/standard", "/run/training"}:
                    process = self.path.rsplit("/", 1)[-1]
                    ok, message = app.start_process(process)
                    self._redirect("/?" + urlencode({"message": message, "ok": str(ok)}))
                elif self.path == "/feedback":
                    app.save_feedback(form)
                    self._redirect("/order?" + urlencode({"run": form["run_id"][0], "order": form["order_number"][0]}))
                else:
                    self._send("Nicht gefunden", 404, "text/plain; charset=utf-8")
            except (AnalysisError, ValueError, OSError) as exc:
                self._send(_layout("Fehler", "", _card("Eingabe konnte nicht gespeichert werden", html.escape(str(exc))), app.run_state()), 400)

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    app = WebApplication(root)
    host = os.environ.get("SP_NAKA_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("SP_NAKA_WEB_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), make_handler(app))
    print(f"SP_Naka Weboberfläche: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("SP_Naka Weboberfläche beendet.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

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
from .costing import confirmed_data_error_orders
from .nachkalkulation import load_order_calculation, number as parse_number
from .pipeline import run_analysis


MAX_POST_BYTES = 1024 * 1024

CALCULATION_DATASETS = {"test", "training", "standard"}
PROFESSIONAL_ASSESSMENTS = {
    "OFFEN",
    "IN_ORDNUNG",
    "AUFFAELLIG_ABER_ERKLAERT",
    "KORREKTUR_ERFORDERLICH",
    "DATENFEHLER",
    "AKZEPTIERTE_AUSNAHME",
}
REVIEW_STATUSES = {"OFFEN", "IN_PRUEFUNG", "ABGESCHLOSSEN"}
CORRECTION_ACTIONS = {"OFFEN", "AKZEPTIERT", "WIRD_KORRIGIERT"}
PERFORMANCE_STATUSES = {
    "IM_REFERENZBEREICH", "AUFFAELLIG_NEGATIV", "AUFFAELLIG_POSITIV",
    "SEHR_NEGATIV", "SEHR_POSITIV", "NICHT_BEWERTET",
    "AKZEPTIERTE_AUSNAHME_NACHPRODUKTION",
    "AKZEPTIERTE_AUSNAHME_KONSTRUKTION_DATEN",
}
KNOWN_REASON_CODES = {
    "ERGEBNIS_NEGATIV", "AUSLASTUNGSKUNDE", "NACHPRODUKTION_ERKANNT",
    "KONSTRUKTIONS_DATENAUFTRAG", "ROBUSTE_PEER_ABWEICHUNG",
    "PREISNIVEAU_NIEDRIG", "LEISTUNG_ZEIT_AUFFAELLIG",
    "MATERIALAUFWAND_AUFFAELLIG", "EINZELKOSTEN_AUFFAELLIG",
    "MEHRAUFWAND_ERFASST", "DRUCKABSTIMMUNG_ERKANNT",
    "HANDARBEIT_MIT_AUSSERGEWOEHNLICHEM_AUFWAND",
    "ERSTE_STANZFORM_MIT_WS", "ERSTE_STANZFORM_OHNE_WS_HINWEIS",
    "SERIENKANDIDAT", "ROHWARENMENGE_HINWEIS", "ROHWARENMENGE_PRUEFEN",
    "ROHWARENMENGE_KRITISCH", "PREIS_KRITISCH",
    "THEORETISCHE_KOSTEN_UNVOLLSTAENDIG", "KOSTENABSTIMMUNG_WARNUNG",
    "KOSTENABSTIMMUNG_KRITISCH",
}
CLARIFICATION_FIELDS = [
    "dataset", "order_number", "professional_assessment", "review_status",
    "professional_clarification", "correction_required", "correction_action",
    "reviewed_by", "reviewed_at",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_semicolon_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


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


def _write_semicolon_csv_replace(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
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
        self.order_clarifications_path = self.local_root / "feedback" / "order_clarifications.csv"
        self.test_cases_path = self.local_root / "TestDaten" / "Testset_3_Beispiele.csv"
        self.rules_path = self.root / "config" / "rules.json"
        self.csrf_token = secrets.token_urlsafe(32)
        self._state_lock = threading.Lock()
        self._running: dict[str, object] = {"active": False, "message": "Bereit"}
        self._ensure_local_files()
        threading.Thread(target=self._scheduler_loop, daemon=True).start()

    def _defaults(self) -> dict[str, object]:
        supplied_training = self.local_root / "Komplett" / "CSV"
        supplied_test = self.local_root / "TestDaten" / "CSV"
        legacy_standard = self.local_root / "CSV_Original"
        legacy_test = self.local_root / "CSV_TestDataSet"
        return {
            "standard_data_dir": str(supplied_test if supplied_test.is_dir() else legacy_standard),
            "training_data_dir": str(supplied_test if supplied_test.is_dir() else legacy_test),
            "reference_data_dir": str(supplied_training if supplied_training.is_dir() else legacy_standard),
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
        clarification_rows = _read_csv(self.order_clarifications_path)
        if not self.order_clarifications_path.is_file() or (
            clarification_rows and "correction_action" not in clarification_rows[0]
        ):
            for row in clarification_rows:
                row["correction_action"] = (
                    "WIRD_KORRIGIERT" if row.get("correction_required") == "YES" else "OFFEN"
                )
            _write_csv_replace(self.order_clarifications_path, CLARIFICATION_FIELDS, clarification_rows)

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

    def calculation_data_dir(self, selection: str) -> Path:
        field = {
            "test": "training_data_dir",
            "training": "reference_data_dir",
            "standard": "standard_data_dir",
        }.get(selection)
        if field is None:
            raise AnalysisError("Unbekannter Datenbestand.")
        path = Path(str(self.config()[field])).expanduser().resolve()
        if not path.is_dir():
            raise AnalysisError(f"Datenverzeichnis nicht gefunden: {path}")
        return path

    def test_case(self, order_number: str) -> dict[str, str]:
        record = next(
            (
                row
                for row in _read_semicolon_csv(self.test_cases_path)
                if (row.get("order_number") or "").strip() == order_number
            ),
            {},
        )
        if record and not (record.get("professional_explanation") or "").strip():
            explanation = (record.get("current_explanation") or "").strip()
            codes = (record.get("current_reason_codes") or "").strip()
            if not explanation and codes and (" " in codes or "." in codes):
                explanation = codes
                record["current_reason_codes"] = ""
            if explanation:
                record["professional_explanation"] = explanation
        return record

    def order_clarification(self, order_number: str, dataset: str) -> dict[str, str]:
        if dataset not in CALCULATION_DATASETS:
            raise AnalysisError("Unbekannter Datenbestand.")
        saved = next(
            (
                row
                for row in _read_csv(self.order_clarifications_path)
                if row.get("dataset") == dataset and row.get("order_number") == order_number
            ),
            {},
        )
        if saved:
            return saved
        test_case = self.test_case(order_number)
        inherited_status = (test_case.get("review_status") or "OFFEN").strip().upper()
        return {
            "dataset": dataset,
            "order_number": order_number,
            "professional_assessment": "OFFEN",
            "review_status": inherited_status if inherited_status in REVIEW_STATUSES else "OFFEN",
            "professional_clarification": (test_case.get("professional_explanation") or "").strip(),
            "correction_required": "NO",
            "correction_action": "OFFEN",
            "reviewed_by": "",
            "reviewed_at": "",
        }

    def latest_order_assessment(self, order_number: str, source_dir: Path) -> dict[str, str]:
        expected_source = source_dir.resolve()
        for item in self.run_history(100):
            manifest = item["manifest"]
            configured_source = manifest.get("configuration", {}).get("source_directory", "")
            if not configured_source:
                continue
            try:
                if Path(str(configured_source)).expanduser().resolve() != expected_source:
                    continue
            except OSError:
                continue
            performance = next((row for row in _read_csv(item["dir"] / "performance_assessments.csv") if row.get("order_number") == order_number), {})
            costs = next((row for row in _read_csv(item["dir"] / "cost_assessments.csv") if row.get("order_number") == order_number), {})
            if performance or costs:
                codes = list(dict.fromkeys(
                    code for value in (performance.get("reason_codes", ""), costs.get("reason_codes", ""))
                    for code in value.split("|") if code
                ))
                explanations = [value for value in (performance.get("reason_explanation", ""), costs.get("reason_explanation", "")) if value]
                return {
                    **performance, **costs,
                    "reason_codes": "|".join(codes),
                    "reason_explanation": " | ".join(explanations),
                    "run_id": item["dir"].name,
                }
        return {}

    def save_order_clarification(self, form: dict[str, list[str]]) -> None:
        fields = CLARIFICATION_FIELDS
        dataset = form.get("dataset", [""])[0].strip()
        order = form.get("order_number", [""])[0].strip()
        assessment = form.get("professional_assessment", [""])[0].strip()
        status = form.get("review_status", [""])[0].strip()
        clarification = form.get("professional_clarification", [""])[0].strip()
        reviewed_by = form.get("reviewed_by", [""])[0].strip()
        correction_action = form.get("correction_action", ["OFFEN"])[0].strip()
        if dataset not in CALCULATION_DATASETS:
            raise AnalysisError("Unbekannter Datenbestand.")
        if assessment not in PROFESSIONAL_ASSESSMENTS:
            raise AnalysisError("Bitte eine gültige fachliche Bewertung wählen.")
        if status not in REVIEW_STATUSES:
            raise AnalysisError("Bitte einen gültigen Prüfstatus wählen.")
        if correction_action not in CORRECTION_ACTIONS:
            raise AnalysisError("Bitte eine gültige Korrekturentscheidung wählen.")
        if len(clarification) > 10000 or len(reviewed_by) > 200:
            raise AnalysisError("Die fachliche Rückmeldung ist zu lang.")
        load_order_calculation(self.calculation_data_dir(dataset), order)
        rows = [
            row for row in _read_csv(self.order_clarifications_path)
            if not (row.get("dataset") == dataset and row.get("order_number") == order)
        ]
        rows.append({
            "dataset": dataset,
            "order_number": order,
            "professional_assessment": assessment,
            "review_status": status,
            "professional_clarification": clarification,
            "correction_required": "YES" if (
                form.get("correction_required", [""])[0] == "on"
                or correction_action == "WIRD_KORRIGIERT"
            ) else "NO",
            "correction_action": correction_action,
            "reviewed_by": reviewed_by,
            "reviewed_at": datetime.now().isoformat(timespec="seconds"),
        })
        _write_csv_replace(self.order_clarifications_path, fields, rows)

    def save_test_case(self, form: dict[str, list[str]]) -> None:
        fields = [
            "order_number", "current_performance_status", "current_reason_codes",
            "current_explanation", "expected_performance_status", "expected_reason_codes",
            "accepted_exception", "correction_required", "professional_explanation",
            "review_status",
        ]
        order = form.get("order_number", [""])[0].strip()
        if not order or len(order) > 50:
            raise AnalysisError("Bitte eine gültige Auftragsnummer eingeben.")
        existing = next(
            (
                row for row in _read_semicolon_csv(self.test_cases_path)
                if (row.get("order_number") or "").strip() == order
            ),
            {},
        )
        values = {"order_number": order}
        for field in fields[1:]:
            if field == "expected_reason_codes" and field in form:
                values[field] = "|".join(dict.fromkeys(
                    value.strip() for value in form[field] if value.strip()
                ))
            else:
                values[field] = (
                    form[field][0].strip() if field in form else existing.get(field, "").strip()
                )
        if values["expected_performance_status"] and values["expected_performance_status"] not in PERFORMANCE_STATUSES:
            raise AnalysisError("Ungültige erwartete Performancebewertung.")
        selected_codes = set(filter(None, values["expected_reason_codes"].split("|")))
        if not selected_codes.issubset(_known_reason_codes(self)):
            raise AnalysisError("Mindestens ein ausgewählter Reason Code ist unbekannt.")
        if values["review_status"] and values["review_status"] not in REVIEW_STATUSES:
            raise AnalysisError("Ungültiger Testfallstatus.")
        if any(len(value) > 10000 for value in values.values()):
            raise AnalysisError("Testvorgabe ist zu lang.")
        rows = [
            row for row in _read_semicolon_csv(self.test_cases_path)
            if (row.get("order_number") or "").strip() != order
        ]
        rows.append(values)
        rows.sort(key=lambda row: (row.get("order_number") or ""))
        _write_semicolon_csv_replace(self.test_cases_path, fields, rows)

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
                order_clarifications_path=self.order_clarifications_path,
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
        ("calculation", "/calculation", "Nachkalkulation"),
        ("runs", "/runs", "Laufhistorie"),
        ("orders", "/orders", "Aufträge & Prüfung"),
        ("test-cases", "/test-cases", "Testvorgaben"),
        ("parameters", "/parameters", "Parametrierung"),
        ("documentation", "/documentation", "Dokumentation"),
    ]
    nav = "".join(
        f'<a class="nav-item {"active" if key == active else ""}" href="{url}">{html.escape(label)}</a>'
        for key, url, label in menus
    )
    run_class = "running" if state.get("active") else "ready"
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · SP_Naka</title><link rel="stylesheet" href="/static/style.css"><link rel="stylesheet" href="/static/workflow.css"></head>
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


def _optional_number(value: object, kind: str = "number") -> str:
    if value is None or value == "":
        return "—"
    return _formatted_number(str(value), kind)


def _data_table(
    rows: list[dict[str, object]] | list[dict[str, str]],
    columns: tuple[tuple[str, str], ...],
    empty: str = "Keine Daten vorhanden",
    bold_fields: frozenset[str] = frozenset(),
    footer: dict[str, object] | None = None,
) -> str:
    head = "".join(f"<th>{html.escape(label)}</th>" for label, _ in columns)
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{'<strong>' if field in bold_fields else ''}"
            f"{html.escape(str(row.get(field, '') or ''))}"
            f"{'</strong>' if field in bold_fields else ''}</td>"
            for _, field in columns
        )
        + "</tr>"
        for row in rows
    )
    if not body:
        body = f'<tr><td colspan="{len(columns)}">{html.escape(empty)}</td></tr>'
    if footer is not None:
        body += '<tr class="table-total">' + "".join(
            f"<th>{html.escape(str(footer.get(field, '') or ''))}</th>"
            for _, field in columns
        ) + "</tr>"
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _calculation_page(app: WebApplication, params: dict[str, list[str]]) -> str:
    order = params.get("order", [""])[0].strip()
    selection = params.get("dataset", ["test"])[0]
    if selection not in CALCULATION_DATASETS:
        selection = "test"
    options = (
        ("test", "Testdaten"),
        ("training", "Trainingsdaten (Komplett)"),
        ("standard", "Standarddaten"),
    )
    option_html = "".join(
        f'<option value="{key}" {"selected" if selection == key else ""}>{html.escape(label)}</option>'
        for key, label in options
    )
    search = f"""<form method="get" class="calculation-search">
<label>Auftragsnummer<input name="order" value="{html.escape(order)}" required autocomplete="off" placeholder="z. B. 123456"></label>
<label>Datenbestand<select name="dataset">{option_html}</select></label>
<button class="primary">Nachkalkulation anzeigen</button></form>"""
    if not order:
        return _card(
            "Auftrag aufrufen",
            search
            + '<p class="hint">Die Ansicht liest die lokalen CSV-Dateien ausschließlich lesend. '
            "Fehlende Kostenbestandteile werden gekennzeichnet und nicht geschätzt.</p>",
        )
    try:
        calculation = load_order_calculation(
            app.calculation_data_dir(selection),
            order,
            Path(str(app.config()["reference_data_dir"])),
            confirmed_data_error_orders(app.order_clarifications_path),
        )
    except AnalysisError as exc:
        return _card("Auftrag aufrufen", search) + _card("Nicht gefunden", html.escape(str(exc)), "warning-card")

    header = calculation["header"]
    assert isinstance(header, dict)
    revenue = calculation["revenue"]
    cost = calculation["cost"]
    result = calculation["result"]
    margin_rate = calculation["margin_rate"]
    cost_assessment = calculation["cost_assessment"]
    result_class = "negative" if isinstance(result, (int, float)) and result < 0 else "positive"
    identity = f"""<div class="order-heading"><div><span>Auftrag</span><strong>{html.escape(order)}</strong></div>
<div><span>Beschreibung</span><strong>{html.escape(str(header.get('Zusatztext', '') or '—'))}</strong></div>
<div><span>Kunde</span><strong>{html.escape(str(header.get('Kunde Key', '') or ''))} · {html.escape(str(header.get('KundeName', '') or ''))}</strong></div>
<div><span>Produktgruppe</span><strong>{html.escape(str(header.get('X_ArtikelGruppe', '') or ''))} · {html.escape(str(header.get('ArtikelGruppeBez', '') or ''))}</strong></div></div>"""
    summary = f"""<div class="calculation-summary">
<div><span>Erlöse</span><strong>{html.escape(_optional_number(revenue, 'money'))}</strong></div>
<div><span>Gesamtkosten</span><strong>{html.escape(_optional_number(cost, 'money'))}</strong></div>
<div class="{result_class}"><span>Ergebnis</span><strong>{html.escape(_optional_number(result, 'money'))}</strong><small>{html.escape(_optional_number(margin_rate, 'ratio'))}</small></div>
<div><span>Abgestimmte Istkosten*</span><strong>{html.escape(_optional_number(cost_assessment['reconstructed_cost'], 'money'))}</strong><small>{html.escape(str(cost_assessment['reconciliation_status']))}</small></div>
<div><span>Theoretische Sollkosten</span><strong>{html.escape(_optional_number(cost_assessment['theoretical_total_cost'], 'money'))}</strong><small>{'PREIS KRITISCH' if cost_assessment['price_critical'] else 'theoretisch positiv möglich'}</small></div></div>
<p class="hint">* Rekonstruktion aus Istmaterial, Produktionszeiten, Rechnungskontrollen, KORE-/Lagerkosten und den zum Belegdatum gültigen Zuschlägen.</p>"""

    positions = _data_table(
        calculation["positions"],
        (
            ("Pos.", "PositionsNr"), ("Artikel", "Artikel"),
            ("Produktgruppe", "ArtikelGruppeBez"), ("Menge", "Menge"),
            ("Geliefert", "gelieferte_Menge"), ("Offen", "offen"),
            ("Netto", "GesamtNetto"), ("Muster", "Muster"),
        ),
    )
    production_summary = calculation["production_summary"]
    for row in production_summary:
        row["duration_display"] = _optional_number(row.get("duration"))
        row["machine_display"] = _optional_number(row.get("machine_duration"))
        row["employee_display"] = _optional_number(row.get("employee_duration"))
        row["quantity_display"] = _optional_number(row.get("quantity"))
        row["performance_display"] = _optional_number(row.get("performance"))
        row["cost_display"] = (
            _optional_number(row.get("cost"), "money")
            if calculation["production_detail_available"]
            else "0,00 € im Export"
        )
    production = _data_table(
        production_summary,
        (
            ("Stufe", "stage"), ("Meldungen", "entries"),
            ("AZ", "duration_display"), ("MF", "machine_display"),
            ("MH", "employee_display"), ("Menge", "quantity_display"),
            ("Leistung (Menge/Gesamtzeit)", "performance_display"),
            ("Kosten", "cost_display"), ("Mehraufwand", "extra_effort_entries"),
        ),
        bold_fields=frozenset({"cost_display"}),
        footer={
            "stage": "Summe Produktionskosten",
            "cost_display": _optional_number(cost_assessment["production_cost"], "money"),
        },
    )
    for row in calculation["production"]:
        row["cost_display"] = _optional_number(row.get("Kosten"), "money")
    production_details = _data_table(
        calculation["production"],
        (
            ("Datum", "Datum"), ("Stufe", "Stufe"), ("Kostenstelle", "KSTKurz"),
            ("Arbeitsvorgang", "ARVOKurz"), ("AZ", "Dauer"),
            ("MF", "DauerMaschine"), ("MH", "DauerMF"),
            ("Menge", "Menge"), ("Kosten", "cost_display"),
            ("Mehraufwand", "Mehraufwand Id"),
        ),
        bold_fields=frozenset({"cost_display"}),
        footer={
            "Stufe": "Summe Produktionskosten",
            "cost_display": _optional_number(cost_assessment["production_cost"], "money"),
        },
    )

    individual_rows: list[dict[str, object]] = []
    for row in calculation["manufacturing_material"]:
        individual_rows.append({
            "source": "Fertigungsmaterial", "date": "", "article": row.get("Artikel", ""),
            "description": row.get("Bezeichnung", ""), "group": row.get("ArtikelGruppeBez", row.get("GruppeBezeichnung", "")),
            "quantity": row.get("VerbrauchteMenge", ""), "unit": "", "value": _optional_number(row.get("Materialwert"), "money"),
        })
    for row in calculation["raw_bookings"]:
        parsed_value = parse_number(row.get("WertMat"))
        # RW-Verbrauch ist in der Quelle negativ und wird als positive
        # Kostenwirkung gezeigt; eine positive Korrekturbuchung entsprechend
        # als negative Kostenwirkung.
        value = -parsed_value if parsed_value is not None else None
        individual_rows.append({
            "source": "RW-Buchung", "date": row.get("BuchungsDatum", ""), "article": row.get("Artikel", ""),
            "description": row.get("Sorte", ""), "group": row.get("ArtikelGruppeBez", ""),
            "quantity": row.get("Menge", ""), "unit": row.get("Artikel EH", ""), "value": _optional_number(value, "money"),
        })
    for row in calculation["invoice_controls"]:
        individual_rows.append({
            "source": "Rechnungskontrolle", "date": row.get("RechnungsDatum", ""), "article": row.get("Artikel Key", ""),
            "description": row.get("Bezeichnung", ""), "group": row.get("ArtikelGruppeBez", ""),
            "quantity": row.get("Menge", ""), "unit": "", "value": _optional_number(row.get("WarenwertEUR"), "money"),
        })
    for row in calculation["cost_bookings"]:
        individual_rows.append({
            "source": "Kostenträger", "date": row.get("BuchungsDatum", ""), "article": row.get("TrKoArt", ""),
            "description": row.get("BuchungsText", ""), "group": "", "quantity": row.get("Menge", ""),
            "unit": "", "value": _optional_number(row.get("Betrag"), "money"),
        })
    individual = _data_table(
        individual_rows,
        (
            ("Quelle", "source"), ("Datum", "date"), ("Artikel", "article"),
            ("Bezeichnung", "description"), ("Gruppe", "group"),
            ("Menge", "quantity"), ("EH", "unit"), ("Kostenwirkung", "value"),
        ),
        bold_fields=frozenset({"value"}),
        footer={
            "source": "Summe Einzelkosten",
            "value": _optional_number(cost_assessment["individual_cost"], "money"),
        },
    )

    vv_total = cost_assessment["vv_surcharge"] + cost_assessment["fixed_surcharge"]
    cost_rows = (
        ("Produktionskosten", cost_assessment["production_cost"], False),
        ("Einzelkosten", cost_assessment["individual_cost"], False),
        ("Gesamtkosten (netto)", cost_assessment["net_cost"], True),
        ("VV-Zuschlag (variabel + fix)", vv_total, False),
        ("Materialzuschlag", cost_assessment["material_surcharge"], False),
        ("Gesamtkosten", cost_assessment["reconstructed_cost"], True),
    )
    cost_body = "".join(
        f"<tr><{'th' if bold else 'td'}>{html.escape(label)}</{'th' if bold else 'td'}>"
        f"<{'th' if bold else 'td'}>{html.escape(_optional_number(value, 'money'))}</{'th' if bold else 'td'}></tr>"
        for label, value, bold in cost_rows
    )
    cost_body += '<tr aria-hidden="true"><td colspan="2">&nbsp;</td></tr>'
    cost_body += (
        f"<tr><td>Kosten Auftragskopf</td><td>{html.escape(_optional_number(cost_assessment['official_cost'], 'money'))}</td></tr>"
        f"<tr><td>Differenz ({html.escape(str(cost_assessment['reconciliation_status']))})</td>"
        f"<td>{html.escape(_optional_number(cost_assessment['reconciliation_difference'], 'money'))} / "
        f"{html.escape(_optional_number(cost_assessment['reconciliation_difference_rate'], 'ratio'))}</td></tr>"
    )
    limitations = "".join(f"<li>{html.escape(str(value))}</li>" for value in calculation["limitations"])
    cost_sources = f'<table><thead><tr><th>Kostenblock</th><th>Betrag</th></tr></thead><tbody>{cost_body}</tbody></table>' + f'<ul class="limitations">{limitations}</ul>'

    theory_rows = [
        {"label": "Material mit Sollmengen", "actual": _optional_number(cost_assessment["actual_material_cost"], "money"), "theory": _optional_number(cost_assessment["theoretical_material_cost"], "money")},
        {"label": "Produktion mit Idealleistung", "actual": _optional_number(cost_assessment["production_cost"], "money"), "theory": _optional_number(cost_assessment["theoretical_production_cost"], "money")},
        {"label": "Eingangsfaktura (z. B. WKS/WS)", "actual": _optional_number(cost_assessment["invoice_cost"], "money"), "theory": _optional_number(cost_assessment["theoretical_invoice_cost"], "money")},
        {"label": "Materialgemeinkosten", "actual": _optional_number(cost_assessment["material_surcharge"], "money"), "theory": _optional_number(cost_assessment["theoretical_material_surcharge"], "money")},
        {"label": "VV-Zuschlag", "actual": _optional_number(cost_assessment["vv_surcharge"], "money"), "theory": _optional_number(cost_assessment["theoretical_vv_surcharge"], "money")},
        {"label": "Gesamtkosten", "actual": _optional_number(cost_assessment["reconstructed_cost"], "money"), "theory": _optional_number(cost_assessment["theoretical_total_cost"], "money")},
        {"label": "Ergebnis", "actual": _optional_number(result, "money"), "theory": _optional_number(cost_assessment["theoretical_result"], "money")},
    ]
    theory_summary = _data_table(theory_rows, (("Kostenblock", "label"), ("Ist", "actual"), ("Theoretisch", "theory")))
    theory_production_rows = []
    for row in cost_assessment["theoretical_production_details"]:
        theory_production_rows.append({
            "stage": row["stage"], "machine": row["machine"],
            "actual_performance": _optional_number(row["actual_performance"]),
            "ideal_performance": _optional_number(row["ideal_performance"]),
            "reference": f"{row['reference_level']} ({row['reference_count']})",
            "actual_cost": _optional_number(row["actual_cost"], "money"),
            "theoretical_cost": _optional_number(row["theoretical_cost"], "money"),
        })
    theory_production = _data_table(
        theory_production_rows,
        (("Stufe", "stage"), ("Maschine", "machine"), ("Ist-Leistung", "actual_performance"),
         ("Idealleistung P75", "ideal_performance"), ("Referenz", "reference"),
         ("Istkosten", "actual_cost"), ("Sollkosten", "theoretical_cost")),
    )
    theory_material_rows = []
    for row in cost_assessment["theoretical_material_details"]:
        theory_material_rows.append({
            "article": row["article"], "group": row["group"],
            "quantity": _optional_number(row["planned_quantity"]),
            "price": _optional_number(row["unit_price"], "money"),
            "match": row["match_level"], "cost": _optional_number(row["theoretical_cost"], "money"),
        })
    theory_material = _data_table(
        theory_material_rows,
        (("Artikel", "article"), ("Gruppe", "group"), ("Sollmenge", "quantity"),
         ("abgeleiteter Preis", "price"), ("Zuordnung", "match"), ("Sollkosten", "cost")),
    )
    theoretical = theory_summary + f'<details><summary>Idealleistung je Produktionsstufe</summary>{theory_production}</details>' + f'<details><summary>Sollmaterial und Preiszuordnung</summary>{theory_material}</details>'

    test_case = app.test_case(order)
    clarification = app.order_clarification(order, selection)
    automated = app.latest_order_assessment(order, calculation["source_dir"])
    official_assessment = (
        "NEGATIVES ERGEBNIS" if isinstance(result, (int, float)) and result < 0
        else "POSITIVES ERGEBNIS" if isinstance(result, (int, float)) and result > 0
        else "ERGEBNIS NULL ODER UNBEKANNT"
    )
    assessment_options = (
        ("OFFEN", "Offen"),
        ("IN_ORDNUNG", "In Ordnung"),
        ("AUFFAELLIG_ABER_ERKLAERT", "Auffällig, aber erklärt"),
        ("KORREKTUR_ERFORDERLICH", "Korrektur erforderlich"),
        ("DATENFEHLER", "Datenfehler"),
        ("AKZEPTIERTE_AUSNAHME", "Akzeptierte Ausnahme"),
    )
    assessment_select = "".join(
        f'<option value="{key}" {"selected" if clarification.get("professional_assessment") == key else ""}>{html.escape(label)}</option>'
        for key, label in assessment_options
    )
    status_select = "".join(
        f'<option value="{key}" {"selected" if clarification.get("review_status") == key else ""}>{html.escape(label)}</option>'
        for key, label in (("OFFEN", "Offen"), ("IN_PRUEFUNG", "In Prüfung"), ("ABGESCHLOSSEN", "Abgeschlossen"))
    )
    automated_rows = (
        ("Systembewertung", automated.get("performance_status") or official_assessment),
        (
            "Muss geprüft werden?",
            "JA" if automated.get("manual_review_required") == "True" else "NEIN",
        ),
        (
            "Konkreter Prüfauftrag",
            _review_focus(
                automated.get("reason_codes", ""), automated.get("reason_review_status", "")
            ) if automated.get("manual_review_required") == "True" else "Keine Bestätigung erforderlich",
        ),
        ("System-Prüfstatus", automated.get("reason_review_status") or "—"),
        (
            "Reason Codes",
            automated.get("reason_codes")
            or test_case.get("current_reason_codes")
            or "Noch nicht berechnet – dieser Auftrag war bisher nur Teil des Referenzbestands.",
        ),
        (
            "Reason Explanation",
            automated.get("reason_explanation")
            or test_case.get("current_explanation")
            or "Noch nicht berechnet – keine passende Auftragsbewertung vorhanden.",
        ),
        ("Analyselauf", automated.get("run_id") or "Noch keine passende Analyse vorhanden"),
        ("Historisches NakaOK", header.get("NakaOK") or "—"),
        ("Historische NakaBemerkung", header.get("NakaBem") or "—"),
        ("Historischer Status", header.get("Status") or "—"),
        ("Erwartete Bewertung aus Testfall", test_case.get("expected_performance_status") or "—"),
        ("Vorhandener Testfallstatus", test_case.get("review_status") or "—"),
        ("Gespeicherte Fachbewertung", clarification.get("professional_assessment") or "OFFEN"),
        ("Prüfstatus", clarification.get("review_status") or "OFFEN"),
        ("Korrekturentscheidung", clarification.get("correction_action") or "OFFEN"),
    )
    automated_table = "".join(
        f"<tr><th>{html.escape(label)}</th><td>{html.escape(str(value))}</td></tr>"
        for label, value in automated_rows
    )
    saved_message = params.get("message", [""])[0]
    message_html = f'<p class="success-message">{html.escape(saved_message)}</p>' if saved_message else ""
    clarification_form = f"""<form method="post" action="/calculation/clarification" class="form-grid compact">
<input type="hidden" name="csrf" value="{app.csrf_token}"><input type="hidden" name="dataset" value="{html.escape(selection)}"><input type="hidden" name="order_number" value="{html.escape(order)}">
<label>Fachliche Bewertung<select name="professional_assessment" required>{assessment_select}</select></label>
<label>Status<select name="review_status" required>{status_select}</select></label>
<label class="full-width">Fachliche Klärung<textarea name="professional_clarification" rows="5" placeholder="Beobachtung, Ursache und fachliche Entscheidung dokumentieren">{html.escape(clarification.get('professional_clarification', ''))}</textarea></label>
<label>Korrekturentscheidung<select name="correction_action"><option value="OFFEN" {"selected" if clarification.get("correction_action", "OFFEN") == "OFFEN" else ""}>Offen</option><option value="AKZEPTIERT" {"selected" if clarification.get("correction_action") == "AKZEPTIERT" else ""}>Auffälligkeit akzeptiert</option><option value="WIRD_KORRIGIERT" {"selected" if clarification.get("correction_action") == "WIRD_KORRIGIERT" else ""}>Wird im führenden System korrigiert</option></select></label>
<label>Geprüft von<input name="reviewed_by" maxlength="200" value="{html.escape(clarification.get('reviewed_by', ''))}"></label>
<button class="primary">Bewertung lokal speichern</button></form>"""
    note = _card(
        "Bewertung & fachliche Klärung",
        message_html + '<div class="grid two"><div><h3>Analyse und vorhandene Hinweise</h3>'
        + f'<table class="details">{automated_table}</table></div><div><h3>Fachliche Rückmeldung</h3>'
        + clarification_form + "</div></div>",
    )

    return (
        _card("Auftrag aufrufen", search)
        + _card("Nachkalkulation", identity + summary, "calculation-sheet")
        + note
        + _card("Auftragspositionen", positions)
        + _card("Produktionsleistungen/-zeiten", production + f'<details><summary>Einzelmeldungen anzeigen ({len(calculation["production"])})</summary>{production_details}</details>')
        + _card("Einzelkosten aus gelieferten Quellen", individual)
        + _card("Istkostenabstimmung", cost_sources)
        + _card("Theoretische Sollkosten", theoretical)
    )


def _latest_run(app: WebApplication, requested: str = "") -> tuple[str, Path | None]:
    if requested:
        return requested, _safe_run_dir(app.output_root(), requested)
    history = app.run_history(1)
    return (history[0]["dir"].name, history[0]["dir"]) if history else ("", None)


def _dataset_for_source(app: WebApplication, source: Path) -> str:
    resolved = source.resolve()
    for selection in ("standard", "test", "training"):
        try:
            if app.calculation_data_dir(selection) == resolved:
                return selection
        except (AnalysisError, OSError):
            pass
    return "standard"


def _review_focus(codes: str, review_status: str = "") -> str:
    values = set(filter(None, codes.split("|")))
    if values.intersection({"ROHWARENMENGE_PRUEFEN", "ROHWARENMENGE_KRITISCH"}):
        return "Rohwarenkorrektur prüfen und entscheiden"
    if values.intersection({"LEISTUNG_ZEIT_AUFFAELLIG", "MATERIALAUFWAND_AUFFAELLIG", "EINZELKOSTEN_AUFFAELLIG"}):
        return "Leistung, Material bzw. Einzelkosten prüfen"
    if any(value.startswith("KOSTENABSTIMMUNG_") for value in values):
        return "Kostenabstimmung begründen"
    if "PREIS_KRITISCH" in values:
        return "Preisursache bestätigen"
    if review_status == "PROPOSED_REASON_CONFIRMATION_REQUIRED":
        return "Vorgeschlagene Ursache bestätigen"
    return "Fachliche Ursache dokumentieren"


def _is_correction_candidate(row: dict[str, str]) -> bool:
    codes = set(filter(None, row.get("reason_codes", "").split("|")))
    return bool(codes.intersection({
        "ROHWARENMENGE_PRUEFEN", "ROHWARENMENGE_KRITISCH",
        "LEISTUNG_ZEIT_AUFFAELLIG", "MATERIALAUFWAND_AUFFAELLIG",
        "EINZELKOSTEN_AUFFAELLIG",
    }))


def _known_reason_codes(app: WebApplication) -> set[str]:
    codes = set(KNOWN_REASON_CODES)
    try:
        configured = json.loads(app.rules_path.read_text(encoding="utf-8"))
        codes.update(str(rule.get("id", "")).strip() for rule in configured.get("rules", []))
    except (OSError, json.JSONDecodeError):
        pass
    for item in app.run_history(10):
        for file_name, field in (
            ("performance_assessments.csv", "reason_codes"),
            ("cost_assessments.csv", "reason_codes"),
            ("order_assessments.csv", "reason_codes"),
        ):
            for row in _read_csv(item["dir"] / file_name):
                codes.update(filter(None, row.get(field, "").split("|")))
    return {code for code in codes if code}


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
    costs = {row["order_number"]: row for row in _read_csv(run_dir / "cost_assessments.csv")}
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    source = Path(manifest.get("configuration", {}).get("source_directory", ""))
    dataset = _dataset_for_source(app, source) if source.is_dir() else "standard"
    descriptions = {}
    if source.is_dir() and (source / "Auftragskopf.csv").is_file():
        descriptions = {row["BelegNummer"].strip(): row.get("Zusatztext", "").strip() for row in read_rows(source, "Auftragskopf.csv")}
    orders = sorted(set(performance).union(static).union(costs))
    result = []
    for order in orders:
        p, s, c = performance.get(order, {}), static.get(order, {}), costs.get(order, {})
        if only_review and not any(row.get("manual_review_required") == "True" for row in (p, s, c)):
            continue
        combined_codes = list(dict.fromkeys(
            code for value in (p.get("reason_codes", ""), c.get("reason_codes", ""), s.get("reason_codes", ""))
            for code in value.split("|") if code
        ))
        combined_explanation = " | ".join(
            value for value in (p.get("reason_explanation", ""), c.get("reason_explanation", ""), s.get("reasons", "")) if value
        )
        haystack = " ".join((order, descriptions.get(order, ""), combined_explanation, " ".join(combined_codes))).casefold()
        if query and query.casefold() not in haystack:
            continue
        result.append({
            **s, **p, **c,
            "reason_codes": "|".join(combined_codes),
            "reason_explanation": combined_explanation,
            "order_number": order,
            "description": descriptions.get(order, ""),
            "dataset": dataset,
            "review_required": "JA" if any(
                row.get("manual_review_required") == "True" for row in (p, s, c)
            ) else "NEIN",
            "review_focus": _review_focus("|".join(combined_codes), p.get("reason_review_status", "")),
        })
    return result


def _orders_page(app: WebApplication, params: dict[str, list[str]], only_review: bool = False) -> str:
    run_id, run_dir = _latest_run(app, params.get("run", [""])[0])
    if not run_dir:
        return _card("Keine Ergebnisse", "Noch kein vollständiger Lauf vorhanden.")
    query = params.get("q", [""])[0].strip()
    view = "review" if only_review else params.get("view", ["all"])[0]
    if view not in {"all", "review", "corrections"}:
        view = "all"
    rows = _order_rows(app, run_dir, False, query)
    if view == "review":
        rows = [row for row in rows if row["review_required"] == "JA"]
    elif view == "corrections":
        rows = [row for row in rows if _is_correction_candidate(row)]
    rows = rows[:500]
    clarifications = {
        (row.get("dataset", ""), row.get("order_number", "")): row
        for row in _read_csv(app.order_clarifications_path)
    }
    table_rows = "".join(
        f'<tr><td><a href="/calculation?{urlencode({"dataset":row["dataset"],"order":row["order_number"]})}">{html.escape(row["order_number"])}</a></td>'
        f'<td>{html.escape(row.get("description", ""))}</td><td><span class="status {html.escape(row.get("performance_status", "").lower())}">{html.escape(row.get("performance_status", ""))}</span></td>'
        f'<td><strong>{html.escape(row["review_required"])}</strong></td><td>{html.escape(row["review_focus"] if row["review_required"] == "JA" else "Keine Bestätigung nötig")}</td>'
        f'<td>{html.escape(clarifications.get((row["dataset"], row["order_number"]), {}).get("correction_action", "OFFEN"))}</td>'
        f'<td>{html.escape(clarifications.get((row["dataset"], row["order_number"]), {}).get("review_status", "OFFEN"))}</td>'
        f'<td>{html.escape(row.get("reconciliation_status", ""))}</td><td>{html.escape(row.get("overall_status", ""))}</td><td>{html.escape(row.get("reason_explanation", row.get("reasons", "")))}</td></tr>'
        for row in rows
    ) or '<tr><td colspan="10">Keine passenden Aufträge</td></tr>'
    filters = '<div class="view-filters">' + "".join(
        f'<a class="nav-item {"active" if view == key else ""}" href="/orders?{urlencode({"run": run_id, "view": key, "q": query})}">{label}</a>'
        for key, label in (("all", "Alle Aufträge"), ("review", "Prüfung erforderlich"), ("corrections", "Korrekturen"))
    ) + '</div>'
    search = f'<form method="get" class="search"><input type="hidden" name="run" value="{html.escape(run_id)}"><input type="hidden" name="view" value="{html.escape(view)}"><input name="q" value="{html.escape(query)}" placeholder="Auftrag oder Beschreibung"><button>Suchen</button></form>'
    intro = '<p class="hint">Einheitliche Auftragsliste: Filter auswählen und über die Auftragsnummer direkt in der Nachkalkulation prüfen, begründen oder eine Korrekturentscheidung erfassen.</p>'
    return _card(f"Lauf {run_id}", intro + filters + search + f'<table><thead><tr><th>Auftrag</th><th>Zusatzbeschreibung</th><th>Performance</th><th>Prüfung</th><th>Zu prüfen / bestätigen</th><th>Korrektur</th><th>Status</th><th>Kostenabstimmung</th><th>Statisch</th><th>Begründung</th></tr></thead><tbody>{table_rows}</tbody></table>')


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
        ("Kostenabstimmung", "reconciliation_status", "text"),
        ("Rekonstruierte Istkosten", "reconstructed_cost_eur", "money"),
        ("Abweichung Auftragskopf", "reconciliation_difference_eur", "money"),
        ("Theoretische Sollkosten", "theoretical_total_cost_eur", "money"),
        ("Theoretisches Ergebnis", "theoretical_result_eur", "money"),
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


def _corrections_page(app: WebApplication, params: dict[str, list[str]]) -> str:
    run_id, run_dir = _latest_run(app, params.get("run", [""])[0])
    if not run_dir:
        return _card("Keine Ergebnisse", "Noch kein vollständiger Lauf vorhanden.")
    rows = _order_rows(app, run_dir, False)
    saved = {
        (row.get("dataset", ""), row.get("order_number", "")): row
        for row in _read_csv(app.order_clarifications_path)
    }
    candidates = [
        row for row in rows
        if _is_correction_candidate(row)
        or saved.get((row["dataset"], row["order_number"]), {}).get("correction_action") == "WIRD_KORRIGIERT"
    ]
    table_rows = "".join(
        '<tr>'
        f'<td><a href="/calculation?{urlencode({"dataset": row["dataset"], "order": row["order_number"]})}">{html.escape(row["order_number"])}</a></td>'
        f'<td>{html.escape(_review_focus(row.get("reason_codes", "")))}</td>'
        f'<td>{html.escape(row.get("raw_material_quantity_status", "") or "—")}</td>'
        f'<td>{html.escape(saved.get((row["dataset"], row["order_number"]), {}).get("correction_action", "OFFEN"))}</td>'
        f'<td>{html.escape(saved.get((row["dataset"], row["order_number"]), {}).get("review_status", "OFFEN"))}</td>'
        f'<td>{html.escape(row.get("reason_explanation", ""))}</td></tr>'
        for row in candidates
    ) or '<tr><td colspan="6">Im aktuellen Lauf sind keine Korrekturkandidaten offen.</td></tr>'
    intro = (
        '<p>Hier stehen Rohwaren-, Leistungs-, Material- und Einzelkostenauffälligkeiten, die '
        'akzeptiert oder im führenden System korrigiert werden müssen. Nach neuen CSV-Daten wird '
        'jeder Auftrag im nächsten Lauf erneut beurteilt.</p>'
    )
    return _card(
        f"Korrekturen · Lauf {run_id}",
        intro + '<table><thead><tr><th>Auftrag</th><th>Prüfpunkt</th><th>Rohwarenstufe</th><th>Entscheidung</th><th>Status</th><th>Systemhinweis</th></tr></thead><tbody>' + table_rows + '</tbody></table>',
    )


def _test_cases_page(app: WebApplication, params: dict[str, list[str]]) -> str:
    rows = _read_semicolon_csv(app.test_cases_path)
    selected_order = params.get("order", [""])[0].strip()
    selected = next((row for row in rows if row.get("order_number") == selected_order), {})
    message = params.get("message", [""])[0]
    table_rows = "".join(
        f'<tr><td><a href="/test-cases?{urlencode({"order": row.get("order_number", "")})}">{html.escape(row.get("order_number", ""))}</a></td>'
        f'<td>{html.escape(row.get("expected_performance_status", ""))}</td><td>{html.escape(row.get("expected_reason_codes", ""))}</td>'
        f'<td>{html.escape(row.get("review_status", ""))}</td><td>{html.escape(row.get("professional_explanation", ""))}</td></tr>'
        for row in rows
    ) or '<tr><td colspan="5">Noch keine Testvorgaben vorhanden.</td></tr>'
    notice = f'<div class="notice">{html.escape(message)}</div>' if message else ""
    selected_codes = set(filter(None, selected.get("expected_reason_codes", "").split("|")))
    reason_choices = "".join(
        f'<label class="check"><input type="checkbox" name="expected_reason_codes" value="{html.escape(code)}" {"checked" if code in selected_codes else ""}> {html.escape(code)}</label>'
        for code in sorted(_known_reason_codes(app))
    )
    status_choices = "".join(
        f'<option value="{html.escape(status)}" {"selected" if selected.get("expected_performance_status") == status else ""}>{html.escape(status)}</option>'
        for status in sorted(PERFORMANCE_STATUSES)
    )
    def yes_no_select(name: str, label: str) -> str:
        current = selected.get(name, "").strip().upper()
        return f'<label>{html.escape(label)}<select name="{name}"><option value=""></option><option value="JA" {"selected" if current in {"JA", "YES"} else ""}>Ja</option><option value="NEIN" {"selected" if current in {"NEIN", "NO"} else ""}>Nein</option></select></label>'
    form = f'''{notice}<form method="post" action="/test-cases" class="form-grid compact">
<input type="hidden" name="csrf" value="{app.csrf_token}">
<label>Auftragsnummer<input name="order_number" required value="{html.escape(selected_order)}"></label>
<label>Erwartete Performancebewertung<select name="expected_performance_status"><option value=""></option>{status_choices}</select></label>
<div><span class="field-label">Erwartete Reason Codes</span><input type="hidden" name="expected_reason_codes" value=""><details class="multi-select"><summary>{html.escape(', '.join(sorted(selected_codes)) if selected_codes else 'Reason Codes auswählen')}</summary><div class="multi-select-options">{reason_choices}</div></details></div>
{yes_no_select("accepted_exception", "Akzeptierte Ausnahme")}
{yes_no_select("correction_required", "Erwartete Korrektur")}
<label>Fachliche Erklärung<textarea name="professional_explanation" rows="4">{html.escape(selected.get("professional_explanation", ""))}</textarea></label>
<label>Status<select name="review_status"><option value=""></option>{''.join(f'<option value="{status}" {"selected" if selected.get("review_status") == status else ""}>{status}</option>' for status in sorted(REVIEW_STATUSES))}</select></label>
<button class="primary">Testvorgabe lokal speichern</button></form>'''
    return _card("Testvorgaben", '<p class="hint">Bestätigte Fachfälle sichern erwartete Ergebnisse für künftige Testläufe.</p><table><thead><tr><th>Auftrag</th><th>Erwarteter Status</th><th>Reason Codes</th><th>Prüfstatus</th><th>Fachliche Erklärung</th></tr></thead><tbody>' + table_rows + '</tbody></table>') + _card("Testvorgabe bearbeiten", form)


def _documentation_page(app: WebApplication) -> str:
    path = app.root / "docs" / "RULES_AND_REVIEW_PROCESS.md"
    text = path.read_text(encoding="utf-8")
    # Bewusst einfache, sichere Darstellung: Originaltext wird vollständig escaped.
    return _card(
        "Regeln und fachlicher Prüfprozess",
        '<p><a href="/documentation/raw">Markdown-Dokument öffnen</a></p>'
        + f'<pre class="documentation">{html.escape(text)}</pre>',
    )


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
            if parsed.path == "/static/workflow.css":
                self._send((app.root / "src" / "sp_naka" / "web" / "workflow.css").read_text(encoding="utf-8"), content_type="text/css; charset=utf-8")
                return
            state = app.run_state()
            routes = {
                "/": ("dashboard", "Übersicht", lambda: _dashboard(app)),
                "/calculation": ("calculation", "Nachkalkulation", lambda: _calculation_page(app, params)),
                "/runs": ("runs", "Laufhistorie", lambda: _runs_page(app)),
                "/orders": ("orders", "Aufträge & Prüfung", lambda: _orders_page(app, params)),
                "/review": ("orders", "Aufträge & Prüfung", lambda: _orders_page(app, params, True)),
                "/corrections": ("orders", "Aufträge & Prüfung", lambda: _orders_page(app, {**params, "view": ["corrections"]})),
                "/test-cases": ("test-cases", "Testvorgaben", lambda: _test_cases_page(app, params)),
                "/order": ("orders", "Auftragsdetails", lambda: _order_detail(app, params)),
                "/parameters": ("parameters", "Parametrierung", lambda: _parameters_page(app, params.get("message", [""])[0])),
                "/documentation": ("documentation", "Dokumentation", lambda: _documentation_page(app)),
            }
            if parsed.path == "/documentation/raw":
                self._send((app.root / "docs" / "RULES_AND_REVIEW_PROCESS.md").read_text(encoding="utf-8"), content_type="text/plain; charset=utf-8")
                return
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
                elif self.path == "/calculation/clarification":
                    app.save_order_clarification(form)
                    self._redirect("/calculation?" + urlencode({
                        "dataset": form["dataset"][0],
                        "order": form["order_number"][0],
                        "message": "Bewertung gespeichert",
                    }))
                elif self.path == "/test-cases":
                    app.save_test_case(form)
                    self._redirect("/test-cases?" + urlencode({
                        "order": form["order_number"][0], "message": "Testvorgabe gespeichert"
                    }))
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

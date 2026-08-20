"""Read-only order view assembled from the available local CSV exports."""

from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path

from .errors import AnalysisError


ORDER_NUMBER = re.compile(r"[A-Za-z0-9._-]{1,40}")


def number(value: str | None) -> float | None:
    """Parse the German decimal representation used by the exports."""
    text = (value or "").strip().replace("\u00a0", "")
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        result = float(text)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def _rows(path: Path, field: str, value: str) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if field not in (reader.fieldnames or []):
            raise AnalysisError(f"{path.name}: Suchfeld fehlt: {field}")
        return [row for row in reader if (row.get(field) or "").strip() == value]


def _source_total(rows: list[dict[str, str]], field: str) -> float:
    return sum(abs(value) for row in rows if (value := number(row.get(field))) is not None)


def _production_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        stage = (row.get("Stufe") or row.get("Stufe Bezeichnung") or "Ohne Stufe").strip()
        current = grouped.setdefault(
            stage,
            {
                "stage": stage,
                "duration": 0.0,
                "machine_duration": 0.0,
                "employee_duration": 0.0,
                "quantity": 0.0,
                "cost": 0.0,
                "entries": 0,
                "extra_effort_entries": 0,
            },
        )
        current["entries"] = int(current["entries"]) + 1
        if (row.get("Mehraufwand Id") or "").strip():
            current["extra_effort_entries"] = int(current["extra_effort_entries"]) + 1
        for target, source in (
            ("duration", "Dauer"),
            ("machine_duration", "DauerMaschine"),
            ("employee_duration", "DauerMF"),
            ("quantity", "Menge"),
            ("cost", "Kosten"),
        ):
            value = number(row.get(source))
            if value is not None:
                current[target] = float(current[target]) + value
    for current in grouped.values():
        total_duration = float(current["duration"])
        current["performance"] = (
            float(current["quantity"]) / total_duration if total_duration > 0 else None
        )
    return sorted(grouped.values(), key=lambda item: str(item["stage"]))


def _reconstructed_direct_costs(
    manufacturing: list[dict[str, str]],
    raw_bookings: list[dict[str, str]],
    invoice_controls: list[dict[str, str]],
    cost_bookings: list[dict[str, str]],
) -> float:
    """Reconstruct only costs represented by the supplied detail exports.

    Raw-material bookings take precedence over manufacturing-material values for
    the same article. Invoice-control and cost-object bookings are separate
    sources and are therefore added. This is deliberately not presented as the
    official proALPHA individual-cost total.
    """
    fm: defaultdict[str, float] = defaultdict(float)
    rw: defaultdict[str, float] = defaultdict(float)
    for row in manufacturing:
        article = (row.get("Artikel") or "").strip().upper()
        value = number(row.get("Materialwert"))
        if article and value is not None:
            fm[article] += max(value, 0.0)
    for row in raw_bookings:
        article = (row.get("Artikel") or "").strip().upper()
        value = number(row.get("WertMat"))
        if article and value is not None:
            rw[article] += value
    article_total = sum(abs(rw[article]) if article in rw else fm[article] for article in set(fm) | set(rw))
    return (
        article_total
        + _source_total(invoice_controls, "WarenwertEUR")
        + _source_total(cost_bookings, "Betrag")
    )


def load_order_calculation(source_dir: Path, order_number: str) -> dict[str, object]:
    """Load one order without modifying any source file."""
    order = order_number.strip()
    if not ORDER_NUMBER.fullmatch(order):
        raise AnalysisError("Die Auftragsnummer enthält unzulässige Zeichen.")
    source = source_dir.expanduser().resolve()
    if not source.is_dir():
        raise AnalysisError(f"Datenverzeichnis nicht gefunden: {source}")

    headers = _rows(source / "Auftragskopf.csv", "BelegNummer", order)
    if not headers:
        raise AnalysisError(f"Auftrag {order} wurde in {source.name} nicht gefunden.")
    if len(headers) != 1:
        raise AnalysisError(f"Auftrag {order} ist im Auftragskopf nicht eindeutig.")
    header = headers[0]
    header_key = (header.get("BelegKopfKey") or "").strip()

    positions = _rows(source / "VertriebsPositionen.csv", "BelegKopfKey", header_key)
    planning = _rows(source / "Planung.csv", "AuftragNr", order)
    production = _rows(source / "ProdZeiten.csv", "Auftrag", order)
    manufacturing = _rows(source / "Fertigungsmaterial.csv", "Auftrag", order)
    raw_positions = _rows(source / "RohwarenPos.csv", "BelegNummer", order)
    raw_bookings = _rows(source / "RW_Buchungen.csv", "BelegNummer", order)
    invoice_controls = _rows(source / "Rechnungskontrollen.csv", "Traeger", order)
    cost_bookings = _rows(source / "KTRBuchungenKI.csv", "KostenTraeger", order)
    billing = _rows(source / "Faktura.csv", "Auftrag", order)

    revenue = number(header.get("Erlöse"))
    cost = number(header.get("Kosten"))
    result = revenue - cost if revenue is not None and cost is not None else None
    margin_rate = result / abs(revenue) if result is not None and revenue not in (None, 0) else None
    production_detail_available = any(abs(number(row.get("Kosten")) or 0.0) > 0.000001 for row in production)

    die_forms = sorted(
        {
            value
            for row in planning
            if (value := (row.get("STANZFORM") or "").strip())
        }
    )
    direct_costs = _reconstructed_direct_costs(
        manufacturing, raw_bookings, invoice_controls, cost_bookings
    )
    limitations = [
        "Fixe und variable VV-/Materialzuschläge sind in den gelieferten CSV-Dateien nicht enthalten.",
        "Lagerkosten und Palettenwerte sind nicht enthalten.",
    ]
    if production and not production_detail_available:
        limitations.append(
            "ProdZeiten.Kosten enthält für diesen Auftrag ausschließlich 0. "
            "Produktionszeiten und Mengen sind vorhanden, Stundensätze wurden nicht geliefert."
        )
    elif not production:
        limitations.append("Für diesen Auftrag wurden keine Produktionszeitmeldungen geliefert.")

    return {
        "source_dir": source,
        "order_number": order,
        "header": header,
        "positions": positions,
        "planning": planning,
        "production": production,
        "production_summary": _production_summary(production),
        "manufacturing_material": manufacturing,
        "raw_positions": raw_positions,
        "raw_bookings": raw_bookings,
        "invoice_controls": invoice_controls,
        "cost_bookings": cost_bookings,
        "billing": billing,
        "revenue": revenue,
        "cost": cost,
        "result": result,
        "margin_rate": margin_rate,
        "die_forms": die_forms,
        "production_detail_available": production_detail_available,
        "production_cost_from_rows": _source_total(production, "Kosten"),
        "reconstructed_direct_costs": direct_costs,
        "source_totals": {
            "manufacturing_material": _source_total(manufacturing, "Materialwert"),
            "raw_bookings": _source_total(raw_bookings, "WertMat"),
            "invoice_controls": _source_total(invoice_controls, "WarenwertEUR"),
            "cost_bookings": _source_total(cost_bookings, "Betrag"),
        },
        "limitations": limitations,
    }

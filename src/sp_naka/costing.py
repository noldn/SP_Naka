"""Nachvollziehbare Istkostenabstimmung und theoretische Sollkosten."""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

from .errors import AnalysisError


RAW_GROUPS = {"01", "02", "03"}
MINIMUM_IDEAL_PEERS = 5
LAGER_COST_TYPE = "250950"
FREIGHT_COST_TYPES = {"7300", "7310", "7315"}
DELIVERY_TOLERANCE = 0.10
BILLING_TOLERANCE = 0.10
COST_REQUIRED_FILES = {
    "Auftragskopf.csv", "VertriebsPositionen.csv", "ProdZeiten.csv",
    "Fertigungsmaterial.csv", "RohwarenPos.csv", "RW_Buchungen.csv",
    "Rechnungskontrollen.csv", "KTRBuchungenKI.csv", "Zuschlaege.csv",
}
COST_FIELDS = [
    "run_id", "order_number", "reconciliation_status", "official_cost_eur",
    "reconstructed_cost_eur", "reconciliation_difference_eur",
    "reconciliation_difference_rate", "actual_material_cost_eur",
    "production_cost_eur", "individual_cost_eur", "net_cost_eur",
    "invoice_cost_eur", "ktr_cost_eur", "lager_cost_eur",
    "material_surcharge_eur", "vv_surcharge_eur", "fixed_surcharge_eur",
    "theoretical_invoice_cost_eur",
    "theoretical_total_cost_eur", "theoretical_result_eur", "theoretical_complete",
    "price_critical", "afterproduction_detected", "manual_review_required",
    "order_closed", "delivery_status", "delivery_deviation_count",
    "billing_status", "theoretical_position_value_eur", "invoiced_value_eur",
    "credited_value_eur", "billed_revenue_eur", "billing_difference_eur",
    "billing_difference_rate", "credit_note_present", "special_cost_value_eur",
    "reason_codes", "reason_explanation",
]


def _number(value: str | None) -> float | None:
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


def _date(value: str | None) -> date | None:
    for pattern in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime((value or "").strip(), pattern).date()
        except ValueError:
            pass
    return None


def is_afterproduction(description: str | None) -> bool:
    """Recognise the agreed prefix and common spelling variants."""
    return "nachprod" in (description or "").casefold()


def _net(rows: list[dict[str, str]], field: str) -> float:
    return sum(value for row in rows if (value := _number(row.get(field))) is not None)


def _positive_cost(rows: list[dict[str, str]], field: str) -> float:
    return abs(_net(rows, field))


def _group(row: dict[str, str]) -> str:
    return (row.get("ArtikelGruppe") or "").strip().zfill(2)


def _article(row: dict[str, str]) -> str:
    return (row.get("Artikel") or "").strip().upper()


def _fulfillment_assessment(
    header: dict[str, str],
    positions: list[dict[str, str]],
    billing: list[dict[str, str]],
) -> dict[str, object]:
    closed = (header.get("offen") or "").strip() == "0"
    bill = billing[0] if len(billing) == 1 else {}
    invoice = _number(bill.get("Summe_Rechnung_EUR"))
    credit = _number(bill.get("Summe_Gutschrift_EUR")) or 0.0
    billed_revenue = _number(bill.get("Erloes_EUR"))
    credit_present = (_number(bill.get("Anzahl_Gutschriften")) or 0.0) > 0 or abs(credit) > 0.005
    theoretical = 0.0
    special_cost = 0.0
    delivery_deviations: list[dict[str, object]] = []
    priced_positions = 0
    for row in positions:
        price = _number(row.get("EinzelpreismZuAbschl"))
        if price is None:
            price = _number(row.get("Einzelpreis"))
        factor = _number(row.get("Preiseinheitsfaktor")) or 1.0
        quantity = _number(row.get("Menge")) or 0.0
        if price is None or price <= 0 or factor <= 0 or quantity <= 0:
            continue
        priced_positions += 1
        position_value = quantity * price / factor
        theoretical += position_value
        group_code = (row.get("ArtikelGruppe") or "").strip().zfill(2)
        group_name = (row.get("ArtikelGruppeBez") or "").strip().casefold()
        value_position = (row.get("WertPosition") or "").strip() == "1"
        preproduction = group_code == "13" or "vorfertigung" in group_name
        special = group_code == "30" or "sonderkosten" in group_name
        if special:
            special_cost += position_value
        if not closed or value_position or preproduction:
            continue
        delivered = _number(row.get("gelieferte_Menge")) or 0.0
        ratio = delivered / quantity
        lower_violation = ratio < 1.0 - DELIVERY_TOLERANCE and not credit_present
        upper_violation = ratio > 1.0 + DELIVERY_TOLERANCE
        if lower_violation or upper_violation:
            delivery_deviations.append({
                "position": (row.get("PositionsNr") or "").strip(),
                "article": (row.get("Artikel") or "").strip(),
                "ordered": quantity,
                "delivered": delivered,
                "ratio": ratio,
            })
    theoretical = _round(theoretical)
    special_cost = _round(special_cost)
    billing_difference = (
        billed_revenue - theoretical
        if billed_revenue is not None and theoretical > 0 else None
    )
    billing_difference_rate = (
        abs(billing_difference) / abs(theoretical)
        if billing_difference is not None and theoretical else None
    )
    invoice_ratio = invoice / theoretical if invoice is not None and theoretical > 0 else None
    if not closed:
        delivery_status = "OFFENER_AUFTRAG"
        billing_status = "OFFENER_AUFTRAG"
    else:
        delivery_status = "PRUEFEN" if delivery_deviations else "OK"
        if priced_positions == 0:
            billing_status = "NICHT_RELEVANT"
        elif not bill or invoice is None:
            billing_status = "PRUEFEN"
        elif invoice_ratio is not None and not (
            1.0 - BILLING_TOLERANCE <= invoice_ratio <= 1.0 + BILLING_TOLERANCE
        ):
            billing_status = "PRUEFEN"
        else:
            billing_status = "OK_MIT_GUTSCHRIFT" if credit_present else "OK"
    return {
        "order_closed": closed,
        "delivery_status": delivery_status,
        "delivery_deviations": delivery_deviations,
        "delivery_deviation_count": len(delivery_deviations),
        "billing_status": billing_status,
        "theoretical_position_value": theoretical,
        "invoiced_value": invoice,
        "credited_value": credit,
        "billed_revenue": billed_revenue,
        "billing_difference": billing_difference,
        "billing_difference_rate": billing_difference_rate,
        "credit_note_present": credit_present,
        "special_cost_value": special_cost,
        "priced_position_count": priced_positions,
        "billing_row_available": bool(bill),
    }


def _round(value: float) -> float:
    return round(value + 0.0, 2)


def _percentile_75(values: list[float]) -> float:
    """Inclusive, linearly interpolated 75th percentile."""
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * 0.75
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def _read(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


@lru_cache(maxsize=4096)
def load_surcharges(source_dir: Path, observed: date | None) -> dict[str, float | str]:
    """Load the two valid rate rows for hourly-rate variant 2."""
    path = source_dir / "Zuschlaege.csv"
    if not path.is_file():
        raise AnalysisError(f"Zuschlagsdatei fehlt: {path}")
    if observed is None:
        raise AnalysisError("BelegDatum fehlt oder ist ungültig; Zuschläge sind nicht bestimmbar.")
    selected: dict[str, dict[str, str]] = {}
    for row in _read(path):
        kind = (row.get("Zuschlagsart") or "").strip()
        if (row.get("Stundensatz") or "").strip() != "2" or kind == "Nichtdefiniert":
            continue
        start, end = _date(row.get("GueltigVon")), _date(row.get("GueltigBis"))
        if start is None or end is None or start > end:
            raise AnalysisError(f"{path.name}: ungültiger Gültigkeitszeitraum für {kind}.")
        if start <= observed <= end:
            if kind in selected:
                raise AnalysisError(f"{path.name}: überlappende Zuschläge für {kind} am {observed}.")
            selected[kind] = row
    missing = {"MatGemeinkosten", "VVZuschlag"}.difference(selected)
    if missing:
        raise AnalysisError(
            f"{path.name}: kein gültiger Zuschlag für {', '.join(sorted(missing))} am {observed}."
        )
    material = selected["MatGemeinkosten"]
    vv = selected["VVZuschlag"]
    material_rate = _number(material.get("ZuschlagVariabel"))
    fixed = _number(vv.get("ZuschlagFix"))
    vv_rate = _number(vv.get("ZuschlagVariabel"))
    if material_rate is None or fixed is None or vv_rate is None:
        raise AnalysisError(f"{path.name}: Zuschlagswert ist nicht numerisch.")
    return {
        "material_rate": material_rate,
        "fixed": fixed,
        "vv_rate": vv_rate,
        "valid_from": material.get("GueltigVon", ""),
        "valid_until": material.get("GueltigBis", ""),
    }


def _actual_material(
    manufacturing: list[dict[str, str]], raw_bookings: list[dict[str, str]]
) -> tuple[float, float, float, dict[str, float], dict[str, float]]:
    """Use RW per article, with FM fallback, and never count an article twice."""
    fm: defaultdict[str, float] = defaultdict(float)
    rw: defaultdict[str, float] = defaultdict(float)
    fm_groups: dict[str, str] = {}
    rw_groups: dict[str, str] = {}
    for row in manufacturing:
        article = _article(row)
        value = _number(row.get("Materialwert"))
        if article and value is not None:
            fm[article] += value
            fm_groups[article] = _group(row)
    for row in raw_bookings:
        article = _article(row)
        value = _number(row.get("WertMat"))
        if article and value is not None:
            rw[article] += value
            rw_groups[article] = _group(row)
    costs = {
        # RW-Verbräuche werden negativ, Rückbuchungen/Korrekturen positiv
        # geliefert. Für die Kostenwirkung wird deshalb das Vorzeichen einmal
        # umgedreht; abs() würde Korrekturen fälschlich zu Kosten addieren.
        article: -rw[article] if article in rw else max(fm[article], 0.0)
        for article in set(fm).union(rw)
    }
    groups = {**fm_groups, **rw_groups}
    raw_actual = sum(costs[a] for a in costs if groups.get(a) in RAW_GROUPS)
    other_actual = sum(costs.values()) - raw_actual
    eligible_base = abs(
        sum(
            _number(row.get("WertMat")) or 0.0
            for row in raw_bookings
            if _group(row) in RAW_GROUPS
        )
    )
    return sum(costs.values()), raw_actual, other_actual, costs, {
        article: float(value) for article, value in rw.items()
    } | {"__eligible_base__": eligible_base}


def _theoretical_material(
    manufacturing: list[dict[str, str]],
    raw_positions: list[dict[str, str]],
    raw_bookings: list[dict[str, str]],
    actual_costs: dict[str, float],
) -> dict[str, object]:
    planned: defaultdict[str, float] = defaultdict(float)
    planned_group: dict[str, str] = {}
    for row in raw_positions:
        article = _article(row)
        quantity = _number(row.get("Menge"))
        if article and quantity is not None and quantity > 0:
            planned[article] += quantity
            planned_group[article] = _group(row)

    booked_quantity: defaultdict[str, float] = defaultdict(float)
    booked_value: defaultdict[str, float] = defaultdict(float)
    booked_group: dict[str, str] = {}
    for row in raw_bookings:
        article = _article(row)
        if not article:
            continue
        booked_quantity[article] += _number(row.get("Menge")) or 0.0
        booked_value[article] += _number(row.get("WertMat")) or 0.0
        booked_group[article] = _group(row)

    exact_planned = {article for article in planned if abs(booked_quantity[article]) > 1e-12}
    unmatched_booked = set(booked_quantity).difference(exact_planned)
    group_quantity: defaultdict[str, float] = defaultdict(float)
    group_value: defaultdict[str, float] = defaultdict(float)
    for article in unmatched_booked:
        group = booked_group.get(article, "")
        if group:
            group_quantity[group] += booked_quantity[article]
            group_value[group] += booked_value[article]

    details: list[dict[str, object]] = []
    used_planned: set[str] = set()
    consumed_actual_articles: set[str] = set()
    missing: list[str] = []
    raw_total = 0.0
    eligible_total = 0.0
    for article, quantity in sorted(planned.items()):
        group = planned_group.get(article, "")
        price = None
        match = "NOT_AVAILABLE"
        if article in exact_planned:
            price = abs(booked_value[article]) / abs(booked_quantity[article])
            match = "EXACT_ARTICLE"
            consumed_actual_articles.add(article)
        elif group and abs(group_quantity[group]) > 1e-12:
            price = abs(group_value[group]) / abs(group_quantity[group])
            match = "ARTICLE_GROUP_ALTERNATIVE"
            consumed_actual_articles.update(
                booked_article for booked_article in unmatched_booked
                if booked_group.get(booked_article) == group
            )
        if price is None:
            fallback = actual_costs.get(article)
            if fallback is not None:
                cost = fallback
                match = "ACTUAL_COST_FALLBACK"
                consumed_actual_articles.add(article)
            else:
                cost = 0.0
                missing.append(article)
        else:
            cost = quantity * price
        used_planned.add(article)
        raw_total += cost
        if group in RAW_GROUPS:
            eligible_total += cost
        details.append({
            "article": article,
            "group": group,
            "planned_quantity": quantity,
            "unit_price": price,
            "match_level": match,
            "theoretical_cost": cost,
        })

    # Materials not represented by a raw-material target remain at actual cost.
    actual_other = 0.0
    for article, cost in actual_costs.items():
        if article not in used_planned and article not in consumed_actual_articles:
            actual_other += cost
    return {
        "raw_cost": raw_total,
        "other_actual_cost": actual_other,
        "total": raw_total + actual_other,
        "eligible_base": eligible_total,
        "complete": not missing,
        "missing_articles": missing,
        "details": details,
    }


def _identity_from_invoice(value: str) -> str:
    text = value.strip().upper()
    return text.split("|", 1)[-1] if "|" in text else text


@lru_cache(maxsize=4)
def _ideal_profiles_cached(
    source_text: str,
    header_mtime: int,
    production_mtime: int,
    sales_mtime: int,
    invoice_mtime: int,
    excluded_orders: tuple[str, ...],
) -> dict[tuple[str, str, str, str], list[tuple[str, float]]]:
    del header_mtime, production_mtime, sales_mtime, invoice_mtime
    source = Path(source_text)
    headers = _read(source / "Auftragskopf.csv")
    header_to_order: dict[str, str] = {}
    excluded: set[str] = set(excluded_orders)
    for row in headers:
        order = (row.get("BelegNummer") or "").strip()
        header_to_order[(row.get("BelegKopfKey") or "").strip()] = order
        if is_afterproduction(row.get("Zusatztext")):
            excluded.add(order)
    wms: defaultdict[str, set[str]] = defaultdict(set)
    for row in _read(source / "VertriebsPositionen.csv"):
        order = header_to_order.get((row.get("BelegKopfKey") or "").strip(), "")
        value = (row.get("Muster") or "").strip().upper()
        if order and value.startswith("WM"):
            wms[order].add(value)
    wss: defaultdict[str, set[str]] = defaultdict(set)
    for row in _read(source / "Rechnungskontrollen.csv"):
        order = (row.get("Traeger") or "").strip()
        value = _identity_from_invoice(row.get("Artikel Key") or "")
        if order and value.startswith("WS"):
            wss[order].add(value)

    grouped: defaultdict[tuple[str, str, str], dict[str, float | bool]] = defaultdict(
        lambda: {"quantity": 0.0, "duration": 0.0, "extra": False}
    )
    for row in _read(source / "ProdZeiten.csv"):
        order = (row.get("Auftrag") or "").strip()
        stage = (row.get("Stufe") or row.get("Stufe Bezeichnung") or "").strip()
        machine = (row.get("KSTNrKurz") or row.get("KSTKurz") or "").strip()
        current = grouped[(order, stage, machine)]
        current["quantity"] = float(current["quantity"]) + (_number(row.get("Menge")) or 0.0)
        current["duration"] = float(current["duration"]) + (_number(row.get("Dauer")) or 0.0)
        current["extra"] = bool(current["extra"]) or bool((row.get("Mehraufwand Id") or "").strip())
    profiles: defaultdict[tuple[str, str, str, str], list[tuple[str, float]]] = defaultdict(list)
    for (order, stage, machine), values in grouped.items():
        quantity, duration = float(values["quantity"]), float(values["duration"])
        if order in excluded or values["extra"] or quantity <= 0 or duration <= 0 or not stage or not machine:
            continue
        performance = quantity / duration
        if len(wms[order]) == 1:
            profiles[("WM", next(iter(wms[order])), stage, machine)].append((order, performance))
        if len(wss[order]) == 1:
            profiles[("WS", next(iter(wss[order])), stage, machine)].append((order, performance))
        profiles[("MACHINE", "", stage, machine)].append((order, performance))
    return dict(profiles)


def ideal_profiles(
    source_dir: Path, excluded_orders: set[str] | None = None
) -> dict[tuple[str, str, str, str], list[tuple[str, float]]]:
    source = source_dir.resolve()
    paths = [
        source / "Auftragskopf.csv", source / "ProdZeiten.csv",
        source / "VertriebsPositionen.csv", source / "Rechnungskontrollen.csv",
    ]
    if not all(path.is_file() for path in paths):
        return {}
    return _ideal_profiles_cached(
        str(source), *(path.stat().st_mtime_ns for path in paths),
        tuple(sorted(excluded_orders or set())),
    )


def confirmed_data_error_orders(path: Path | None) -> set[str]:
    if path is None or not path.is_file():
        return set()
    return {
        (row.get("order_number") or "").strip()
        for row in _read(path)
        if (row.get("professional_assessment") or "").strip() == "DATENFEHLER"
        and (row.get("review_status") or "").strip() == "ABGESCHLOSSEN"
    }


def _order_identities(positions: list[dict[str, str]], invoices: list[dict[str, str]]) -> tuple[str, str]:
    wms = {(row.get("Muster") or "").strip().upper() for row in positions}
    wms = {value for value in wms if value.startswith("WM")}
    wss = {_identity_from_invoice(row.get("Artikel Key") or "") for row in invoices}
    wss = {value for value in wss if value.startswith("WS")}
    return (next(iter(wms)) if len(wms) == 1 else "", next(iter(wss)) if len(wss) == 1 else "")


def _theoretical_production(
    order: str,
    rows: list[dict[str, str]],
    positions: list[dict[str, str]],
    invoices: list[dict[str, str]],
    profiles: dict[tuple[str, str, str, str], list[tuple[str, float]]],
) -> dict[str, object]:
    wm, ws = _order_identities(positions, invoices)
    grouped: defaultdict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"quantity": 0.0, "duration": 0.0, "cost": 0.0}
    )
    for row in rows:
        stage = (row.get("Stufe") or row.get("Stufe Bezeichnung") or "").strip()
        machine = (row.get("KSTNrKurz") or row.get("KSTKurz") or "").strip()
        current = grouped[(stage, machine)]
        current["quantity"] += _number(row.get("Menge")) or 0.0
        current["duration"] += _number(row.get("Dauer")) or 0.0
        current["cost"] += _number(row.get("Kosten")) or 0.0
    details: list[dict[str, object]] = []
    actual_total = theoretical_total = 0.0
    for (stage, machine), values in sorted(grouped.items()):
        quantity, duration, actual_cost = values["quantity"], values["duration"], values["cost"]
        actual_total += actual_cost
        candidates = []
        if wm:
            candidates.append(("SAME_WM_MACHINE_STAGE", ("WM", wm, stage, machine)))
        if ws:
            candidates.append(("SAME_WS_MACHINE_STAGE", ("WS", ws, stage, machine)))
        candidates.append(("SAME_MACHINE_STAGE", ("MACHINE", "", stage, machine)))
        reference_level, reference_values = "ACTUAL_FALLBACK", []
        for level, key in candidates:
            usable = [performance for peer_order, performance in profiles.get(key, []) if peer_order != order]
            if len(usable) >= MINIMUM_IDEAL_PEERS:
                reference_level, reference_values = level, usable
                break
        ideal = _percentile_75(reference_values) if reference_values else None
        actual_performance = quantity / duration if quantity > 0 and duration > 0 else None
        if ideal and duration > 0 and quantity > 0 and actual_cost > 0:
            ideal_duration = min(duration, quantity / ideal)
            theoretical_cost = ideal_duration * (actual_cost / duration)
        else:
            ideal_duration = duration
            theoretical_cost = actual_cost
        theoretical_total += theoretical_cost
        details.append({
            "stage": stage or "Ohne Stufe",
            "machine": machine or "Ohne Maschine",
            "quantity": quantity,
            "actual_duration": duration,
            "actual_performance": actual_performance,
            "reference_level": reference_level,
            "reference_count": len(reference_values),
            "ideal_performance": ideal,
            "theoretical_duration": ideal_duration,
            "actual_cost": actual_cost,
            "theoretical_cost": theoretical_cost,
        })
    return {"actual": actual_total, "theoretical": theoretical_total, "details": details}


def assess_order_costs(
    source_dir: Path,
    header: dict[str, str],
    positions: list[dict[str, str]],
    production: list[dict[str, str]],
    manufacturing: list[dict[str, str]],
    raw_positions: list[dict[str, str]],
    raw_bookings: list[dict[str, str]],
    invoice_controls: list[dict[str, str]],
    cost_bookings: list[dict[str, str]],
    reference_dir: Path | None = None,
    reference_profiles: dict[tuple[str, str, str, str], list[tuple[str, float]]] | None = None,
    billing: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    order = (header.get("BelegNummer") or "").strip()
    official = _number(header.get("Kosten"))
    revenue = _number(header.get("Erlöse"))
    rates = load_surcharges(source_dir, _date(header.get("BelegDatum")))
    material, raw_actual, other_material, article_costs, rw_values = _actual_material(
        manufacturing, raw_bookings
    )
    eligible_actual = float(rw_values.pop("__eligible_base__", 0.0))
    production_cost = _net(production, "Kosten")
    invoice_cost = _positive_cost(invoice_controls, "WarenwertEUR")
    ktr_cost = _net(cost_bookings, "Betrag")
    lager_cost = _net([r for r in cost_bookings if (r.get("TrKoArt") or "").strip() == LAGER_COST_TYPE], "Betrag")
    freight_cost = _net([r for r in cost_bookings if (r.get("TrKoArt") or "").strip() in FREIGHT_COST_TYPES], "Betrag")
    other_ktr = ktr_cost - lager_cost - freight_cost
    fixed = _round(float(rates["fixed"]))
    material_surcharge = _round(eligible_actual * float(rates["material_rate"]) / 100.0)
    vv_surcharge = _round(production_cost * float(rates["vv_rate"]) / 100.0)
    individual_cost = material + invoice_cost + ktr_cost
    net_cost = production_cost + individual_cost
    reconstructed = net_cost + fixed + material_surcharge + vv_surcharge
    difference = reconstructed - official if official is not None else None
    difference_rate = abs(difference) / abs(official) if difference is not None and official not in (None, 0) else None
    if difference is None:
        reconciliation = "NICHT_BEWERTET"
    elif abs(difference) > 500 and difference_rate is not None and difference_rate > 0.05:
        reconciliation = "KRITISCH"
    elif abs(difference) > 100 and difference_rate is not None and difference_rate > 0.02:
        reconciliation = "WARNUNG"
    else:
        reconciliation = "OK"

    theory_material = _theoretical_material(manufacturing, raw_positions, raw_bookings, article_costs)
    profiles = reference_profiles if reference_profiles is not None else ideal_profiles(reference_dir or source_dir)
    theory_production = _theoretical_production(order, production, positions, invoice_controls, profiles)
    theoretical_mgk = _round(float(theory_material["eligible_base"]) * float(rates["material_rate"]) / 100.0)
    theoretical_vv = _round(float(theory_production["theoretical"]) * float(rates["vv_rate"]) / 100.0)
    theoretical_total = (
        float(theory_material["total"]) + float(theory_production["theoretical"])
        + ktr_cost + fixed + theoretical_mgk + theoretical_vv
    )
    theoretical_result = revenue - theoretical_total if revenue is not None else None
    complete = bool(theory_material["complete"])
    price_critical = bool(complete and theoretical_result is not None and theoretical_result <= 0)
    afterproduction = is_afterproduction(header.get("Zusatztext"))
    fulfillment = _fulfillment_assessment(header, positions, billing or [])
    reason_codes = []
    if reconciliation in {"WARNUNG", "KRITISCH"}:
        reason_codes.append(f"KOSTENABSTIMMUNG_{reconciliation}")
    if afterproduction:
        reason_codes.append("NACHPRODUKTION_ERKANNT")
    if price_critical:
        reason_codes.append("PREIS_KRITISCH")
    if not complete:
        reason_codes.append("THEORETISCHE_KOSTEN_UNVOLLSTAENDIG")
    if fulfillment["delivery_status"] == "PRUEFEN":
        reason_codes.append("LIEFERMENGE_AUSSERHALB_TOLERANZ")
    if fulfillment["credit_note_present"] and fulfillment["order_closed"]:
        reason_codes.append("GUTSCHRIFT_ERKANNT")
    if fulfillment["billing_status"] == "PRUEFEN":
        reason_codes.append("FAKTURAWERT_AUSSERHALB_TOLERANZ")
        if float(fulfillment["special_cost_value"]) > 0:
            reason_codes.append("SONDERKOSTEN_FAKTURA_PRUEFEN")
    return {
        "actual_material_cost": material,
        "actual_raw_material_cost": raw_actual,
        "actual_other_material_cost": other_material,
        "production_cost": production_cost,
        "invoice_cost": invoice_cost,
        "ktr_cost": ktr_cost,
        "lager_cost": lager_cost,
        "freight_cost": freight_cost,
        "other_ktr_cost": other_ktr,
        "individual_cost": individual_cost,
        "net_cost": net_cost,
        "material_surcharge_base": eligible_actual,
        "material_surcharge_rate": rates["material_rate"],
        "material_surcharge": material_surcharge,
        "vv_surcharge_rate": rates["vv_rate"],
        "vv_surcharge": vv_surcharge,
        "fixed_surcharge": fixed,
        "surcharge_validity": f"{rates['valid_from']}–{rates['valid_until']}",
        "reconstructed_cost": reconstructed,
        "official_cost": official,
        "reconciliation_difference": difference,
        "reconciliation_difference_rate": difference_rate,
        "reconciliation_status": reconciliation,
        "afterproduction_detected": afterproduction,
        "theoretical_material_cost": theory_material["total"],
        "theoretical_production_cost": theory_production["theoretical"],
        "theoretical_material_surcharge": theoretical_mgk,
        "theoretical_vv_surcharge": theoretical_vv,
        "theoretical_invoice_cost": 0.0,
        "theoretical_total_cost": theoretical_total,
        "theoretical_result": theoretical_result,
        "theoretical_complete": complete,
        "price_critical": price_critical,
        "theoretical_material_details": theory_material["details"],
        "theoretical_production_details": theory_production["details"],
        "missing_theoretical_articles": theory_material["missing_articles"],
        **fulfillment,
        "reason_codes": reason_codes,
    }


def cost_sources_available(source_dir: Path) -> bool:
    return all((source_dir / name).is_file() for name in COST_REQUIRED_FILES)


def _by_order(rows: list[dict[str, str]], field: str) -> dict[str, list[dict[str, str]]]:
    result: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        order = (row.get(field) or "").strip()
        if order:
            result[order].append(row)
    return dict(result)


def analyze_costs(
    source_dir: Path,
    reference_dir: Path,
    run_id: str,
    order_clarifications_path: Path | None = None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Calculate cost assessments for a complete analysis run."""
    source = source_dir.resolve()
    reference = reference_dir.resolve()
    if not cost_sources_available(source):
        missing = sorted(name for name in COST_REQUIRED_FILES if not (source / name).is_file())
        raise AnalysisError(f"Kostenanalyse: Quelldateien fehlen: {', '.join(missing)}")
    headers = _read(source / "Auftragskopf.csv")
    positions_by_header = _by_order(_read(source / "VertriebsPositionen.csv"), "BelegKopfKey")
    sources = {
        "production": _by_order(_read(source / "ProdZeiten.csv"), "Auftrag"),
        "manufacturing": _by_order(_read(source / "Fertigungsmaterial.csv"), "Auftrag"),
        "raw_positions": _by_order(_read(source / "RohwarenPos.csv"), "BelegNummer"),
        "raw_bookings": _by_order(_read(source / "RW_Buchungen.csv"), "BelegNummer"),
        "invoices": _by_order(_read(source / "Rechnungskontrollen.csv"), "Traeger"),
        "ktr": _by_order(_read(source / "KTRBuchungenKI.csv"), "KostenTraeger"),
        "billing": _by_order(_read(source / "Faktura.csv"), "Auftrag") if (source / "Faktura.csv").is_file() else {},
    }
    # Build and cache the reference once before iterating over orders.
    excluded_data_errors = confirmed_data_error_orders(order_clarifications_path)
    profiles = ideal_profiles(reference, excluded_data_errors)
    output: list[dict[str, object]] = []
    statuses: defaultdict[str, int] = defaultdict(int)
    for header in headers:
        order = (header.get("BelegNummer") or "").strip()
        assessment = assess_order_costs(
            source,
            header,
            positions_by_header.get((header.get("BelegKopfKey") or "").strip(), []),
            sources["production"].get(order, []),
            sources["manufacturing"].get(order, []),
            sources["raw_positions"].get(order, []),
            sources["raw_bookings"].get(order, []),
            sources["invoices"].get(order, []),
            sources["ktr"].get(order, []),
            reference,
            profiles,
            sources["billing"].get(order, []),
        )
        codes = list(assessment["reason_codes"])
        explanations = []
        if assessment["reconciliation_status"] in {"WARNUNG", "KRITISCH"}:
            explanations.append(
                "Kosten Ist aus dem Auftragskopf und Kosten errechnet weichen oberhalb der absoluten und relativen Prüfschwelle voneinander ab. Ursache kann ein veralteter/unvollständiger Istkostenstand oder ein Datenfehler in den errechneten Kosten sein."
            )
        if assessment["reconciliation_status"] == "KRITISCH":
            explanations.append("Die massive Kostenabweichung ist korrekturpflichtig und muss fachlich einer der beiden Kostenquellen zugeordnet werden.")
        if assessment["afterproduction_detected"]:
            explanations.append("Der Zusatztext kennzeichnet den Auftrag als Nachproduktion.")
        if assessment["price_critical"]:
            explanations.append("Auch mit Sollmaterial und Idealleistung bleibt das theoretische Ergebnis negativ oder null; der Preis ist ein kritischer Faktor.")
        if not assessment["theoretical_complete"]:
            explanations.append("Mindestens einem Sollmaterial konnte kein Preis belastbar zugeordnet werden.")
        if assessment["delivery_status"] == "PRUEFEN":
            explanations.append(
                f'{assessment["delivery_deviation_count"]} fakturierbare Lieferposition(en) liegen außerhalb der zulässigen Liefermenge von ±10 %. Vorfertigungsteile, Wertpositionen und Positionen ohne Preis sind ausgenommen.'
            )
        if assessment["credit_note_present"]:
            explanations.append(
                f'Gutschrift über {float(assessment["credited_value"]):.2f} EUR erkannt; eine geringere Liefer- oder Nettoerlösmenge kann dadurch fachlich erklärt sein.'
            )
        if assessment["billing_status"] == "PRUEFEN":
            explanations.append(
                "Die Rechnungssumme liegt außerhalb von ±10 % des theoretischen Positionswerts oder die Fakturazusammenfassung fehlt. Positionen ohne Preis sind nicht relevant."
            )
        if "SONDERKOSTEN_FAKTURA_PRUEFEN" in codes:
            explanations.append(
                "Der Auftrag enthält bepreiste Sonderkosten. Wegen der nur je Auftrag aggregierten Fakturaquelle ist zu prüfen, ob diese vollständig verrechnet wurden."
            )
        construction_data_order = (header.get("AuftragsArt") or "").strip().upper() in {"M", "B"}
        manual = assessment["reconciliation_status"] in {"WARNUNG", "KRITISCH"} or not bool(
            assessment["theoretical_complete"]
        ) or bool(
            assessment["price_critical"]
            and not assessment["afterproduction_detected"]
            and not construction_data_order
        )
        manual |= assessment["delivery_status"] == "PRUEFEN" or assessment["billing_status"] == "PRUEFEN"
        statuses[str(assessment["reconciliation_status"])] += 1
        output.append({
            "run_id": run_id,
            "order_number": order,
            "reconciliation_status": assessment["reconciliation_status"],
            "official_cost_eur": assessment["official_cost"],
            "reconstructed_cost_eur": assessment["reconstructed_cost"],
            "reconciliation_difference_eur": assessment["reconciliation_difference"],
            "reconciliation_difference_rate": assessment["reconciliation_difference_rate"],
            "actual_material_cost_eur": assessment["actual_material_cost"],
            "production_cost_eur": assessment["production_cost"],
            "individual_cost_eur": assessment["individual_cost"],
            "net_cost_eur": assessment["net_cost"],
            "invoice_cost_eur": assessment["invoice_cost"],
            "ktr_cost_eur": assessment["ktr_cost"],
            "lager_cost_eur": assessment["lager_cost"],
            "material_surcharge_eur": assessment["material_surcharge"],
            "vv_surcharge_eur": assessment["vv_surcharge"],
            "fixed_surcharge_eur": assessment["fixed_surcharge"],
            "theoretical_invoice_cost_eur": assessment["theoretical_invoice_cost"],
            "theoretical_total_cost_eur": assessment["theoretical_total_cost"],
            "theoretical_result_eur": assessment["theoretical_result"],
            "theoretical_complete": assessment["theoretical_complete"],
            "price_critical": assessment["price_critical"],
            "afterproduction_detected": assessment["afterproduction_detected"],
            "order_closed": assessment["order_closed"],
            "delivery_status": assessment["delivery_status"],
            "delivery_deviation_count": assessment["delivery_deviation_count"],
            "billing_status": assessment["billing_status"],
            "theoretical_position_value_eur": assessment["theoretical_position_value"],
            "invoiced_value_eur": assessment["invoiced_value"],
            "credited_value_eur": assessment["credited_value"],
            "billed_revenue_eur": assessment["billed_revenue"],
            "billing_difference_eur": assessment["billing_difference"],
            "billing_difference_rate": assessment["billing_difference_rate"],
            "credit_note_present": assessment["credit_note_present"],
            "special_cost_value_eur": assessment["special_cost_value"],
            "manual_review_required": manual,
            "reason_codes": "|".join(codes),
            "reason_explanation": " | ".join(explanations) or "Kostenabstimmung und theoretische Kosten ohne zusätzlichen Hinweis.",
        })
    return output, {
        "method": "RECONCILED_ACTUAL_AND_THEORETICAL_COSTS",
        "orders_scored": len(output),
        "reconciliation_status_counts": dict(sorted(statuses.items())),
        "manual_reviews_created": sum(1 for item in output if item["manual_review_required"]),
        "price_critical_orders": sum(1 for item in output if item["price_critical"]),
        "confirmed_data_error_orders_excluded": len(excluded_data_errors),
    }

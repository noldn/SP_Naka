"""Erklärbare, robuste Peer-Gruppen für die Auftragsperformance.

Die Auswertung ist bewusst kein selbstlernender Regelautomat. Sie trainiert bei
jedem Lauf robuste Referenzbereiche auf historischen Aufträgen und kennzeichnet
statistische Auffälligkeiten als prüfbare Hinweise.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from .csv_io import read_rows
from .errors import AnalysisError


PERFORMANCE_FILES = {
    "Auftragskopf.csv",
    "VertriebsPositionen.csv",
    "Planung.csv",
    "ProdZeiten.csv",
    "Fertigungsmaterial.csv",
    "RohwarenPos.csv",
    "RW_Buchungen.csv",
    "Rechnungskontrollen.csv",
}

PERFORMANCE_FIELDS = [
    "run_id", "order_number", "performance_status", "absolute_result",
    "revenue_eur", "cost_eur", "margin_eur", "margin_rate",
    "peer_group_level", "peer_group_size", "robust_margin_z",
    "accepted_negative_customer", "manual_review_required", "reason_codes",
    "reason_explanation", "reason_review_status", "quantity_proxy", "quantity_bucket", "product_group",
    "construction", "die_form", "extra_effort_entries", "handwork_present",
    "print_approval_present", "first_observed_die_form", "ws_invoice_present",
    "wellboard_cost_source", "wellboard_net_value", "series_candidate",
    "series_color_overlap", "maximum_raw_material_quantity_ratio",
    "raw_material_quantity_status", "paper_cardboard_material_cost_eur",
    "paper_cardboard_share_of_revenue", "paper_cardboard_share_of_cost",
    "total_material_cost_eur", "total_material_share_of_revenue",
    "total_material_share_of_cost", "limitations",
]
EXPECTED_RESULT_FIELDS = [
    "order_number", "expected_performance_status", "expected_rule_ids",
    "expected_reason_codes", "accepted_exception", "professional_explanation",
    "review_status",
]


def _number(value: str) -> float | None:
    text = value.strip().replace("\u00a0", "")
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        result = float(text)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def _order_date(value: str) -> date | None:
    for pattern in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), pattern).date()
        except ValueError:
            pass
    return None


def _single(values: set[str]) -> str:
    cleaned = sorted(value for value in values if value)
    return cleaned[0] if len(cleaned) == 1 else ""


def _quantity_bucket(value: float | None, boundaries: list[float]) -> str:
    if value is None or value <= 0:
        return "UNKNOWN"
    lower = 0.0
    for upper in boundaries:
        if value <= upper:
            return f"{int(lower) + 1}-{int(upper)}"
        lower = upper
    return f">{int(boundaries[-1])}"


def _ratio(value: float, denominator: float | None) -> float | None:
    return value / abs(denominator) if denominator not in (None, 0) else None


def _raw_material_status(
    ratio: float | None, levels: list[dict[str, object]]
) -> str:
    status = "OK"
    if ratio is None:
        return "NICHT_BEWERTET"
    for level in levels:
        if ratio >= float(level["minimum_ratio"]):
            status = str(level["status"])
    return status


def _invoice_article(value: str, separator: str) -> str:
    text = value.strip().upper()
    return text.split(separator, 1)[-1] if separator in text else text


def load_parameters(path: Path) -> dict[str, object]:
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"Analyseparameter können nicht gelesen werden: {path}") from exc
    performance = content.get("performance", {})
    try:
        minimum = int(performance["minimum_peer_group_size"])
        threshold = float(performance["robust_z_threshold"])
        warning = float(performance["robust_z_warning_threshold"])
        buckets = [float(value) for value in performance["quantity_buckets"]]
    except (KeyError, TypeError, ValueError) as exc:
        raise AnalysisError("Analyseparameter für Peer-Gruppen sind unvollständig.") from exc
    if (
        minimum < 3
        or warning <= 0
        or threshold <= warning
        or not buckets
        or buckets != sorted(set(buckets))
    ):
        raise AnalysisError("Ungültige Peer-Gruppen-Parameter.")
    return content


def load_accepted_customers(path: Path) -> dict[str, list[tuple[date | None, date | None]]]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if "customer_key" not in (reader.fieldnames or []):
            raise AnalysisError(f"Stammdatendatei ohne customer_key: {path}")
        result: dict[str, list[tuple[date | None, date | None]]] = defaultdict(list)
        for row in reader:
            key = (row.get("customer_key") or "").strip()
            if not key:
                continue
            dates: list[date | None] = []
            for field in ("active_from", "active_until"):
                value = (row.get(field) or "").strip()
                try:
                    dates.append(datetime.strptime(value, "%Y-%m-%d").date() if value else None)
                except ValueError as exc:
                    raise AnalysisError(
                        f"{path.name}: {field} muss YYYY-MM-DD oder leer sein."
                    ) from exc
            if dates[0] and dates[1] and dates[0] > dates[1]:
                raise AnalysisError(f"{path.name}: active_from liegt nach active_until.")
            result[key].append((dates[0], dates[1]))
        return dict(result)


def _accepted_on(
    periods: list[tuple[date | None, date | None]], observed: date | None
) -> bool:
    return any(
        (start is None or observed is not None and observed >= start)
        and (end is None or observed is not None and observed <= end)
        for start, end in periods
    )


def performance_sources_available(source_dir: Path) -> bool:
    return all((source_dir / name).is_file() for name in PERFORMANCE_FILES)


def _load_features(source_dir: Path, parameters: dict[str, object]) -> dict[str, dict[str, object]]:
    articles = parameters["article_identification"]
    construction_prefix = str(articles["construction_prefix"]).upper()
    separator = str(articles["invoice_article_company_separator"])
    ws_prefix = str(articles["die_form_service_prefix"]).upper()
    wellboard_prefix = str(articles["wellboard_prefix"]).upper()
    evidence_keywords = parameters.get("evidence_keywords", {})
    print_keywords = [
        str(value).casefold() for value in evidence_keywords.get("print_approval", ["druckabstim"])
    ]
    hand_keywords = [
        str(value).casefold() for value in evidence_keywords.get("handwork", ["hand"])
    ]
    material_parameters = parameters.get("material_factors", {})
    paper_cardboard_groups = {
        str(value).casefold()
        for value in material_parameters.get("paper_cardboard_groups", ["Papier", "Karton"])
    }

    features: dict[str, dict[str, object]] = {}
    header_to_order: dict[str, str] = {}
    for row in read_rows(source_dir, "Auftragskopf.csv"):
        order = row["BelegNummer"].strip()
        revenue = _number(row.get("Erlöse", ""))
        cost = _number(row.get("Kosten", ""))
        margin = revenue - cost if revenue is not None and cost is not None else None
        margin_rate = margin / abs(revenue) if margin is not None and revenue not in (None, 0) else None
        features[order] = {
            "order_number": order,
            "order_date": _order_date(row.get("BelegDatum", "")),
            "customer": row.get("Kunde Key", "").strip(),
            "product_group": row.get("X_ArtikelGruppe", "").strip(),
            "revenue": revenue,
            "cost": cost,
            "margin": margin,
            "margin_rate": margin_rate,
            "constructions": set(), "die_forms": set(), "colors": set(),
            "quantity_proxy": None, "actual_duration": 0.0,
            "extra_effort": 0, "handwork": False, "print_approval": False,
            "material_value": 0.0, "fm_wellboard_value": 0.0,
            "rw_wellboard_value": 0.0, "rw_wellboard_rows": 0,
            "ws_invoice": False, "completion_hour": None,
            "raw_required_by_article": defaultdict(float),
            "raw_booked_by_article": defaultdict(float),
            "fm_value_by_article": defaultdict(float),
            "fm_groups_by_article": defaultdict(set),
            "rw_value_by_article": defaultdict(float),
            "rw_rows_by_article": defaultdict(int),
        }
        header_to_order[row["BelegKopfKey"].strip()] = order

    for row in read_rows(source_dir, "VertriebsPositionen.csv"):
        order = header_to_order.get(row["BelegKopfKey"].strip())
        if not order:
            continue
        muster = row.get("Muster", "").strip()
        if muster.upper().startswith(construction_prefix):
            features[order]["constructions"].add(muster)
        quantity = _number(row.get("Menge", ""))
        current = features[order]["quantity_proxy"]
        if quantity is not None and quantity > 0 and (current is None or quantity > current):
            features[order]["quantity_proxy"] = quantity

    for row in read_rows(source_dir, "Planung.csv"):
        order = row["AuftragNr"].strip()
        if order not in features:
            continue
        die_form = row.get("STANZFORM", "").strip()
        if die_form:
            features[order]["die_forms"].add(die_form)
        completion = _number(row.get("AuftragFertigDatum", ""))
        current = features[order]["completion_hour"]
        if completion is not None and (current is None or completion * 24 > current):
            features[order]["completion_hour"] = completion * 24

    for row in read_rows(source_dir, "ProdZeiten.csv"):
        order = row["Auftrag"].strip()
        if order not in features:
            continue
        duration = _number(row.get("DauerMaschine", ""))
        if duration is None or duration == 0:
            duration = _number(row.get("Dauer", ""))
        if duration is not None and duration > 0:
            features[order]["actual_duration"] += duration
        if row.get("Mehraufwand Id", "").strip():
            features[order]["extra_effort"] += 1
        operation = (row.get("ARVOKurz") or "").casefold()
        stage = (row.get("Stufe") or "").casefold()
        features[order]["handwork"] |= any(
            keyword in operation or keyword in stage for keyword in hand_keywords
        )
        features[order]["print_approval"] |= any(
            keyword in operation for keyword in print_keywords
        )

    for row in read_rows(source_dir, "Fertigungsmaterial.csv"):
        order = row["Auftrag"].strip()
        if order not in features:
            continue
        value = _number(row.get("Materialwert", "")) or 0.0
        article = row.get("Artikel", "").strip().upper()
        if article:
            features[order]["fm_value_by_article"][article] += value
        if article.startswith(wellboard_prefix):
            features[order]["fm_wellboard_value"] += value
        group = row.get("GruppeBezeichnung", "").casefold()
        if article and group:
            features[order]["fm_groups_by_article"][article].add(group)
        if group in {"farben", "lacke"} or article.startswith("MIX"):
            features[order]["colors"].add(article)

    for row in read_rows(source_dir, "RW_Buchungen.csv"):
        order = row["BelegNummer"].strip()
        if order not in features:
            continue
        article = row.get("Artikel", "").strip().upper()
        quantity = _number(row.get("Menge", "")) or 0.0
        if article:
            features[order]["raw_booked_by_article"][article] += quantity
            features[order]["rw_rows_by_article"][article] += 1
            features[order]["rw_value_by_article"][article] += _number(row.get("WertMat", "")) or 0.0
        if article.startswith(wellboard_prefix):
            features[order]["rw_wellboard_rows"] += 1
            features[order]["rw_wellboard_value"] += _number(row.get("WertMat", "")) or 0.0

    for row in read_rows(source_dir, "RohwarenPos.csv"):
        order = row["BelegNummer"].strip()
        if order not in features:
            continue
        article = row.get("Artikel", "").strip().upper()
        quantity = _number(row.get("Menge", ""))
        if article and quantity is not None and quantity > 0:
            features[order]["raw_required_by_article"][article] += quantity

    for row in read_rows(source_dir, "Rechnungskontrollen.csv"):
        order = row["Traeger"].strip()
        if order not in features:
            continue
        article = _invoice_article(row.get("Artikel Key", ""), separator)
        features[order]["ws_invoice"] |= article.startswith(ws_prefix)

    for item in features.values():
        item["construction"] = _single(item.pop("constructions"))
        item["die_form"] = _single(item.pop("die_forms"))
        item["identity"] = item["die_form"] or item["construction"]
        quantity = item["quantity_proxy"]
        item["unit_revenue"] = item["revenue"] / quantity if item["revenue"] is not None and quantity else None
        item["duration_per_unit"] = item["actual_duration"] / quantity if quantity else None
        item["material_per_unit"] = item["material_value"] / quantity if quantity else None
        if item["rw_wellboard_rows"]:
            item["wellboard_cost_source"] = "RW_Buchungen.csv"
            item["wellboard_net_value"] = item["rw_wellboard_value"]
        elif item["fm_wellboard_value"]:
            item["wellboard_cost_source"] = "Fertigungsmaterial.csv_FALLBACK"
            item["wellboard_net_value"] = item["fm_wellboard_value"]
        else:
            item["wellboard_cost_source"] = "NONE"
            item["wellboard_net_value"] = 0.0
        ratios = [
            abs(item["raw_booked_by_article"].get(article, 0.0)) / required
            for article, required in item["raw_required_by_article"].items()
            if required > 0 and article in item["raw_booked_by_article"]
        ]
        item["maximum_raw_material_quantity_ratio"] = max(ratios, default=None)
        all_material_articles = set(item["fm_value_by_article"]).union(item["rw_value_by_article"])
        material_costs: dict[str, float] = {}
        for article in all_material_articles:
            if item["rw_rows_by_article"].get(article, 0):
                material_costs[article] = abs(item["rw_value_by_article"].get(article, 0.0))
            else:
                material_costs[article] = max(item["fm_value_by_article"].get(article, 0.0), 0.0)
        paper_cost = sum(
            value for article, value in material_costs.items()
            if paper_cardboard_groups.intersection(item["fm_groups_by_article"].get(article, set()))
        )
        total_material_cost = sum(material_costs.values())
        item["paper_cardboard_material_cost"] = paper_cost
        item["total_material_cost"] = total_material_cost
        item["material_value"] = total_material_cost
        item["material_per_unit"] = total_material_cost / quantity if quantity else None
    return features


def _robust(values: list[float]) -> tuple[float, float]:
    median = statistics.median(values)
    mad = statistics.median(abs(value - median) for value in values)
    return median, mad


def _z(value: float | None, profile: tuple[float, float] | None) -> float | None:
    if value is None or profile is None or profile[1] == 0:
        return None
    return 0.67448975 * (value - profile[0]) / profile[1]


def _peer_keys(item: dict[str, object], bucket: str) -> list[tuple[str, str]]:
    customer, identity, product = item["customer"], item["identity"], item["product_group"]
    candidates = []
    if customer and identity:
        candidates.append(("customer+identity+quantity_bucket", f"{customer}|{identity}|{bucket}"))
    if identity:
        candidates.append(("identity+quantity_bucket", f"{identity}|{bucket}"))
    if product:
        candidates.append(("product_group+quantity_bucket", f"{product}|{bucket}"))
    candidates.append(("global+quantity_bucket", bucket))
    return candidates


def _build_profiles(features: dict[str, dict[str, object]], buckets: list[float]) -> dict[tuple[str, str], dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for item in features.values():
        bucket = _quantity_bucket(item["quantity_proxy"], buckets)
        for key in _peer_keys(item, bucket):
            grouped[key].append(item)
    profiles = {}
    for key, items in grouped.items():
        profile: dict[str, object] = {"size": len(items)}
        for metric in ("margin_rate", "unit_revenue", "duration_per_unit", "material_per_unit"):
            values = [float(item[metric]) for item in items if item[metric] is not None]
            profile[metric] = _robust(values) if len(values) >= 3 else None
        profiles[key] = profile
    return profiles


def _first_observed_dates(features: dict[str, dict[str, object]]) -> dict[str, date]:
    earliest: dict[str, date] = {}
    return earliest


def _mark_first_observed(
    features: dict[str, dict[str, object]], earliest: dict[str, date]
) -> None:
    for item in features.values():
        identity, observed = item["die_form"], item["order_date"]
        if identity and observed and (identity not in earliest or observed < earliest[identity]):
            earliest[identity] = observed
    for item in features.values():
        item["first_observed_die_form"] = bool(
            item["die_form"] and item["order_date"] and earliest.get(item["die_form"]) == item["order_date"]
        )


def _mark_series(
    reference: dict[str, dict[str, object]],
    scoring: dict[str, dict[str, object]],
    minimum: float,
    maximum: float,
) -> None:
    by_identity: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in reference.values():
        if item["identity"] and item["completion_hour"] is not None:
            by_identity[item["identity"]].append(item)
    for item in scoring.values():
        item["series_candidate"] = False
        item["series_color_overlap"] = False
    for current in scoring.values():
        if not current["identity"] or current["completion_hour"] is None:
            continue
        previous_candidates = [
            item for item in by_identity.get(current["identity"], [])
            if item["order_number"] != current["order_number"]
            and item["completion_hour"] is not None
            and float(item["completion_hour"]) < float(current["completion_hour"])
        ]
        if not previous_candidates:
            continue
        previous = max(previous_candidates, key=lambda value: float(value["completion_hour"]))
        delta = float(current["completion_hour"]) - float(previous["completion_hour"])
        if minimum <= delta <= maximum:
            current["series_candidate"] = True
            current["series_color_overlap"] = bool(current["colors"].intersection(previous["colors"]))


def analyze_performance(
    reference_dir: Path,
    scoring_dir: Path,
    parameters_path: Path,
    accepted_customers_path: Path,
    run_id: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    parameters = load_parameters(parameters_path)
    perf = parameters["performance"]
    buckets = [float(value) for value in perf["quantity_buckets"]]
    minimum = int(perf["minimum_peer_group_size"])
    threshold = float(perf["robust_z_threshold"])
    warning = float(perf["robust_z_warning_threshold"])
    reference = _load_features(reference_dir, parameters)
    scoring = _load_features(scoring_dir, parameters)
    if reference_dir.resolve() != scoring_dir.resolve():
        training = {
            order: item for order, item in reference.items() if order not in scoring
        }
    else:
        training = reference
    profiles = _build_profiles(training, buckets)
    earliest = _first_observed_dates(reference)
    _mark_first_observed(reference, earliest)
    _mark_first_observed(scoring, earliest)
    series = parameters["series_detection"]
    raw_levels = parameters["raw_material_quantity_check"].get("levels", [])
    try:
        raw_thresholds = [float(level["minimum_ratio"]) for level in raw_levels]
        raw_statuses = [str(level["status"]) for level in raw_levels]
    except (KeyError, TypeError, ValueError) as exc:
        raise AnalysisError("Rohwaren-Mengenstufen sind unvollständig.") from exc
    if (
        not raw_thresholds
        or raw_thresholds != sorted(set(raw_thresholds))
        or raw_thresholds[0] <= 1
        or raw_statuses != ["HINWEIS", "PRUEFEN", "KRITISCH"]
    ):
        raise AnalysisError("Rohwaren-Mengenstufen müssen aufsteigend HINWEIS, PRUEFEN, KRITISCH definieren.")
    _mark_series(
        reference,
        scoring,
        float(series["minimum_hours"]),
        float(series["maximum_hours"]),
    )
    accepted = load_accepted_customers(accepted_customers_path)

    output: list[dict[str, object]] = []
    counts: defaultdict[str, int] = defaultdict(int)
    for order in sorted(scoring):
        item = scoring[order]
        bucket = _quantity_bucket(item["quantity_proxy"], buckets)
        selected_key = None
        selected_profile = None
        for key in _peer_keys(item, bucket):
            if profiles.get(key, {}).get("size", 0) >= minimum:
                selected_key, selected_profile = key, profiles[key]
                break
        margin_z = _z(item["margin_rate"], selected_profile.get("margin_rate") if selected_profile else None)
        if margin_z is None:
            status = "NICHT_BEWERTET"
        elif margin_z <= -threshold:
            status = "SEHR_NEGATIV"
        elif margin_z >= threshold:
            status = "SEHR_POSITIV"
        elif margin_z <= -warning:
            status = "AUFFAELLIG_NEGATIV"
        elif margin_z >= warning:
            status = "AUFFAELLIG_POSITIV"
        else:
            status = "IM_REFERENZBEREICH"

        reason_codes: list[str] = []
        explanations: list[str] = []
        customer_code = str(item["customer"]).split("|", 1)[-1]
        periods = accepted.get(str(item["customer"]), []) + accepted.get(customer_code, [])
        accepted_customer = _accepted_on(periods, item["order_date"])
        if item["margin"] is not None and item["margin"] < 0:
            reason_codes.append("ERGEBNIS_NEGATIV")
            explanations.append("Erlöse minus Kosten ist negativ.")
            if accepted_customer:
                reason_codes.append("AUSLASTUNGSKUNDE")
                explanations.append("Negatives Ergebnis ist für diesen Auslastungskunden grundsätzlich zulässig.")
        if status in {
            "SEHR_NEGATIV", "SEHR_POSITIV", "AUFFAELLIG_NEGATIV", "AUFFAELLIG_POSITIV"
        }:
            reason_codes.append("ROBUSTE_PEER_ABWEICHUNG")
            explanations.append("Die Marge weicht im robusten Vergleich deutlich von der passendsten Peer-Gruppe ab.")

        unit_price_z = _z(item["unit_revenue"], selected_profile.get("unit_revenue") if selected_profile else None)
        duration_z = _z(item["duration_per_unit"], selected_profile.get("duration_per_unit") if selected_profile else None)
        material_z = _z(item["material_per_unit"], selected_profile.get("material_per_unit") if selected_profile else None)
        if status in {"SEHR_NEGATIV", "AUFFAELLIG_NEGATIV"}:
            if unit_price_z is not None and unit_price_z <= -threshold:
                reason_codes.append("PREISNIVEAU_NIEDRIG")
                explanations.append("Der Erlös je Mengen-Proxy ist gegenüber der Peer-Gruppe auffällig niedrig.")
            if duration_z is not None and duration_z >= threshold:
                reason_codes.append("LEISTUNG_ZEIT_AUFFAELLIG")
                explanations.append("Die Ist-Zeit je Mengen-Proxy ist gegenüber der Peer-Gruppe auffällig hoch.")
            if material_z is not None and material_z >= threshold:
                reason_codes.append("MATERIALAUFWAND_AUFFAELLIG")
                explanations.append("Der erfasste Materialwert je Mengen-Proxy ist gegenüber der Peer-Gruppe auffällig hoch.")
            if item["extra_effort"]:
                reason_codes.append("MEHRAUFWAND_ERFASST")
                explanations.append("Mindestens eine Produktionszeitmeldung enthält einen Mehraufwand.")
            if item["print_approval"]:
                reason_codes.append("DRUCKABSTIMMUNG_ERKANNT")
                explanations.append("In den Arbeitsvorgängen wurde eine Druckabstimmung erkannt.")
            if item["handwork"] and (item["extra_effort"] or item["print_approval"]):
                reason_codes.append("HANDARBEIT_MIT_AUSSERGEWOEHNLICHEM_AUFWAND")
                explanations.append(
                    "Handarbeit wurde zusammen mit Druckabstimmung oder erfasstem Mehraufwand erkannt. "
                    "Geplante Handarbeit allein ist keine Negativbegründung."
                )
        if item["first_observed_die_form"]:
            code = "ERSTE_STANZFORM_MIT_WS" if item["ws_invoice"] else "ERSTE_STANZFORM_OHNE_WS_HINWEIS"
            reason_codes.append(code)
            explanations.append(
                "Die Stanzform wird im bereitgestellten Zeitraum erstmals beobachtet; "
                + ("ein WS-Artikel ist vorhanden." if item["ws_invoice"] else "kein WS-Artikel wurde gefunden. Wegen des begrenzten Datenzeitraums ist dies nur ein Prüfhinweis.")
            )
        if item["series_candidate"]:
            reason_codes.append("SERIENKANDIDAT")
            explanations.append("Gleiche Stanzform/Konstruktion wurde 12 bis 24 Stunden nach dem vorherigen beobachteten Auftrag fertiggestellt.")
        raw_ratio = item["maximum_raw_material_quantity_ratio"]
        raw_status = _raw_material_status(raw_ratio, raw_levels)
        if raw_status in {"HINWEIS", "PRUEFEN", "KRITISCH"}:
            reason_codes.append(f"ROHWARENMENGE_{raw_status}")
            explanations.append(
                "Die absolute Netto-Rohwarenbuchung ist bei mindestens einem exakt passenden Artikel "
                f"{raw_ratio:.2f}-mal so hoch wie die positive Sollmenge (Stufe {raw_status}). "
                "Eine nicht korrigierte Restpalette ist möglich."
            )

        absolute = "POSITIV" if item["margin"] is not None and item["margin"] > 0 else "NEGATIV" if item["margin"] is not None and item["margin"] < 0 else "NULL_ODER_UNBEKANNT"
        manual = status in {
            "SEHR_NEGATIV", "SEHR_POSITIV", "AUFFAELLIG_NEGATIV", "AUFFAELLIG_POSITIV"
        }
        manual |= raw_status in {"PRUEFEN", "KRITISCH"}
        explanatory_codes = {
            "PREISNIVEAU_NIEDRIG", "LEISTUNG_ZEIT_AUFFAELLIG",
            "MATERIALAUFWAND_AUFFAELLIG", "MEHRAUFWAND_ERFASST",
            "DRUCKABSTIMMUNG_ERKANNT", "HANDARBEIT_MIT_AUSSERGEWOEHNLICHEM_AUFWAND",
        }
        if raw_status in {"PRUEFEN", "KRITISCH"}:
            reason_review_status = "CORRECTION_CONFIRMATION_REQUIRED"
        elif manual and explanatory_codes.intersection(reason_codes):
            reason_review_status = "PROPOSED_REASON_CONFIRMATION_REQUIRED"
        elif manual:
            reason_review_status = "REASON_REQUIRED"
        else:
            reason_review_status = "NO_CONFIRMATION_REQUIRED"
        counts[status] += 1
        output.append({
            "run_id": run_id, "order_number": order, "performance_status": status,
            "absolute_result": absolute, "revenue_eur": item["revenue"], "cost_eur": item["cost"],
            "margin_eur": item["margin"], "margin_rate": item["margin_rate"],
            "peer_group_level": selected_key[0] if selected_key else "NONE",
            "peer_group_size": selected_profile["size"] if selected_profile else 0,
            "robust_margin_z": margin_z, "accepted_negative_customer": accepted_customer,
            "manual_review_required": manual, "reason_codes": "|".join(reason_codes),
            "reason_explanation": " | ".join(explanations) or "Keine zusätzliche Erklärungsevidenz erkannt.",
            "reason_review_status": reason_review_status,
            "quantity_proxy": item["quantity_proxy"], "quantity_bucket": bucket,
            "product_group": item["product_group"], "construction": item["construction"],
            "die_form": item["die_form"], "extra_effort_entries": item["extra_effort"],
            "handwork_present": item["handwork"], "print_approval_present": item["print_approval"],
            "first_observed_die_form": item["first_observed_die_form"], "ws_invoice_present": item["ws_invoice"],
            "wellboard_cost_source": item["wellboard_cost_source"], "wellboard_net_value": item["wellboard_net_value"],
            "series_candidate": item["series_candidate"], "series_color_overlap": item["series_color_overlap"],
            "maximum_raw_material_quantity_ratio": raw_ratio,
            "raw_material_quantity_status": raw_status,
            "paper_cardboard_material_cost_eur": item["paper_cardboard_material_cost"],
            "paper_cardboard_share_of_revenue": _ratio(item["paper_cardboard_material_cost"], item["revenue"]),
            "paper_cardboard_share_of_cost": _ratio(item["paper_cardboard_material_cost"], item["cost"]),
            "total_material_cost_eur": item["total_material_cost"],
            "total_material_share_of_revenue": _ratio(item["total_material_cost"], item["revenue"]),
            "total_material_share_of_cost": _ratio(item["total_material_cost"], item["cost"]),
            "limitations": "Keine Lagerkosten; Ursachen sind Evidenzhinweise; Referenzexport kann historische Lücken enthalten.",
        })
    return output, {
        "method": "ROBUST_HIERARCHICAL_PEER_GROUPS",
        "reference_orders": len(reference), "training_orders": len(training),
        "scored_orders": len(scoring),
        "minimum_peer_group_size": minimum, "robust_z_threshold": threshold,
        "robust_z_warning_threshold": warning,
        "status_counts": dict(sorted(counts.items())),
        "accepted_negative_customers_loaded": len(accepted),
        "series_detection_status": "HYPOTHESIS_ONLY",
    }

"""Orchestrierung der statischen Auftragsprüfung."""

from __future__ import annotations

import hashlib
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .csv_io import (
    REQUIRED_COLUMNS,
    read_rows,
    resolve_source_dir,
    sha256_file,
    validate_output_location,
    validate_sources,
    write_csv,
    write_json,
)
from .errors import AnalysisError
from .models import OrderAssessment, RuleResult
from .performance import (
    EXPECTED_RESULT_FIELDS,
    PERFORMANCE_FIELDS,
    PERFORMANCE_REQUIRED_FILES,
    analyze_performance,
    available_performance_files,
    performance_sources_available,
)
from .rules import evaluate_rule, load_rules, normalize, normalize_stage, rule_applies
from .version import __version__


ASSESSMENT_FIELDS = [
    "run_id", "order_number", "order_header_key", "order_date", "overall_status",
    "applicable_rule_count", "passed_rule_count", "deviation_count",
    "accepted_exception_count", "reason_codes", "exception_codes", "reasons",
    "manual_review_required",
]
RULE_RESULT_FIELDS = [
    "run_id", "order_number", "rule_id", "status", "reason", "evidence_count",
]
FEEDBACK_FIELDS = [
    "run_id", "order_number", "rule_id", "rule_status", "rule_reason",
    "review_decision", "review_comment", "reviewed_by", "reviewed_at",
]
DATA_QUALITY_FIELDS = [
    "source_file", "row_number", "issue_code", "field", "severity", "handling",
]
PERFORMANCE_FEEDBACK_FIELDS = [
    "run_id", "order_number", "performance_status", "reason_codes",
    "review_decision", "error_category", "review_comment", "reviewed_by",
    "reviewed_at",
]


def _load_orders(source_dir: Path) -> dict[str, tuple[str, str]]:
    return {
        row["BelegNummer"].strip(): (
            row["BelegKopfKey"].strip(),
            row["BelegDatum"].strip(),
        )
        for row in read_rows(source_dir, "Auftragskopf.csv")
    }


def _load_stages(source_dir: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for file_name, order_field in (
        ("Planung.csv", "AuftragNr"),
        ("ProdZeiten.csv", "Auftrag"),
    ):
        for row in read_rows(source_dir, file_name):
            order = row[order_field].strip()
            stage = normalize_stage(row["Stufe"])
            if order and stage:
                result[order].add(stage)
    return result


def _load_material_groups(source_dir: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for row in read_rows(source_dir, "Fertigungsmaterial.csv"):
        order = row["Auftrag"].strip()
        group = normalize(row["GruppeBezeichnung"])
        if order and group:
            result[order].add(group)
    return result


def _load_articles(source_dir: Path) -> dict[str, dict[str, set[str]]]:
    result: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for file_name, order_field in (
        ("Fertigungsmaterial.csv", "Auftrag"),
        ("RW_Buchungen.csv", "BelegNummer"),
    ):
        for row in read_rows(source_dir, file_name):
            order = row[order_field].strip()
            article = row["Artikel"].strip()
            if order and article:
                result[order][file_name].add(article)
    return result


def _assess(
    orders: dict[str, tuple[str, str]],
    stages: dict[str, set[str]],
    groups: dict[str, set[str]],
    articles: dict[str, dict[str, set[str]]],
    rules,
) -> tuple[list[OrderAssessment], list[RuleResult]]:
    assessments: list[OrderAssessment] = []
    all_results: list[RuleResult] = []

    for order_number in sorted(orders):
        applicable = [rule for rule in rules if rule_applies(rule, stages.get(order_number, set()))]
        results = [
            evaluate_rule(
                rule,
                order_number,
                groups.get(order_number, set()),
                articles.get(order_number, {}),
            )
            for rule in applicable
        ]
        deviations = [result for result in results if result.status == "ABWEICHUNG"]
        accepted_exceptions = [
            result for result in results if result.status == "AKZEPTIERTE_AUSNAHME"
        ]
        passed = len(results) - len(deviations)
        if not results:
            overall = "NICHT_BEWERTET"
        elif deviations:
            overall = "ABWEICHUNG"
        elif accepted_exceptions:
            overall = "REGELKONFORM_MIT_AUSNAHME"
        else:
            overall = "REGELKONFORM"

        header_key, order_date = orders[order_number]
        assessments.append(
            OrderAssessment(
                order_number=order_number,
                order_header_key=header_key,
                order_date=order_date,
                overall_status=overall,
                applicable_rule_count=len(results),
                passed_rule_count=passed,
                deviation_count=len(deviations),
                accepted_exception_count=len(accepted_exceptions),
                reason_codes="|".join(result.rule_id for result in deviations),
                exception_codes="|".join(
                    result.rule_id for result in accepted_exceptions
                ),
                reasons=" | ".join(
                    result.reason for result in deviations + accepted_exceptions
                )
                or (
                    "Alle anwendbaren Regeln bestanden."
                    if results
                    else "Keine statische Regel anwendbar."
                ),
                manual_review_required=bool(deviations),
            )
        )
        all_results.extend(results)

    return assessments, all_results


def _record(item) -> dict[str, object]:
    return dict(item.__dict__)


def run_analysis(
    data_dir: Path,
    output_root: Path,
    rules_path: Path,
    run_id: str | None = None,
    reference_data_dir: Path | None = None,
    analysis_parameters_path: Path | None = None,
    accepted_customers_path: Path | None = None,
) -> Path:
    started = datetime.now(timezone.utc)
    source_dir = resolve_source_dir(data_dir)
    validate_output_location(source_dir, output_root)
    row_counts, data_quality_issues = validate_sources(source_dir)
    rules_version, rules = load_rules(rules_path)

    effective_run_id = run_id or started.strftime("%Y%m%dT%H%M%S.%fZ")
    if (
        effective_run_id.startswith(".")
        or not effective_run_id.replace("-", "").replace("_", "").replace(".", "").isalnum()
    ):
        raise AnalysisError("run_id darf nur Buchstaben, Zahlen, Punkt, Minus und Unterstrich enthalten.")
    resolved_output_root = output_root.expanduser().resolve()
    run_dir = resolved_output_root / effective_run_id
    # Unter macOS kann ein als Punkt-Ordner angelegtes Verzeichnis das
    # Finder-Attribut "hidden" nach dem atomaren Umbenennen behalten. Der
    # sichtbare Präfix verhindert das, ohne die atomare Veröffentlichung des
    # fertigen Laufs zu verändern.
    temporary_run_dir = resolved_output_root / f"tmp-{effective_run_id}"
    if run_dir.exists():
        raise AnalysisError(f"Ausgabelauf existiert bereits: {run_dir}")
    if temporary_run_dir.exists():
        raise AnalysisError(f"Temporäres Ausgabeverzeichnis existiert bereits: {temporary_run_dir}")

    orders = _load_orders(source_dir)
    stages = _load_stages(source_dir)
    material_groups = _load_material_groups(source_dir)
    articles = _load_articles(source_dir)
    unknown_orders = (
        set(stages).union(material_groups).union(articles).difference(orders)
    )
    if unknown_orders:
        raise AnalysisError(
            f"{len(unknown_orders)} Auftragsreferenzen fehlen im Auftragskopf; Lauf abgebrochen."
        )
    assessments, rule_results = _assess(orders, stages, material_groups, articles, rules)

    performance_results: list[dict[str, object]] = []
    performance_summary: dict[str, object] | None = None
    reference_dir: Path | None = None
    if analysis_parameters_path is not None:
        reference_dir = resolve_source_dir(reference_data_dir or source_dir)
        if not performance_sources_available(source_dir):
            missing = sorted(name for name in PERFORMANCE_REQUIRED_FILES if not (source_dir / name).is_file())
            raise AnalysisError(f"Performance-Auswertung: Quelldateien fehlen: {', '.join(missing)}")
        if not performance_sources_available(reference_dir):
            missing = sorted(name for name in PERFORMANCE_REQUIRED_FILES if not (reference_dir / name).is_file())
            raise AnalysisError(f"Performance-Referenz: Quelldateien fehlen: {', '.join(missing)}")
        performance_results, performance_summary = analyze_performance(
            reference_dir,
            source_dir,
            analysis_parameters_path,
            accepted_customers_path or Path("__missing_master_data__"),
            effective_run_id,
        )

    deviations = [item for item in rule_results if item.status == "ABWEICHUNG"]
    completed = datetime.now(timezone.utc)
    status_counts = Counter(item.overall_status for item in assessments)
    rule_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for item in rule_results:
        rule_status_counts[item.rule_id][item.status] += 1
    used_source_names = set(REQUIRED_COLUMNS)
    if performance_summary is not None:
        used_source_names.update(available_performance_files(source_dir))
    source_files = {
        file_name: {
            "rows": row_counts.get(file_name) or sum(1 for _ in read_rows(source_dir, file_name)),
            "sha256": sha256_file(source_dir / file_name),
        }
        for file_name in sorted(used_source_names)
    }
    reference_files = None
    if reference_dir is not None and reference_dir != source_dir:
        reference_files = {
            file_name: {
                "rows": sum(1 for _ in read_rows(reference_dir, file_name)),
                "sha256": sha256_file(reference_dir / file_name),
            }
            for file_name in sorted(available_performance_files(reference_dir))
        }
    rules_bytes = rules_path.read_bytes()
    manifest = {
        "run_id": effective_run_id,
        "program_version": __version__,
        "rules_version": rules_version,
        "rules_sha256": hashlib.sha256(rules_bytes).hexdigest(),
        "started_at_utc": started.isoformat(),
        "completed_at_utc": completed.isoformat(),
        "configuration": {
            "rules_file": str(rules_path.resolve()),
            "source_directory": str(source_dir),
            "output_directory": str(run_dir),
            "performance_parameters_file": (
                str(analysis_parameters_path.resolve()) if analysis_parameters_path else None
            ),
            "performance_reference_directory": str(reference_dir) if reference_dir else None,
            "accepted_customers_file": (
                str(accepted_customers_path.resolve()) if accepted_customers_path else None
            ),
            "performance_parameters_sha256": (
                sha256_file(analysis_parameters_path) if analysis_parameters_path else None
            ),
            "accepted_customers_sha256": (
                sha256_file(accepted_customers_path)
                if accepted_customers_path and accepted_customers_path.is_file()
                else None
            ),
        },
        "control_totals": {
            "input_rows": sum(item["rows"] for item in source_files.values()),
            "orders_read": len(orders),
            "orders_processed": len(assessments),
            "orders_excluded": 0,
            "invalid_records": len(data_quality_issues),
            "rule_results_created": len(rule_results),
            "manual_reviews_created": len(deviations),
            "performance_reviews_created": sum(
                1 for item in performance_results if item["manual_review_required"]
            ),
            "order_status_counts": dict(sorted(status_counts.items())),
            "rule_status_counts": {
                rule_id: dict(sorted(counts.items()))
                for rule_id, counts in sorted(rule_status_counts.items())
            },
        },
        "source_files": source_files,
        "reference_files": reference_files,
        "performance_analysis": performance_summary,
        "result_status": "COMPLETED",
    }
    temporary_run_dir.mkdir(parents=True)
    try:
        write_csv(
            temporary_run_dir / "order_assessments.csv",
            ASSESSMENT_FIELDS,
            ({"run_id": effective_run_id, **_record(item)} for item in assessments),
        )
        write_csv(
            temporary_run_dir / "rule_results.csv",
            RULE_RESULT_FIELDS,
            ({"run_id": effective_run_id, **_record(item)} for item in rule_results),
        )
        write_csv(
            temporary_run_dir / "manual_review_template.csv",
            FEEDBACK_FIELDS,
            (
                {
                    "run_id": effective_run_id,
                    "order_number": item.order_number,
                    "rule_id": item.rule_id,
                    "rule_status": item.status,
                    "rule_reason": item.reason,
                    "review_decision": "",
                    "review_comment": "",
                    "reviewed_by": "",
                    "reviewed_at": "",
                }
                for item in deviations
            ),
        )
        write_csv(
            temporary_run_dir / "data_quality_issues.csv",
            DATA_QUALITY_FIELDS,
            data_quality_issues,
        )
        if performance_results:
            write_csv(
                temporary_run_dir / "performance_assessments.csv",
                PERFORMANCE_FIELDS,
                performance_results,
            )
            write_csv(
                temporary_run_dir / "performance_review_template.csv",
                PERFORMANCE_FEEDBACK_FIELDS,
                (
                    {
                        "run_id": effective_run_id,
                        "order_number": item["order_number"],
                        "performance_status": item["performance_status"],
                        "reason_codes": item["reason_codes"],
                        "review_decision": "",
                        "error_category": "",
                        "review_comment": "",
                        "reviewed_by": "",
                        "reviewed_at": "",
                    }
                    for item in performance_results
                    if item["manual_review_required"]
                ),
            )
            write_csv(
                temporary_run_dir / "expected_results_template.csv",
                EXPECTED_RESULT_FIELDS,
                (
                    {
                        "order_number": item["order_number"],
                        "expected_performance_status": "",
                        "expected_rule_ids": "",
                        "expected_reason_codes": "",
                        "accepted_exception": "",
                        "professional_explanation": "",
                        "review_status": "",
                    }
                    for item in performance_results
                ),
            )
        write_json(temporary_run_dir / "run_manifest.json", manifest)
        temporary_run_dir.replace(run_dir)
    except Exception:
        shutil.rmtree(temporary_run_dir, ignore_errors=True)
        raise

    latest_path = resolved_output_root / "latest_run.txt"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(f"{run_dir}\n", encoding="utf-8")
    return run_dir

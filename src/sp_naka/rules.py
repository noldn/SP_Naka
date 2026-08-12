"""Konfigurierbare, deterministische Materialregeln."""

from __future__ import annotations

import json
from pathlib import Path

from .errors import AnalysisError
from .models import Rule, RuleResult


ALLOWED_REQUIREMENTS = {"material_group_any", "article_prefix"}
ALLOWED_SOURCES = {"Fertigungsmaterial.csv", "RW_Buchungen.csv"}


def normalize(value: str) -> str:
    return value.strip().casefold()


def normalize_stage(value: str) -> str:
    return value.strip().upper()


def load_rules(path: Path) -> tuple[str, list[Rule]]:
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"Regelkonfiguration kann nicht gelesen werden: {path}") from exc

    version = str(content.get("version", "")).strip()
    entries = content.get("rules")
    if not version or not isinstance(entries, list) or not entries:
        raise AnalysisError("Regelkonfiguration benötigt Version und mindestens eine Regel.")

    rules: list[Rule] = []
    seen_ids: set[str] = set()
    for entry in entries:
        try:
            rule_id = str(entry["id"]).strip()
            requirement = entry["requirement"]
            requirement_type = str(requirement["type"]).strip()
            source = str(requirement["source"]).strip()
            values = tuple(str(value).strip() for value in requirement["values"])
            trigger_stages = frozenset(
                normalize_stage(str(value)) for value in entry["trigger_stages"]
            )
            rule = Rule(
                rule_id=rule_id,
                description=str(entry["description"]).strip(),
                trigger_stages=trigger_stages,
                requirement_type=requirement_type,
                values=values,
                source=source,
                pass_reason=str(entry["pass_reason"]).strip(),
                fail_reason=str(entry["fail_reason"]).strip(),
                acceptance_exception_none_groups=tuple(
                    str(value).strip()
                    for value in entry.get("acceptance_exception", {}).get("none_of_groups", [])
                ),
                acceptance_exception_reason=str(
                    entry.get("acceptance_exception", {}).get("reason", "")
                ).strip(),
            )
        except (KeyError, TypeError) as exc:
            raise AnalysisError("Unvollständige Regelkonfiguration.") from exc

        if not rule_id or rule_id in seen_ids:
            raise AnalysisError(f"Leere oder doppelte Regel-ID: {rule_id!r}")
        if not trigger_stages or not values:
            raise AnalysisError(f"{rule_id}: Trigger und Prüfwerte dürfen nicht leer sein.")
        if requirement_type not in ALLOWED_REQUIREMENTS:
            raise AnalysisError(f"{rule_id}: unbekannter Anforderungstyp {requirement_type}")
        if source not in ALLOWED_SOURCES:
            raise AnalysisError(f"{rule_id}: unzulässige Quelle {source}")
        if bool(rule.acceptance_exception_none_groups) != bool(
            rule.acceptance_exception_reason
        ):
            raise AnalysisError(
                f"{rule_id}: automatische Ausnahme benötigt Prüfwerte und Begründung."
            )
        seen_ids.add(rule_id)
        rules.append(rule)

    return version, rules


def rule_applies(rule: Rule, order_stages: set[str]) -> bool:
    return bool(rule.trigger_stages.intersection(order_stages))


def evaluate_rule(
    rule: Rule,
    order_number: str,
    material_groups: set[str],
    article_numbers_by_source: dict[str, set[str]],
) -> RuleResult:
    if rule.acceptance_exception_none_groups:
        exception_groups = {
            normalize(value) for value in rule.acceptance_exception_none_groups
        }
        if not exception_groups.intersection(material_groups):
            return RuleResult(
                order_number=order_number,
                rule_id=rule.rule_id,
                status="AKZEPTIERTE_AUSNAHME",
                reason=rule.acceptance_exception_reason,
                evidence_count=0,
            )

    if rule.requirement_type == "material_group_any":
        expected = {normalize(value) for value in rule.values}
        evidence_count = len(expected.intersection(material_groups))
    elif rule.requirement_type == "article_prefix":
        articles = article_numbers_by_source.get(rule.source, set())
        evidence_count = sum(
            1 for article in articles if any(article.startswith(prefix) for prefix in rule.values)
        )
    else:  # durch load_rules abgesichert
        raise AnalysisError(f"Unbekannter Anforderungstyp: {rule.requirement_type}")

    passed = evidence_count > 0
    return RuleResult(
        order_number=order_number,
        rule_id=rule.rule_id,
        status="BESTANDEN" if passed else "ABWEICHUNG",
        reason=rule.pass_reason if passed else rule.fail_reason,
        evidence_count=evidence_count,
    )

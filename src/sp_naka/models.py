"""Datenmodelle für Regeln und Prüfergebnisse."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    trigger_stages: frozenset[str]
    requirement_type: str
    values: tuple[str, ...]
    source: str
    pass_reason: str
    fail_reason: str
    acceptance_exception_none_groups: tuple[str, ...] = ()
    acceptance_exception_reason: str = ""


@dataclass(frozen=True)
class RuleResult:
    order_number: str
    rule_id: str
    status: str
    reason: str
    evidence_count: int


@dataclass(frozen=True)
class OrderAssessment:
    order_number: str
    order_header_key: str
    order_date: str
    overall_status: str
    applicable_rule_count: int
    passed_rule_count: int
    deviation_count: int
    accepted_exception_count: int
    reason_codes: str
    exception_codes: str
    reasons: str
    manual_review_required: bool

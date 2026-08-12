from __future__ import annotations

import unittest

from sp_naka.models import Rule
from sp_naka.rules import evaluate_rule, rule_applies


class RuleEvaluationTests(unittest.TestCase):
    def test_lacquer_only_satisfies_color_or_lacquer_rule(self) -> None:
        rule = Rule(
            rule_id="DRUCK-FARBE-LACK",
            description="",
            trigger_stages=frozenset({"DRUCK"}),
            requirement_type="material_group_any",
            values=("Farben", "Lacke"),
            source="Fertigungsmaterial.csv",
            pass_reason="ok",
            fail_reason="fehlt",
        )

        result = evaluate_rule(rule, "1", {"lacke"}, {})

        self.assertTrue(rule_applies(rule, {"DRUCK"}))
        self.assertEqual("BESTANDEN", result.status)
        self.assertEqual(1, result.evidence_count)

    def test_missing_print_material_is_deviation(self) -> None:
        rule = Rule(
            rule_id="DRUCK-PLATTE",
            description="",
            trigger_stages=frozenset({"DRUCK"}),
            requirement_type="material_group_any",
            values=("Druckplatten",),
            source="Fertigungsmaterial.csv",
            pass_reason="ok",
            fail_reason="fehlt",
        )

        result = evaluate_rule(rule, "1", set(), {})

        self.assertEqual("ABWEICHUNG", result.status)
        self.assertEqual(0, result.evidence_count)

    def test_missing_plate_and_color_is_accepted_exception(self) -> None:
        rule = Rule(
            rule_id="DRUCK-PLATTE",
            description="",
            trigger_stages=frozenset({"DRUCK"}),
            requirement_type="material_group_any",
            values=("Druckplatten",),
            source="Fertigungsmaterial.csv",
            pass_reason="ok",
            fail_reason="fehlt",
            acceptance_exception_none_groups=("Druckplatten", "Farben"),
            acceptance_exception_reason="fachlich akzeptiert",
        )

        result = evaluate_rule(rule, "1", {"lacke"}, {})

        self.assertEqual("AKZEPTIERTE_AUSNAHME", result.status)
        self.assertEqual("fachlich akzeptiert", result.reason)

    def test_wellkarton_prefix_must_start_with_94(self) -> None:
        rule = Rule(
            rule_id="WELLKARTON",
            description="",
            trigger_stages=frozenset({"KLEBEN"}),
            requirement_type="article_prefix",
            values=("94",),
            source="Fertigungsmaterial.csv",
            pass_reason="ok",
            fail_reason="fehlt",
        )
        present = {"Fertigungsmaterial.csv": {"94001"}}
        embedded_only = {"Fertigungsmaterial.csv": {"194001"}}

        self.assertEqual("BESTANDEN", evaluate_rule(rule, "1", set(), present).status)
        self.assertEqual(
            "ABWEICHUNG", evaluate_rule(rule, "1", set(), embedded_only).status
        )

    def test_wellkarton_is_checked_in_configured_source(self) -> None:
        rule = Rule(
            rule_id="WELLKARTON-BUCHUNG",
            description="",
            trigger_stages=frozenset({"AUFRICHT"}),
            requirement_type="article_prefix",
            values=("94",),
            source="RW_Buchungen.csv",
            pass_reason="ok",
            fail_reason="fehlt",
        )
        only_consumed = {"Fertigungsmaterial.csv": {"94001"}}

        result = evaluate_rule(rule, "1", set(), only_consumed)

        self.assertEqual("ABWEICHUNG", result.status)


if __name__ == "__main__":
    unittest.main()

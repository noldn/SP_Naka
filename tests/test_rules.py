from __future__ import annotations

import unittest

from sp_naka.models import Rule
from sp_naka.rules import evaluate_rule, rule_applies


class RuleEvaluationTests(unittest.TestCase):
    def test_window_stage_requires_window_film(self) -> None:
        rule = Rule(
            rule_id="FENSTER-FOLIE",
            description="",
            trigger_stages=frozenset({"FENSTER"}),
            requirement_type="material_group_any",
            values=("Fensterfolien",),
            source="Fertigungsmaterial.csv",
            pass_reason="ok",
            fail_reason="fehlt",
        )

        present = evaluate_rule(rule, "1", {"fensterfolien"}, {})
        missing = evaluate_rule(rule, "2", {"kaltfolien"}, {})

        self.assertTrue(rule_applies(rule, {"FENSTER"}))
        self.assertFalse(rule_applies(rule, {"DRUCK"}))
        self.assertEqual("BESTANDEN", present.status)
        self.assertEqual("ABWEICHUNG", missing.status)

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

    def test_mix_article_counts_as_color_and_prevents_empty_print_exception(self) -> None:
        articles = {"Fertigungsmaterial.csv": {"MIX-001"}}
        color_rule = Rule(
            rule_id="DRUCK-FARBE",
            description="",
            trigger_stages=frozenset({"DRUCK"}),
            requirement_type="material_group_any",
            values=("Farben", "Lacke"),
            source="Fertigungsmaterial.csv",
            pass_reason="ok",
            fail_reason="fehlt",
            article_prefixes=("MIX",),
            acceptance_exception_none_groups=("Druckplatten", "Farben"),
            acceptance_exception_none_article_prefixes=("MIX",),
            acceptance_exception_reason="fachlich akzeptiert",
        )
        plate_rule = Rule(
            rule_id="DRUCK-PLATTE",
            description="",
            trigger_stages=frozenset({"DRUCK"}),
            requirement_type="material_group_any",
            values=("Druckplatten",),
            source="Fertigungsmaterial.csv",
            pass_reason="ok",
            fail_reason="fehlt",
            acceptance_exception_none_groups=("Druckplatten", "Farben"),
            acceptance_exception_none_article_prefixes=("MIX",),
            acceptance_exception_reason="fachlich akzeptiert",
        )

        self.assertEqual(
            "BESTANDEN", evaluate_rule(color_rule, "1", {"fehler"}, articles).status
        )
        self.assertEqual(
            "ABWEICHUNG", evaluate_rule(plate_rule, "1", {"fehler"}, articles).status
        )

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

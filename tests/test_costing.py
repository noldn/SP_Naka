from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from sp_naka.costing import _commercial_assessment, assess_order_costs, is_afterproduction


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


class CostingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        write_csv(
            self.root / "Zuschlaege.csv",
            ["Zuschlagsart", "Stundensatz", "ZuschlagVariabel", "ZuschlagFix", "GueltigVon", "GueltigBis"],
            [
                ["MatGemeinkosten", "2", "20", "0", "01.01.2020", "31.12.2099"],
                ["VVZuschlag", "2", "10", "100", "01.01.2020", "31.12.2099"],
                ["Nichtdefiniert", "2", "99", "999", "01.01.2020", "31.12.2099"],
            ],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _assessment(self, official: str = "536") -> dict[str, object]:
        return assess_order_costs(
            self.root,
            {"BelegNummer": "100", "BelegDatum": "01.01.2024", "Erlöse": "450", "Kosten": official, "Zusatztext": "Nachprodukiton Reklamation"},
            [],
            [{"Auftrag": "100", "Stufe": "DRUCK", "KSTKurz": "M1", "Dauer": "2", "Menge": "100", "Kosten": "200"}],
            [
                {"Artikel": "A1", "ArtikelGruppe": "01", "Materialwert": "120"},
                {"Artikel": "F1", "ArtikelGruppe": "05", "Materialwert": "10"},
            ],
            [{"Artikel": "A1", "ArtikelGruppe": "01", "Menge": "6"}],
            [
                {"Artikel": "A1", "ArtikelGruppe": "01", "Menge": "-10", "WertMat": "-100"},
                {"Artikel": "A1", "ArtikelGruppe": "01", "Menge": "2", "WertMat": "20"},
            ],
            [{"WarenwertEUR": "50"}],
            [
                {"TrKoArt": "250950", "Betrag": "30"},
                {"TrKoArt": "7300", "Betrag": "20"},
                {"TrKoArt": "9999", "Betrag": "10"},
            ],
        )

    def test_actual_costs_surcharges_and_theory_are_reconciled(self) -> None:
        result = self._assessment()

        self.assertEqual(90.0, result["actual_material_cost"])
        self.assertEqual(16.0, result["material_surcharge"])
        self.assertEqual(20.0, result["vv_surcharge"])
        self.assertEqual(536.0, result["reconstructed_cost"])
        self.assertEqual("OK", result["reconciliation_status"])
        self.assertEqual(0.0, result["theoretical_invoice_cost"])
        self.assertEqual(462.0, result["theoretical_total_cost"])
        self.assertTrue(result["price_critical"])
        self.assertIn("PREIS_KRITISCH", result["reason_codes"])

    def test_reconciliation_thresholds_require_absolute_and_relative_limit(self) -> None:
        self.assertEqual("WARNUNG", self._assessment("400")["reconciliation_status"])
        self.assertEqual("KRITISCH", self._assessment("30")["reconciliation_status"])

    def test_closed_order_uses_delivered_quantity_for_billing(self) -> None:
        positions = [
            {"PositionsNr": "1", "Artikel": "A", "Menge": "100", "gelieferte_Menge": "115", "EinzelpreismZuAbschl": "10", "Preiseinheitsfaktor": "1", "WertPosition": "0", "ArtikelGruppe": "01"},
            {"PositionsNr": "2", "Artikel": "ZK", "Menge": "1", "gelieferte_Menge": "0", "EinzelpreismZuAbschl": "100", "Preiseinheitsfaktor": "1", "WertPosition": "1", "ArtikelGruppe": "30", "ArtikelGruppeBez": "Sonderkosten"},
            {"PositionsNr": "3", "Artikel": "OHNE", "Menge": "10", "gelieferte_Menge": "0", "EinzelpreismZuAbschl": "0", "Preiseinheitsfaktor": "1", "WertPosition": "0"},
        ]

        result = _commercial_assessment(
            {"offen": "0"}, positions,
            [{"Summe_Rechnung_EUR": "1250", "Summe_Gutschrift_EUR": "0", "Erloes_EUR": "1250", "Anzahl_Gutschriften": "0"}],
        )

        self.assertEqual(1250.0, result["theoretical_billing_value"])
        self.assertEqual("OK", result["delivery_status"])
        self.assertEqual("OK", result["billing_status"])
        self.assertEqual(100.0, result["special_cost_value"])
        self.assertEqual("OK", result["special_cost_status"])

    def test_underdelivery_requires_review_only_without_credit(self) -> None:
        position = {"PositionsNr": "1", "Artikel": "A", "Menge": "100", "gelieferte_Menge": "89.99", "Einzelpreis": "10", "Preiseinheitsfaktor": "1", "WertPosition": "0"}

        without_credit = _commercial_assessment({"offen": "0"}, [position], [])
        with_credit = _commercial_assessment(
            {"offen": "0"}, [position],
            [{"Summe_Rechnung_EUR": "899.90", "Summe_Gutschrift_EUR": "100", "Erloes_EUR": "799.90", "Anzahl_Gutschriften": "1"}],
        )

        self.assertEqual("PRUEFEN", without_credit["delivery_status"])
        self.assertEqual("OK_MIT_GUTSCHRIFT", with_credit["delivery_status"])

        position["gelieferte_Menge"] = "90"
        boundary = _commercial_assessment({"offen": "0"}, [position], [])
        self.assertEqual("OK", boundary["delivery_status"])

    def test_billing_rounding_tolerance_and_special_cost_review(self) -> None:
        position = {"PositionsNr": "1", "Artikel": "ZK", "Menge": "1", "gelieferte_Menge": "0", "Einzelpreis": "100", "Preiseinheitsfaktor": "1", "WertPosition": "1", "ArtikelGruppe": "30"}

        boundary = _commercial_assessment(
            {"offen": "0"}, [position],
            [{"Summe_Rechnung_EUR": "101", "Erloes_EUR": "101"}],
        )
        mismatch = _commercial_assessment(
            {"offen": "0"}, [position],
            [{"Summe_Rechnung_EUR": "101.01", "Erloes_EUR": "101.01"}],
        )

        self.assertEqual("OK", boundary["billing_status"])
        self.assertEqual("PRUEFEN", mismatch["billing_status"])
        self.assertEqual("PRUEFEN", mismatch["special_cost_status"])

    def test_open_order_and_missing_faktura_are_distinguished(self) -> None:
        position = {"PositionsNr": "1", "Artikel": "A", "Menge": "100", "gelieferte_Menge": "100", "Einzelpreis": "10", "Preiseinheitsfaktor": "1", "WertPosition": "0"}

        open_order = _commercial_assessment({"offen": "1"}, [position], [])
        closed_order = _commercial_assessment({"offen": "0"}, [position], [])

        self.assertEqual("OFFENER_AUFTRAG", open_order["billing_status"])
        self.assertEqual("PRUEFEN_DATEN_FEHLEN", closed_order["billing_status"])

    def test_afterproduction_spelling_variants_use_prefix(self) -> None:
        self.assertTrue(is_afterproduction("Nachproduktion"))
        self.assertTrue(is_afterproduction("Nachprod Reklamation"))
        self.assertTrue(is_afterproduction("Nachprodukiton"))
        self.assertFalse(is_afterproduction("normale Produktion"))

    def test_ideal_production_uses_p75_of_at_least_five_peers(self) -> None:
        profiles = {
            ("WM", "WM-1", "DRUCK", "M1"): [
                (f"P{index}", performance)
                for index, performance in enumerate([40.0, 50.0, 60.0, 70.0, 80.0], start=1)
            ]
        }
        result = assess_order_costs(
            self.root,
            {"BelegNummer": "100", "BelegDatum": "01.01.2024", "Erlöse": "1000", "Kosten": "500"},
            [{"Muster": "WM-1"}],
            [{"Stufe": "DRUCK", "KSTKurz": "M1", "Dauer": "2", "Menge": "100", "Kosten": "200"}],
            [], [], [], [], [], self.root, profiles,
        )

        detail = result["theoretical_production_details"][0]
        self.assertEqual(70.0, detail["ideal_performance"])
        self.assertEqual("SAME_WM_MACHINE_STAGE", detail["reference_level"])
        self.assertAlmostEqual(142.85714285714286, detail["theoretical_cost"])

    def test_group_alternative_is_not_counted_again_as_actual_material(self) -> None:
        result = assess_order_costs(
            self.root,
            {"BelegNummer": "100", "BelegDatum": "01.01.2024", "Erlöse": "1000", "Kosten": "300"},
            [], [], [],
            [{"Artikel": "PLAN", "ArtikelGruppe": "01", "Menge": "5"}],
            [{"Artikel": "ALT", "ArtikelGruppe": "01", "Menge": "-10", "WertMat": "-100"}],
            [], [], self.root, {},
        )

        self.assertEqual(50.0, result["theoretical_material_cost"])
        detail = result["theoretical_material_details"][0]
        self.assertEqual("ARTICLE_GROUP_ALTERNATIVE", detail["match_level"])

    def test_positive_raw_correction_reduces_actual_cost(self) -> None:
        result = assess_order_costs(
            self.root,
            {"BelegNummer": "100", "BelegDatum": "01.01.2024", "Erlöse": "1000", "Kosten": "100"},
            [], [], [], [],
            [
                {"Artikel": "RAW", "ArtikelGruppe": "01", "Menge": "-100", "WertMat": "-100"},
                {"Artikel": "RAW", "ArtikelGruppe": "01", "Menge": "120", "WertMat": "120"},
            ],
            [], [], self.root, {},
        )

        self.assertEqual(-20.0, result["actual_material_cost"])


if __name__ == "__main__":
    unittest.main()

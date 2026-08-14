from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from sp_naka.errors import AnalysisError
from sp_naka.performance import _quantity_bucket, analyze_performance, load_parameters


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def write_dataset(path: Path, margins: list[float], prefix: str) -> None:
    path.mkdir()
    heads = []
    sales = []
    planning = []
    times = []
    material = []
    rw = []
    raw_positions = []
    invoices = []
    for index, margin_rate in enumerate(margins, start=1):
        order = f"{prefix}{index}"
        key = f"K{order}"
        revenue = 1000.0
        cost = revenue - revenue * margin_rate
        heads.append(["01.01.2026", key, "C1", order, "PG", revenue, cost])
        sales.append([key, 1000, "WM-ONE"])
        planning.append([order, "FORM-ONE", 46000 + index / 24])
        times.append([order, 10, "", "", "PRODUKTION", "DRUCK"])
        material.append([order, "P1", "Papier", 100])
    write_csv(path / "Auftragskopf.csv", ["BelegDatum", "BelegKopfKey", "Kunde Key", "BelegNummer", "X_ArtikelGruppe", "Erlöse", "Kosten"], heads)
    write_csv(path / "VertriebsPositionen.csv", ["BelegKopfKey", "Menge", "Muster"], sales)
    write_csv(path / "Planung.csv", ["AuftragNr", "STANZFORM", "AuftragFertigDatum"], planning)
    write_csv(path / "ProdZeiten.csv", ["Auftrag", "DauerMaschine", "Dauer", "Mehraufwand Id", "ARVOKurz", "Stufe"], times)
    write_csv(path / "Fertigungsmaterial.csv", ["Auftrag", "Artikel", "GruppeBezeichnung", "Materialwert"], material)
    write_csv(path / "RW_Buchungen.csv", ["BelegNummer", "Artikel", "Menge", "WertMat"], rw)
    write_csv(path / "RohwarenPos.csv", ["BelegNummer", "Artikel", "Menge"], raw_positions)
    write_csv(path / "Rechnungskontrollen.csv", ["Traeger", "Artikel Key"], invoices)


class PerformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.reference = self.root / "reference"
        self.scoring = self.root / "scoring"
        write_dataset(self.reference, [0.08, 0.09, 0.10, 0.11, 0.12], "R")
        write_dataset(self.scoring, [-0.80], "S")
        write_csv(
            self.scoring / "ProdZeiten.csv",
            ["Auftrag", "DauerMaschine", "Dauer", "Mehraufwand Id", "ARVOKurz", "Stufe"],
            [["S1", 100, "", "M1", "Druckabstimmung", "HAND"]],
        )
        write_csv(
            self.scoring / "Fertigungsmaterial.csv",
            ["Auftrag", "Artikel", "GruppeBezeichnung", "Materialwert"],
            [["S1", "94001", "Papier", 500]],
        )
        self.parameters = self.root / "parameters.json"
        self.parameters.write_text(json.dumps({
            "performance": {
                "minimum_peer_group_size": 5,
                "robust_z_warning_threshold": 2.0,
                "robust_z_threshold": 3.5,
                "quantity_buckets": [1000, 5000],
            },
            "series_detection": {"minimum_hours": 12, "maximum_hours": 24},
            "raw_material_quantity_check": {
                "levels": [
                    {"minimum_ratio": 1.1, "status": "HINWEIS"},
                    {"minimum_ratio": 1.25, "status": "PRUEFEN"},
                    {"minimum_ratio": 1.5, "status": "KRITISCH"},
                ]
            },
            "material_factors": {"paper_cardboard_groups": ["Papier", "Karton"]},
            "article_identification": {
                "construction_prefix": "WM",
                "invoice_article_company_separator": "|",
                "die_form_service_prefix": "WS",
                "wellboard_prefix": "94",
            },
        }), encoding="utf-8")
        self.customers = self.root / "customers.csv"
        write_csv(self.customers, ["customer_key"], [["C1"]])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_negative_outlier_gets_explainable_evidence(self) -> None:
        write_csv(
            self.scoring / "RW_Buchungen.csv",
            ["BelegNummer", "Artikel", "Menge", "WertMat"],
            [["S1", "R1", -150, -20]],
        )
        write_csv(
            self.scoring / "RohwarenPos.csv",
            ["BelegNummer", "Artikel", "Menge"],
            [["S1", "R1", 100]],
        )
        rows, summary = analyze_performance(
            self.reference, self.scoring, self.parameters, self.customers, "test"
        )

        self.assertEqual("SEHR_NEGATIV", rows[0]["performance_status"])
        self.assertTrue(rows[0]["accepted_negative_customer"])
        self.assertIn("DRUCKABSTIMMUNG_ERKANNT", rows[0]["reason_codes"])
        self.assertIn("HANDARBEIT_MIT_AUSSERGEWOEHNLICHEM_AUFWAND", rows[0]["reason_codes"])
        self.assertEqual("Fertigungsmaterial.csv_FALLBACK", rows[0]["wellboard_cost_source"])
        self.assertIn("ROHWARENMENGE_KRITISCH", rows[0]["reason_codes"])
        self.assertEqual("KRITISCH", rows[0]["raw_material_quantity_status"])
        self.assertEqual("CORRECTION_CONFIRMATION_REQUIRED", rows[0]["reason_review_status"])
        self.assertGreater(rows[0]["total_material_share_of_revenue"], 0)
        self.assertEqual(5, summary["training_orders"])

    def test_quantity_bucket_boundary_is_inclusive(self) -> None:
        self.assertEqual("1-1000", _quantity_bucket(1000, [1000, 5000]))
        self.assertEqual("1001-5000", _quantity_bucket(1000.01, [1000, 5000]))
        self.assertEqual("UNKNOWN", _quantity_bucket(None, [1000, 5000]))

    def test_planned_handwork_alone_is_not_a_negative_reason(self) -> None:
        write_csv(
            self.scoring / "ProdZeiten.csv",
            ["Auftrag", "DauerMaschine", "Dauer", "Mehraufwand Id", "ARVOKurz", "Stufe"],
            [["S1", 100, "", "", "Handarbeit geplant", "HAND"]],
        )

        rows, _ = analyze_performance(
            self.reference, self.scoring, self.parameters, self.customers, "test"
        )

        self.assertTrue(rows[0]["handwork_present"])
        self.assertNotIn("HANDARBEIT_MIT_AUSSERGEWOEHNLICHEM_AUFWAND", rows[0]["reason_codes"])

    def test_invalid_minimum_peer_group_size_is_rejected(self) -> None:
        content = json.loads(self.parameters.read_text(encoding="utf-8"))
        content["performance"]["minimum_peer_group_size"] = 2
        self.parameters.write_text(json.dumps(content), encoding="utf-8")

        with self.assertRaisesRegex(AnalysisError, "Ungültige Peer"):
            load_parameters(self.parameters)

    def test_invalid_raw_material_warning_ratio_is_rejected(self) -> None:
        content = json.loads(self.parameters.read_text(encoding="utf-8"))
        content["raw_material_quantity_check"]["levels"][0]["minimum_ratio"] = 1
        self.parameters.write_text(json.dumps(content), encoding="utf-8")

        with self.assertRaisesRegex(AnalysisError, "Rohwaren-Mengenstufen"):
            analyze_performance(
                self.reference, self.scoring, self.parameters, self.customers, "test"
            )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from sp_naka.errors import AnalysisError
from sp_naka.nachkalkulation import load_order_calculation


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


class NachkalkulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        write_csv(
            self.root / "Auftragskopf.csv",
            ["BelegNummer", "BelegKopfKey", "Erlöse", "Kosten", "Zusatztext"],
            [["100", "K100", "1000,00", "1200,00", "Testauftrag"]],
        )
        write_csv(
            self.root / "VertriebsPositionen.csv",
            ["BelegKopfKey", "PositionsNr", "Artikel", "Menge"],
            [["K100", "1", "V1", "100"]],
        )
        write_csv(
            self.root / "ProdZeiten.csv",
            ["Auftrag", "Stufe", "Dauer", "DauerMaschine", "DauerMF", "Menge", "Kosten", "Mehraufwand Id"],
            [["100", "DRUCK", "2,5", "2", "1,5", "100", "0", "M1"]],
        )
        write_csv(
            self.root / "Fertigungsmaterial.csv",
            ["Auftrag", "Artikel", "ArtikelGruppeBez", "Materialwert"],
            [["100", "A1", "Papier", "10"], ["100", "A2", "Farben", "5"]],
        )
        write_csv(
            self.root / "RW_Buchungen.csv",
            ["BelegNummer", "Artikel", "WertMat"],
            [["100", "A1", "-12"]],
        )
        write_csv(
            self.root / "KTRBuchungenKI.csv",
            ["KostenTraeger", "Betrag"],
            [["100", "3"]],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_order_view_uses_official_total_and_non_duplicate_detail_costs(self) -> None:
        result = load_order_calculation(self.root, "100")

        self.assertEqual(-200.0, result["result"])
        self.assertEqual(20.0, result["reconstructed_direct_costs"])
        self.assertEqual(2.5, result["production_summary"][0]["duration"])
        self.assertEqual(40.0, result["production_summary"][0]["performance"])
        self.assertFalse(result["production_detail_available"])
        self.assertIn("ausschließlich 0", " ".join(result["limitations"]))
        self.assertEqual("Testauftrag", result["header"]["Zusatztext"])

    def test_production_performance_is_unknown_when_total_duration_is_zero(self) -> None:
        write_csv(
            self.root / "ProdZeiten.csv",
            ["Auftrag", "Stufe", "Dauer", "DauerMaschine", "DauerMF", "Menge", "Kosten", "Mehraufwand Id"],
            [["100", "DRUCK", "0", "0", "0", "100", "0", ""]],
        )

        result = load_order_calculation(self.root, "100")

        self.assertIsNone(result["production_summary"][0]["performance"])

    def test_invalid_order_number_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalysisError, "unzulässige Zeichen"):
            load_order_calculation(self.root, "../100")


if __name__ == "__main__":
    unittest.main()

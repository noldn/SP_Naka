from __future__ import annotations

import csv
import stat
import tempfile
import unittest
from pathlib import Path

from sp_naka.csv_io import sha256_file
from sp_naka.errors import AnalysisError
from sp_naka.pipeline import run_analysis


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = PROJECT_ROOT / "config" / "rules.json"


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class PipelineIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.output = self.root / "output"
        self.data.mkdir()

        write_csv(
            self.data / "Auftragskopf.csv",
            ["BelegNummer", "BelegKopfKey", "BelegDatum"],
            [
                ["100", "K100", "01.01.2026"],
                ["200", "K200", "02.01.2026"],
                ["300", "K300", "03.01.2026"],
                ["400", "K400", "04.01.2026"],
                ["500", "K500", "05.01.2026"],
            ],
        )
        write_csv(
            self.data / "Planung.csv",
            ["AuftragNr", "Stufe"],
            [
                ["100", "DRUCK"],
                ["200", "KLEBEN"],
                ["300", "AUFRICHTEN"],
                ["400", "HAND"],
                ["500", "DRUCK"],
            ],
        )
        write_csv(
            self.data / "ProdZeiten.csv",
            ["Auftrag", "Stufe"],
            [["100", "DRUCK"], ["200", "KLEB"], ["300", "AUFRICHT"]],
        )
        write_csv(
            self.data / "Fertigungsmaterial.csv",
            ["Auftrag", "Artikel", "ArtikelGruppeBez"],
            [
                ["100", "PL1", "Druckplatten"],
                ["100", "LA1", "Lacke"],
                ["200", "94001", "Karton"],
                ["300", "94002", "Karton"],
            ],
        )
        write_csv(
            self.data / "RW_Buchungen.csv",
            ["BelegNummer", "Artikel"],
            [["200", "94001"]],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_pipeline_creates_explainable_results_without_changing_sources(self) -> None:
        before = {
            path.name: sha256_file(path) for path in self.data.glob("*.csv")
        }

        run_dir = run_analysis(
            self.data, self.output, RULES_PATH, run_id="integration-test"
        )

        after = {path.name: sha256_file(path) for path in self.data.glob("*.csv")}
        self.assertEqual(before, after)
        assessments = {
            row["order_number"]: row
            for row in read_csv(run_dir / "order_assessments.csv")
        }
        self.assertEqual("REGELKONFORM", assessments["100"]["overall_status"])
        self.assertEqual("REGELKONFORM", assessments["200"]["overall_status"])
        self.assertEqual("ABWEICHUNG", assessments["300"]["overall_status"])
        self.assertEqual("NICHT_BEWERTET", assessments["400"]["overall_status"])
        self.assertEqual(
            "REGELKONFORM_MIT_AUSNAHME", assessments["500"]["overall_status"]
        )
        self.assertEqual("2", assessments["500"]["accepted_exception_count"])
        self.assertEqual("False", assessments["500"]["manual_review_required"])
        self.assertEqual("True", assessments["300"]["manual_review_required"])
        feedback = read_csv(run_dir / "manual_review_template.csv")
        self.assertEqual(1, len(feedback))
        self.assertEqual("MAT-KLEB-AUFRICHT-WELLKARTON-BUCHUNG", feedback[0]["rule_id"])
        rule_results = read_csv(run_dir / "rule_results.csv")
        self.assertFalse(
            any("WELLKARTON-VERBRAUCH" in row["rule_id"] for row in rule_results)
        )
        self.assertTrue((run_dir / "run_manifest.json").is_file())
        if hasattr(run_dir.stat(), "st_flags") and hasattr(stat, "UF_HIDDEN"):
            self.assertEqual(0, run_dir.stat().st_flags & stat.UF_HIDDEN)

    def test_hidden_run_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalysisError, "run_id"):
            run_analysis(self.data, self.output, RULES_PATH, run_id=".hidden")

    def test_missing_required_column_stops_run(self) -> None:
        write_csv(
            self.data / "Auftragskopf.csv",
            ["BelegNummer", "BelegKopfKey"],
            [["100", "K100"]],
        )

        with self.assertRaisesRegex(AnalysisError, "Pflichtfelder fehlen"):
            run_analysis(self.data, self.output, RULES_PATH, run_id="invalid")

        self.assertFalse((self.output / "invalid").exists())

    def test_empty_material_article_is_reported_and_not_silently_used(self) -> None:
        write_csv(
            self.data / "Fertigungsmaterial.csv",
            ["Auftrag", "Artikel", "ArtikelGruppeBez"],
            [["100", "", "Druckplatten"], ["100", "LA1", "Lacke"]],
        )

        run_dir = run_analysis(
            self.data, self.output, RULES_PATH, run_id="quality-issue"
        )

        issues = read_csv(run_dir / "data_quality_issues.csv")
        self.assertEqual(1, len(issues))
        self.assertEqual("EMPTY_REQUIRED_VALUE", issues[0]["issue_code"])
        self.assertEqual("Artikel", issues[0]["field"])

    def test_output_inside_source_is_rejected(self) -> None:
        with self.assertRaisesRegex(AnalysisError, "nicht im Quelldatenverzeichnis"):
            run_analysis(
                self.data,
                self.data / "results",
                RULES_PATH,
                run_id="unsafe-output",
            )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sp_naka.errors import AnalysisError
from sp_naka.webapp import WebApplication, _safe_run_dir


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class WebApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()
        (self.root / "data" / "local").mkdir(parents=True)
        (self.root / "output" / "runs").mkdir(parents=True)
        (self.root / "config" / "analysis_parameters.json").write_text(
            (PROJECT_ROOT / "config" / "analysis_parameters.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (self.root / "config" / "rules.json").write_text("{}\n", encoding="utf-8")
        self.app = WebApplication(self.root)
        for name in ("standard", "training", "reference"):
            (self.root / name).mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_local_settings_and_customer_master_are_saved_outside_config(self) -> None:
        form = {
            "standard_data_dir": [str(self.root / "standard")],
            "training_data_dir": [str(self.root / "training")],
            "reference_data_dir": [str(self.root / "reference")],
            "output_dir": [str(self.root / "output" / "runs")],
            "schedule_enabled": ["on"],
            "schedule_time": ["03:15"],
            "schedule_process": ["standard"],
            "minimum_peer_group_size": ["6"],
            "robust_z_warning_threshold": ["2.1"],
            "robust_z_threshold": ["3.6"],
            "raw_hint": ["1.08"],
            "raw_review": ["1.2"],
            "raw_critical": ["1.4"],
            "accepted_customers": ["100001\n100002"],
        }

        self.app.save_settings(form)

        config = json.loads(self.app.web_config_path.read_text(encoding="utf-8"))
        parameters = json.loads(self.app.local_parameters_path.read_text(encoding="utf-8"))
        customers = self.app.customers_path.read_text(encoding="utf-8-sig")
        self.assertTrue(config["schedule_enabled"])
        self.assertEqual(6, parameters["performance"]["minimum_peer_group_size"])
        self.assertIn("100001", customers)
        self.assertNotEqual(
            self.app.local_parameters_path,
            self.root / "config" / "analysis_parameters.json",
        )

    def test_invalid_schedule_time_is_rejected(self) -> None:
        form = {
            "standard_data_dir": [str(self.root / "standard")],
            "training_data_dir": [str(self.root / "training")],
            "reference_data_dir": [str(self.root / "reference")],
            "output_dir": [str(self.root / "output" / "runs")],
            "schedule_time": ["25:99"], "schedule_process": ["standard"],
        }
        with self.assertRaisesRegex(AnalysisError, "Planzeit"):
            self.app.save_settings(form)

    def test_run_directory_cannot_escape_output_root(self) -> None:
        run = self.root / "output" / "runs" / "valid-run"
        run.mkdir()
        self.assertEqual(run.resolve(), _safe_run_dir(self.root / "output" / "runs", "valid-run"))
        self.assertIsNone(_safe_run_dir(self.root / "output" / "runs", "../outside"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sp_naka.csv_io import read_rows, write_csv


class CsvOutputSafetyTests(unittest.TestCase):
    def test_formula_like_text_is_neutralized_in_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.csv"
            write_csv(path, ["value"], [{"value": "=unsafe"}])

            result = list(read_rows(Path(directory), "result.csv"))

        self.assertEqual("'=unsafe", result[0]["value"])


if __name__ == "__main__":
    unittest.main()

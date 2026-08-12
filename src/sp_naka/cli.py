"""Kommandozeileneinstieg für SP_Naka."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .errors import AnalysisError
from .pipeline import run_analysis


def _dotenv_value(path: Path, key: str) -> str | None:
    if not path.is_file():
        return None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == key:
            return value.strip().strip('"').strip("'")
    return None


def _configured_path(value: str | None, project_root: Path, fallback: Path) -> Path:
    if not value:
        return fallback
    path = Path(value).expanduser()
    return path if path.is_absolute() else project_root / path


def build_parser(project_root: Path) -> argparse.ArgumentParser:
    env_data = os.environ.get("SP_NAKA_DATA_DIR") or _dotenv_value(
        project_root / ".env", "SP_NAKA_DATA_DIR"
    )
    env_output = os.environ.get("SP_NAKA_OUTPUT_DIR") or _dotenv_value(
        project_root / ".env", "SP_NAKA_OUTPUT_DIR"
    )
    default_data = _configured_path(
        env_data, project_root, project_root / "data" / "local"
    )
    default_output = _configured_path(
        env_output, project_root, project_root / "output" / "runs"
    )
    parser = argparse.ArgumentParser(
        description="Deterministische Materialprüfung für SP_Naka-Aufträge."
    )
    parser.add_argument("--data-dir", type=Path, default=default_data)
    parser.add_argument("--output-dir", type=Path, default=default_output)
    parser.add_argument("--rules", type=Path, default=project_root / "config" / "rules.json")
    parser.add_argument("--run-id", help="Optionale eindeutige Laufkennung.")
    return parser


def main(argv: list[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[2]
    args = build_parser(project_root).parse_args(argv)
    try:
        run_dir = run_analysis(args.data_dir, args.output_dir, args.rules, args.run_id)
    except AnalysisError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"FEHLER: Dateioperation fehlgeschlagen: {exc}", file=sys.stderr)
        return 3

    print("SP_Naka-Prüfung erfolgreich abgeschlossen.")
    print(f"Ergebnisse: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

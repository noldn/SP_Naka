"""Read-only CSV-Zugriff und getrennte Ergebnis-Ausgabe."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from .errors import AnalysisError


REQUIRED_COLUMNS: dict[str, frozenset[str]] = {
    "Auftragskopf.csv": frozenset({"BelegNummer", "BelegKopfKey", "BelegDatum"}),
    "Planung.csv": frozenset({"AuftragNr", "Stufe"}),
    "ProdZeiten.csv": frozenset({"Auftrag", "Stufe"}),
    "Fertigungsmaterial.csv": frozenset({"Auftrag", "Artikel", "GruppeBezeichnung"}),
    "RW_Buchungen.csv": frozenset({"BelegNummer", "Artikel"}),
}

NONEMPTY_COLUMNS: dict[str, frozenset[str]] = {
    "Auftragskopf.csv": frozenset({"BelegNummer", "BelegKopfKey", "BelegDatum"}),
    "Planung.csv": frozenset({"AuftragNr", "Stufe"}),
    "ProdZeiten.csv": frozenset({"Auftrag"}),
    "Fertigungsmaterial.csv": frozenset({"Auftrag", "Artikel", "GruppeBezeichnung"}),
    "RW_Buchungen.csv": frozenset({"BelegNummer", "Artikel"}),
}


def resolve_source_dir(data_dir: Path) -> Path:
    """Akzeptiert entweder den Exportordner oder dessen Elternordner."""
    candidate = data_dir.expanduser().resolve()
    nested = candidate / "CSV_Original"
    source_dir = nested if nested.is_dir() else candidate
    if not source_dir.is_dir():
        raise AnalysisError(f"Datenverzeichnis nicht gefunden: {source_dir}")
    return source_dir


def validate_output_location(source_dir: Path, output_root: Path) -> None:
    source = source_dir.resolve()
    output = output_root.expanduser().resolve()
    if output == source or output.is_relative_to(source):
        raise AnalysisError(
            "Das Ausgabeverzeichnis darf nicht im Quelldatenverzeichnis liegen."
        )


def validate_sources(source_dir: Path) -> tuple[dict[str, int], list[dict[str, object]]]:
    """Prüft Pflichtdateien, Header, Zeilenform und Schlüssel des Auftragskopfs."""
    row_counts: dict[str, int] = {}
    issues: list[dict[str, object]] = []
    order_numbers: set[str] = set()
    order_keys: set[str] = set()

    for file_name, required in REQUIRED_COLUMNS.items():
        path = source_dir / file_name
        if not path.is_file():
            raise AnalysisError(f"Pflichtdatei fehlt: {file_name}")

        count = 0
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=",", quotechar='"')
            headers = reader.fieldnames or []
            missing = sorted(required.difference(headers))
            if missing:
                raise AnalysisError(
                    f"{file_name}: Pflichtfelder fehlen: {', '.join(missing)}"
                )
            for line_number, row in enumerate(reader, start=2):
                if None in row:
                    raise AnalysisError(
                        f"{file_name}: ungleich lange CSV-Zeile {line_number}"
                    )
                count += 1
                for field in sorted(NONEMPTY_COLUMNS[file_name]):
                    if not row[field].strip():
                        issues.append(
                            {
                                "source_file": file_name,
                                "row_number": line_number,
                                "issue_code": "EMPTY_REQUIRED_VALUE",
                                "field": field,
                                "severity": "WARNING",
                                "handling": "FIELD_IGNORED_FOR_RULE_EVIDENCE",
                            }
                        )
                if file_name == "Auftragskopf.csv":
                    order_number = row["BelegNummer"].strip()
                    order_key = row["BelegKopfKey"].strip()
                    if not order_number or not order_key:
                        raise AnalysisError(
                            f"Auftragskopf.csv: leerer Pflichtschlüssel in Zeile {line_number}"
                        )
                    if order_number in order_numbers or order_key in order_keys:
                        raise AnalysisError(
                            f"Auftragskopf.csv: doppelter Auftragsschlüssel in Zeile {line_number}"
                        )
                    order_numbers.add(order_number)
                    order_keys.add(order_key)
        row_counts[file_name] = count

    return row_counts, issues


def read_rows(source_dir: Path, file_name: str) -> Iterator[dict[str, str]]:
    """Liest Quelldaten ausschließlich im Text-Lesemodus."""
    with (source_dir / file_name).open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        yield from csv.DictReader(handle, delimiter=",", quotechar='"')


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    def safe_row(row: dict[str, object]) -> dict[str, object]:
        safe: dict[str, object] = {}
        for key, value in row.items():
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                safe[key] = "'" + value
            else:
                safe[key] = value
        return safe

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(safe_row(row) for row in rows)


def write_json(path: Path, content: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(content, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

"""Erzeugt lokale Arbeitsunterlagen ohne Rohdaten für den Transferrechner."""

from __future__ import annotations

import csv
import shutil
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRANSFER = ROOT / "transfer" / f"SP_Naka_Arbeitsunterlagen_{date.today().isoformat()}"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, fields: list[str], rows: list[dict[str, str]]) -> None:
    path = TRANSFER / name
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def latest_test_run() -> Path | None:
    candidates = []
    for path in (ROOT / "output" / "runs").glob("*/performance_assessments.csv"):
        rows = read_csv(path)
        if len(rows) <= 100:
            candidates.append(path.parent)
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def main() -> None:
    TRANSFER.mkdir(parents=True, exist_ok=True)
    (TRANSFER / "README_TRANSFER.md").write_text(
        """# SP_Naka Arbeitsunterlagen

Dieser Ordner ist für die fachliche Bearbeitung auf dem Arbeitsrechner bestimmt
und wird nicht nach GitHub übertragen. Er enthält keine vollständigen Rohdaten.

Empfohlene Reihenfolge:

1. `TODO_FUER_FACHBEREICH.md` durcharbeiten.
2. Artikelgruppen und Stammdatenanforderungen ergänzen.
3. Auslastungskunden vervollständigen.
4. Die drei vorbereiteten Testfälle fachlich bewerten.
5. Regel- und Abweichungsfeedback dokumentieren.
6. Den gesamten Ordner auf den Entwicklungsrechner zurückgeben.

Keine Passwörter, Zugangsdaten oder vollständigen Datenexporte in diesen Ordner
legen.
""",
        encoding="utf-8",
    )
    (TRANSFER / "TODO_FUER_FACHBEREICH.md").write_text(
        """# Nächste fachliche Aufgaben

## 1. Artikelgruppen in allen Artikeltabellen ergänzen

- `VertriebsPositionen.csv`
- `RohwarenPos.csv`
- `RW_Buchungen.csv`
- `Fertigungsmaterial.csv`
- `Rechnungskontrollen.csv`

Bitte je Tabelle den stabilen Artikel- und Artikelgruppenschlüssel, die
Bezeichnung, Einheit und Gültigkeit bereitstellen. Prüfen, ob die Nummernkreise
zwischen Tabellen identisch sind.

## 2. Fehlende Stammdaten und Zusatzinformationen

- Artikelstamm mit Materialart und Einheit,
- Kundenstamm mit freigegebener Kundengruppe,
- Maschinen- und Kostenstellenstamm inklusive Gültigkeitszeitraum,
- Arbeitsgang-/Stufenmapping zwischen Planung und Ist-Zeiten,
- Stanzform-/Konstruktionsstamm mit Erstanlage und Status,
- Fehler- und Mehraufwandskategorien,
- Mengen-, Preis-, Zeit- und Vorzeichendefinitionen,
- Auftrags-/Produktionsreihenfolge mit belastbaren Zeitstempeln,
- Kennzeichen für geplante Handarbeit und außerplanmäßige Handarbeit,
- Lagerkosten beziehungsweise freigegebene Näherung.

## 3. Auslastungskunden definieren

Liste vervollständigen und Gültigkeitszeiträume, Begründung sowie Freigabe
ergänzen. Diese Aufträge werden weiterhin vollständig auf Daten-, Material- und
relative Performanceabweichungen geprüft.

## 4. Ausgaben und Regeln prüfen

- Sind die gestuften Rohwarenfaktoren 1,10 / 1,25 / 1,50 sinnvoll?
- Sind Papier-/Karton- und Gesamtmaterialfaktor fachlich richtig abgegrenzt?
- Ist die Fensterfolienregel korrekt und gibt es Ausnahmen?
- Sind Peer-Gruppen und Auflagenklassen passend?
- Welche positiven Auffälligkeiten benötigen tatsächlich eine Prüfung?

## 5. Abweichungen und Begründungen prüfen

Für jeden ausgewählten Auftrag dokumentieren:

- Begründung bestätigt oder geändert,
- tatsächliche Korrektur erforderlich: ja/nein,
- Datenfehler oder realer Produktionsfall,
- akzeptierte Ausnahme,
- Regeländerung erforderlich,
- kurze fachliche Erklärung.

## 6. Test-Data-Set ausfüllen

Zunächst die drei vorbereiteten Beispiele bearbeiten. Danach weitere eindeutig
bekannte Positiv-, Negativ-, Grenz- und Fehlerfälle ergänzen. Besonders wertvoll
sind bekannte Druckabstimmungen, Restpaletten, neue Stanzformen, geplante
Handarbeit und echte Leistungsprobleme.
""",
        encoding="utf-8",
    )

    write_csv(
        "Artikelgruppen_Ergaenzung.csv",
        ["source_table", "article_field", "article_key_field", "new_article_group_field", "new_group_description_field", "unit_field", "status", "notes"],
        [
            {"source_table": name, "article_field": article, "article_key_field": key, "new_article_group_field": "", "new_group_description_field": "", "unit_field": "", "status": "OFFEN", "notes": ""}
            for name, article, key in (
                ("VertriebsPositionen.csv", "Artikel", "Artikel Key"),
                ("RohwarenPos.csv", "Artikel", "Artikel Key"),
                ("RW_Buchungen.csv", "Artikel", "Artikel Key"),
                ("Fertigungsmaterial.csv", "Artikel", ""),
                ("Rechnungskontrollen.csv", "", "Artikel Key"),
            )
        ],
    )
    write_csv(
        "Stammdaten_und_Zusatzinformationen.csv",
        ["master_data", "required_fields", "purpose", "available", "source", "notes"],
        [
            {"master_data": "Artikel", "required_fields": "Artikel; Gruppe; Bezeichnung; Einheit; Gültigkeit", "purpose": "Materialfaktoren und Regeln", "available": "", "source": "", "notes": ""},
            {"master_data": "Kunden", "required_fields": "Kunde Key; Gruppe; Gültigkeit", "purpose": "Peer-Gruppen und Auslastung", "available": "", "source": "", "notes": ""},
            {"master_data": "Maschinen/Kostenstellen", "required_fields": "ID; Bezeichnung; Stufe; Gültigkeit", "purpose": "Leistungscluster und Strukturwechsel", "available": "", "source": "", "notes": ""},
            {"master_data": "Arbeitsgänge", "required_fields": "ARVONR; Typ; geplant/ungeplant", "purpose": "Druckabstimmung, Handarbeit, Einrichten", "available": "", "source": "", "notes": ""},
            {"master_data": "Stanzformen/Konstruktionen", "required_fields": "Schlüssel; Erstanlage; Status", "purpose": "Erstauftrag und Folgeauftrag", "available": "", "source": "", "notes": ""},
            {"master_data": "Fehlerkategorien", "required_fields": "Code; Kategorie; Beschreibung; aktiv", "purpose": "kontrolliertes Feedback", "available": "", "source": "", "notes": ""},
        ],
    )

    customers = read_csv(ROOT / "data" / "local" / "master_data" / "accepted_negative_customers.csv")
    write_csv(
        "Auslastungskunden.csv",
        ["customer_key", "active_from", "active_until", "reason", "approved_by", "approved_at"],
        customers,
    )
    write_csv(
        "Regel_Feedback.csv",
        ["rule_id", "change_type", "current_behavior", "desired_behavior", "example_order", "reason", "approved_by", "status"],
        [],
    )

    run_dir = latest_test_run()
    examples: list[dict[str, str]] = []
    if run_dir:
        candidates = [row for row in read_csv(run_dir / "performance_assessments.csv") if row.get("manual_review_required") == "True"]
        for row in candidates[:3]:
            examples.append({
                "order_number": row.get("order_number", ""),
                "current_performance_status": row.get("performance_status", ""),
                "current_reason_codes": row.get("reason_codes", ""),
                "current_explanation": row.get("reason_explanation", ""),
                "expected_performance_status": "BITTE AUSFÜLLEN",
                "expected_reason_codes": "BITTE AUSFÜLLEN",
                "accepted_exception": "",
                "correction_required": "",
                "professional_explanation": "BITTE AUSFÜLLEN",
                "review_status": "OFFEN",
            })
    write_csv(
        "Testset_3_Beispiele.csv",
        ["order_number", "current_performance_status", "current_reason_codes", "current_explanation", "expected_performance_status", "expected_reason_codes", "accepted_exception", "correction_required", "professional_explanation", "review_status"],
        examples,
    )
    shutil.copy2(ROOT / "config" / "master_data_templates" / "error_categories.csv", TRANSFER / "Fehlerkategorien.csv")
    print(TRANSFER)


if __name__ == "__main__":
    main()

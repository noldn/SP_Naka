# Mitwirkung und Entwicklungsablauf

## Vor dem Start

1. `AGENTS.md` und `PROJECT_GOAL.md` lesen.
2. Einen eigenen Branch für die Änderung erstellen.
3. Prüfen, ob Daten, Notizen oder Screenshots vertrauliche Inhalte enthalten.

## Empfohlener Ablauf

```bash
git switch -c feature/kurze-beschreibung
git status
```

Nach der Umsetzung:

```bash
git diff
git status
git add <gezielt-ausgewählte-dateien>
git diff --staged
git commit -m "Kurze Beschreibung"
git push -u origin HEAD
```

Dateien sollen gezielt hinzugefügt werden. Dadurch sinkt das Risiko, versehentlich
lokale Daten oder vertrauliche Notizen zu committen.

## Dokumentation einer Änderung

- Technische Grundsatzentscheidung: `docs/decisions/`
- Laufende Erkenntnis oder Besprechungsnotiz: `docs/notes/`
- Beschreibung eines Datensatzes: `docs/data/DATA_CATALOG.md`
- Benutzerrelevante Änderung: `docs/CHANGELOG.md`
- Für das Intranet aufbereiteter Inhalt: `docs/intranet/`

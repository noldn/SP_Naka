# Leitlinien für Daten

## Grundsatz

Git enthält Programmcode, Schemata, Dokumentation und freigegebene Beispieldaten.
Echte Arbeitsdaten verbleiben lokal oder in einer dafür genehmigten Datenplattform.

## Vor Aufnahme in Git prüfen

- Enthält die Datei personenbezogene oder vertrauliche Informationen?
- Ist die Speicherung außerhalb des Unternehmens zulässig?
- Ist die Quelle genannt und erlaubt die Lizenz eine Weitergabe?
- Lassen sich Personen oder Organisationen trotz Anonymisierung erkennen?
- Wird die Datei für Tests wirklich benötigt?

Wenn eine Frage unklar ist, wird die Datei nicht committed.

## Verarbeitung

- Originaldaten möglichst unverändert und schreibgeschützt behandeln.
- Bereinigungs- und Transformationsschritte im Code abbilden.
- Datenqualität, Ausschlüsse und Annahmen dokumentieren.
- Analyseausgaben nicht ungeprüft als Fakten oder Entscheidungen verwenden.
- Aufbewahrung und Löschung nach den geltenden Unternehmensregeln durchführen.

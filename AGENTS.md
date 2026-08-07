# Entwicklungsleitplanken für SP_Naka

Diese Datei gilt für das gesamte Repository. Menschen und KI-Agenten müssen sie
vor Änderungen lesen und beachten.

## Verbindliche Reihenfolge

1. `PROJECT_GOAL.md` lesen und prüfen, ob die Änderung zum Projektziel passt.
2. Relevante Dokumentation unter `docs/` lesen.
3. Vorhandenen Code und Tests untersuchen, bevor etwas geändert wird.
4. Eine kleine, nachvollziehbare Änderung umsetzen.
5. Passende Tests und Dokumentation aktualisieren.
6. Vor einem Commit prüfen, dass keine lokalen Daten oder Geheimnisse enthalten sind.

## Leitplanken

- Datenschutz, Nachvollziehbarkeit und Reproduzierbarkeit haben Vorrang vor Tempo.
- Echte Rohdaten bleiben in `data/local/` oder außerhalb des Repositorys.
- Eingabedaten werden standardmäßig nur gelesen und niemals stillschweigend verändert.
- Keine personenbezogenen, vertraulichen oder lizenzrechtlich geschützten Inhalte committen.
- Keine Zugangsdaten, Tokens, Kennwörter oder internen URLs in Code oder Dokumentation.
- Pfade und Einstellungen werden konfiguriert, nicht fest in den Code geschrieben.
- Für Tests nur kleine synthetische oder nachweislich anonymisierte Daten verwenden.
- Analyseergebnisse müssen ihre Datenquelle, Methode, Annahmen und Grenzen nennen.
- KI-Ausgaben gelten als Vorschläge und müssen vor fachlicher Verwendung geprüft werden.
- Unsicherheiten dürfen nicht als gesicherte Fakten dargestellt werden.

## Anforderungen an Änderungen

- Neue Funktionen benötigen einen nachvollziehbaren Test oder eine dokumentierte Begründung,
  warum ein automatisierter Test nicht möglich ist.
- Zufallsbasierte Analysen verwenden dokumentierte Seeds, soweit technisch möglich.
- Abhängigkeiten werden sparsam ergänzt und mit Zweck und Version dokumentiert.
- Fehler sollen verständliche Meldungen liefern, ohne vertrauliche Daten auszugeben.
- Generierte Dateien und lokale Analyseergebnisse gehören nicht in Git.
- Architekturentscheidungen werden unter `docs/decisions/` festgehalten.
- Laufende Erkenntnisse gehören unter `docs/notes/`; vertrauliche Notizen nicht.
- Benutzerrelevante Änderungen werden in `docs/CHANGELOG.md` ergänzt.

## Dokumentationsstandard

Markdown (`.md`) ist das Standardformat, weil es reiner Text, Git-fähig und leicht
in ein Intranet übertragbar ist. Jede fachliche Notiz enthält mindestens:

- Datum und Autor/in
- Thema oder Fragestellung
- Quelle beziehungsweise Datenbasis
- Ergebnis oder Entscheidung
- offene Punkte und nächste Schritte

## Definition of Done

Eine Änderung ist abgeschlossen, wenn:

- sie zum dokumentierten Projektziel passt,
- relevante Tests erfolgreich sind,
- die Dokumentation aktuell ist,
- keine lokalen oder vertraulichen Daten im Git-Diff stehen,
- Annahmen und Einschränkungen der Analyse nachvollziehbar sind.

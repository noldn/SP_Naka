# Architektur

## Ziel

SP_Naka trennt ausführbaren Programmcode konsequent von lokalen Daten. Der Code
ist auf GitHub nachvollziehbar, während die Daten ausschließlich auf dem lokalen
Rechner oder in einer später festgelegten, geschützten Datenquelle verbleiben.

## Datenzugriff

Der Datenpfad wird nicht fest in den Programmcode geschrieben. Das Programm liest
ihn aus der Umgebungsvariable `SP_NAKA_DATA_DIR`. Für die lokale Entwicklung wird
diese Variable in der nicht versionierten Datei `.env` gesetzt.

Vorgesehener Ablauf:

```text
.env -> SP_NAKA_DATA_DIR -> Anwendung -> lokale Dateien/Datenbank
```

Dadurch kann das gleiche Programm auf verschiedenen Rechnern mit jeweils eigenen
lokalen Daten verwendet werden.

## Aktueller Analysefluss

```text
lokale CSV-Originale (nur lesend)
  -> Schema- und Schlüsselvalidierung
  -> Zusammenführung je Auftrag
  -> versionierte statische Regeln
  -> getrennte lokale Ergebnisdateien
  -> manuelle Prüfung und kontrolliertes Feedback
```

Die Programmlogik liegt im Python-Paket `src/sp_naka/`. `run_analysis.sh` ist der
einfache Kommandozeileneinstieg. Regeln sind als JSON unter `config/rules.json`
versioniert. Ausgaben werden standardmäßig unter `output/runs/` abgelegt und durch
Git ignoriert.

Jeder Lauf verwendet ein neues Verzeichnis. Erst nachdem alle Ergebnisdateien und
das Laufprotokoll geschrieben wurden, wird der Lauf atomar als vollständig
bereitgestellt. Ein abgebrochener Lauf darf nicht als freigegebenes Ergebnis gelten.

Die Analysefunktion ist von der Bedienoberfläche getrennt. Eine spätere
Weboberfläche soll dieselbe Pipeline aufrufen und keine zweite Fachlogik erhalten.

## Sicherheitsregeln

1. Keine vertraulichen Daten oder Zugangsdaten in Quellcode, Tests oder Logs.
2. Lokale Daten bleiben unter `data/local/` oder außerhalb des Projektordners.
3. Nur `.env.example`, niemals `.env`, wird versioniert.
4. Tests verwenden künstliche oder anonymisierte Testdaten.
5. Vor jedem Push werden `git status` und die staged Änderungen geprüft.

## Festgelegt für die erste Phase

- Programmiersprache: Python 3, zunächst nur Standardbibliothek.
- Bedienung: Kommandozeile über `run_analysis.sh`.
- Eingabe: dokumentierte lokale CSV-Dateien.
- Ausgabe: getrennte lokale CSV-/JSON-Dateien je Lauf.
- Fachlogik: statische Materialregeln vor quantitativer Analyse und Clustering.

## Noch festzulegen

- Web-Framework, Authentifizierung und Betriebsumgebung
- fachliche Toleranzen für Mengen, Zeiten, Kosten und Leistungen
- Merkmale und Validierungsmethode für Clustering
- Deployment- und Release-Strategie

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

## Sicherheitsregeln

1. Keine vertraulichen Daten oder Zugangsdaten in Quellcode, Tests oder Logs.
2. Lokale Daten bleiben unter `data/local/` oder außerhalb des Projektordners.
3. Nur `.env.example`, niemals `.env`, wird versioniert.
4. Tests verwenden künstliche oder anonymisierte Testdaten.
5. Vor jedem Push werden `git status` und die staged Änderungen geprüft.

## Noch festzulegen

- Programmiersprache und Framework
- Format und Umfang der lokalen Daten
- Benutzeroberfläche (CLI, Desktop oder Web)
- Test- und Build-Prozess
- Deployment- und Release-Strategie

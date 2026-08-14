# Lokale Weboberfläche

## Zweck

Die Weboberfläche stellt die vorhandene Analyse-Pipeline lokal im Browser bereit.
Sie ist an der kompakten proALPHA-Arbeitsweise orientiert: Navigationsbereich
links, Funktionsstatus oben und tabellarische Arbeitsbereiche. Sie verwendet keine
proALPHA-Komponenten und greift nicht direkt auf produktive Systeme zu.

## Menüpunkte

### Übersicht

- Status des aktuell laufenden Prozesses,
- Kennzahlen des letzten Laufs,
- manueller Start des Standardprozesses,
- manueller Start des Anlern-/Testprozesses.

Der Standardprozess analysiert den konfigurierten aktuellen Datenbestand. Der
Anlern-/Testprozess bewertet den kleineren Testbestand gegen die historische
Referenz und entfernt die Testaufträge aus dem Training.

### Laufhistorie

- Anzahl vorhandener Läufe,
- letzte zehn Läufe,
- Auftrags- und Prüffallzahlen,
- häufigste statische Abweichungen und Begründungscodes je Lauf,
- häufigste Hinweise über die letzten zehn Läufe.

### Auftragsbewertung

- Auftrag, Zusatzbeschreibung und Bewertung,
- statischer Regelstatus,
- negative beziehungsweise positive Performance,
- erzeugte Begründung,
- Suche nach Auftrag oder Beschreibung.

### Prüfung und Feedback

Es werden nur Aufträge mit statischer oder quantitativer Prüfanforderung
angezeigt. Je Auftrag kann der Anwender:

- die Begründung bestätigen,
- eine Begründung ändern,
- keine Korrektur erforderlich melden,
- einen Datenfehler melden,
- einen Regeländerungsbedarf melden,
- eine tatsächlich notwendige Korrektur kennzeichnen,
- Kommentar und Prüfer dokumentieren.

Klare finanzielle Tatsachen werden direkt gesetzt. Vermutete Ursachen bleiben als
Vorschlag gekennzeichnet; offene Ursachen und mögliche Datenkorrekturen erhalten
einen eigenen Rückmeldestatus.

Feedback wird lokal unter `data/local/feedback/performance_feedback.csv`
gespeichert. Es ändert weder Regeln noch Quelldaten automatisch. Bestätigte
Rückmeldungen werden später kontrolliert in Testfälle oder Regeländerungen
übernommen.

### Parametrierung

- Standard-, Test-, Referenz- und Ausgabepfade,
- Mindestgröße und robuste Warnschwellen der Peer-Gruppen,
- dreistufige Rohwarenfaktoren,
- Auslastungskunden,
- tägliche Ausführungszeit und Prozessart.

Alle Änderungen werden lokal in `data/local/` gespeichert. Versionierte
Standardwerte unter `config/` bleiben unverändert.

## Start ohne Docker

```bash
./run_web.sh
```

Danach `http://localhost:8765` öffnen.

## Start mit Docker

Voraussetzung ist Docker Desktop. Im Projektordner:

```bash
docker compose up -d --build
```

Stoppen:

```bash
docker compose down
```

Die Anwendung ist nur auf `127.0.0.1:8765` veröffentlicht. `data/local/` und
`output/` werden als lokale Verzeichnisse eingebunden und nicht in das Image
kopiert.

## Einfache Installation

- macOS: `install_macos.command` doppelklicken.
- Windows: Rechtsklick auf `install_windows.ps1` und mit PowerShell ausführen.

Der Installer verwendet das vorhandene Projekt oder lädt das private GitHub-
Repository. Bei einem privaten Repository muss GitHub auf dem Rechner bereits
authentifiziert sein. Lokale Git-Änderungen werden nicht automatisch überschrieben.
Anschließend werden Start- und Stoppsymbole auf dem Desktop erzeugt.

## Aufgabenplanung

Die eingebaute tägliche Planung funktioniert, solange der Container oder die
lokale Anwendung läuft. Der letzte geplante Ausführungstag wird lokal gespeichert,
damit ein Lauf am selben Tag nicht doppelt gestartet wird. Für einen späteren
produktiven Betrieb ist ein zentral überwachter Scheduler vorzuziehen.

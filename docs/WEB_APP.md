# Lokale Weboberfläche

## Zweck

Die Weboberfläche stellt die vorhandene Analyse-Pipeline lokal im Browser bereit.
Sie ist an der kompakten proALPHA-Arbeitsweise orientiert: Navigationsbereich
links, Funktionsstatus oben und tabellarische Arbeitsbereiche. Sie verwendet keine
proALPHA-Komponenten und greift nicht direkt auf produktive Systeme zu.

## Menüpunkte

### Nachkalkulation

- direkte Suche nach einer Auftragsnummer ohne vorherigen Analyselauf,
- Auswahl zwischen Test-, Trainings- und Standarddatenbestand,
- Anzeige von Auftragskopf, Positionen, Produktionszeiten und Einzelkostenquellen,
- Leistung je Produktionsabteilung/-stufe als `Summe Menge / Summe ProdZeiten.Dauer`;
  bei einer Gesamtzeit von null bleibt die Leistung unbekannt,
- Anzeige der Systembewertung und vorhandener Testfallhinweise in allen
  Datenbeständen,
- Anzeige der historischen Bestandsfelder `NakaOK`, `NakaBem` und `Status`; diese
  werden von berechneten Reason-Codes und Reason-Erklärungen getrennt dargestellt,
- lokale Erfassung von fachlicher Bewertung, Prüfstatus, Klärung,
  Korrekturbedarf und Prüfer direkt in der Nachkalkulation,
- offizielle Summen aus `Auftragskopf.Erlöse` und `Auftragskopf.Kosten`,
- klar gekennzeichnete Lücken für Produktionsstundensätze, Lagerkosten und
  fixe beziehungsweise variable Zuschläge.

Die rekonstruierte Detailkostensumme ist eine Quellenkontrolle. Sie ersetzt nicht
die offizielle Nachkalkulation, solange Kostenbestandteile fehlen.
Wenn Produktionsmeldungen vorhanden sind, `ProdZeiten.Kosten` für den Auftrag aber
nur Nullwerte enthält, zeigt die Oberfläche ausdrücklich `0,00 € im Export`.
Damit wird dieser Datenzustand von einer fehlenden Kostenquelle unterschieden.

Die Rückmeldungen aus der Nachkalkulation werden je Auftragsnummer und
Datenbestand unter `data/local/feedback/order_clarifications.csv` gespeichert.
Die Datei verändert weder Quelldaten noch Regeln. Ohne passenden Analyselauf zeigt
die Ansicht als vorläufige Systeminformation nur das Vorzeichen des offiziellen
Ergebnisses; sie gibt das nicht als vollständige Performancebewertung aus.

### Empfohlener Stichproben- und Lernablauf

1. `Komplett/CSV` bleibt der unveränderte historische Referenzbestand.
2. Neue Aufträge werden vollständig, also über alle zusammengehörigen CSV-Tabellen,
   in `TestDaten/CSV` bereitgestellt.
3. Der Anlern-/Testprozess bewertet diese Aufträge gegen `Komplett/CSV`. Gleiche
   Auftragsnummern werden dabei aus ihrer eigenen Referenz ausgeschlossen.
4. Der Fachbereich ergänzt Bewertung, Status und Klärung in der Nachkalkulation.
5. Bestätigte Rückmeldungen bilden einen kuratierten Validierungskatalog. Eine
   Übernahme in Regeln oder Referenzdaten erfolgt erst kontrolliert und fachlich
   freigegeben.

Einzelne Zeilen oder Dateien sollten nicht manuell zwischen den Datenbeständen
verschoben werden, weil ein Auftrag über mehrere CSV-Tabellen verbunden ist.

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

Dieses laufbezogene Feedback bleibt zusätzlich zur auftragsbezogenen fachlichen
Klärung in der Nachkalkulation bestehen.

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

Unter Windows kann die Anwendung ohne Docker mit `run_web_windows.ps1` gestartet
werden. Die direkte Nachkalkulationssuche liegt unter
`http://127.0.0.1:8765/calculation`.

Für die bereitgestellte lokale Ordnerstruktur werden standardmäßig
`data/local/TestDaten/CSV` als Testbestand und `data/local/Komplett/CSV` als
historischer Trainings-/Referenzbestand verwendet.

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

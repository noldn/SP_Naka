# Statische Auftragsregeln

## Zweck und Geltungsbereich

Die erste Prüfphase bewertet ausschließlich nachvollziehbare Materialabhängigkeiten.
Sie bewertet noch keine Kostenabweichungen, Mengenstreuungen, Produktivität oder
Gesamtperformance. Diese Trennung verhindert, dass normale Produktionsschwankungen
vorzeitig als Fehler interpretiert werden.

Die ausführbare Konfiguration liegt in `config/rules.json`. Jede Änderung benötigt
eine fachliche Begründung, Tests und eine neue Regelversionsnummer.

## Bewertungsstatus

| Status | Bedeutung |
|---|---|
| `REGELKONFORM` | Mindestens eine Regel war anwendbar und alle anwendbaren Regeln wurden bestanden. |
| `REGELKONFORM_MIT_AUSNAHME` | Alle anwendbaren Regeln sind bestanden oder durch eine ausdrücklich freigegebene automatische Ausnahme akzeptiert. |
| `ABWEICHUNG` | Mindestens eine anwendbare Regel wurde verletzt; manuelle Prüfung erforderlich. |
| `NICHT_BEWERTET` | Für die erkannten Stufen existiert noch keine statische Regel. Dies ist keine positive Bewertung. |

Eine Abweichung ist ein Prüfhinweis, keine automatische fachliche Fehlerfreigabe.

## Aktive Regeln – Version 2026-08-12.2

### MAT-DRUCK-PLATTE

- Trigger: Stufe `DRUCK` in Planung oder Produktionszeiten.
- Erwartung: Materialgruppe `Druckplatten` in `Fertigungsmaterial.csv`.
- Abweichung: Drucken ist vorhanden, aber keine Druckplatte wurde nachgewiesen.
- Automatische Ausnahme: Wenn gleichzeitig weder `Druckplatten` noch `Farben`
  vorhanden sind, wird die Regel als `AKZEPTIERTE_AUSNAHME` gewertet.

### MAT-DRUCK-FARBE-LACK

- Trigger: Stufe `DRUCK` in Planung oder Produktionszeiten.
- Erwartung: mindestens eine der Materialgruppen `Farben` oder `Lacke`.
- Lack-only-Aufträge erfüllen die Regel durch `Lacke`; Farbe ist nicht zusätzlich
  erforderlich.
- Abweichung: weder Farbe noch Lack wurde nachgewiesen.
- Automatische Ausnahme: Wenn gleichzeitig weder `Druckplatten` noch `Farben`
  vorhanden sind, wird die Regel als `AKZEPTIERTE_AUSNAHME` gewertet. Das gilt
  unabhängig davon, ob Lack vorhanden ist.
- Die Regel prüft zunächst nur das Vorhandensein, nicht die Menge.

### Hinweis zu Papier- und ET-Aufträgen

- Papier als Fertigungsmaterial ist kein eindeutiges Merkmal für einen Etikettenauftrag.
- ET-Aufträge werden bei späteren produktspezifischen Regeln über das Präfix `ET-`
  in `Auftragskopf.X_ArtikelGruppe` erkannt.
- Lack ist bei ET-Aufträgen nicht zwingend. Da die aktive Regel ohnehin Farbe
  **oder** Lack erwartet, ist dafür keine eigene Lack-Ausnahme notwendig.

### MAT-KLEB-AUFRICHT-WELLKARTON-VERBRAUCH

- Trigger: `KLEBEN`, `KLEB`, `AUFRICHTEN` oder `AUFRICHT` in Planung oder
  Produktionszeiten.
- Erwartung: ein Artikel mit Präfix `94` in `Fertigungsmaterial.csv`.
- Das Präfix wird am Anfang der als Text eingelesenen Artikelnummer geprüft.
- Abweichung: kein entsprechender Verbrauch vorhanden.

### MAT-KLEB-AUFRICHT-WELLKARTON-BUCHUNG

- Trigger: wie bei der Verbrauchsregel.
- Erwartung: ein Artikel mit Präfix `94` in `RW_Buchungen.csv`.
- Abweichung: keine entsprechende Rohwarenbuchung vorhanden.
- Verbrauch und Buchung sind absichtlich getrennte Regeln, damit die Ursache der
  Abweichung sichtbar bleibt.

## Bewusste Grenzen der ersten Version

- Materialmengen und -werte werden noch nicht beurteilt.
- Normale Schwankungsbreiten und Toleranzen sind noch nicht definiert.
- `PlanungAktivStatus` wird nicht gefiltert, weil die Bedeutung der beobachteten
  Werte fachlich noch offen ist.
- Planung und tatsächliche Produktionszeiten werden für den Stufentrigger vereinigt;
  ein Auftrag gilt als betroffen, wenn die Stufe in mindestens einer Quelle vorkommt.
- Rückbuchungen, Stornos und Vorzeichen ändern den reinen Vorhandenheitsnachweis
  derzeit nicht. Eine Nettomengenregel benötigt zuerst eine freigegebene
  Vorzeichen- und Mengendefinition.
- Ergebnisse verändern keine Quell- oder Produktivdaten.
- Automatisch akzeptierte Ausnahmen bleiben mit Regel-ID und Begründung im
  Ergebnis sichtbar, erzeugen aber keine Zeile für die manuelle Prüfung.

## Erweiterung und Ausnahmen

Manuell geprüfte Abweichungen werden lokal in der erzeugten
`manual_review_template.csv` dokumentiert. Zulässige Entscheidungen sind zunächst:

- `CONFIRMED_DEVIATION`
- `ACCEPTED_EXCEPTION`
- `DATA_ERROR`
- `RULE_CHANGE_NEEDED`

Feedback ändert Regeln nicht automatisch. Wiederkehrende, fachlich bestätigte
Fälle werden als neuer Regel- oder Ausnahmekandidat dokumentiert, getestet und erst
nach menschlicher Freigabe in `config/rules.json` übernommen. Damit kann das System
schrittweise besser werden, ohne selbstständig fachliche Regeln zu erfinden.

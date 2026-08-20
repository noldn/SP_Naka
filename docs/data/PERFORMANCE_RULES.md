# Performancebewertung und erklärbare Peer-Gruppen

## Fachliches Ziel

Ein Auftrag wird finanziell anhand der im Auftragskopf gespeicherten
Nachkalkulation beurteilt:

```text
Auftragsergebnis = Auftragskopf.Erlöse - Auftragskopf.Kosten
Margenquote       = Auftragsergebnis / abs(Auftragskopf.Erlöse)
```

`Erlöse` und `Kosten` sind die Ergebnisse des bestehenden
Nachkalkulationsprozesses und deshalb die verbindliche Zielgröße. Die aus den
Detailtabellen abgeleiteten Merkmale dienen zur Plausibilisierung und Erklärung.
Eine vollständige unabhängige Kostenrechnung ist noch nicht freigegeben, weil die
Lagerkosten fehlen und mehrere Vorzeichen-/Einheitenregeln noch offen sind.

## Robuste Peer-Gruppen

Das Verfahren trainiert bei jedem Lauf Referenzbereiche aus dem angegebenen
historischen Bestand. Es verwendet Median und MAD (Median Absolute Deviation),
damit einzelne extreme Aufträge den Vergleich weniger stark verzerren.

Die passendste Gruppe mit mindestens fünf Referenzaufträgen wird in dieser
Reihenfolge gewählt:

1. Kunde + Stanzform/Konstruktion + Auflagenklasse,
2. Stanzform/Konstruktion + Auflagenklasse,
3. Produktgruppe + Auflagenklasse,
4. globale Auflagenklasse.

Als Auflagen-Proxy wird derzeit die größte positive Bestellmenge einer
Vertriebsposition verwendet. Die Grenzen stehen in `config/analysis_parameters.json`.

| Robuster z-Wert | Bewertung |
|---|---|
| kleiner/gleich `-3,5` | `SEHR_NEGATIV` |
| kleiner/gleich `-2,0` | `AUFFAELLIG_NEGATIV` |
| zwischen `-2,0` und `2,0` | `IM_REFERENZBEREICH` |
| größer/gleich `2,0` | `AUFFAELLIG_POSITIV` |
| größer/gleich `3,5` | `SEHR_POSITIV` |

Die Grenzwerte sind statistische Startparameter, keine endgültigen fachlichen
Toleranzen. Das Testset und manuelle Bestätigungen müssen sie validieren.

## Auslastungskunden

Ein negativer Auftragsertrag kann für freigegebene Auslastungskunden zulässig
sein. Solche Aufträge werden weiterhin gegen ihre Peer-Gruppe verglichen. Nur die
absolute Negativität wird durch `AUSLASTUNGSKUNDE` erklärt; eine starke relative
Verschlechterung bleibt prüfpflichtig.

Echte Kundenschlüssel werden lokal unter
`data/local/master_data/accepted_negative_customers.csv` gepflegt. Die
Git-fähige Strukturvorlage liegt unter `config/master_data_templates/`. Zulässig
ist der vollständige Exportschlüssel oder die Kundennummer nach dem Trenner `|`.

## Erklärungsevidenz

Bei auffälligen negativen Aufträgen werden folgende Hinweise geprüft:

- auffällig niedriger Erlös je Auflagen-Proxy,
- auffällig hohe Ist-Zeit je Auflagen-Proxy,
- auffällig hoher Materialwert je Auflagen-Proxy,
- erfasster Mehraufwand,
- Druckabstimmung im Arbeitsvorgang,
- Handarbeit in Stufe oder Arbeitsvorgang, aber nur als Negativbegründung, wenn
  zugleich Druckabstimmung oder erfasster Mehraufwand vorhanden ist. Geplante
  Handarbeit allein ist kein negativer Grund.

Diese Merkmale belegen eine Korrelation im Auftrag, aber noch keine Ursache. Die
Ausgabe formuliert sie deshalb als Evidenzhinweise.

## Rohwarenmengen und Restpaletten

Je Auftrag und exakt gleichem Rohwarenartikel wird berechnet:

```text
abs(Summe RW_Buchungen.Menge) / Summe positiver RohwarenPos.Menge
```

Die Zuordnung erfolgt verbindlich in zwei Schritten:

1. zuerst exakt gleicher Artikel zwischen Sollposition und Buchung,
2. danach nur für noch nicht zugeordnete Artikel ein Vergleich innerhalb
   derselben Artikelgruppe.

Damit wird ein Alternativmaterial nicht mit einer fachlich anderen Sollposition
verrechnet. `RohwarenPos.csv` ist für die historische Peer-Referenz optional;
fehlt sie dort, bleiben die Finanz-/Zeitreferenzen nutzbar. Für den zu bewertenden
Testauftrag ist ohne Rohwarenposition keine Mengenprüfung möglich und der Status
bleibt `NICHT_BEWERTET`.

Die erste Parameterfassung verwendet drei Stufen:

| Faktor | Status | Wirkung |
|---|---|---|
| ab `1,10` | `HINWEIS` | sichtbar, noch keine manuelle Pflichtprüfung |
| ab `1,25` | `PRUEFEN` | manueller Prüffall |
| ab `1,50` | `KRITISCH` | dringender Korrekturkandidat |

Dies soll insbesondere bereitgestellte ganze Paletten erkennen, deren Restmenge
nicht zurückgebucht wurde. Wegen noch offener Einheiten- und Vorzeichenregeln
erfolgt niemals eine automatische Korrektur. Die Schwellen werden lokal über die
Weboberfläche parametriert.

## Materialfaktoren je Auftrag

Für jeden Auftrag werden zwei Kostensichten ausgegeben:

1. Papier-/Karton-Materialkosten für Fertigungsmaterialgruppen `Papier` und
   `Karton`.
2. Gesamtmaterialkosten aus allen erkannten Roh- und Fertigungsmaterialartikeln,
   darunter Wellkarton, Fensterfolie, Farben, Lacke und weitere Materialien.

Je Artikel hat `RW_Buchungen.WertMat` Vorrang. Liegt keine RW-Buchung vor, wird
`Fertigungsmaterial.Materialwert` als Fallback verwendet. Damit werden dieselben
Artikel nicht doppelt addiert. Der RW-Nettowert wird wegen der beobachteten
negativen Verbrauchsvorzeichen absolut verwendet.

Ausgegeben werden jeweils:

- Materialkosten in EUR,
- Anteil an `Auftragskopf.Erlöse`,
- Anteil an `Auftragskopf.Kosten`.

Die Faktoren enthalten keine Lagerkosten. Solange Artikelgruppen nicht in allen
Artikeltabellen vorliegen, ist insbesondere der Papier-/Karton-Faktor unvollständig
und als Arbeitskennzahl zu behandeln.

## Wellkarton-Kostenbasis

- Die statische Buchungsregel prüft Wellkarton weiterhin ausschließlich in
  `RW_Buchungen.csv`.
- Für die Kostenplausibilisierung wird ebenfalls die RW-Buchung verwendet.
- Fehlt die RW-Buchung noch vollständig, wird der Wert aus
  `Fertigungsmaterial.csv` als gekennzeichneter Fallback ausgegeben.
- Der Fallback ist keine bestandstechnische Buchungsbestätigung.

## Stanzformen, Konstruktionen und Serien

- `Planung.STANZFORM` ist die bevorzugte Vergleichsidentität.
- Fehlt sie, wird ein eindeutiges `VertriebsPositionen.Muster` mit Präfix `WM`
  als Konstruktion verwendet.
- Rechnungskontrollartikel werden nach dem Firmenschlüssel und dem Trenner `|`
  ausgewertet. Artikel mit anschließendem Präfix `WS` gelten als WS-Evidenz.
- Die erste im bereitgestellten Zeitraum beobachtete Stanzform ist nur ein
  Näherungswert für eine neue Stanzform. Frühere Verwendungen können fehlen.
- Ein Serienkandidat hat dieselbe Stanzform oder Konstruktion und wird 12 bis 24
  Stunden nach dem unmittelbar vorherigen beobachteten Auftrag fertiggestellt.
  Farbüberschneidung wird zusätzlich ausgewiesen.

Die Serienerkennung hat Status `HYPOTHESIS_ONLY` und verändert die Bewertung noch
nicht, weil der Export nur fertige Aufträge der letzten drei Jahre enthält und
dadurch Lücken in der tatsächlichen Produktionsfolge möglich sind.

## Testset und Feedback

Der historische Gesamtbestand wird mit `--reference-data-dir` als Lernreferenz
angegeben. Aufträge des Testsets werden aus der Referenz entfernt, damit sie ihre
eigene Bewertung nicht beeinflussen. Jeder Lauf erzeugt
`expected_results_template.csv`. Diese lokale Datei wird fachlich ausgefüllt und
später als Soll-Ergebnis für Regressionstests verwendet.

Feedback darf neue Regelkandidaten erzeugen. Es darf weder Quelldaten korrigieren
noch Regeln oder Parameter automatisch freigeben.

Die Spalte `reason_review_status` unterscheidet dabei:

- `NO_CONFIRMATION_REQUIRED`: kein Begründungsfeedback notwendig,
- `PROPOSED_REASON_CONFIRMATION_REQUIRED`: vorhandene Evidenz soll bestätigt oder
  geändert werden,
- `REASON_REQUIRED`: auffälliger Auftrag ohne hinreichenden Erklärungshinweis,
- `CORRECTION_CONFIRMATION_REQUIRED`: konkreter Mengen-/Datenkandidat; tatsächliche
  Korrektur muss bestätigt werden.

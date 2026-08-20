# Analyse- und Bewertungsprozess

## Zielbild

SP_Naka soll Aufträge reproduzierbar prüfen, Abweichungen begründen und Fälle für
eine manuelle Kontrolle bereitstellen. Die Entwicklung erfolgt in klar getrennten
Phasen.

## Phase 1 – statische Materialregeln (implementiert)

1. Pflichtdateien und Pflichtfelder validieren.
2. Aufträge über die dokumentierten Schlüssel verbinden.
3. relevante Produktionsstufen aus Planung und Ist-Zeiten bestimmen.
4. statische Materialregeln anwenden.
5. je Regel einen nachvollziehbaren Status und Grund erzeugen.
6. je Auftrag eine Gesamtbeurteilung erzeugen.
7. Abweichungen in eine lokale Vorlage zur manuellen Prüfung schreiben.
8. Kontrollsummen, Dateiprüfsummen, Regel- und Programmversion protokollieren.

Automatisch freigegebene Ausnahmen werden als `AKZEPTIERTE_AUSNAHME` je Regel
und als `REGELKONFORM_MIT_AUSNAHME` je Auftrag ausgegeben. Sie bleiben damit
sichtbar, führen aber nicht zu einer manuellen Prüfanforderung.

## Phase 2 – quantitative Regeln und Toleranzen (erste Version implementiert)

Erst nach fachlicher Definition werden Mengen, Zeiten, Kosten und Leistungen
bewertet. Für jede Kennzahl müssen Einheit, Bezugsgröße, Vorzeichen, Rundung und
zulässige Schwankungsbreite festgelegt werden. Abweichungen innerhalb einer
freigegebenen Toleranz dürfen nicht negativ bewertet werden.

Mögliche Reihenfolge:

1. Vergleich nur innerhalb fachlich homogener Produkt-/Prozessgruppen.
2. robuste Referenzbereiche statt starrer Einzelwerte.
3. getrennte Grenzen für Warnung und prüfpflichtige Abweichung.
4. historische Referenzaufträge und Summenabstimmung.

Die erste Version verwendet robuste Peer-Gruppen für Margenquote, Erlös-, Zeit-
und Materialkennzahlen. Die Bewertung und ihre bewussten Grenzen sind unter
`docs/data/PERFORMANCE_RULES.md` dokumentiert.

## Phase 3 – Clustering und Interpretation (geplant)

Clustering dient der Erkennung ähnlicher Auftrags- und Abweichungsmuster. Es darf
statische Regeln nicht unbemerkt ersetzen. Vor Einsatz sind mindestens festzulegen:

- verwendete Merkmale und Einheiten,
- Behandlung fehlender Werte und Ausreißer,
- fachlich sinnvolle Segmentierung,
- Stabilität der Cluster über mehrere Datenstände,
- nachvollziehbare Erklärung, warum ein Auftrag einem Muster zugeordnet wurde,
- menschliche Freigabe für daraus abgeleitete Regelvorschläge.

## Phase 4 – Weboberfläche und kontrolliertes Feedback (lokale erste Version)

Die aktuelle Programmlogik ist von der Kommandozeile getrennt, sodass später eine
Weboberfläche denselben Analyseprozess starten und Ergebnisse anzeigen kann. Eine
Webanwendung benötigt zusätzlich Authentifizierung, Berechtigungen, Protokollierung,
Schutz der lokalen Daten und ein freigegebenes Betriebsmodell.

Feedback aus manuellen Prüfungen wird zunächst als lokales Prüfprotokoll geführt.
Automatische Änderungen an produktiven Regeln oder Quelldaten sind nicht zulässig.

Auftragsbezogene Bewertungen und fachliche Klärungen werden unabhängig vom
gewählten Datenbestand lokal protokolliert. Sie dienen als kuratierte Soll- und
Validierungsinformation. Erst nach fachlicher Freigabe dürfen daraus geänderte
Regeln oder ein aktualisierter Referenzbestand entstehen.

Die lokale Browseroberfläche stellt Parametrierung, Standard- und Anlernprozess,
Aufgabenplanung, Laufhistorie, Auftragsdetails und kontrolliertes Feedback bereit.
Die Bedienung ist in `docs/WEB_APP.md` beschrieben.

## Ergebnisse eines Laufs

Jeder Lauf erhält ein eigenes Verzeichnis unter `output/runs/`:

| Datei | Inhalt |
|---|---|
| `order_assessments.csv` | eine Gesamtbeurteilung je Auftrag |
| `rule_results.csv` | jede anwendbare Regel mit Status, Grund und Evidenzanzahl |
| `manual_review_template.csv` | nur Abweichungen plus leere Felder für fachliches Feedback |
| `data_quality_issues.csv` | kontrolliert markierte unvollständige Werte ohne Geschäftsinhalt |
| `run_manifest.json` | Eingabeprüfsummen, Zeilenzahlen, Versionen, Zeiten und Kontrollsummen |
| `performance_assessments.csv` | absolute und relative Performance samt Evidenzhinweisen |
| `performance_review_template.csv` | auffällige Performance- und Mengenfälle für manuelle Prüfung |
| `expected_results_template.csv` | lokale Soll-Ergebnisvorlage für das Testset |

Die Originaldateien werden nur gelesen. Bei einem kritischen Validierungsfehler wird
kein vollständiger Ergebnislauf veröffentlicht.

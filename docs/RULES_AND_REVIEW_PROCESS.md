# Regeln und fachlicher Prüfprozess

## Kurzfassung

1. Jeder neue Datenlauf bewertet alle gelieferten Aufträge neu. Die Quelldaten werden nicht verändert.
2. Ohne Auffälligkeit ist keine Bestätigung erforderlich.
3. Starke oder unklare negative Abweichungen müssen fachlich geprüft und begründet werden.
4. Rohwarenmengen der Stufen `PRUEFEN` und `KRITISCH` sowie unmögliche Leistungswerte erscheinen zusätzlich unter **Korrekturen**.
5. Eine Korrektur wird als **Auffälligkeit akzeptiert** oder **Wird korrigiert** entschieden. Nach dem nächsten Datenexport wird der Auftrag automatisch neu bewertet.
6. Auftragsarten `M` und `B` sind Konstruktions-/Datenbearbeitungsaufträge und grundsätzlich in Ordnung. Nur ein außerhalb der robusten Bandbreite liegender Zeit-, Material- oder Einzelkostenaufwand wird vorgelegt.
7. Nachproduktionen dürfen negativ sein. Unabhängige Auffälligkeiten bei Material, Leistung oder Buchungen bleiben prüfpflichtig.
8. Wellkarton wird über die Artikelgruppe `09` erkannt, nicht über einen Artikelnummern-Präfix.
9. Eine fachliche Rückmeldung wird lokal gespeichert und verändert weder Rohdaten noch Regeln automatisch.
10. Eine massive Abweichung zwischen **Kosten Ist (Auftragskopf)** und **Kosten errechnet** ist ein Korrekturkandidat. Zu klären ist, ob die Istkosten noch nicht vollständig/aktuell oder die errechneten Detaildaten fehlerhaft sind.
11. Bei abgeschlossenen Aufträgen (`offen = 0`) werden Unterlieferungen und die Fakturasumme geprüft. Mehrlieferungen sind zulässig; Positionen unter 90 % benötigen eine Gutschrift oder fachliche Klärung.
12. Eine erstmals im gelieferten Datenzeitraum beobachtete Stanzform bleibt als Näherungswert sichtbar. Sie wird in der Auftragsliste zusätzlich in einer eigenen Spalte angezeigt.

## Was muss geprüft oder bestätigt werden?

| Anzeige | Bedeutung | Erforderliche Entscheidung |
|---|---|---|
| Keine Prüfung | Auftrag liegt im erwarteten Bereich | keine |
| Begründung erforderlich | stark/unklar auffällig, Ursache nicht eindeutig | Ursache dokumentieren und abschließen |
| Vorgeschlagene Begründung bestätigen | System hat Preis-, Zeit-, Material- oder Mehraufwand erkannt | Ursache bestätigen oder fachlich ändern |
| Korrektur bestätigen | Rohwarenmenge oder Leistungswert liegt außerhalb der akzeptierten Bandbreite | Auffälligkeit akzeptieren oder „Wird korrigiert“ wählen |
| Kostenabstimmung prüfen | rekonstruierte Kosten weichen erheblich vom Auftragskopf ab | fehlende Kosten/Buchungen klären und begründen |
| Lieferung/Faktura prüfen | geschlossener Auftrag hat eine Unterlieferung ohne Gutschrift oder eine abweichende Fakturasumme | Lieferung, Gutschrift, Nachbesserung, Sonderkosten oder Datenfehler klären |

Die Menüseite **Aufträge & Prüfung** führt Auftragsbewertung, Prüfung/Feedback und Korrekturen zusammen. Die Filter **Alle Aufträge**, **Prüfung erforderlich** und **Korrekturen** bestimmen, welche Fälle angezeigt werden. Ein Klick auf die Auftragsnummer öffnet unmittelbar die Nachkalkulation. Dort werden Systembewertung, Prüfauftrag, fachliche Bewertung, Korrekturentscheidung und Abschlussstatus zusammengeführt.

## Ablauf je Datenzyklus

1. CSV-Dateien im vorgesehenen Datenbestand ersetzen.
2. Standard- oder Testprozess starten.
3. Unter **Aufträge & Prüfung** den Filter **Korrekturen** zuerst bearbeiten; diese Fälle enthalten konkrete Daten- oder Leistungsauffälligkeiten.
4. Danach den Filter **Prüfung erforderlich** bearbeiten und fachliche Ursachen bestätigen.
5. Mit Status `ABGESCHLOSSEN` wird die Entscheidung für diesen Auftrag dokumentiert.
6. Bei **Wird korrigiert** erfolgt die eigentliche Korrektur im führenden System. Der nächste Export und Lauf bewertet die neuen Daten neu.
7. Wiederkehrende fachlich bestätigte Fälle können als Testvorgabe gepflegt werden. Eine einzelne Rückmeldung ändert die Analyse nicht automatisch.

## Test- und Lerndaten

Unter **Testvorgaben** wird der Auftrag aus dem vorhandenen Testdatenbestand ausgewählt; eine freie Eingabe der Auftragsnummer ist nicht möglich. Aktuelle Systembewertung, Reason Codes und Erklärung werden angezeigt und bei einem neuen Testfall als Vorschlag für die erwarteten Werte übernommen. Status und Reason Codes werden aus festen Listen gewählt; mehrere Reason Codes können im Auswahlfeld angehakt werden. Bestehende Vorgaben können gelöscht werden. Frühere Fehleinträge, deren Auftrag nicht im Testdatenbestand vorkommt, sind entsprechend markiert und können nur noch gelöscht werden. Diese Vorgaben dienen als Regressionstest und als nachvollziehbares Fachwissen. Neue Stichproben sollten zunächst im Testdatenbestand bleiben; bestätigte, repräsentative Fälle können später kontrolliert in den historischen Referenzbestand übernommen werden.

## Regeln im Detail

### Statische Materialregeln

- Drucken: Druckplatte sowie Farbe/MIX/Lack werden gemäß Regelkonfiguration geprüft.
- Fenstern: Fensterfolie muss gebucht sein.
- Kleben/Aufrichten: Eine Rohwarenbuchung der Artikelgruppe `09` muss vorhanden sein.

Die technische Konfiguration steht in `config/rules.json`; die fachliche Erläuterung in `docs/data/STATIC_RULES.md`.

### Performance und robuste Bandbreite

Die Anwendung vergleicht passende Peer-Gruppen nach Produkt/Konstruktion und Mengenband. Median und Median Absolute Deviation begrenzen den Einfluss einzelner Ausreißer. Die Schwellenwerte stehen unter **Parametrierung**. Eine Abweichung ist ein Prüfhinweis, keine automatische Fehlerbehauptung.

Für M/B wird das negative Ergebnis bzw. eine reine Margenabweichung als erwartbare Ausnahme behandelt. Prüfpflicht entsteht nur durch hohe Zeit, hohen Materialeinsatz, hohe Einzelkosten oder konkrete Rohwarenauffälligkeiten.

### Korrekturen

Korrekturkandidaten sind insbesondere:

- Rohwarenmenge `PRUEFEN` oder `KRITISCH`,
- auffällige Zeit/Leistung,
- auffälliger Material- oder Einzelkostenaufwand,
- kritische Abweichung der Istkosten zu den errechneten Kosten.

**Auffälligkeit akzeptiert** hält fest, dass der Wert fachlich korrekt ist. **Wird korrigiert** hält fest, dass die Korrektur im führenden System erfolgt. Die Anwendung überschreibt keine Quelldaten.

### Kosten und Sollkosten

Die Istkostenabstimmung rekonstruiert Produktions- und Einzelkosten, ergänzt VV- und Materialzuschläge und vergleicht sie mit dem Auftragskopf. Die theoretischen Sollkosten verwenden ideale Produktionsleistungen und Sollmaterialmengen. Werkzeuge (`WS`, `WKS`) und Eingangsrechnungen fließen nicht in die theoretischen Einzelkosten ein.

Eine Kostenabweichung ist **kritisch**, wenn sowohl der konfigurierte absolute als auch der relative Grenzwert überschritten wird. Der Fall erscheint dann als Korrekturkandidat. Die Kennzeichnung entscheidet nicht automatisch, welche Seite falsch ist: Ursache können ein verspäteter oder unvollständiger Kostenstand im Auftragskopf ebenso wie fehlende, doppelte oder falsche Detailbuchungen sein.

### Lieferung und Faktura

Die Prüfung gilt nur für abgeschlossene Aufträge mit `Auftragskopf.offen = 0`:

- Positionen ohne positiven Preis oder ohne gültigen Preiseinheitsfaktor werden nicht bewertet.
- Vorfertigungsteile (Artikelgruppe `13` beziehungsweise Bezeichnung „Vorfertigungsteile“) und direkte Wertpositionen werden nicht auf Liefermenge geprüft.
- Normale bepreiste Positionen unter 90 % der Bestellmenge werden ohne Gutschrift zur Prüfung vorgelegt. Genau 90 % ist zulässig. Mehrlieferungen werden nicht beanstandet, auch wenn sie deutlich über 110 % liegen.
- Bei einer Gutschrift darf die Liefermenge niedriger sein. Aussortieren oder Nachbesserung kann außerdem zu mehrfach gemeldeten Liefermengen führen; diese werden nicht automatisch als Fehler bewertet.
- Der theoretische Fakturawert normaler Artikel wird aus `gelieferte_Menge × EinzelpreismZuAbschl ÷ Preiseinheitsfaktor` berechnet. Falls der Abschlusspreis fehlt, wird `Einzelpreis` verwendet.
- Direkte Wert- und Sonderkostenpositionen werden aus `Menge × Preis ÷ Preiseinheitsfaktor` berechnet, weil sie nicht zwingend über eine Liefermenge fakturiert werden.
- Die Bruttorechnung aus `Faktura.Summe_Rechnung_EUR` wird mit dem theoretischen Fakturawert verglichen. Abweichungen bis einschließlich 1,00 EUR gelten als Rundungstoleranz.
- Gutschrift und Nettoerlös werden getrennt angezeigt. Eine Gutschrift erklärt eine Abweichung, hebt eine weiterhin bestehende Brutto-Summenabweichung aber nicht automatisch auf.
- Bei vorhandenen Sonderkosten und einer Fakturaabweichung wird ausdrücklich geprüft, ob die Sonderkosten verrechnet wurden.

`Faktura.csv` enthält nur Summen je Auftrag. Die Anwendung kann deshalb eine Summenabweichung erkennen, aber nicht sicher bestimmen, welche einzelne Position fehlt. Dafür wären Fakturapositionen mit Auftrags- und Positionsbezug notwendig.

### Stanzform neu

`Planung.STANZFORM` wird weiterhin ausgewertet. „Stanzform neu“ bedeutet, dass die Stanzform im bereitgestellten historischen Zeitraum erstmals am Datum des Auftrags beobachtet wird. Das ist wegen des begrenzten Datenzeitraums ein Hinweis und kein Beweis für eine tatsächlich neu beschaffte Stanzform. Ein vorhandener WS-Artikel aus den Rechnungskontrollen wird separat berücksichtigt.

## Grenzen

- Die Anwendung lernt nicht ungeprüft aus einzelnen Entscheidungen.
- Fachliche Bestätigungen bleiben lokale, nachvollziehbare Daten.
- Schwellenwert- oder Regeländerungen erfolgen bewusst und versioniert.
- Fehlende oder verspätete Kosten können nur gekennzeichnet, nicht erfunden werden.

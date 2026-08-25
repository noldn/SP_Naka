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

## Was muss geprüft oder bestätigt werden?

| Anzeige | Bedeutung | Erforderliche Entscheidung |
|---|---|---|
| Keine Prüfung | Auftrag liegt im erwarteten Bereich | keine |
| Begründung erforderlich | stark/unklar auffällig, Ursache nicht eindeutig | Ursache dokumentieren und abschließen |
| Vorgeschlagene Begründung bestätigen | System hat Preis-, Zeit-, Material- oder Mehraufwand erkannt | Ursache bestätigen oder fachlich ändern |
| Korrektur bestätigen | Rohwarenmenge oder Leistungswert liegt außerhalb der akzeptierten Bandbreite | Auffälligkeit akzeptieren oder „Wird korrigiert“ wählen |
| Kostenabstimmung prüfen | rekonstruierte Kosten weichen erheblich vom Auftragskopf ab | fehlende Kosten/Buchungen klären und begründen |

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

Unter **Testvorgaben** werden erwarteter Status, erwartete Reason Codes, akzeptierte Ausnahme, Korrekturhinweis und fachliche Erklärung je Testauftrag gepflegt. Status und Reason Codes werden aus festen Listen gewählt; mehrere Reason Codes können im Auswahlfeld angehakt werden. Diese Vorgaben dienen als Regressionstest und als nachvollziehbares Fachwissen. Neue Stichproben sollten zunächst im Testdatenbestand bleiben; bestätigte, repräsentative Fälle können später kontrolliert in den historischen Referenzbestand übernommen werden.

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
- auffälliger Material- oder Einzelkostenaufwand.

**Auffälligkeit akzeptiert** hält fest, dass der Wert fachlich korrekt ist. **Wird korrigiert** hält fest, dass die Korrektur im führenden System erfolgt. Die Anwendung überschreibt keine Quelldaten.

### Kosten und Sollkosten

Die Istkostenabstimmung rekonstruiert Produktions- und Einzelkosten, ergänzt VV- und Materialzuschläge und vergleicht sie mit dem Auftragskopf. Die theoretischen Sollkosten verwenden ideale Produktionsleistungen und Sollmaterialmengen. Werkzeuge (`WS`, `WKS`) und Eingangsrechnungen fließen nicht in die theoretischen Einzelkosten ein.

## Grenzen

- Die Anwendung lernt nicht ungeprüft aus einzelnen Entscheidungen.
- Fachliche Bestätigungen bleiben lokale, nachvollziehbare Daten.
- Schwellenwert- oder Regeländerungen erfolgen bewusst und versioniert.
- Fehlende oder verspätete Kosten können nur gekennzeichnet, nicht erfunden werden.

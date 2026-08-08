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


# Entwicklungs- und Sicherheitsrichtlinie NAKA

## 1. Grundprinzipien

Dieses Projekt verarbeitet interne Kalkulations-, Produktions- und Auftragsdaten.

Der Quellcode muss nachvollziehbar, reproduzierbar, testbar und revisionsfähig sein.

KI-generierter Code gilt grundsätzlich als ungeprüfter Änderungsvorschlag. Er darf nicht ohne Tests und fachliche Prüfung produktiv eingesetzt werden.

## 2. Schutz der Quelldaten

* Quelldaten werden ausschließlich lesend verarbeitet.
* Originaldateien dürfen niemals verändert, umbenannt oder gelöscht werden.
* Ausgaben werden ausschließlich in getrennte Ausgabe- oder Staging-Verzeichnisse geschrieben.
* Produktive Proalpha-, Qlik- oder Datenbanktabellen dürfen nicht direkt verändert werden.
* Schreibende Schnittstellen müssen ausdrücklich freigegeben und technisch getrennt implementiert werden.
* Jeder produktive Lauf muss anhand der Eingabedateien, Konfiguration und Programmversion reproduzierbar sein.

## 3. Datenschutz und Vertraulichkeit

* Reale Unternehmensdaten dürfen nicht an nicht freigegebene externe KI-, Cloud- oder Analysedienste übertragen werden.
* Zugangsdaten, API-Schlüssel, Passwörter und Verbindungszeichenfolgen dürfen niemals im Quellcode gespeichert werden.
* Geheimnisse werden ausschließlich über Umgebungsvariablen oder einen freigegebenen Secret Store geladen.
* Protokolle dürfen keine unnötigen personenbezogenen Daten oder Geschäftsgeheimnisse enthalten.
* Testdaten sind nach Möglichkeit synthetisch oder anonymisiert.

## 4. Versionsverwaltung

* Sämtlicher Quellcode und sämtliche Konfigurationsdateien werden mit Git versioniert.
* Der produktive Hauptbranch darf nicht direkt bearbeitet werden.
* Änderungen erfolgen in separaten Feature- oder Bugfix-Branches.
* Jede Änderung muss über einen nachvollziehbaren Commit verfügen.
* Produktive Versionen werden mit einer Versionsnummer oder einem Git-Tag gekennzeichnet.
* Force Pushes und das Löschen des Hauptbranches sind nicht zulässig.
* Änderungen an fachlichen Berechnungsregeln müssen gesondert dokumentiert werden.

## 5. Anforderungen an Änderungen

Vor jeder Änderung müssen folgende Punkte definiert werden:

* fachliches Ziel,
* betroffene Eingabedaten,
* erwartetes Ergebnis,
* Sonderfälle,
* Fehlerverhalten,
* Abnahmekriterien.

Die KI darf keine fachlichen Regeln erfinden. Unklare Anforderungen müssen als offene Punkte gekennzeichnet werden.

Bestehende Berechnungslogik darf nicht verändert werden, wenn dies nicht ausdrücklich Bestandteil der Aufgabe ist.

## 6. Codequalität

* Funktionen sollen klein und eindeutig abgegrenzt sein.
* Fachlogik, Datenzugriff, Validierung und Ausgabe werden getrennt implementiert.
* Feldnamen, Einheiten und Vorzeichenlogik müssen eindeutig dokumentiert sein.
* Geldbeträge, Mengen, Zeiten und Gewichte müssen mit definierten Datentypen und Rundungsregeln verarbeitet werden.
* Fehler dürfen nicht stillschweigend ignoriert werden.
* Unsichere Standardwerte oder automatische Fallbacks sind nicht zulässig.
* Bei fehlenden Pflichtfeldern muss der Datensatz entweder kontrolliert abgewiesen oder eindeutig als fehlerhaft markiert werden.
* Keine dynamische Ausführung von Eingabewerten über `eval`, `exec`, Shell-Kommandos oder vergleichbare Mechanismen.
* SQL-Abfragen müssen parametrisiert sein.
* Dateipfade und Dateinamen müssen validiert werden.

## 7. Tests

Jede fachliche Regel benötigt mindestens:

* einen regulären Testfall,
* einen Grenzfall,
* einen fehlerhaften oder unvollständigen Testfall.

Zusätzlich müssen Regressionstests für bereits bestätigte Ergebnisse bestehen.

Vor einer produktiven Freigabe müssen mindestens folgende Prüfungen erfolgreich sein:

* Unit-Tests,
* Integrationstest mit definierten Testdaten,
* Vergleich mit bekannten historischen Aufträgen,
* Summen- und Mengenabstimmung,
* Prüfung auf fehlende oder doppelte Datensätze,
* Prüfung auf unerwartete Abweichungen,
* statische Codeprüfung,
* Prüfung verwendeter Abhängigkeiten.

Tests dürfen nicht entfernt, abgeschwächt oder übersprungen werden, nur damit eine Änderung erfolgreich durchläuft.

## 8. Plausibilitäts- und Kontrollsummen

Jeder Programmlauf muss mindestens dokumentieren:

* Anzahl eingelesener Datensätze,
* Anzahl verarbeiteter Aufträge,
* Anzahl ausgeschlossener Datensätze,
* Anzahl fehlerhafter Datensätze,
* Anzahl erzeugter Ergebnisse,
* Summen der wesentlichen Mengen- und Wertfelder,
* verwendete Programmversion,
* Start- und Endzeit,
* verwendete Konfiguration.

Abweichungen gegenüber dem vorherigen Lauf müssen erkennbar sein.

## 9. Fehlerbehandlung

* Fehler müssen mit verständlicher Ursache protokolliert werden.
* Bei kritischen Fehlern darf kein Ergebnis als vollständig freigegeben werden.
* Teilverarbeitungen müssen eindeutig als unvollständig gekennzeichnet sein.
* Ein Fehler in einem Auftrag darf nicht unbemerkt Ergebnisse anderer Aufträge verändern.
* Wiederholte Programmläufe mit identischen Eingaben müssen identische Ergebnisse liefern.
* Temporäre Dateien müssen kontrolliert behandelt und nach Fehlern aufgeräumt werden.

## 10. Produktive Freigabe

Eine Version darf nur produktiv eingesetzt werden, wenn:

* alle automatisierten Tests erfolgreich sind,
* die Ergebnisse mit Referenzfällen verglichen wurden,
* die fachliche Änderung dokumentiert wurde,
* ein Rollback auf die vorherige Version möglich ist,
* die freigegebene Git-Version eindeutig feststeht.

Die KI darf keine Version selbstständig produktiv setzen oder freigeben.

## 11. KI-spezifische Anweisungen

Bei jeder Änderung muss die KI:

1. zuerst die bestehende Struktur und die betroffenen Dateien analysieren,
2. Annahmen ausdrücklich nennen,
3. nur die für die Aufgabe notwendigen Dateien ändern,
4. keine bestehenden Schnittstellen ohne Begründung verändern,
5. passende Tests erstellen oder anpassen,
6. bestehende Tests ausführen,
7. das Testergebnis vollständig angeben,
8. auf nicht getestete Bereiche hinweisen,
9. Sicherheits- und Datenrisiken der Änderung nennen,
10. einen verständlichen Änderungsüberblick liefern.

Die KI darf nicht:

* Testergebnisse erfinden,
* behaupten, Code ausgeführt zu haben, wenn dies nicht erfolgt ist,
* unbekannte Datenstrukturen vermuten und als Tatsache behandeln,
* Sicherheitsprüfungen deaktivieren,
* Zugangsdaten in Dateien schreiben,
* produktive Daten verändern,
* bestehende Fehler durch pauschales Abfangen von Ausnahmen verdecken,
* fachliche Regeln ohne ausdrückliche Anforderung ändern.

## 12. Sicherheitsgrundlage

Der Entwicklungsprozess orientiert sich am NIST Secure Software Development Framework.

Technische Sicherheitsanforderungen werden, soweit für die Anwendung relevant, aus dem OWASP Application Security Verification Standard abgeleitet.

Vor der produktiven Einführung wird ein dokumentiertes Threat Model erstellt. Dieses enthält mindestens:

* schützenswerte Daten und Funktionen,
* Benutzer und Berechtigungen,
* Datenquellen und Datenziele,
* Vertrauensgrenzen,
* mögliche Manipulationen,
* Fehler- und Ausfallszenarien,
* notwendige Gegenmaßnahmen.


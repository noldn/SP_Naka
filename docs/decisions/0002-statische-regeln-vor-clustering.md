# ADR 0002: Statische Regeln vor statistischer Analyse und Clustering

- **Status:** Angenommen
- **Datum:** 2026-08-12

## Kontext

Material- und Leistungsabweichungen können durch normale Produktionsschwankungen
entstehen. Gleichzeitig bestehen fachlich klare Abhängigkeiten zwischen bestimmten
Produktionsstufen und erwarteten Materialien. Ein datengetriebenes Verfahren könnte
ohne diese Trennung normale Streuung als Fehler oder Datenfehler als Muster lernen.

## Entscheidung

Die Analyse wird schrittweise aufgebaut:

1. deterministische, versionierte und erklärbare Regeln,
2. fachlich definierte quantitative Toleranzen,
3. Clustering und Musterinterpretation,
4. kontrollierte Übernahme menschlich bestätigter Erkenntnisse.

Regelergebnisse werden getrennt von Quelldaten gespeichert. Manuelles Feedback darf
Regeln nicht automatisch verändern, sondern erzeugt prüfbare Änderungskandidaten.

## Konsequenzen

- Erste Ergebnisse sind einfach erklärbar und reproduzierbar.
- Normale Mengenschwankungen werden in Phase 1 nicht bewertet.
- Zusätzliche Regeln und Ausnahmen benötigen Konfiguration, Tests und Freigabe.
- Eine spätere Weboberfläche kann dieselbe Analysefunktion verwenden.

# Änderungsprotokoll

Wesentliche Änderungen werden hier in umgekehrt chronologischer Reihenfolge erfasst.

## Noch nicht veröffentlicht

### Korrigiert

- Ergebnisordner bleiben unter macOS im Finder sichtbar. Temporäre Laufordner
  werden nicht mehr als Punkt-Ordner angelegt, und unsichtbare Laufkennungen
  werden abgewiesen.

### Hinzugefügt

- Grundstruktur für Code, Tests, Konfiguration und lokale Daten.
- Entwicklungsleitplanken in `AGENTS.md`.
- Projektziel und Erfolgskriterien in `PROJECT_GOAL.md`.
- Strukturierte Dokumentation für Entscheidungen, Notizen, Daten und Intranet-Inhalte.
- Ausfüllbare Mehrtabellen-Vorlage im Datenkatalog mit Feldern, Beziehungen,
  Qualitätsprüfungen und Regeln für optionale Rohwarenzuordnungen.
- Lokale Vollprofilierung von neun CSV-Datenquellen in den Datenkatalog übernommen;
  Schlüsselabdeckung, CSV-Brauchbarkeit und fachlich offene Definitionen dokumentiert.
- Datenkatalog gegen den Export vom 2026-08-12 neu geprüft: entfernte
  Mengenmeldungsdatei und entfallene Spalten dokumentiert, Produktionsplanung und
  Faktura ergänzt sowie Schlüssel, Beziehungen, Zeiträume und Qualitätskennzahlen
  aktualisiert.
- Erste ausführbare Auftragsprüfung ergänzt: sichere CSV-Validierung, versionierte
  Materialregeln für Drucken sowie Kleben/Aufrichten, begründete Auftrags- und
  Regelresultate, manuelle Feedbackvorlage und reproduzierbares Laufprotokoll.
- Mehrstufigen Ausbau von statischen Regeln über quantitative Toleranzen bis zu
  Clustering und Weboberfläche dokumentiert.
- Druckregeln auf Version 2026-08-12.2 präzisiert: Lack bleibt optional;
  Druckaufträge ohne Druckplatte und ohne Farbe werden nachvollziehbar als
  automatische Ausnahme akzeptiert und nicht zur manuellen Prüfung gestellt.
- Regelwerk auf Version 2026-08-14.1 erweitert: MIX-Artikel gelten als
  Farbnachweis; Wellkarton wird bei Kleben/Aufrichten ausschließlich anhand der
  übertragenen Rohwarenbuchungen geprüft, nicht anhand der vorgelagerten
  BDE-Erfassung im Fertigungsmaterial.
- Performanceanalyse Version 0.4.0 ergänzt: Zielgröße `Erlöse - Kosten`,
  robuste hierarchische Peer-Gruppen, auflagenabhängige Referenzen, erklärbare
  Evidenz für Preis, Zeit, Material, Mehraufwand, Druckabstimmung und Handarbeit.
- Lokale Stammdatenstruktur für Auslastungskunden und Fehlerkategorien sowie eine
  automatisch erzeugte Soll-Ergebnisvorlage für Testaufträge hinzugefügt.
- Rohwaren-Mengenkandidat für nicht korrigierte Restpaletten und gekennzeichneten
  Wellkarton-Kostenfallback aus Fertigungsmaterial eingeführt.
- Regelwerk 2026-08-14.2: Stufe `FENSTER` erfordert Materialgruppe
  `Fensterfolien`; geplante Handarbeit allein ist keine Negativbegründung.
- Rohwarenfaktor in die Stufen Hinweis ab 1,10, Prüfen ab 1,25 und Kritisch ab
  1,50 aufgeteilt sowie Papier-/Karton- und Gesamtmaterialfaktoren je Auftrag
  ergänzt.
- Lokale Browseroberfläche Version 0.5.0 mit proALPHA-orientierter Navigation,
  Parametrierung, Standard-/Anlernprozess, täglicher Planung, Laufhistorie,
  Auftragsdetails und kontrolliertem Feedback hinzugefügt.
- Docker-Umgebung, lokale Startbefehle und Installationsskripte für macOS und
  Windows ergänzt; Threat Model dokumentiert.
- Generator für ein von Git ausgeschlossenes Transferpaket mit TODO,
  Stammdatenlisten und drei vorbereiteten Testfällen hinzugefügt.

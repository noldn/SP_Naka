# Projektstart und Dokumentationskonzept

- **Datum:** 2026-08-07
- **Autor/in:** Projektteam SP_Naka
- **Status:** geprüft
- **Thema:** Leitplanken und systemübergreifende Dokumentation

## Fragestellung

Wie können Entwicklung, lokale Datenanalyse und portable Projektdokumentation
sicher miteinander verbunden werden?

## Erkenntnisse

- Markdown eignet sich als lesbares, Git-fähiges und Intranet-taugliches Textformat.
- Code und freigegebene Dokumentation können über GitHub synchronisiert werden.
- Echte Daten und vertrauliche Informationen müssen getrennt bleiben.
- `AGENTS.md` kann Entwicklungsregeln für Menschen und KI-Agenten festhalten.

## Entscheidungen

- Projektziel und Leitplanken werden im Repository versioniert.
- Fachliche und technische Entscheidungen werden getrennt von laufenden Notizen geführt.
- Lokale Daten bleiben unter `data/local/` oder in einem externen lokalen Speicher.
- Das Repository `noldn/SP_Naka` ist privat; die Datenleitplanken gelten trotzdem.

## Offene Punkte

- [ ] Konkrete Analysefälle und Datenformate beschreiben.
- [ ] Programmiersprache und technische Architektur auswählen.
- [ ] Regeln für die spätere Intranet-Freigabe abstimmen.

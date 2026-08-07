# ADR 0001: Git für Code und nicht vertrauliche Dokumentation

- **Status:** angenommen
- **Datum:** 2026-08-07
- **Verantwortlich:** Projektverantwortliche/r SP_Naka

## Kontext

Code, Projektnotizen und Entscheidungen sollen auf verschiedenen Systemen und an
verschiedenen Orten verfügbar sowie später in ein Intranet übertragbar sein. Die
Anwendung muss gleichzeitig lokale Daten verarbeiten können.

## Entscheidung

Programmcode und freigegebene Markdown-Dokumentation werden in Git versioniert.
Echte lokale Daten, Geheimnisse, generierte Ergebnisse und vertrauliche Notizen
werden durch technische und organisatorische Regeln ausgeschlossen.

## Begründung

Git macht Änderungen nachvollziehbar, ermöglicht systemübergreifenden Zugriff und
verwendet portable Textformate. Die Trennung schützt lokale Daten vor einer
versehentlichen Veröffentlichung.

## Folgen

- Markdown-Dateien können direkt gelesen, verglichen und ins Intranet übertragen werden.
- Mitarbeitende müssen Inhalte vor jedem Commit auf Vertraulichkeit prüfen.
- Für vertrauliche Dokumentation ist ein gesonderter, freigegebener Speicher notwendig.

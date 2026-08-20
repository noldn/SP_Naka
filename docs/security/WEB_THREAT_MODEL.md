# Threat Model der lokalen Weboberfläche

## Schützenswerte Werte

- interne Auftrags-, Kosten-, Kunden- und Produktionsdaten,
- lokale Pfade und Stammdaten,
- Analyseparameter, Feedback und Ergebnisdateien,
- Integrität der unveränderten Quelldateien.

## Benutzer und Berechtigungen

Die erste Version ist eine Einzelplatzanwendung für einen fachlich berechtigten
lokalen Benutzer. Sie enthält noch keine Benutzerverwaltung oder Anmeldung und
darf deshalb nicht im Firmen-LAN oder Internet freigegeben werden.

## Datenquellen und -ziele

- Quellen: konfigurierbare lokale CSV-Verzeichnisse, ausschließlich lesend.
- Ziele: lokales `output/` sowie Konfiguration, Stammdaten und Feedback unter
  `data/local/`.
- Keine Cloud-, KI- oder produktive proALPHA-Schnittstelle.

## Vertrauensgrenzen

1. Browser zum lokalen HTTP-Server.
2. Webserver zu lokalen Daten- und Ergebnisverzeichnissen.
3. Docker-Container zu den explizit eingebundenen Host-Verzeichnissen.
4. Git-Repository zu den bewusst ausgeschlossenen vertraulichen lokalen Daten.

## Risiken und Gegenmaßnahmen

| Risiko | Gegenmaßnahme |
|---|---|
| Zugriff durch andere Rechner | Portbindung ausschließlich an `127.0.0.1` |
| Manipulierte Formulare | POST, CSRF-Token, Größenlimit und Eingabevalidierung |
| Pfadmanipulation bei Laufauswahl | Lauf-IDs und aufgelöster Zielpfad werden validiert |
| Formelinjektion in CSV | bestehende sichere CSV-Ausgabe; Feedbackfelder werden nicht ausgeführt |
| Shell-Injektion | Analyse wird als Python-Funktion ohne benutzergesteuerte Shell ausgeführt |
| Automatische Regelveränderung | Feedback bleibt getrennt und benötigt fachliche Freigabe |
| Veränderung von Originaldaten | Quellen nur lesend; Ausgaben in getrennten Verzeichnissen |
| Container-Eskalation | Nicht-root-Benutzer, read-only Root-Dateisystem, `no-new-privileges` |
| Daten in Docker-Image oder Git | `.dockerignore` und `.gitignore` schließen lokale Daten aus |
| Unvollständige Läufe | atomare Laufverzeichnisse und Manifest aus bestehender Pipeline |

## Offene Punkte vor Mehrbenutzerbetrieb

- Authentifizierung und Rollenmodell,
- TLS und freigegebener Reverse Proxy,
- zentrale Protokollierung ohne vertrauliche Inhalte,
- Backup- und Aufbewahrungsregeln für Feedback und Ergebnisse,
- verbindliche Freigabe der erreichbaren Datenpfade,
- Schutz vor parallelen Instanzen auf gemeinsamem Speicher,
- Sicherheitsprüfung und dokumentierter Wiederherstellungstest.

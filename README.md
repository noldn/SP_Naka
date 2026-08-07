# SP_Naka

SP_Naka wird lokal entwickelt und über GitHub versioniert und dokumentiert.
Das Programm darf lokale Daten verarbeiten, ohne diese Daten in das
GitHub-Repository hochzuladen.

Das Projektziel steht in [PROJECT_GOAL.md](PROJECT_GOAL.md). Verbindliche
Entwicklungsleitplanken für Menschen und KI-Agenten stehen in
[AGENTS.md](AGENTS.md). Der Einstieg in die Projektdokumentation befindet sich in
[docs/INDEX.md](docs/INDEX.md).

## Projektstruktur

```text
SP_Na/
├── src/                 Programmcode
├── tests/               Automatisierte Tests
├── docs/                Projektdokumentation
├── config/              Versionierbare Beispielkonfiguration
├── data/
│   ├── README.md        Regeln für lokale Daten
│   └── local/           Lokale Daten (nicht in GitHub)
├── .env.example         Vorlage für lokale Einstellungen
├── AGENTS.md             Verbindliche Entwicklungsleitplanken
├── PROJECT_GOAL.md       Ziel, Umfang und Erfolgskriterien
└── .gitignore           Ausschlüsse für GitHub
```

## Lokale Einrichtung

1. Repository klonen.
2. `.env.example` als `.env` kopieren.
3. Lokale Daten in `data/local/` ablegen.
4. In `.env` den lokalen Datenpfad konfigurieren.
5. Die für die gewählte Programmiersprache benötigten Abhängigkeiten installieren.

Beispiel:

```bash
cp .env.example .env
```

## Datenschutz und GitHub

Folgende Inhalte dürfen nicht committed werden:

- Dateien aus `data/local/`
- `.env` und andere Dateien mit Zugangsdaten
- personenbezogene, vertrauliche oder lizenzrechtlich geschützte Daten
- lokale Datenbanken und generierte Ausgabedateien
- vertrauliche Arbeitsnotizen aus `docs/private/`

Vor jedem Commit sollte geprüft werden, welche Dateien aufgenommen werden:

```bash
git status
git diff --staged
```

Weitere technische Entscheidungen werden in [docs/ARCHITEKTUR.md](docs/ARCHITEKTUR.md)
dokumentiert.

## Dokumentation und Notizen

Markdown-Dateien sind normale Textdateien und können auf allen Systemen über Git
synchronisiert, durchsucht und später in ein Intranet übertragen werden.

- Laufende, nicht vertrauliche Notizen: `docs/notes/`
- Dauerhafte Entscheidungen: `docs/decisions/`
- Datenbeschreibungen ohne Rohdaten: `docs/data/`
- Für das Intranet geprüfte Inhalte: `docs/intranet/`
- Nur lokale vertrauliche Notizen: `docs/private/` (von Git ausgeschlossen)

## GitHub-Workflow

Für Änderungen wird jeweils ein eigener Branch verwendet:

```bash
git switch -c feature/kurze-beschreibung
git add src tests docs config .env.example .gitignore README.md
git commit -m "Kurze Beschreibung der Änderung"
git push -u origin feature/kurze-beschreibung
```

Anschließend wird auf GitHub ein Pull Request erstellt. So bleiben Änderungen
nachvollziehbar und können vor dem Zusammenführen geprüft werden.

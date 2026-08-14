#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin:${PATH}"

REPOSITORY_URL="https://github.com/noldn/SP_Naka.git"
DEFAULT_TARGET="${HOME}/Documents/SP_Naka"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker Desktop ist noch nicht installiert."
  echo "Bitte zuerst https://www.docker.com/products/docker-desktop/ installieren."
  read -r -p "Zum Beenden Eingabetaste drücken."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  open -a Docker
  echo "Docker Desktop wird gestartet ..."
  for _ in {1..60}; do
    docker info >/dev/null 2>&1 && break
    sleep 2
  done
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker Desktop konnte nicht rechtzeitig gestartet werden."
  exit 1
fi

if [[ -f "${SCRIPT_DIR}/compose.yaml" ]]; then
  PROJECT_DIR="$SCRIPT_DIR"
elif [[ -d "${DEFAULT_TARGET}/.git" ]]; then
  PROJECT_DIR="$DEFAULT_TARGET"
  if [[ -n "$(git -C "$PROJECT_DIR" status --porcelain)" ]]; then
    echo "Im vorhandenen Projekt gibt es lokale Änderungen. Es wird nicht automatisch aktualisiert."
  else
    git -C "$PROJECT_DIR" pull --ff-only
  fi
else
  git clone "$REPOSITORY_URL" "$DEFAULT_TARGET"
  PROJECT_DIR="$DEFAULT_TARGET"
fi

mkdir -p "$PROJECT_DIR/data/local" "$PROJECT_DIR/output"
docker compose -f "$PROJECT_DIR/compose.yaml" build

START_ICON="${HOME}/Desktop/SP_Naka starten.command"
STOP_ICON="${HOME}/Desktop/SP_Naka stoppen.command"
printf '#!/usr/bin/env bash\nexec "%s/start_docker_macos.command"\n' "$PROJECT_DIR" > "$START_ICON"
printf '#!/usr/bin/env bash\nexec "%s/stop_docker_macos.command"\n' "$PROJECT_DIR" > "$STOP_ICON"
chmod +x "$START_ICON" "$STOP_ICON" "$PROJECT_DIR/start_docker_macos.command" "$PROJECT_DIR/stop_docker_macos.command"

echo "Installation abgeschlossen."
echo "Daten bitte unter $PROJECT_DIR/data/local ablegen."
echo "Danach das Desktop-Symbol 'SP_Naka starten' verwenden."
read -r -p "Zum Beenden Eingabetaste drücken."

#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin:${PATH}"

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  osascript -e 'display alert "Docker Desktop fehlt" message "Bitte Docker Desktop installieren und danach erneut starten."'
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  open -a Docker
  for _ in {1..60}; do
    docker info >/dev/null 2>&1 && break
    sleep 2
  done
fi
if ! docker info >/dev/null 2>&1; then
  osascript -e 'display alert "Docker ist nicht bereit" message "Bitte Docker Desktop vollständig starten und erneut versuchen."'
  exit 1
fi

docker compose up -d --build
sleep 2
open "http://localhost:8765"

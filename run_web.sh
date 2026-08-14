#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
export SP_NAKA_WEB_HOST="${SP_NAKA_WEB_HOST:-127.0.0.1}"
export SP_NAKA_WEB_PORT="${SP_NAKA_WEB_PORT:-8765}"
exec python3 -m sp_naka.webapp

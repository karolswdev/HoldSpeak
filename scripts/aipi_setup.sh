#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AIPI_DIR="$ROOT_DIR/aipi-lite"
VENV_DIR="${AIPI_VENV:-$AIPI_DIR/.venv}"
PYTHON_BIN="${PYTHON:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/aipi_setup.sh

Creates/updates the local AIPI-Lite bridge test/runtime environment at:
  aipi-lite/.venv

The environment installs:
  - aipi-lite/requirements-dev.txt
  - this HoldSpeak checkout in editable mode, so protocol-sync tests can
    import HoldSpeak's device contract models.

Environment:
  AIPI_VENV=/path/to/venv   Override the venv location.
  PYTHON=python3.12         Override the Python executable.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -d "$AIPI_DIR" ]]; then
  echo "ERROR: $AIPI_DIR does not exist." >&2
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: Python executable not found: $PYTHON_BIN" >&2
  exit 1
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$AIPI_DIR/requirements-dev.txt"
"$VENV_DIR/bin/python" -m pip install -e "$ROOT_DIR"

echo "AIPI-Lite environment ready: $VENV_DIR"

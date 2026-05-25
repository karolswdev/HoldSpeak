#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AIPI_DIR="$ROOT_DIR/aipi-lite"
VENV_DIR="${AIPI_VENV:-$AIPI_DIR/.venv}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/aipi_test.sh [pytest args...]

Runs the AIPI-Lite bridge test suite from the unified HoldSpeak checkout.
Passes any arguments through to pytest.

Examples:
  scripts/aipi_test.sh
  scripts/aipi_test.sh tests/test_settings.py -q

Environment:
  AIPI_VENV=/path/to/venv   Override the venv location.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "ERROR: AIPI venv missing: $VENV_DIR" >&2
  echo "Run: scripts/aipi_setup.sh" >&2
  exit 1
fi

cd "$AIPI_DIR"
if [[ $# -eq 0 ]]; then
  set -- tests
fi
"$VENV_DIR/bin/python" -m pytest "$@"

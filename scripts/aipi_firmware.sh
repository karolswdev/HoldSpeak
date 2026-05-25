#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AIPI_DIR="$ROOT_DIR/aipi-lite"

usage() {
  cat <<'USAGE'
Usage:
  scripts/aipi_firmware.sh <esphome args...>

Runs ESPHome from the unified HoldSpeak checkout with cwd set to aipi-lite/.

Examples:
  scripts/aipi_firmware.sh compile aipi.yaml
  scripts/aipi_firmware.sh run aipi.yaml --device /dev/ttyACM0
  scripts/aipi_firmware.sh logs aipi.yaml

Install ESPHome with one of:
  pipx install esphome
  uv tool install esphome
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -eq 0 ]]; then
  usage
  exit 0
fi

if ! command -v esphome >/dev/null 2>&1; then
  echo "ERROR: esphome not found. Install with: pipx install esphome" >&2
  exit 1
fi

cd "$AIPI_DIR"
exec esphome "$@"

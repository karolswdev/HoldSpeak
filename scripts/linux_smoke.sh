#!/usr/bin/env bash
set -euo pipefail

echo "HoldSpeak Linux smoke"
echo "====================="
echo

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage:
  scripts/linux_smoke.sh

What it does:
  - Prints basic environment info
  - Verifies required binaries (best-effort)
  - Imports key HoldSpeak modules without downloading models
  - Runs lightweight audio-device and monitor-source discovery calls

Notes:
  - Does NOT instantiate Whisper models (avoids downloads).
  - Does NOT start the TUI.
EOF
  exit 0
fi

echo "System:"
uname -a || true
echo "Session env:"
echo "  XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-}"
echo "  WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-}"
echo "  DISPLAY=${DISPLAY:-}"
echo

echo "Binaries:"
for bin in python uv ffmpeg pactl xclip wl-copy wl-paste; do
  if command -v "$bin" >/dev/null 2>&1; then
    echo "  OK  $bin -> $(command -v "$bin")"
  else
    echo "  --  $bin (not found)"
  fi
done
echo

resolve_python() {
  if [[ -x ".venv/bin/python" ]]; then
    printf '%s\n' "$(pwd)/.venv/bin/python"
    return 0
  fi

  if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
    printf '%s\n' "${VIRTUAL_ENV}/bin/python"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  return 1
}

if ! PYTHON_BIN="$(resolve_python)"; then
  echo "ERROR: No python interpreter found." >&2
  echo "Install python3 (recommended) or python, then rerun this smoke test." >&2
  exit 1
fi

echo "Python:"
echo "  selected: $PYTHON_BIN"
"$PYTHON_BIN" --version
echo

echo "Imports (no model load):"
"$PYTHON_BIN" - <<'PY'
import sys
from unittest.mock import patch

print("  python:", sys.version.split()[0])

import holdspeak  # noqa: F401
print("  holdspeak: import ok")

from holdspeak import transcribe as t
print("  holdspeak.transcribe: import ok")
print("    mlx modules available:", bool(getattr(t, "_module_available", lambda _m: False)("mlx")))
print("    mlx_whisper available:", bool(getattr(t, "_module_available", lambda _m: False)("mlx_whisper")))
print("    faster_whisper available:", bool(getattr(t, "_module_available", lambda _m: False)("faster_whisper")))

from holdspeak import audio_devices as ad
print("  holdspeak.audio_devices: import ok")

try:
    monitor = ad.find_pulse_monitor_source()
    print("    pactl monitor source:", monitor)
except Exception as exc:
    print("    pactl monitor source: ERROR:", exc)

try:
    with patch("holdspeak.audio_devices.subprocess.run", side_effect=FileNotFoundError("pactl")):
        monitor = ad.find_pulse_monitor_source()
        print("    pactl missing simulation:", monitor)
except Exception as exc:
    print("    pactl missing simulation: ERROR:", exc)

try:
    devs = ad.query_devices()
    print("  sounddevice.query_devices:", len(devs), "devices")
except Exception as exc:
    print("  sounddevice.query_devices: ERROR:", exc)
PY
echo

echo "OK"

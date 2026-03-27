#!/usr/bin/env bash
set -euo pipefail

# HoldSpeak installer
# - Installs minimal OS dependencies when possible
# - Creates an isolated venv under ~/.local/share/holdspeak
# - Installs HoldSpeak and places a wrapper in ~/.local/bin/holdspeak

INSTALL_ROOT="${HOLDSPEAK_INSTALL_ROOT:-$HOME/.local/share/holdspeak}"
BIN_DIR="${HOLDSPEAK_BIN_DIR:-$HOME/.local/bin}"
VENV_DIR="$INSTALL_ROOT/venv"

# Override this to pin a release tag/commit or use a local/package spec.
# Examples:
#   HOLDSPEAK_PIP_SPEC="holdspeak[linux]==0.2.0"
#   HOLDSPEAK_PIP_SPEC="holdspeak[linux] @ git+https://github.com/karolswdev/HoldSpeak.git@main"
HOLDSPEAK_PIP_SPEC="${HOLDSPEAK_PIP_SPEC:-}"

WITH_MEETING=0
SKIP_SYSTEM_DEPS="${HOLDSPEAK_SKIP_SYSTEM_DEPS:-0}"

usage() {
  cat <<USAGE
Usage: bash scripts/install.sh [--with-meeting] [--skip-system-deps]

Options:
  --with-meeting      Install meeting extras ([meeting])
  --skip-system-deps  Skip apt/brew dependency install
  -h, --help          Show help

Environment variables:
  HOLDSPEAK_INSTALL_ROOT    Install root (default: ~/.local/share/holdspeak)
  HOLDSPEAK_BIN_DIR         Wrapper bin dir (default: ~/.local/bin)
  HOLDSPEAK_PIP_SPEC        Full pip requirement spec override
  HOLDSPEAK_SKIP_SYSTEM_DEPS=1  Skip apt/brew dependency install
USAGE
}

log() { printf '[holdspeak-install] %s\n' "$*"; }
warn() { printf '[holdspeak-install] WARN: %s\n' "$*" >&2; }
err() { printf '[holdspeak-install] ERROR: %s\n' "$*" >&2; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --with-meeting) WITH_MEETING=1 ;;
    --skip-system-deps) SKIP_SYSTEM_DEPS=1 ;;
    -h|--help) usage; exit 0 ;;
    *) err "Unknown argument: $arg" ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  err "python3 not found. Install Python 3.10+ and rerun."
fi

PY_VERSION_RAW="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PY_MAJOR="${PY_VERSION_RAW%%.*}"
PY_MINOR="${PY_VERSION_RAW##*.}"
if (( PY_MAJOR < 3 || (PY_MAJOR == 3 && PY_MINOR < 10) )); then
  err "Python 3.10+ required. Found $PY_VERSION_RAW"
fi

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
EXTRAS=""
if [[ "$OS" == "linux" ]]; then
  EXTRAS="linux"
fi
if (( WITH_MEETING == 1 )); then
  if [[ -n "$EXTRAS" ]]; then
    EXTRAS="$EXTRAS,meeting"
  else
    EXTRAS="meeting"
  fi
fi
if [[ -n "$EXTRAS" ]]; then
  EXTRAS="[$EXTRAS]"
fi

install_linux_deps() {
  if (( SKIP_SYSTEM_DEPS == 1 )); then
    log "Skipping Linux system dependencies (HOLDSPEAK_SKIP_SYSTEM_DEPS=1)"
    return
  fi

  if ! command -v apt-get >/dev/null 2>&1; then
    warn "apt-get not found. Install these manually: ffmpeg libportaudio2 xclip pulseaudio-utils"
    return
  fi

  local pkgs=(ffmpeg libportaudio2 xclip pulseaudio-utils)
  log "Installing Linux system dependencies: ${pkgs[*]}"

  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y "${pkgs[@]}"
  else
    apt-get update
    apt-get install -y "${pkgs[@]}"
  fi
}

install_macos_deps() {
  if (( SKIP_SYSTEM_DEPS == 1 )); then
    log "Skipping macOS system dependencies (HOLDSPEAK_SKIP_SYSTEM_DEPS=1)"
    return
  fi

  if ! command -v brew >/dev/null 2>&1; then
    warn "Homebrew not found. Install Homebrew, then install: portaudio ffmpeg"
    return
  fi

  log "Installing macOS system dependencies: portaudio ffmpeg"
  brew install portaudio ffmpeg || true
}

if [[ "$OS" == "linux" ]]; then
  install_linux_deps
elif [[ "$OS" == "darwin" ]]; then
  install_macos_deps
else
  warn "Unsupported OS '$OS'. Proceeding with Python-only install."
fi

mkdir -p "$INSTALL_ROOT" "$BIN_DIR"

log "Creating virtual environment at $VENV_DIR"
python3 -m venv "$VENV_DIR"

log "Upgrading pip"
"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel

if [[ -z "$HOLDSPEAK_PIP_SPEC" ]]; then
  SOURCE="git+https://github.com/karolswdev/HoldSpeak.git@main"
  HOLDSPEAK_PIP_SPEC="holdspeak${EXTRAS} @ ${SOURCE}"
fi

log "Installing $HOLDSPEAK_PIP_SPEC"
"$VENV_DIR/bin/pip" install "$HOLDSPEAK_PIP_SPEC"

WRAPPER="$BIN_DIR/holdspeak"
cat > "$WRAPPER" <<WRAP
#!/usr/bin/env bash
exec "$VENV_DIR/bin/holdspeak" "\$@"
WRAP
chmod +x "$WRAPPER"

log "Installed HoldSpeak wrapper: $WRAPPER"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  warn "$BIN_DIR is not in PATH. Add this line to your shell profile:"
  warn "  export PATH=\"$BIN_DIR:\$PATH\""
fi

log "Running setup check"
"$WRAPPER" doctor || true

log "Install complete. Start with: holdspeak"

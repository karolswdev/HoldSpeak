#!/usr/bin/env bash
# Build the dogfood sandbox: an isolated HOME with a holdspeak config wired for
# either the fast plumbing tier (no LLM) or the real-metal tier (.43 intel).
#
#   dogfood/setup.sh              # tier-2 real-metal config (default)
#   dogfood/setup.sh --tier1      # fast no-LLM plumbing config
#   dogfood/setup.sh --force      # overwrite an existing sandbox config
#
# Endpoint overrides (tier 2):
#   DOGFOOD_INTEL_BASE_URL=http://192.168.1.43:8080/v1
#   DOGFOOD_INTEL_MODEL=Qwen3.5-9B-UD-Q6_K_XL.gguf
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOGFOOD_HOME="${DOGFOOD_HOME:-$HERE/_home}"
REAL_HOME="${REAL_HOME:-$HOME}"

TIER=2
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --tier1) TIER=1 ;;
    --tier2) TIER=2 ;;
    --force) FORCE=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

INTEL_BASE_URL="${DOGFOOD_INTEL_BASE_URL:-http://192.168.1.43:8080/v1}"
INTEL_MODEL="${DOGFOOD_INTEL_MODEL:-Qwen3.5-9B-UD-Q6_K_XL.gguf}"

echo "Dogfood sandbox HOME: $DOGFOOD_HOME"
mkdir -p "$DOGFOOD_HOME/.config/holdspeak" \
         "$DOGFOOD_HOME/.local/share/holdspeak" \
         "$DOGFOOD_HOME/.cache"

# Reuse model caches from the real HOME so the sandbox doesn't re-download.
link_cache() {
  local rel="$1" src="$REAL_HOME/$1" dst="$DOGFOOD_HOME/$1"
  if [[ -e "$src" && ! -e "$dst" ]]; then
    mkdir -p "$(dirname "$dst")"
    ln -s "$src" "$dst"
    echo "  linked $rel -> $src"
  fi
}
link_cache ".cache/huggingface"
link_cache "Models"

CONFIG="$DOGFOOD_HOME/.config/holdspeak/config.json"
if [[ -f "$CONFIG" && "$FORCE" -ne 1 ]]; then
  echo "Config exists: $CONFIG"
  echo "  (re-run with --force to overwrite)"
  exit 0
fi

if [[ "$TIER" -eq 1 ]]; then
  echo "Writing TIER 1 (plumbing, no LLM) config"
  cat > "$CONFIG" <<'JSON'
{
  "config_version": 1,
  "model": { "name": "base", "language": "auto", "warm_on_start": false },
  "meeting": {
    "intel_enabled": false,
    "intent_router_enabled": false,
    "allow_actuators": false
  },
  "dictation": {
    "pipeline": { "enabled": false, "journal_enabled": true },
    "spoken_symbols": [
      { "spoken": "at sign", "symbol": "@", "attach": "none" },
      { "spoken": "hash", "symbol": "#", "attach": "left" },
      { "spoken": "dash", "symbol": "-", "attach": "none" },
      { "spoken": "percent sign", "symbol": "%", "attach": "left" }
    ]
  }
}
JSON
else
  echo "Writing TIER 2 (real-metal) config -> intel at $INTEL_BASE_URL ($INTEL_MODEL)"
  cat > "$CONFIG" <<JSON
{
  "config_version": 1,
  "model": { "name": "base", "language": "auto", "warm_on_start": true },
  "meeting": {
    "intel_enabled": true,
    "intel_provider": "cloud",
    "intel_cloud_base_url": "$INTEL_BASE_URL",
    "intel_cloud_model": "$INTEL_MODEL",
    "intent_router_enabled": true,
    "mir_profile": "balanced",
    "intent_segment_probe_enabled": true,
    "allow_actuators": false,
    "allowed_actuators": [],
    "webhook_allowed_hosts": [],
    "slack_webhook_url": ""
  },
  "dictation": {
    "pipeline": {
      "enabled": true,
      "stages": ["intent-router", "kb-enricher"],
      "max_total_latency_ms": 8000,
      "rewrite_passes": 2,
      "corrections_enabled": true,
      "target_detect_llm_enabled": true,
      "journal_enabled": true
    },
    "runtime": {
      "backend": "openai_compatible",
      "openai_compatible_base_url": "$INTEL_BASE_URL",
      "openai_compatible_model": "$INTEL_MODEL",
      "openai_compatible_api_key_env": "OPENAI_API_KEY",
      "openai_compatible_timeout_seconds": 30.0
    },
    "macros": {
      "enabled": true,
      "items": [
        { "keyword": "open inbox", "action": { "kind": "open_url", "payload": "https://mail.google.com" } },
        { "keyword": "launch editor", "action": { "kind": "launch_app", "payload": "TextEdit" } },
        { "keyword": "list files", "action": { "kind": "shell", "payload": "ls -la" } },
        { "keyword": "paste quote", "action": { "kind": "type_text", "payload": "\"correctness over cleverness\"" } }
      ]
    },
    "spoken_symbols": [
      { "spoken": "at sign", "symbol": "@", "attach": "none" },
      { "spoken": "hash", "symbol": "#", "attach": "left" },
      { "spoken": "dash", "symbol": "-", "attach": "none" },
      { "spoken": "percent sign", "symbol": "%", "attach": "left" }
    ]
  }
}
JSON
fi

echo "Wrote $CONFIG"
echo
echo "Next:"
echo "  dogfood/hs doctor              # verify the isolated runtime"
echo "  python dogfood/make_fixtures.py   # render audio (macOS say)"
echo "  see dogfood/PROTOCOL.md         # the test protocol"

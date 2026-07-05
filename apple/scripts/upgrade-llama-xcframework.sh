#!/usr/bin/env bash
# Upgrade the on-device engine: swap LLM.swift's stale (2025-12) vendored
# llama.cpp xcframework for a CURRENT build that supports the frontier
# on-device archs — Gemma 4 (`gemma4`) and Qwen3.5 (`qwen35`) — which the
# shipped LLM.swift 2.1.0 binary lacks.
#
# Proven 2026-07-05: after this swap the app builds + links, and the framework
# binary carries gemma4/gemma4-assistant/qwen35 (verified via `strings`).
#
# Usage:  scripts/upgrade-llama-xcframework.sh <derived-data-path>
#   e.g.  scripts/upgrade-llama-xcframework.sh build/dd-device
#
# Runs AFTER package resolution (i.e. after patch-llm-macro.sh has cloned
# LLM.swift into <derived-data>/SourcePackages/checkouts). Idempotent: if the
# checkout's framework already has `gemma4`, it no-ops.
#
# Reproducible: pinned to the llama.cpp commit below. Uses a per-commit cache
# in ~/.holdspeak-build-cache so only the FIRST run pays the ~15-min build;
# later runs (and other derived-data dirs) copy from cache instantly.
set -euo pipefail

LLAMA_COMMIT="2da6686"                       # ggml-org/llama.cpp, 2026-07-05 (has gemma4 + qwen35)
DD="${1:?usage: upgrade-llama-xcframework.sh <derived-data-path>}"
CHECKOUT="$DD/SourcePackages/checkouts/LLM.swift/llama.cpp/llama.xcframework"
CACHE="$HOME/.holdspeak-build-cache/llama-xcframework-$LLAMA_COMMIT"
DEV="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"

if [[ ! -d "$CHECKOUT" ]]; then
  echo "== no LLM.swift checkout at $CHECKOUT — run patch-llm-macro.sh first" >&2
  exit 1
fi

# Whether the checkout's device framework already carries the frontier arch.
# NOTE: use `grep -c` (reads all input), not `grep -q` — with `set -o pipefail`,
# grep -q closes the pipe early and SIGPIPEs `strings`, which pipefail then
# reports as a failure even on a match (a false negative).
has_gemma4() {
  [[ "$(strings "$1" 2>/dev/null | grep -cw gemma4 || true)" -gt 0 ]]
}
DEV_FW="$CHECKOUT/ios-arm64/llama.framework/llama"

# Already upgraded? (the frontier arch is the tell)
if has_gemma4 "$DEV_FW"; then
  echo "== engine already current (gemma4 present) — nothing to do"
  exit 0
fi

# Build the xcframework once, cache it per commit.
if [[ ! -d "$CACHE" ]]; then
  echo "== building llama.cpp xcframework @ $LLAMA_COMMIT (first run, ~15 min) =="
  WORK="$(mktemp -d)"
  git clone --filter=blob:none "https://github.com/ggml-org/llama.cpp.git" "$WORK/llama.cpp"
  git -C "$WORK/llama.cpp" checkout "$LLAMA_COMMIT"
  ( cd "$WORK/llama.cpp" && DEVELOPER_DIR="$DEV" ./build-xcframework.sh )
  mkdir -p "$(dirname "$CACHE")"
  cp -R "$WORK/llama.cpp/build-apple/llama.xcframework" "$CACHE"
  rm -rf "$WORK"
else
  echo "== using cached xcframework at $CACHE"
fi

# Swap it in (keep a one-shot backup of the stale one).
rm -rf "$CHECKOUT.stale"
mv "$CHECKOUT" "$CHECKOUT.stale"
cp -R "$CACHE" "$CHECKOUT"

if has_gemma4 "$DEV_FW"; then
  echo "== engine upgraded: gemma4 + qwen35 now available on-device"
else
  echo "== WARNING: swap done but gemma4 not found — check the build" >&2
  exit 1
fi

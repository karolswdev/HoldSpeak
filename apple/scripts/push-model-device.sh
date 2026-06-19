#!/bin/bash
# HSM-5-03 (dev loop): push a local GGUF onto the iPad/iPhone app's data container
# with devicectl, so the on-device engine (HSM-5-02) has a model without going
# through the App Store or an in-app download. This is the developer counterpart to
# the two shipping paths (Files sideload + Hugging Face download).
#
# Usage: apple/scripts/push-model-device.sh <local-gguf> [device-udid] [dest-name]
#   Copies into the app's Documents/ — the model manager imports from there (or the
#   harness loads it). Requires the app to be installed first (harness-device.sh).
#
# NOTE: unverified while the target iPad is locked; the devicectl invocation is the
# documented path and runs once the device is unlocked.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="${1:?usage: push-model-device.sh <local-gguf> [device-udid] [dest-name]}"
[ -f "$SRC" ] || { echo "no such file: $SRC" >&2; exit 1; }
BUNDLE_ID="dev.holdspeak.mobile"
DEST_NAME="${3:-$(basename "$SRC")}"

DEVID="${2:-}"
if [ -z "$DEVID" ]; then
  UUID_RE='[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
  LIST="$(xcrun devicectl list devices 2>/dev/null || true)"
  DEVID="$(printf '%s\n' "$LIST" | grep -i 'iPad' | grep -oE "$UUID_RE" | head -1 || true)"
  [ -z "$DEVID" ] && DEVID="$(printf '%s\n' "$LIST" | grep -iE 'iPad|iPhone' | grep -oE "$UUID_RE" | head -1 || true)"
fi
echo "== pushing $(basename "$SRC") ($(du -h "$SRC" | cut -f1)) -> $BUNDLE_ID:Documents/$DEST_NAME on ${DEVID:-<none>} =="

xcrun devicectl device copy to \
  --device "$DEVID" \
  --domain-type appDataContainer \
  --domain-identifier "$BUNDLE_ID" \
  --source "$SRC" \
  --destination "Documents/$DEST_NAME"

echo "== done — the app can now import/load Documents/$DEST_NAME =="

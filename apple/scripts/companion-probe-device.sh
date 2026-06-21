#!/bin/bash
# HSM-12-01 (real-metal): build + sign the Companion probe and install/launch it on a
# physical iPad/iPhone. The probe points at a HoldSpeak desktop/homelab server and
# proves the seam: pairing -> handshake against /health + /api/runtime/status ->
# reachable / runtime-ready / honest egress. No model push (pure networking).
#
# Point it hands-off by exporting the desktop coordinates before running; they are
# injected into the launched process so it auto-probes on open. Or leave them unset
# and fill the form on the device.
#
#   HS_DESKTOP_HOST=192.168.1.28 HS_DESKTOP_PORT=8000 HS_DESKTOP_TOKEN=<token> \
#     apple/scripts/companion-probe-device.sh [device-udid]
set -euo pipefail
cd "$(dirname "$0")/.."

ruby scripts/gen-companion-probe.rb

DEVID="${1:-}"
if [ -z "$DEVID" ]; then
  UUID_RE='[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
  LIST="$(xcrun devicectl list devices 2>/dev/null || true)"
  DEVID="$(printf '%s\n' "$LIST" | grep -i 'iPad' | grep -oE "$UUID_RE" | head -1 || true)"
  [ -z "$DEVID" ] && DEVID="$(printf '%s\n' "$LIST" | grep -iE 'iPad|iPhone' | grep -oE "$UUID_RE" | head -1 || true)"
fi
echo "== target device: ${DEVID:-<none found>} =="

# No external package deps here, so no -skipMacroValidation needed; keep the isolated
# derivedDataPath posture for parity with the other device harnesses.
echo "== build + sign (generic/platform=iOS) =="
xcodebuild -project build/HoldSpeakCompanionProbe.xcodeproj -scheme HoldSpeakMobile \
  -configuration Debug \
  -destination 'generic/platform=iOS' \
  -allowProvisioningUpdates \
  -derivedDataPath build/dd-companion \
  build

APP="$PWD/build/dd-companion/Build/Products/Debug-iphoneos/HoldSpeakMobile.app"
echo "== install $APP =="
xcrun devicectl device install app --device "$DEVID" "$APP"

# Inject desktop coordinates so the probe auto-connects on launch (hands-off proof).
ENVJSON=""
add_env() { # key value
  [ -z "$2" ] && return 0
  if [ -z "$ENVJSON" ]; then ENVJSON="\"$1\":\"$2\""; else ENVJSON="$ENVJSON,\"$1\":\"$2\""; fi
}
add_env HS_DESKTOP_HOST  "${HS_DESKTOP_HOST:-}"
add_env HS_DESKTOP_PORT  "${HS_DESKTOP_PORT:-}"
add_env HS_DESKTOP_TOKEN "${HS_DESKTOP_TOKEN:-}"

echo "== launch =="
if [ -n "$ENVJSON" ]; then
  echo "   (auto-probing ${HS_DESKTOP_HOST:-?}:${HS_DESKTOP_PORT:-?})"
  xcrun devicectl device process launch --terminate-existing --device "$DEVID" \
    --environment-variables "{$ENVJSON}" dev.holdspeak.mobile
else
  xcrun devicectl device process launch --terminate-existing --device "$DEVID" dev.holdspeak.mobile
fi

echo "== companion probe launched on $DEVID =="
echo "(on the iPad: it probes the desktop's /health + /api/runtime/status and shows reachable / runtime-ready / egress)"

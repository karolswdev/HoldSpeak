#!/bin/bash
# HSM-5-06: build + sign the on-device inference harness and install/launch it on a
# physical iPad, so a real meeting transcript is turned into artifacts on the device
# against a homelab/LAN OpenAI-compatible endpoint (charter Mode C).
#
# Usage: apple/scripts/harness-device.sh [device-udid]
set -euo pipefail
cd "$(dirname "$0")/.."

ruby scripts/gen-inference-harness.rb

DEVID="${1:-}"
if [ -z "$DEVID" ]; then
  UUID_RE='[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
  LIST="$(xcrun devicectl list devices 2>/dev/null || true)"
  DEVID="$(printf '%s\n' "$LIST" | grep -i 'iPad' | grep -oE "$UUID_RE" | head -1 || true)"
  [ -z "$DEVID" ] && DEVID="$(printf '%s\n' "$LIST" | grep -iE 'iPad|iPhone' | grep -oE "$UUID_RE" | head -1 || true)"
fi
echo "== target device: ${DEVID:-<none found>} =="

HWUDID="$(xcrun devicectl device info details --device "$DEVID" 2>/dev/null | awk -F': ' '/ udid:/{print $2; exit}' | tr -d ' ')"
rm -f ~/Library/MobileDevice/Provisioning\ Profiles/*.mobileprovision 2>/dev/null || true
echo "== build + sign (destination id=$HWUDID) =="
xcodebuild -project build/HoldSpeakHarness.xcodeproj -scheme HoldSpeakMobile \
  -configuration Debug \
  -destination "platform=iOS,id=$HWUDID" \
  -allowProvisioningUpdates \
  CONFIGURATION_BUILD_DIR="$PWD/build/harness-device" \
  build

APP="$PWD/build/harness-device/HoldSpeakMobile.app"
echo "== install $APP =="
xcrun devicectl device install app --device "$DEVID" "$APP"

echo "== launch =="
xcrun devicectl device process launch --device "$DEVID" dev.holdspeak.mobile

echo "== HSM-5-06 harness launched on $DEVID =="
echo "(on the iPad: tap Allow on the Local Network prompt, then 'Generate artifacts on device')"

#!/bin/bash
# HSM-14-17 — build + sign the on-device meeting-capture app and install/launch it on a physical
# iPad, so a real recording runs the post-capture speaker-diarization pass (who spoke each segment)
# fully on-device. Mirrors harness-device.sh for the meeting-capture project.
#
# Usage: apple/scripts/meeting-capture-device.sh [device-udid]
set -euo pipefail
cd "$(dirname "$0")/.."

ruby scripts/gen-meeting-capture.rb

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
# Use -derivedDataPath (NOT a flat CONFIGURATION_BUILD_DIR): the app pulls in swift-syntax via
# swift macros, and flattening all products into one dir collides its per-module .o files
# ("Multiple commands produce SwiftSyntax.o"). The nested derived-data layout keeps them apart.
DD="$PWD/build/meeting-capture-dd"
xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile \
  -configuration Debug \
  -destination "platform=iOS,id=$HWUDID" \
  -allowProvisioningUpdates \
  -skipMacroValidation \
  -derivedDataPath "$DD" \
  build

APP="$DD/Build/Products/Debug-iphoneos/HoldSpeakMobile.app"
echo "== install $APP =="
xcrun devicectl device install app --device "$DEVID" "$APP"

echo "== launch =="
xcrun devicectl device process launch --device "$DEVID" dev.holdspeak.mobile

echo "== meeting-capture app launched on $DEVID =="
echo "(on the iPad: Record a short 2-person chat -> Stop -> open the meeting -> the transcript"
echo " blocks are speaker-colored; tap any line to hear it and judge the label.)"

#!/bin/bash
# HSM-13-04 (the gate): build + sign the Companion *voice answer* app and install/launch
# it on a physical iPad. The iPad surfaces the waiting coder's question, records a spoken
# answer, transcribes it ON-DEVICE (WhisperKit), and delivers the text into the coder via
# POST /api/dictation/remote. WhisperKit fetches its Whisper model on first run (needs
# wifi once); after that it's offline.
#
# Point it hands-off by exporting the desktop coordinates before running:
#   HS_DESKTOP_HOST=192.168.1.28 HS_DESKTOP_PORT=8000 HS_DESKTOP_TOKEN=<token> \
#     apple/scripts/companion-answer-device.sh [device-udid]
set -euo pipefail
cd "$(dirname "$0")/.."

ruby scripts/gen-companion-answer.rb

DEVID="${1:-}"
if [ -z "$DEVID" ]; then
  UUID_RE='[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
  LIST="$(xcrun devicectl list devices 2>/dev/null || true)"
  DEVID="$(printf '%s\n' "$LIST" | grep -i 'iPad' | grep -oE "$UUID_RE" | head -1 || true)"
  [ -z "$DEVID" ] && DEVID="$(printf '%s\n' "$LIST" | grep -iE 'iPad|iPhone' | grep -oE "$UUID_RE" | head -1 || true)"
fi
echo "== target device: ${DEVID:-<none found>} =="

# WhisperKit ships Swift macros → -skipMacroValidation; isolated derivedData + SPM dir
# (package deps collide in a flat build dir), as the speak harness does.
echo "== build + sign (generic/platform=iOS) =="
xcodebuild -project build/HoldSpeakCompanionAnswer.xcodeproj -scheme HoldSpeakMobile \
  -configuration Debug \
  -destination 'generic/platform=iOS' \
  -allowProvisioningUpdates \
  -skipMacroValidation \
  -clonedSourcePackagesDirPath build/spm-answer \
  -derivedDataPath build/dd-answer \
  build

APP="$PWD/build/dd-answer/Build/Products/Debug-iphoneos/HoldSpeakMobile.app"
echo "== install $APP =="
xcrun devicectl device install app --device "$DEVID" "$APP"

ENVJSON=""
add_env() { [ -z "$2" ] && return 0; if [ -z "$ENVJSON" ]; then ENVJSON="\"$1\":\"$2\""; else ENVJSON="$ENVJSON,\"$1\":\"$2\""; fi; }
add_env HS_DESKTOP_HOST  "${HS_DESKTOP_HOST:-}"
add_env HS_DESKTOP_PORT  "${HS_DESKTOP_PORT:-}"
add_env HS_DESKTOP_TOKEN "${HS_DESKTOP_TOKEN:-}"

echo "== launch =="
if [ -n "$ENVJSON" ]; then
  xcrun devicectl device process launch --terminate-existing --device "$DEVID" \
    --environment-variables "{$ENVJSON}" dev.holdspeak.mobile
else
  xcrun devicectl device process launch --terminate-existing --device "$DEVID" dev.holdspeak.mobile
fi

echo "== companion answer launched on $DEVID =="
echo "(on the iPad: Allow Microphone, see the waiting question, Hold to speak, review, Send)"

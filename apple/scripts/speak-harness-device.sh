#!/bin/bash
# HSM-3 + HSM-5 "Speak to it": build + sign the speak harness (record -> on-device
# WhisperKit -> local Qwen via llama.cpp) and install/launch it on a physical iPad.
# Reuses the GGUF already in the app's Documents (same bundle id as the local harness),
# so no model re-push is needed. WhisperKit fetches its small Whisper model on first
# run (needs wifi once); after that it's offline.
#
# Usage: apple/scripts/speak-harness-device.sh [device-udid]
set -euo pipefail
cd "$(dirname "$0")/.."

ruby scripts/gen-speak-harness.rb

DEVID="${1:-}"
if [ -z "$DEVID" ]; then
  UUID_RE='[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
  LIST="$(xcrun devicectl list devices 2>/dev/null || true)"
  DEVID="$(printf '%s\n' "$LIST" | grep -i 'iPad' | grep -oE "$UUID_RE" | head -1 || true)"
  [ -z "$DEVID" ] && DEVID="$(printf '%s\n' "$LIST" | grep -iE 'iPad|iPhone' | grep -oE "$UUID_RE" | head -1 || true)"
fi
echo "== target device: ${DEVID:-<none found>} =="

# Same posture as the local harness: -skipMacroValidation (LLM macro plugin) and
# -derivedDataPath (NOT a flat CONFIGURATION_BUILD_DIR — package deps collide).
echo "== build + sign (generic/platform=iOS) =="
xcodebuild -project build/HoldSpeakSpeakHarness.xcodeproj -scheme HoldSpeakMobile \
  -configuration Debug \
  -destination 'generic/platform=iOS' \
  -allowProvisioningUpdates \
  -skipMacroValidation \
  -clonedSourcePackagesDirPath build/spm-speak \
  -derivedDataPath build/dd-speak \
  build

APP="$PWD/build/dd-speak/Build/Products/Debug-iphoneos/HoldSpeakMobile.app"
echo "== install $APP =="
xcrun devicectl device install app --device "$DEVID" "$APP"
echo "== launch =="
xcrun devicectl device process launch --terminate-existing --device "$DEVID" dev.holdspeak.mobile

echo "== speak harness launched on $DEVID =="
echo "(on the iPad: Allow Microphone, tap the mic, talk, tap stop — transcribes + analyzes on-device)"

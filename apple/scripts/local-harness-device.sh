#!/bin/bash
# HSM-5-02: build + sign the FULLY-LOCAL (Mode A) harness and install/launch it on a
# physical iPad, so a meeting transcript is turned into artifacts by a GGUF running on
# the device's Metal — no network. Push a model first with push-model-device.sh.
#
# Usage: apple/scripts/local-harness-device.sh [device-udid]
set -euo pipefail
cd "$(dirname "$0")/.."

ruby scripts/gen-local-harness.rb

DEVID="${1:-}"
if [ -z "$DEVID" ]; then
  UUID_RE='[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
  LIST="$(xcrun devicectl list devices 2>/dev/null || true)"
  DEVID="$(printf '%s\n' "$LIST" | grep -i 'iPad' | grep -oE "$UUID_RE" | head -1 || true)"
  [ -z "$DEVID" ] && DEVID="$(printf '%s\n' "$LIST" | grep -iE 'iPad|iPhone' | grep -oE "$UUID_RE" | head -1 || true)"
fi
echo "== target device: ${DEVID:-<none found>} =="

# Build for a generic iOS destination (does not require a live device tunnel — more
# reliable than pinning the device id when the build-time connection is flaky), then
# install via devicectl which talks to the connected device directly.
#
# NOTE: do NOT flatten CONFIGURATION_BUILD_DIR here — LLM.swift pulls swift-syntax
# (macros), and a flat product dir makes "Multiple commands produce …" collisions for
# those package targets. Use -derivedDataPath (standard per-target layout) instead.
# -skipMacroValidation enables the LLM macro plugin without the interactive trust gate.
echo "== build + sign (generic/platform=iOS) =="
xcodebuild -project build/HoldSpeakLocalHarness.xcodeproj -scheme HoldSpeakMobile \
  -configuration Debug \
  -destination 'generic/platform=iOS' \
  -allowProvisioningUpdates \
  -skipMacroValidation \
  -clonedSourcePackagesDirPath build/spm-local \
  -derivedDataPath build/dd-local \
  build

APP="$PWD/build/dd-local/Build/Products/Debug-iphoneos/HoldSpeakMobile.app"
echo "== install $APP =="
xcrun devicectl device install app --device "$DEVID" "$APP"

echo "== launch =="
xcrun devicectl device process launch --device "$DEVID" dev.holdspeak.mobile

echo "== HSM-5-02 local harness launched on $DEVID =="
echo "(on the iPad: it loads the .gguf you pushed to Documents, tap 'Run on device')"

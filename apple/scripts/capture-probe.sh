#!/bin/bash
# Run the real AudioCaptureService on the iPhone simulator and print the captured
# frame count. Compiles the package's audio sources (cross-module imports stripped
# so it's one module) together with a SwiftUI probe, bundles a .app, grants mic,
# launches with --console, and surfaces PROBE_RESULT.
set -euo pipefail
cd "$(dirname "$0")/.."

DEV="iPhone 17 Pro Max"
BUNDLE_ID="dev.holdspeak.captureprobe"
SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
TMP="build/probe-src"
APP="build/CaptureProbe.app"

rm -rf "$TMP" "$APP"; mkdir -p "$TMP" "$APP"
# Gather sources and strip cross-module imports (compile as one module).
cp Sources/Contracts/*.swift Sources/Providers/Providers.swift \
   Sources/Providers/Audio/*.swift scripts/probe/CaptureProbeApp.swift "$TMP/"
sed -i '' -E '/^import (Contracts|Providers|RuntimeCore)$/d' "$TMP"/*.swift

xcrun --sdk iphonesimulator swiftc \
    -target arm64-apple-ios17.0-simulator -sdk "$SDK" -parse-as-library \
    "$TMP"/*.swift -o "$APP/CaptureProbe"

cat > "$APP/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>CaptureProbe</string>
  <key>CFBundleIdentifier</key><string>${BUNDLE_ID}</string>
  <key>CFBundleExecutable</key><string>CaptureProbe</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>CFBundleShortVersionString</key><string>0.1.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>LSRequiresIPhoneOS</key><true/>
  <key>MinimumOSVersion</key><string>17.0</string>
  <key>UILaunchScreen</key><dict/>
  <key>NSMicrophoneUsageDescription</key><string>Capture probe</string>
  <key>CFBundleSupportedPlatforms</key><array><string>iPhoneSimulator</string></array>
  <key>UIDeviceFamily</key><array><integer>1</integer><integer>2</integer></array>
</dict></plist>
PLIST

xcrun simctl boot "$DEV" 2>/dev/null || true
xcrun simctl bootstatus "$DEV" -b >/dev/null
xcrun simctl install "$DEV" "$APP"
xcrun simctl privacy "$DEV" grant microphone "$BUNDLE_ID" 2>/dev/null || true
echo "== launching probe =="
xcrun simctl launch "$DEV" "$BUNDLE_ID"
sleep 8
CONTAINER="$(xcrun simctl get_app_container "$DEV" "$BUNDLE_ID" data)"
RESULT="$CONTAINER/Documents/probe-result.txt"
echo "== result =="
if [ -f "$RESULT" ]; then cat "$RESULT"; echo; else echo "(no result file written)"; fi
echo "== done =="

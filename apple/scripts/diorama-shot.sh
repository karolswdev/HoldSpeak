#!/bin/bash
# HSM-14 — build the premium 2.5D DESK DIORAMA harness (one SwiftUI module) for the iOS Simulator and
# screenshot it in LANDSCAPE. Isolated from scripts/experience (which now holds a macOS SceneKit CLI).
set -euo pipefail
cd "$(dirname "$0")/.."

DEV="${DIO_DEVICE:-iPad Air 11-inch (M4)}"
BUNDLE_ID="dev.holdspeak.diorama"
SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
TMP="build/diorama-src"
APP="build/Diorama.app"
OUT="${1:-build/diorama-shot.png}"

rm -rf "$TMP" "$APP"; mkdir -p "$TMP" "$APP"
cp scripts/diorama/*.swift "$TMP/"
cp scripts/experience/assets/*.png "$APP/" 2>/dev/null || true   # bespoke PixelLab objects (shared, not duplicated)
cp App/qlippy.png "$APP/" 2>/dev/null || true

xcrun --sdk iphonesimulator swiftc \
  -target arm64-apple-ios17.0-simulator -sdk "$SDK" -parse-as-library \
  "$TMP"/*.swift -o "$APP/Diorama"

cat > "$APP/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Diorama</string>
  <key>CFBundleIdentifier</key><string>${BUNDLE_ID}</string>
  <key>CFBundleExecutable</key><string>Diorama</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>CFBundleShortVersionString</key><string>0.1.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>LSRequiresIPhoneOS</key><true/>
  <key>MinimumOSVersion</key><string>17.0</string>
  <key>UILaunchScreen</key><dict/>
  <key>CFBundleSupportedPlatforms</key><array><string>iPhoneSimulator</string></array>
  <key>UIDeviceFamily</key><array><integer>2</integer></array>
  <key>UIRequiresFullScreen</key><true/>
  <key>UISupportedInterfaceOrientations</key><array>
    <string>UIInterfaceOrientationLandscapeRight</string>
  </array>
  <key>UISupportedInterfaceOrientations~ipad</key><array>
    <string>UIInterfaceOrientationLandscapeRight</string>
  </array>
</dict></plist>
PLIST

xcrun simctl boot "$DEV" 2>/dev/null || true
xcrun simctl bootstatus "$DEV" -b >/dev/null
xcrun simctl install "$DEV" "$APP"
xcrun simctl launch "$DEV" "$BUNDLE_ID" >/dev/null
sleep 6
xcrun simctl io "$DEV" screenshot "$OUT"
echo "shot: $OUT"

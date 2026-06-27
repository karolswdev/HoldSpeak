#!/bin/bash
# HSM-14 — build the MG_Memory ("Echo") harness (one self-contained SwiftUI module) for the iOS Simulator
# and screenshot it (portrait iPad). Mirrors scripts/arkanoid-shot.sh exactly. The screenshot needs an
# ABSOLUTE path. Loop: edit scripts/mg-memory/MGMemory.swift → ./scripts/mg-memory-shot.sh /tmp/x.png → Read it.
set -euo pipefail
cd "$(dirname "$0")/.."

DEV="${MG_DEVICE:-iPad Air 11-inch (M4)}"
BUNDLE_ID="dev.holdspeak.mgmemory"
SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
TMP="build/mg-memory-src"
APP="build/MGMemory.app"
OUT="${1:-build/mg-memory-shot.png}"

rm -rf "$TMP" "$APP"; mkdir -p "$TMP" "$APP"
cp scripts/mg-memory/*.swift "$TMP/"

xcrun --sdk iphonesimulator swiftc \
  -target arm64-apple-ios17.0-simulator -sdk "$SDK" -parse-as-library \
  "$TMP"/*.swift -o "$APP/MGMemory"

cat > "$APP/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>MGMemory</string>
  <key>CFBundleIdentifier</key><string>${BUNDLE_ID}</string>
  <key>CFBundleExecutable</key><string>MGMemory</string>
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
    <string>UIInterfaceOrientationPortrait</string>
  </array>
  <key>UISupportedInterfaceOrientations~ipad</key><array>
    <string>UIInterfaceOrientationPortrait</string>
  </array>
</dict></plist>
PLIST

xcrun simctl boot "$DEV" 2>/dev/null || true
xcrun simctl bootstatus "$DEV" -b >/dev/null
xcrun simctl install "$DEV" "$APP"
xcrun simctl launch "$DEV" "$BUNDLE_ID" >/dev/null
sleep "${MG_SLEEP:-2}"
xcrun simctl io "$DEV" screenshot "$OUT"
echo "shot: $OUT"

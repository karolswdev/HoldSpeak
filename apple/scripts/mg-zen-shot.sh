#!/bin/bash
# HSM-14 — build the STILLWATER zen-toy harness (one self-contained SwiftUI module, @main) for the iOS
# Simulator and screenshot it (portrait iPad). Mirrors scripts/arkanoid-shot.sh exactly. The screenshot
# needs an ABSOLUTE path. HS_DESK_ZEN=shot seeds a believable in-motion frame (simctl cannot tap).
# Loop: edit App/MeetingCapture/DeskMiniGame_Zen.swift + scripts/mg-zen/Zen.swift → ./scripts/mg-zen-shot.sh /tmp/x.png → Read it.
set -euo pipefail
cd "$(dirname "$0")/.."

DEV="${ZEN_DEVICE:-iPad Air 11-inch (M4)}"
BUNDLE_ID="dev.holdspeak.mgzen"
SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
TMP="build/mg-zen-src"
APP="build/MGZen.app"
OUT="${1:-build/mg-zen-shot.png}"

rm -rf "$TMP" "$APP"; mkdir -p "$TMP" "$APP"
cp scripts/mg-zen/*.swift "$TMP/"

xcrun --sdk iphonesimulator swiftc \
  -target arm64-apple-ios17.0-simulator -sdk "$SDK" -parse-as-library \
  "$TMP"/*.swift -o "$APP/MGZen"

cat > "$APP/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>MGZen</string>
  <key>CFBundleIdentifier</key><string>${BUNDLE_ID}</string>
  <key>CFBundleExecutable</key><string>MGZen</string>
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
SIMCTL_CHILD_HS_DESK_ZEN="${HS_DESK_ZEN:-shot}" xcrun simctl launch "$DEV" "$BUNDLE_ID" >/dev/null
sleep "${ZEN_SLEEP:-3}"
xcrun simctl io "$DEV" screenshot "$OUT"
echo "shot: $OUT"

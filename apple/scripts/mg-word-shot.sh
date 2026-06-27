#!/bin/bash
# HSM-14 — build the WORD mini-game (MG_Word) harness as one SwiftUI module for the iOS Simulator and
# screenshot it in PORTRAIT on the iPad Air. Mirrors scripts/diorama-shot.sh. The harness copies the desk
# palette locally and renders MG_Word inside a faux launcher window so we can judge the real fit + feel.
set -euo pipefail
cd "$(dirname "$0")/.."

DEV="${MG_DEVICE:-iPad Air 11-inch (M4)}"
BUNDLE_ID="dev.holdspeak.mgword"
SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
TMP="build/mg-word-src"
APP="build/MGWord.app"
OUT="${1:-build/mg-word-shot.png}"

rm -rf "$TMP" "$APP"; mkdir -p "$TMP" "$APP"
cp scripts/mg-word/Harness.swift "$TMP/"
cp App/MeetingCapture/DeskMiniGame_Word.swift "$TMP/"

xcrun --sdk iphonesimulator swiftc \
  -target arm64-apple-ios17.0-simulator -sdk "$SDK" -parse-as-library \
  "$TMP"/*.swift -o "$APP/MGWord"

cat > "$APP/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>MGWord</string>
  <key>CFBundleIdentifier</key><string>${BUNDLE_ID}</string>
  <key>CFBundleExecutable</key><string>MGWord</string>
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
# HS_MG_WORD=mid stages a believable mid-puzzle frame (first letters forged, a streak running)
SIMCTL_CHILD_HS_MG_WORD="${HS_MG_WORD:-mid}" xcrun simctl launch "$DEV" "$BUNDLE_ID" >/dev/null
sleep 5
xcrun simctl io "$DEV" screenshot "$OUT"
echo "shot: $OUT"

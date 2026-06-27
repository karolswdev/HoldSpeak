#!/bin/bash
# HSM — build the LOGIC mini-game ("Tenfold") harness for the iOS Simulator and screenshot it in PORTRAIT.
# Compiles the real game file (App/MeetingCapture/DeskMiniGame_Logic.swift) + the harness wrapper, so the
# screenshot proves the ACTUAL shipped MG_Logic view, not a copy.
set -euo pipefail
cd "$(dirname "$0")/.."

DEV="${DIO_DEVICE:-iPad Air 11-inch (M4)}"
BUNDLE_ID="dev.holdspeak.mglogic"
SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
TMP="build/mg-logic-src"
APP="build/MGLogic.app"
OUT="${1:-build/mg-logic-shot.png}"
SEED="${HS_MG_LOGIC:-seed}"   # default to the staged mid-draw board

rm -rf "$TMP" "$APP"; mkdir -p "$TMP" "$APP"
cp App/MeetingCapture/DeskMiniGame_Logic.swift "$TMP/"
cp scripts/mg-logic/Harness.swift "$TMP/"

xcrun --sdk iphonesimulator swiftc \
  -target arm64-apple-ios17.0-simulator -sdk "$SDK" -parse-as-library \
  "$TMP"/*.swift -o "$APP/MGLogic"

cat > "$APP/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>MGLogic</string>
  <key>CFBundleIdentifier</key><string>${BUNDLE_ID}</string>
  <key>CFBundleExecutable</key><string>MGLogic</string>
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
SIMCTL_CHILD_HS_MG_LOGIC="$SEED" xcrun simctl launch --terminate-running-process "$DEV" "$BUNDLE_ID" >/dev/null
sleep 5
xcrun simctl io "$DEV" screenshot "$OUT"
echo "shot: $OUT"

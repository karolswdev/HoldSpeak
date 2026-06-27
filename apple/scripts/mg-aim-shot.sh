#!/bin/bash
# HSM-14 — build the MG_Aim (Orbit Gate) mini-game harness for the iOS Simulator and screenshot it
# (portrait iPad). Mirrors scripts/arkanoid-shot.sh. The screenshot needs an ABSOLUTE path.
# Loop: edit App/MeetingCapture/DeskMiniGame_Aim.swift → ./scripts/mg-aim-shot.sh /tmp/x.png → Read it.
set -euo pipefail
cd "$(dirname "$0")/.."

DEV="${MGA_DEVICE:-iPad Air 11-inch (M4)}"
BUNDLE_ID="dev.holdspeak.mgaim"
SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
TMP="build/mg-aim-src"
APP="build/MGAim.app"
OUT="${1:-build/mg-aim-shot.png}"

rm -rf "$TMP" "$APP"; mkdir -p "$TMP" "$APP"
cp scripts/mg-aim/*.swift "$TMP/"
cp App/MeetingCapture/DeskMiniGame_Aim.swift "$TMP/"

xcrun --sdk iphonesimulator swiftc \
  -target arm64-apple-ios17.0-simulator -sdk "$SDK" -parse-as-library -DHS_MG_AIM_STANDALONE \
  "$TMP"/*.swift -o "$APP/MGAim"

cat > "$APP/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>MGAim</string>
  <key>CFBundleIdentifier</key><string>${BUNDLE_ID}</string>
  <key>CFBundleExecutable</key><string>MGAim</string>
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
# HS_MG_AIM=play stages a mid-run frame (comet in flight, gates sweeping) for the screenshot.
SIMCTL_CHILD_HS_MG_AIM="${HS_MG_AIM:-play}" xcrun simctl launch "$DEV" "$BUNDLE_ID" >/dev/null
sleep "${MGA_SLEEP:-2}"
xcrun simctl io "$DEV" screenshot "$OUT"
echo "shot: $OUT"

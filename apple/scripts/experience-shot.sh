#!/bin/bash
# HSM-14 — build the "Tactile Sheets" experience harness for the iOS Simulator and
# screenshot it. Compiles the SwiftUI sources directly (one module), bundles a .app,
# boots a simulator, installs, launches, and captures a PNG. No Xcode project, no device.
set -euo pipefail
cd "$(dirname "$0")/.."

DEV="${EXP_DEVICE:-iPhone 17 Pro Max}"
BUNDLE_ID="dev.holdspeak.experience"
SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
TMP="build/experience-src"
APP="build/Experience.app"
OUT="${1:-build/experience-shot.png}"

rm -rf "$TMP" "$APP"; mkdir -p "$TMP" "$APP"
cp scripts/experience/*.swift "$TMP/"

xcrun --sdk iphonesimulator swiftc \
  -target arm64-apple-ios17.0-simulator -sdk "$SDK" -parse-as-library \
  "$TMP"/*.swift -o "$APP/Experience"

cat > "$APP/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Experience</string>
  <key>CFBundleIdentifier</key><string>${BUNDLE_ID}</string>
  <key>CFBundleExecutable</key><string>Experience</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>CFBundleShortVersionString</key><string>0.1.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>LSRequiresIPhoneOS</key><true/>
  <key>MinimumOSVersion</key><string>17.0</string>
  <key>UILaunchScreen</key><dict/>
  <key>CFBundleSupportedPlatforms</key><array><string>iPhoneSimulator</string></array>
  <key>UIDeviceFamily</key><array><integer>1</integer><integer>2</integer></array>
</dict></plist>
PLIST

xcrun simctl boot "$DEV" 2>/dev/null || true
xcrun simctl bootstatus "$DEV" -b >/dev/null
xcrun simctl install "$DEV" "$APP"
xcrun simctl launch "$DEV" "$BUNDLE_ID" >/dev/null
sleep 6
xcrun simctl io "$DEV" screenshot "$OUT"
echo "shot: $OUT"

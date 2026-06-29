#!/bin/bash
# Repro harness for the desk overlap + empty-zone bugs: build the REAL meeting-capture app for the
# iOS Simulator and screenshot a FULL desk on iPhone (lane) and iPad (diorama).
set -euo pipefail
cd "$(dirname "$0")/.."

ruby scripts/gen-meeting-capture.rb
DD="$PWD/build/sim-dd"
scripts/patch-llm-macro.sh "$DD" build/HoldSpeakMeetingCapture.xcodeproj HoldSpeakMobile
xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile \
  -configuration Debug \
  -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  -skipMacroValidation \
  -disableAutomaticPackageResolution \
  -derivedDataPath "$DD" \
  build

APP="$DD/Build/Products/Debug-iphonesimulator/HoldSpeakMobile.app"
BUNDLE="dev.holdspeak.mobile"
# simctl io screenshot needs an ABSOLUTE path (it errors on a relative one).
OUTDIR="$(cd "${1:-build}" && pwd)"

shoot() {
  local dev="$1" tag="$2"
  xcrun simctl boot "$dev" 2>/dev/null || true
  xcrun simctl bootstatus "$dev" -b >/dev/null
  xcrun simctl uninstall "$dev" "$BUNDLE" 2>/dev/null || true
  xcrun simctl install "$dev" "$APP"
  SIMCTL_CHILD_HS_DESK_PARITY=1 SIMCTL_CHILD_HS_DESK_ZONE=directory SIMCTL_CHILD_HS_DESK_AGENTS=2 \
    xcrun simctl launch "$dev" "$BUNDLE" >/dev/null
  sleep 7
  xcrun simctl io "$dev" screenshot "$OUTDIR/desk-$tag.png"
  echo "shot: $OUTDIR/desk-$tag.png"
}

shoot "iPhone 17 Pro" "iphone"
shoot "iPad Air 13-inch (M4)" "ipad"

#!/bin/bash
# HSM-1-04 / Gate 1: build the minimal runtime shell and launch it on an iPhone
# and an iPad simulator (the charter's Tier-2 + Tier-1 targets). The app is
# compiled together with the Contracts sources, so a successful launch exercises
# the real contract layer. Usage: apple/scripts/gate1-launch.sh
set -euo pipefail
cd "$(dirname "$0")/.."

IPHONE="iPhone 17 Pro Max"
IPAD="iPad Pro 13-inch (M5)"
BUNDLE_ID="dev.holdspeak.mobile"
APP="build/HoldSpeakMobile.app"
SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"

echo "== compiling shell + Contracts for the iOS simulator =="
rm -rf "$APP"; mkdir -p "$APP"
xcrun --sdk iphonesimulator swiftc \
    -target arm64-apple-ios17.0-simulator \
    -sdk "$SDK" \
    -parse-as-library \
    Sources/Contracts/*.swift App/HoldSpeakApp.swift \
    -o "$APP/HoldSpeakMobile"
cp App/Info.plist "$APP/Info.plist"
echo "built $APP"

mkdir -p "$PWD/build"
launch_on() {
    local dev="$1"
    echo "== $dev =="
    xcrun simctl boot "$dev" 2>/dev/null || true
    xcrun simctl bootstatus "$dev" -b
    xcrun simctl install "$dev" "$APP"
    xcrun simctl launch "$dev" "$BUNDLE_ID"
    sleep 3
    local shot="$PWD/build/launch-$(echo "$dev" | tr ' ()' '___').png"
    xcrun simctl io "$dev" screenshot "$shot" 2>/dev/null && echo "screenshot: $shot" \
        || echo "(screenshot skipped for $dev)"
}

launch_on "$IPHONE"
launch_on "$IPAD"
echo "== Gate 1: launched on iPhone + iPad =="

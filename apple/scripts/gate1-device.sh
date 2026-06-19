#!/bin/bash
# HSM Gate 1 (real metal): build + sign the Phase-1 runtime shell for a *physical*
# device and launch it via devicectl, capturing a screenshot as proof. This is the
# on-device counterpart to gate1-launch.sh (which targets simulators only).
#
# Prereqs (one-time): Xcode > Settings > Accounts > sign in with the Apple ID that
# owns the HXY77XFPS4 team, so automatic provisioning can mint a profile + register
# the device. Then plug in the iPad/iPhone and trust this Mac.
#
# Usage: apple/scripts/gate1-device.sh [device-udid]
#   device-udid: hardware UDID from `xcrun devicectl list devices`; defaults to the
#   first available paired device.
set -euo pipefail
cd "$(dirname "$0")/.."

ruby scripts/gen-device-project.rb

DEVID="${1:-}"
if [ -z "$DEVID" ]; then
  # Prefer a connected iPad; the Identifier is the UUID-shaped token on its row.
  # Guard greps with `|| true` so an empty match doesn't trip `set -e`.
  UUID_RE='[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
  LIST="$(xcrun devicectl list devices 2>/dev/null || true)"
  DEVID="$(printf '%s\n' "$LIST" | grep -i 'iPad' | grep -oE "$UUID_RE" | head -1 || true)"
  [ -z "$DEVID" ] && DEVID="$(printf '%s\n' "$LIST" | grep -iE 'iPad|iPhone' | grep -oE "$UUID_RE" | head -1 || true)"
fi
echo "== target device: ${DEVID:-<none found>} =="

# Hardware UDID (distinct from the coredevice UUID): xcodebuild's -destination
# wants this, and targeting the device explicitly makes -allowProvisioningUpdates
# register its UDID into the development profile (else install fails 0xe8008012).
HWUDID="$(xcrun devicectl device info details --device "$DEVID" 2>/dev/null | awk -F': ' '/ udid:/{print $2; exit}' | tr -d ' ')"
# Clear the cached wildcard team profile so automatic signing regenerates one
# that includes this device (a stale cache can omit a newly-targeted device).
rm -f ~/Library/MobileDevice/Provisioning\ Profiles/*.mobileprovision 2>/dev/null || true
echo "== build + sign (destination id=$HWUDID) =="
# Destination-only (no -sdk): a concrete connected device makes automatic signing
# register its UDID into the development profile.
xcodebuild -project build/HoldSpeakMobile.xcodeproj -scheme HoldSpeakMobile \
  -configuration Debug \
  -destination "platform=iOS,id=$HWUDID" \
  -allowProvisioningUpdates \
  CONFIGURATION_BUILD_DIR="$PWD/build/device" \
  build

APP="$PWD/build/device/HoldSpeakMobile.app"
echo "== install $APP =="
xcrun devicectl device install app --device "$DEVID" "$APP"

echo "== launch =="
xcrun devicectl device process launch --device "$DEVID" dev.holdspeak.mobile

echo "== Gate 1 (device): launched dev.holdspeak.mobile on $DEVID =="
echo "(screenshot the iPad to attach as the real-metal proof)"

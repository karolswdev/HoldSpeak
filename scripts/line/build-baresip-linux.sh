#!/usr/bin/env bash
# Build baresip and libre for the Line on Linux, in user space (LINE design §9).
#
# Ubuntu 24.04 ships baresip 1.0.0 (2020); the Line needs 4.12.0. This script
# fetches the two pinned source tarballs, checks their SHA-256, and installs
# into a prefix you own. No sudo, no apt, no system file.
#
# Licences: baresip and libre are BSD-3-Clause. The modules list below is the
# whole list we build: every one is BSD-3 and links only BSD/Apache libraries
# (OpenSSL 3, libopus, zlib). gzrtp (GNU ZRTP) and any GPL module are never
# built.
#
#   scripts/line/build-baresip-linux.sh [PREFIX]   (default ~/holdspeak-line/opt)
#
# Needs: cc, cmake, make, and the headers of openssl, opus and zlib
# (libssl-dev, libopus-dev, zlib1g-dev). If one is missing the script stops
# and names it; installing it is the owner's one sudo press.
set -euo pipefail

BARESIP_VERSION="4.12.0"
LIBRE_VERSION="4.12.0"
BARESIP_SHA256="710d79d60c15c09f0aeb93e5d2f219e7f12ab93f62cab826e4280592a1ea155f"
LIBRE_SHA256="707b6194dd3b8d3fb1641ca08a0999aaac1d38d36b5c45514777a13ded311923"
BARESIP_URL="https://github.com/baresip/baresip/archive/refs/tags/v${BARESIP_VERSION}.tar.gz"
LIBRE_URL="https://github.com/baresip/re/archive/refs/tags/v${LIBRE_VERSION}.tar.gz"
MODULES="g711;l16;opus;auresamp;account;menu;ctrl_tcp;stun;ice;turn;srtp"

PREFIX="${1:-${HOLDSPEAK_LINE_PREFIX:-$HOME/holdspeak-line/opt}}"
WORK="${HOLDSPEAK_LINE_SRC:-$(dirname "$PREFIX")/src}"

if [ "$(id -u)" = "0" ]; then
  echo "Do not run this as root: the Line builds in user space." >&2
  exit 2
fi
missing=""
for tool in cc cmake make; do
  command -v "$tool" >/dev/null 2>&1 || missing="$missing $tool"
done
for header in openssl/ssl.h opus/opus.h zlib.h; do
  [ -f "/usr/include/$header" ] || missing="$missing $header"
done
if [ -n "$missing" ]; then
  echo "Missing:$missing. Install them (one sudo press), then run this again." >&2
  exit 3
fi

fetch() { # url sha256 file
  if [ ! -f "$3" ]; then
    curl -fsSL "$1" -o "$3.part" && mv "$3.part" "$3"
  fi
  echo "$2  $3" | sha256sum -c - >/dev/null || { echo "Checksum mismatch: $3" >&2; exit 4; }
}

mkdir -p "$WORK" "$PREFIX"
cd "$WORK"
fetch "$LIBRE_URL" "$LIBRE_SHA256" "re-${LIBRE_VERSION}.tar.gz"
fetch "$BARESIP_URL" "$BARESIP_SHA256" "baresip-${BARESIP_VERSION}.tar.gz"
tar xzf "re-${LIBRE_VERSION}.tar.gz"
tar xzf "baresip-${BARESIP_VERSION}.tar.gz"

jobs="$(nproc 2>/dev/null || echo 4)"
cmake -S "re-${LIBRE_VERSION}" -B build-re -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" -DUSE_OPENSSL=ON -DUSE_MBEDTLS=OFF >/dev/null
cmake --build build-re -j "$jobs" >/dev/null
cmake --install build-re >/dev/null

cmake -S "baresip-${BARESIP_VERSION}" -B build-bs -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" -DCMAKE_PREFIX_PATH="$PREFIX" \
  -DCMAKE_INSTALL_RPATH="$PREFIX/lib" -DMODULES="$MODULES" >/dev/null
cmake --build build-bs -j "$jobs" >/dev/null
cmake --install build-bs >/dev/null

echo "baresip ${BARESIP_VERSION} is in $PREFIX/bin/baresip (modules: ${MODULES//;/, })"

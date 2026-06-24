#!/usr/bin/env bash
# Thin wrapper: render dogfood audio fixtures using the repo venv's Python
# (so PyYAML is available). All args are forwarded to make_fixtures.py.
#   dogfood/make_fixtures.sh --list
#   dogfood/make_fixtures.sh --dry-run
#   dogfood/make_fixtures.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
PY="$REPO/.venv/bin/python"
[[ -x "$PY" ]] || PY="python3"
exec "$PY" "$HERE/make_fixtures.py" "$@"

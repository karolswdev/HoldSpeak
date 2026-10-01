#!/bin/bash
set -uo pipefail
phase_home=$(mktemp -d)
trap 'python3 -c "import shutil,sys; shutil.rmtree(sys.argv[1])" "$phase_home"' EXIT
mkdir -p "$phase_home/tmp"
env HOME="$phase_home" TMPDIR="$phase_home/tmp" PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --python 3.13 pytest -q --basetemp "$phase_home/pytest" tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 2>&1 | tee .tmp/philo-12-01/speak-confirm.log
exit "${PIPESTATUS[0]}"

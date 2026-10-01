#!/bin/bash
set -uo pipefail
phase_home=$(mktemp -d)
trap 'python3 -c "import shutil,sys; shutil.rmtree(sys.argv[1])" "$phase_home"' EXIT
printf 'Python: '
.venv/bin/python --version
printf 'Isolated HOME and basetemp: %s\n' "$phase_home"
env HOME="$phase_home" PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run --python 3.13 pytest -q -n auto --ignore=tests/e2e/test_metal.py --basetemp "$phase_home/pytest" 2>&1 | tee .tmp/philo-12-01/full-suite.log
exit "${PIPESTATUS[0]}"

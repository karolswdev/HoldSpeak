#!/usr/bin/env bash
# PHILO-11-06 part 2 full suite: Python 3.13, isolated HOME and basetemp.
set -euo pipefail

task_real_home="$HOME"
task_test_home=$(mktemp -d "${TMPDIR:-/tmp}/philo11-full-suite.XXXXXX")
cleanup_test_home() {
  /usr/bin/python3 -c 'import shutil, sys; shutil.rmtree(sys.argv[1], ignore_errors=True)' "$task_test_home"
}
trap cleanup_test_home EXIT
mkdir -p "$task_test_home/tmp" "$task_test_home/basetemp"

export PATH="/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$task_real_home/Library/Caches/ms-playwright}"
export npm_config_cache="$task_test_home/npm-cache"
export TMPDIR="$task_test_home/tmp"

printf 'Isolated HOME: %s\nBasetemp: %s\n' "$task_test_home" "$task_test_home/basetemp"
HOME="$task_test_home" uv run --python 3.13 --extra test --extra dev pytest \
  -q -n auto --basetemp="$task_test_home/basetemp" \
  --ignore=tests/e2e/test_metal.py

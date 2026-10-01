#!/usr/bin/env bash
# Run from the worktree root. First argument is the retained log path;
# remaining arguments go to pytest. Keep the real result and complete log.
set -u

task_log=${1:?Usage: verify_tests.sh LOG PYTEST_ARGS...}
shift
task_original_home="$HOME"
task_home=$(mktemp -d "${TMPDIR:-/tmp}/philo11-atlas-tests.XXXXXX")
mkdir -p "$task_home/tmp" "$(dirname "$task_log")"

export PATH="/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$task_original_home/Library/Caches/ms-playwright}"
export npm_config_cache="${npm_config_cache:-$task_original_home/.npm}"
export TMPDIR="$task_home/tmp"

printf 'Isolated HOME: %s\nBasetemp: %s/pytest\n' "$task_home" "$task_home"
HOME="$task_home" uv run --python 3.13 --extra test --extra dev pytest \
  --basetemp "$task_home/pytest" "$@" > "$task_log" 2>&1
task_rc=$?
tail -100 "$task_log"
printf '\nComplete pytest log: %s\nExit code: %s\n' "$task_log" "$task_rc"
exit "$task_rc"

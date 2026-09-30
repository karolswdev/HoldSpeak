#!/usr/bin/env bash
# PHILO-11-02 verification: every process uses a disposable HOME and TMPDIR.
set -u

task_real_home="$HOME"
task_home=$(mktemp -d "${TMPDIR:-/tmp}/philo11-slack.XXXXXX")
trap 'rm -rf "$task_home"' EXIT
mkdir -p "$task_home/tmp"

export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$task_real_home/Library/Caches/ms-playwright}"
export npm_config_cache="${npm_config_cache:-$task_real_home/.npm}"
export TMPDIR="$task_home/tmp"

mode=${1:?Use pytest, walk, or run followed by arguments}
shift
case "$mode" in
  pytest)
    env HOME="$task_home" uv run --python 3.13 --extra test --extra dev pytest \
      --basetemp "$task_home/pytest" "$@"
    ;;
  walk)
    env HOME="$task_home" uv run --python 3.13 --extra dev python scripts/graph_walk.py run "$@"
    ;;
  run)
    env HOME="$task_home" "$@"
    ;;
  *)
    printf 'Unknown verification mode: %s\n' "$mode" >&2
    exit 2
    ;;
esac

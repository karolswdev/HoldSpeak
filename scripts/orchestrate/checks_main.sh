#!/usr/bin/env bash
# checks_main.sh <base-sha>
# The checks on main after a merge batch, ONCE: quick check against the last green head, the main
# check, then the whole non-browser suite. Pull main first; never pull or branch there while it runs.
# Last line: RESULT quick=<rc> main=<rc> suite=<rc>. After a red fix: scripts/quick_check.sh --retry.
. "$(dirname "$0")/_env.sh"
cd "$ROOT" || exit 2
echo "HEAD $(git rev-parse --short HEAD) base $1"
scripts/quick_check.sh "$1" 2>&1 | tail -25; QC=${PIPESTATUS[0]}
scripts/main_check.sh 2>&1 | tail -8; MC=${PIPESTATUS[0]}
bash "$(dirname "$0")/suite_main.sh" 2>&1 | tail -15; SU=${PIPESTATUS[0]}
echo "RESULT quick=$QC main=$MC suite=$SU"

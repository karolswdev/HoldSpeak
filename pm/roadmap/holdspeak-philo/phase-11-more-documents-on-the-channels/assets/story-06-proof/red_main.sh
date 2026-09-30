#!/bin/zsh
# PHILO-11-06: run the actual Phase 11 atlas against the pre-Phase-11 source.
# The Phase 7–10 regression atlases run on the phase head; the pre-Phase-11
# source predates their current document_ref wire and is not a valid baseline
# for that regression batch.  The product is a git archive under
# .tmp; only this branch's graph rig, named atlases and philo11 fixtures are
# overlaid.  The runner marks the archive source revision explicitly because
# git otherwise resolves the enclosing worktree's .git directory.
#
# Usage: BASE=332d9158 red_main.sh <label> [--case ID ...]
# The default label is red-<BASE>.  Additional arguments are passed through to
# rig_run.py after the label; atlas paths stay fixed below.
set -euo pipefail

HERE=${0:A:h}
WT=${HERE}/../../../../../..
WT=${WT:A}
BASE=${BASE:-332d9158}
REV=$(cd "$WT" && git rev-parse "$BASE")
ARCHIVE=$WT/.tmp/philo11-06/base-$REV
if [[ -e $ARCHIVE && ! -d $ARCHIVE ]]; then
  print -u2 "archive path exists and is not a directory: $ARCHIVE"
  exit 2
fi
if [[ ! -d $ARCHIVE/web ]]; then
  mkdir -p "$ARCHIVE"
  (cd "$WT" && git archive "$REV" | tar -x -C "$ARCHIVE")
  print -r -- "$REV" > "$ARCHIVE/.philo11-source-revision"
elif [[ "$(<"$ARCHIVE/.philo11-source-revision")" != "$REV" ]]; then
  print -u2 "archive marker does not match requested revision: $ARCHIVE"
  exit 2
fi

# Overlay only the instrument, the named atlas inputs and their recording
# fixtures.  Product source remains the archived base, so a red result is a
# real absence/regression in the base rather than current code in disguise.
mkdir -p "$ARCHIVE/scripts" "$ARCHIVE/docs/internal/philo/graph"
cp "$WT/scripts/graph_walk.py" "$ARCHIVE/scripts/graph_walk.py"
ATLAS_FILES=(
  docs/internal/philo/graph/atlas-phase11-slack.json
  docs/internal/philo/graph/atlas-phase11.json
)
for atlas in $ATLAS_FILES; do
  [[ -f "$WT/$atlas" ]] && cp "$WT/$atlas" "$ARCHIVE/$atlas"
done
for fixture_dir in "$WT"/tests/fixtures/philo11_*; do
  [[ -d "$fixture_dir" ]] || continue
  mkdir -p "$ARCHIVE/tests/fixtures"
  cp -R "$fixture_dir" "$ARCHIVE/tests/fixtures/"
done

label=${1:-red-$REV}; shift || true
OUT=$WT/.tmp/philo11-06
PYTHON=${PYTHON:-$WT/.venv/bin/python}
if [[ ! -x $PYTHON ]]; then
  print -u2 "Python 3.13 toolchain not found: $PYTHON"
  exit 2
fi

exec "$PYTHON" "$HERE/rig_run.py" "$label" \
  --root "$ARCHIVE" \
  --out "$OUT" \
  --brain astra \
  --source-revision "$REV" \
  --source-dirty true \
  "$@" \
  $ATLAS_FILES

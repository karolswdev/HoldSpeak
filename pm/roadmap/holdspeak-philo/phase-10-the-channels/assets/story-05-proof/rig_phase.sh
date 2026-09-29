#!/bin/zsh
# PHILO-10-05: build the bundle, run every case of the named atlas files through
# the rig (rig_run.py: one hub, one mkdtemp HOME, one run directory per
# case x width x run), then keep every run with retain.py under
# assets/story-05-shots/<label>/ (OBS_ONLY=1: each run's observation only).
# ROOT=<export dir>: run the product of a `git archive` export (its own web
# build, PYTHONPATH); this branch's rig and the named atlas files are copied in.
# Exit: the rig's status, or retain's when the rig passed (never a pipe's).
# Usage: [OBS_ONLY=1] [ROOT=<export> [KEEP_RIG=1]] rig_phase.sh <label> <jobs> <atlas.json> ...
cd ${0:A:h}/../../../../../..
HERE=pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof
label=$1; jobs=$2; shift 2
echo "HEAD = $(git rev-parse HEAD); load $(sysctl -n vm.loadavg)"
if [[ -n $ROOT ]]; then
  echo "product: the export at $ROOT"
  (cd $ROOT/web && npm run build 2>&1 | tail -1)
  # KEEP_RIG=1: the export's OWN rig (a "before" run of the rig change).
  [[ -z $KEEP_RIG ]] && cp scripts/graph_walk.py $ROOT/scripts/
  mkdir -p $ROOT/tests/fixtures/philo10_atlas && cp tests/fixtures/philo10_atlas/*.json $ROOT/tests/fixtures/philo10_atlas/
  for f in "$@"; do [[ $f == *.json ]] && cp $f $ROOT/$f; done
else
  (cd web && npm run build 2>&1 | tail -1)
fi
H=$(mktemp -d); trap 'rm -rf "$H"' EXIT INT TERM
HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm \
  .venv/bin/python $HERE/rig_run.py $label --jobs $jobs ${ROOT:+--root} ${ROOT:+$ROOT} "$@" | cut -c1-240
rc=${pipestatus[1]}
.venv/bin/python $HERE/retain.py .tmp/p10s05/$label pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-shots/$label ${OBS_ONLY:+--obs-only}
kc=$?
echo "rig exit $rc; retain exit $kc"
(( rc != 0 )) && exit $rc
exit $kc

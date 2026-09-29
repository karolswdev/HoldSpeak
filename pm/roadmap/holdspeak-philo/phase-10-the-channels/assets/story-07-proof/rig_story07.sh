#!/bin/zsh
# PHILO-10-07 round two: build the bundle, walk atlas-phase10.json through the rig
# (story 05's rig_run.py: one hub, one mkdtemp HOME, one run directory per case x
# width), keep every run with story 05's retain.py under assets/story-07-shots/<label>/.
# Usage: rig_story07.sh <label> [--obs-only] [--case ID ...]
cd ${0:A:h}/../../../../../..
P5=pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof
label=$1; shift
obs=""; [[ $1 == --obs-only ]] && { obs=--obs-only; shift; }
echo "HEAD = $(git rev-parse HEAD) (+ working tree); load $(sysctl -n vm.loadavg)"
(cd web && npm run build 2>&1 | tail -1; exit ${pipestatus[1]}) || { echo "BUILD FAILED: no walk, no retention"; exit 3; }
H=$(mktemp -d); trap 'rm -rf "$H"' EXIT INT TERM
HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm \
  .venv/bin/python $P5/rig_run.py $label --jobs 4 --out .tmp/p10s07 "$@" docs/internal/philo/graph/atlas-phase10.json | cut -c1-240
rc=${pipestatus[1]}
.venv/bin/python $P5/retain.py .tmp/p10s07/$label pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-07-shots/$label $obs
kc=$?
echo "rig exit $rc; retain exit $kc"
(( rc != 0 )) && exit $rc
exit $kc

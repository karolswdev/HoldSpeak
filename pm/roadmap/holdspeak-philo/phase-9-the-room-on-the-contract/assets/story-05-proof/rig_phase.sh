#!/bin/zsh
# PHILO-9-05: build the bundle, run every case of the named atlas files through
# the rig (rig_run.py), retain runs.tsv and each run's observation.json under
# assets/story-05-shots/<label>/ (shots too when SHOTS=1).
# Usage: rig_phase.sh <label> <jobs> <atlas.json> ...
cd ${0:A:h}/../../../../../..
label=$1; jobs=$2; shift 2
echo "HEAD = $(git rev-parse HEAD); load $(sysctl -n vm.loadavg)"
(cd web && npm run build 2>&1 | tail -1)
HOME_REAL=$HOME
PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright HOME=$(mktemp -d) .venv/bin/python \
  pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_run.py $label --jobs $jobs "$@" | cut -c1-240
rc=${pipestatus[1]}
dest=pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-shots/$label
rm -rf $dest; mkdir -p $dest
cp .tmp/s05/$label/runs.tsv $dest/
for run in .tmp/s05/$label/*/; do
  mkdir -p $dest/${run:h:t}
  if [[ -n $SHOTS ]]; then cp $run* $dest/${run:h:t}/; else cp $run/observation.json $dest/${run:h:t}/; fi
done
exit $rc

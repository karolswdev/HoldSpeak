#!/bin/zsh
# PHILO-9-05: build the bundle, run every case of the named atlas files through
# the rig (rig_run.py), retain runs.tsv and each run's observation.json under
# assets/story-05-shots/<label>/<case>--<width>/<run id>/ with its shots (OBS_ONLY=1: the observation only).
# Usage: [OBS_ONLY=1] [ROOT=<export>] rig_phase.sh <label> <jobs> <atlas.json> ...
cd ${0:A:h}/../../../../../..
label=$1; jobs=$2; shift 2
echo "HEAD = $(git rev-parse HEAD); load $(sysctl -n vm.loadavg)"
if [[ -n $ROOT ]]; then echo "product: the export at $ROOT"; (cd $ROOT/web && npm run build 2>&1 | tail -1); cp scripts/graph_walk.py $ROOT/scripts/; for f in "$@"; do cp $f $ROOT/$f; done
else (cd web && npm run build 2>&1 | tail -1); fi
HOME_REAL=$HOME
PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright HOME=$(mktemp -d) .venv/bin/python \
  pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_run.py $label --jobs $jobs ${ROOT:+--root} ${ROOT:+$ROOT} "$@" | cut -c1-240
rc=${pipestatus[1]}
dest=pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-shots/$label
rm -rf $dest; mkdir -p $dest
cp .tmp/s05/$label/runs.tsv $dest/
# Codex Astra r1 finding 1: copy each run's OWN directory (the runs.tsv
# run_dir column: <case>--<width>/<run id>), every file (observation.json and
# its shots), then count: one retained directory per row, or exit 1.
tail -n +2 .tmp/s05/$label/runs.tsv | cut -f8 | while read rd; do
  mkdir -p $dest/$rd
  # OBS_ONLY=1 (the base atlas: 194 runs, about 200 MB of shots): the
  # observation.json of every run; its shots stay in .tmp (named in evidence).
  if [[ -n $OBS_ONLY ]]; then cp .tmp/s05/$label/$rd/observation.json $dest/$rd/; else cp -R .tmp/s05/$label/$rd/. $dest/$rd/; fi
done
rows=$(( $(wc -l < $dest/runs.tsv) - 1 ))
kept=$(ls -d $dest/*/*/ 2>/dev/null | wc -l | tr -d ' ')
obs=$(ls $dest/*/*/observation.json 2>/dev/null | wc -l | tr -d ' ')
echo "retained: $rows rows, $kept run directories, $obs observations"
[[ $rows -eq $kept && $rows -eq $obs ]] || { echo "RETENTION MISMATCH"; exit 1; }
exit $rc

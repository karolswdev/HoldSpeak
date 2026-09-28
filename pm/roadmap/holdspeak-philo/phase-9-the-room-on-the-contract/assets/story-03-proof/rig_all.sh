#!/bin/zsh
# Run the four PHILO-9-03 atlas cases at 1440 and 393 through the rig (each run
# makes its own mkdtemp HOME). Usage: rig_all.sh <label>
cd ${0:A:h}/../../../../../..
label=$1
out=.tmp/graph-walk/philo9-03-$label
mkdir -p .tmp/graph-walk
for c in case.p9.room_items.late_row case.p9.update_list.head_updates case.p9.update.delivered_row case.p9.room_steward_verb.owned; do
  for vp in 1440 393; do
    PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright .venv/bin/python scripts/graph_walk.py run \
      --atlas docs/internal/philo/graph/atlas-phase9.json --case $c --brain muaddib --viewport $vp --no-build \
      --out $out > $out-$c-$vp.log 2>&1
    echo "$c $vp exit=$? $(grep -h -E '^VERDICT' $out-$c-$vp.log | head -1 | cut -c1-200)"
  done
done

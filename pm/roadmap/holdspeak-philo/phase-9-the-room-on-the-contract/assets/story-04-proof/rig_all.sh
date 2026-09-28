#!/bin/zsh
# Run the four PHILO-9-04 atlas cases at 1440 and 393 through the rig (isolated
# HOME per run: the rig makes its own mkdtemp HOME). Usage: rig_all.sh <label>
cd ${0:A:h}/../../../../../..
label=$1
out=.tmp/graph-walk/philo9-04-$label
for c in case.p9.list_status.shown case.p9.list_columns.in_view case.p9.list_sort.zone_pressed case.p9.list_row_menu.delete_in_view; do
  for vp in 1440 393; do
    uv run --extra test python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase9.json \
      --case $c --brain muaddib --viewport $vp --no-build --out $out > $out-$c-$vp.log 2>&1
    echo "$c $vp exit=$? $(grep -o '"verdict": "[a-z_]*"' $out-$c-$vp.log | tail -1) $(grep -i -m1 -E 'reason|because' $out-$c-$vp.log | cut -c1-200)"
  done
done

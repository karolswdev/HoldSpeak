#!/bin/zsh
# PHILO-9-05: the story 05 cases on main BEFORE stories 02, 03 and 07
# (1f332bc3 = main with stories 01 and 04). An export of that commit
# (git archive) with ITS OWN web bundle built from its own web source and its
# own product package (PYTHONPATH); the instrument is this branch's rig and
# atlas file, copied in. Each run: its own hub, mkdtemp HOME, --engine none.
# Usage: red_main.sh [case ...]   (default: the five story 05 cases)
HERE=${0:A:h}
WT=${HERE}/../../../../../..
WT=${WT:A}
BASE=${BASE:-1f332bc3}
MAIN=$WT/.tmp/main-$BASE
[ -d $MAIN/web ] || (mkdir -p $MAIN && cd $WT && git archive $BASE | tar -x -C $MAIN)
echo "base = $(cd $WT && git rev-parse $BASE)"
[ -e $MAIN/web/node_modules ] || ln -s $WT/web/node_modules $MAIN/web/node_modules
(cd $MAIN/web && npm run build 2>&1 | tail -1)
cp $WT/scripts/graph_walk.py $MAIN/scripts/graph_walk.py
cp $WT/docs/internal/philo/graph/atlas-phase9.json $MAIN/docs/internal/philo/graph/atlas-phase9.json
cases=("$@")
[ ${#cases} -eq 0 ] && cases=(case.p9.grant.project_allowed case.p9.grant_route.project_allowed case.p9.grant.desk_reads_desk case.p9.connections.never_checked_face case.p9.update.delivered_row.op)
OUT=$WT/.tmp/s05/red-$BASE
mkdir -p $OUT
cd $MAIN
for c in $cases; do
  if [[ $c == *.op || $c == case.p9.grant_route.* ]]; then widths=(op); else widths=(1440 393); fi
  for w in $widths; do
    if [[ $w == op ]]; then extra=(--viewport 1440 --headless); else extra=(--viewport $w); fi
    HOME=$(mktemp -d) PYTHONPATH=$MAIN PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
      $WT/.venv/bin/python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase9.json \
      --case $c --brain muaddib $extra --no-build --out $OUT > $OUT/$c-$w.log 2>&1
    echo "$c $w exit=$? $(grep -h -E '^VERDICT' $OUT/$c-$w.log | head -1) | $(grep -h -E '^NOTE: (predicate|BLOCKED)' $OUT/$c-$w.log | tail -1 | cut -c1-330)"
  done
done

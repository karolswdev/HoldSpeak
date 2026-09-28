#!/bin/zsh
# PHILO-9-07 red face on main: the glass fences against an export of main with
# ITS OWN built bundle (web/node_modules linked from the worktree; the fence
# builds main's web source). Isolated HOME.
HERE=${0:A:h}
WT=${HERE}/../../../../../..
WT=${WT:A}
MAIN=$WT/.tmp/main-face
[ -d $MAIN/web ] || (mkdir -p $MAIN && cd $WT && git archive origin/main | tar -x -C $MAIN)
echo "main = $(cd $WT && git rev-parse origin/main)"
[ -e $MAIN/web/node_modules ] || ln -s $WT/web/node_modules $MAIN/web/node_modules
cp $WT/tests/e2e/test_philo9_07_project_grant_glass.py $MAIN/tests/e2e/
cd $MAIN
HOME=$(mktemp -d) PYTHONPATH=$MAIN PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  npm_config_cache=/Users/karol/.npm $WT/.venv/bin/python -m pytest -p no:cacheprovider -q --tb=no \
  --junitxml=$MAIN/red.xml tests/e2e/test_philo9_07_project_grant_glass.py 2>&1 | tail -2
$WT/.venv/bin/python $HERE/junit_summary.py $MAIN/red.xml

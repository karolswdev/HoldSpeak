#!/bin/zsh
# PHILO-9-07 red on main: the fences run unchanged against an export of main
# (git archive origin/main -> .tmp/main-copy), the fence files and the test
# helpers they import copied in. Isolated HOME. A 404 for the new grant route
# is never counted as a red: the reds are the assertions BEFORE the grant.
HERE=${0:A:h}
WT=$HERE/../../../../../..
WT=${WT:A}
MAIN=$WT/.tmp/main-copy
rm -rf $MAIN && mkdir -p $MAIN && (cd $WT && git archive origin/main | tar -x -C $MAIN)
echo "main = $(cd $WT && git rev-parse origin/main)"
for f in tests/unit/test_philo9_project_grant.py tests/unit/test_philo9_project_grant_lifecycle.py \
         tests/unit/test_philo9_project_grant_restart.py tests/unit/test_philo9_steward_admission.py \
         tests/unit/test_philo9_b1_connections.py "$@"; do
  mkdir -p $MAIN/$(dirname $f); cp $WT/$f $MAIN/$f
done
cd $MAIN
HOME=$(mktemp -d) PYTHONPATH=$MAIN $WT/.venv/bin/python -m pytest -p no:cacheprovider -q -n 8 --tb=no \
  --junitxml=$MAIN/red.xml tests/unit/test_philo9_project_grant.py tests/unit/test_philo9_project_grant_lifecycle.py \
  tests/unit/test_philo9_project_grant_restart.py 2>&1 | tail -2
$WT/.venv/bin/python $HERE/junit_summary.py $MAIN/red.xml

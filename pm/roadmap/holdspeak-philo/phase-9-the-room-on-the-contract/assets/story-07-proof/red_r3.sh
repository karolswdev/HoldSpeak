#!/bin/zsh
# PHILO-9-07 round three red: the two Codex Astra r1 regressions against an
# export of the checked head 7a432a29 (its own bundle), fences copied in.
HERE=${0:A:h}
WT=${HERE}/../../../../../..
WT=${WT:A}
R=$WT/.tmp/r3-head
[ -d $R/web ] || (mkdir -p $R && cd $WT && git archive 7a432a29 | tar -x -C $R)
[ -e $R/web/node_modules ] || ln -s $WT/web/node_modules $R/web/node_modules
cp $WT/tests/unit/test_philo9_project_grant.py $R/tests/unit/
cp $WT/tests/e2e/test_philo9_07_project_grant_glass.py $R/tests/e2e/
cd $R
HOME=$(mktemp -d) PYTHONPATH=$R PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  npm_config_cache=/Users/karol/.npm $WT/.venv/bin/python -m pytest -p no:cacheprovider -q --tb=no --junitxml=$R/red.xml \
  "tests/unit/test_philo9_project_grant.py::test_an_agent_named_like_the_owner_cannot_stop_the_owners_run" \
  "tests/unit/test_philo9_project_grant.py::test_an_agent_named_like_the_scheduler_cannot_stop_the_schedulers_run" \
  tests/e2e/test_philo9_07_project_grant_glass.py::TestArchivedProjectGrant 2>&1 | tail -2
$WT/.venv/bin/python $HERE/junit_summary.py $R/red.xml

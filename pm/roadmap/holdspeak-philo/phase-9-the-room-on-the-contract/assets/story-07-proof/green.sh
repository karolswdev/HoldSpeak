#!/bin/zsh
# PHILO-9-07 green: this story's fences (collected, then run) and the scoped
# suites its seams touch (story 02's, Phase 7's grant, the kernel, the schema),
# parallel, isolated HOME. Never tests/e2e/test_metal.py; never the full suite.
cd ${0:A:h}/../../../../../..
PY=$PWD/.venv/bin/python
MINE=(tests/unit/test_philo9_project_grant.py tests/unit/test_philo9_project_grant_lifecycle.py
      tests/unit/test_philo9_project_grant_restart.py tests/unit/test_philo9_project_grant_face_rule.py)
HOME=$(mktemp -d) $PY -m pytest --collect-only -q -p no:cacheprovider $MINE | tail -1
HOME=$(mktemp -d) $PY -m pytest -q -n 8 -p no:cacheprovider -rf $MINE \
  tests/unit/test_philo9_steward_admission.py tests/unit/test_philo9_steward_lifecycle.py \
  tests/unit/test_philo9_steward_restart.py tests/unit/test_philo9_command_race.py tests/unit/test_philo9_mark_delivered.py \
  tests/unit/test_philo9_room_contract.py tests/unit/test_philo9_contract.py tests/unit/test_philo9_compat.py \
  tests/unit/test_philo7_grant_lifecycle.py tests/unit/test_philo7_grant_restart.py tests/unit/test_philo7_article_xi.py \
  tests/unit/test_philo7_round_two.py tests/unit/test_philo7_file_and_find.py tests/unit/test_philo7_compat.py \
  tests/unit/test_hs174_reach_wire.py tests/integration/test_hs174_runner_loopback.py tests/unit/test_kernel_broker.py \
  tests/unit/test_inference_kernel.py tests/unit/test_one_path_provenance.py tests/unit/test_workbench_runner_migration.py \
  tests/unit/test_sequence_workflow_runner_migration.py tests/integration/test_principal_separation.py \
  tests/integration/test_kernel_real_hub.py tests/unit/test_db.py tests/unit/test_steward_engine.py \
  tests/unit/test_steward_effects.py tests/integration/test_steward_routes.py tests/unit/test_docs_navigation.py \
  2>&1 | tail -4

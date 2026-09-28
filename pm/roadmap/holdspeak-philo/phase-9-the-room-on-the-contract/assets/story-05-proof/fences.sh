#!/bin/zsh
# PHILO-9-05: the atlas fences (the phase file, the general fences over every
# atlas file, the earlier phases' atlas fences), the mutations of the phase
# file, and the api/MCP equivalence fences stories 01, 02 and 07 shipped, on
# this branch (main 79fdee3c + story 05). Isolated HOME.
cd ${0:A:h}/../../../../../..
echo "HEAD = $(git rev-parse HEAD)"
HOME=$(mktemp -d) .venv/bin/python -m pytest -q -p no:cacheprovider -n 4 \
  tests/unit/test_philo9_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo9_04_atlas.py tests/unit/test_api_surface.py \
  tests/unit/test_philo8_atlas.py tests/unit/test_philo7_atlas.py \
  tests/unit/test_philo9_compat.py tests/unit/test_philo9_room_contract.py tests/unit/test_philo9_mark_delivered.py \
  tests/unit/test_philo9_delivery_record.py tests/unit/test_philo9_project_grant.py \
  tests/unit/test_philo9_steward_admission.py tests/unit/test_philo9_rig_op.py tests/unit/test_philo9_02_rig_op.py 2>&1 | tail -3
rc=${pipestatus[1]}
.venv/bin/python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/mutations.py | cut -c1-220
mrc=$?
exit $(( rc != 0 || mrc != 0 ))

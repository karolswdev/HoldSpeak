#!/bin/zsh
# PHILO-10-05: the atlas fences (the phase file, the general fences over every
# atlas file, the earlier phases' atlas fences), the OpenAPI surface check, the
# story 01-04 channel fences the atlas leans on, then the mutations of the phase
# file. Isolated HOME. Exit nonzero when EITHER half fails (each status read
# with ${pipestatus[1]}, never the pipe's last command).
cd ${0:A:h}/../../../../../..
echo "HEAD = $(git rev-parse HEAD)"
H=$(mktemp -d); trap 'rm -rf "$H"' EXIT INT TERM
HOME=$H .venv/bin/python -m pytest -q -p no:cacheprovider -n 4 --basetemp=$H/pt \
  tests/unit/test_philo10_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo9_atlas.py \
  tests/unit/test_philo9_04_atlas.py tests/unit/test_philo8_atlas.py tests/unit/test_philo7_atlas.py \
  tests/unit/test_api_surface.py tests/unit/test_philo10_rig_op.py tests/unit/test_philo9_rig_op.py \
  tests/unit/test_philo9_02_rig_op.py tests/unit/test_philo10_send_contract.py 2>&1 | tail -3
rc=${pipestatus[1]}
.venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof/mutations.py | cut -c1-220
mrc=${pipestatus[1]}
echo "fences exit $rc; mutations exit $mrc"
exit $(( rc != 0 || mrc != 0 ))

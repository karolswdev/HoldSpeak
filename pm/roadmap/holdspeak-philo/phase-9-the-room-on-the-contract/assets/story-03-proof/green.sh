#!/bin/zsh
# GREEN ON THE BRANCH: the bundle built, the story's glass at 1440 + 393 on an
# isolated HOME (shots and measurements written when HOLDSPEAK_EVIDENCE_WRITE=1),
# the backend Room fences, the atlas fences, then the four atlas cases through
# the rig at both widths.
cd ${0:A:h}/../../../../../..
echo "HEAD = $(git rev-parse HEAD); product diff vs the base aeae7bd8:"
git diff --stat aeae7bd8 -- web/src holdspeak | tail -1
(cd web && npm run build 2>&1 | tail -1)
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python -m pytest -q -p no:cacheprovider -n 8 -rA \
  tests/e2e/test_philo9_03_room_face_glass.py \
  tests/unit/test_philo9_mark_delivered.py tests/unit/test_philo9_room_contract.py tests/unit/test_hs174_reach_wire.py \
  tests/unit/test_philo9_steward_lifecycle.py \
  tests/unit/test_philo9_04_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo8_atlas.py \
  tests/unit/test_philo7_atlas.py tests/unit/test_philo4_01_atlas_contracts.py 2>&1 \
  | grep -E "^(FAILED|ERROR)|^PASSED tests/e2e|passed|failed" | cut -c1-300
rc=${pipestatus[1]}
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/rig_all.sh branch
fails=$(grep -L "VERDICT: pass" .tmp/graph-walk/philo9-03-branch-*.log | wc -l | tr -d ' ')
echo "rig cases not passing: $fails"
exit $(( rc != 0 || fails != 0 ))

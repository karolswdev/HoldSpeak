#!/bin/zsh
# GREEN ON THE BRANCH: the bundle built, the glass at 1440 + 393 on an isolated
# HOME (shots and measurements written when HOLDSPEAK_EVIDENCE_WRITE=1), the
# unit fences (structural + atlas + every-atlas), then the four atlas cases
# through the rig at both widths.
cd ${0:A:h}/../../../../../..
echo "HEAD = $(git rev-parse HEAD); product diff vs origin/main:"
git diff --stat origin/main -- web/src | tail -1
(cd web && npm run build 2>&1 | tail -1)
HOME_REAL=$HOME
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright UV_CACHE_DIR=$HOME_REAL/.cache/uv \
  uv run --extra test python -m pytest -q -p no:cacheprovider -n 4 -rA \
  tests/e2e/test_philo9_04_desk_debts_glass.py tests/unit/test_philo9_04_sort_button_fence.py \
  tests/unit/test_philo9_04_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo8_atlas.py \
  tests/unit/test_philo7_atlas.py tests/unit/test_philo4_01_atlas_contracts.py 2>&1 \
  | grep -E "^(FAILED|ERROR)|^PASSED tests/(e2e|unit/test_philo9)|passed|failed" | cut -c1-300
rc=${pipestatus[1]}
PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/rig_all.sh branch
grep -h -E "^(VERDICT|NOTE: predicate)" .tmp/graph-walk/philo9-04-branch-*.log | cut -c1-300
fails=$(grep -L "VERDICT: pass" .tmp/graph-walk/philo9-04-branch-*.log | wc -l)
echo "rig cases not passing: $fails"
exit $(( rc != 0 || fails != 0 ))

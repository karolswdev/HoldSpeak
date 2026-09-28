#!/bin/zsh
# ROUND TWO RED: the round-two fences (Codex Astra r1 findings 1 and 2) against
# the product at a given ref (default f58cb5b0, the revision Astra reviewed),
# then against origin/main. The branch files are put back and rebuilt at the end.
cd ${0:A:h}/../../../../../..
proof=pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof
HOME_REAL=$HOME
for ref in ${1:-f58cb5b0} origin/main; do
  echo "=== product at $ref ($(git rev-parse --short $ref))"
  $proof/swap.sh main $ref
  HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright UV_CACHE_DIR=$HOME_REAL/.cache/uv \
    uv run --extra test python -m pytest -q -p no:cacheprovider -n 3 -rA \
    tests/e2e/test_philo9_04_desk_debts_glass.py -k "editor or composer or launch" 2>&1 \
    | grep -E "^(FAILED|PASSED|ERROR)|^E   |passed|failed" | cut -c1-420
  $proof/swap.sh branch
done
git diff --stat origin/main -- web/src | tail -1

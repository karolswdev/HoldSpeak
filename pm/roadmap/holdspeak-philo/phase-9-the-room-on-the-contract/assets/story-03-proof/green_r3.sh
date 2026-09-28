#!/bin/zsh
# ROUND THREE GREEN: the receipt-scope census + the story glass (both widths)
# + the Room backend fences, on the branch; then the generated-docs checks.
cd ${0:A:h}/../../../../../..
(cd web && npm run build 2>&1 | tail -1)
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python -m pytest -q -p no:cacheprovider -n 8 tests/unit/test_philo9_03_receipt_scope.py \
  tests/e2e/test_philo9_03_room_face_glass.py tests/unit/test_philo9_room_contract.py tests/unit/test_philo9_mark_delivered.py \
  tests/unit/test_hs174_reach_wire.py tests/unit/test_philo_graph_atlas.py 2>&1 | grep -E "^(FAILED|ERROR)|passed|failed" | cut -c1-240
for s in philo_api_reference philo_boundary_census philo_graph_reference; do python3 scripts/$s.py --check >/dev/null 2>&1; echo "$s --check rc=$?"; done

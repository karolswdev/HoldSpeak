#!/bin/zsh
# The story's glass at 1440 + 393 on an isolated HOME (shots written when
# HOLDSPEAK_EVIDENCE_WRITE=1), after the bundle is built.
cd ${0:A:h}/../../../../../..
(cd web && npm run build 2>&1 | tail -1)
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python -m pytest -q -p no:cacheprovider -n 8 -rA tests/e2e/test_philo9_03_room_face_glass.py 2>&1 \
  | grep -E "^(FAILED|ERROR|PASSED)|passed|failed" | cut -c1-240

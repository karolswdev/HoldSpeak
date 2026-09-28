#!/bin/zsh
# ROUND THREE RED (Codex Astra r2 finding 3): the receipt reader as it was at
# the counselled head e77a5416 (any payload value equal to the id scoped a
# receipt), the receipts fence at 1440 + 393 through the real hub; then the
# branch file back.
cd ${0:A:h}/../../../../../..
f=holdspeak/services/project_service.py
mkdir -p .tmp/philo9-03/r3; cp $f .tmp/philo9-03/r3/project_service.py; git show e77a5416:$f > $f
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python -m pytest -q -p no:cacheprovider -n 2 -k rooms_work tests/e2e/test_philo9_03_room_face_glass.py 2>&1 \
  | grep -E "^(FAILED|PASSED)|^E   .*(Assert|assert)|passed|failed" | cut -c1-240
cp .tmp/philo9-03/r3/project_service.py $f
git diff --stat e77a5416 -- $f | tail -1

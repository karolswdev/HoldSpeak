#!/bin/zsh
# RED BEFORE THIS STORY: the base's product files in place (swap.sh base), the
# bundle built, the story's glass at 1440 + 393 on an isolated HOME; then the
# branch files put back and the bundle rebuilt, whatever the result.
cd ${0:A:h}/../../../../../..
echo "base = $(git rev-parse aeae7bd8) (main 1f332bc3 + PHILO-9-02)"
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/swap.sh base
git diff --stat aeae7bd8 -- web/src holdspeak/services/project_service.py | tail -1
echo "(an empty diffstat above = the base's product files are in place)"
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python -m pytest -q -p no:cacheprovider -n 8 -rf tests/e2e/test_philo9_03_room_face_glass.py 2>&1 \
  | grep -E "^(FAILED|PASSED)|^E   |passed|failed" | cut -c1-360
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/rig_all.sh base
grep -h -E "^NOTE" .tmp/graph-walk/philo9-03-base-*.log | cut -c1-220
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-proof/swap.sh branch
git diff --stat aeae7bd8 -- web/src | tail -1

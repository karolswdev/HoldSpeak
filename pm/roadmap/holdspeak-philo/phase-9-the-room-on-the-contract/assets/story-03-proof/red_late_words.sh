#!/bin/zsh
# RED BEFORE RULING 3: the face files as they were at PR #686's first head
# (5c7b8d06: the hub's words on the face), the bundle built, the late-words
# fence at 1440 + 393; then the branch files back and rebuilt.
cd ${0:A:h}/../../../../../..
save=.tmp/philo9-03/ruling3
files=(web/src/features/project-room/ProjectRoomCore.tsx web/src/features/project-room/model.ts)
for f in $files; do mkdir -p $save/${f:h}; cp $f $save/$f; git show 5c7b8d06:$f > $f; done
(cd web && npm run build 2>&1 | tail -1)
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python -m pytest -q -p no:cacheprovider -n 2 -k late_words tests/e2e/test_philo9_03_room_face_glass.py 2>&1 \
  | grep -E "^(FAILED|PASSED)|^E   |passed|failed" | cut -c1-240
for f in $files; do cp $save/$f $f; done
(cd web && npm run build 2>&1 | tail -1)
git diff --stat -- $files | tail -1

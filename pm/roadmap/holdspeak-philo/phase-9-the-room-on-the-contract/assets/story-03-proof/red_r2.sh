#!/bin/zsh
# ROUND TWO RED (Codex Astra r1 findings 1-3): the product files as they were
# at the counselled head 62375d84, the bundle built, the three new fences at
# 1440 + 393 through the real hub; then the branch files back and rebuilt.
cd ${0:A:h}/../../../../../..
save=.tmp/philo9-03/r2
ref=62375d84
files=(holdspeak/services/project_service.py web/src/desk/surface/egress.ts
  web/src/features/project-room/ProjectRoomCore.tsx web/src/features/project-room/model.ts
  web/src/features/project-room/review/api.ts web/src/features/project-room/review/useReviewController.ts
  web/src/features/project-room/review/ReviewPosture.tsx web/src/features/project-room/steward/StewardPosture.tsx
  web/src/features/project-room/update/UpdatePosture.tsx)
for f in $files; do mkdir -p $save/${f:h}; cp $f $save/$f; git show $ref:$f > $f; done
(cd web && npm run build 2>&1 | tail -1)
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python -m pytest -q -p no:cacheprovider -n 6 \
  -k "refused_delivery_receipt or review_on_a_completed or rooms_work" tests/e2e/test_philo9_03_room_face_glass.py 2>&1 \
  | grep -E "^(FAILED|PASSED)|^E   |passed|failed" | cut -c1-260
for f in $files; do cp $save/$f $f; done
(cd web && npm run build 2>&1 | tail -1)
git diff --stat -- $files | tail -1

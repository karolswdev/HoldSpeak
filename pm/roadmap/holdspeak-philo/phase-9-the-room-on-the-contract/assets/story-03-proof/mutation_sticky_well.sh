#!/bin/zsh
# MUTATION: the branch with the Ask well sticky again at a narrow window (the
# F10 repair removed) -- the F10 fence must turn red at 393; 1440 keeps
# Condition 7 and stays green. The branch rule is put back and rebuilt after.
cd ${0:A:h}/../../../../../..
f=web/src/features/project-room/project-room.css
cp $f .tmp/philo9-03-project-room.css
python3 - <<'PY'
import pathlib
p = pathlib.Path("web/src/features/project-room/project-room.css"); s = p.read_text()
s = s.replace("@container surface (max-width: 559px) {\n  .room-ask-container {\n    position: static;", "@container surface (max-width: 559px) {\n  .room-ask-container {\n    position: sticky;", 1)
p.write_text(s)
PY
grep -n -B1 -A2 "position: sticky;" $f
(cd web && npm run build 2>&1 | tail -1)
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  .venv/bin/python -m pytest -q -p no:cacheprovider -n 2 -k ask_well tests/e2e/test_philo9_03_room_face_glass.py 2>&1 \
  | grep -E "^(FAILED|PASSED)|^E   |passed|failed" | cut -c1-300
cp .tmp/philo9-03-project-room.css $f
(cd web && npm run build 2>&1 | tail -1)
git diff --stat -- $f | tail -1

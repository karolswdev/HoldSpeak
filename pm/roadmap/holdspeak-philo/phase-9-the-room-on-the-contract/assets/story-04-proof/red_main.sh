#!/bin/zsh
# RED ON MAIN: main's seven product web files in place (origin/main via
# `git show`, the branch copies saved), the bundle built, then the story's
# glass (1440 + 393, isolated HOME), the structural fence, and the four atlas
# cases through the rig at both widths. The branch files are put back and the
# bundle rebuilt at the end, whatever the result.
cd ${0:A:h}/../../../../../..
echo "origin/main = $(git rev-parse origin/main)"
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/swap.sh main
git diff --stat origin/main -- web/src/desk/components/DeskListView.tsx web/src/desk/components/DeskMenu.tsx web/src/desk/components/DeskSortableTable.tsx web/src/desk/components/chrome-menus.css web/src/desk/components/list-view.css web/src/styles/global.css web/src/styles/tokens.css
echo "(an empty diffstat above = main's product files are in place)"
HOME_REAL=$HOME
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright UV_CACHE_DIR=$HOME_REAL/.cache/uv \
  uv run --extra test python -m pytest -q -p no:cacheprovider -n 4 -rf \
  tests/e2e/test_philo9_04_desk_debts_glass.py tests/unit/test_philo9_04_sort_button_fence.py 2>&1 \
  | grep -E "^(FAILED|PASSED)|^E   |passed|failed" | cut -c1-420
PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/rig_all.sh main
grep -h -E "^(VERDICT|NOTE: predicate|EVIDENCE)" .tmp/graph-walk/philo9-04-main-*.log | cut -c1-300
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof/swap.sh branch
git diff --stat origin/main -- web/src | tail -1

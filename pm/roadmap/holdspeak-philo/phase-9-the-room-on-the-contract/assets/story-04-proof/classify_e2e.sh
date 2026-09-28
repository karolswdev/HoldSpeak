#!/bin/zsh
# Classify the three PHILO-8 one-delete E2E reds on PR #683's CI (run
# 36404923266, head 9dcb569d) that main's run 36369788814 did not list: each
# runs three times on main's product (origin/main's web files, swap.sh) and
# three times on the branch, isolated HOME. Same red on main = inherited;
# passes on both = flaky.
cd ${0:A:h}/../../../../../..
proof=pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-proof
HOME_REAL=$HOME
T=tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete
cases=("$T::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440]"
       "$T::test_leaving_the_face_inside_the_window_commits_the_delete[list-393]"
       "$T::test_the_list_palette_delete_removes_the_selected_object[1440]")
run() {
  for i in 1 2 3; do
    HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright UV_CACHE_DIR=$HOME_REAL/.cache/uv \
      uv run --extra test python -m pytest -q -p no:cacheprovider -n 3 -rA $cases 2>&1 \
      | grep -E "^(PASSED|FAILED|ERROR) " | sed -E "s/^/try $i: /" | cut -c1-200
  done
}
echo "=== main's product ($(git rev-parse --short origin/main))"
$proof/swap.sh main origin/main
run
$proof/swap.sh branch
echo "=== the branch ($(git rev-parse --short HEAD))"
run

#!/usr/bin/env bash
# The whole non-browser suite on origin/main, in its own worktree, through the lock, isolated HOME.
. "$(dirname "$0")/_env.sh"
WT="${HS_SUITE_WT:-$TREES/wt-suite-main}"
[ -d "$WT" ] || { echo "no suite worktree $WT: HOLDSPEAK_SKIP_WEB_BUILD=1 scripts/lane.sh new suite-main"; exit 2; }
cd "$WT" && git fetch -q origin && git checkout -q --detach origin/main || exit 3
export HOLDSPEAK_SKIP_WEB_BUILD=1
HS_REAL_HOME="$HOME"; HS_TEST_HOME="$(mktemp -d)"
export HOME="$HS_TEST_HOME" PLAYWRIGHT_BROWSERS_PATH="$HS_REAL_HOME/Library/Caches/ms-playwright" npm_config_cache="$HS_REAL_HOME/.npm"
echo "head $(git rev-parse --short HEAD) start $(date)"
uv run python scripts/test_lock.py -- uv run pytest -q -n 6 --dist worksteal -m "not slow" -p no:cacheprovider \
  tests/unit tests/integration tests/critical tests/web tests/mcp tests/uat 2>&1 | tail -60
RC=${PIPESTATUS[0]}
python3 -c "import shutil,sys; shutil.rmtree(sys.argv[1], ignore_errors=True)" "$HS_TEST_HOME"
echo "end $(date) rc $RC"; exit $RC

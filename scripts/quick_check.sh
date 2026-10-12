#!/usr/bin/env bash
# The pre-merge check (owner ruling 2026-10-12, "the fast cycle"): about 2-4 minutes.
#
#   scripts/quick_check.sh [base]        # base defaults to origin/main
#
# It runs, under the one-run-at-a-time lock and an isolated HOME:
#   1. the web build;
#   2. vitest on the tests RELATED to the changed web files (vitest related);
#   3. pytest -m "not slow" on the changed test files plus the unit and
#      integration files that import a changed holdspeak module;
#   4. the desk sweep (every app at 1440 and 393: fit, visible, console,
#      readable, contrast, 12 px, clipped, overlap, library Button, material,
#      still, egress) plus the canon guard and the ratchet.
# The whole suite does NOT run here: it runs on main after the merge
# (the orchestrator's main watcher), and a red there is fixed forward at once.
set -uo pipefail
base="${1:-origin/main}"
root="$(git rev-parse --show-toplevel)"; cd "$root"
git fetch -q origin 2>/dev/null || true
changed="$(git diff --name-only "$base"...HEAD; git diff --name-only; git diff --name-only --cached)"
changed="$(printf '%s\n' "$changed" | sort -u | grep -v '^$' || true)"
[ -z "$changed" ] && { echo "quick_check: no changes against $base"; exit 0; }
echo "quick_check: $(printf '%s\n' "$changed" | wc -l | tr -d ' ') changed files against $base"

HOME_REAL="$HOME"; H="$(mktemp -d)"; trap 'rm -rf "$H"' EXIT
export PLAYWRIGHT_BROWSERS_PATH="$HOME_REAL/Library/Caches/ms-playwright" npm_config_cache="$HOME_REAL/.npm"
lock() { uv run python scripts/test_lock.py -- "$@"; }
fail=0

echo "== build"; npm --prefix web run build >/dev/null 2>&1 || { echo "BUILD FAILED"; exit 1; }

web="$(printf '%s\n' "$changed" | grep -E '^web/src/.*\.(ts|tsx|css)$' | sed 's#^web/##' || true)"
if [ -n "$web" ]; then
  echo "== vitest related ($(printf '%s\n' "$web" | wc -l | tr -d ' ') files)"
  out="$(cd web && HOME="$H" uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest related --run $web 2>&1)"; rc=$?
  printf '%s\n' "$out" | grep -E '^ FAIL|×|Test Files|Tests ' | sort -u | sed 's/^/   /'
  # vitest exits 1 on jsdom's unhandled "not implemented" errors (canvas)
  # even when every test passes; judge by failed tests, as check_web_baseline does.
  if printf '%s\n' "$out" | grep -qE '^ FAIL|Tests .*[0-9]+ failed|Test Files .*[0-9]+ failed'; then fail=1
  elif ! printf '%s\n' "$out" | grep -qE 'Tests .*[0-9]+ passed'; then echo "   vitest did not report (rc=$rc)"; fail=1; fi
fi

py_tests="$(printf '%s\n' "$changed" | grep -E '^tests/(unit|integration|critical|web|mcp)/.*\.py$' || true)"
mods="$(printf '%s\n' "$changed" | grep -E '^holdspeak/.*\.py$' | sed -e 's#\.py$##' -e 's#/__init__$##' -e 's#/#.#g' || true)"
for m in $mods; do
  py_tests="$py_tests"$'\n'"$(grep -rlE "(from|import) $m\b" tests/unit tests/integration 2>/dev/null || true)"
done
py_tests="$(printf '%s\n' "$py_tests" | grep -v '^$' | sort -u | while read -r f; do [ -f "$f" ] && echo "$f"; done)"
if [ -n "$py_tests" ]; then
  n="$(printf '%s\n' "$py_tests" | wc -l | tr -d ' ')"
  echo "== pytest affected ($n files)"
  HOME="$H" lock uv run pytest -q -n 8 --dist worksteal -m "not slow" $py_tests 2>&1 | tail -3 | sed 's/^/   /'
  [ "${PIPESTATUS[0]}" = 0 ] || fail=1
fi

echo "== desk sweep + canon guards"
HOME="$H" lock uv run pytest -q -n 8 --dist worksteal tests/e2e/test_desk_sweep.py tests/unit/test_interior_canon_guard.py tests/unit/test_ux_canon_ratchet.py 2>&1 | grep -E '^(FAILED|ERROR)|passed|failed' | tail -12 | sed 's/^/   /'
[ "${PIPESTATUS[0]}" = 0 ] || fail=1

if [ "$fail" = 0 ]; then echo "QUICK CHECK GREEN: merge; the main watcher runs the whole suite."; else echo "QUICK CHECK RED: fix before merging."; fi
exit "$fail"

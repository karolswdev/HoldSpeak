#!/usr/bin/env bash
# The pre-merge check (owner ruling 2026-10-12, "the fast cycle"): about 2-4 minutes.
#
#   scripts/quick_check.sh [base]        # base defaults to origin/main
#   QUICK_TESTS="tests/x.py tests/y.py" scripts/quick_check.sh   # add test files
#
# It runs, under the one-run-at-a-time lock and an isolated HOME:
#   1. the web build;
#   2. vitest on the tests RELATED to the changed web files (vitest related);
#   3. pytest -m "not slow" on the affected test files
#      (scripts/quick_check_affected.py: changed test files, tests/uat and
#      tests/e2e included; tests that import a changed holdspeak module or
#      scripts/*.py; QUICK_TESTS);
#   4. the desk sweep (every app at 1440 and 393), which must PROVE it ran
#      (60 or more passed, never skipped), then the canon guard and the ratchet.
# The whole suite does NOT run here: it runs on main after the merge
# (the orchestrator's main watcher), and a red there is fixed forward at once.
#
# Fail closed (Astra's review of the first version): a change discovery that
# fails, a skipped sweep, or an unhandled vitest error that is not jsdom's
# canvas "Not implemented" is RED, never a quiet green.
set -uo pipefail
base="${1:-origin/main}"
root="$(git rev-parse --show-toplevel)" || { echo "QUICK CHECK RED: not in a git work tree"; exit 1; }
cd "$root"
SWEEP_MIN="${QUICK_SWEEP_MIN:-60}"
red() { echo "QUICK CHECK RED: $*"; exit 1; }

# ── 1. what changed (each git call is checked; an error is red) ──────────────
git fetch -q origin 2>/dev/null || echo "quick_check: fetch failed; using the local $base"
git rev-parse --verify --quiet "$base^{commit}" >/dev/null || red "base '$base' is not a commit"
d1="$(git diff --name-only "$base"...HEAD)" || red "git diff $base...HEAD failed"
d2="$(git diff --name-only)" || red "git diff (work tree) failed"
d3="$(git diff --name-only --cached)" || red "git diff --cached failed"
d4="$(git ls-files --others --exclude-standard)" || red "git ls-files failed"
changed="$(printf '%s\n%s\n%s\n%s\n' "$d1" "$d2" "$d3" "$d4" | grep -v '^$' | sort -u || true)"
[ -z "$changed" ] && { echo "quick_check: no changes against $base"; exit 0; }
echo "quick_check: $(printf '%s\n' "$changed" | wc -l | tr -d ' ') changed files against $base"

uncovered="$(printf '%s\n' "$changed" | grep -E '\.(ts|tsx|css)$' | grep -v '^web/src/' || true)"
if [ -n "$uncovered" ]; then
  echo "quick_check: NOT COVERED by the quick check (web files outside web/src; test them yourself):"
  printf '%s\n' "$uncovered" | sed 's/^/   /'
fi

HOME_REAL="$HOME"; H="$(mktemp -d)"; trap 'rm -rf "$H"' EXIT
export PLAYWRIGHT_BROWSERS_PATH="$HOME_REAL/Library/Caches/ms-playwright" npm_config_cache="$HOME_REAL/.npm"
lock() { HOME="$H" uv run python scripts/test_lock.py -- "$@"; }
fail=0

# ── 2. the build, under the lock and the isolated HOME (it never replaces the
#      bundle under a locked browser run) ───────────────────────────────────────
echo "== build"
lock npm --prefix web run build >"$H/build.log" 2>&1 || { tail -20 "$H/build.log"; red "the web build failed"; }

# ── 3. vitest related ────────────────────────────────────────────────────────
web="$(printf '%s\n' "$changed" | grep -E '^web/src/.*\.(ts|tsx|css)$' | sed 's#^web/##' || true)"
web="$(printf '%s\n' "$web" | while read -r f; do [ -n "$f" ] && [ -f "web/$f" ] && echo "$f"; done)"
if [ -n "$web" ]; then
  echo "== vitest related ($(printf '%s\n' "$web" | wc -l | tr -d ' ') files)"
  out="$(cd web && HOME="$H" uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest related --run $web 2>&1)"; rc=$?
  printf '%s\n' "$out" | grep -E '^ FAIL|×|Test Files|Tests |Errors ' | sort -u | sed 's/^/   /'
  # The unhandled-error blocks: each starts with "⎯ Unhandled Error ⎯" or
  # "⎯ Unhandled Rejection ⎯"; its first line is the error.
  read -r unhandled canvas < <(printf '%s\n' "$out" | awk '
    /Unhandled (Error|Rejection) ⎯/ { grab = 1; total++; next }
    grab && NF { grab = 0; if ($0 ~ /Not implemented: HTMLCanvasElement\.prototype\.getContext/) canvas++ }
    END { print total + 0, canvas + 0 }')
  if printf '%s\n' "$out" | grep -qE '^ FAIL|Tests .*[0-9]+ failed|Test Files .*[0-9]+ failed'; then
    echo "   vitest failed: RED"; fail=1
  elif ! printf '%s\n' "$out" | grep -qE 'Tests .*[0-9]+ passed'; then
    echo "   vitest did not report its tests (rc=$rc)"; fail=1
  elif [ "$rc" != 0 ]; then
    # The ONE tolerated exit: every unhandled error is jsdom's canvas
    # "Not implemented" (no canvas package in the test environment).
    if [ "$unhandled" -gt 0 ] && [ "$unhandled" = "$canvas" ]; then
      echo "   vitest rc=$rc: $canvas unhandled jsdom canvas error(s) only (tolerated)"
    else
      echo "   vitest rc=$rc: $unhandled unhandled error(s), $canvas of them canvas: RED"
      printf '%s\n' "$out" | awk '/Unhandled (Error|Rejection) ⎯/ { grab = 1; next } grab && NF { print "   > " $0; grab = 0 }'
      fail=1
    fi
  fi
fi

# ── 4. pytest on the affected test files ─────────────────────────────────────
py_tests="$(printf '%s\n' "$changed" | uv run python scripts/quick_check_affected.py)" || red "the affected-test selection failed"
py_tests="$(printf '%s\n' "$py_tests" | grep -v -e '^$' -e 'tests/e2e/test_desk_sweep.py' -e 'tests/e2e/test_metal.py' || true)"
if [ -n "$py_tests" ]; then
  n="$(printf '%s\n' "$py_tests" | wc -l | tr -d ' ')"
  echo "== pytest affected ($n files)"
  printf '%s\n' "$py_tests" | sed 's/^/   · /'
  lock uv run pytest -q -n 8 --dist worksteal -m "not slow" $py_tests >"$H/py.log" 2>&1; prc=$?
  grep -E '^(FAILED|ERROR)|passed|failed|no tests ran' "$H/py.log" | tail -8 | sed 's/^/   /'
  # 5 = no tests collected (every file's tests are marked slow): not a failure.
  [ "$prc" = 0 ] || [ "$prc" = 5 ] || { echo "   pytest failed (rc=$prc): RED"; fail=1; }
fi

# ── 5. the desk sweep (it must prove it ran), then the canon guards ─────────
echo "== desk sweep"
lock uv run pytest -q -rs -n 8 --dist worksteal tests/e2e/test_desk_sweep.py >"$H/sweep.log" 2>&1; src=$?
grep -E '^(FAILED|ERROR|SKIPPED)|passed|failed|skipped' "$H/sweep.log" | tail -12 | sed 's/^/   /'
swept="$(grep -oE '[0-9]+ passed' "$H/sweep.log" | tail -1 | grep -oE '[0-9]+' || echo 0)"
if grep -qiE 'skipped' "$H/sweep.log"; then
  echo "   the desk sweep SKIPPED (is Playwright installed?): RED"; fail=1
elif [ "$src" != 0 ]; then
  echo "   the desk sweep failed (rc=$src): RED"; fail=1
elif [ "${swept:-0}" -lt "$SWEEP_MIN" ]; then
  echo "   the desk sweep ran ${swept:-0} cases, under the floor of $SWEEP_MIN: RED"; fail=1
fi

echo "== canon guards"
lock uv run pytest -q tests/unit/test_interior_canon_guard.py tests/unit/test_ux_canon_ratchet.py >"$H/canon.log" 2>&1 || { echo "   the canon guards failed: RED"; fail=1; }
grep -E '^(FAILED|ERROR)|passed|failed' "$H/canon.log" | tail -4 | sed 's/^/   /'

if [ "$fail" = 0 ]; then echo "QUICK CHECK GREEN: merge; the main watcher runs the whole suite."; else echo "QUICK CHECK RED: fix before merging."; fi
exit "$fail"

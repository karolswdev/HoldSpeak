#!/usr/bin/env bash
# The pre-merge check (owner ruling 2026-10-12, "the fast cycle").
#
#   scripts/quick_check.sh [base]        # base defaults to origin/main
#   scripts/quick_check.sh --retry       # after a red: the failed tests only
#   QUICK_TESTS="tests/x.py tests/y.py" scripts/quick_check.sh   # add test files
#
# It runs under the test lock and an isolated HOME:
#   * the web build; vitest on the tests the changed web files reach
#     (scripts/vitest_related.py) and the web guards (vitest censuses);
#   * pytest -m "not slow" on the affected test files
#     (scripts/quick_check_affected.py, plus QUICK_TESTS);
#   * the desk sweep (every app at 1440 and 393), which must PROVE it ran
#     (60 or more passed, never skipped); the canon guards; the repo guards
#     (whole-repo censuses and ratchets).
# The whole suite does NOT run here: it runs on main after the merge
# (the orchestrator's main watcher), and a red there is fixed forward at once.
#
# Faster (2026-11-08, owner: "I still see a ton of sequentiality… come on"):
#   * Parallel: the build, vitest and the web guards start together; when the
#     build is done (the hub tests read its bundle), pytest, the desk sweep,
#     the canon guards and the repo guards run together. Each step has its own
#     log and a share of the CPU; one summary prints at the end, in order.
#   * Incremental: .tmp/quick-check/green.json keeps, per step, the head and
#     the sha256 of the step's inputs at its last GREEN
#     (scripts/quick_check_memo.py). A step whose inputs did not change is
#     skipped with one line. A red never records.
#   * No test twice: the canon and repo guards drop the files pytest affected
#     already runs.
#   * A red writes .tmp/quick-check/retry.txt (the failed test ids, and the
#     steps that did not run); `scripts/quick_check.sh --retry` runs only those,
#     and a green records the memo only at the head of the run it retries,
#     for a step whose inputs that run saw (else the next check runs it).
#   * The lock: the whole check holds one lock. It is a "browser" hold
#     (exclusive) when the desk sweep runs, else a "unit" hold, which two other
#     unit runs can share (scripts/test_lock.py).
#
# Fail closed (Astra's review of the first version): a change discovery that
# fails, a skipped sweep, or an unhandled vitest error that is not jsdom's
# canvas "Not implemented" is RED, never a quiet green.
set -uo pipefail
retry=0
base="origin/main"
case "${1:-}" in
  --retry) retry=1 ;;
  "") ;;
  *) base="$1" ;;
esac
root="$(git rev-parse --show-toplevel)" || { echo "QUICK CHECK RED: not in a git work tree"; exit 1; }
cd "$root"
SWEEP_MIN="${QUICK_SWEEP_MIN:-60}"
memo_dir=".tmp/quick-check"
retry_file="$memo_dir/retry.txt"
red() { echo "QUICK CHECK RED: $*"; exit 1; }
memo() { uv run python scripts/quick_check_memo.py "$@"; }

if [ "$retry" = 1 ]; then
  [ -f "$retry_file" ] || red "no $retry_file: the last check was green, or never ran here"
  base="$(sed -n 's/^base //p' "$retry_file" | head -1)"
  [ -n "$base" ] || red "$retry_file names no base"
fi

# ── 1. what changed (each git call is checked; an error is red) ──────────────
# The fetch runs once, before the lock (the run under the lock skips it).
if [ -z "${QUICK_CHECK_CLASS:-}" ]; then
  git fetch -q origin 2>/dev/null || echo "quick_check: fetch failed; using the local $base"
fi
git rev-parse --verify --quiet "$base^{commit}" >/dev/null || red "base '$base' is not a commit"
d1="$(git diff --name-only "$base"...HEAD)" || red "git diff $base...HEAD failed"
d2="$(git diff --name-only)" || red "git diff (work tree) failed"
d3="$(git diff --name-only --cached)" || red "git diff --cached failed"
d4="$(git ls-files --others --exclude-standard)" || red "git ls-files failed"
changed="$(printf '%s\n%s\n%s\n%s\n' "$d1" "$d2" "$d3" "$d4" | grep -v '^$' | sort -u || true)"
[ -z "$changed" ] && { echo "quick_check: no changes against $base"; exit 0; }

webany="$(printf '%s\n' "$changed" | grep -E '^web/' || true)"
hubany="$(printf '%s\n' "$changed" | grep -E '^holdspeak/' || true)"
code="$(printf '%s\n' "$changed" | grep -E '^(web/|holdspeak/|tests/|scripts/|apple/|pyproject\.toml|uv\.lock|package\.json|\.holdspeak/|\.github/)' || true)"

# The retry list: "base <ref>", "ids <step> <id>", "step <step>".
in_retry() { [ "$retry" = 1 ] && grep -qE "^(ids|step) $1( |$)" "$retry_file"; }
retry_ids() { sed -n "s/^ids $1 //p" "$retry_file"; }

# ── 2. one lock for the whole check (2026-11-08) ─────────────────────────────
# Browser (exclusive) when the sweep may run, else unit (shared with two other
# unit runs). The run under the lock does the work; this one only waits.
if [ -z "${QUICK_CHECK_CLASS:-}" ]; then
  cls=unit
  if [ -n "$code" ]; then
    if [ "$retry" = 1 ]; then
      in_retry sweep && cls=browser
    elif [ -n "$webany$hubany" ]; then
      sweep_head="$(memo plan sweep | awk '{print $3}')"
      [ "$sweep_head" = "-" ] && cls=browser
    fi
  fi
  HOME_REAL="${HOME_REAL:-$HOME}"
  H0="$(mktemp -d)"
  HOME="$H0" uv run python scripts/test_lock.py --class "$cls" -- \
    env HOME="$HOME_REAL" HOME_REAL="$HOME_REAL" QUICK_CHECK_CLASS="$cls" bash "$0" "$@"
  rc=$?
  rm -rf "$H0"
  exit "$rc"
fi

started=$(date +%s)
echo "quick_check: $(printf '%s\n' "$changed" | wc -l | tr -d ' ') changed files against $base ($QUICK_CHECK_CLASS lock)"
[ "$retry" = 1 ] && echo "quick_check: --retry: the failed tests and the steps that did not run, from $retry_file"

uncovered="$(printf '%s\n' "$changed" | grep -E '\.(ts|tsx|css)$' | grep -v '^web/src/' || true)"
if [ -n "$uncovered" ]; then
  echo "quick_check: NOT COVERED by the quick check (web files outside web/src; test them yourself):"
  printf '%s\n' "$uncovered" | sed 's/^/   /'
fi

# A caller that already isolated HOME (the Programs engine) names the real one.
HOME_REAL="${HOME_REAL:-$HOME}"; H="$(mktemp -d)"
log_dir="${QUICK_LOG_DIR:-$memo_dir/$(date +%Y%m%d-%H%M%S)}"
keep_logs() {
  mkdir -p "$log_dir"
  for log in "$H"/*.log; do
    [ -f "$log" ] && cp "$log" "$log_dir/"
  done
  rm -rf "$H"
}
trap keep_logs EXIT
export PLAYWRIGHT_BROWSERS_PATH="$HOME_REAL/Library/Caches/ms-playwright" npm_config_cache="$HOME_REAL/.npm"
mkdir -p "$memo_dir"

# Each step writes $H/<step>.log (its output), $H/<step>.sum (its summary
# lines) and $H/<step>.rc (0 green, 1 red); a step that did not run writes no
# .rc. A memo skip writes .skip.
sum() { printf '%s\n' "${@:2}" >>"$H/$1.sum"; }
done_step() { echo "$2" >"$H/$1.rc"; }

# ── the docs-only path (2026-11-07): no code changed; the doc check and the
#    guards that read docs ──────────────────────────────────────────────────
doc_guards=(tests/unit/test_doc_drift_guard.py tests/unit/test_product_copy.py tests/unit/test_decisions.py
            tests/unit/test_graph_atlas.py tests/unit/test_ux_canon_scan.py)
if [ -z "$code" ]; then
  echo "== docs-only change: the build, vitest, pytest and the desk sweep are skipped"
  key="$(memo plan docguards)" || red "the memo failed"
  if [ "$retry" = 0 ] && [ "$(echo "$key" | awk '{print $3}')" != "-" ]; then
    echo "== doc guards: green at $(echo "$key" | awk '{print $3}'), inputs unchanged"
    echo "   ok: not run again"
    echo "QUICK CHECK GREEN: merge; the main watcher runs the whole suite."
    exit 0
  fi
  HOME="$H" uv run python scripts/check_docs.py >"$H/docs.log" 2>&1 || { tail -5 "$H/docs.log"; red "the doc check failed"; }
  tail -1 "$H/docs.log" | sed 's/^/   /'
  echo "== doc guards"
  targets=("${doc_guards[@]}")
  if in_retry docguards; then ids="$(retry_ids docguards)"; [ -n "$ids" ] && targets=($ids); fi
  if HOME="$H" uv run pytest -q "${targets[@]}" >"$H/docguards.log" 2>&1; then
    grep -E 'passed|failed' "$H/docguards.log" | tail -1 | sed 's/^/   /'
    if [ "$retry" = 1 ]; then memo promote "$retry_file" "docguards=$(echo "$key" | awk '{print $2}')"
    else memo record "docguards=$(echo "$key" | awk '{print $2}')"; fi
    rm -f "$retry_file"
    echo "QUICK CHECK GREEN: merge; the main watcher runs the whole suite."
    exit 0
  fi
  grep -E '^(FAILED|ERROR)' "$H/docguards.log" | head -8 | sed 's/^/   /'
  { if [ "$retry" = 1 ]; then grep -E '^(base|head|key) ' "$retry_file"
    else echo "base $base"; echo "head $(git rev-parse HEAD)"; echo "key docguards $(echo "$key" | awk '{print $2}')"; fi
    ids="$(grep -E '^(FAILED|ERROR) ' "$H/docguards.log" | sed -e 's/ - .*//' | awk '{print $2}' | sort -u)"
    if [ -n "$ids" ]; then printf '%s\n' "$ids" | sed 's/^/ids docguards /'; else echo "step docguards"; fi
  } >"$retry_file.new"
  mv "$retry_file.new" "$retry_file"
  echo "   retry the failed tests only: scripts/quick_check.sh --retry"
  red "the doc guards failed"
fi

# ── 3. the selections ────────────────────────────────────────────────────────
# vitest: not `vitest related` (2026-10-31): it follows every barrel and the
# app registry transitively, so one stylesheet selected all 431 files.
# scripts/vitest_related.py walks the same imports, follows a barrel by name,
# and over 120 files keeps the tests within two imports, every per-app T2 file
# and every test that names the file.
web="$(printf '%s\n' "$changed" | grep -E '^web/src/.*\.(ts|tsx|css)$' | sed 's#^web/##' || true)"
web="$(printf '%s\n' "$web" | while read -r f; do [ -n "$f" ] && [ -f "web/$f" ] && echo "$f"; done)"
vt=""
if [ -n "$web" ]; then
  vt="$(uv run python scripts/vitest_related.py --why $web 2>"$H/vitest-related.why")" || red "the vitest selection failed"
fi
printf '%s\n' "$vt" >"$H/vitest.sel"

# The web guards (2026-10-31): vitest censuses that read sources by glob, walk
# or path, so `vitest related` never picks them for the file they judge.
web_guards=(
  src/desk/__tests__/containerQueryLaw.test.ts           # viewport media only on shell exceptions (every CSS file)
  src/pages/cores/__tests__/settingsWriters.test.ts      # one writer per settings subtree (every source file)
  src/desk/__tests__/writeReceiptGuard.test.ts           # a desk write leaves a receipt (every desk source)
  src/desk/__tests__/emojiGuard.test.ts                  # no emoji in glyph and label sources
  src/desk/systemSprites.test.ts                         # every Dock item and launcher has its sprite file
  src/desk/__tests__/illustratedIcons.test.ts            # every illustrated icon has its SVG and PNG
  src/desk/__tests__/sprites32.test.ts                   # the 32 px world sprites (web/public)
  src/desk/__tests__/philo13FacesDoNotLie.test.tsx       # faces show no raw error or raw title (named sources)
  src/desk/components/__tests__/agentWordsFence.test.tsx # agent words come from AgentWords only
  src/desk/surface/__tests__/fence.test.ts               # the surface fence ratchet (fence-baseline.json)
  src/desk/surface/__tests__/kitDelight.test.tsx         # the kit motion and material rules (kit.css, react-app.css)
  src/desk/components/window/__tests__/workBand.test.ts  # the work band tokens (tokens.css)
  src/desk/__tests__/memoryRefsOpen.test.ts              # memory refs match the hub (holdspeak/services/memory_grounding.py)
  src/lib/productLanguage.test.ts                        # product words match docs/product-language.json
  src/desk/attention.test.ts                             # attention ranking matches tests/fixtures (the hub's twin)
  src/desk/surface/__tests__/egress.test.ts              # loopback spellings match tests/fixtures (the hub's twin)
  src/desk/surface/__tests__/fieldLabelWords.test.tsx    # field labels in sentence case (gadgets.css, surface.css)
  src/desk/surface/__tests__/chipWords.test.tsx          # no host on a chip (gadgets.css)
  src/desk/surface/__tests__/lampWords.test.tsx          # lamp words (gadgets.css, recordings.css, DeskChrome)
)

py_tests="$(printf '%s\n' "$changed" | uv run python scripts/quick_check_affected.py)" || red "the affected-test selection failed"
py_tests="$(printf '%s\n' "$py_tests" | grep -v -e '^$' -e 'tests/e2e/test_desk_sweep.py' -e 'tests/e2e/test_metal.py' || true)"
printf '%s\n' "$py_tests" >"$H/pytest.sel"

canon_guards=(tests/unit/test_interior_canon_guard.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_lan_address_guard.py
              tests/unit/test_automation_name_guard.py tests/unit/test_agents_name_guard.py tests/unit/test_engines_name_guard.py)
# The repo guards (2026-10-18): fast whole-repo censuses and ratchets that a
# "related tests" run never picks, so their reds used to reach main unseen
# (static SQL, density, copy, API surface, frame registry, model-call census,
# time census, kernel line budget, residual census, atlas anchors, the
# thread tool gate, the 12 px type floor, the graph join; 2026-10-28: the
# kit's container rule, host-agnostic cores, no HTML injection, no dash in
# web copy; 2026-10-30: the lamp words, the metal lane in the guide, the desk
# never navigates, the build stamp, the desk locks, the first-run wires and
# every MCP tool on a real hub: eight reds that reached main unseen).
repo_guards=(tests/unit/test_static_sql_matches_schema.py tests/unit/test_density_guard.py tests/unit/test_product_copy.py
  tests/unit/test_api_surface.py tests/unit/test_realtime_frame_registry.py tests/unit/test_one_path_census.py
  tests/unit/test_aware_time_census.py tests/unit/test_kernel_effect_fence.py tests/unit/test_decisions.py
  tests/unit/test_philo7_contract.py tests/unit/test_doc_drift_guard.py tests/unit/test_graph_atlas.py
  tests/unit/test_ux_canon_scan.py tests/unit/test_thread_tool_gate.py
  tests/unit/test_philo13_18_type_floor_static.py tests/unit/test_graph_reference.py tests/unit/test_native_surfaces_guard.py
  tests/unit/test_page_cores_guard.py tests/unit/test_web_null_read_guard.py tests/unit/test_web_vocabulary_guard.py
  tests/unit/test_hub_handlers_off_loop.py tests/unit/test_lamp_words_guard.py tests/unit/test_vitest_related.py
  tests/unit/test_ci_lanes.py tests/unit/test_desk_no_exit_guard.py tests/unit/test_web_build_stamp_assets.py
  tests/unit/test_desk_locks.py tests/integration/test_desk_firstrun.py tests/integration/test_mcp_every_tool_runs_on_hub.py)

# No test twice (2026-11-08): a guard file the affected step selected runs
# there, once. ("already run" counts print in the summary.)
not_selected() { for f in "$@"; do grep -qxF "$f" "$H/pytest.sel" || echo "$f"; done; }
canon_run="$(not_selected "${canon_guards[@]}")"
repo_run="$(not_selected "${repo_guards[@]}")"
canon_dropped=$(( ${#canon_guards[@]} - $(printf '%s' "$canon_run" | grep -c . || true) ))
repo_dropped=$(( ${#repo_guards[@]} - $(printf '%s' "$repo_run" | grep -c . || true) ))
printf '%s\n' "${canon_guards[@]}" >"$H/canon.sel"
printf '%s\n' "${repo_guards[@]}" >"$H/repo.sel"
printf '%s\n' "${web_guards[@]}" >"$H/web-guards.sel"

# ── 4. the plan: which steps run, which the memo skips ───────────────────────
plan="$(memo plan build npm "vitest=$H/vitest.sel" "web-guards=$H/web-guards.sel" sweep "pytest=$H/pytest.sel" \
  "canon=$H/canon.sel" "repo=$H/repo.sel")" || red "the memo failed"
key_of() { printf '%s\n' "$plan" | awk -v s="$1" '$1 == s {print $2}'; }
green_at() { printf '%s\n' "$plan" | awk -v s="$1" '$1 == s && $3 != "-" {print $3}'; }

# want <step> <changed-files-gate>: echo run | memo | none | retry-skip
want() {
  local step="$1" gate="$2"
  if [ "$retry" = 1 ]; then
    if in_retry "$step"; then echo run; else echo retry-skip; fi
    return
  fi
  [ -z "$gate" ] && { echo none; return; }
  [ -n "$(green_at "$step")" ] && { echo memo; return; }
  echo run
}
w_build="$(want build "$webany")"
# The built bundle must exist for the sweep, whatever the memo says.
[ "$w_build" = memo ] && [ ! -f holdspeak/static/_built/index.html ] && w_build=run
w_vitest="$(want vitest "$vt")"
w_webg="$(want web-guards "$webany")"
w_py="$(want pytest "$py_tests")"
w_sweep="$(want sweep "$webany$hubany")"
w_canon="$(want canon yes)"
w_repo="$(want repo yes)"
if [ "$w_sweep" = run ] && [ "$QUICK_CHECK_CLASS" != browser ]; then
  red "the tree changed while the check waited for the lock (the desk sweep now has to run): run the check again"
fi

# The CPU budget (12 cores): shared while steps run together.
if [ "$w_sweep" = run ]; then py_n=4; sweep_n=8; repo_n=3; else py_n=8; sweep_n=8; repo_n=4; fi
vt_n=4; webg_n=2

# ── 5. the steps ─────────────────────────────────────────────────────────────
pytest_ids() {  # the failed test ids of a pytest log
  grep -E '^(FAILED|ERROR) ' "$1" | sed -e 's/ - .*//' | awk '{print $2}' | sort -u
}

# The install before the build (2026-11-08): lanes link the main checkout's
# web/node_modules, and a reinstall while a lane runs gave it "two Reacts" and
# "Cannot find module 'react-router/dom'". `npm ci` runs only when
# web/package-lock.json changed since its last green; never through a link.
install_web() {
  local at had=""; at="$(green_at npm)"; [ -d web/node_modules ] && had=1
  if [ -L web/node_modules ]; then
    sum build "   npm ci: web/node_modules is a link to $(readlink web/node_modules); not reinstalled from here"
  elif [ -n "$at" ] && [ -d web/node_modules ]; then
    sum build "   npm ci: web/package-lock.json unchanged since $at, skipped"
  elif [ -d web/node_modules ] && ! grep -q '"npm"' "$memo_dir/green.json" 2>/dev/null; then
    sum build "   npm ci: no record yet and web/node_modules is there, skipped (recorded on a green build)"
  else
    if ! HOME="$H" npm --prefix web ci >"$H/npm-ci.log" 2>&1; then
      tail -20 "$H/npm-ci.log" | sed 's/^/   /' >>"$H/build.sum"; sum build "   npm ci failed: RED"; return 1
    fi
    if [ -n "$had" ]; then sum build "   npm ci: web/package-lock.json changed, reinstalled"
    else sum build "   npm ci: web/node_modules was missing, installed"; fi
  fi
}

run_build() {
  install_web || { done_step build 1; return; }
  if HOME="$H" npm --prefix web run build >"$H/build.log" 2>&1; then
    sum build "   build ok"; done_step build 0
  else
    tail -20 "$H/build.log" | sed 's/^/   /' >>"$H/build.sum"; sum build "   the web build failed: RED"; done_step build 1
  fi
}

# vitest_step <step> <workers> <file...>: the vitest verdict rules (unchanged).
vitest_step() {
  local step="$1" n="$2"; shift 2
  local out rc unhandled canvas
  out="$(cd web && HOME="$H" ./node_modules/.bin/vitest run --maxWorkers="$n" "$@" 2>&1)"; rc=$?
  printf '%s\n' "$out" >"$H/$step.log"
  printf '%s\n' "$out" | grep -E '^ FAIL|×|Test Files|Tests |Errors ' | sort -u | sed 's/^/   /' >>"$H/$step.sum"
  # The unhandled-error blocks: each starts with "⎯ Unhandled Error ⎯" or
  # "⎯ Unhandled Rejection ⎯"; its first line is the error.
  read -r unhandled canvas < <(printf '%s\n' "$out" | awk '
    /Unhandled (Error|Rejection) ⎯/ { grab = 1; total++; next }
    grab && NF { grab = 0; if ($0 ~ /Not implemented: HTMLCanvasElement\.prototype\.getContext/) canvas++ }
    END { print total + 0, canvas + 0 }')
  if printf '%s\n' "$out" | grep -qE '^ FAIL|Tests .*[0-9]+ failed|Test Files .*[0-9]+ failed'; then
    sum "$step" "   $step failed: RED"; done_step "$step" 1
  elif ! printf '%s\n' "$out" | grep -qE 'Tests .*[0-9]+ passed'; then
    sum "$step" "   $step did not report its tests (rc=$rc): RED"; done_step "$step" 1
  elif [ "$rc" != 0 ]; then
    # The ONE tolerated exit: every unhandled error is jsdom's canvas
    # "Not implemented" (no canvas package in the test environment).
    if [ "$unhandled" -gt 0 ] && [ "$unhandled" = "$canvas" ]; then
      sum "$step" "   $step rc=$rc: $canvas unhandled jsdom canvas error(s) only (tolerated)"; done_step "$step" 0
    else
      sum "$step" "   $step rc=$rc: $unhandled unhandled error(s), $canvas of them canvas: RED"
      printf '%s\n' "$out" | awk '/Unhandled (Error|Rejection) ⎯/ { grab = 1; next } grab && NF { print "   > " $0; grab = 0 }' >>"$H/$step.sum"
      done_step "$step" 1
    fi
  else
    done_step "$step" 0
  fi
}

run_vitest() {
  local files
  if [ "$retry" = 1 ]; then files="$(retry_ids vitest)"; [ -z "$files" ] && files="$vt"; else files="$vt"; fi
  vitest_step vitest "$vt_n" $files
}
run_webg() {
  local files
  files="$(retry_ids web-guards 2>/dev/null)"
  [ "$retry" = 1 ] && [ -n "$files" ] || files="${web_guards[*]}"
  vitest_step web-guards "$webg_n" $files
}

# py_step <step> <log-name> <pytest args...>
py_step() {
  local step="$1"; shift
  HOME="$H" uv run pytest "$@" >"$H/$step.log" 2>&1; local prc=$?
  grep -E '^(FAILED|ERROR)|passed|failed|no tests ran' "$H/$step.log" | tail -8 | sed 's/^/   /' >>"$H/$step.sum"
  # 5 = no tests collected (every file's tests are marked slow): not a failure.
  if [ "$prc" = 0 ] || [ "$prc" = 5 ]; then done_step "$step" 0
  else sum "$step" "   $step failed (rc=$prc): RED"; done_step "$step" 1; fi
}
targets_for() {  # the ids to retry for a step, else its default files
  local step="$1"; shift
  local ids=""
  [ "$retry" = 1 ] && ids="$(retry_ids "$step")"
  if [ -n "$ids" ]; then printf '%s\n' "$ids"; else printf '%s\n' "$@"; fi
}
run_pytest() { py_step pytest -q -n "$py_n" --dist worksteal -m "not slow" $(targets_for pytest $py_tests); }
run_canon() {
  local t; t="$(targets_for canon $canon_run)"
  if [ -z "$t" ]; then sum canon "   ok: every file already ran in pytest affected"; done_step canon 0; return; fi
  py_step canon -q $t
}
run_repo() {
  local t; t="$(targets_for repo $repo_run)"
  if [ -z "$t" ]; then sum repo "   ok: every file already ran in pytest affected"; done_step repo 0; return; fi
  py_step repo -q -n "$repo_n" $t
}
run_sweep() {
  local t floor="$SWEEP_MIN" src swept
  t="$(targets_for sweep tests/e2e/test_desk_sweep.py)"
  [ "$retry" = 1 ] && floor=1
  HOME="$H" uv run pytest -q -rfEs -n "$sweep_n" --dist worksteal $t >"$H/sweep.log" 2>&1; src=$?
  grep -E '^(FAILED|ERROR|SKIPPED)|passed|failed|skipped' "$H/sweep.log" | tail -12 | sed 's/^/   /' >>"$H/sweep.sum"
  swept="$(grep -oE '[0-9]+ passed' "$H/sweep.log" | tail -1 | grep -oE '[0-9]+' || echo 0)"
  if grep -qiE 'skipped' "$H/sweep.log"; then
    sum sweep "   the desk sweep SKIPPED (is Playwright installed?): RED"; done_step sweep 1
  elif [ "$src" != 0 ]; then
    grep -E '^E  ' "$H/sweep.log" | head -15 | cut -c1-220 | sed 's/^/   /' >>"$H/sweep.sum"
    sum sweep "   the desk sweep failed (rc=$src): RED (log: $log_dir/sweep.log)"; done_step sweep 1
  elif [ "${swept:-0}" -lt "$floor" ]; then
    sum sweep "   the desk sweep ran ${swept:-0} cases, under the floor of $floor: RED"; done_step sweep 1
  else
    done_step sweep 0
  fi
}

# Phase 1: the build, vitest and the web guards (node only) together.
pids=""
[ "$w_build" = run ] && { run_build & build_pid=$!; }
[ "$w_vitest" = run ] && { run_vitest & pids="$pids $!"; }
[ "$w_webg" = run ] && { run_webg & pids="$pids $!"; }
# Phase 2 waits for the build: the hub tests and the sweep read its bundle
# (holdspeak/static/_built), which the build rewrites in place.
[ "$w_build" = run ] && wait "$build_pid"
build_red=0
[ "$w_build" = run ] && [ "$(cat "$H/build.rc" 2>/dev/null)" != 0 ] && build_red=1
[ "$w_py" = run ] && { run_pytest & pids="$pids $!"; }
if [ "$w_sweep" = run ] && [ "$build_red" = 0 ]; then run_sweep & pids="$pids $!"; fi
[ "$w_canon" = run ] && { run_canon & pids="$pids $!"; }
[ "$w_repo" = run ] && { run_repo & pids="$pids $!"; }
for p in $pids; do wait "$p"; done

# ── 6. the summary, in order ─────────────────────────────────────────────────
fail=0
promote=""
retry_rows=""
# report <step> <title> <want> <none-reason>
report() {
  local step="$1" title="$2" w="$3" none="$4" rc
  case "$w" in
    none) echo "== $title: $none, skipped"; echo "   ok: not needed"; return ;;
    memo) echo "== $title: green at $(green_at "$step"), inputs unchanged"; echo "   ok: not run again"; return ;;
    retry-skip) echo "== $title: not in the retry list (green or not needed in the last run)"; echo "   ok: not run again"; return ;;
  esac
  rc="$(cat "$H/$step.rc" 2>/dev/null || echo none)"
  if [ "$retry" = 1 ]; then echo "== $title (retry: the failed tests of the last run)"; else echo "== $title${5:-}"; fi
  [ -f "$H/$step.sum" ] && cat "$H/$step.sum"
  if [ "$rc" = 0 ]; then
    promote="$promote $step=$(key_of "$step")"
  elif [ "$rc" = none ]; then
    echo "   did not run (the build is red): RED"; fail=1
    retry_rows="$retry_rows
step $step"
  else
    fail=1
    local ids=""
    case "$step" in
      vitest|web-guards) ids="$(grep -E '^ FAIL ' "$H/$step.log" 2>/dev/null | awk '{print $2}' | sort -u)" ;;
      build) ids="" ;;
      *) ids="$(pytest_ids "$H/$step.log")" ;;
    esac
    if [ -n "$ids" ]; then
      retry_rows="$retry_rows
$(printf '%s\n' "$ids" | sed "s/^/ids $step /")"
    else
      retry_rows="$retry_rows
step $step"
    fi
  fi
}
nweb="$(printf '%s\n' "$web" | grep -c . || true)"; nvt="$(printf '%s\n' "$vt" | grep -c . || true)"
npy="$(printf '%s\n' "$py_tests" | grep -c . || true)"
report build "build" "$w_build" "nothing under web/ changed"
if [ "$retry" = 0 ] && [ -s "$H/vitest-related.why" ] && [ "$w_vitest" = run ]; then sed 's/^/   /' "$H/vitest-related.why"; fi
if [ -n "$web" ] && [ -z "$vt" ] && [ "$retry" = 0 ]; then echo "== vitest: no web test reaches the changed files"; echo "   ok"
else report vitest "vitest" "$w_vitest" "no web test file changed or reached" " ($nweb changed web files, $nvt test files)"; fi
report web-guards "web guards" "$w_webg" "nothing under web/ changed" " (${#web_guards[@]} files)"
if [ "$w_py" = run ] && [ "$retry" = 0 ]; then
  report pytest "pytest affected" "$w_py" "no test file affected" " ($npy files, -n $py_n)"
  printf '%s\n' "$py_tests" | sed 's/^/   · /'
else
  report pytest "pytest affected" "$w_py" "no test file affected" " ($npy files)"
fi
if [ "$build_red" = 1 ] && [ "$w_sweep" = run ]; then
  echo "== desk sweep"; echo "   did not run (the build is red): RED"; fail=1
  retry_rows="$retry_rows
step sweep"
else
  report sweep "desk sweep" "$w_sweep" "nothing under web/ or holdspeak/ changed" " (-n $sweep_n)"
fi
report canon "canon guards" "$w_canon" "" " ($canon_dropped of ${#canon_guards[@]} files already run in pytest affected)"
report repo "repo guards" "$w_repo" "" " ($repo_dropped of ${#repo_guards[@]} files already run in pytest affected)"

# A deduplicated guard step is green only with the affected step that ran its
# dropped files: record it only when pytest is green (or was not needed).
pyrc="$(cat "$H/pytest.rc" 2>/dev/null || echo 0)"
rec=""
for pair in $promote; do
  case "$pair" in canon=*|repo=*) [ "$pyrc" = 0 ] || continue ;; esac
  rec="$rec $pair"
  # A green build means the install it ran on is good: the lock file's key.
  case "$pair" in build=*) rec="$rec npm=$(key_of npm)" ;; esac
done
if [ "$retry" = 1 ]; then
  # A retry records only at the head of the run it retries, and only a step
  # whose inputs are what that run saw (retry.txt "head" and "key").
  [ -n "$rec" ] && memo promote "$retry_file" $rec
else
  [ -n "$rec" ] && memo record $rec
fi

took=$(( $(date +%s) - started ))
if [ "$fail" = 0 ]; then
  rm -f "$retry_file"
  echo "QUICK CHECK GREEN: merge; the main watcher runs the whole suite. (${took} s)"
else
  if [ "$retry" = 1 ]; then
    # Still red: keep the run being retried (its head and keys); the ids are new.
    { grep -E '^(base|head|key) ' "$retry_file"; printf '%s\n' "$retry_rows" | grep -v '^$'; } >"$retry_file.new"
    mv "$retry_file.new" "$retry_file"
  else
    { echo "base $base"; echo "head $(git rev-parse HEAD)"
      printf '%s\n' "$plan" | awk '{print "key " $1 " " $2}'
      printf '%s\n' "$retry_rows" | grep -v '^$'; } >"$retry_file"
  fi
  nids="$(grep -c '^ids ' "$retry_file" || true)"; nsteps="$(grep -c '^step ' "$retry_file" || true)"
  echo "   retry: $nids failed test id(s) and $nsteps whole step(s) in $retry_file"
  echo "   after the fix, run: scripts/quick_check.sh --retry"
  echo "QUICK CHECK RED: fix before merging. (${took} s)"
fi
exit "$fail"

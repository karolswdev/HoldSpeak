#!/usr/bin/env bash
# The post-merge guard check (owner ruling 2026-11-09: the load and the
# check time were "unacceptable").
#
#   scripts/main_check.sh            # on main, ONCE after a merge batch
#   scripts/main_check.sh --retry    # after a red: the failed tests only
#
# The orchestrator runs it on main after a merge batch: never per PR, never
# in a lane. It runs the whole-repo guards that scripts/quick_check.sh ran on
# every PR until 2026-11-09, together, each inside the test CPU budget
# (scripts/test_lock.py) with an isolated HOME:
#   * pytest: the repo guards and the canon guards, -n 6 --dist loadfile (a
#     module fixture builds once per file, not once per worker);
#   * vitest: the web guards (censuses that read sources by glob, walk or
#     path, so a related-tests run never picks them);
#   * scripts/check_docs.py.
# A red writes .tmp/main-check/retry.txt ("ids <step> <id>" or "step <step>");
# --retry runs only those. A red is fixed forward at once.
set -uo pipefail
retry=0
[ "${1:-}" = "--retry" ] && retry=1
root="$(git rev-parse --show-toplevel)" || { echo "MAIN CHECK RED: not in a git work tree"; exit 1; }
cd "$root"
retry_file=".tmp/main-check/retry.txt"
[ "$retry" = 1 ] && [ ! -f "$retry_file" ] && { echo "MAIN CHECK RED: no $retry_file"; exit 1; }
HOME_REAL="${HOME_REAL:-$HOME}"; H="$(mktemp -d)"
log_dir=".tmp/main-check/$(date +%Y%m%d-%H%M%S)"
trap 'mkdir -p "$log_dir"; cp "$H"/*.log "$log_dir/" 2>/dev/null; rm -rf "$H"' EXIT
export PLAYWRIGHT_BROWSERS_PATH="$HOME_REAL/Library/Caches/ms-playwright" npm_config_cache="$HOME_REAL/.npm"
locked() { local n="$1"; shift; uv run --project "$root" python "$root/scripts/test_lock.py" --cpus "$n" -- "$@"; }

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

# targets <step> <default...>: the retry ids of a step, else its defaults;
# nothing when a retry does not name the step.
targets() {
  local step="$1"; shift
  if [ "$retry" = 0 ]; then printf '%s\n' "$@"; return; fi
  grep -qE "^step $step$" "$retry_file" && { printf '%s\n' "$@"; return; }
  sed -n "s/^ids $step //p" "$retry_file"
}
py_t="$(targets pytest "${repo_guards[@]}" "${canon_guards[@]}")"
vt_t="$(targets vitest "${web_guards[@]}")"
docs_t="$(targets docs docs)"

started=$(date +%s)
pids=""
[ -n "$py_t" ] && { HOME="$H" locked 6 uv run pytest -q -n 6 --dist loadfile --durations=5 $py_t >"$H/pytest.log" 2>&1
                    echo $? >"$H/pytest.rc"; } & pids="$pids $!"
[ -n "$vt_t" ] && { (cd web && HOME="$H" locked 4 ./node_modules/.bin/vitest run --maxWorkers=4 $vt_t) >"$H/vitest.log" 2>&1
                    echo $? >"$H/vitest.rc"; } & pids="$pids $!"
[ -n "$docs_t" ] && { HOME="$H" locked 1 uv run python scripts/check_docs.py >"$H/docs.log" 2>&1
                      echo $? >"$H/docs.rc"; } & pids="$pids $!"
for p in $pids; do wait "$p"; done

fail=0
rows=""
for step in pytest vitest docs; do
  [ -f "$H/$step.log" ] || continue
  rc="$(cat "$H/$step.rc" 2>/dev/null || echo 1)"
  echo "== $step"
  case "$step" in
    pytest) grep -E '^(FAILED|ERROR)|passed|failed|slowest|^[0-9.]+s ' "$H/pytest.log" | tail -14 | sed 's/^/   /' ;;
    vitest) grep -E '^ FAIL|Test Files|Tests ' "$H/vitest.log" | sort -u | sed 's/^/   /' ;;
    docs) tail -3 "$H/docs.log" | sed 's/^/   /' ;;
  esac
  [ "$rc" = 0 ] && continue
  fail=1
  case "$step" in
    pytest) ids="$(grep -E '^(FAILED|ERROR) ' "$H/pytest.log" | sed -e 's/ - .*//' | awk '{print $2}' | sort -u)" ;;
    vitest) ids="$(grep -E '^ FAIL ' "$H/vitest.log" | awk '{print $2}' | sort -u)" ;;
    *) ids="" ;;
  esac
  if [ -n "$ids" ]; then rows="$rows$(printf '%s\n' "$ids" | sed "s/^/ids $step /")
"; else rows="${rows}step $step
"; fi
  echo "   $step failed (rc=$rc): RED (log: $log_dir/$step.log)"
done

took=$(( $(date +%s) - started ))
mkdir -p "$(dirname "$retry_file")"
if [ "$fail" = 0 ]; then
  rm -f "$retry_file"
  echo "MAIN CHECK GREEN (${took} s)"
else
  printf '%s' "$rows" >"$retry_file"
  echo "   after the fix, run: scripts/main_check.sh --retry"
  echo "MAIN CHECK RED: fix forward on main. (${took} s)"
fi
exit "$fail"

# Validation and test commands

**Shared reference for the current [ordered plan](EXECUTION_INDEX.md). Detailed planning is authorized; this document grants no repository execution or shipping permission.**
## What these commands mean

Command spellings, script definitions and named target paths were checked statically against the pinned repository's `AGENTS.md`, `CLAUDE.md`, `web/package.json`, `pyproject.toml` and `scripts/quick_check.sh`; see [Evidence](EVIDENCE.md) and the [readiness inventory](PACKAGE_VALIDATION.md#source-defined-validation-readiness). This does not establish installed tools, successful collection, executable commands or passing checks. They were **not executed while preparing this plan**. Run them only in the assigned authorized implementation checkout after HS-T00. Do not treat Markdown package checks as HoldSpeak test results.

Use the current repo instructions if they changed. The October 12 fast cycle supersedes older FAST/full-suite premerge text: workers run only named focused files; the integration/ship owner runs quick check; full tape is for the postmerge watcher/nightly. No extra mandatory premerge brain ceremony is introduced here.

## Setup and isolation

Source requirements include Python 3.10+, uv, npm, Node 22.12+. For a new authorized implementation environment, the repo directs `uv sync --extra dev`; add only a necessary platform extra (Linux may need `--extra linux`). Never `--all-extras` or plain `uv sync`. Read current `CONTRIBUTING.md` for web dependency installation; do not guess a package manager or run install commands against this documentation folder.

All pytest, Vitest, glass selectors and graph walks acquire `scripts/test_lock.py`; never bypass/nest it. Each run gets isolated HOME. Keep keystores, DB and agent config inside that HOME. The wrapper below uses the repository's documented macOS browser-cache path; **on Linux or another executor, resolve its actual installed Playwright cache and use that absolute path before running**. Do not assume this host shares the owner's cache.

Rigs must disable real machine/provider effects. Verify current fixture opt-outs: `HOLDSPEAK_AGENT_STATE=off`, `HOLDSPEAK_ACTIVE_TARGET=off`, `HOLDSPEAK_DESKTOP_NOTIFY=0`, `HOLDSPEAK_MACOS_CALENDAR=0`, `HOLDSPEAK_CLI_ENGINES=off`, `HOLDSPEAK_RESTART_CHECK=off`, `HOLDSPEAK_SCREEN_RULES=off`, `HOLDSPEAK_CALLS=off`, `HOLDSPEAK_LINE=off`, `HOLDSPEAK_RECORDINGS=off`, `HOLDSPEAK_MIC_CHECK=off`, `HOLDSPEAK_PROGRAMS=off`, `HOLDSPEAK_PHONE=off`, `HOLDSPEAK_TELEGRAM=off`. Ask probing also has `HOLDSPEAK_ASK_SERVER_TOOLS=off`. A capability-specific test may exercise fake adapters deliberately; it may not implicitly enable a real phone/model/send just because its test name contains Calls. Inspect the fixture before executing.

Never run `tests/e2e/test_metal.py`; never set `HOLDSPEAK_EVIDENCE_WRITE=1`. Do not use a rig's configured LAN engine as permission to contact it.

## Focused Python recipe

From repository root, with only the task's listed files at the end:

```sh
(
  HS_REAL_HOME="$HOME"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_REAL_HOME/Library/Caches/ms-playwright"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/unit/test_thread_tool_loop.py
)
```

Collect first when confirming added coverage: same isolation and lock, with `--collect-only` added to pytest. Collection is not a test run or a pass; it can execute module/application code and requires the same authority and isolation. Record the actual command, collection output, run tail and exit status. Do not erase logs with scratch HOME: copy useful logs into an authorized `.tmp/` location before cleanup, or capture them from the executor output. If using `tee`, enable pipefail so logging cannot turn failure into success.

## Focused web recipe

From repository root, using the same actual-cache adjustment:

```sh
(
  HS_REAL_HOME="$HOME"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_REAL_HOME/Library/Caches/ms-playwright"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  cd web
  uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 src/desk/hooks/__tests__/usePrimitiveDetail.test.ts src/desk/programs/__tests__/programs.app.test.tsx
)
```

Use recorded real hub answers and press through to a rendered result. Do not replace them with a typed object that bypasses the producer. Existing setup clears `deskQueryClient` between tests; preserve that isolation. A deferred promise test can prove stale-result suppression, not physical HTTP abort unless the actual transport supports and demonstrates it.

## Focused suite matrix

| Task family | Exact existing test files |
| --- | --- |
| Program query | `web/src/desk/hooks/__tests__/usePrimitiveDetail.test.ts`; `web/src/desk/programs/__tests__/programs.app.test.tsx` |
| Thread core | `tests/unit/test_thread_tool_loop.py` |
| Ask integration | `tests/integration/test_desk_ask_tools.py` |
| Calls integration and late work | `tests/integration/test_calls_turn.py`; `tests/unit/test_phone_answer_later.py`; `tests/integration/test_line_call.py` |
| Project update policy | `tests/unit/test_project_update_drafter.py` |
| Checkpoint/handoff backend | `tests/integration/test_desk_programs.py`; `tests/unit/test_program_handoff.py` |
| Checkpoint UI | `web/src/desk/programs/__tests__/programs.app.test.tsx` |

Tasks specify their own subset and new cases. New test files, if truly necessary, must be explicitly labeled proposed and approved within the task's ownership; prefer extending these existing app/domain suites.

## Integrated gate

From repository root, with a real current comparison base established in T00:

```sh
DESK_SWEEP_SHOTS=1 scripts/quick_check.sh origin/main
```

It manages HOME and the machine lock itself. **Do not wrap it in `test_lock.py`.** At this pin, a no-change comparison exits 0 before any build/test/sweep stage: that result is not an integrated validation pass. The affected-Python stage also uses `-m "not slow"` and tolerates pytest exit 5 (no tests collected), so green alone does not prove each required focused test executed. Inspect actual stage output, not exit status alone. The script also assigns the macOS Playwright cache internally; the focused-recipe cache adjustment above does not fix this wrapper on another platform. Confirm a supported browser-cache arrangement in the eventual assigned environment before claiming sweep readiness. It fetches origin when possible, builds the web, selects affected tests, runs web guards, the Desk sweep and canon/repository guards. An unavailable fetch means the script may use a local base; report that and confirm the compared commit. If affected selection misses a required Python file, add its verified path through the documented `QUICK_TESTS="..."` environment variable. Never reduce sweep thresholds or add allowlist entries to mask failures. The sweep must actually run at 1440 and 393, not skip.

Inspect relevant shots from `.tmp/evidence-shots/`. E04 changes visible row states, so inspect ordinary/handoff success/failure and neutral rows; E01 must not introduce loading flicker or hide failure/receipts. When reflow changes, also inspect a narrow window on a wide Desk. A real-browser task is needed only for claims that require focus/keys/touch/geometry beyond the existing sweep. If a necessary case is not selected, name its verified existing browser file in the scoped plan; do not invent a command or launch a broad suite.

Supplemental repository-defined web scripts (definition checked; not run) (not substitutes for behavior/quick check): `npm --prefix web run typecheck`, `npm --prefix web run build`, `npm --prefix web run guard:architecture`, and token checks only if the task touches those responsibilities. Use the repository's lock for any invocation that runs tests. Do not run `npm run check` as an unbounded replacement for the named budget.

## Failure and completion rules

- A failing baseline is reported with an isolated reproduction; do not call it your regression without evidence or clean others' files.
- A failed assertion, skipped required check, unhandled exception, missing screenshot, unknown external result or incomplete final persistence is not success.
- Reproduction and fix stay within authorized task paths. Wider code or test work needs a bounded amendment, not a broad rewrite.
- Preserve logs and report which boundary was exercised. Fixture proof is not live-provider proof; green technical checks are not owner aesthetic acceptance.
- Finish with [the completion report](COMPLETION_REPORT_TEMPLATE.md). No staging, commit, PR, merge or deployment unless separately authorized.

## V23 First-slice verification

**Applies to HS-S23 only.** Source verification: pinned root `AGENTS.md` (test/lock/setup sections), current fast-cycle `CLAUDE.md`, `pyproject.toml`, `scripts/test_lock.py`, `scripts/quick_check.sh`, and the five test files below were inspected; main matched the pin at 19:34 UTC on 3 November 2026. No commands in this section were run during planning. Installed dependencies, collection and passing tests are not established.

### Exact focused file budget

1. `tests/unit/test_program_text.py`
2. `tests/unit/test_program_agent_bar.py`
3. `tests/unit/test_program_shaper.py`
4. `tests/unit/test_program_night.py`
5. `tests/unit/test_program_night_canon.py`

The first three are the only editable tests; the final two are unchanged consumer regression coverage. Existing fixtures are `tests/integration/program_rig.py`, `program_night_seed.py`, `program_shape_seed.py` and `tests/conftest.py`. Inspect their current injected adapters and opt-outs; do not launch real agents, models, GitHub operations, phone or owner-data reads. A test using a local temporary Git rig is not permission to operate on the owner's repositories.

### Existing assertions versus proposed new coverage

| Existing source-inspected case | Keep or extend |
| --- | --- |
| `test_program_agent_bar.py::test_removing_a_within_path_lowers_the_bar` | Split full/partial removal. Keep full removal's owner handling; revise partial removal only after accepted G23 |
| `test_program_agent_bar.py::test_an_agents_allow_lower_is_refused_by_name`; `test_the_owner_lowers_the_bar_as_before`; `test_an_agents_shaped_lower_bar_never_applies_at_yolo` | Preserve actual owner/creator-agent and forbidden allow-list behavior; add `within` expansion siblings |
| `test_program_text.py::test_a_dry_run_writes_nothing`; `test_a_refused_row_or_an_unpassed_lowering_writes_nothing`; `test_a_field_changed_since_he_read_it_is_a_conflict` | Preserve no-write, stale-conflict and other-field behavior |
| `test_program_text.py::test_the_rows_that_lower_the_bar`; `test_the_program_fields_apply_and_read_back`; grammar/round-trip cases | Add C01–C15 with returned row/allowed-text and stored-state assertions, not only helper output |
| `test_program_shaper.py::test_a_row_that_lowers_the_bar_never_applies_at_yolo`; `test_at_yolo_a_mixed_answer_applies_the_allowed_row_and_keeps_the_lowering_for_his_press` | Extend to `within`; preserve generated owner-invoked lower-bar hold and allowed-row partial application |
| `test_program_night.py::test_at_the_window_start_each_item_is_planned_into_one_tiny_step_and_handed`; `test_with_no_planner_an_item_runs_as_written` | Unchanged night behavior and no universal-enforcement claim |
| `test_program_night_canon.py::test_the_canon_files_five_door_tasks_inside_within_and_never_twice_while_open` | Unchanged bounded canon selection |

All C01–C15 and newly named regression tests are **proposed** until authored. Existing source tests were not collected or executed for this plan. The test `AGENT` fixture is the creator `Principal(PrincipalKind.AGENT, 'agent:orchestrator')`; use the existing `_agents_program`/`_hand_to_agent` and Rig seams rather than inventing wire state or weakening principal checks.

### Future authorized focused command

The lock/pytest flags and file paths are verified from repository source. The following Bash wrapper is **plan-composed** to retain evidence, not an existing repository script. Run it from the assigned repository root only after HS-T00. Set `HS_PLAYWRIGHT_CACHE` to the actual supported cache on that host; the repository's example is macOS-specific. Set `HS_EVIDENCE_DIR` to a task-owned path such as an absolute `.tmp/hs-s23/baseline` or `.tmp/hs-s23/final` inside that checkout, outside temporary HOME.

```sh
(
  set -euo pipefail
  : "${HS_PLAYWRIGHT_CACHE:?Resolve the actual host browser cache first}"
  : "${HS_EVIDENCE_DIR:?Set an absolute task-owned evidence path}"
  HS_REAL_HOME="$HOME"
  mkdir -p "$HS_EVIDENCE_DIR"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_PLAYWRIGHT_CACHE"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  files=(
    tests/unit/test_program_text.py
    tests/unit/test_program_agent_bar.py
    tests/unit/test_program_shaper.py
    tests/unit/test_program_night.py
    tests/unit/test_program_night_canon.py
  )
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal "${files[@]}" | tee "$HS_EVIDENCE_DIR/collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal "${files[@]}" | tee "$HS_EVIDENCE_DIR/run.log"
)
```

Capture the outer command's exit status as well as both logs. `pipefail` preserves pytest failures; a collection failure stops the run. Do not treat an expected red during HS-T23-02 as final acceptance. Retain baseline and final logs separately. Current fixture isolation takes precedence over a stale command example; never solve a failure by opting into a real provider.

### Future integration-owner command

Repository-defined command/flags, **not run**:

```sh
DESK_SWEEP_SHOTS=1 QUICK_TESTS="tests/unit/test_program_text.py tests/unit/test_program_agent_bar.py tests/unit/test_program_shaper.py tests/unit/test_program_night.py tests/unit/test_program_night_canon.py" scripts/quick_check.sh origin/main
```

The integration owner must confirm the comparison ref is the intended base, inspect any fetch/base drift and report the actual compared commit. If current workflow uses a recorded commit instead of `origin/main`, pass that reviewed supported base argument and record it. This script can fetch, build and run tests; it is not a read-only research command. It owns isolation/locks, so do not wrap it. Its hardcoded macOS cache assumptions and the no-change/no-test early-exit caveats in [Integrated gate](#integrated-gate) still apply. Desk sweep stages and required shots must run, not merely be configured. Workers do not run the full tape.

No mandatory Ruff invocation was found in the inspected current workflow, despite Ruff being a dev dependency. Do not invent a required lint pass or replace the repository aggregate gate with one. A separately proposed optional command must be labeled as such and stay within exact owned files.

### Proof classification

- **Verified while planning:** pin/current-main match, source symbol/test paths, script definitions and flags.
- **Not established:** environment setup, test collection, baseline/final results, screenshots, integrated gate, runtime behavior or owner acceptance.
- **Completion evidence required after assignment:** accepted G23, final diff identity, collected test count, exact commands/exit statuses/logs, all C cases and authority/YOLO proof, independent review, integrated-stage evidence and remaining gaps.

## V11 Program-creation verification

**Applies to HS-S11's conditional bound-creation branch only.** Exact paths, command definitions and the real create chain were inspected at `80b641fa41c7352280cfa52e933acf6dbe8d3857`. This is source verification, not installed-tool readiness, executed collection, passing tests or live UI proof. The task's G11 and implementation assignment remain prerequisites.

### Exact focused file budget

Editable tests:
1. `tests/integration/test_desk_programs.py`
2. `web/src/desk/programs/__tests__/programs.app.test.tsx`

Unchanged preservation tests:
3. `tests/integration/test_desk_program_from_action.py`
4. `web/src/desk/programs/__tests__/runAsProgram.app.test.tsx`

Proposed new editable browser test, absent until implemented:
5. `tests/e2e/test_program_creation_glass.py`

The backend creation proof must keep `ProgramService.create`, `_repository`, `_project_source` and `resolve_project_repository` real, injecting only a temporary hand/registry dependency. The existing from-action test substitutes `_project_source`, so it is contextual/provenance preservation evidence, not the new full resolver proof. Reuse current `Rig`, `_client`, `_fixture` and bare per-test runtime composition; do not use the owner's DB, registration or Git checkout.

### Existing assertions and new proof

- Existing `programs.app.test.tsx` case `New program makes a Fast cycle Program and opens its window` at the pin accepts the incomplete `{title, template}` body. Replace that expectation with no creation before explicit project choice and the complete acknowledged request. Existing `program.drafting.json` was produced from a raw-repository overnight Program with planned steps; it is not matching Fast-cycle/project-create evidence.
- Existing New/template/list-event, note-origin and contextual `runAsProgram.app.test.tsx` behavior must remain. The Programs app harness exposes `mocks.openPullout` and unmount; direct deferred `apiFetch` mocks support late-result cases. Its `hub()` helper structured-clones values and must not receive a Promise. A thrown reveal can be simulated, but `openProgram` returning normally does not prove mounted UI. Current `usePrograms.reload` catches read failure internally; use its error/read state for the refresh case. Reset mock implementations per case, not only call history.
- New producer cases are **proposed** as `test_creation_context_project_create_records_real_wire` and `test_creation_context_refusals_preserve_outcomes` in the existing integration file. The first is the **sole writer of all four captures**, from one synthetic scenario: repository-backed project, no-repository project and archived exclusion. Use actual active-project GET plus real create POST, with temporary filed local repository and explicit owner principal. Keep each roster ID, successful request/Program project ID and no-repository request ID coherent. The browser must select that actual no-repository member before replaying its refusal. Do not regenerate independently unrelated IDs and repair the captured bodies by hand.
- The second producer writes no fixture. Assert 400/repository_required and 409/no_repository before a Program save; then inject `_checkpoint` failure after real `save_program` in a separate attempt, retaining actual route/create. Assert generic500, exactly one new persisted Program from before/after ID-set difference, and zero hand/launch. Restore the injected failure before real service readback. This proves the existing persisted-but-unconfirmed boundary without a new runtime mechanism or another capture. The bare router is producer contract proof, not full hub authentication proof.
- The client uses existing `web/src/lib/api.ts::ApiError` status/payload and the route’s structured code. Only the two proved status/code pairs above may be labeled pre-Program refusal in this slice; other errors are unconfirmed unless independently proved. Even a pre-Program refusal is not universal no-side-effect proof because resolver fallback can register a source.
- New owned fixture paths are the four `program.create_*.json` files named in HS-T11-02. Each uses the **proposed test-only capture record** `{request: {method, path, json?}, response: {status, body}}`. `json` is the exact submitted body and is omitted for GET; `response.body` is the actual decoded hub response, not a fabricated success or a new service envelope. Pass this complete record through existing `_fixture` with its documented temporary-path scrubbing. The success and project-list consumers replay `response.body`; refusal consumers build the existing ApiError or Playwright reply from `response.status`/`response.body`. Obtain the failed request’s project ID from `request.json.project_id`, because the actual refusal body carries no project ID. Preserve raw response fields and exact identity relationships; do not add metadata inside the service body or hand-edit captured IDs. IDs/timestamps may vary between source runs; shape equality is not semantic equality or byte-deterministic replay.

### Future focused command

Use the [setup/isolation rules](#setup-and-isolation) and actual host browser cache. The Bash wrapper below is **plan-composed**, while the lock, pytest/Vitest flags and target files are source-verified. Set `HS_EVIDENCE_DIR` to an absolute task-owned path outside scratch HOME. Run from the assigned repository root after HS-T00. No command below was executed during planning.

```sh
(
  set -euo pipefail
  : "${HS_PLAYWRIGHT_CACHE:?Resolve the actual host browser cache first}"
  : "${HS_EVIDENCE_DIR:?Set an absolute task-owned evidence path}"
  HS_REAL_HOME="$HOME"
  mkdir -p "$HS_EVIDENCE_DIR"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_PLAYWRIGHT_CACHE"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  unset HOLDSPEAK_WIRE_WRITE HOLDSPEAK_WRITE_WIRE_FIXTURES HOLDSPEAK_EVIDENCE_WRITE
  py_files=(tests/integration/test_desk_programs.py tests/integration/test_desk_program_from_action.py)
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/python.log"
  (
    cd web
    uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 src/desk/programs/__tests__/programs.app.test.tsx src/desk/programs/__tests__/runAsProgram.app.test.tsx
  ) | tee "$HS_EVIDENCE_DIR/web.log"
)
```

Record actual selected case counts and skipped cases. New cases do not exist until implemented. Run the unchanged baseline first and the final suite after the last edit; a failed baseline is not automatically a regression. This budget does not include HS-S23's classifier tests unless that separate assigned slice also changed.

### Bounded fixture recording during implementation

The existing `_fixture` writes only with `HOLDSPEAK_WIRE_WRITE=1`, scrubs the temp root to `/tmp/rig` and then checks shape. This is distinct from the forbidden `HOLDSPEAK_EVIDENCE_WRITE=1`. Shape alone is insufficient, so keep real response/store assertions in the producer tests.

Under the same isolation/lock setup, first collect the **proposed** new selection and confirm it contains only the two intended producer cases. Then record only the sole capture-owner node, inspect exactly four approved output paths and rerun both cases with recording off. The assertion-only node must never call `_fixture` for these files:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/integration/test_desk_programs.py -k creation_context
HOLDSPEAK_WIRE_WRITE=1 uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/integration/test_desk_programs.py::test_creation_context_project_create_records_real_wire
```

The selector and new cases are plan proposals; if collection matches other producers or writes other files, stop and narrow the invocation. Do not run `scripts/record_program_fixtures.py`, the whole producer file with recording enabled, or a broad fixture refresh. These recording commands belong only to an assigned implementation task owning those fixture writes, not a read-only verification task.

### Bounded browser lane

**Proposed test:** `tests/e2e/test_program_creation_glass.py`. Its behavior and filename are planned, not an existing passing check. Do not substitute `test_program_keys_glass.py`: that existing test really creates, plans and starts Programs. Reuse the existing `tests/e2e/glass_infra.py`, not a new harness.

Source-verified helpers: `_ensure_build` 140–185, `_boot` 199–331, `clear_hub_windows` 405–414, `_api` 417–429, `_normal_chair` 769–776, `_settle` 473–491, `_assert_readable` 661–665 and `_assert_clean` 670–680. The existing keys-glass imports/cleanup demonstrate `evidence_dir`, headless Chromium and `finally` cleanup. Exact new test names/selectors are proposed and must be checked against the actual rendered UI.

1. Build via the existing helper only in the assigned environment, then `_boot(tmp_path, monkeypatch, token=<test token>)`. It isolates `tmp_path/home` and `tmp_path/holdspeak.db` and disables real machine/provider probes. `HOLDSPEAK_PROGRAMS=off` stops ticking, **not HTTP creation**.
2. Before navigation, install a small test-local Playwright context route handler for exact method/path contracts. Fulfill GET `/api/projects` from `program.create_projects.json`, GET `/api/programs` with the actual empty-list shape, and expected POST `/api/programs` with the captured no-repository refusal envelope/status. Record and assert the exact submitted project/template/title, with the chosen roster ID equal to the captured no-repository request ID; do not replay that refusal against the repository-backed success member. Abort unexpected Program mutations and fail the test; no create/plan/start may fall through to the real hub. This is a proposed fixture edge, not a new production adapter.
3. Add test-local route variants for delayed loading, an empty `{projects: []}` result, a failed project read, and a refreshed roster that removes/archives the selected ID. Label these as deliberate fault/state injection, not captured live server behavior. Trigger refresh through the proposed explicit Refresh projects action; prove it does not select a replacement. These variants add no fixture files or production API and still intercept/fail closed for every Program mutation.
4. Use the isolated shell's existing onboarding/window API and helpers to open `surface-programs`. Do not create a Project/repository or invent a successful Program ID in this UI lane. Exercise New and compact Templates, explicit selection, Cancel before submit (zero POSTs), keyboard/Escape/focus return, reopen and an intercepted refusal retaining the well/context. Successful real creation is proved by the separate producer test; acknowledged reveal logic is proved by app tests, not by this refusal-only browser lane.
5. Observe 1440 and 393, plus a narrow window on a wide Desk, including the named loading/empty/read-failure/unavailable-selection/refusal variants. Use the actual pointer resize grip `#surface-programs .desk-window-grip`: existing `web/src/desk/components/DeskWindow.tsx` binds `resizeBind` at 679–696, renders the grip at 786–790/1451 and the root ID at 1250. `web/src/desk/applications.ts` 218–234 sets this window’s `minW: 420`. At 1440, start in an ordinary noncompact/unmaximized window, drag the real grip toward its legal minimum and measure the settled frame/content dimensions; do not claim 393-wide desktop content or force CSS/store dimensions. At 393, the frame is compact and has no grip, so that is separate viewport proof. These are source-verified controls, not an already executed browser case; missing/obscured controls or failed measured resizing leave that proof blocked.
6. Run readability/clean checks, inspect 44px targets and real hit ownership, and retain screenshots in the proposed `evidence_dir("program-creation")` namespace. Assert no unexpected mutations and zero `programs` rows in the isolated DB before and after. Always close contexts/browser and stop the local server in `finally`.

Prerequisites are not installed-readiness claims: full authorized checkout/backend dev dependencies; Node/npm plus web dependencies (build may run); Playwright plus usable Chromium at the actual cache; POSIX `fcntl`; writable temp/build output and `web/.glass-build.lock`; authority to bind a local test server. Missing or skipped Playwright is not success. No owner DB, real provider/agent or personal repository is needed.

After the new file exists, under the same isolated-HOME/cache/lock setup:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/e2e/test_program_creation_glass.py
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/e2e/test_program_creation_glass.py
```

Require non-skipped cases and inspected screenshots. These are source-defined command forms applied to a **proposed new target**, not commands already executed or proof the target exists.

### Final integration and UI proof

Source-defined supplemental checks: `npm --prefix web run typecheck` and `npm --prefix web run guard:architecture`. Run from the assigned root; retain failures. No token changes are planned, so do not invent a mandatory token-regeneration step.

The assigned integration owner uses the current [integrated gate](#integrated-gate), with the two existing Python files and the proposed browser file (once implemented) in documented `QUICK_TESTS` if affected selection would omit them:

```sh
DESK_SWEEP_SHOTS=1 QUICK_TESTS="tests/integration/test_desk_programs.py tests/integration/test_desk_program_from_action.py tests/e2e/test_program_creation_glass.py" scripts/quick_check.sh origin/main
```

That command is source-defined composition, unexecuted here. Do not wrap its internal lock. Revalidate actual comparison base, host/browser support and stage execution; no-change exit 0 and tolerated no-test selection are not passing proof. Inspect 1440/393 plus narrow-in-wide creation states. The generic sweep is not the specific new-well interaction proof. The separately scoped intercepted browser test must run; a missing/skipped case remains incomplete. Do not invent a passing result or silently broaden the E2E suite. Keyboard/focus/hit-target claims require appropriate observed evidence, not only a React mock.

## V42 Meeting-decision filing verification

**Conditional HS-S42 scope only.** Source definitions were inspected in the archive at `80b641fa41c7352280cfa52e933acf6dbe8d3857`. No application imports, tests, fixtures, builds or browser commands ran during planning. New targets, cases and fixture names are proposed. D19/G42, assigned execution authority and actual environment readiness remain prerequisites.

### Exact budget and ownership by task

| Task | Named focused targets |
| --- | --- |
| T42-02 creation outcomes | Proposed `tests/integration/test_meeting_decision_filing.py`; existing `tests/unit/test_decision_records_routes.py`; editable `web/src/desk/__tests__/deskDecisionRef.test.ts` |
| T42-03 meeting scope/receipt | Editable `web/src/desk/__tests__/philo1308Decide.test.tsx`, `decision.app.test.tsx`, `deskRemembers2.philo1307.test.tsx` (all in that same directory); proposed browser target below |
| T42-04 correction | Editable `web/src/desk/components/DeskFilingStrip.test.tsx` and `web/src/desk/__tests__/decision.app.test.tsx`; new producer's correction cases; unchanged `tests/integration/test_memory_desk_decision_ref.py` and `tests/integration/test_one_place_relationships.py` |
| T42-05 accepted-slice final proof | Union of applicable targets above plus proposed `tests/e2e/test_meeting_decision_filing_glass.py`, then current integration-owner gate |

There are eight existing suites and two proposed new test files in the full-story budget. Do not require all ten for each intermediate task. Correction-only scope uses its own cases and does not claim the creation journey complete. If task02 is not assigned, task04 owns creating the same proposed producer and required fixtures/browser cases; no unassigned task is an implicit dependency. Coordinate shared producer/app/browser files; a named source reference is not edit ownership.

### Actual producer, authority and fixtures

The existing bare canonical test in `test_decision_records_routes.py:56–91` proves a canonical/source response, not membership. Its anonymous bare-edge refusal is 400; do not mistake that for the full hub's anonymous 401. The old `test_desk_meetings.py::_decide` and `decision.app.test.tsx` mock path create legacy decisions. They are not proof of the revised meeting canonical path.

The proposed new integration file uses a real temporary HTTP hub following `tests/unit/test_philo5_the_loop.py::_boot` 130–166 and teardown 169–175: new `tmp_path/hub.db`, actual DB/observer/composition, real `MeetingWebServer` and an isolated authenticated owner TestClient. Apply current isolated-HOME and `glass_infra._boot` safety controls before constructing/importing the app. Reuse that bounded setup pattern; do not run the unrelated loop tests. Preserve real `PrimitiveService`, `DecisionRecordService`, `ProjectService`, operation registry and desk/project kernel. Seed only temporary projects/meetings. No model, recording, repository registration, Program, agent or external communication is needed.

Two proposed producer cases:

- `test_decision_filing_records_canonical_lifecycle`: real canonical POST (201), actual source/canonical identities and provenance, admitted canonical member PUT (200), relationship GET, canonical DELETE (200) and readback. Check operation/receipt identity and actual stored state. Seed source alias/KB/drawer edges independently; canonical removal must leave those and meeting/source provenance unchanged. Assert inherited visibility rather than falsely requiring disappearance.
- `test_decision_filing_records_refusals_and_replay`: real full-edge anonymous and ungranted-agent refusals, unknown project, invalid command, stale revision and command-key conflict. Use the isolated authenticated-agent precedent in `test_philo7_article_xi.py:115–125`; remove inherited owner token headers. Count only operations since each tested step, using its 66–100 pattern. A transport fault injected in an app test is not a real kernel refusal.

Source-established statuses: anonymous full edge 401 with no write/operation; authenticated agent without required Desk/Project grant 403 with refusal receipt; unknown project 404; invalid command 400; stale revision or command-key payload conflict 409. Verify actual current conditions before asserting them; do not weaken admission to fit a fixture. The canonical creation route mints fresh IDs and forwards no client create command key. Membership optional `command_id`/`expected_revision` are separate existing contracts. Test same-key member replay without a second effect and changed-payload conflict; after later deletion or a relationship-kind change, the old success receipt is historical and current membership must still be read. This does not claim the current UI sends a command key or that creation is idempotent.

**Canonical edge meaning (C42-15), within the same two proposed producer cases and existing helper/strip targets:** round-trip the exact canonical ref under `member`, then deliberately change the same row to `source`/`output`/`related` through real admitted commands. Assert one project/ref row with the actual current kind, rather than two memberships. A historical member command replay must return its original result without turning the newer relation back into member; current relationship GET governs reconciliation. Exercise DELETE's whole-edge meaning and `removed=false` separately from performed removal. This characterizes the backend, not permission for a frontend retry to convert/delete an edge. Feed those producer-derived variants to the accepted G42 UI branch; no generic re-create, refile or inverse toggle on a non-member/malformed/mismatched read. Retain the proposed four capture files, recording these bounded variants within their scenario envelopes; no additional module/capture path or global recorder is assigned.

Exact source: `holdspeak/services/project_service.py:list_resource_relationships` 600–612, `add_resource` 4626–4674 and `remove_resource` 4783–4791; `holdspeak/db/relationships.py` 65–85/189–221/255–262; `web/src/desk/components/DeskFilingStrip.tsx` 115–120/219–230. Existing `tests/integration/test_one_place_relationships.py:39–62` already reads a source-kind project edge alongside independent axes. `tests/unit/test_project_room_contract.py:641–663` proves original member receipt replay after a later output edit/removal, and `tests/unit/test_project_service_characterization.py:396–402` accepts custom source relations. The latter two are inspected counterevidence/reference only, not added V42 run/edit targets. No tests ran here. The proposed new canonical producer and consumer cases fill the identity/role composition gap, not a new backend behavior or a claim that the existing generic strip is universally wrong.

**Only four new owned wire outputs:** `web/src/desk/__tests__/fixtures/decision-filing/created.json`, `filed.json`, `removed.json`, `refused.json`. Store actual status/body plus relevant scoped roster/mapping/readback envelopes in these captures; retain relationships between source/canonical IDs. Assert semantic values independently of fixture shape. IDs/timestamps are not byte-deterministic. Delayed, malformed, lost-response and unavailable-read variants are labeled fault injection, not captured production incidents.

A small test-local recorder may follow `tests/integration/test_desk_programs.py:38–54`: write only under `HOLDSPEAK_WIRE_WRITE=1`, scrub the temp root to `/tmp/rig`, compare shape. This S42 recorder is proposed, not already present. Do not reuse the Program fixture directory, import its whole rig, run a global recorder or set `HOLDSPEAK_EVIDENCE_WRITE=1`.

Within the authorized task's isolated environment, first collect the new producer selection and confirm only these two cases and four output paths, then record that exact selection and inspect the diff:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/integration/test_meeting_decision_filing.py -k 'records_canonical_lifecycle or records_refusals_and_replay'
HOLDSPEAK_WIRE_WRITE=1 uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/integration/test_meeting_decision_filing.py -k 'records_canonical_lifecycle or records_refusals_and_replay'
```

These targets/cases do not exist until implementation. Recording belongs only to the task owning their writes; independent verification keeps both write flags unset. Any unexpected selected producer or modified fixture is a stop condition.

### Source-defined commands, plan-composed final invocation

The repository defines lock usage, pytest `-n 8 --dist worksteal`, focused Vitest `--maxWorkers=8`, typecheck and architecture checks. The wrapper below composes those definitions; it is not a repository script or an executed result. Use the actual authorized checkout/root, host browser cache and evidence path outside scratch HOME. Run only the accepted task subset during development; this is the full accepted-story union after its targets exist.

```sh
(
  set -euo pipefail
  : "${HS_PLAYWRIGHT_CACHE:?Resolve the actual host browser cache first}"
  : "${HS_EVIDENCE_DIR:?Set an absolute task-owned evidence path}"
  HS_REAL_HOME="$HOME"
  mkdir -p "$HS_EVIDENCE_DIR"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_PLAYWRIGHT_CACHE"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  unset HOLDSPEAK_WIRE_WRITE HOLDSPEAK_EVIDENCE_WRITE
  py_files=(tests/integration/test_meeting_decision_filing.py tests/unit/test_decision_records_routes.py tests/integration/test_memory_desk_decision_ref.py tests/integration/test_one_place_relationships.py)
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/python.log"
  (
    cd web
    uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 src/desk/__tests__/deskDecisionRef.test.ts src/desk/__tests__/philo1308Decide.test.tsx src/desk/__tests__/decision.app.test.tsx src/desk/__tests__/deskRemembers2.philo1307.test.tsx src/desk/components/DeskFilingStrip.test.tsx
  ) | tee "$HS_EVIDENCE_DIR/web.log"
)
```

Run source-defined `npm --prefix web run typecheck` and `npm --prefix web run guard:architecture`; no token redesign is planned. Record baseline, expected-red/new-case proof and final results separately. A shared-file change after validation requires renewed final proof.

### Bounded real-browser lane

**Proposed new file:** `tests/e2e/test_meeting_decision_filing_glass.py`. Reuse existing `tests/e2e/glass_infra.py` build/boot/readability/cleanup helpers and `evidence_dir("meeting-decision-filing")`. The parked `test_philo13_08_decide_glass.py` gives interaction references only: setup 96–124, local project/meeting 134–159, focus/44px targets 161–191, local creation 225–263 and cancellation 265–298. Its legacy refs/receipt assumptions and relative import are not a reason to restore or run it.

1. Use the existing `_ensure_build` and isolated `_boot` 199–331 with all current machine/provider probes disabled, redirected HOME/DB/key stores and no owner credentials. The default recording route is unavailable, not a real microphone. No summary generation, agent/Program start, Send, provider setup or remote service may be invoked. `HOLDSPEAK_PROGRAMS=off` alone is not a mutation firewall.
2. Seed temporary projects/meetings only. Before navigation, install a test-local request guard admitting only the exact expected canonical creation, canonical membership commands and required setup/window operations. Source KB/drawer mutation is admitted only for an explicitly tested axis. Enumerate actual request methods/paths from supported setup; no blanket `/api/**` allow. `hubWindows.ts:80–100` describes window persistence, not draft syncing. Fail on unexpected mutation/egress.
3. Real canonical decision/member writes in this isolated hub can prove the complete local path. Test visible single/multiple/no/unavailable context, cancel before create, one Save, receipt, close/reopen, same-ID filing recovery, canonical correction and unchanged source axes. Count actual created records/operations. Inject a lost member response only on that exact request (for example `route.fetch` then suppress the response), then read/reconcile without replaying creation. Label injected faults explicitly.
4. Observe 1440 and 393 plus a genuinely resized narrow window on a wide Desk. `tests/e2e/test_frame_glass.py:674–684` demonstrates `.desk-window-grip` dragging and rectangle checks; inspect the actual meeting/decision frame before choosing a selector. Do not force CSS width. Check keyboard focus/Escape, real hit ownership/44px targets, readable/clean states and inspected screenshots. Microphone custody may use a fake browser media/recognized-input seam; focus alone is not speech/audio proof and no physical mic is authorized.
5. Inspect actual source/canonical/member/kernel state; always close browser contexts and stop the test server in `finally`. Cover pending create/timeout → close/reopen/reload retaining unconfirmed attempt state without invented IDs or automatic/generic create retry. Same-browser reload receipt recovery is conditional on successful workspace storage. Storage loss/crash/cross-device custody and exactly-once creation are not proven by this lane.

Prerequisites remain unverified: full authorized checkout/dependencies, Node/npm/web build dependencies, installed Playwright/Chromium at the actual cache, writable temp/build lock/output, POSIX `fcntl` and local-server permission. Missing/skipped tests are not a pass. Under the same isolated HOME/lock setup, after the target is implemented:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/e2e/test_meeting_decision_filing_glass.py
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/e2e/test_meeting_decision_filing_glass.py
```

The integration owner runs the current [integrated gate](#integrated-gate), adding only required exact Python targets to `QUICK_TESTS` if affected selection omits them. For full accepted S42, the proposed command is:

```sh
DESK_SWEEP_SHOTS=1 QUICK_TESTS="tests/integration/test_meeting_decision_filing.py tests/unit/test_decision_records_routes.py tests/integration/test_memory_desk_decision_ref.py tests/integration/test_one_place_relationships.py tests/e2e/test_meeting_decision_filing_glass.py" scripts/quick_check.sh origin/main
```

Revalidate base/platform prerequisites and actual stages; do not nest the lock. No-change exit 0, tolerated no-test selection, generic sweep images or skipped new browser cases do not establish accepted-slice completion. Require actual focused producer/app/browser results after the final edit, then independent review and a separate shipping decision.

## V12 Focused-navigation verification

**Conditional HS-S12 branch only.** Pinned source, declarations, selected tests and active browser targets were read at `80b641fa41c7352280cfa52e933acf6dbe8d3857`; no application collection/execution/build/browser ran. Proposed new cases, fields and the new browser file are not implemented. G-OPEN, the current supported-caller closure and assigned execution environment remain gates.

### Owned tests and focused subsets

Use per-task subsets, then the affected final union. Removing a shared registration export can affect test seams beyond the two main files; do not hide those behind an artificially small budget.

| Subset | Exact existing paths (repository-relative) |
| --- | --- |
| Task02 state/dispatch | `web/src/desk/__tests__/shell.test.tsx`; `web/src/desk/__tests__/surface-windows.test.tsx` |
| Task03 startup and exact target | `web/src/desk/DeskApp.test.tsx`; `web/src/routes.test.ts`; `web/src/desk/__tests__/projectRoomKey.test.ts`; `web/src/desk/needs/__tests__/NeedsDrawer.test.tsx`; `web/src/features/project-room/__tests__/room.app.test.tsx` |
| Task03 active compatibility seams | `web/src/desk/__tests__/settings.app.test.tsx`; `web/src/desk/__tests__/menus.app.test.tsx`; `web/src/desk/__tests__/verbRegistry.test.ts`; `web/src/desk/__tests__/settle.test.tsx`; `web/src/desk/pullouts/__tests__/note.app.test.tsx`; `web/src/desk/components/DeskArrival.test.tsx`; `web/src/desk/components/DeskMenuBar.test.tsx`; `web/src/desk/components/window/Dock.test.tsx`; `web/src/features/project-room/door/__tests__/newProject.app.test.tsx` |
| Conductor/Drawer/Dock behavior | `web/src/desk/conductor/__tests__/conductor.test.tsx`; `web/src/desk/__tests__/conductor.app.test.tsx`; `web/src/desk/drawer/__tests__/drawer.test.tsx`; `web/src/desk/chair/__tests__/chairWindows.philo1311.test.tsx` |
| Unchanged read/lazy fences | `web/src/desk/__tests__/phonepass.philo17.test.ts`; `web/src/runtime/__tests__/freshBuild.test.ts` |

The first four rows are editable only for accepted new cases or genuinely registration-dependent harness migration; do not rewrite unrelated assertions. The final two files are read-only regression proof. If the current closure finds further supported consumers, report and obtain the smallest owned-path amendment. The separately parked `web/src/desk/__tests__/_parked/settings.app.test.tsx` is not an active passing suite or automatically an approved restoration.

**No fixture writes are planned.** Room tests already use recorded `P172_ROOM_BEFORE`, `P172_PROPOSALS`, `DRAFT`, `PUT` and other room-wire fixtures. Conductor app uses existing `wire/hubWire.ts` recordings (`coders-sessions.c4`, `onboarding-agents.isolated`, `lane.c4-runbook`), whose producer is `tests/integration/test_desk_agents_wire.py`. Keep them unchanged; fixture shape cannot replace the exact target/effect assertions. A changed wire protocol/fixture requires a new scoped producer plan, not broad recording.

### Source limits and necessary added cases

- Existing shell coverage flushes one pending request. Add accepted same-key and distinct-key command order, admitted recovery subsequence, staged precedence and alternating storage success/failure. The old reset clears Maps but not pending/staged resources: explicitly isolate every transient/storage path.
- Existing surface coverage checks one staged arrival, aliases/recovery and normalization. Add retained off-glass reveal, recovery→normal staged retention, repeated mode/mount/unmount and stale cleanup. Assert transient fields are absent from workspace serialization **and** hub window payloads.
- DeskApp currently mocks SurfaceWindows. Retain its selection tests but add a real-host boundary case; mock prop equality is not full readiness/reveal proof.
- Current Conductor opens/raises on explicit open, but `showFromHub` preserves seating. Its delayed restore means FIFO dispatch is not a cross-family focus guarantee. Do not stub away the action under test to make an order assertion pass.
- The compact Dictate test distinguishes explicit Dock origin from no origin. Current phone manifest instead has a Capture tile; preserve both facts. Do not hijack the Dock's already-running/minimized restore branch.
- Needs You and Room tests cover exact proposals, no additional PUT during pending/failed update Save, newer drafts and repeated reveals. Count writes before/after navigation, not zero total when an earlier explicit Save is allowed to complete. Add absence of navigation-triggered Confirm/publish/Send. Unavailable/settled target behavior is characterization unless separately accepted.
- `phonepass` covers mounted read/late-slot registration; `freshBuild` asks for build refresh and still throws failed lazy loads. Keep them unchanged. Neither mechanism is retired with the opener registry.

The source-only dependency check followed static local value imports/reexports from Desk, Conductor and Drawer store roots and found no static path back to shell. It excluded type-only/dynamic edges, assets, package internals and runtime initialization. A shell→Chair import has a concrete return path and is outside the plan. Revalidate the actual changed graph and startup tests; a text-only check is not runtime or whole-product compatibility proof. Run any executable graph walk only under current repository lock/role instructions, not as an unassigned read-only action.

### Navigation and People landing-order gate

**Conditional integration ownership, not a new prerequisite or approved execution.** S12's opener cutover and S43's normal People entry can be assigned independently. Their later combined acceptance must preserve the already-landed behavior, not the pin's registration mechanism. S33 is independently assignable too; it does not grant navigation a durable private receipt. Use the actual predecessor completion report, current source and accepted local gates, not an assumed implementation order.

- **If S43 lands before S12:** T12-01 records the added no-scope `openSurfaceOr("open-people", "/")` caller and its actual-host proof; T12-03/04 retain that contract through the cutover. `NeedsDrawer.test.tsx` and `surface-windows.test.tsx` are already in V12. The conditional additional **read-only regression target** is `web/src/desk/__tests__/people.app.test.tsx`, which V43 owns for actual Needs→People host proof. When landed S43 is present in the later S12 baseline, this target must be explicitly included in that assignment before combined acceptance; standalone S12 with no landed S43 does not acquire it. An assignment that omits the inherited proof needs that bounded amendment before the combined state can be accepted. If that inherited test harness requires migration, obtain a bounded owned-path amendment before editing it; do not replace it with a mock opener, drop its assertions or restore the old registry to make it pass. No capture regeneration is included.
- **If S12 lands before S43:** T43-01/02 use the actual accepted shell compatibility/admission contract and current SurfaceWindows host. In S43, “registered” describes the pin only, not an architectural invariant. Verify the ready/admitted warm/cold destination through the same no-scope public entry and actual body; do not reintroduce `registerSurface` or a test-only callback owner. Preserve the fallback/disallowed/deferred meaning accepted under G-OPEN. A changed interface or a required forced person/lens/roster reset needs a local gate amendment; it is not a routine test update.
- **If S33 is already present in either baseline:** preserve its same-person/same-mount receipt, actual-person change and protection-clearing limits; record which inherited assertions cover the changed host path. A restored window or saved People place is not a restored receipt. `SurfaceWindows.tsx` passes `unmountOnMinimize` (252), and `DeskWindow.tsx:1201–1202` returns no core while minimized; recovery can also withhold the host. G33-A's in-memory receipt therefore cannot promise continuation across those unmounts. Do not persist private receipts, keep cores alive or auto-accept to make navigation appear seamless. Any additional composed S33 proof or file ownership beyond the assigned budgets must be named before execution, not assumed from the shared People suite.

**Stable S43 CTA proof contract:** no forced person/project/lens scope or reset, truthful readiness/fallback, actual People content, and preserved transient local state while the same core/pane remains mounted. The CTA adds no navigation-triggered request/accept/Done/Nudge/Note/Send. Explicit scoped navigation elsewhere keeps its own accepted behavior. After full unmount, existing saved place/drafts and unknown-effect handling retain their separate contracts. Test evidence must distinguish a mounted instance, minimized/restored instance, recovery-withheld instance and a fresh mount; an existing window ID is insufficient. This does not require a new case for every state in every task: the later owner identifies the already-covered assertions and the smallest missing affected case before accepting the combined scope.

**Pinned anchors:** `web/src/desk/shell.ts:openSurfaceOr` 116–123; `components/SurfaceWindows.tsx` 137–175/252; `components/DeskWindow.tsx` 1201–1202; `store/compositorSlice.ts:openSurfaceWindow` 537–577 (those three paths are relative to `web/src/desk/`); `web/src/pages/cores/PeopleCore.tsx` 211–240/351–382 (local state, scoped selection and saved-person restoration). This is source inspection, not observed preservation after a cutover.

For an accepted S43-first combined assignment, append `files+=(src/desk/__tests__/people.app.test.tsx)` to the existing V12 recipe after its `files=(...)` line and before the locked Vitest invocation. Use the same isolated HOME/cache, recording-off setup and evidence log; no second unbounded suite or nested lock. The path and command form are source-verified, but the added later-slice run and its results are proposed/unexecuted. S43's existing V43 union already contains this target and `surface-windows.test.tsx`; do not duplicate that budget or its capture writer. Serialize shared harness changes, then let the later slice's independent reviewer check the current combined state. A new failure returns to its actual owner, not a guessed global sequencing dependency.

### Commands: definitions verified, invocations not run

Reuse [setup/isolation](#setup-and-isolation): assigned checkout, current instructions, isolated HOME, actual host Playwright cache, task-owned evidence path, pipefail and machine-wide lock. Source-defined focused web form, from `web/`:

```sh
uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 <exact web-relative files from the accepted subset>
```

For task02, the concrete command inside that environment is:

```sh
uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 src/desk/__tests__/shell.test.tsx src/desk/__tests__/surface-windows.test.tsx
```

For the standalone accepted S12 union (plus the explicitly assigned conditional target above when applicable), the following is **plan-composed** from source-defined commands and verified existing paths. Run from the assigned root; retain the command and actual run counts, skips, logs and exit status:

```sh
(
  set -euo pipefail
  : "${HS_PLAYWRIGHT_CACHE:?Resolve the actual host browser cache first}"
  : "${HS_EVIDENCE_DIR:?Set an absolute task-owned evidence path}"
  HS_REAL_HOME="$HOME"
  mkdir -p "$HS_EVIDENCE_DIR"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_PLAYWRIGHT_CACHE"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  unset HOLDSPEAK_WIRE_WRITE HOLDSPEAK_EVIDENCE_WRITE
  cd web
  files=(src/desk/__tests__/shell.test.tsx src/desk/__tests__/surface-windows.test.tsx src/desk/DeskApp.test.tsx src/routes.test.ts src/desk/__tests__/projectRoomKey.test.ts src/desk/needs/__tests__/NeedsDrawer.test.tsx src/features/project-room/__tests__/room.app.test.tsx src/desk/__tests__/settings.app.test.tsx src/desk/__tests__/menus.app.test.tsx src/desk/__tests__/verbRegistry.test.ts src/desk/__tests__/settle.test.tsx src/desk/pullouts/__tests__/note.app.test.tsx src/desk/components/DeskArrival.test.tsx src/desk/components/DeskMenuBar.test.tsx src/desk/components/window/Dock.test.tsx src/features/project-room/door/__tests__/newProject.app.test.tsx src/desk/conductor/__tests__/conductor.test.tsx src/desk/__tests__/conductor.app.test.tsx src/desk/drawer/__tests__/drawer.test.tsx src/desk/chair/__tests__/chairWindows.philo1311.test.tsx src/desk/__tests__/phonepass.philo17.test.ts src/runtime/__tests__/freshBuild.test.ts)
  uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 "${files[@]}" | tee "$HS_EVIDENCE_DIR/web.log"
)
```

Run `npm --prefix web run typecheck` and `npm --prefix web run guard:architecture` from the root. No token/theme change or eager-loading rewrite is planned. Missing/extra consumers must not be made invisible with allowlists. Do not substitute an unbounded frontend suite for the named cases.

### Active browser proof and proposed new target

Existing source-verified active node IDs:

- `tests/e2e/test_desk_sweep.py::test_every_html_route_loads_clean`
- `tests/e2e/test_meetings_glass.py::TestOneMeetingOneWindow::test_one_meeting_opens_in_one_window_from_every_door`
- `tests/e2e/test_dock_glass.py::TestDockTap393::test_a_tap_on_a_paged_dock_presses_that_icon_393`

The first observes actual routes/windows and late errors, not the registry marker. The generic every-window sweep opens through the hub API and can bypass shell; it alone does not prove replacement. Meetings uses injected fake capture and checks one scoped window. Dock covers actual phone tiles (including Capture and Agents), not a supposed phone Speak tile. The explicit registry-marker wait found in `tests/e2e/_parked/test_hs144_door_glass.py` is historical, not current active proof.

**Proposed new owned browser file:** `tests/e2e/test_navigation_readiness_glass.py`, task03 creates and task04 reviews/runs. Use existing `glass_infra`/evidence helpers, not a new harness or restored parked test. This is an allowed new file only in an assigned implementation lane; it does not exist in the source pin.

Its cases must cover cold route with scope/query preserved; initial and reopened recovery; admitted alias reveal of retained windows; staged arrival held until normal readiness; valid/invalid/throwing/alternating storage; remount without same-runtime replay; actual warm and repeated project-proposal reveal with editor draft custody; and target rendering after readiness. Use the app's real shell entry paths, not only hub window POSTs or a test-only dispatcher injected into production. If a pre-readiness multi-request sequence cannot be driven at that layer, keep its deterministic proof in the focused state tests and state that limit instead of claiming browser coverage.

Use a temporary isolated hub, current `_boot` safety controls and fake capture. Allow only enumerated local setup/window/project/meeting fixture operations needed by these cases; block unexpected agent/Program starts, Send, proposal Confirm, update publish, provider setup and egress. An explicitly seeded/in-flight update Save may complete, so assert navigation adds no new mutation rather than zero writes. Query/token values are test-only and must stay on the isolated origin. No physical mic, owner HOME/DB/Keychain, live services or real external sends are needed.

Inspect 1440×900, 393×852 and narrow-in-wide actual target geometry/focus/hit ownership. Use the existing frame-resize pattern from `tests/e2e/test_frame_glass.py:674–684`; do not force CSS width. Wait for the actual target/content, not `data-settled` or navigation marker alone. Save shots with proposed `evidence_dir("navigation-readiness")`, inspect them and always close context/browser/server in `finally`. Unsupported/settled target and cross-family final focus remain explicitly characterized unless their new policy was accepted.

The existing browser suite loads manifest code during collection through Node, and `_ensure_build` can build. **Collection is application execution**, not a source-only check. After assignment and implementation, use the isolated environment and lock to collect/run the exact new file and the three verified existing nodes:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/e2e/test_navigation_readiness_glass.py tests/e2e/test_desk_sweep.py::test_every_html_route_loads_clean tests/e2e/test_meetings_glass.py::TestOneMeetingOneWindow::test_one_meeting_opens_in_one_window_from_every_door tests/e2e/test_dock_glass.py::TestDockTap393::test_a_tap_on_a_paged_dock_presses_that_icon_393
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/e2e/test_navigation_readiness_glass.py tests/e2e/test_desk_sweep.py::test_every_html_route_loads_clean tests/e2e/test_meetings_glass.py::TestOneMeetingOneWindow::test_one_meeting_opens_in_one_window_from_every_door tests/e2e/test_dock_glass.py::TestDockTap393::test_a_tap_on_a_paged_dock_presses_that_icon_393
```

A full checkout, installed backend/web dependencies, usable Playwright/Chromium/cache, writable temp/build lock/output, POSIX support and local-server authority remain unverified prerequisites. Empty/skipped selection is a blocker. Do not run metal tests or enable evidence-writing flags.

The integration owner then uses the current [integrated gate](#integrated-gate), with the proposed new browser file in `QUICK_TESTS` if affected selection would omit it:

```sh
DESK_SWEEP_SHOTS=1 QUICK_TESTS="tests/e2e/test_navigation_readiness_glass.py" scripts/quick_check.sh origin/main
```

Revalidate actual base/platform cache and actual stages; never nest its lock. The three exact preservation nodes above must have their own observed results even if another sweep passes. No-change exit 0, a skipped target or uninspected images do not establish accepted-slice completion. Final proof follows the last edit and independent review; shipping remains separate.

## V32 Delivery-recovery verification

**Conditional HS-S32 first branch only.** Repository paths/definitions were inspected at `80b641fa41c7352280cfa52e933acf6dbe8d3857`; current official CLI documentation was checked separately on 3 November 2026. No application import, collection, test, Git operation, build or browser was run. New metadata, request fields, tests/fixtures and behavior remain proposed. G32, installed command support and the execution assignment remain gates.

### Exact source and ownership map

| Existing repository path / anchor | Contract to inspect | Ownership |
| --- | --- | --- |
| `holdspeak/services/program_delivery.py` · `DeliveryFailed` 51, `pending` 79, `deliver` 128, `merge` 159, `_line` 182, `_write` 213, `turn_item` 268, `decide` 288 | Newest delivery ledger, handled stages, lossy create return, phase loss on merge failure, Retry versus known PR | Task02; preserve evidence allowlist and existing checkpoint choices |
| `holdspeak/services/program_service.py` · `_deliver_once` 1020, `decide/_decide` 2653–2686, `changed` 5022 | Owner admission, current process-local RLock, expected binding forwarding and independent Program Done | Task02 only delivery branch/signatures; no general service split |
| `holdspeak/web/routes/programs.py` · decide route 214–223 | Existing POST forwards principal/kind/choice, no expected receipt yet | Task02 additive delivery binding; no new endpoint |
| `holdspeak/db/programs.py` · `add_checkpoint` 235–251, `list_checkpoints` 271–301; `holdspeak/db/connection.py` · `ConnectionCache.connection` | Integer checkpoint IDs, newest ID order, optional undo JSON; commit on successful connection-context exit | Read-only; no schema or history rewrite |
| `holdspeak/services/program_runner.py` · injected run 151–184, default timeout 69/126–135, `_git` 245, step merge 2278 | Current subprocess seam, 120-second default, swallowed Git failure, separate step-follow-through behavior | Read-only; no second subprocess site or runner lifecycle rewrite |
| `holdspeak/delivery/pr_receipts.py` · `view_pr` 488, `list_branch_prs` 520, `_row` 414, `pr_state` 146 | Registry-specific precedent, bounded/limited reads, unknown-state coercion unsuitable for proof | Read-only; Program does not necessarily have required source ID |
| `holdspeak/delivery/registry.py` · `normalize_git_url` 67 | Credential-free repository identity precedent | Read-only; do not persist raw credential-bearing origins |
| `web/src/desk/programs/ProgramWindow.tsx` · verbs 86–102, press 200–228, `DeliveredLine` 641–650 | Check must be a declared verb; send displayed binding; no false Delivered | Task03 |
| `web/src/desk/programs/types.ts` · `YourTurnItem` 398–436, `DecideBody` 627–635; `web/src/desk/programs/api.ts` · decide 74–77 | Additive typed projection/request; raw undo is not a declared checkpoint UI field | Task03 |
| `holdspeak/services/brief_words.py` · delivery happened/question/consequences/results 282/365/448/472 | Correct words for Check, queued/unknown, Merge request and Skip | Task03; preserve unrelated language |
| `holdspeak/services/briefing_service.py` · labels 156, frozen composition 505–516, direct `decide_item` 713–739, `_answer` 989–994, `_decide_args` 1025–1038 | Frozen displayed binding, never fresh-ID substitution; direct unbound recovery refusal | Task03; no generic page lifecycle rewrite |
| `holdspeak/sdk/programs.py` · decide 67–74; `holdspeak/commands/program.py` · parser 45–53/dispatch 119–127; `holdspeak/mcp/families/program.py` · schema 375–395/handler 523–527 | Forward optional expected binding or produce accepted explicit refusal | Task03; authority unchanged |
| `holdspeak/mcp/tool_authority.py` · 347; `holdspeak/kernel/program_ops.py` · 95–111 | Authority classification; kernel record is not an external transaction/idempotency key | Read-only |

**Proposed protocol:** an optional positive-integer `expected_delivery_checkpoint_id` on the existing decision request, projected from the current held delivery row and frozen into newly composed briefing content. The accepted first branch requires it for Check/Retry/Merge/Skip because each can append history or effects. Missing/stale values refuse before effects; other decision kinds remain unchanged. The name is proposed, not source-existing. Direct channel callers without the displayed binding must not replace it with a fresh lookup. Old rows remain readable; legacy identity/binding restrictions are a G32 compatibility decision.

### Provider command contract, not an executed command

The official [PR view manual](https://cli.github.com/manual/gh_pr_view) documents an explicit URL target and JSON fields including URL, number, state, head/base and merge information. The [merge manual](https://cli.github.com/manual/gh_pr_merge) documents a head-commit condition and notes that merge-queue branches may queue a request rather than immediately merge. Installed version/field behavior remains unverified.

A proposed adapter may construct a URL-targeted JSON read and a URL-targeted squash merge with `--match-head-commit <recorded SHA>` through the existing injected runner. These are new implementation choices, not current commands. Verify supported flags without contacting a remote, fail closed if absent, and keep test execution entirely fake. Do not use no-argument/current-branch selection, `--admin`, `--auto`, branch deletion or a list-by-branch fallback.

The provider condition binds the **head**, not an atomic full repository/base/fork snapshot. Explicit canonical URL identifies the PR; base/fork and other identity facts are read-time checks. State this remaining race/limit honestly rather than claiming a transactional full-identity lock. G32 must accept that boundary or select a separately verified stronger provider operation.

Check budget: one bounded read, no mutation commands. Recovery Merge budget: fresh read, at most one head-conditioned merge, confirming read. Read error/timeout/malformed response stays unknown. Exit zero with open/queued result is not Delivered. Retain a merge-requested/uncertain marker after any unconfirmed merge attempt; later Check must not casually reoffer Merge or resend it. Clearing that marker requires a separately specified proof/owner resolution, outside this first branch. This conservative rule can leave failed initial Normal/YOLO merges Check/Skip until externally resolved, which G32 must explicitly accept. No live polling/retry process is introduced. For every owner-initiated known-PR Merge, including fresh Secure, commit an owner-requested/unconfirmed `kind="delivery", choice="pr_open"` checkpoint before the command. An append failure issues zero merge commands; a later outcome-append failure leaves the committed barrier. Every observation/error row retains its marker until confirmed merged. After interruption before command, Check/Skip remains truthful even if no request reached GitHub. This is a new bounded G32 contract, not the initial delivery implementation or a cross-process claim.

### Focused proof budget

| Owner | Exact files | Status / purpose |
| --- | --- | --- |
| Task02 | `tests/unit/test_program_delivery_recovery.py` | **Proposed new** pure recording-runner/state/identity tests; no real subprocess in this layer |
| Task02/03, serialized | `tests/integration/test_program_delivery.py`; `tests/integration/program_rig.py` | Existing route/ledger producer and fake implementation; fake file is not a standalone collected test |
| Task03 adapters/words | `tests/unit/test_program_cli.py`; `tests/unit/test_sdk_programs.py`; `tests/unit/test_brief_in_his_terms.py`; `tests/unit/test_program_window_words.py`; `tests/unit/test_calls_decide.py` | Existing suites; extend only binding/blocked-delivery or affected wording cases. MCP schema/handler cases belong to the proposed recovery unit file, not unrelated `test_program_family.py` |
| Read-only regression proof | `tests/unit/test_program_answer_once.py`; `tests/integration/test_calls_program_decide.py`; `tests/integration/test_program_run.py` | Existing one-answer/non-delivery Calls and shared fake/runner contracts; a failing preservation test requires diagnosis, not silently expanded edits |
| Task03 web | `web/src/desk/programs/__tests__/programs.app.test.tsx` | Existing delivery fixture tests 540–576; add real button/request/receipt/error cases |
| Task03 browser | `tests/e2e/test_program_delivery_recovery_glass.py` | **Proposed new** isolated real UI with intercepted Program requests and producer-derived responses |

The ten Python test targets comprise nine existing files plus one proposed file. The shared rig is an additional explicitly owned helper, not an eleventh test target. Task02 initially runs its new unit and delivery integration suites; task03 runs the affected named consumer subset; task04 records the final union and actual selection. Avoid unrelated broad sweeps.

**Real-local versus fake boundary:** `program_rig.git/make_repo` execute Git, create a temporary repository/bare origin, configure a GitHub-shaped URL rewrite to that bare path and push locally. FakeHand/FakeAgent create worktrees/commits. Delivery `_rails` copies and executes the repository's actual `.githooks/dw`/`dw_pmo`. FakeGitHub does not perform real GitHub merge integration; it currently assumes number-targeted successful merge and cannot handle new view/URL/conditional-head cases without extension. All gh calls must remain fake and unsupported variants must fail closed. Isolated HOME alone is not network isolation; inspect the current rig and assert every remote is local before any Git/DW execution. No real owner repository, credentials, installed gh fallback, model, microphone, Send or provider effect is allowed.

**Skip truth boundary, proposed G32 choice:** at the pin, `program_delivery.py:302–303` appends only a local skipped line; `pending` 79–81 and `turn_item` 267–284 then suppress automatic delivery and the held turn. It does not read or cancel provider work. `brief_words.py:448–473` nevertheless uses unconditional “Done, not delivered” consequences/settled text; `settle_words` 493–499 and `briefing_service.py:_item_state` 784–802 select that result from kind/choice rather than external confirmation. Existing `tests/integration/test_program_delivery.py:135–156,183–202` proves the words only for a known pre-remote DW refusal, not a queued/unconfirmed request. This is a planning contradiction, not an observed live misdelivery.

Under the accepted G32 Skip distinction, task02/03 extend the already-owned delivery integration producer, affected brief-word suites and window app test: compare known no-effect Skip with queued/unconfirmed-result Skip; assert zero provider commands for the press, no automatic recheck, local terminal Skip/Program Done, removal of the held turn, and the visible unresolved observation plus any acknowledged safe PR identity without false “not delivered” or cancellation. Include the settled briefing result, not just its pre-press consequence. Prior identity/observation display and any additive representation stay subject to G32/task02 review; no new schema is mandated. Use the existing queued/unknown producer responses and existing consumer scope, with no ninth fixture output, eleventh Python target or extra browser/capture lane. Do not add a post-Skip provider read to establish these assertions.

Also test closed-Program delivery-target change with the same latest delivery-row ID. Current update may write only a plain checkpoint; the binding alone does not detect that drift. Known-PR words/effects retain recorded original target/phase; preparation Retry refuses drift, and the Program is re-read under the decision lock.

C32 requires command-count **negative proof**, not just return values. Inject fail-before-effect, recorded-effect-then-error, raised timeout, malformed response, wrong repo/same number, fork/base/head mismatch, stale receipt, queued result and missing post-read. Preserve initial rule tests. Prove owner-Merge marker-before-command, failed pre-command append, reconstruction before command, failed post-command append and marker retention through Check/error. Do not call deterministic reconstruction a process-kill test. Initial automatic and full preparation-Retry paths still have unclosed post-effect crash/escaping/append-failure windows. An older server ignores the marker, so safe rollback requires a reviewed refusal guard or holding downgrade, not merely readable optional JSON.

### Review-to-delivery integration gate

**Conditional joint proof, not a new prerequisite or shared merge policy.** Use this gate only when G25-A and G32 are accepted and a joint S25/S32 proof is explicitly assigned. Independently implemented slices keep their own budgets and exits. T32-02 owns the bounded case in existing `tests/integration/test_program_delivery.py`; coordinate its existing `program_rig.py` helper with T25-03's accepted opt-in real receipt/observer path. T32-04 verifies it after both slices' final edits; T25-04 supplies its admission/producer report. No new production owner, test target, fixture output or browser case is added. Both focused unions still run when jointly assigned; this one case does not replace them.

**Pinned crossing and present proof gap:** `program_runner.py:_pr` 2164–2219 treats an observed terminal outcome before review eligibility; `merge` 2278–2305 writes the step's request marker after the command. `program_service.py:your_turn` 581–588 adds Secure owner Close, and `program_state` 833–855 returns waiting while that turn exists. `changed` 5022–5050 computes state from all applicable steps/requirements and handles automatic closure where control permits; Secure `close` 2939–2953 calls `changed`. Computed Done **and** `closed_at` allow `_deliver_once` 1020–1031. `program_delivery.py:_write` 213–266 creates a separate delivery worktree/branch and DW evidence PR. These relative filenames are under `holdspeak/services/`. Existing `test_program_person_review.py:24–53` has no delivery target and uses normalized fake follow-through; `test_program_delivery.py:_done` 80–95 uses an ordinary non-person step and default fake sweep. Passing those cases separately is not proof of this crossing, nor evidence that it currently fails.

In the assigned existing integration file, reuse `_rails` and the opt-in fake-gh → real `PrReceiptsService` → real `FollowThroughObserver` → launch ledger path described in [V25](#v25-current-person-review-verification):

1. Create a Secure, delivery-configured Program with a person-gated step and an owner-word requirement. Apply raw approval while held, then newer requested changes, then clear the other hold. Assert no step merge, no manufactured closure, and no final-delivery worktree/DW/commit/push/create/merge. Counts must distinguish ordinary step setup from the later delivery phase.
2. Return corrected work through the existing same-branch/same-PR flow: requested changes can transition the step to working (`_person_changes` 2221–2252), and completed checked/reviewed work returns via `pass_gate` 2009–2022. Approval alone does not make a working step mergeable. Apply qualifying newer raw approval, satisfy applicable requirements on that work, and use the existing explicit owner **step** Merge. Model an accepted request while its PR remains open: the step's `merge_requested_at` is not a merged receipt, Program Done or delivery permission. Then deliver an actual matching merged observation through the real receipt/observer chain. With all Program end checks satisfied, assert finished steps, Program waiting on Close, absent `closed_at` and no final delivery before Secure owner Close. A later unavailable review must not erase this actual terminal outcome.
3. Use the actual owner Close → `changed` → `_deliver_once` chain; assert Program Done/closed after that transition. Assert a **different** delivery PR, branch and Program-level `kind="delivery"` checkpoint. The step approval/history/request marker neither admits nor suppresses this operation. Its artifact remains the existing allowlisted DW Done record and PR references, not a copy or independent proof of step implementation. Do not add raw reviewer payloads, private alias rosters, briefs or transcripts to that projection; this does not sanitize arbitrary owner-written content in already-allowed requirement lines. Secure final delivery still needs its own owner press.
4. Exercise G32's displayed **delivery** checkpoint binding: missing/stale binding makes no provider command; accepted fresh owner Merge commits its delivery request barrier before the fake command. Queued/unavailable confirmation stays Check/Skip, retaining the barrier through reconstruction and Check. Matching confirmed merge settles only delivery. Count zero repeated step/agent work and zero repeated delivery DW/commit/push/create on known-PR recovery; Program stays Done and phase/history facts remain truthful.

Use the V32 isolation and command recipes below; the case is collected through the already-listed delivery integration suite. Serialize shared-rig edits and give each V25/V32 command union a separate absolute evidence directory so identically named logs cannot overwrite each other. Raw provider data, receipt quality, actual stored state and separate per-operation command counts are required; manually setting Done, review metadata or a delivery checkpoint is not the only composed proof. The fake must distinguish step and final PR identities and support pending/queued outcomes without falling back to real gh. This is deterministic producer/consumer evidence with real temporary local Git/DW, **not** actual GitHub merge integration, process-kill, concurrency or live branch-protection proof. Initial automatic/preparation-Retry receipt gaps remain outside the accepted contract.

For joint rollback, inspect S25's unfinished person gates and S32's unconfirmed delivery markers separately. Safe state in one population does not make the other safe for older code; apply their existing hold/refusal requirements independently. No new recovery owner, remote undo or history deletion is implied.

### Exact fixture outputs

Existing owned outputs under `web/src/desk/programs/__fixtures__/`:
- `program.delivery_failed.json`
- `program.delivery_merge.json`
- `program.delivery_merged.json`

Proposed new outputs in that same directory:
- `program.delivery_check.json`
- `program.delivery_checked_open.json`
- `program.delivery_unknown.json`
- `program.delivery_queued.json`
- `program.delivery_legacy_blocked.json`

Task03 records these **eight** files only through the extended real route producer in `tests/integration/test_program_delivery.py::_fixture`. Do not type fixture truth manually. Existing shape comparison does not prove value semantics; assert actual choices, expected ID, safe PR target and recovery state in the producer and consumer. No global wire refresh or `HOLDSPEAK_EVIDENCE_WRITE` is permitted. Inspect the diff for unrelated outputs after recording.

### Commands: source-defined form, proposed invocations

Use [setup/isolation](#setup-and-isolation), actual current instructions, assigned isolated checkout, HOME/cache and machine-wide lock. These future commands are **plan-composed** from source-defined scripts and verified paths; no installed dependencies, collection or passing results are established. Collection may execute application code and needs the same authority/isolation.

From the assigned repository root inside the isolated environment, task02 focused example:

```sh
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/unit/test_program_delivery_recovery.py tests/integration/test_program_delivery.py
```

Final Python union (collect first using `--collect-only`, then run with that flag removed):

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/unit/test_program_delivery_recovery.py tests/integration/test_program_delivery.py tests/unit/test_program_cli.py tests/unit/test_sdk_programs.py tests/unit/test_brief_in_his_terms.py tests/unit/test_program_window_words.py tests/unit/test_calls_decide.py tests/unit/test_program_answer_once.py tests/integration/test_calls_program_decide.py tests/integration/test_program_run.py
```

After the producer/fake is implemented and its wire-write scope is verified, task03's explicit recording command is:

```sh
HOLDSPEAK_WIRE_WRITE=1 uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/integration/test_program_delivery.py
```

Then unset the flag and rerun normally; inspect all eight authorized fixture diffs and any unexpected changes. Run the same producer without write mode as part of final proof. For the web consumer from `web/`:

```sh
uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 src/desk/programs/__tests__/programs.app.test.tsx
```

From root, `npm --prefix web run typecheck` and `npm --prefix web run guard:architecture` retain their source-defined spellings. No theme/token changes are planned. Retain logs outside temporary HOME and use pipefail if piping to tee.

### Safe browser and integrated proof

The new browser file must reuse existing `tests/e2e/glass_infra.py` boot/build/evidence/cleanup conventions, as used by current `tests/e2e/test_program_keys_glass.py`. Disable actual Programs/agents/providers and intercept all scoped Program writes with producer-derived responses. Assert exact request payloads and reject unexpected routes/actions. This exercises real UI/focus/layout with fake server effects; the separate real-route/local-Git integration proves the producer. Neither proves real GitHub availability or semantics.

Cover Check open/merged/unavailable, queued/uncertain result, blocked legacy/create uncertainty, stale displayed ID and repeat press. Verify Done versus delivery wording, recoverable error/custody, safe PR target, keyboard interaction and actual button hit ownership at 1440×900, 393×852 and genuinely resized narrow-in-wide. Use the current frame-grip pattern, not forced CSS. Save and inspect shots with proposed `evidence_dir("program-delivery-recovery")`. Cleanup browser/server/context in finally; no physical mic or external link navigation is needed.

After the proposed file exists, collect/run it under the same isolated lock:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/e2e/test_program_delivery_recovery_glass.py
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/e2e/test_program_delivery_recovery_glass.py
```

The integration owner follows the current [integrated gate](#integrated-gate), explicitly including the new browser test if affected selection omits it:

```sh
DESK_SWEEP_SHOTS=1 QUICK_TESTS="tests/e2e/test_program_delivery_recovery_glass.py" scripts/quick_check.sh origin/main
```

Verify actual base, host browser cache, stages, counts/skips, exit status and inspected images; never nest its lock. Missing tools, unsupported CLI flags, unexecuted new tests, skipped selections or no-change exit zero do not establish completion. No live provider operation is a prerequisite for this fixture proof; real remote validation would require a separately authorized task and exact target.

## V52 Project-review boundary verification

**Conditional G52-B only.** Source paths, definitions and existing tests were inspected at `80b641fa41c7352280cfa52e933acf6dbe8d3857`. Sixteen central application files matched the pinned archive and retained blob hashes. No application imports, collection, tests, build, Git operation, real database or provider call ran while planning. New selector/availability names and added cases are proposals, not implemented or passing results.

### Exact ownership and source map

| Repository path / anchor | Contract | Scope |
| --- | --- | --- |
| `holdspeak/db/delta.py` · `DeltaRepository` 23, `list_proposals` 433–461, `get_review/list_reviews` 614–647, `_execute_read` 697–703 | Existing registered repository; first open selection currently lives in Delta helper. Proposal default limit is 200; reviews normalize IDs/status and order `opened_at DESC` | Editable: proposed first-or-None helper beside review reads, delegating to unchanged `list_reviews(status="open", limit=1)` |
| `holdspeak/services/project_service.py` · constructor 507–512, Room 766–880, `_room_section` 888–897, review helper 1091–1125, needs-you gate 1392–1411 | Three availability gates, outer absence/degradation, inner caught faults and returned-row count | Editable: constructor capability/shim, gates and selector call only; no broad method extraction |
| `holdspeak/services/project_delta_service.py` · constructor/attachment 597–617, `open_review` 621, `get_delta` 1829–1864, helpers 1868–1959 | Existing open selector, frozen serializer and source-coverage shape | Editable: selector delegation and attachment rationale only. Collector, commands and frozen projection read-only |
| `holdspeak/runtime/room_composition.py` · 13–32/87–96 | Held root/context objects, missing-instance construction and conditional attachment | Editable: missing-Project capability argument/comment only; preserve all partial-context semantics |
| `holdspeak/web_server.py` · 1410–1415/1448–1451/1586–1613/1658–1661 | Delta first, same Project into context/collaborators, late attachment | Editable: explicit availability at current constructor and mutual-read comments only; no assembly relocation |
| `docs/internal/project-rooms/CONTRACTS-P0.md` · review composition 252–307 | Existing contract home; older P0 availability statements are historical rollout, not complete current inventory | Editable: bounded current owner/availability/fault/proof map, not unrelated feature inventory |
| `holdspeak/services/project_service.py` · `create_item_in_transaction` 5261–5412; `holdspeak/services/project_delta_service.py` · proposal decision 910–1018, review acceptance 1075–1257, `_record_command` 1279–1306 | Separate atomic command boundaries, same connection and nested command-kind matching | Read-only command bodies, even within edited service files |
| `holdspeak/services/project_kernel.py` · `KernelHandle.close_in` 149–161, `answered` 456–474, `_record_answer` 485–503, `_unwind`/call path 314–377, replay 397–429/531–567; `holdspeak/kernel/journal_atomic.py` · `transition_and_receipt_in` 122–166 | Whole command answer/terminal receipt in caller transaction; terminal-write failure differs from an earlier nested-command failure. Delta uses its service replay branch, not the publication-only shortcut | Read-only; preservation assertions must match failure class, command kind and handle state |
| `holdspeak/services/observer.py` · 165–280; `holdspeak/services/sqlite_observer.py` · 23–51 | Public service observation can write pipeline events; private and `*_in_transaction` methods are excluded | Read-only; no new observed façade or double emission |
| `holdspeak/db/base.py` · 19–29; `holdspeak/db/core.py` · imports 21–40/install 232–239 | Existing repository registration and shared connection factory, no service-observer wrapper | Read-only; no new repository instance/core registration/schema |
| `holdspeak/operations.py` · 1458–1465/1540–1558/1775–1861/2507–2579 | Existing read/write dispatch, bound targets and principal/admission handling | Read-only; no new endpoint/tool or authority |
| `holdspeak/web/routes/project_reviews.py` · 34–39/67–107/118–162; `holdspeak/mcp/resources.py` · 462–469/635–659 | Existing HTTP Delta read/frozen-by-ID and MCP resource; resource empty shape omits source_coverage; resource Room is bare/absent | Read-only; retain compatibility wrapper and exact keysets |
| `holdspeak/mcp/families/project.py` · 1099–1126/1140–1153; `holdspeak/services/briefing_sources.py` · 261–273; `holdspeak/runtime/composition.py` · install/compose call | Bare builders, fallback using legacy constructor, existing composition root | Read-only for this branch; shim preserves the accepted same-DB availability behavior |

There are five edited application files plus one existing contract document. No new production/test file, frontend code, recorded JSON/wire fixture, DB schema, registry or generic protocol is planned. Relevant `project_contracts.py`, refs, event ledger and observer/kernel implementations are context, not permission to edit them.

### Exact characterization boundaries

- Proposed `review_available: bool | None = None`: None infers `delta_service is not None`; explicit True/False wins. Bare default remains unavailable. A non-None falsey object is still available. Legacy compatibility is call shape/availability under the accepted same-DB query contract, not arbitrary custom override or different-DB behavior.
- Three gates must agree: outer Room review field, inner review query and Delta needs-you row. Disabled capability stays absent/omitted even when the database has open reviews. Enabled with no review is `ok`, zero, None and the existing last-accepted time.
- Selector failure is swallowed into zero/None; proposal read failure after ID assignment leaves zero/**that ID**. Only the review helper's later room-fields failure reaches its section wrapper. The earlier orientation read in `room` can fail the whole Room. Use call-specific/stateful injection or the helper wrapped in `_room_section`, never a globally failing method followed by a section-only assertion.
- The pending count is at most the existing 200 returned proposals, not a true total. Seed 201+ proposals to preserve that boundary deliberately; do not upgrade the query while moving it. Test newest open with distinct timestamps; ties retain current SQL semantics, not a new deterministic ID rule.
- `compose_room_services` prefers held root objects over context. Both absent builds/attaches as today; missing Project builds an available Project; existing bare Project plus missing Delta does not backfill availability. Both held skips the attachment block even if Delta lacks its Project. Preserve these cases, not an idealized universally attached graph.
- MCP resource empty shape and `get_delta` empty shape differ. Keep resource principal/missing-project checks and collector=None read safety. Frozen-by-ID resource/route paths retain current serialization/refs/sort/JSON tolerance.
- No query-specific observer event is added; the public Room observer still runs once with its current principal/error behavior. Do not assert a complete Room read performs zero DB writes merely because the selected repository query is read-only.
- `decide_proposal(accept/edit_accept)` creates items inside its supplied transaction; `accept_review` separately moves cursor/status/revision and supersedes open proposals. Preserve both, including replay/hash refusal and milestone guards. New terminal-failure cases must target Delta through the actual admitted route/operation, not report a publication test as Delta proof.

### Focused test budget

All ten test files below exist in the pin. Test names are source anchors, not executed results.

| File | Ownership / proving boundary |
| --- | --- |
| `tests/unit/test_delta_schema.py` | Editable: add selector beside `TestReviewShape` persistence tests; empty/scoped/accepted/newest/normalization/parameters/no domain writes |
| `tests/unit/test_project_room_read.py` | Editable: `TestAbsentMarkers::test_review_absent`, `TestFaultIsolation`, `TestByteDeterminism`, `TestNotFound`; add availability/falsey/precedence and exact targeted faults |
| `tests/integration/test_review_routes.py` | Editable: `TestRoomReviewSection`, `TestDeltaEmptyState`, `TestFullLoop`; prove real producer shape and same service attachment with no-op collector |
| `tests/unit/test_room_operations.py` | Editable: `test_each_row_is_bound_to_the_hubs_one_instance`, registry/admission cases; add held/missing/partial constructor matrix and current observer identity |
| `tests/unit/test_project_room_contract.py` | Editable: `test_f22_one_waiting_proposal_is_singular`; add disabled/partial/fault/multiple/capped needs-you cases as needed |
| `tests/unit/test_project_mcp.py` | Editable: `test_resource_project_room`, `test_resource_project_delta`, typed unknown project; add exact empty keyset and frozen projection |
| `tests/unit/test_philo9_02_round_three.py` | Editable: reuse the admitted real-hub fault harness; add Delta-specific proposal/review answer/receipt failure, same-ID retry and replay. Existing terminal-rollback test is publication-specific |
| `tests/unit/test_frozen_review.py` | Read-only regression: `TestGoldenWindows`, `TestOneOpenReviewLaw`; no new concurrent atomicity claim |
| `tests/unit/test_review_decisions.py` | Read-only regression: `TestDecideCreateItemAtomicity`, `TestAcceptReview`, decision replay/refusal and `TestDOM007Guard`; diagnoses may require a bounded amendment, not weakened expectations |
| `tests/unit/test_room_compat.py` | Read-only HTTP/MCP compatibility envelope/status proof |

The seven editable files are the complete initial test budget; no broad test fixture sweep is authorized. Tests using a legacy delta keyword may remain useful compatibility tests rather than all being mechanically migrated. Do not claim an existing test covers the added fault/partial-context cases merely because its filename matches.

### Delta terminal-failure recipe

**Proposed test-only construction, not a reproduced defect or passing proof.** Keep the new cases in the already-editable `tests/unit/test_philo9_02_round_three.py`. Its `_inject` (81–121) is publication-specific: the receipt predicate only matches `project.publish_update`, while its answer branch raises unconditionally. Copying it unchanged can either miss Delta entirely or fail the nested `create_item` answer **before** the outer Delta terminal boundary. Filtering only by operation name is also insufficient: that inner command runs under the outer handle.

1. **Use the existing admitted hub.** This module imports `test_philo5_the_loop.Hub/_boot` (130–169), which binds an isolated DB/observer, installed root and bearer-authenticated client. Keep the actual registry-bound Delta and its attached Project, and assert their held identity and database match. Do not replace them with new unit-service objects, forge a handle or bypass admission. Use the existing owner HTTP `decide` and `accept` routes (`project_reviews.py` 118–162) for these cases. This is not a claim to a new cross-transport fault matrix; the existing MCP/HTTP compatibility suite remains in the union.
2. **Prepare deterministic review data before faulting.** `_boot` constructs a real `ProjectEvidenceCollector` (`web_server.py` 1412–1415); the separate route fixture's no-op collector is not installed automatically. Replace only the held Delta's `_collector` with the `collect_all(project_id)` no-op contract demonstrated in `tests/integration/test_review_routes.py` 47–49. Seed synthetic observations through `hub.db.project_observations` using that file's `_seed_observation` shape (134–161), then produce the review through the real open-review path. Preserve the attached Project and registry. Obtain actual review/proposal IDs from the result, not fabricated frozen responses. For proposal cases, select a real create-item proposal such as `risk_attention` produced by `followthrough.overdue`; assert that precondition. For whole-review acceptance retain an undecided proposal to prove supersession. No real collector scan is needed or authorized by this plan.
3. **Keep the cases distinct.** Cover create-item `accept`, create-item `edit_accept` with a valid changed title, and whole-review `accept_review`, each at the answer and receipt seam. These six combinations are a proposed matrix, not existing tests. Use a fresh isolated scenario and explicit outer command ID for each. Snapshot relevant domain and command rows after setup, before the attempted write. Retry on the same authenticated transport/principal with the identical path/body/command ID: identity is not just the command string across different principals.
4. **Target the outer answer exactly.** In a test-local wrapper of `project_kernel._record_answer(conn, command_id, project_id, command_kind, request_hash, answer)`, match the expected caller command ID, project ID, outer kind (`decide_proposal` or `accept_review`) and `project_kernel.current().name`. Require the matching handle's `terminal_in_txn` to be true. Let the nested generated `create_item` answer call the real writer normally. Call the real matching outer writer, then raise a non-domain `RuntimeError`, preserving the existing terminal-write fault class. Record the hit, operation ID and connection; require exactly one intended injection and no earlier fault. Leave the original publication cases intact.
5. **Target the caller-transaction receipt exactly.** For the receipt case, use the pinned `journal_atomic.transition_and_receipt_in`, not a separately opened transaction or fallback API. Pass through the real outer answer and retain its connection/handle ID. Match that operation ID/name, the same connection and the successful terminal transition. Call the real `_in` function and then raise the test `RuntimeError`; this proposed after-write case proves rollback of inserted receipt/state rows as well as domain/answer rows. Require exactly one hit. Do not keep the helper's publication predicate. Neither wrapper changes production kernel/command code or synthesizes a replacement return value.
6. **Prove the intended rollback, not just an error response.** First assert the intended seam fired once. Relevant proposal/review/cursor/revision/item/change/service-ledger and newly written command rows must equal the pre-attempt snapshot. The matching admitted operation remains nonterminal with no terminal receipt. Setup, public observation or admission rows may exist; this is not a zero-database-write assertion. An earlier item/event/domain failure has different terminal semantics and cannot stand in for this case. Restore the injected fault before retrying, including on test failure.
7. **Prove recovery and replay through the real Delta path.** The identical request must succeed under the original operation ID with one terminal receipt and the correct domain effects once. Repeat it, comparing the full response/receipt identity, stored answer and domain snapshot. Delta's own recorded-answer branches (`project_delta_service.py` 827–850 and 1107–1127) handle replay; `project_kernel.RECORD_ANSWERS` does not include these operations. Create-item success legitimately records both a generated inner `create_item` command and the caller-keyed outer `decide_proposal` command, with one item and one revision bump. Both new command records roll back on the fault. Do not misread “commit once” as one command row; whole-review acceptance has its separate cursor/revision/ledger/supersession effects and does not create an item.

The existing direct-service item-insert rollback test (`TestDecideCreateItemAtomicity`) and whole-review transaction rollback test remain useful regression counterexamples, but neither is an admitted outer-terminal proof. Stop if the hit predicate, held identity, setup isolation or expected failure boundary cannot be established. No change to kernel, exception policy or Delta command bodies belongs to this cleanup.

### Future commands and safe execution

Use [setup/isolation](#setup-and-isolation), current root/backend guides, assigned worktree, isolated HOME/DB/key stores, exact provider opt-outs and the machine-wide test lock. The following invocations are **plan-composed** from source-defined command forms and verified existing paths. They were not run; collection itself can execute application code. Missing prerequisites/unsafe fixtures block proof, not justify new live effects.

Start with the selector/Room producer subset:

```sh
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/unit/test_delta_schema.py tests/unit/test_project_room_read.py tests/integration/test_review_routes.py
```

Final named union (collect using `--collect-only`, then run the same list with that flag removed):

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/unit/test_delta_schema.py tests/unit/test_project_room_read.py tests/unit/test_frozen_review.py tests/unit/test_review_decisions.py tests/integration/test_review_routes.py tests/unit/test_room_operations.py tests/unit/test_project_room_contract.py tests/unit/test_project_mcp.py tests/unit/test_room_compat.py tests/unit/test_philo9_02_round_three.py
```

The route/operation/kernel fixtures use real isolated SQLite and application/HTTP or MCP dispatch. Install and assert the test-specific no-op collector described above before the new hub review cases; `_boot` alone does not do that. These cases are not merely static assertions. Inspect actual fixture switches and key/DB paths before execution; configuration flags alone are not proof no egress occurs. No real collector scan, model, device, remote repository or owner-state access is needed. Do not run parked or metal suites or enable `HOLDSPEAK_WIRE_WRITE`/`HOLDSPEAK_EVIDENCE_WRITE`. No recorded fixture needs regeneration for unchanged shape.

There is no frontend change or new browser case in this branch. Exact producer/resource parity and existing compatibility tests are the focused proof. Do not invent UI work or a new harness to make a backend cleanup look larger. The integration owner still runs the current [integrated gate](#integrated-gate) under its authorized role:

```sh
DESK_SWEEP_SHOTS=1 scripts/quick_check.sh origin/main
```

The script owns its lock/HOME and may fetch/build/select tests; never nest a lock or run it during source-only planning. Recheck actual base, platform/browser cache, stage selection, skips/counts/logs/exit and any produced images. A no-change exit zero or skipped required focused case is not proof. No broad full-suite or arbitrary additional architecture ceremony is added.

### Structural and onboarding exit proof

Review the final active data/object path, not just imports or removed-name count: Room→existing repository selector; Delta wrapper→the same selector; Delta commands→the same attached Project transaction method where current composition attaches it. Legacy keyword/wrapper retention is intentional compatibility, not a failed deletion target.

The existing contract must let a fresh reviewer find the selector, all three capability gates, exact faults, distinct resource shape and command proof from a bounded map. Compare the same representative concern before/after. Report concrete reduced dependency and remaining coupling without invented runtime speed, token/file budgets, purity or full-product coverage. If the move gives no meaningful benefit, retaining the explicit façade is a valid design result, not a failed mandatory rewrite.

## V21 Action-Program binding verification

**Conditional D14/G21-A.** All source paths below were inspected at `80b641fa41c7352280cfa52e933acf6dbe8d3857`; no application imports, test collection/run, build, Git operation or provider call occurred during planning. Proposed cases, fixture outputs and browser file are not existing or passing results. The branch binds a new logical step to existing completion paths, not a new whole-Program acceptance policy.

### Exact ownership and contracts

| Existing repository path / anchor | Contract and scope |
| --- | --- |
| `web/src/desk/programs/ProgramWindow.tsx` · `toPlan` 548–555, `ProgramBody` 725+, draft projection 765–768, `savePlan/addStep` 878–885, Runs-on callbacks 949–951, Add entries 970/1042 | Editable: explicit add-time choice, append-only Add, captured response handling and protective bulk `onPick` guard. Do not expand `toPlan` and call it lossless |
| `web/src/desk/programs/types.ts` · `ProgramStep` origin 346, Program origin 536, `PlanStep` 638–650 | Editable: optional existing backend input `origin_ref` on PlanStep; no new server status or fulfillment DTO |
| `web/src/desk/programs/StepFold.tsx` · shared render 414–535/512–525; conditional `PlannedBrief` 145–181/463–466 | Editable only for read-only binding presentation across planned/started/review/finished folds, not just conditional PlannedBrief; existing per-step `changeStep` is the preserved alternative. Do not rewrite field authority or introduce origin reassignment |
| `web/src/desk/programs/programs.css` | Existing optional local style budget only; reuse current controls rather than new generic widgets |
| `web/src/desk/programs/api.ts` · `planProgram` 64–66, `changeStep` 151–168; `RunAsProgram.tsx` 13–17 | Read-only: existing raw plan input and exact-step PATCH; contextual action/project creation retained |
| `holdspeak/web/routes/programs.py` · from-action 152–157, plan 180–188; `holdspeak/mcp/families/program.py` · origin input 91, plan 446–449 | Read-only: existing transport/caller contracts. No global uniqueness or replacement policy is added |
| `holdspeak/services/program_service.py` · writer 1720–1729, `plan` 2159–2312, `from_action` 2314–2346, `plan_from_project` 2348–2360 | Read-only: provenance versus explicit step origin; append versus non-atomic replacement; from-action docstring is not proof of automatic closure |
| Same service · `change_step` 3609–3661 / `_apply_step_change` 3690–3711; `_step_wire` 1444–1470 / `runs_on_of` 1820–1834 | Read-only: in-place field edits; wire resolves effective/inherited defaults, so roundtrip replacement cannot preserve every original input |
| `holdspeak/db/programs.py` · `delete_step` 214–216; `holdspeak/db/schema.py` · requirements 5346–5366; Program service `_copy_parents` 3043–3048 | Read-only: replacement re-IDs rows; requirement step IDs have no FK and can retain deleted IDs. Every-step parent copying is not transfer of all step-local requirements |
| `holdspeak/services/program_service.py` · transition 4795–4850, `_close_origin_task` 4901–4936, `step_origin` 5604–5618 | Read-only: first non-history merged/done transition, separate action/marker/checkpoint writes, action only from explicit step origin, decision-only Program fallback |
| `holdspeak/services/program_runner.py` · contenders 885–901, pass gate 2010–2021, winner 2024–2066, merge decision 2254–2276 | Read-only: logical race, no-PR Done and current review/requirement/control rules |
| `holdspeak/services/program_split.py` · part origin 317–327, split 330–360, overturn 383–411 | Read-only: origin moves to last part; add-before-remove means a new global uniqueness guard would alter current protocol |
| `holdspeak/services/program_text.py` · origin 437/607–608/1063, `_STEP_FIXED` 1143–1146; Program service text apply 4290–4315 | Read-only: existing-step origin is fixed; added text rows can carry origin. No language edit needed |
| `holdspeak/services/follow_through_service.py` · complete 416–647, receipt 669–690; `services/service_event_ledger.py` · append transaction 59–63 | Read-only: action/linked ordinary records/event transaction, terminal replay/refusal, explicit reopen. Not a Program operation identity or permission inferred from receipt |
| `holdspeak/delivery/follow_through.py` · `_follow` 647–718, `_close_or_confirm/_close` 810–868 | Read-only: second completion producer, selected PR identity, global Secure confirmation, independent launch ledger. No one-actor guarantee |
| Program service · `close` 2940–2953, state helpers 648–665/833–853, `changed` 5037–5050; `program_rules.py` 298–301 | Read-only: Done/closed/history/parking do not define a new accepted whole-Program fulfillment predicate; delivery remains separate |

Initial production budget is three existing TS/TSX files plus optional existing local CSS. No backend implementation, schema, framework, new module, current-action-status API, source reassignment or completion retry is included. Preserve [I01/I08/I13/I16/I18/I19/I20/I22/I24](INVARIANTS.md) and the story's explicit actor/custody limits. Shared ProgramWindow/types/tests overlap S32 and other Program work; serialize them.

### Focused tests and new case ownership

All ten Python files and both existing web suites below resolve in the pinned archive. Names are source anchors, not runtime results. Three Python files and two web suites are editable; unchanged suites do not automatically prove new cases.

| Target | Ownership and proof |
| --- | --- |
| `tests/integration/test_desk_program_from_action.py` · current route/provenance case 33–59 | Editable: real from-action → ordinary/unbound versus explicitly bound append; existing IDs/gates/requirement custody; exact producer response capture |
| `tests/integration/test_program_closes_origin_task.py` · existing explicit-origin merge/park cases 16–53 | Editable: composed finish, no-PR Done, failures/replay, binding preservation through split/text/race as appropriate, distinct Program/action records |
| `tests/unit/test_conductor_k4_follow_through.py` · merge/restart 218–290, Secure 479–544 | Editable: combined observer/Program actor orders, mixed controls, reopen-between and failure windows; no live gh fallback |
| `tests/unit/test_program_service.py` · authority 118–160 | Unchanged regression: owner/creator-agent/MCP authority |
| `tests/unit/test_program_requirements.py` · 208–231/306–330/423–443 | Unchanged regression: head-bound judgment, owner word, end requirements |
| `tests/unit/test_program_rules.py` · 100–110 | Unchanged regression: Program Done control decisions |
| `tests/unit/test_program_text.py` · 161–164/243–273/336–440/700–713 | Unchanged regression: origin parse/render/immutability. New composed assertions live in owned producer tests |
| `tests/unit/test_phase200_continuity.py` · 421–457/588–625 | Unchanged regression: completion receipt, terminal replay/refusal and reopen; linked records are not private People storage |
| `tests/unit/test_program_sizing.py` · split 93, overturn 125/144 | Unchanged regression: current split placement/restoration. Extend origin-specific coverage in the owned composed tests, not this file without amendment |
| `tests/integration/test_program_race.py` · winner 82, failure 110 | Unchanged regression: logical winner/loser semantics, not proof of global origin uniqueness |
| `web/src/desk/programs/__tests__/programs.app.test.tsx` | Editable: explicit choice/default/body, append custody, bulk guard and per-step alternative, independent picker commands, uncertainty/late results and binding display |
| `web/src/desk/programs/__tests__/runAsProgram.app.test.tsx` · 23–48 | Editable: retain exact contextual creation/open/refusal behavior; no global picker or automatic step/start |
| `tests/e2e/test_program_action_binding_glass.py` | **Proposed new file:** narrowly intercepted UI proof below, not a test that exists at the pin |

Use the existing `tests/integration/program_rig.py` and fake check as read-only harness. It runs real temporary local Git, bare remote/worktrees and SQLite with fake agent/GitHub edges. A future assignment must authorize that local execution and verify no fallback can reach a real provider/repository. Do not claim this is a simulated-only or live-GitHub test.

The two **proposed, currently absent** captured files are `web/src/desk/programs/__fixtures__/program.action_binding.unbound.json` and `program.action_binding.bound.json`. A proposed `test_action_binding_wire` in the owned from-action file produces real GET Program responses before and after the explicit append. Seed stable IDs/clock as supported, assert semantic origin/ID/gate/requirement effects before capture, and use existing `_fixture`. Its shape check and temp-path scrubbing are not semantic or byte-determinism proof. No other recorded outputs or shared rig writes belong to this task.

### Cases whose meaning must not be flattened

- Compare all preexisting step IDs, explicit origins/gates and local requirement links before/after Add. Do not merely count the returned steps. Bulk guard sends zero `replace=true` requests in protected scope; an exact-step agent PATCH keeps identity. Other picker callbacks retain their separate commands.
- Bind a new logical row only. Matching/ambiguous existing origins suppress the convenience without rejecting public legacy data. Race children can share the origin; split moves it to the last part. New uniqueness enforcement would be a different contract.
- Test Program and global delivery control independently. Observe both actor orders and reopen-between. Preserve current behavior as characterized; the result is not a passing no-reclose guarantee.
- Test action transaction failure, then action committed/marker failure, then marker committed/checkpoint failure. Inspect action/linked records/domain event separately from step marker/checkpoint. Missing marker is not proof action is open; marker is not current status or causal credit. Merged→Done is not an automatic retry.
- Test already-done replay without a new domain receipt, dismissed/missing refusal, no-PR Done and non-history versus history/park/failed. Existing helper evidence can name a head as merged_sha without an actual merge; do not upgrade its meaning in copy.
- Plan responses can fail after persistence. Capture request identity, block overlapping local submit, retain acknowledged rows, and distinguish uncertainty from known refusal. Dismissal cannot cancel the server write. No title matching, inferred IDs or automatic retransmission.

**Source-destination contract, not new navigation ownership:** the [S21 destination limit](stories/HS-S21-action-program-binding.md#action-destination-and-current-status-limit) is mandatory for this slice. The new line is recorded origin identity only. `web/src/desk/openObject.ts:166–168,234–239`, `intelligenceNavigation.ts:31–42` and `pullouts/IntelligencePullout.tsx:38–46` (last two relative to `web/src/desk/`) explain why a dispatch with the correct ID is not exact-action reveal. `web/src/desk/__tests__/needsYou.app.test.tsx:139–155` and `web/src/desk/chair/arrivalAttention.test.tsx:371–389` are read-only source references, not additional V21 run/edit targets. `programs.app.test.tsx` mocks openRef at 97/116; keep dispatch and destination claims separate. No new Needs/People fixture, route mutation, reader or opener migration is assigned.

`holdspeak/services/follow_through_service.py:203–214` excludes terminal actions before its focus exception; `tests/unit/test_follow_through_service.py:452–493` preserves exact held-action focus, other filters and terminal/missing omission. These are also inspected references, not extra V21 targets. The existing real completion tests must inspect actual stored state/receipts; absence from an attention response, marker or successful dispatch cannot substitute. The bounded UI branch does not change backend from-action/plan admission or promise that a recorded origin is still live. If precise source inspection is selected later, amend G21, source ownership and safe destination proof before implementing it; do not loosen this slice's no-provider browser safeguards.

### Future commands, source-defined form versus proposed targets

Use [setup/isolation](#setup-and-isolation), current root/scoped guides, assigned worktree, isolated HOME/DB/key stores, fake provider edges and the machine-wide lock. Exact invocation lists below are **plan-composed** from source-defined commands and inspected paths; none were executed. Collection itself can import/execute application code. Missing safe fixtures/tooling is blocked proof, not permission for live operations.

Focused Python union, collect first and then remove `--collect-only` to run the identical list:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/integration/test_desk_program_from_action.py tests/integration/test_program_closes_origin_task.py tests/unit/test_conductor_k4_follow_through.py tests/unit/test_program_service.py tests/unit/test_program_requirements.py tests/unit/test_program_rules.py tests/unit/test_program_text.py tests/unit/test_phase200_continuity.py tests/unit/test_program_sizing.py tests/integration/test_program_race.py
```

Focused frontend, from `web/`, after its installed prerequisites are verified:

```sh
uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 src/desk/programs/__tests__/programs.app.test.tsx src/desk/programs/__tests__/runAsProgram.app.test.tsx
```

Only the assigned implementation lane may record the two owned fixture outputs. The selector below is **proposed**: first confirm collection selects exactly the intended producer, then record, inspect the diff and rerun with writing unset. Never run the whole fixture producer/recorder with writing enabled.

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/integration/test_desk_program_from_action.py -k action_binding_wire
HOLDSPEAK_WIRE_WRITE=1 uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/integration/test_desk_program_from_action.py -k action_binding_wire
```

Keep `HOLDSPEAK_EVIDENCE_WRITE` unset. Read-only verification also keeps `HOLDSPEAK_WIRE_WRITE` unset. Unexpected selected cases or changed fixture paths stop recording.

### Narrow browser proof and final gate

Reuse existing `tests/e2e/glass_infra.py`: `_ensure_build`, `_boot`, `_normal_chair`, `_settle`, `_assert_readable`, `_assert_clean` and `evidence_dir`, with the source-checked isolation/cleanup pattern in `test_program_keys_glass.py`. The existing keys test really creates/plans/starts Programs; do not substitute running it for this no-provider UI proof.

In the proposed browser file, boot an isolated temporary local hub with tick/provider opt-outs, then intercept exact Program read/mutation routes **before** navigation. Fulfill Program GET with the captured unbound/bound response; intercept the intended plan POST, assert its exact source/body and `replace=false`, and return the captured bound response or a clearly labeled injected refusal/uncertain variant. Abort and fail on every unexpected Program mutation. All Program writes stay fake in this browser lane; the separate producer proves real persistence. Permitted real writes are only isolated setup/window state. `HOLDSPEAK_PROGRAMS=off` does not block HTTP mutations by itself.

Exercise toolbar Add and, only where reachable with source-produced states, empty-state Add; an empty Draft currently renders the board, not that empty-state button. Do not invent an empty-Draft affordance/fixture or claim it was reached. Cover default-off choice, Cancel, acknowledged binding, refusal/uncertainty, protected bulk guard and accessible per-step alternative. Keep the main proof on the Board; text continuity is proved separately by producer/app tests, so no guessed text fixture is needed. Check 1440 and 393 plus a narrow window on a wide Desk, keyboard/Escape/focus and actual hit ownership. Use current compositor resizing, not CSS-forced width; locate/verify its control or report that proof blocked. Capture under proposed `evidence_dir("program-action-binding")`, inspect screenshots, verify zero real Program rows before/after, then close browser/server in `finally`.

The new target and evidence namespace are proposals. After implementation, under the authorized isolated cache/HOME/lock setup, collect then run:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/e2e/test_program_action_binding_glass.py
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/e2e/test_program_action_binding_glass.py
```

Source-defined supplemental checks are `npm --prefix web run typecheck` and `npm --prefix web run guard:architecture`. The assigned integration owner runs the current [integrated gate](#integrated-gate), including the new browser and composed producer if affected selection would omit them. `DESK_SWEEP_SHOTS=1 scripts/quick_check.sh origin/main` owns its lock/HOME and may fetch/build/run selected tests; never nest its lock or run it during planning. Verify actual base, selected counts/stages/skips/logs and screenshots. A no-change exit zero, skipped browser, generic sweep or fixture-shape pass cannot substitute for C21 proof. No broad unrelated suite or live GitHub operation is authorized by these instructions.

## V22 Step starting-input verification

**Conditional D25/G22-A.** Source: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. Twelve core source files were byte-compared to the retained archive; selected source/test/tooling files were read as data. No application imports, collection/tests, Git commands, builds or provider operations ran during planning. Proposed metadata, helpers, argv and added cases are not existing APIs or passing results.

### Exact ownership and source map

| Existing repository path / anchor | Contract and scope |
| --- | --- |
| `holdspeak/services/agent_hand_service.py` · Program spec/source 182–223; classification/capacity 457–593; brief/request 600–688; answer 779–784; prior launch 1069–1113 | Editable: server-owned new-Program descriptor after classification/capacity, checkpoint expected input, answer proof/final bytes, unresolved-attempt guard. No project resolver/queue rewrite |
| `holdspeak/delivery/factory_launch.py` · ledger 708–805; admitted record 932–955; worktree resolution 1186–1257; starting/create/spawn 1381–1518; submit/hold/send 1656–1762 | Editable: strict descriptor/server validation, post-claim selection, durable proof, literal start point, pre-spawn verification and text finalization, preservation across record replacement. Keep generic command receipts unchanged |
| `holdspeak/services/program_brief.py` · compose 151–234, current branch line 192, redaction/byte cap 224–229 | Editable: bounded deterministic start-context finalizer using supplied evidence, not another Git lookup. Existing brief/handoff rules and caps remain |
| `holdspeak/services/program_runner.py` · tick lock 138–140/397–404, promote 521–527, handoff 816–876, hand/result 905–956 | Editable: consume authoritative initial proof, distinguish current HEAD, preserve carried diff base and unknown-attempt handling. Do not change readiness/merge/control policy |
| `docs/programs.md` · Program/step 15–23, handoff/checkpoint 135–146, states 148+ | Editable: narrow accepted input/compatibility explanation, including local-only and new moved-ref verification; no unrelated guide rewrite |
| `holdspeak/agent_operations.py` · 8–13/80–86; `holdspeak/kernel/process_spawn.py` · 58–125 | Read-only: agent.hand is unenforced; process.spawn validates, hashes nested arguments, admits, decides and claims. Placement is local. No new top-level codec field is assumed |
| `holdspeak/services/program_service.py` · readiness 1369–1373; repository 1846–1873/1952/1973–1977/2051–2057; checkpoint 2590; default branch 5590–5603 | Read-only: owner-parked readiness, saved Program root, filing does not rebind, checkpoint stores ref+commit+IDs, bare branch is not fixed baseline |
| `holdspeak/delivery/commands.py` · native result persistence 749–779, stored duplicate/reconcile answers 1089–1097/1147–1156 | Read-only: arbitrary executor return metadata is not durable commit proof. No receipt expansion is needed for the local LaunchLedger route |
| `holdspeak/delivery/first_message.py` · hold 347–369, delivery 647–650; `holdspeak/kernel/process_input.py` · 130–143 | Read-only: retained final text and actual input hash. Do not re-fetch on pending-message resume or change text after input admission |
| `holdspeak/db/programs.py` · facts JSON 17–29/146–151/190–195; `holdspeak/delivery/registry.py` · 292–375 | Read-only: existing evidence JSON and source/common-directory identity; old fingerprints do not prove immunity to external replacement |
| `holdspeak/services/program_runner.py` · end tree 471–484/local merge 2131–2162; `holdspeak/services/program_delivery.py` · 213–226 | Read-only precedents/counterexamples: their fetch/fallback behavior is not the new freshness proof |

Initial edit budget: four existing production Python files, four existing test files and one existing guide. No new files, DB schema, web view, captured fixtures, ref namespace, global lock manager, generic command format or scheduler is planned. Preserve [I16/I18/I19/I20/I22/I24](INVARIANTS.md) and the story's exact identity/continuation constraints. Serialize hand/launch/runner ownership with other accepted Program work.

### Proposed descriptor, evidence and first-message contract

Names here are proposed and must be frozen in G22. A nested `worktree.program_start` descriptor may contain server-derived Program/step/source identity, ordinary-new policy, base ref and a credential-free remote identity token. It is included in the existing spawn argument hash; its selected result is not. Reject arbitrary mismatched client metadata, existing-tree/helper origins and unsupported policies. Explicit checkpoint input uses separately validated expected commit/ref metadata, with no remote selector. Compare the ref to its saved commit, freeze/pass that commit to creation, retain the ref as provenance and verify actual new HEAD; a ref moved between comparison and creation must not substitute its new target. Current code only passes its ref: moved-ref comparison is **new G22-gated verification**.

A bounded launch-owned `start_input` result can contain policy, Program/step/source IDs, common-directory identity token, remote name/credential-free target token, requested ref, selected commit, observation/fetch times and verified initial commit/time. Existing launch/operation/worktree/command IDs supply linkage. Never persist raw remote credentials, unbounded stderr or an invented old baseline. `LaunchLedger.record()` replaces rather than merges; retain these fields through starting, failure, registration and success writes.

Use a proposed internal instruction argument to `launch()` for this Program path. After selection, finalize/check/store the actual redacted Program text **before spawn**, enforcing the existing Program cap and generic instruction cap. `submit_process_spawn` then uses the retained final text for hold/send; AgentHand returns its true byte count. Copy the same bounded launch proof into the hand answer for the runner, checking launch/Program/step identity. Held resume uses its stored text, not a recomposed or newly fetched snapshot. This is an internal transport change, not an existing API or a new generic first-message system.

For new worktrees, the verified initial commit supplies the diff base. On continuation, preserve an existing `facts.base_commit`; current HEAD and any initial-proof absence remain distinct. Do not fabricate proof for a legacy launch or newly refuse supported continuation only because the new field is absent.

### Official Git semantics and candidate argv

These are proposed subprocess argument sequences, not shell interpolation or commands run during planning. Verify the installed Git supports the chosen flags. The exact remote operand must be captured/bound to the admitted source and effective endpoint, not repeatedly resolved from an externally mutable `origin` alias without comparison. Account for configured `insteadOf` rewriting; source ID alone does not freeze the destination. Keep credentials transient and scrubbed. Detected drift stops; atomic immunity to arbitrary external config/filesystem replacement is not claimed.

1. `git -C <root> ls-remote --exit-code --refs <bound-remote> refs/heads/<base>`: require exactly one matching full ref and capture its complete object ID. The [official ls-remote documentation](https://git-scm.com/docs/git-ls-remote) defines output and nonmatch status.
2. `git -C <root> fetch --no-tags --no-write-fetch-head --refmap= --no-recurse-submodules <bound-remote> <full-object-id>`: require exit zero even if the object exists locally. Use no destination ref and never derive the chosen object from shared FETCH_HEAD/tracking refs. These options and fetching a full object ID are documented by [git fetch](https://git-scm.com/docs/git-fetch). Review configured pruning/maintenance behavior against the accepted no-incidental-ref-change boundary and use supported controls where necessary; do not silently rely on unknown installation defaults.
3. `git -C <root> rev-parse --verify --end-of-options <full-object-id>^{commit}`: require the same full commit ID, using [git rev-parse semantics](https://git-scm.com/docs/git-rev-parse). Pass that literal ID through the existing worktree-create payload, then verify actual new HEAD before spawn and persist the result.

A server can reject fetching the selected raw object, especially after the ref moves; [upload-pack reachability configuration](https://git-scm.com/docs/git-config#Documentation/git-config.txt-uploadpackallowReachableSHA1InWant) is not this feature's authority to change. Refuse/hold explicitly, with no stale local fallback or server-security change. This selects the snapshot advertised at one point, not an eternal latest head. A later known-safe retry is a new observed attempt, never an overwrite of an unresolved attempt.

### Focused test budget and real producer path

All nine files below exist at the pin. Four are editable; five remain regression-only. No new test file or shared rig rewrite is assumed.

| Existing target | Ownership and proving boundary |
| --- | --- |
| `tests/unit/test_program_hand.py` · current production hand/tree assertion 19–64 | Editable: compose production AgentHand/LaunchService/kernel/Git with a real ProgramRunner predecessor merge, then inspect B's initial dependency before simulated work. Current local-base equality must be deliberately revised under G22, not deleted without replacement |
| `tests/unit/test_factory_launch.py` · partials/guards 425–520, dirty/dedup/no-rider 544–610 | Editable: selected object, pre-spawn actual HEAD, stored proof/text, byte-cap failures, record reload/rewrite, immediate post-spawn HEAD movement and no duplicate/unknown retry |
| `tests/unit/test_process_spawn_kernel.py` · admission/claim 80–111 | Editable: nested selector validation/hash, no effects before successful claim or on denied/expired request. Its fake launch service does not prove actual Git behavior |
| `tests/unit/test_program_service.py` · brief 82–104 | Editable: deterministic supplied start context, redaction/cap and truthful initial-versus-current semantics |
| `tests/unit/test_agent_hand_cap.py` · 98–135 | Unchanged: capacity waiting/queue behavior. New no-fetch assertions belong in editable production-hand tests |
| `tests/unit/test_agent_hand_again_builder.py` · 16–33 | Unchanged: builder identity and reviewer exclusion |
| `tests/unit/test_program_handoff.py` · 187–221 | Unchanged: same worktree and dirty work. Add production-hand baseline/proof assertions in the editable tests |
| `tests/integration/test_desk_programs.py` · 291–339 | Unchanged: handoff/ref and checkpoint tree; uses FakeHand, so new moved-ref/production-launch proof must be added in the editable real-hand suite |
| `tests/integration/test_program_execution_perfection.py` · 262–295 | Unchanged positive regression: real local remote final files and Done; not proof of B's initial state |

`tests/integration/program_rig.py` is read-only harness context. Its FakeHand creates worktrees itself and bypasses production launch selection; its fake GitHub merge updates fake PR state, not real Git. Do not implement the desired selector again in FakeHand. Put the composed starting-input proof in `test_program_hand.py` using its actual hand/kernel/Git machinery and a real local predecessor merge. If that requires editing another fixture, request a bounded amendment with the reason.

### Fixture composition and failure visibility

The named suites provide useful parts, not a ready-made combined starting-input fixture. Compose the following inside the four editable V22 test files; the additional harness paths below are **read-only construction references, not extra run/edit targets**.

1. `tests/unit/test_factory_launch.py::_make_repo` (63–72) creates a local seed with no remote. `tests/unit/test_program_hand.py` imports that helper and `tests/unit/test_agent_hand.py::_rig`; copying the existing positive case unchanged would exercise G22's missing-origin branch, not remote freshness. Use the existing `tests/integration/program_rig.py::make_repo(..., github=False)` precedent (61–78) to construct a task-owned bare local remote, then bind the real hand/launch machinery to that repository. Preserve explicit missing-origin negative cases. Do not install an agent CLI to make this fake-process lane work: `LaunchService` skips real executable preflight when a runner is injected unless `which` is supplied (factory_launch 878–883).
2. Bind one temporary DB explicitly to `ProgramService`, `ProgramRunner`, `AgentHandService` and `LaunchService`, and the actual launch ledger to the runner's ledger reader. `test_agent_hand._rig` wires real broker/receipts/fake transports (251–277) but does **not** pass `db=` to `LaunchService`; factory_launch 863–868/915 otherwise allows fallback for Program control reads. The independent integration `Rig` has its own coupled DB, `FakeHand`, in-memory ledger and runner (program_rig 300–334). Do not create A in one rig and pass only its IDs to an unrelated B rig, or copy fictional selection evidence between ledgers. The exact local assembly belongs in T22-01's fixture map; production constructor seams are `ProgramRunner` 151–180 and `LaunchService` 845–898. If a safe assembly needs an unowned helper edit, stop for the smallest amendment.
3. A's merge must traverse the existing real non-GitHub runner path. B's selection, creation, launch evidence and runner facts must traverse production hand/launch, not the integration `FakeHand` worktree implementation. Arrange the controlled fake-agent state and tick boundary so B cannot already have been created by FakeHand; require B's worktree/launch absence before the actual production dispatch. Keep A/B dependency records in the same Program store and preserve the existing final-output regression.
4. Observe **both** Git paths: `LaunchService(git_runner=...)` (855/898) and its process/worktree-command runner; also observe the injected ProgramRunner command seam used for A. `FakeTmuxServer.__call__` (test_factory_launch 101–106) forwards real Git **before** recording `self.calls`. Therefore an empty tmux call list is not proof of no fetch. Use a checked, recording delegate limited to the test-owned roots and local remote, with fail-closed provider/process fakes. Assert zero advertisement/fetch at the relevant admission/capacity/continuation boundaries against those actual delegates. Do not require zero Git overall: existing safe local/source reads are separate.
5. `test_program_hand._git` (15–16) returns stdout without checking the exit code. For the new object/tree proof, use checked subprocess results or the checked `program_rig.git` helper (48–51), assert nonempty valid commit identities and intended dependency content, and test that an invalid ref/failing Git result fails proof. Equality of two empty outputs is never a successful starting-tree assertion. Inject deliberate error outcomes distinctly from successful real local Git; inspect named state/receipt and unexpected error logs because runner tick can log an exception instead of propagating it.
6. Supply synthetic rider claims for the actual Program worktree and each launch/step. `_rig`'s default claim is fixed to one derived path/session (test_agent_hand 291–306); the existing single-step Program test already overrides it (test_program_hand 31–42). Reusing that fixed claim is not two-launch registration proof. Wait for the actual stored instruction state using the existing `_wait_for` precedent before asserting sent text, and close the test's fake session/worker activity on failure as well as success. Do not mistake return from `hand()` for completed first-message delivery.
7. Assert the temporary source/owner-tree snapshots, exact initial HEAD, persisted proof, actual first text and runner facts **inside the test before teardown**. `pyproject.toml` 183–188 sets `tmp_path_retention_policy = "failed"`; a passing tree may already be gone when pytest returns. Report the executed assertion/node IDs and retained command/failure logs, not an assumed post-run folder. Do not change global retention, preserve every scratch tree, invent permanent evidence files or enable wire/evidence recording to compensate.

### Required acceptance cases

- Create a temporary bare remote, A and B with a real dependency. A introduces a file/API and pushes via the actual non-GitHub merge path. Keep the owner's local base behind. B's production hand must select, fetch and create from the advertised object; inspect/use A's API in B **before** simulated builder changes. Compare source/attempt/OID, actual initial HEAD, stored verification, first text and runner diff base. Keep final-output regression too.
- Snapshot owner branch/HEAD/index, tracked dirty files and untracked files before/after. Allow object-store metadata changes; forbid reset/checkout/rebase/clean of that owner working tree. Program filing changes must not select another root.
- Inject advertisement/fetch failure despite cached objects, missing origin, missing ref, malformed/noncommit data, server raw-object refusal, unsupported flags and endpoint drift. Under accepted policy, no spawn and no stale fallback. Only temporary local remotes are real; server errors are explicit injected subprocess outcomes.
- Interleave remote movement and another fetch: each distinct attempt uses its own advertised immutable ID. Same-step competition must preserve current collision/identity guards and explicit loser/unknown outcome; no claim of global exactly-once scheduling follows from an in-process lock.
- Reload ledger between selected input, create, verification and spawn. Positive command receipt is necessary but not enough: selected proof and pre-spawn HEAD must agree. Failed persistence/mismatch keeps artifacts and stops. Path existence or a duplicate receipt cannot reconstruct missing provenance.
- Simulate an agent commit immediately after fake spawn. The recorded initial commit/diff base/first context remain pre-spawn; a later observed HEAD may differ. Pending-first-message resume reuses retained text/proof, with no new fetch or second first instruction.
- Test denied/expired claim, preview, capacity, held launch, helper/reviewer and same-worktree continuation with zero added remote selection. Source registration may already write metadata before capacity; do not assert the whole current hand path is effect-free.
- Test exact checkpoint ref/commit, missing ref and the newly accepted moved-ref refusal, including movement after comparison but before creation. Literal saved-commit input and pre-spawn HEAD verification must keep the chosen tree exact, with no remote fallback. Existing dirty continuation/handoff retains prior diff base; missing legacy proof remains unknown. Keep owner-parked predecessor readiness unchanged.

### Future verification commands

Use [setup/isolation](#setup-and-isolation), current root/backend guides, assigned worktree, actual platform/cache configuration and the machine-wide test lock. Real Git operations are limited to task-owned temporary repositories/remotes; fake tmux/agent/GitHub/provider edges must fail closed. No owner repository, real remote, installs, browser task or fixture recording is needed for focused proof. Collection can execute application code and requires the same assignment.

The following **plan-composed Bash recipe** uses source-defined flags and the same nine verified existing targets. First collect. Only after inspecting successful collection, use a fresh isolated run with `--collect-only` removed and the **identical** array. It is not a run result or an installation command.

The general hub opt-out `HOLDSPEAK_PROGRAMS=off` must not be copied blindly into this direct injected-Program-rig lane: `program_service.py::programs_on` (223–234) reads it and `ProgramRunner.tick` (372–375) returns immediately when disabled. The existing integration `Rig` does not override it. Here `on` is scoped to this isolated subprocess and these named fake-edge service/route tests, not permission to start a live/background hub. Preserve all unrelated machine/provider opt-outs; if a current target newly starts a live hub, stop and amend its isolation rather than enable background work. The real-CLI guard is explicit because conftest's default uses `setdefault` (8–12).

```bash
(
  set -euo pipefail
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  unset HOLDSPEAK_ALLOW_REAL_HOME HOLDSPEAK_WIRE_WRITE HOLDSPEAK_EVIDENCE_WRITE
  export HOLDSPEAK_TEST_NO_REAL_CLI=1
  export HOLDSPEAK_PROGRAMS=on
  files=(
    tests/unit/test_program_hand.py
    tests/unit/test_factory_launch.py
    tests/unit/test_process_spawn_kernel.py
    tests/unit/test_program_service.py
    tests/unit/test_agent_hand_cap.py
    tests/unit/test_agent_hand_again_builder.py
    tests/unit/test_program_handoff.py
    tests/integration/test_desk_programs.py
    tests/integration/test_program_execution_perfection.py
  )
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal "${files[@]}"
)
```

No browser cache is needed by this named Python service/route lane; broader integration remains a separate role/gate below. Conftest isolates each xdist worker HOME and tmux socket (680–723), not just the outer shell. Keep the normal shared machine lock: do not rename it per worker, nest it or treat lock timeout (test_lock exit75) as a test pass. A failed/empty collection, missing target, required skip, fixture setup failure, unexpected runner error or incomplete first-message assertion blocks proof. Do not install real agent/provider tools or widen to a broad suite to bypass a harness failure.

Establish baseline, relevant per-change subset and final named union after the last edit. Inspect selected node IDs/counts, skips, logs and the in-test tree/ledger/text assertions. Preserve useful output before temporary HOME cleanup; if piping logs, keep `pipefail`. A fake command's success is not remote or filesystem proof. The existing five regression-only modules and four editable modules remain unchanged in scope.

The assigned integration owner runs the current [integrated gate](#integrated-gate). `DESK_SWEEP_SHOTS=1 scripts/quick_check.sh origin/main` manages its own lock/HOME and can fetch/build/run browser checks despite this backend slice; do not nest its lock or run it during planning. Verify real base and actual stage/target execution; include necessary named targets using current documented selection if omitted. No-change exit zero or skipped required focused cases is incomplete proof. There is no new frontend/browser feature lane in S22.

## V41 Director-person identity verification

**Conditional HS-S41 scope only.** Source pin: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. Paths and contracts were inspected from the retained source archive; no application import, collection, test, build, browser or provider ran during authoring. Commands are composed from source-defined tooling, not installed-tool or passing-run evidence. D16/G41 and an assigned environment remain prerequisites.

### Source and ownership map

| Existing path / symbol | Source boundary and edit scope |
| --- | --- |
| `web/src/pages/cores/history/MeetingDetail.tsx` · `MeetingOutcomes` | Owner list/read 219–239/296–302; Door action-ID read 242–295; Project/People menu 372–382; owner control 470–485. **T41-02 production edit** |
| `web/src/features/project-room/RoomPeopleSection.tsx` · `ResolveWell`, `load`, `pick` | Candidate buttons 266–295; initial/read-return paths 317–347; immediate alias write/catch 349–363; resolved person/owner rows 390–505. **T41-03 production edit** |
| `web/src/features/project-room/api.ts` | `RoomPersonCandidate` 316 has only ID/name; preparation GET 336–351; existing `linkOwnerAlias` 355–363 returns void after `apiFetch`. Read-only; acknowledged HTTP completion and projection refresh are separate |
| `web/src/pages/cores/history/useMeetingData.tsx`; `holdspeak/web/routes/proposals.py`; `holdspeak/services/proposal_bridge_service.py` | Current confirm body text/owner/due, action-kind ordinary identity chain and decision-kind distinction. Read-only; the user did not choose a person-ID schema |
| `holdspeak/services/people_service.py` | `list_relationships` 131–155; `link_owner_alias` 1417–1464; `resolve_owner_candidates` 1641–1739; reader/writer checks 1939–1971; candidate/list views 2048–2054. Read-only. Alias matching is Python casefold; candidate projection intentionally narrower than authorized list |
| `holdspeak/people/store.py`; `holdspeak/people/keys.py`; `holdspeak/web_server.py`; `holdspeak/principals.py` | Read-only: encrypted `replace` 214–222 puts then reads; `MemoryKeyStore`; `_create_app` imports People factory 1246/invokes 1328; `_web_auth_gate` 1071–1108 and `required_right` 868–937 require OWNER for People REST. `launch_reader` 733–740 is a separate service-level contract |
| `holdspeak/web/routes/people.py` | Error translation 38–66, list 155–166 and existing owner-alias routes. Read-only. 409 holder data, 422 reserved and protected/unavailable cases must not collapse into success |
| `holdspeak/services/room_people_service.py` | `_read_room_commitments` 228–270 uses ordinary decision-commitment IDs and eligibility; resolved placement 369–384. Read-only; current attribution is not alias-write acknowledgement |
| `holdspeak/services/door_service.py` | `_build_owner_person_index` 430–465: read-time alias/name resolution and People-free/unavailable omission. Read-only; no destination does not identify the reason |
| `web/src/pages/cores/PeopleCore.tsx`; `web/src/desk/pullouts/PeoplePullout.tsx` | Read-only: roster return cleanup 309–313 differs from exact `PersonWindowBody` 704–783, mounted by PeoplePullout 12–27; supported internal tabs 789–795; `OwnerAliasSection` 1532–1573 provides existing Context Add, mounted 1616. Exact-person close is not proof of the roster return event, current Room read or identity certainty |
| `web/src/lib/api.ts`; `web/src/desk/openObject.ts`; `web/src/desk/objectWindows.ts`; `web/src/desk/returnToTask.ts` | Existing `ApiError.status/payload`, `openPerson` supported `now`/`prep` lenses and return-to-task signal. Read-only; no new transport/navigation framework |
| `tests/unit/test_philo5_the_loop.py`; `tests/unit/test_conductor_k6_agent_mcp.py`; `tests/e2e/glass_infra.py`; `tests/e2e/test_frame_glass.py` | Local authenticated hub/teardown; test-local launch credential pattern 104–110 and owner-header removal 82–87; isolated glass boot/readability/cleanup; frame-grip resize 674–684. Read-only setup references, not extra suite executions or shared rig edit permission |

Exact symbol/line drift must be reconciled before execution. No additional production/CSS file, backend fixture helper or public export is automatically writable. Two UI files can remain cohesive; no arbitrary size cap or helper fragmentation is prescribed.

### Exact-person inspection and return proof

The source distinguishes two real hosts. `openObject.ts::openPerson` (29–35) opens `pullout:people:<id>`; `PeoplePullout.tsx` (12–27) mounts `PersonWindowBody`. The latter reads/refreshes its own person (PeopleCore 704–783), but it does not contain the roster's `taskFocusPending`/`announceTaskReturn` cleanup at PeopleCore 309–313. Existing Context Add posts the alias and refreshes that person (1538–1549), not the Room preparation reader.

`RoomPeopleSection` reads on mount/project change and the explicit return signal (326–342). Its current alias path also loads after its own POST, but exact inspection performs no such Room POST. `ProjectRoomCore`'s desk-change callback reloads its controller (2035–2036), while the People child receives only unchanged `projectId` (2477–2480); `roomReads.ts::useRoomRead` (20–27) reports layout readiness, not data invalidation. These inspected paths do not establish an automatic exact-person-to-Room refresh. This is a source-backed integration/proof gap, not a reproduced live stale-screen incident or a claim that all window focus behavior is absent.

The pending bounded G41 branch therefore uses **explicit read-only Room Check after exact inspection**, including when no inline write receipt exists. Keep the resolver's Check available; reopen/Check refreshes authorized People metadata plus the current Room projection under the existing identity/race/privacy rules. Returning from existing Context Add can establish current alias/commitment attribution, not historical acknowledgement of a Room write. No extra production path, global event, close listener, focus protocol or backend change is assigned. Exact Inspect must not acquire the roster's shared return-focus token without a supported consumer; preserve that existing token/event path for Someone else/roster only.

The existing editable `roomPeople200.test.tsx` AC4 (178–198) explicitly invokes `announceTaskReturn`; it proves the Room **event consumer**, not that exact-person close emits the event. Retain it for its roster contract. Add the explicit-Check/no-inline-receipt/failure cases to this same suite and use the already proposed browser file for the real person-host sequence. Never dispatch `settings-updated`, remount Room or seed its final projection merely to make the exact-person journey pass. If automatic exact-person return is wanted instead, stop for a scoped contract/ownership amendment; do not silently edit read-only PeopleCore or navigation.

### Exact test and fixture budget

| Owner / role | Targets |
| --- | --- |
| T41-02 editable existing app suite | `web/src/pages/cores/history/__tests__/meetingKit.phase16.test.tsx` |
| T41-03 editable existing app suite | `web/src/features/project-room/__tests__/roomPeople200.test.tsx` |
| Read-only Python regressions | `tests/unit/test_owner_gesture.py`; `tests/unit/test_room_people_service.py`; `tests/unit/test_door_read_model.py`; `tests/unit/test_people_no_leaks.py`; `tests/unit/test_phase200_meeting_outcomes.py` |
| Read-only web regressions | `web/src/pages/cores/__tests__/peopleReopenLens.philo1306.test.tsx`; `web/src/desk/__tests__/people.app.test.tsx`; `web/src/features/project-room/__tests__/roomPeopleTokens.test.ts` |
| Proposed new composed producer | `tests/integration/test_meeting_owner_alias.py` |
| Proposed new browser file | `tests/e2e/test_meeting_owner_alias_glass.py` |

**Ten existing suites and two proposed files.** The five Python preservation suites are not blanket edit scope. Existing owner-gesture cases cover alias conflict/idempotence/reserved/schema boundaries; Room tests explicitly exclude private role context and test attribution; Door tests preserve read-time metadata. Existing Meeting tests using obsolete `proposal-person-btn` absence must be strengthened against the actual More menu in the editable suite. Do not delete positive unique-name/direct-navigation cases to fit a new warning.

T41-02 owns the proposed producer and four captures when both branches are assigned; T41-03 extends its alias/Room cases. If only the resolver is assigned, T41-03 owns creation of the same producer and relevant cases itself, not an implicit dependency on an unassigned task. Serialize these files and browser ownership. Independent T41-04 verification does not record new fixtures or silently edit implementation.

**Only four proposed synthetic capture outputs:** `web/src/desk/__tests__/fixtures/meeting-owner-alias/unresolved.json`, `linked.json`, `refused.json`, `unavailable.json`. Each is a bounded envelope of actual status/body for the relevant roster, ordinary confirmation, Room and Door reads. Refused may contain the named owner/agent/conflict/reserved/missing cases. IDs/joins come from the real temporary producer; preserve action IDs versus commitment IDs. All names/context are synthetic, never copied from real People data. Delays, malformed bodies and suppressed responses are labeled injection variants derived from those captures, not production incidents. Both editable app suites consume the relevant real envelope portions.

### Composed producer and preservation proof

Use a test-local fixture patterned on `test_philo5_the_loop.py::_boot` and teardown, with a real temporary ordinary DB, real composition, authenticated owner TestClient and an explicitly injected encrypted People service using temporary storage and an in-memory test key store. Apply current isolated-HOME/probe controls before constructing the hub. Initialize the temporary `EncryptedPeopleStore` with `MemoryKeyStore`, then test-locally monkeypatch `holdspeak.people.production_people_store` to return that store **before** `MeetingWebServer` construction. `_create_app` imports this factory internally and gives its one People service to consumers; patching service references after routers capture them is not equivalent. Assert the installed service really uses the temporary store rather than its unavailable fallback. Do not touch OS Keychain, the owner's keystore or shared fixture modules. Full-hub auth differs from a bare route fixture. No model, recording, repository, Program, phone, connector or Send is required.

Proposed test cases, to be written in the new producer:

- `test_owner_alias_journey_records_real_contract`: seed two synthetic same-name relationships with distinguishable role context; two meeting/action-kind proposal chains in real projects; confirm through the actual proposal route with owner **text**. Assert ordinary action/decision-commitment/source IDs and unchanged owner strings, no relationship assignment field. Read roster, Room and Door before alias linking; capture unresolved. POST the existing alias route under owner authority to the chosen ID. Capture actual acknowledgement/current roster and fresh Room/Door. Compare original commitment IDs under the person and original action IDs in Door. A second matching obligation demonstrates reusable scope beyond the first. Preserve ordinary stored IDs/text and protected Room/observer boundaries. Capture linked state.
- `test_owner_alias_records_refusals_and_unavailable`: exercise real owner-only REST GET/POST checks (401 unauthenticated, 403 non-owner), alias held elsewhere, reserved owner string, missing/archived candidate and unavailable encrypted store. Separately test PeopleService reads with a live launch-bound credential/principal and its alias-write refusal; do not expect this reader to pass the owner-only HTTP GET edge. Use the existing `test_conductor_k6_agent_mcp.py` 104–110 pattern in the temporary credential store, remove inherited owner headers, issue no real launch, and revoke only task-created credentials in cleanup. Do not import/run that unrelated full scenario. Capture bounded refusal/unavailable envelopes and assert unchanged ordinary state. Record which permission layer each assertion exercises; service read capability does not confer REST or alias-write permission. Generic store/write 503 is not proof no effect occurred.
- `test_owner_alias_current_attribution_is_not_receipt`: inject a failure in the post-put record read of the real encrypted store, prove alias state was written while the route reports its normalized 503, and ensure this is labeled uncertain rather than pre-effect refusal. Keep the failure hook test-local and restore it before reconciliation. Also check sequential same-relationship case-variant idempotence, exact saved spelling and independent current resolution. Close/park/unfile a synthetic ordinary source in the bounded test and reread: absence is not an alias-write result. Preserve private field exclusion and People-free read behavior using the existing service/context seam. This is not a concurrent-store atomicity proof.

Do not invent a new assignment endpoint, action field or alias replay key. The existing service's current checks and source cases define the domain. If the composed fixture cannot safely inject encrypted storage or authenticated launched-reader identity without extra source changes, report that specific proof blocked and request a test-only amendment; do not weaken admission or substitute owner credentials for the agent case.

A test-local recorder may follow `test_desk_programs.py:38–54`: write only these four paths under `HOLDSPEAK_WIRE_WRITE=1`, normalize temporary roots/timestamps as necessary without erasing identity relationships, compare shapes and assert semantics independently. No global recorder or `HOLDSPEAK_EVIDENCE_WRITE=1`. Before recording, collect the exact named producer cases and inspect selected targets/output paths. Independent verification keeps both write flags unset.

```sh
# Proposed commands after the test file exists, under authorized isolation:
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/integration/test_meeting_owner_alias.py -k 'records_real_contract or records_refusals_and_unavailable or current_attribution_is_not_receipt'
HOLDSPEAK_WIRE_WRITE=1 uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/integration/test_meeting_owner_alias.py -k 'records_real_contract or records_refusals_and_unavailable or current_attribution_is_not_receipt'
```

### Focused commands and honest results

Follow [setup/isolation](#setup-and-isolation) and current scoped guides. Resolve actual installed browser cache, safe HOME/DB/key store, dependency and local-server permissions first. The wrapper below is plan-composed from source tooling; none of its commands ran during authoring. Collection can execute application code. Use only the assigned task subset while developing; this is the full accepted-story union.

```sh
(
  set -euo pipefail
  : "${HS_PLAYWRIGHT_CACHE:?Resolve the actual host browser cache first}"
  : "${HS_EVIDENCE_DIR:?Set an absolute task-owned evidence directory}"
  HS_REAL_HOME="$HOME"
  mkdir -p "$HS_EVIDENCE_DIR"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_PLAYWRIGHT_CACHE"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  unset HOLDSPEAK_WIRE_WRITE HOLDSPEAK_EVIDENCE_WRITE
  py_files=(tests/integration/test_meeting_owner_alias.py tests/unit/test_owner_gesture.py tests/unit/test_room_people_service.py tests/unit/test_door_read_model.py tests/unit/test_people_no_leaks.py tests/unit/test_phase200_meeting_outcomes.py)
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/python.log"
  (
    cd web
    uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 src/pages/cores/history/__tests__/meetingKit.phase16.test.tsx src/features/project-room/__tests__/roomPeople200.test.tsx src/pages/cores/__tests__/peopleReopenLens.philo1306.test.tsx src/desk/__tests__/people.app.test.tsx src/features/project-room/__tests__/roomPeopleTokens.test.ts
  ) | tee "$HS_EVIDENCE_DIR/web.log"
)
```

Run source-defined `npm --prefix web run typecheck` and `npm --prefix web run guard:architecture` in the authorized checkout after the UI changes. Baseline, collection, expected-red new cases, focused final run, browser and current integration-owner gate are separate evidence. No-change quick-check exit or skipped/empty collection is not coverage. Renew proof after later shared edits.

### Bounded browser proof

Proposed `tests/e2e/test_meeting_owner_alias_glass.py` uses current `glass_infra._ensure_build`, isolated `_boot`, readability and cleanup helpers. Reuse only their supported construction patterns with temporary synthetic People storage; no browser interaction may configure a real keystore, mic, engine or account. Proposed `evidence_dir("meeting-owner-alias")` is an output label, not an existing fixture guarantee.

1. Seed the same synthetic identity/project/meeting context as the producer. Permit only its explicitly named local proposal confirmation, alias POST and necessary setup/window operations. Guard requests before navigation, fail unexpected mutations/egress, and verify ordinary/encrypted final state. No blanket `/api/**` mutation allow; no Send, recording, agent or provider effects.
2. Inspect Meeting's name-only choice and actual More menu. Confirm one ordinary action, observe unresolved identity without a guessed person, use existing project navigation, then the Room resolver. Do not claim the project link focuses the owner row; find it through the real Room UI. Only eligible seeded obligations may be used for this path.
3. Exercise distinct fresh synthetic scenarios in this same browser target. For distinguishable inline candidates, select/cancel/Inspect without effect, return to Room and press Check, then deliberately Link once; preserve ordinary identities. For indistinguishable inline candidates, keep inline Link unavailable, open the **actual exact-person pullout**, use its existing Context Add only after the person is identified, close it and explicitly return to Room/press Check. That scenario has one alias POST from Context and zero from Room; do not press Link again or present a Room-write acknowledgement. A no-write Inspect → return → Check scenario has zero alias POSTs. Do not synthesize the roster return event, force a Room remount or claim special focus restoration on exact-person close. Preserve the separate roster/Someone else return behavior. Return to Meeting and explicitly Check its Door read; verify the known action-ID People destination. No reconfirmation or Send follows.
4. Inject a lost alias response on that exact local request only, then Check/Inspect without a second POST. Distinguish positive exact-literal reconciliation, inconclusive case variants and failed refresh after known acknowledgement. Injection is not a live incident. New attempt/current rows must survive late old completions.
5. Prove keyboard/Escape/focus and real hit ownership at 1440×900, 393×852 and a genuinely narrowed Room/Meeting window on a wide Desk. Use the current frame grip (`test_frame_glass.py:674–684`), not CSS-forced width. Inspect screenshots and accessible labels, including indistinguishable candidates, read/protected failures and pending/unknown outcomes. If identity remains indistinguishable, the correct result is unresolved, not a successful arbitrary Link.
6. Stop browser/server in `finally`; inspect final temporary state/effect counts before cleanup. Same-browser in-memory custody is not durable reload recovery. No real People data or private context may enter committed screenshots/captures.

After the file exists, under the same isolated HOME/cache/lock setup, collect then run only this file:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/e2e/test_meeting_owner_alias_glass.py
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/e2e/test_meeting_owner_alias_glass.py
```

Report each C41 row passed/failed/blocked, actual invoked commands and changed state, source-versus-runtime limits, remaining G41 choices and rollback consequences. A read-only planning review does not satisfy this implementation proof.

## V25 Current-person review verification

**Conditional HS-S25/G25 scope only.** Source pin `80b641fa41c7352280cfa52e933acf6dbe8d3857`. Static source/CLI documentation was inspected; no application imports, collection, tests, Git, installed gh, browser or provider operations ran during planning. Exact field/helper names below are proposed. Assignment, G25 and source drift checks precede execution.

### Exact source and edit ownership

| Existing path | Bounded symbols / ownership |
| --- | --- |
| `holdspeak/delivery/pr_receipts.py` | **T25-02:** `GH_FIELDS` 50–54 remains; `_approved_by`/`_changes_requested` 203–229; source state/view/refresh 252–402; `_row` 438–467; `view_pr` 488–518, branch list 520–552, `_degrade` 554–559. Add review quality/read association without invalidating unrelated PR facts |
| `holdspeak/delivery/follow_through.py` | **T25-02:** sweep quality 176–231; direct poll 298–365; `_follow` projection 648–685; `_select_pr` 724–772; `_save` 805–806. Keep terminal/discovery/origin closure and poll cadence intact |
| `holdspeak/services/program_runner.py` | **T25-03:** `prompt_builder` 331–349; tick/fingerprint 397–442; existing-PR return 2009–2022; `_pr` 2164–2219, `_person_changes` 2221–2252, `_decide_merge` 2254–2275, `merge` 2278–2305. Shared read-only review evaluator and actual dispatch admission; preserve effect uncertainty |
| `holdspeak/services/program_service.py` | **T25-03:** `_LOCK` 230; `your_turn` Merge/Ask 541–578; `step_wait` 805; person matching 942–970; `step_wire` 1440–1525; owner decide 2675–2732; facts save/transition 4800–4836/4960–4965; `changed` 5022–5065. No authority, requirement or alias-matching redesign |
| `holdspeak/services/brief_words.py` | **T25-03:** Merge explanation 271–275; historical-review/not-checked wording 805–807. Existing reports/choices, not a new frontend structure |
| `docs/programs.md` | **T25-03 scoped guide edit:** person-review paragraph near 864. Explain latest applied observation, unavailable versus revoked, feedback limitations and request versus actual merge. Do not rewrite unrelated Program guidance; coordinate with S22's different guide section |
| `holdspeak/delivery/factory_launch.py`; `holdspeak/services/agent_review.py` | Read-only: existing ledger update 798–814; actual prompt path 352–369. Ledger durability/in-process updates and adapter returns do not establish exactly-once delivery |
| `holdspeak/web/routes/delivery_prs.py`; `web/src/desk/prReceipts.ts`; `web/src/test/wireShape.ts` | Read-only additive-row compatibility: routes 103–124 return existing dicts; frontend 16–51/93–109 has compile-time interfaces and accepts sources. Existing strict wire fixture has empty sources, not proof of a populated new observation |

Five production files plus one existing guide. No new module/table/route, raw provider query field, scheduler, global lock or frontend file is required. If source drift exposes a strict consumer that rejects the additive metadata, stop for its smallest explicit amendment rather than weaken validation.

### Proposed observation and admission proof

Current source live status validates only the outer provider shape. Add a narrow review-completeness result. Valid empty latestReviews is usable no-approval; malformed/missing/unknown-author/unknown-state data is unverified for the conservative branch. Existing approval/change summaries remain compatible. Provider reviewDecision cannot replace a per-person match. Do not infer explicit dismissal or reviewed SHA from a missing summary.

A local successful-read token can be stamped on normalized row review metadata and its source-success envelope. A direct view/branch read keeps its own token; it must not relabel the cache-wide source envelope. Sweep accepts only a live, structurally usable row paired with that envelope. Tokens prove coherent read association, **not that `refresh()` returns the exact result of its own invocation**: it returns `rows_view()` after calls and can observe a later cache update. The policy is latest applied coherent snapshot, not request-start/completion chronology across all receipt instances. No top-level schema/version change or general read-order framework.

Observer sequence/quality lives in existing per-launch follow-through JSON under the current observer lock. Preserve last complete matching evidence separately from latest attempt; equal-second times are not identity. Non-live source, missing target, malformed review or mismatched read token cannot promote retained rows. Direct failure must persist unusable quality while preserving history. A token alone is not enough without target/quality agreement.

The person-gated dispatch uses `gh pr merge <validated canonical PR URL> --squash`; [official GitHub CLI syntax](https://cli.github.com/manual/gh_pr_merge) accepts URL targets. Installed CLI support and remote behavior remain untested. URL binding identifies the PR, not an atomic review/head condition. Exit zero may only have requested/enqueued a merge. Other gate branches keep their existing command behavior. [Official view](https://cli.github.com/manual/gh_pr_view) and [list](https://cli.github.com/manual/gh_pr_list) document the existing JSON fields, not a per-review commit guarantee.

### Exact focused test budget

| Owner | Existing targets |
| --- | --- |
| T25-02 editable producer tests | `tests/unit/test_pr_receipts.py`; `tests/unit/test_conductor_k4_follow_through.py`; `tests/unit/test_philo15_17_merge_reaches_update.py` |
| T25-03 editable integration/words tests | `tests/integration/test_program_person_review.py`; `tests/unit/test_brief_in_his_terms.py`; `tests/unit/test_program_window_words.py` |
| T25-03 bounded shared helper | `tests/integration/program_rig.py` only for an opt-in real receipt/observer path at the fake-gh boundary; not a collection target |
| Unchanged regressions | `tests/unit/test_program_requirements.py`; `tests/unit/test_program_answer_once.py`; `tests/integration/test_program_run.py` |

**Nine existing runnable test modules, six editable, plus one editable existing helper. No new test file, captured wire fixture or browser target.** Intermediate tasks run their subset; final proof uses the union. The unchanged regression files are not blanket edit scope. Coordinate shared rig/Program ownership with S21/S22/S32 and rerun their affected proof if the helper's preserved default changes.

Useful existing anchors: receipt refresh/stale tests 189–232; real receipt/observer fake-gh setup in `test_conductor_k4_follow_through.py:65–119`, sweep assertions 150–173, failed source 197–212 and retained target 327–337; direct poll `test_philo15_17_merge_reaches_update.py:431–452` and bounds 482–486; person approval/word hold 39–53 and feedback/dedup 56–86 in `test_program_person_review.py`; ready-merge wording `test_brief_in_his_terms.py:185–202`. These are source-inspected cases, not passing results.

### Real producer chain, fake provider

The current Program rig uses real temporary Git/SQLite and a fake agent/gh. Its `FakeGitHub.sweep` directly writes normalized follow-through facts, bypassing the exact producer boundary being changed. Keep that default for unrelated tests; it cannot be the only S25 proof.

Add one opt-in fixture path in existing `program_rig.py` (exact option name proposed), enabled by S25 composed cases and, only under an explicit joint assignment, the [review-to-delivery integration gate](#review-to-delivery-integration-gate). Reuse current injectable `PrReceiptsService` and `FollowThroughObserver`, source/worktree registry setup patterns in the producer unit suites and the rig's existing launch ledger. Supply raw gh JSON through a strictly fake process seam; the S25 cases explicitly choose `latestReviews`, head/repository identity, state, CI and provider faults. Do not fabricate the new observation fields in this composed path or reconstruct the only raw test payload from already-normalized approval lists. Keep default fake sweep and all unrelated callers unchanged. The fake gh dispatcher must accept the now URL-targeted person merge and record exact argv; unexpected command/URL is a test failure, never fallback to real gh.

All Git repositories/remotes are task-owned local paths, even when the rig uses a GitHub-looking origin with an `insteadOf` mapping. Verify the effective mapping before running; no real GitHub account/token is needed. Fake merge success only updates test provider state and is not proof of actual merge mechanics/branch protection. Existing real local Git still requires explicit test execution authority and correct fixture isolation.

Required cases in the owned files:

1. Raw approval, valid empty, commented/explicit nonapproval, matching changes, missing/null/non-list/malformed rows, missing/deleted authors and aggregate-only approval. Preserve unrelated merged/CI data despite review incompleteness.
2. Source success→failure→recovery; direct success→failure; direct/sweep both application orders; same-second observations; matching/mismatched read tokens; retained PR absent from a bounded list. Assert no historical snapshot is rewritten as fresh and no absence is called dismissal.
3. Real raw producer→observer→ledger→Program chain: approval while owner-word requirement or CI holds; later changes; other hold clears; zero merge. Fix work on same PR, replay the same feedback observation and show it still blocks without another automatic round. Then explicit newer approval plus all other gates applicable to that existing caller permits exactly the expected sequential request.
4. Matching aliases with both approval and changes, changed effective person, unavailable person lookup, legacy historical bool, wrong launch/source/URL/number/head, incomplete quality and late unavailable attempt. Each invalid admission issues zero provider read and zero merge command.
5. Owner Merge before next Program tick and direct runner merge use fresh local projection. Verify precise URL argv, owner/agent authority, retained other requirements/control rules and preservation of unrelated facts/request marker across later writes.
6. A durable person-gated GitHub request marker suppresses sequential repeat and service reconstruction before a real receipt, with no duplicate command/success checkpoint. Explicitly document simultaneous-before-marker and command-before-persistence as unproved/unsolved, not hidden by a sequential test.
7. Prompt raised, missing launch, owner-taken and ambiguous-return cases: gate stays blocked; recorded feedback attempt never claims delivery or automatically repeats. Preserve current timestamp/`seen` dedup limitations. Do not inject a success boolean merely because the fake records a call.
8. Review-only facts change triggers an existing Program frame; fresh report/turn/wait data withdraws stale Merge, preserves previous approval, distinguishes unverified/no current approval/changes/request outstanding, and offers no automatic Ask/Send. Timestamp-only refresh does not create repeated meaningful-change notifications. Verify stored/report identities after final updates.
9. Terminal observed merge/closed, imported history, local/non-person/agent-review paths, ordinary requirements and unrelated Program progression remain unchanged. No observation gate may erase an actual external outcome.

### Source-defined commands, composed invocation

Follow [setup/isolation](#setup-and-isolation), current root/backend instructions, assigned checkout and machine-wide lock. No collection or command below was executed during authoring. Collection can execute application code. Resolve actual dependencies; use isolated HOME/DB/config and fake effects. No browser cache is required for this focused Python union; integration-owner checks have their own current prerequisites.

```sh
(
  set -euo pipefail
  : "${HS_EVIDENCE_DIR:?Set an absolute task-owned evidence directory}"
  mkdir -p "$HS_EVIDENCE_DIR"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  unset HOLDSPEAK_WIRE_WRITE HOLDSPEAK_EVIDENCE_WRITE
  files=(tests/unit/test_pr_receipts.py tests/unit/test_conductor_k4_follow_through.py tests/unit/test_philo15_17_merge_reaches_update.py tests/integration/test_program_person_review.py tests/unit/test_brief_in_his_terms.py tests/unit/test_program_window_words.py tests/unit/test_program_requirements.py tests/unit/test_program_answer_once.py tests/integration/test_program_run.py)
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal "${files[@]}" | tee "$HS_EVIDENCE_DIR/collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal "${files[@]}" | tee "$HS_EVIDENCE_DIR/python.log"
)
```

Record actual selected tests, baseline, expected-red new cases, final run tails and stored results separately. `bash -n` over a recipe verifies shell syntax only. The integration owner runs current [integrated gate](#integrated-gate) after final shared edits; it may fetch/build/run affected tests and must not be nested under another lock. A skipped/no-tests/no-change quick check is not proof. Existing Desk sweep may check rendered words, but this slice makes no new keyboard/geometry/browser-flow claim and does not add an ungrounded glass target.

Completion requires every accepted C25 case and independent review, plus applicable integrated checks. Report legacy holds, current observation limits, actual requested-versus-merged outcomes and the safe-downgrade condition. No passing fake-provider test proves live branch protection or creates shipping authority.

## V13 Project-Program continuity verification

**Conditional HS-S13/G13-A only.** Pin `80b641fa41c7352280cfa52e933acf6dbe8d3857`. Source was inspected as data; no app imports, collection, tests, Git, build, browser or provider operation ran. New helper/field/test-node names are proposals. Execution requires the accepted local branch, assignment, current instructions and isolated checkout.

### Exact source and production ownership

| Existing path | Symbols / bounded role |
| --- | --- |
| `web/src/features/project-room/ProjectRoomCore.tsx` | **Editable:** keyed scope remount 2019–2024; existing refresh subscription 2034–2036; read-layout gate 2217–2258; Refresh 2290–2293; active filed-work composition 2465–2487. Add current Programs state wrapper and stable local refresh-kind declaration, not another reader/host |
| `web/src/features/project-room/model.ts` | **Editable:** optional Programs section/row 559–573; generic decoder 629–644 read-only except use by local Programs branch; current Programs decoding 896–908. Tighten this section only; absent/degraded/invalid must not become fake empty |
| `web/src/features/project-room/useProjectRoomController.ts` | **Editable:** phase-1 load/sequence/quiet handling 95–161; later phases 163 onward; returned state 370–420. Add bounded last-read truth; current Phase 1 owns it, not detail/extras |
| `web/src/desk/programs/RoomPrograms.tsx`; `web/src/desk/programs/model.ts`; `web/src/desk/programs/open.ts` | **Read-only:** complete reused component 13–48; `programChip` 58–65; `openProgram` 4–5. The component owns its fold, omits empty arrays and opens the exact ID. Do not copy its rows or add a second Programs fold |
| `web/src/features/project-room/api.ts`; `web/src/desk/useDeskChangedRefresh.ts`; `web/src/desk/components/window/dockState.ts` | **Read-only:** fetch/decode Room 22–26; kinds 76–80 and debounced hook 138 onward; actual `frameNames` compatibility 75–100. Unknown `program` already passes today; explicit local ownership is not a proven refresh repair |
| `holdspeak/services/project_service.py`; `holdspeak/services/program_service.py`; `holdspeak/db/programs.py` | **Read-only:** room Programs/fault isolation 876–895; `for_project` 1162–1170, `_summary` 1276 onward, create 1999–2015, update/file 2098, changed 5070–5074, `_waiting_first` 5524–5528; uncapped store query 183–186. No backend projection/lifecycle/cap change |
| `holdspeak/web/routes/projects.py`; `holdspeak/web/routes/programs.py` | **Read-only:** real admitted Room and Program detail/create/update routes. Full-app auth must be exercised, not inferred from the bare Programs test client |
| `web/src/desk/applications.ts`; `web/src/pages/cores/MemoryCore.tsx` | **Read-only:** current Memory/project entry 426–442, Room composition 410–411. Reuse the current app, not the parked drawer |
| `web/src/desk/store/compositorSlice.ts`; `web/src/desk/objectWindows.ts`; `web/src/desk/components/Pullout.tsx` | **Read-only:** exact pullout dedup 329–336, restore/raise 653–658; absent-list stand-in 164–173; actual family mount 73–79/129–138. Preserve existing Program branch `projectReturn: null`; there is no special return-to-project contract to promise |
| `web/src/desk/pullouts/families.ts`; `web/src/desk/programs/ProgramWindow.tsx`; `web/src/desk/programs/RunAsProgram.tsx` | **Read-only:** existing detail mount/ID read and project/action launch. The current overview does not add Start, Done, delivery or creation semantics |

**Three existing production files only.** No new module/CSS/route/schema, global refresh constant, Program detail cache or backend query. If a named path/symbol differs at the assigned revision, resolve it under HS-T00 rather than invent a second owner. Geometry failure may justify a separately approved smallest style-path amendment; it is not permission to duplicate UI or hide the view on phone.

### Exact test and capture budget

| Role | Existing test path |
| --- | --- |
| Editable real producer | `tests/integration/test_desk_project_room.py` (new scoped cases only; retain existing `_hub`/other cases) |
| Editable active Room app | `web/src/features/project-room/__tests__/room.app.test.tsx` (real raw envelope and actual decoder/refresh predicate) |
| Editable read/decoder suites | `web/src/features/project-room/__tests__/useProjectRoomController.test.tsx`; `web/src/features/project-room/__tests__/model.test.ts` |
| Editable bounded browser nodes | `tests/e2e/test_room_glass.py` (new named S13 node only, using existing app-specific file) |
| Unchanged backend regressions | `tests/unit/test_project_room_read.py`; `tests/integration/test_desk_program_from_action.py` |
| Unchanged web regressions | `web/src/features/project-room/__tests__/ProjectRoomCore.test.tsx`; `web/src/features/project-room/__tests__/roomOpen.philo1306.test.tsx`; `web/src/desk/__tests__/phonepass.philo17.test.ts`; `web/src/desk/programs/__tests__/programs.app.test.tsx`; `web/src/desk/programs/__tests__/runAsProgram.app.test.tsx`; `web/src/desk/store/__tests__/pulloutIdentity.test.ts` |

**Standalone S13 budget: thirteen existing suite paths, three Python producer/regression, nine web, one browser. Five are editable, eight are unchanged regressions. No new test file.** The [joint creation-to-Room gate](#creation-to-room-integration-gate) below conditionally allows one linked edit in the already listed Programs app suite; it does not widen standalone S13 ownership. Exact new test nodes below do not exist at the pin. Shared test edits require coordination with S11/S12/S21/S25/S32/S41/S42/S52. Do not edit every named regression merely because it is in the budget.

**One proposed capture file:** `web/src/features/project-room/__tests__/room-wires/programs13.json`. A synthetic envelope contains actual status/body for loaded Room A plus the selected matching Program detail, successfully empty Room, degraded Programs Room, and bounded full emitted `desk_changed` frames containing matching Program changes used by app cases. Check `deskChanges` membership; a coalesced frame may have note/project at top level. Preserve real IDs/joins and distinguish deliberately seeded stored states from lifecycle transitions. Absent/malformed/delayed transport variants are labeled test injections, not separately fabricated server captures. Only `test_project_program_continuity_records_scope_and_reads` owns the complete capture write, including the empty/degraded cases; other nodes assert without recording. Record only this path; existing `room.programs.json` and unrelated room wires remain unchanged.

Source precedents: full-hub `_isolate` 73–108 and `_hub` 112–144 in `test_desk_project_room.py`; current Room RuntimeBus harness 59–79 in `room.app.test.tsx`; quiet baseline assertions 286–364 in controller tests; isolated legacy `RoomPrograms` assertion near 762 in `programs.app.test.tsx`; source-only fixture recorder `scripts/record_program_fixtures.py:637` captures a section, not this full journey. The recursive `_shape` precedent in `test_desk_programs.py:38–54` validates types only; semantic IDs, scope, order, state and detail joins need independent assertions.

### Producer-to-consumer proof

Extend `test_desk_project_room.py` with two explicitly proposed nodes, without altering unrelated helper behavior:

- `test_project_program_continuity_records_scope_and_reads`: use existing authenticated `_hub(..., lifespan=False)` and real shared DB/routers. Before constructing it, apply current `glass_infra._boot` isolation switches absent from this older helper, including `HOLDSPEAK_PROGRAMS=off`, phone/Telegram/CLI-engine/Calls/Line/recording/mic-check controls; inspect current semantics to ensure they disable background effects rather than silently replace tested routes. Inject a fake `gh_runner` that fails on any invocation. Initialize only a task-owned tiny local Git repository with local identity/README, explicit base branch, no remote and no DW rails. POST two projects and Programs through real routes with explicit repository/project context. Do not use `test_desk_programs._rig`, Start, tick, plan/shape, delivery, model or agent execution. Capture admitted Room and matching exact detail; assert no launches/provider effects. Assert the actual full-app unauthenticated denial and non-owner read denial for these owner-scoped HTTP routes. Use only a test-local principal/credential seam and the current auth implementation; no real credential or persistent owner access. This is not proof of per-project private ACLs.
- In the same producer, exercise current project filing/update on one acknowledged Draft and reread both Rooms. Confirm association changes visibility without repository/worktree migration or ID change. Capture the actual full emitted `desk_changed` frame through the current composition callback, not a handwritten claimed server event. Assert the matching Program entry using the same changes-first semantics as `deskChanges`, including a coalesced `changes` list; the frontend consumer runs that actual helper, while the Python producer inspects the recorded JSON. Do not rewrite its top-level kind to Program. Add a synthetic many-row case beyond incidental UI list sizes and stored-state cases through existing ProgramStore primitives where needed; label these as fixture seeding, not proof that an agent really completed or merged work. The service derives summary state from actual stored Program/step/requirement/checkpoint facts, so do not set only a state string and assume the intended summary. Preserve its order/progress/turn semantics.
- `test_project_program_continuity_records_failures`: use its own isolated hub and the same actual Room route for refusal/fault/archive assertions, but **never write the capture file**, even when the recording flag is set. Verify empty versus injected `_read_room_programs`/`ProgramService.for_project` failure, Programs-only degradation, archived read behavior and unchanged Program IDs/counts. The first node is the sole capture owner: it also gathers the genuine empty and fault-isolated Room responses in its own fixture, restores the fault hook, assembles the complete loaded/detail/empty/degraded/frames envelope, then writes the one bundle once. No cross-test accumulator, merge-on-write or partial file is allowed; xdist workers are not serialized by the outer test lock.

A fixture helper may follow the existing file's `HOLDSPEAK_WIRE_WRITE` convention. Record temporary path/timestamp normalization explicitly without breaking Program/project/detail identities. If capture needs additional response fields or output paths, obtain a narrow amendment. The full hub is necessary for admission/composition evidence; a dual-router bare TestClient is not a substitute. No user HOME/DB/key store, real credential or network provider enters the rig.

The active Room app suite consumes the raw captured envelope through the real API decoder/controller. Keep `useOnDeskChanged` and `frameNames` actual while the RuntimeBus transport is the existing controllable harness. Add explicit cases for any Program ID, moved-in/out, burst debounce, windows-only and known unrelated kind. Unknown-kind fallback must remain compatible. Test missing/unknown section state, malformed/non-array/null row/duplicate/missing ID, and invalid numeric evidence without false empty. Preserve valid extra fields and unknown nonempty state words. Add initial Phase 1 failure with no retained Room (existing load failure, no last-read claim), full/quiet latest-read races, current recovery, later detail/extras failure and scope remount; assert valid retained content plus last-read warning instead of spinners/all-clear.

Under assigned isolation, after those nodes exist, collect both planned nodes, then record only the single capture-owner node:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/integration/test_desk_project_room.py -k project_program_continuity
HOLDSPEAK_WIRE_WRITE=1 uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/integration/test_desk_project_room.py -k project_program_continuity_records_scope_and_reads
```

No such collection or recording was run. Independent verification unsets all three recording flags named in the recipe. A missing new node before implementation is expected, not permission to treat an empty selection as passing.

### Focused verification commands

Use [setup/isolation](#setup-and-isolation), actual current repository role instructions and the machine-wide lock. Resolve installed tooling/browser cache and local-server permissions first. The following wrapper is plan-composed from source-defined commands; no commands below were executed while authoring. Collection can execute application code. Keep evidence outside the disposable HOME.

```sh
(
  set -euo pipefail
  : "${HS_EVIDENCE_DIR:?Set an absolute task-owned evidence directory}"
  : "${HS_PLAYWRIGHT_CACHE:?Resolve the actual host browser cache first}"
  HS_REAL_HOME="$HOME"
  mkdir -p "$HS_EVIDENCE_DIR"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_PLAYWRIGHT_CACHE"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  unset HOLDSPEAK_WIRE_WRITE HOLDSPEAK_WRITE_WIRE_FIXTURES HOLDSPEAK_EVIDENCE_WRITE
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/integration/test_desk_project_room.py -k project_program_continuity | tee "$HS_EVIDENCE_DIR/producer-collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/integration/test_desk_project_room.py -k project_program_continuity | tee "$HS_EVIDENCE_DIR/producer.log"
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/unit/test_project_room_read.py tests/integration/test_desk_program_from_action.py | tee "$HS_EVIDENCE_DIR/regression-collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/unit/test_project_room_read.py tests/integration/test_desk_program_from_action.py | tee "$HS_EVIDENCE_DIR/regression.log"
  (
    cd web
    uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 src/features/project-room/__tests__/room.app.test.tsx src/features/project-room/__tests__/useProjectRoomController.test.tsx src/features/project-room/__tests__/model.test.ts src/features/project-room/__tests__/ProjectRoomCore.test.tsx src/features/project-room/__tests__/roomOpen.philo1306.test.tsx src/desk/__tests__/phonepass.philo17.test.ts src/desk/programs/__tests__/programs.app.test.tsx src/desk/programs/__tests__/runAsProgram.app.test.tsx src/desk/store/__tests__/pulloutIdentity.test.ts
  ) | tee "$HS_EVIDENCE_DIR/web.log"
)
```

Run source-defined `npm --prefix web run typecheck` and `npm --prefix web run guard:architecture` under the assigned checkout. Record baseline, expected-red characterization, collected/executed counts, skips and final run tails separately. The current [integrated gate](#integrated-gate) is performed by its assigned owner after final shared edits; it can fetch/build/test and must not be nested under another lock. A no-change/empty/skip exit is not this slice's proof.

### Bounded actual-browser proof

Add one proposed node `test_project_program_continuity_geometry_and_focus` to existing `tests/e2e/test_room_glass.py`, using current `_ensure_build`, `_boot`, readability/hit checks and finally cleanup. Do not resurrect parked walks or create another per-feature browser framework. Existing Room open helpers at 251–263/727–738 stage `{key: "open-project-memory", scope: "project:<id>"}` then reload/normal-chair setup; use the current supported path.

The browser boots a temporary isolated local hub/Desk, but all Program mutations fail closed and Program detail/Room responses used by this case are intercepted from the real producer bundle. Install request guards before navigation. Ensure staged project, Room orientation, Program row and intercepted detail share exact synthetic IDs; if local setup produces different IDs, seed a controlled compatible project or explicitly remap the entire linked fixture consistently, then assert that mapping. Do not silently mix real setup IDs with unrelated captured rows. Permitted setup/window persistence and existing `/room/read` bookkeeping are a bounded named allowlist, not a blanket `/api/**` mutation grant. No Start/create/merge/delivery, Ask/Send, agent, provider or recording may run. Assert final temporary Program DB has no browser-created Programs/launches and inspect all attempted Program mutations.

Verify at 1440×900 and 393×852, plus an actually resized Room window on a wide Desk (use the current frame grip, not forced CSS):

1. The Programs fold occupies its accepted place without nested fold or sibling layout jump. Inspect long same-name titles, counts, state/turn words, empty/unavailable/last-read states, keyboard operation and accessible Open labels. Existing phone layout/read registration remains intact; no private People detail is added.
2. Open a row via keyboard and pointer. Observe exactly one `[id='pullout:program:<id>']`, actual ProgramBody identity/detail, front/hit ownership and preserved surviving Room. A store-call spy or ready flag is insufficient. Repeat Open and reopen a minimized existing Program where that control exists. Use the phone's current window menu/ring rather than a nonexistent desktop Iconify control. Test current exact-ID reuse/raise behavior, not a new back-navigation promise.
3. Return to the surviving Room using current window controls, not an invented special Program project-return action. Deliver a full captured `desk_changed` frame containing a matching Program change and changed Room response; see moved/new state without forcing a window switch, autosave or effect. Inject failed refresh/recovery and inspect the visible last-read distinction.
4. When current detail is unavailable, the existing Program detail failure remains truthful; do not infer Open success from void return or recreate the Program. Keep effect counters at zero, preserve observed current identity and inspect actual screenshots for clipping/overlap/hit ownership.
5. Stop browser/server in `finally` and inspect final temporary state before cleanup. Report fixture-backed geometry/focus evidence separately from live provider/real work execution, which this test does not establish.

After the new node exists, collect then run only that scoped node, under the same isolated HOME/cache/lock setup:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/e2e/test_room_glass.py -k project_program_continuity_geometry_and_focus
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/e2e/test_room_glass.py -k project_program_continuity_geometry_and_focus
```

Every accepted C13 row needs passing or explicitly blocked evidence, independent review and applicable integrated checks. Document source/fixture/runtime boundaries, current admission, no Program effects, rollback and remaining G13 choice. Product acceptance and shipping are separate.

### Creation-to-Room integration gate

**Conditional composed proof, not a new story or automatic dependency.** Apply only after S11’s D13 branch A/G11 and S13’s D15/G13-A are separately accepted and the combined proof is assigned. T13-02 owns this amendment and its sole capture producer; T13-03 verifies it with T11-03’s report. Each slice can otherwise complete on its own evidence without claiming this joint journey. No S12 opener rewrite, new production owner or live browser creation is required.

**Source contract.** `holdspeak/services/program_service.py::create` 1999–2015 commits the Program before checkpoint/requirements/changed/readback. `changed` 5022–5076 emits Program and desk notifications later. `holdspeak/web/announce.py::install` 173–193 adds a generic full-hub announcement for 2xx writes, a positive existing fallback; it does not repair a post-save 500. `holdspeak/runtime/composition.py::emit_desk_changed/_send_desk_changed` 187–239 coalesces all changes and catches broadcast failure. `web/src/desk/components/window/dockState.ts::deskChanges` 58–64 prefers a nonempty `changes` array; top-level kind is only the first change. Preserve these producers, do not add a reliable-event subsystem or claim delivery from an HTTP acknowledgement.

S11 `ProgramsCore.make`/`usePrograms.reload` (`web/src/desk/programs/ProgramsWindow.tsx` 154–166; `api.ts` 267–283) rereads only the global list. S13 receives its own Room snapshot via controller Phase 1 (`useProjectRoomController.ts` 95–161), a received qualifying debounced frame, explicit Refresh or real remount (`ProjectRoomCore.tsx` 2019–2036/2290–2293). Raising an existing same-scope window need not remount it. A missed event is not an observed read failure, so the proposed last-read warning cannot detect every stale snapshot. Refresh may fail/degrade or return a changed association; it is not a guarantee of finding an unknown write.

Both entry points open an acknowledged/returned row ID through `web/src/desk/programs/open.ts::openProgram` 4–5 → `store/compositorSlice.ts::openPullout` 324–336 → existing Program-family host. This bypasses ordinary surface-opener registration, preserves exact-ID dedup/raise and `projectReturn: null`, and does not depend on S12. A void return still does not prove mounted content/focus.

**Exact bounded proof amendment.** Existing thirteen-suite budget and one `programs13.json` capture remain. No new test file or fixture path. Five S13 suites remain editable for standalone work; **only for this assigned joint gate**, the existing `web/src/desk/programs/__tests__/programs.app.test.tsx` is a sixth editable suite for one consumer case, serialized with S11. Other seven suites remain unchanged regressions. Browser guards stay unchanged: S11’s browser lane is refusal-only, S13’s browser lane forwards no Program mutation. This is linked real-producer/fixture-consumer proof, **not one live browser create-to-Room transaction**.

1. Extend the existing sole capture node `test_project_program_continuity_records_scope_and_reads` in `tests/integration/test_desk_project_room.py`. For one ordinary create use exactly `{title: "New program", template: "fast-cycle", project_id: <explicit selected ID>}` **without repository**. Keep S13’s authenticated full hub, no lifespan, isolated state and no provider/launch. Register/file its task-owned local repository using the actual registry dependency and real resolution, following [S11’s exact source map](stories/HS-S11-program-creation-context.md#exact-source-map-and-ownership); do not patch `_project_source`/resolver or pass a raw repository to bypass the seam. Keep distinct project B/empty/archived fixtures where already needed, with unambiguous source membership.
2. Add a **proposed test-only `creationHandoff` record** inside that same sole-owned `programs13.json`, not another capture. Include actual project-choice response, Room-before, exact create request/status/body, Room-after, matching detail and full actual coalesced frames. Use the request/response record convention `{request: {method, path, json?}, response: {status, body}}`; actual hub bodies remain unchanged except documented temporary-path normalization. Assert selected project = request = stored association = returned Room member, and acknowledgement ID = Room row ID = detail ID. Another project sharing repository/title is excluded; no Start, inference, hand or delivery occurs. Do not import unrelated S11 capture IDs or hand-repair raw bodies. The existing node remains the only writer of the complete bundle.
3. Add one linked case to the existing Programs app suite: read the bundle’s choices, make the actual proposed G11 explicit selection/final press, assert the exact captured tuple, retain its acknowledged ID and invoke existing open/list behavior. The Room app consumes the corresponding captured Room/detail through actual decoder/controller. S11’s independent four captures remain untouched. The existing S13 browser proof observes that same exact row/detail ID and real host with Program mutations intercepted; do not call this a live backend UI transaction.
4. Strengthen existing assertion-only `test_project_program_continuity_records_failures`: inject at checkpoint entry **after real save**, keep the actual full-app create route and no extra capture. Compare isolated store IDs before/after to identify exactly one persisted Program, assert generic failure and no launch, and inspect every actual coalesced change for that Program’s create announcement. The injected pre-changed fault should produce none; do not infer this from top-level kind or from a bare-router test. Restore the hook, explicitly GET Room and exact detail through admitted routes, and prove the persisted association is discoverable on successful read. This set-difference is test-only evidence, never client reconciliation logic. Other incidental events do not establish a reliable create-discovery protocol.
5. In the existing Room app test, retain the before snapshot and deliberately deliver **no notification**. A global Programs reload or elapsed debounce time is not a Room read trigger. Explicit existing Refresh may then obtain the captured after snapshot; no Program POST, retry or fabricated empty state accompanies that read. Separately retain received-frame/burst proof and current Phase-1 failed-read/recovery truth. Unknown create does not automatically acquire an ID: the owner may inspect refreshed rows and explicitly open a returned ID, but the UI must not identify the old attempt by title, auto-open it, or repeat creation. Existing Room read-marker/window bookkeeping remains permitted, not a claim that Refresh is wholly write-free.

Run the same named V11/V13 focused commands only under the joint assignment, once per coordinated final test state rather than mechanically running duplicate unions. The existing S13 capture-owner invocation is still the sole recording command; a consumer never rewrites the capture. Record the selected joint cases and their actual results. If the real registry/full-hub setup or linked host identity cannot be established within current ownership, stop this combined proof for a bounded amendment; do not hold unrelated accepted slices or invent a new architecture. Full build/review/delivery and a single live end-to-end browser journey remain later HS-S91 proof, not a result of this source-only plan.

## V33 People Add recovery verification

**Source pin:** `80b641fa41c7352280cfa52e933acf6dbe8d3857`. [HS-S33](stories/HS-S33-people-add-recovery.md) / pending G33-A. All source/test paths below were inspected in the pinned archive, not imported or run. New node/bundle/helper names are proposals. One existing production file; backend, auth, store and ordinary workspace persistence remain read-only contracts. Same-mount recovery is not durable creation idempotence.

### Exact source and edit ownership

| Existing repository path | Symbols / contract | Ownership |
| --- | --- | --- |
| `web/src/pages/cores/PeopleCore.tsx` | `select` 352–366, `selected` 433, roster `RelationshipPane` 478; `PersonWindowBody.read` 726–745 and pane 776; `RelationshipPane`/mounted Prep; `PrepAddWell` 991–1009; `PrepPane.run` 1102–1105, `addOwe` 1115–1122, `accept` 1132, Asked-of-you 1276–1278 | **Only production edit**: local attempt/read identity, controls, scoped failure/protection, conservative draft custody |
| `web/src/lib/api.ts` | `apiFetch` 54–78; JSON parse failure becomes `{}` even on 2xx | Read-only; validate relied-on payload locally, not a global parser redesign |
| `web/src/desk/deskMemory.ts`; `web/src/desk/store/compositorSlice.ts`; `web/src/desk/store/workspaceStorage.ts` | `useDeskDraft`/`keptDraft`; `setDraft` 306–312 replaces map on real writes and no-ops equal value; ordinary workspace serialization | Read-only; no receipt persistence or shared revision API |
| `holdspeak/services/people_service.py` | `get_relationship` 174–196; `create_request` 247–255; `accept_request` 300–329; service-only `get_request` 331–338; `_require_owner`/`_require_reader` 1939–1951, `_require_ready_owner` 1953–1964; `_create` 1973–1977; `_record_view` 2065–2066 | Read-only identity/authority/projection. Request input `source` is not copied; not a correlation key |
| `holdspeak/people/store.py` | `put` 127–139; `create` 154–163; `accept_request` 243–304; `_ready_connection` 405–424 | Read-only fresh create IDs, same-ID acceptance transaction/replay, post-commit uncertainty |
| `holdspeak/people/keys.py` | `FileKeyStore.get`/file load 145–182; no key cache | Read-only key/readiness contract; only synthetic temporary key files may be fault-injected in future tests |
| `holdspeak/web/routes/people.py`; `holdspeak/web_server.py`; `holdspeak/principals.py` | `_failure` 37–64, relationship GET 175–183, create 250–255, accept 322–327; `_web_auth_gate`; `required_right` | Read-only owner HTTP boundary and actual routes. No GET-request endpoint; live-reader service permission is not HTTP owner authority |
| `tests/unit/test_desk_needs_you.py`; `tests/conftest.py` | `_boot` 32–74 and `hub` 78–83; TestClient patch 49–58 injects `X-HoldSpeak-Token` | Read-only full-hub producer setup; remove both automatic token and Authorization for unauthorized proof |
| `tests/unit/test_desk_speak.py`; `tests/e2e/glass_infra.py`; `web/src/test/wireShape.ts` | `_record` 262–278; isolated real-server `_boot`/`_ensure_build`; `inventedFields` | Reuse unchanged helper/rig/shape fence. Scalar/ID/outcome assertions are additional, not inferred from shape |

Line numbers are rediscovery aids, not permission to ignore drift. Inspect existing callers of exported `RelationshipPane` and both active hosts before narrowing host guards. Do not move/replace the whole People component because of its line count.

### Exact test and capture budget

Nine existing suite paths are in the focused proof union. Five may be edited, four are unchanged regressions. No new test module is needed.

| Existing path | Scope |
| --- | --- |
| `tests/unit/test_people_store.py` | Unchanged replay/transaction/ID regression; source test `test_accepting_request_is_atomic_and_idempotently_returns_one_commitment` is positive evidence, not already-run fault injection |
| `tests/unit/test_people_service.py` | Unchanged request-versus-promise/active-person regression |
| `tests/unit/test_people_routes.py` | Unchanged thin-route/injected-principal regression, not full-edge authentication proof |
| `tests/unit/test_people_no_leaks.py` | Unchanged private-store/ordinary-DB leakage regression; not browser draft-custody proof |
| `tests/integration/test_desk_people.py` | **Editable**: full real-hub producer, request/accept states, failure/admission cases, one capture owner |
| `web/src/pages/cores/__tests__/peopleCore.test.tsx` | **Editable**: actual Core/Prep state/races, scoped failure/draft guard. Correct only Owe-specific misleading mocks; preserve agenda/report-owes behavior |
| `web/src/desk/__tests__/people.app.test.tsx` | **Editable**: actual PersonWindowBody/host and raw producer envelopes, independent person reads/late responses |
| `web/src/desk/__tests__/deskRemembers.philo1307.test.tsx` | **Editable**: narrow same-text/other-window draft map and close/reload residual assertions; keep broader workspace behavior |
| `tests/e2e/test_desk_glass.py` | **Editable**: one scoped keyboard/focus/geometry class/node using current rig; no business-logic duplicate browser matrix |

One **proposed new synthetic capture file**: `web/src/desk/__tests__/fixtures/people-add-recovery.json`. Proposed sole capture node: `tests/integration/test_desk_people.py::test_people_add_recovery_wire`. Proposed other producer names use `people_add_recovery` in that same module. Only the capture node calls `_record("people-add-recovery", ..., folder=<existing fixtures directory>)`, writing the complete bundle once. Other cases never write it, including under xdist. Source helper uses **HOLDSPEAK_WIRE_WRITE=1**, not the different `HOLDSPEAK_WRITE_WIRE_FIXTURES` used by the existing opposite-direction chair producer. Keep all recording flags off in normal proof. Initial capture is a separately assigned test/fixture write; review generated diff and synthetic provenance, never hand-edit returned fields.

Bundle covers readiness, relationship before/create/requested/accepted/terminal reads, request and commitment responses, and named safe refusal payloads. Preserve linked opaque IDs within a scenario; use fresh real IDs across independently created requests. Record raw source responses plus separate scenario labels/call ledger, not invented endpoint fields. A shape fence alone cannot prove exact IDs, state or cardinality. Preserve existing `people-wire` folder and report-owes captures unchanged.

### Real producer and consumer contract

The integration producer imports the existing `hub` fixture from `test_desk_needs_you.py`. It constructs real `MeetingWebServer(...).app` and authenticated TestClient **without** `server.start()` or entering TestClient lifespan, so startup/background loops do not run in that producer. Its HOME, ordinary DB, file-backed People test key and derived encrypted sidecar stay under the temporary path. No native Keychain, owner database, external engine or daily-work seed is required. Inspect current opt-outs and setup route before execution; temporary FileKeyStore is deliberate test custody, not a new production key policy.

Required real producer cases, asserted through current routes/service and final encrypted state:

1. Setup a synthetic person, create two requests with identical words and prove IDs differ. Accept only one Q and replay Q; prove exactly one matching leader-owes commitment, canonical identity and unchanged terminal lifecycle/history after Done/dismissal. A request alone is not yet a commitment.
2. Force a failure before the second acceptance write and verify transaction rollback leaves the request requested and no commitment; restore injection and accept Q once. Separately execute real acceptance then suppress only its observed response, so final read proves the committed identity despite client uncertainty. Do not fake the database result.
3. Inject create failure **after** persistence at its private-file/readback seam, restore the seam and inspect persisted request count. A no-ID 503 can represent saved work. `_note_writes` is defensive bookkeeping, not a naturally failing production claim; use any such seam only as explicit fault injection.
4. Check exact owner edge and pre-write errors, before/after archive, missing request and invalid state. Remove both `X-HoldSpeak-Token` and `Authorization` for anonymous/agent edge cases; the global TestClient patch otherwise silently authenticates the test. Verify unauthorized body cannot set principal. A later refusal does not erase a previously known Q.
5. Public projection contains no accepted_commitment_id. Match exact Q/R and one canonical commitment with compatible leader-owes direction; terminal commitments are valid evidence. Optional first-accept body override is legitimate: show actual saved words/state, never replace/recreate merely because words differ. Service active-person checks precede store replay; do not claim archive plus replay is one atomic admission transaction.

Known no-effect codes apply only to **this invocation**: production `principal_right_required`; service `people_owner_required`; create `people_relationship_not_found`, `people_payload_required`, `people_payload_invalid`, `people_payload_too_large`, `people_visibility_invalid`; accept `people_request_not_found`, `people_relationship_not_found`, `people_payload_invalid`, `people_payload_too_large`, `people_request_not_acceptable`. Verify exact current path before classification. Generic service write failure is publicly redacted to store-unavailable; 503 and network/malformed results remain uncertain. Existing valid request identity survives a later accept refusal. Protection may require hiding its private receipt, not declaring it absent. `_require_ready_owner` maps missing/locked/corrupt-key readiness to generic store-unavailable, so mutation503 alone cannot prove ordinary outage. Use the existing read-only `/api/people/readiness` contract: current ready permits retention; nonready clears protected context; failed/malformed readiness invokes G33’s explicit protective fallback, loses the private in-memory binding and requires later manual inspection without automatic effects. Preserve ordinary drafts under their existing lifetime. Producer proof must exercise actual test-key/readiness behavior, not only hand-injected423/key codes. At this pin FileKeyStore rereads its file for every get. In the no-lifespan hub only, retain the synthetic `tmp_path/people.key` bytes in test memory; write `{}` to produce missing-key/key_unavailable, or malformed JSON to produce locked readiness. Assert the generic 503 and actual readiness response/no acceptance, then restore the exact test bytes and 0600 mode in finally and reread durable IDs. Never log/capture key bytes, use NativeKeyStore or touch owner files. Recheck this no-cache behavior at execution drift validation; the separate glass rig uses a different temporary HOME path.

Consumer tests feed these raw envelopes through actual Core and PersonWindowBody. Hold/release promises, not arbitrary sleeps. Cover C33 with both forbidden-call counts and visible state: rapid dispatch, generic busy overwrite, wrong/old host read success/failure/loading, Back/unmount/close, fold/lens, auth/key clear and late response, malformed 2xx, incomplete relationship arrays, matching Asked-of-you accept, terminal/mismatched saved words, current refresh failure, real503/readiness ready/nonready/unavailable outcomes and newer/cross-window same-text draft edits. A requested record plus an unexpected matching commitment is a mixed observation, not an invitation to accept automatically. Check is always read-only. Full unmount/reload must document lost receipt binding and existing persistent draft, not pretend recovery survived. No text-based rebinding or automatic remount acceptance.

### Focused commands and execution limits

Follow [setup/isolation](#setup-and-isolation), current scoped instructions and assigned roles. Resolve actual browser cache, installed dependencies, temporary key/store and local-server allowance first. Collection imports application code and is an execution action. The following Bash recipe composes the source-defined lock/pytest/Vitest forms with the verified paths; it was **not run** during planning. Use the assigned subset while developing; this is the full non-browser accepted-story union.

```sh
(
  set -euo pipefail
  : "${HS_PLAYWRIGHT_CACHE:?Resolve the actual host browser cache first}"
  : "${HS_EVIDENCE_DIR:?Set an absolute task-owned evidence directory}"
  HS_REAL_HOME="$HOME"
  mkdir -p "$HS_EVIDENCE_DIR"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_PLAYWRIGHT_CACHE"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  unset HOLDSPEAK_WIRE_WRITE HOLDSPEAK_WRITE_WIRE_FIXTURES HOLDSPEAK_EVIDENCE_WRITE
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/integration/test_desk_people.py -k people_add_recovery | tee "$HS_EVIDENCE_DIR/producer-collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/integration/test_desk_people.py -k people_add_recovery | tee "$HS_EVIDENCE_DIR/producer.log"
  py_files=(tests/unit/test_people_store.py tests/unit/test_people_service.py tests/unit/test_people_routes.py tests/unit/test_people_no_leaks.py)
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/regression-collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/regression.log"
  (
    cd web
    uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 src/pages/cores/__tests__/peopleCore.test.tsx src/desk/__tests__/people.app.test.tsx src/desk/__tests__/deskRemembers.philo1307.test.tsx
  ) | tee "$HS_EVIDENCE_DIR/web.log"
)
```

The `-k people_add_recovery` nodes do **not** exist at the baseline; first characterize existing suites and then collect new nodes only after implementation creates them. Empty collection is blocked proof, not success. For initial capture, the authorized owner runs only proposed `test_people_add_recovery_wire` with `HOLDSPEAK_WIRE_WRITE=1` under this same isolation/lock after reviewing the node; then turn recording off and rerun. No fixture write is performed by this package.

Run source-defined `npm --prefix web run typecheck` and `npm --prefix web run guard:architecture` in the assigned checkout. Record baseline, expected-red, collected/executed counts, skips, exits and final tails separately. After final shared edits the current [integrated gate](#integrated-gate) belongs to its assigned owner; it can fetch/build/test and cannot be nested under another lock. A green no-change/empty/skipped result is not S33 proof.

### Bounded actual-browser proof

Add proposed `test_people_add_recovery_geometry_and_focus` (or a parameterized same-named method) to existing `tests/e2e/test_desk_glass.py`. Reuse `_ensure_build`, `_boot`, `_normal_chair`, the existing active window path and current ownership probes. The existing `_TRAP` capture handler stops React click actions: use it only for isolated geometry measurements, then remove it before Add/Check/Accept/Enter and late-response interaction proof. Assert actual intercepted network attempts, not trap hit counts. This browser rig **starts a real temporary HTTP server and lifespan**; it is not the no-background producer. Inspect current CLI/agents/tool probes/LAN/active target/screen/Calls/Line/Programs/phone/Telegram/recording/mic opt-outs before execution. Verify synthetic temporary FileKeyStore/DB only and cleanup in `finally`.

Use real producer bundle envelopes for intercepted People domain reads/writes, plus a bounded named setup/window allowance. Install interception/fail-closed guards before navigation. Do not forward request/accept/Done/Send to a real service in this browser case; persistence and transaction proof belong to the producer above. Count attempted requests and preserve linked synthetic person/request/commitment IDs across the host and bundle; no invented key or stale setup identity. Existing setup/window persistence may run locally only when listed; no blanket `/api/**` mutation allowance, microphone, provider or external effect. Final local state/call ledger must show no browser-created People request or commitment.

At **1440×900** and **393×852**, inspect actual Add/Check/Accept/new-promise controls, warning/saved wording, long submitted/actual saved text, keyboard Enter/tab/focus, touch hit ownership and no clipped receipt or misleading enabled action. Hold create while closing/switching the person; release the late response and prove no unintended accept/focus steal. Keep business-logic permutations in app/producer tests. Save shots using the existing `tests._evidence.evidence_dir` convention and inspect them; screenshot existence alone is not acceptance. Fixture-backed visual proof is not a live privacy/provider exercise.

After the proposed node exists, collect then run it under the same isolated HOME/cache/lock setup:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/e2e/test_desk_glass.py -k people_add_recovery_geometry_and_focus
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/e2e/test_desk_glass.py -k people_add_recovery_geometry_and_focus
```

Each accepted C33 row needs actual passed/failed/blocked evidence, independent review and applicable integrated checks. Report saved request versus commitment, known versus unknown creation, same-mount limits, unchanged private custody, rollback and remaining G33 choice. No application tests, browser actions or source mutations ran to write this plan.

## V43 Obligation coverage verification

**Source pin:** `80b641fa41c7352280cfa52e933acf6dbe8d3857`. [HS-S43](stories/HS-S43-obligation-coverage.md), pending D22/G43-A. Paths below were inspected as source data, not executed. Proposed test/capture/class names are not existing APIs or passing results. Two existing frontend production owners; all data/authority/navigation owners remain unchanged.

### Exact source and edit ownership

| Existing repository path | Symbols / contract | Ownership |
| --- | --- | --- |
| `web/src/desk/needs/NeedsDrawer.tsx` | `NeedsChipRow` 1051 onward; `NEEDS_READS_CAP_MS` 1135; `useNeedFaces`; `NeedsDrawer` 1249 onward; header/filter counts 1285–1305, seen bookkeeping 1315–1335, toolbar/source disclosures/People warning/list/footer 1358–1452 | **Editable**: one static scope note and normal People button only |
| `web/src/desk/needs/needs.css` | Drawer flex/ledger layout and `[data-settling]` 95–100 | **Editable**: local note spacing/wrapping; preserve loading concealment and one ledger scroll |
| `web/src/desk/needs/needsFace.ts`; `web/src/desk/needsYou.ts`; `web/src/desk/coverage.ts`; `web/src/desk/people/PeopleReadFailed.tsx` | `passesChips` 209–219; `needsHead` 956 onward; current store/read coverage and People-unread mapping | Read-only counts/filter/coverage; note is neither a member nor a source gap |
| `holdspeak/services/people_service.py` | `get_relationship` 174–196; project_refs 205–215; `list_cards` 1867–1893; existing owed/brief/lifecycle and owner/reader checks | Read-only exact obligation directions and encrypted public view; no new aggregate or project inference |
| `holdspeak/services/follow_through_service.py`; `holdspeak/services/door_service.py`; `holdspeak/services/needs_you_membership.py` | `board` 156 onward, People overlay 288–308, `people_store_state` 316 onward; `asking_board` 172–193; `door_items` 107–172, `_read_door` 1604–1619 and final projection | Read-only synchronous overlay, project exclusion, selected rows and availability truth. `door_items` is a function in needs_you_membership, not a separate file |
| `holdspeak/web/routes/follow_through.py`; `holdspeak/web/routes/projects.py`; `holdspeak/web/routes/people.py`; `holdspeak/web_server.py` | Existing `/api/follow-through/board` project_id query; `api_desk_needs_you` composes then applies `filter_answer` with separate `project` query; existing People detail/readiness routes; production owner edge | Read-only routing/authority. UI does not gain rights by opening a window |
| `web/src/desk/shell.ts`; `web/src/desk/applications.ts`; `web/src/desk/store/compositorSlice.ts`; `web/src/desk/components/SurfaceWindows.tsx` | `openSurfaceOr` 116–123; `open-people` static application 554 onward; `openSurfaceWindow` 537 onward; host/lazy body (registered at the pin) | Read-only actual normal destination/reuse. `/` fallback is not a People-mount acknowledgement; no registry rewrite within S43 |
| `web/src/pages/cores/PeopleCore.tsx` | `PeopleCore` scope/project initialization 224–231, remembered selection 377 onward, roster/filter/search and `RelationshipPane`/Prep owed-to-you view | Read-only current/saved place; no reset, forced lens, private prefetch or new presentation |
| `tests/unit/test_desk_needs_you.py`; `tests/unit/test_desk_speak.py`; `tests/conftest.py`; `tests/e2e/glass_infra.py` | Existing no-lifespan `_boot`/`hub`; `_record`; injected TestClient token; isolated browser server `_boot` | Reuse test infrastructure unchanged; key custody and browser side-effect guards require actual setup inspection |

Line numbers are rediscovery aids; symbols and current behavior decide drift. Exact normal opener is `openSurfaceOr("open-people", "/")`, without scope/options. `openPerson(id, "prep")` exists for an actual relationship ID but is not this branch. Ordinary names and Needs filter keys do not authorize guessing that ID.

### Exact focused budget

Eight existing suite paths; four editable and four unchanged regressions. No new test module or browser framework.

| Existing suite | Scope |
| --- | --- |
| `tests/integration/test_desk_people.py` | **Editable**: bounded full-hub directional/coverage producer and sole capture node |
| `tests/unit/test_people_service.py` | Unchanged direction, relationship/brief retention and lawful lifecycle regression, including `test_philo17_they_owe_you_is_a_commitment_the_other_way` |
| `tests/unit/test_desk_needs_you.py` | Unchanged actual ordinary waiting, attention/header count and filter producer regression |
| `web/src/desk/needs/__tests__/NeedsDrawer.test.tsx` | **Editable**: settled/empty/filter/muted/error note and unchanged counts/no-extra-browser-read matrix |
| `web/src/desk/__tests__/people.app.test.tsx` | **Editable**: raw bundle → actual Needs store/drawer → SurfaceWindows → People host, retaining existing context |
| `web/src/desk/__tests__/needs-you.app.test.tsx` | Unchanged recorded actual-wire Needs/gate/read behavior |
| `web/src/desk/__tests__/surface-windows.test.tsx` | Unchanged current compositor/host/scope lifecycle; registration is the pinned mechanism |
| `tests/e2e/test_desk_glass.py` | **Editable**: one scoped wide/phone/narrow-short focus/touch/geometry node with current rig |

One **proposed new capture**: `web/src/desk/__tests__/fixtures/needs-people-coverage.json`. Proposed sole writer: `tests/integration/test_desk_people.py::test_needs_people_coverage_wire`; other proposed producer cases use the `needs_people_coverage` name prefix but do not write. Reuse `_record("needs-people-coverage", ..., folder=<existing fixtures directory>)` and its **HOLDSPEAK_WIRE_WRITE=1** convention only for an authorized initial/regeneration run. All normal tests run with recording flags off. Preserve existing fixtures, including S33's separate proposed bundle; neither slice requires the other to be implemented.

Capture a complete synthetic scenario bundle once, with raw Needs, Door, unfiltered/project-filtered board, readiness, roster, relationship and brief responses plus separate provenance/scenario metadata. Keep cross-response IDs coherent and assert values/cardinality/direction independently of `_record`'s shape fence. No copied real names, commitments, credentials or key bytes. Multiple xdist workers must not overwrite the same file. A consumer must not hand-edit fields and call them source-produced.

### Producer and actual-host proof

Use `test_desk_people.py`'s imported existing `hub` from `test_desk_needs_you.py`. That fixture constructs a real authenticated `MeetingWebServer(...).app` and TestClient **without server.start or a TestClient lifespan context**. Its ordinary DB, temporary HOME, FileKeyStore and encrypted People sidecar are isolated; no native Keychain, owner data, provider or background startup loop is needed. Existing producer helpers may be reused after inspection; do not seed daily automation/agents merely to obtain a waiting row.

1. Create a synthetic relationship and real leader-owed/report-owed commitments in shared-intent and leader-private visibility. Assert the exact leader-owed IDs appear in the permitted Follow-through/Door/Needs overlay, while report-owed IDs and bodies remain absent from it and present in relationship/brief owed_to_you. Assert the ordinary action records do not gain copies of People bodies. The test must preserve actual producer authority, not fabricate a unified row DTO.
A report-only scenario can legitimately have other setup/source rows: assert absence of the report-owed IDs, not a fabricated zero complete producer response. Fully empty presentation tests may use the existing explicit empty mock seam, labeled as UI proof rather than real-hub completeness.

2. Produce ordinary waiting work with the existing real meeting/action/Follow-through setup patterns in `test_desk_needs_you.py`, including its attention-versus-waiting regression. Assert its current `direction: "theirs"` and the distinct headline/filtered-count meanings. Do not infer all ordinary obligations appear, or sum the header/chip counts into a total.
3. Link the relationship to a synthetic project. Compare real `FollowThroughService.board(..., project_id=...)` / admitted `/api/follow-through/board?project_id=...` with its unfiltered answer; no People overlay is implied by project_refs. Also check the actual `/api/desk/needs-you?fresh=1&project=...` response and feed unfiltered Needs data through the real frontend chip filter. Needs uses `project`; Follow-through uses `project_id`. Prove projectless exclusion separately at both actual boundaries. Backend project filtering and client chip filtering are different boundaries.
4. Characterize ready, unconfigured, no-key-store and unread states through existing producer contracts. Existing source/People warnings remain truthful and independent of the static note. For full-edge unauthorized cases remove both `Authorization` and automatically injected `X-HoldSpeak-Token`; otherwise the global TestClient fixture can silently authenticate. No new permission or direct store access is a recovery mechanism.
5. Replay the bundle through actual Needs store/drawer and current People host in the existing app test. Do not mock the shell opener for the host case. Verify no new browser `/api/people/*` request before Open; existing Needs/door backend reads can already access their authorized overlay. After Open, allow existing People reads, never infer broader rights or new aggregate data.
6. Establish the actual ready/admitted host entry for cold and warm People state (registered at the pin). If S12 is already present, apply the [landing-order gate](#navigation-and-people-landing-order-gate), not a requirement to resurrect its retired registration. Test saved person, existing project-filtered roster/search/lens, repeated open and return to unchanged chips in a surviving mounted Needs window. Existing unmount may reset local chips; no new persistence/return contract is added. The normal unscoped open may update window scope without remounting/resetting PeopleCore's local state. Observe `[id='surface-people']` and actual rendered body/content, not only a store call. At the pin a fallback-only test records navigation to `/`; after an accepted S12 cutover use its reviewed compatibility/admission contract. Neither a fallback nor deferred/handled return alone proves People mounted.
7. Hold/release Needs/Door reads and use controlled fake timers in component tests for the current **8-second** reveal cap. Keep the static note under the same veil and present after cap even while reads remain unresolved. Cover complete empty/no chips, filtered empty, muted, source gap and People unread together. Preserve the row-list/head/chip input outputs exactly.
8. Inspect attempted-call ledgers. New note/CTA must add no People mutation, request/accept, Done/Nudge/Note/Send, export, aggregate fetch or private context persistence. Existing `/api/desk/needs-you/seen` and ordinary window/workspace bookkeeping are a named allowance; a blanket no-POST assertion is incorrect. Today and briefing behavior is out of scope, not proven complete by this test.

### Focused commands and honest status

Follow [setup/isolation](#setup-and-isolation) and current repository/scoped instructions. The recipe below is composed from source-defined lock/pytest/Vitest forms and verified file paths; **none ran during planning**. Collection itself imports application code and needs an execution assignment. Resolve safe HOME/key/DB, installed dependencies, actual Playwright cache and local-server allowance first. Use the assigned subset while developing; this is the accepted-story non-browser union.

```sh
(
  set -euo pipefail
  : "${HS_PLAYWRIGHT_CACHE:?Resolve the actual host browser cache first}"
  : "${HS_EVIDENCE_DIR:?Set an absolute task-owned evidence directory}"
  HS_REAL_HOME="$HOME"
  mkdir -p "$HS_EVIDENCE_DIR"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  export PLAYWRIGHT_BROWSERS_PATH="$HS_PLAYWRIGHT_CACHE"
  export npm_config_cache="$HS_REAL_HOME/.npm"
  unset HOLDSPEAK_WIRE_WRITE HOLDSPEAK_WRITE_WIRE_FIXTURES HOLDSPEAK_EVIDENCE_WRITE
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/integration/test_desk_people.py -k needs_people_coverage | tee "$HS_EVIDENCE_DIR/producer-collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/integration/test_desk_people.py -k needs_people_coverage | tee "$HS_EVIDENCE_DIR/producer.log"
  py_files=(tests/unit/test_people_service.py tests/unit/test_desk_needs_you.py)
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/regression-collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/regression.log"
  (
    cd web
    uv run --project .. python ../scripts/test_lock.py -- ./node_modules/.bin/vitest run --maxWorkers=8 src/desk/needs/__tests__/NeedsDrawer.test.tsx src/desk/__tests__/people.app.test.tsx src/desk/__tests__/needs-you.app.test.tsx src/desk/__tests__/surface-windows.test.tsx
  ) | tee "$HS_EVIDENCE_DIR/web.log"
)
```

New `-k needs_people_coverage` nodes do not exist at baseline. First characterize existing source suites, then collect new nodes after implementation; empty collection is not a pass. Initial capture is a separate authorized run of only proposed `test_needs_people_coverage_wire` with HOLDSPEAK_WIRE_WRITE=1 under the same isolation/lock. Review synthetic output, disable recording, rerun the union. A new capture is not created during plan authoring.

Run source-defined `npm --prefix web run typecheck` and `npm --prefix web run guard:architecture` in the assigned checkout. Record baseline, expected-red, collection/execution counts, skips, exits and final logs. The current [integrated gate](#integrated-gate) belongs to its assigned owner after final shared edits; it may fetch/build/test and must not be nested under another lock. No-change or empty/skipped success is not coverage.

### Bounded browser geometry and entry

Add proposed `test_needs_people_coverage_geometry_and_entry` to existing `tests/e2e/test_desk_glass.py`. Reuse current `_ensure_build`, `_boot`, `_normal_chair`, actual window controls and `tests._evidence.evidence_dir` screenshot convention. This browser rig starts a real isolated local server/lifespan; it is not the no-startup producer. Inspect current CLI/agent/tool-probe/LAN/Calls/phone/recording/microphone opt-outs and temporary FileKeyStore/DB before running; stop on an unsafe fixture.

Install captured Needs/People read responses and fail-closed domain mutation guards before navigation. Permit only explicitly named synthetic setup/window/seen bookkeeping; no broad `/api/**` mutation allowance. People request/accept/commitment/Note/Send/recording/provider operations remain intercepted/refused. Final temporary domain state and attempted-call ledger must match that boundary. Use coherent synthetic IDs throughout; don't silently mix captured people/project IDs with unrelated setup records.

At 1440×900 and 393×852, then a genuinely narrowed/shortened Needs window using current frame controls, inspect the combined worst case: scope note + expanded missing-source disclosure + People-read failure + several ledger rows + footer. Verify wrapping, scroll access, keyboard order, button hit ownership, no clipped text/CTA, no overlap and no disappearing row actions. Preserve the initial veil and normal reveal, not new late-layout movement. Existing `_TRAP` click-capture probes stop React actions: use them only for geometry measurements, remove them before actual Open People keyboard/pointer/touch proof and assert real intercepted reads/host content.

Open People, observe the actual existing surface/body, then return through current window controls to unchanged Needs chips. The browser proves genuine navigation/geometry, not a live private-data operation or new obligation aggregate. Keep detailed business permutations in producer/app tests. Inspect screenshot pixels, not only file existence, and stop server/browser in finally after final-state inspection.

After the node exists, collect then run under the same isolated HOME/cache/lock setup:

```sh
uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal tests/e2e/test_desk_glass.py -k needs_people_coverage_geometry_and_entry
uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal tests/e2e/test_desk_glass.py -k needs_people_coverage_geometry_and_entry
```

Every accepted C43 row needs actual passed/failed/blocked proof and independent review. Report exact coverage/destination limits, unchanged encrypted authority, source/fixture/runtime distinctions, rollback and remaining decisions. No app code/imports, product tests, browser, Git or provider operation ran to author this plan.

## V24 Program spending contract readiness

**Source pin:** `80b641fa41c7352280cfa52e933acf6dbe8d3857`. [HS-S24 gate](epics/HS-E20-program-contracts.md#hs-s24-spending-contract-gate), [HS-T24-01](tasks/HS-T24-01-spending-contract.md), pending D20/G24. This is a source/contract checkpoint, **not an implementation plan for an accepted cap**. No production or test edit is assigned. Current caller facts, historic design promises, future proof and unknown provider capabilities are separate. No application import, test, build, Git, engine/provider or browser operation ran to write this section.

### Current value and authority contract

| Existing source | Verified behavior at the pin | Limit on the claim |
| --- | --- | --- |
| `holdspeak/services/program_service.py::ProgramService.create` 1914–2000, especially 1945–1951/1977 | Converts non-null amount with `float`, rejects conversion failure and negatives, stores `spend_limit_usd` | No explicit finite/type predicate. Validation alone does not prove how every transport, DB or serializer handles a value |
| `ProgramService.update` 2023–2061; `_require_writer` 1720–1729 | Owner or creator-agent can update; null/empty string clears, otherwise float conversion; no matching create-negative/text-lowering check | Ordinary writable numeric state is not deliberate owner spending consent |
| `holdspeak/services/program_text.py::Head.spend`, `from_wire`, `render`, parser, `_lowers_head` at 177/385/546–547/968–972/1199–1200; service `text_apply` 4163–4187, `_agent_bar_rows` 4199–4225, `_apply_text` 4283–4288 | Canonical `spend up to $<number>` round-trips to the stored amount. Raising it or adding one is a lower-bar row; only owner may approve lowering. Direct update differs | Do not silently unify these writer semantics, rename syntax or infer old consent |
| `holdspeak/db/programs.py` 15/32–55; `holdspeak/db/schema.py` 5213–5221; service wire 1648 | Nullable REAL persisted and exposed as `spend_limit_usd` | Stored/requested amount is not proof of an enforced ceiling |
| `holdspeak/services/program_runner.py::_spend_core` 603–616, ready dispatch 582–593 | Returns immediately for non-Pi profiles or historical `core_cleared: ["spend"]`. For explicit hosted/cloud/remote_paid Pi, only null amount supplies a synthetic `$1` trigger; any non-null amount avoids this question | Zero does not mean enforced zero spend. The synthetic value is neither measured nor predicted cost. Missing explicit engine is not evidence of a free engine |
| `ProgramService._decide` 2675/2759–2770 | Owner Go on clears the current core and appends the kind to step facts/history | No amount/engine/model/revision/scope/expiry binding. Preserve history; do not upgrade it to a new unlimited permission |
| `holdspeak/services/program_rules.py::is_core` 98–128; runner `diff_facts` 1605–1634 and `_after_check` 1653–1659 | Comparator supports positive supplied cost versus supplied limit; the inspected real fact producer supplies repository facts, not accumulated cost | Passing synthetic-cost tests cannot establish a runtime dollar cap |

T24 must explicitly characterize **absent/null, empty-string clearing, booleans, zero, positive, negative, nonnumeric and non-finite** inputs across create/update/text. Python float accepts bool; direct update clearing differs from create. Keep validation, persistence, wire serialization and dispatch separate, particularly for non-finite values. Do not execute speculative values against owner state or assert end-to-end acceptance from a parse expression.

### Exact caller and transport map

All paths in this table are existing **read-only context** for T24. A selected future branch must name its actual editable subset rather than treating the table as permission for a subsystem rewrite.

| Caller | Exact source / current seam | Required scope disposition |
| --- | --- | --- |
| Ordinary ready-step builder | `holdspeak/services/program_runner.py::_hand_step` 904–924 after `_spend_core`; `holdspeak/services/agent_hand_service.py::hand/_hand` 394–472/654–664 | Explicit Pi paid boundary, missing engine/default route, local/private/LAN and subscription profiles differ. Hand arguments carry engine, not Program dollars |
| Handoff | Runner `_limit_follow` 788–791, `handoff` 820–845; service `handoff` 2904–2936 | Direct hand does not reuse the money question. A usage-limit fallback is not a dollar-budget check |
| Review and builder rehand | Runner `_attach_review` 1687–1720, `_rehand_for_review` 1743–1769; `holdspeak/services/agent_review.py::_start_reviewer` 417–443; `holdspeak/services/agent_helpers.py::start_helper` 273–290 | Reviewer pair/helper and review-wait builder hand are separate launches, not free merely because they review or wait |
| Direct Program hand and continued turns | AgentHandService above accepts `program_step`; runner `prompt_builder` 331–346 and `prompt_launch` 348–356 | An initial runner check cannot establish direct-hand or later-turn enforcement. Active work/cutover requires an explicit policy |
| Draft Plan/Split | `holdspeak/services/program_planner.py::plan` 341–413 and `_call` 310–336 | Draft-time inference can precede Start, perform a separate size-split pass and retry unusable answers; its token sizing is not dollars |
| Automatic dispatch-time sizing/split | `holdspeak/services/program_runner.py::_dispatch` 571–593; `holdspeak/services/program_split.py::dispatch_hold` 201–235, `ask` 155–184 and `_ask_and_act` 246–274; shared shaper resolver/invoke 295–348 | A separately routed `program.split` call can precede the builder money question. Secure/Normal Apply/Skip handles the returned split, not permission before inference; include/exclude/unknown scope must be explicit |
| Shape/spoken shaping | `holdspeak/services/program_shaper.py::shape` 450–485, `resolve_engine` 295 onward, `invoke` 321–348 | Shared CanonicalPromptAdapter uses routed planning/Ask fallback and may retry; amount in prompt prose is not transport |
| Round generation/answer shaping | `holdspeak/services/program_rounds.py` 268–284 and shared shaping | Include/exclude retries and answer shaping deliberately; not automatically covered by builder gate |
| Night item planning | `holdspeak/services/program_night.py::ask_item` 566–587 and `plan_pending` 608 onward | Uses shared planning invocation and token sizing, not dollars. Local-builder policy does not prove this planner is cost-free |
| Effective Pi transport | `holdspeak/delivery/factory_launch.py::pi_engine` 1020 onward, Pi launch construction 1320–1340; `holdspeak/delivery/pi_launch.py::PiEngine`, `coding_engine`, `models_document`, `launch_args` 81–132/270–280/346–361; `holdspeak/agent_context/pi_extension/holdspeak-pi.ts` 178–300 | Inspected launch/config/hooks carry no Program amount-to-cost control. This bounded trace does not disprove independent provider/account controls |

**Dispatch-time split ordering matters to the spending decision.** This is different from splitting an editable Draft in `program_planner`. For a ready step that does not fit, `program_split.ask` resolves `agent.plan` or the Ask fallback independently of the builder and uses the shared inference path without Program dollar transport. An unusable first answer can cause a second invocation; a missing engine or no answer follows the existing failure path. The call occurs before the later builder idle/capacity and `_spend_core` checks. Preserve the earlier night/home gates and the split path’s already-held core, in-flight/proposed and no-repeat-split guards; this is not a claim that every waiting step invokes a planner or bypasses all admission. `_ask_and_act` obtains the answer before proposing Apply/Skip under Secure/Normal; its later current-step check does not make that proposal pre-call spending permission. Record this caller’s scope and actual ordering before a chosen branch claims to hold covered paid calls. No observed charge, universal absence of provider controls, new approval policy or implementation is inferred.

The existing `tests/unit/test_program_sizing.py:65–90` asserts a recorded split-planner call while the builder remains unhanded and Apply/Skip is only then presented; 93–118 covers later Apply/Skip, and 144–194 covers no-slot, no-engine, already-split and fits cases. `tests/unit/test_program_shaper.py:53–65` installs the recorded engine through the inference seam. These are source witnesses, not executed results, a paid-engine test or cap proof. The sizing suite remains outside the four-suite characterization budget. A future branch that includes this caller must separately assign its bounded composed proof, preserving the real dispatch/split/invoke order rather than calling a new gate alone.

No whole-Program fail-closed claim may rest only on `_spend_core`. Explicitly settle effective engine selection, cap capability, amount/cost transport, reviews/retries/parallelism, existing-process continuation, engine/model/amount changes and unknown outcomes at each included boundary. A narrower supported scope must be named honestly. No common budget service, new ledger or universal permission model is presumed.

### Visible promise and compatibility

These are existing interface/doc **read-only** paths, not approved edits:

- `holdspeak/web/routes/programs.py` 78–90/145–150/169–174/313–325 admits create/update amount and text operations. `holdspeak/mcp/families/program.py` 182–183/198–210/444–462 describes a maximum cost and forwards it. `holdspeak/mcp/tool_authority.py` 325–342 distinguishes WORK writers from AUTHORITY decisions.
- `web/src/desk/programs/ProgramText.tsx` 23–29/44–80 recognizes canonical spend text and excludes lamps from edited text; `web/src/desk/programs/types.ts` 550 exposes the wire field. `web/src/desk/programs/api.ts::CreateBody` 39–51 has no dedicated amount form. Do not invent an existing numeric settings UI.
- Shaper `GRAMMAR_CARD` 68–100 teaches the spend line; `stripped_text` 162–166 removes lamps. A warning only in a UI lamp will not reach every engine-facing producer.
- `holdspeak/commands/program.py` 28–53/109–139 supplies create/start/get/decide and JSON output, but no dedicated create-dollar flag. That compatibility is separate from the CLI inference cap below.
- `docs/programs.md` 222/581/618/883 and `agent/skills/holdspeak-programs/SKILL.md` 251 describe the amount and behavior. The historical `docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md` 204/606/827 and `docs/internal/betterment/programs/PROGRAM-JOURNEYS-2026-10-31.md` 297/309/375 include hosted planner spending/stop promises. These documents are **design intent, not shipped proof or fresh user authorization**. Resolve the conflict without rewriting historical evidence as if behavior existed.

D20/G24 must choose the promise and scope first. Disclosure-only can truthfully retain a saved/requested amount and existing runtime while explicitly admitting it is not a ceiling; that does not fix the bypass. A real cap needs an enforceable mechanism and proof at its chosen scope, including unsupported/unknown admission handling. Deliberate paid-engine permission needs accepted authority, binding, revocation and legacy rules. **None** may derive new unlimited permission from an old number, nullable field or kind-only Go on. Preserve old data/history and decide canonical spelling/API compatibility before any change. Unsupported-cap hold/refusal can be narrower than implementing a meter, but must still define covered callers and cannot silently fall back to unbounded work.

### Preserve the separate CLI and Automation path

`holdspeak/services/workbench_runner.py::_MeteredPromptAdapter._limited` 46–67 copies the per-call engine and forwards amount only for a capable preset. `holdspeak/intel/cli_engine.py::CliPreset` 87–102, `PRESETS` 117–155, `parse_cli_endpoint` 197–221 and `build_cli_argv` 421–422 declare/validate capability and emit `--max-budget-usd` where supported. `holdspeak/services/model_library_service.py` 514–527 rejects unsupported presets; `holdspeak/services/workbench_service.py::_spend_limit` 26–31 and `set_engine` 348–369 own the Automation amount.

This is positive existing behavior, not a missing generic abstraction. Multiple invocations may each receive the same amount. `tests/integration/test_desk_engines_tools.py` 302–334 and `tests/unit/test_cli_engine.py` 68–82/210–214/280–301 show source assertions for fake CLI transport/accounting, **not an aggregate Program cap or a provider/account guarantee**. They remain an evidence map, outside T24's initial four-suite budget.

### Initial characterization budget and commands

Four existing suites only, all **unchanged** in T24:

| Existing suite | Source witness; not a passing result |
| --- | --- |
| `tests/unit/test_program_service.py` | `test_a_hosted_pi_engine_with_no_spend_limit_is_a_core_question` 271–284: null → owner question → Go on with fake hand; `test_mcp_authority_rules` 118–158. Neither proves numeric enforcement |
| `tests/unit/test_program_rules.py` | `test_each_core_question_goes_to_him_at_every_level` 112–132 and `test_not_core_and_the_ladder_words` 135–140 inject synthetic cost |
| `tests/unit/test_program_text.py` | Existing recorded/generated round trips, dry-run/no-write and refused-lowering tests; generated spend examples are null/5/2.5, not all malformed/zero compatibility |
| `tests/unit/test_program_agent_bar.py` | `_agents_program` 24–33 and shape/round/draft cases 142–195 use Rig/fake engines/invoke_fn; preserve text authority, not proof of dollar-specific direct-update ownership |

`tests/conftest.py` 639–646/904–927/976–1005 establishes installation isolation, bare composition and temporary session/config. `tests/integration/program_rig.py` 1–23/94–144/300–334 uses real temporary local Git/worktrees, fake hand/process/GitHub and fake-check shell. Thus even collection/running requires a separate execution assignment in a safe checkout. No real provider, owner HOME/config or external Git remote is needed; stop if current fixtures violate that boundary. Do not run from the source-data extraction.

The following **future, unrun** Bash recipe composes source-defined test-lock/pytest forms with the four verified files. Read current repository/scoped instructions and [setup/isolation](#setup-and-isolation) first; installed dependencies are not proven. Keep task evidence outside the temporary HOME. The task may instead finish entirely source-only with tests explicitly unrun.

```sh
(
  set -euo pipefail
  : "${HS_EVIDENCE_DIR:?Set an absolute task-owned evidence directory}"
  mkdir -p "$HS_EVIDENCE_DIR"
  HS_TEST_HOME="$(mktemp -d)"
  trap 'rm -rf "$HS_TEST_HOME"' EXIT
  export HOME="$HS_TEST_HOME"
  unset HOLDSPEAK_WIRE_WRITE HOLDSPEAK_WRITE_WIRE_FIXTURES HOLDSPEAK_EVIDENCE_WRITE
  py_files=(tests/unit/test_program_service.py tests/unit/test_program_rules.py tests/unit/test_program_text.py tests/unit/test_program_agent_bar.py)
  uv run python scripts/test_lock.py -- uv run pytest --collect-only -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/s24-collect.log"
  uv run python scripts/test_lock.py -- uv run pytest -q -n 8 --dist worksteal "${py_files[@]}" | tee "$HS_EVIDENCE_DIR/s24-characterization.log"
)
```

Do not automatically union other Program, CLI, web or browser suites into this contract task. `scripts/quick_check.sh` fetches/builds/tests and runs a browser sweep; it is **not** a source-review command or a current S24 requirement. No new test name, fixture output, capture flag run or runtime estimate is claimed here. Record collected/executed counts, skips, exits and unresolved cases honestly if later assigned.

### Proof design required before implementation briefs

- **Truthful-interface branch:** real service/REST/MCP/text writers produce the value and real get/text/prompt consumers carry the same honest meaning. Preserve accepted writer/round-trip/core behavior, legacy syntax and values. Exact initial homes: the four suites above, plus source-verified `tests/unit/test_program_shaper.py` and `tests/unit/test_program_planner.py` for actual prompt production, and `web/src/desk/programs/__tests__/programs.app.test.tsx` for actual Program text consumption. A chosen branch must reduce this to its justified explicit edit/run budget; hand-written display JSON alone is insufficient.
- **Covered-operation hold/refusal branch:** drive the real selected producer through each included matrix row and assert refusal before fake launch/dispatch. `tests/unit/test_program_hand.py` covers real AgentHand separately from runner FakeHand; source-verified `tests/unit/test_program_handoff.py`, `tests/integration/test_program_review_setup.py`, `tests/integration/test_program_review_rehand.py`, `tests/integration/test_program_review_dead_builder.py`, `tests/unit/test_program_rounds.py` and `tests/unit/test_program_night.py` identify relevant existing homes, not an assigned union. Generate old Go on through actual service, not merely injected facts. Test engine changes/retry/restart, old values and direct writers. Preserve helper authority/read-only fences and meaningful unknown outcomes.
- **Enforced ceiling branch:** name the supported enforcer at the chosen scope and how actual amount/cost/remaining allowance reaches it. Define concurrent/retry/reviewer reservations or equivalent semantics only if the accepted scope needs them. A synthetic `$1`, token count, process profile label, passed argv or mocked bill does not by itself prove a whole-Program financial bound. No paid experiment is required or authorized by this plan.
- **Any branch:** decide in-flight transition and rollback before code. Preserve prior history and amounts, never silently kill/restart work or reinterpret old consent. A rollback cannot undo cost already incurred. Stop for missing semantics, unsafe fixture, real paid/provider needs, unsupported capability evidence or changes to another lifecycle. Return the contract in the existing completion response; update D20 only from actual approval evidence. No standalone report, migration or additional task tree is needed until a branch is accepted.

# AGENTS.md verification audit — 2026-10-30

This is a read-only process audit for the proposed replacement of the root
`AGENTS.md`. It does not change product source, tests, or the root charter.
Mechanical facts below come from the checked-out source. Workflow facts use
the latest owner ruling in `CLAUDE.md` (the 2026-10-12 fast cycle).
Line anchors are from this audit snapshot; re-check them if a parallel edit
changes the cited files.

The initial findings below were made against the baseline root `AGENTS.md` at
`base44b7104f7`; those historical line anchors are labelled as baseline. The
shared worktree then received a parallel candidate edit to `AGENTS.md` while
this note was being prepared. The candidate is materially closer to the fast
cycle, but these points still need a decision before it is treated as the
source of truth:

- `AGENTS.md:21-22` links `web/AGENTS.md` and `holdspeak/AGENTS.md`, but those
  files are not present in this checkout. Add the scoped guides in the same
  change or link only to files that exist; a new agent must not be sent to
  dead instructions.
- `AGENTS.md:91,139-142` says to inspect “relevant shots” and that shots go to
  `.tmp/evidence-shots/`, but the sweep emits PNGs only when
  `DESK_SWEEP_SHOTS=1` (`tests/e2e/test_desk_sweep.py:1045-1066`) and
  `quick_check.sh` does not set it. Say “when shots were requested and
  captured,” or provide an explicit capture command. Never report a passing
  sweep as proof that PNGs exist.
- `AGENTS.md:93` permits an authorized live device/provider run, while
  `AGENTS.md:101-105` says tests and walks must not touch an external
  destination. Make the latter the default isolation rule with an explicit,
  separately scoped exception for the former; `--engine real` has a LAN
  default (`scripts/graph_walk.py:273-279`) and must never enter the normal
  quick check.

## What the replacement must fix (baseline `AGENTS.md` at `base44b7104f7`)

| Evidence | Problem | Practical correction |
| --- | --- | --- |
| `AGENTS.md:102-119` | This still describes the 2026-10-03 pre-merge two-brain gate, while `AGENTS.md:3-9` says review is after merge and `CLAUDE.md:17-33` says quick check → merge → tape → Astra review. | State one current flow: small worktree change; `scripts/quick_check.sh`; PR and immediate merge when green; main watcher after merge; Astra review and fix-forward. Only security/data loss uses `git revert`. |
| `AGENTS.md:83-100` | The examples say isolated `HOME`, but omit the mandatory lock, `-n 8`, and the browser/npm cache paths. `CLAUDE.md:163-180` makes those current rules. | Make the lock and isolated-home wrapper mandatory for each individual pytest, Vitest, `glass_for`, and graph run. Keep `PLAYWRIGHT_BROWSERS_PATH` and `npm_config_cache` pointing at the real caches, never at the temporary HOME. |
| `AGENTS.md:93-95`, `AGENTS.md:163-167` | “Read output before PR” and “shots at 1440 and 393 before merge” are too broad and imply that any test shot is owner acceptance. `CLAUDE.md:35-38` says the owner judges a live desk. | Say that `quick_check.sh` is the technical pre-merge check. The sweep covers both viewports, but an automated result is not an aesthetic or owner-live verdict. Explicitly inspect requested PNGs and report the live-owner unknown separately. |
| `AGENTS.md:96-100` | It points at the graph skill without the reproducible command or the checks that make an observation honest. | Include the one-case procedure: fresh HOME, one case per invocation, lock, unique `.tmp/` output, then read `observation.json`, `provenance.db_path`, source `revision`/`dirty`, `initial_feedback`, `terminal_outcome`, and both shots. A blocked case is a result, not a pass. |
| `scripts/quick_check.sh:10-13` vs `scripts/quick_check_affected.py:23,56-81` | The shell comment says changed imports in `tests/e2e` are selected, but the selector searches only `tests/unit`, `integration`, `critical`, `web`, `mcp`, and `uat`. A directly changed e2e test is selected; an e2e test that imports a changed module is not. `quick_check.sh:100-101` also deliberately removes the desk sweep and `test_metal.py` from the affected list. | Do not promise automatic e2e dependency discovery. If an e2e file is the proof, name it with `QUICK_TESTS` or run it explicitly under the lock. The generic desk sweep is already a separate quick-check step; never run `tests/e2e/test_metal.py`. |
| `CLAUDE.md:109-124` vs `CLAUDE.md:173-180` | The older FAST/FULL bullets still say FAST runs before every merge, while the later fast-cycle doctrine says `quick_check.sh` only before merge and FAST/FULL after merge on the main watcher. | The replacement AGENTS file should link to the current quick-check script, not copy the historical FAST/FULL commands. Current source and the latest owner ruling win. |
| `AGENTS.md:35-42` | “Nothing authored … until the other has checked it” is the old general gate and conflicts with the current post-merge review statement. | Keep cross-review as the post-merge reviewer responsibility, not a new pre-merge gate. Do not add contracts, evidence-file gates, owner-approval gates, or broad-suite gates. |

## Canonical commands and isolation

The root AGENTS file should contain only short, executable recipes and defer
the long guard list to `scripts/quick_check.sh` and `CLAUDE.md`.

Before a PR, from the change worktree, run:

```sh
scripts/quick_check.sh origin/main
```

This script discovers changed paths and fails closed (`scripts/quick_check.sh:30-45`),
creates a temporary HOME and preserves the browser/npm caches
(`scripts/quick_check.sh:47-60`), and locks its build, Vitest, pytest, sweep,
canon, and repository-guard commands (`scripts/quick_check.sh:62-65,68-97,99-110,112-148`).
Do not put another outer lock around the whole script: it takes the lock for
each child run.

For a focused pytest run, use a temporary HOME and the machine-wide lock. The
browser cache variables are harmless for a non-browser test and necessary for
browser tests:

```sh
REAL_HOME="$HOME"
TEST_HOME="$(mktemp -d)"
trap 'rm -rf "$TEST_HOME"' EXIT
HOME="$TEST_HOME" \
  PLAYWRIGHT_BROWSERS_PATH="$REAL_HOME/Library/Caches/ms-playwright" \
  npm_config_cache="$REAL_HOME/.npm" \
  uv run python scripts/test_lock.py -- \
  uv run pytest -q -n 8 --dist worksteal tests/unit/test_desk_<app>.py
```

`test_lock.py` is the source of the mutual-exclusion contract: its usage and
priority behavior are documented at `scripts/test_lock.py:1-24`, and the
default lock, waiter, timeout, subprocess exit code, and release are at
`scripts/test_lock.py:88-135`. Every pytest, Vitest, `glass_for`, and graph
walk invocation takes this lock; do not run a smaller parallel “helper” run
beside a held run.

For a focused Vitest app test, run from `web/` as required by the test diet:

```sh
( cd web && HOME="$TEST_HOME" \
    uv run --project .. python ../scripts/test_lock.py -- \
    ./node_modules/.bin/vitest related --run --maxWorkers=8 \
    src/desk/__tests__/<app>.app.test.tsx )
```

The `TEST_HOME` in this example is the one created above. Do not call type
checking a validation result; the current rule says to run the relevant test
and read its output (`CLAUDE.md:200-204`).

## Small task-to-test matrix

Choose the cheapest tier that honestly proves the changed behavior, grouped by
app (`CLAUDE.md:182-201`). A tier is not a claim that higher tiers passed.

| Change | First proof | When to add a higher tier |
| --- | --- | --- |
| Backend route, service, schema, or Desk-window behavior | **T1:** the focused `tests/unit/` or `tests/integration/test_desk_<app>.py`, through `test_lock.py` and isolated HOME. | Add a real route/graph case when the behavior crosses a producer, scheduler, MCP, or rendered face. |
| One web app's state, action, or component | **T2:** one `web/src/**/__tests__/<app>.app.test.tsx` file, Vitest from `web/`, through the lock. | Add T1 when the payload contract changed; add T3 for the window/route or responsive face. |
| A face, window, route, responsive layout, or shared surface | **T3:** `tests/e2e/test_desk_sweep.py`, which is the generic sweep over the manifest, wings, palette, routes, and 1440/393 fences (`tests/e2e/test_desk_sweep.py:1-80,1264-1368`). `quick_check.sh` already runs it (`scripts/quick_check.sh:112-128`). | Add T4 only for behavior the generic sweep cannot prove. |
| Drag, focus, keyboard, touch, hover, clipboard, multi-browser, or an exact geometry relation | **T4:** the smallest focused real-browser file, through the lock. Do not create a phase-named browser file; park retired files in `tests/e2e/_parked/` (`CLAUDE.md:193-201`). | Do not replace a cheaper honest T1/T2 assertion with a browser test merely for confidence. |
| A capability or cross-boundary producer-to-observation claim | One actual atlas case with `scripts/graph_walk.py`, one case per invocation. Face cases run at both viewports; protocol cases run once (`agent/skills/holdspeak-capability-verifier/SKILL.md:49-75`). | Use a real engine only when explicitly in scope. `--engine replayed` proves downstream wiring with a recorded provider answer; it is not real-model proof. |

The script's own affected-test selection is useful but not complete: changed
test files are emitted directly, while imported-module discovery is limited to
the `SEARCH` roots (`scripts/quick_check_affected.py:22-24,54-81`). Use
`QUICK_TESTS="tests/e2e/<file>.py" scripts/quick_check.sh origin/main` when
the focused e2e file is part of the change's proof.

For UI work, keep the face rules short and visible in the replacement AGENTS
file: read `docs/internal/UX-CANON.md` before editing a face; use the library
Button for every verb; keep UI copy to labels/tokens; do not add modals or
zero-count chrome; and disclose egress at the choice or act. The standing
rules and component roster are `docs/internal/UX-CANON.md:151-217` and
`docs/internal/UX-CANON.md:218-240`. A canvas chooses the direction, then the live
desk and the sweep test the built face. These are implementation constraints,
not a reason to add another approval gate.

For backend work, name the producer route/service/schema and the assertion
that reads its result. A route existing in source is not a runtime result: use
T1 for the contract and add a real-hub or graph observation when the path
crosses persistence, a scheduler, MCP, an external engine, or a rendered face.
For a consequential effect, include the kernel admission/terminal receipt in
the source-to-assertion trace (`docs/internal/CONSTITUTION.md:Article XI.1-5`);
do not infer it from a successful HTTP status alone.

## Fixtures, producer truth, and the rendered outcome

For a web test that needs hub data, the preferred chain is:

1. Mint the fixture from the real producer in an isolated HOME. The Needs-you
   recorder boots `MeetingWebServer` through `TestClient`, seeds the browser
   tests, and writes the JSON; it explicitly says that answers are not typed by
   hand (`scripts/record_needs_you_fixture.py:1-16`).
2. Replay that retained answer shape through the test seam. `recordedGet`
   clones a recorded answer, maps the query-string variant, records misses, and
   returns `null` for an unrecorded read (`web/src/test/recordedHub.ts:1-18`).
3. Drive the user press and assert the rendered state, not only the helper or
   POST. For example, the Chair test clicks the owner verb, waits for the well,
   saves, then asserts the row's rendered state and that the old verb is gone
   (`web/src/desk/__tests__/needsChair.app.test.tsx:87-105`). The recorded
   proposal tests reject an unrecorded POST and advance reads only after the
   press (`web/src/desk/__tests__/needsYou.app.test.tsx:242-259`).

Do not call a manually assembled test object producer evidence. The same app
test file contains a local `producerCard` and hand-built responses
(`web/src/desk/__tests__/needsYou.app.test.tsx:50-85`); those can prove a
component branch, but they cannot prove the backend schema. A recorded fixture
also does not prove live runtime behavior: it is a T2 contract test until a
real-hub T1/T3/T4 or graph observation covers the path.

For graph cases, set state through the declared `api`, `ui`, `fixture`, or
`cli` entry point, with one trigger, an expected predicate, and a named
`observe_at` (`agent/skills/holdspeak-capability-verifier/SKILL.md:49-54`). A
fixture is an input-boundary WAV, not a microphone; an engine replay is
installed at the product seam and records its mode
(`scripts/graph_walk.py:74-75,103-131`). Never inject final rows or answers and
label them producer evidence.

## UI evidence and screenshot honesty

The desk sweep is a technical glass check. It waits for the window to settle,
then checks drawn/fit/readable/contrast/type-floor/clipping/overlap/library
Button/material/still/egress and related fences (`tests/e2e/test_desk_sweep.py:1048-1085`;
the fence list is summarized at `tests/e2e/test_desk_sweep.py:28-66`). It
parameterizes every case at 1440 and 393 (`tests/e2e/test_desk_sweep.py:399-407,1264-1268`).

PNG capture is opt-in: `_Case.fences` writes a shot only when
`DESK_SWEEP_SHOTS=1` (`tests/e2e/test_desk_sweep.py:1045-1066`), and the normal
evidence destination is the ignored `.tmp/evidence-shots/` directory unless
`HOLDSPEAK_EVIDENCE_WRITE=1` is deliberately set (`tests/_evidence.py:1-24`).
`quick_check.sh` does not set `DESK_SWEEP_SHOTS`; therefore “the sweep passed”
does not mean “two PNGs were produced.” If a shot is requested, inspect the
PNG and say which viewport and runtime it represents. Browser helpers wait for
animations and decoded images before capture (`tests/e2e/glass_infra.py:468-503`),
but that still does not make a test shot the owner's live aesthetic verdict.

For a graph face case, read the observation before reporting it. The skill
requires checking the predicate result, temporary-HOME `provenance.db_path`,
source `revision` and `dirty`, separate `initial_feedback` and
`terminal_outcome`, and `before.png`/`after.png`
(`agent/skills/holdspeak-capability-verifier/SKILL.md:68-75`). The graph report
prints source, runtime build, hub, database, engine mode, verdict, and shots
(`scripts/graph_walk.py:7713-7728`). A screenshot from a stale build, or a
dirty source tree whose relevant change is not in the runtime bundle, cannot
be reported as source verification. Check the build/source relationship and
keep the unknown explicit.

The owner-facing boundary is constitutional: code presence, executed tests,
release, and owner observation are separate evidence axes
(`agent/skills/holdspeak-capability-verifier/SKILL.md:18-24`); the owner's live
desk judgment remains the face acceptance (`CLAUDE.md:35-38`,
`docs/internal/CONSTITUTION.md:IX.1-4`). Technical green is not aesthetic
ratification.

## Backend and live-runtime limits

The graph rig is a real hub and real browser path, but it intentionally does
not build the microphone recorder or global hotkey listener, and it records
those missing product wires in provenance (`scripts/graph_walk.py:222-237`).
Its hub verifies the resolved database path beneath a run-owned HOME before
acting (`scripts/graph_walk.py:2635-2644`), and the run cleans its temporary
HOME/profile after completion (`scripts/graph_walk.py:7684-7700`). Thus a graph
pass can prove the declared producer → persistence → face/observation path,
but not full OS-device capture, a user's microphone, or every runtime process.
Do not promote a hub pass to “the product works on the owner's machine.”

Browser glass rigs similarly create their own HOME and disable machine-facing
features before boot (`tests/e2e/glass_infra.py:236-300`). One hub is one desk:
all pages on that hub share windows, so clear hub windows through the helper
before asking a second page to start empty (`tests/e2e/glass_infra.py:402-411`).
Do not use localStorage clearing alone as a desk reset.

`--engine real` is a separately scoped external dependency: the graph script
has a configured LAN URL/model default (`scripts/graph_walk.py:273-279`). Use
`--engine replayed` or `none` for local deterministic verification unless the
owner explicitly scopes a live engine; report the engine mode either way.

## The one graph-walk recipe

Use the real atlas, not the calibration/sample atlas, for a capability claim.
The skill's command is the canonical shape; add the lock around the one run:

```sh
REAL_HOME="$HOME"
TEST_HOME="$(mktemp -d)"
trap 'rm -rf "$TEST_HOME"' EXIT
HOME="$TEST_HOME" \
  PLAYWRIGHT_BROWSERS_PATH="$REAL_HOME/Library/Caches/ms-playwright" \
  uv run python scripts/test_lock.py -- \
  uv run --extra dev python scripts/graph_walk.py run \
    --atlas docs/internal/philo/graph/atlas.json --case <case-id> \
    --brain astra --viewport 1440 --engine none \
    --out .tmp/graph-walk/<story>/1440
```

Repeat the same case with `--viewport 393` for a face. Give each run its own
output directory. Then read `<out>/<run-id>/observation.json`; do not edit an
observation by hand or overwrite a tracked shot. The rig itself creates and
verifies a run-owned hub HOME (`scripts/graph_walk.py:7590-7628`), but the
outer temporary HOME keeps the command, package tools, and any helper state
isolated as required by the skill.

## Handoff after a green change

The report should name: changed paths; the source-to-assertion trace; exact
collected test names; the run tail; shot paths; the runtime/build and database
provenance; and remaining unknowns. Separate mocked proof, real-hub proof,
technical visual proof, and owner-live observation. Hold the report for SHIP;
do not stage or commit on behalf of the lane.

After `scripts/quick_check.sh` is green, the fast cycle permits the PR and
immediate merge. The main watcher then runs the whole tape and traces any red
to the merge; Astra reviews after merge and findings are fixed forward
(`CLAUDE.md:17-33`). Update `pm/STATUS.md` at merge. This keeps verification
strong without reinstating a pre-merge full suite, a second approval gate, or
a claim that technical checks equal the owner's Tuesday verdict.

## Final recheck — integrated guides (2026-10-30)

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. `web/AGENTS.md:28-32` names the Button import as
   `components/signal/Signal`, but the actual module is
   `web/src/components/signal/Signal.tsx` and exports `Button` at
   `web/src/components/signal/Signal.tsx:21`. The surrounding line already
   uses the `src/` prefix, so this is an actionable path ambiguity for a new
   worker.
2. `AGENTS.md:93,101-105,146-150` still has an isolation contradiction:
   physical/live-provider work is listed as an authorized tier and graph
   walks say live effects need authorization, while the blanket rule says
   tests and walks must not touch external destinations. The graph's
   `--engine real` also has a LAN default (`scripts/graph_walk.py:273-279`).

CONDITIONS:

- Change the web guide to `src/components/signal/Signal` (or the exact
  `src/components/signal/Button` module) and keep all source paths rooted at
  `web/`.
- Reword the root isolation rule as: all normal tests/walks use isolated
  state and no external effects; a live device/provider walk is a separately
  authorized exception naming its target, engine mode, and output. Keep it
  outside the normal quick check.

MISSED: No other high-cost omission found. The integrated guides now cover
the lock, isolated HOME/cache handling, affected-selector override, T1–T4
selection, producer-to-rendered assertions, 1440/393 sweep and opt-in PNGs,
graph provenance, backend seam/receipt checks, and post-merge tape. The root
guide does not add a pre-merge full suite, second approval, evidence dossier,
or other new gate (`AGENTS.md:95-150,154-170`; `web/AGENTS.md:128-139`;
`holdspeak/AGENTS.md:87-100`).

TUESDAY: Yes for an ordinary UI or backend change after the two wording/path
conditions; the tier table and executable recipes are usable without a new
ritual.

UNKNOWN: I did not execute tests, Vitest, quick check, or a graph walk; this
was the requested read-only command and guidance audit. I verified referenced
command files and test paths exist, including the graph atlas, lock, quick
check, Button module, and backend guard files.

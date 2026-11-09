# Working agreements for HoldSpeak

This file is loaded automatically by Claude Code when it opens this
repo. It tells you (the agent) the rules of the road.

Practical instructions for the workers: read [AGENTS.md](AGENTS.md)
for the common development flow, [web/AGENTS.md](web/AGENTS.md) before interface
work, and [holdspeak/AGENTS.md](holdspeak/AGENTS.md) before hub work. These guides
summarize the current agreements; older passages below do not restore a gate
superseded by the fast cycle.

## How we work now: one brain, one loop, three checks (owner ruling 2026-11-07)

The owner, 2026-11-07: "I can't afford to have so much ceremony… the whole
'two-mind' thing? It's just caused massive delays… We've got to change
something about the way we do things." He said yes to the seven lines below.
They replace the 2026-10-12 fast cycle where the two differ; its mechanics
(small changes, worktrees, quick check, main is his desk, fix forward) stay.

1. **One brain decides.** Muad'Dib. No mutual check, no counsel or ask rounds,
   no doctrine to read on entry. Two Brains is retired (`docs/internal/TWO-BRAINS.md`
   is history).
2. **Astra is a reviewer profile inside Programs, not a process.** One round,
   after the merge, bounded to the diff, and only for a step that touches a
   security surface: the gate boundary, token pages, egress, Telegram,
   credentials. Everything else gets no second model.
3. **Verification is exactly three checks; nothing else gates.** A test that
   fails on main. `scripts/quick_check.sh`, run ONCE by the orchestrator on
   main after a merge batch, never per PR (owner, 2026-11-07 evening: "Why is
   there sooo much waiting?": five workers each ran the whole check and the
   desk sweep, serialized on the lock, 40 min of queue for one proof). A
   worker runs only its focused test files (seconds), commits, pushes, opens
   the PR. His desk on main. A red after the merge is fixed forward at once,
   not debated.
4. **Plans are Programs, never documents.** No contract tasks, completion
   reports or planning packages. The brief is the step text.
   `docs/internal/holdspeak-execution-plan/` (#1788) is reference; its slices
   run as Programs.
5. **`pm/STATUS.md` is one line per merge.**
6. **Nights build, mornings judge.** Hands-off Programs at YOLO overnight, in
   waves that share no files. The owner judges faces live on his desk in the
   morning; one sentence from him is a ruling.
7. **Measure.** Merges per day, presses per night, hours from finding to main;
   one paragraph weekly; change again in two weeks if the numbers are flat.

**The direction every change serves (owner, 2026-11-07):** "an effortless
system, a powerful system at the same time… our desktop environment… is
really powerful now… we're not gluing everything together properly… the
flows are not frictionless… really nail the core workflows and adapt the
architecture and the design around them… not an overcomplicated architecture
with multiple implementations of the same thing." Pick work by core workflow,
not by finding. A change removes a seam or a second implementation; it never
adds one.

- **Kept:** tests never touch the owner's real HOME, DB or Keychain; every
  merge is revertible (`git revert`); never delete, park instead; never push
  `main` directly (merge via PR); a face is judged LIVE on his desk, a mockup
  only picks a direction (`docs/internal/UX-CANON.md`).
- The git hooks are parked in `.githooks/_parked/`. `pm/roadmap/` is history.

## The Seven Tenets (owner's charter 2026-09-19)

`docs/internal/CONSTITUTION.md` opens with the owner's Seven Tenets; they
outrank every article and every rule in this file. Measure every brief,
check and merge against them first: no over-engineering for safety; not
even pre-alpha (the creator has not used it once); help and accelerate,
never a million interfaces; ASD-STE100 (confirmed 2026-09-19) on product text and user docs; a component
framework in the manner of Intuition; Workbench 2.0+ on steroids; the
first user is a Senior Software Architect with reports.

## Two brains: retired (owner ruling 2026-11-07)

Two Brains (2026-09-19: Astra as Muad'Dib's equal, mutual checks, per-PR
review rounds) caused "massive delays" and is retired. `docs/internal/TWO-BRAINS.md`
and `scripts/astra` stay as history. Muad'Dib's workers (Opus 5.5,
`claude-opus-5-5`, `.claude/agents/opus-worker.md`) build; the Programs engine
runs the nights; Codex is one reviewer profile for security-surface steps
(line 2 above).

## Status

- **Status file:** `pm/STATUS.md`: the current phase, open work, last merged.
- **History:** `pm/roadmap/` (old phases, stories, evidence). Read-only.

## Source canon

These are the docs phases must be grounded in. If any phase document
disagrees with one of these, canon wins:

- `docs/internal/CONSTITUTION.md` — **the supreme canon**: the ratified
  articles every phase, story, and design decision is measured against.
  Where any doc below disagrees with it, the Constitution wins.
- `README.md` — public install + usage surface.
- `docs/internal/UX-CANON.md` — **the face canon**: the owner's rulings
  every face must obey (every verb the library Button; no prose; no
  modals; no counters of zero; egress where egress happens; design on
  the canvas before build; build what was ratified) and the review
  protocol. Read it before touching anything a user sees.
- `docs/internal/POSITIONING.md` — the positioning canon: the story, the
  pillars, the named competitive frame, canonical feature names, and the
  voice rules every user-facing doc must align to.
- `pyproject.toml` — package contract.

History, not canon (owner ruling 2026-10-04): the four June plans
`docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`,
`PLAN_PHASE_MULTI_INTENT_ROUTING.md`, `PLAN_PHASE_DICTATION_INTENT_ROUTING.md`
and `PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` name modules that no longer exist.
Read them for background only.

## Test commands

Three runs (owner ruling 2026-10-03). Run the tests that cover the change;
the full suite is nightly. Every run uses an isolated HOME, so local state
and the owner's real DB stay out of it. Times are from the owner's machine
(12 cores) on 2026-10-03, with other lanes running tests at the same time.

- **FAST** (run it before every merge; 5 min 40 s, was 7 min 50 s):
  `HOME_REAL=$HOME; H=$(mktemp -d); HOME=$H PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run pytest -q -n auto --dist worksteal -m "not slow" tests/unit tests/integration tests/critical tests/web tests/mcp tests/uat; rm -rf $H`
  Unit, integration, critical and UAT tests; no browser tests. A test marked
  `slow` (a clean venv install, a real hub restart, the graph-walk
  calibration) runs in FULL and when you name its file.
- **SCOPED browser tests** (run them when the change touches `web/src/` or
  `holdspeak/`; one browser file takes 10 s to 60 s):
  `uv run python scripts/glass_for.py` prints the pytest command for the
  browser tests that cover the diff against `origin/main`, and why it picked
  each file. `eval "$(uv run python scripts/glass_for.py --quiet)"` runs it.
  Name paths to ask about them: `scripts/glass_for.py web/src/desk/delivery.ts`.
- **FULL** (nightly in CI, `.github/workflows/nightly.yml`; not measured with `--dist worksteal` yet; 47 min without it, because three workers held every browser test):
  `HOME_REAL=$HOME; H=$(mktemp -d); HOME=$H PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run pytest -q -n auto --dist worksteal --ignore=tests/e2e/test_metal.py; rm -rf $H`
  Pull-request CI runs FAST and the scoped browser tests only.
- One file or one test: the same command with the path in place of the
  directories. Doctor only: `uv run pytest -q tests/ -k doctor`.
- `PLAYWRIGHT_BROWSERS_PATH` is not optional: the isolated HOME hides the
  browser cache, and browser tests error on "Executable doesn't exist"
  without it. `npm_config_cache` keeps the mermaid-docs renderer on the warm
  npm cache; without it a fresh-HOME run downloads mermaid-cli and Chromium
  again (gigabytes per run).
- Always `-n auto --dist worksteal` (pytest-xdist; an idle worker takes
  tests from a busy one). UAT conductor tests boot real product
  processes; each xdist worker scans its own port range
  (uat/conductor/runs.py), so parallel runs cannot cross-boot onto one port.
- **One hub is one desk (Phase 16 B, #1046).** Every page a browser test opens on one hub sees the same windows; a rig that opens several pages on one hub, or resets a desk by clearing localStorage, calls `clear_hub_windows` (`tests/e2e/glass_infra.py`) first. Every rig hub sets the isolation switches (`HOLDSPEAK_AGENT_STATE=off`, `HOLDSPEAK_ACTIVE_TARGET=off`, `HOLDSPEAK_DESKTOP_NOTIFY=0`, `HOLDSPEAK_MACOS_CALENDAR=0`, `HOLDSPEAK_CLI_ENGINES=off`, `HOLDSPEAK_RESTART_CHECK=off` (glass hubs that share the owner's tmux), `HOLDSPEAK_SCREEN_RULES=off` (no agent screen is read), `HOLDSPEAK_CALLS=off` (no ai-phone is probed or listened to), `HOLDSPEAK_LINE=off` (no baresip is looked for or run; the Line is never the phone), `HOLDSPEAK_RECORDINGS=off` (no ffmpeg run, no Tailscale read, no keep sweep), `HOLDSPEAK_MIC_CHECK=off` (no microphone is opened before Start), `HOLDSPEAK_PROGRAMS=off` (the Programs engine does not tick: no step is handed, checked or merged), `HOLDSPEAK_PHONE=off` (no phone route is mounted, no ring timer or sweep runs, no push is sent), `HOLDSPEAK_TELEGRAM=off` (no Telegram long poll, no send, no bot-token move from the config file), the keystores and agent config paths inside HOME): a new read of machine state needs a switch, default on. Two hub switches for the event log and the loop (PERF-HUB 2026-10-28): `HOLDSPEAK_EVENT_RETENTION_DAYS` (default 14; `0` keeps every row) prunes READ receipts from `pipeline_events` in a daemon thread (`holdspeak/db/pipeline_events_retention.py`; write receipts stay); `HOLDSPEAK_LOOP_WATCH=1` logs each handler that holds the event loop over 100 ms. A hub route runs its database and probe work through `run_in_threadpool`, never on the loop (fenced by `tests/unit/test_hub_loop_budget.py`).
- Browser tests draw on the GPU on macOS (`tests/conftest.py` adds
  `--use-angle=metal` to every Chromium launch; software WebGL made the
  browser suite three times slower). `HOLDSPEAK_GLASS_GPU=0` turns it off;
  it is off when `CI` is set.
- Remove the scratch HOME after each run (`rm -rf $H`).
- The suite cannot wedge: pyproject sets a 300s per-test timeout
  (pytest-timeout, thread method), so a hanging test dies with a stack
  trace naming it instead of stalling the run at 98% forever. A test that
  legitimately needs longer declares `@pytest.mark.timeout(...)`.
- Evidence shots: tests write screenshots and outputs to `.tmp/evidence-shots/`
  by default (`tests/_evidence.py`, fenced by
  `tests/unit/test_evidence_scratch_guard.py`).
  Tests write `pm/roadmap/` only with `HOLDSPEAK_EVIDENCE_WRITE=1`; do not set it.
  The tree is clean after any run: no restore of tracked evidence is needed.
  Old evidence (shots, run dumps, proof databases) is not in the tree: it is on
  branch `archive/evidence-2026-10-04`. `pm/ARCHIVE.md` says how to get a file back.
- Generated docs: `scripts/gen_docs.sh` runs every generator. No output is
  in git (2026-11-08): `docs/generated/`, `docs/api-surface.json`,
  `docs/API_SURFACE.md` and `docs/API_REFERENCE.md` are written on demand;
  generate them when you need to read them. Tests derive what they check from
  the live tree, never from a committed copy. Atlas source references have no `line`; the cited text must be
  in exactly one place in the cited file, so cite the declaration or render
  site. Do not add count fences; a new `.op` case needs no list edit.
- Web-unit inherited baseline:
  `uv run python scripts/check_web_baseline.py --run` — runs the desk
  vitest suite and diffs its failures against
  `tests/web-inherited-baseline.txt` (BASELINE-MATCHED / BRANCH-NEW /
  HEALED; exit 0 only with zero branch-new). See `tests/WEB_BASELINE.md`.

- **ONE TEST RUN AT A TIME ON THE MACHINE (owner catch 2026-10-07: "a ton of
  your workers are just running tests at the same time and keep breaking each
  other").** Every pytest, vitest, glass_for and graph-walk run, in every lane
  and the orchestrator's FAST alike, goes through the lock:
  `uv run python scripts/test_lock.py -- <command>`. Classes (2026-11-08): a
  `unit` run (the default for a direct pytest run that names no browser file,
  and for vitest) shares the machine with two other unit runs; it must set an
  isolated HOME (the lock refuses the real HOME), and above a load of 24 it
  waits to run alone. A `browser` run (tests/e2e, the sweep, glass, Playwright,
  graph walks, tests/uat, and any other command) is exclusive; a waiting
  browser run goes before later unit runs. `--class unit|browser` overrides.
  `scripts/quick_check.sh` takes the lock itself, once: run it bare, never
  wrapped (the lock is reentrant since 2026-11-07, so a wrapped run no longer
  deadlocks for 7200 s; it is still wrong). It runs its steps in parallel,
  skips a step whose inputs did not change since its last green
  (`.tmp/quick-check/green.json`), runs no test file twice, and after a red
  `scripts/quick_check.sh --retry` runs only the failed tests and the steps
  that did not run. The main checkout's `web/node_modules` is shared by lane
  symlinks: never reinstall it while a lane runs (the check's build runs
  `npm ci` only when `web/package-lock.json` changed since its last green, and
  `uv sync` runs `npm ci` too, through `hatch_build.py`).
  A docs-only diff runs only the doc check and the doc guards (seconds). Under the lock use `-n 8` (measured 2026-10-11: the
  whole browser suite 30 min at `-n 4`, 16.5 min at `-n 8`; FAST 11 → 6.5 min), not `-n auto`.
  A worker never runs FAST; a worker waits for the lock rather than running
  a smaller suite in parallel. Load above 60 means someone skipped the lock.

- **THE TEST DOCTRINE (owner order 2026-10-08, revised by the fast cycle
  2026-10-12).** Before merge: `scripts/quick_check.sh` only. The system-level
  runs (FAST, the whole browser suite, `check_web_baseline --run`) are the
  orchestrator's main watcher's, on each new main head, after the merge. A
  worker's own test budget is still written in its brief IN FILES; a worker
  that wants a wider run says so in its report. A new worktree is synced with
  `uv sync --extra dev` ONLY: `--all-extras` exhausts an xdist worker's file
  descriptors, and plain `uv sync` strips pytest.

- **THE TEST DIET (owner approval 2026-10-11: "each time we run a test suite it
  fucking takes hours … didn't we just build out a declarative compositor framework
  … programmatic e2e … without relying much (or at all) on playwright?" → "I do like
  your plan, and approve you immediately working on it").** A new check goes to the
  CHEAPEST tier that honestly proves it, grouped BY APP, never by phase:
  T1 a hub test (`tests/unit|integration/test_desk_<app>.py`; window behaviour
  against `/api/desk/windows`); T2 vitest, one file per app
  (`web/src/**/__tests__/<app>.app.test.tsx`); T3 the generic desk sweep
  (`tests/e2e/test_desk_sweep.py`: every app in `applications.ts`, every wing, the
  palette, `chair:needs` and every page route at 1440 and 393; fit, visible,
  console, readable, contrast, 12 px, clipped, overlap, library Button, material,
  still, egress); T4 a real browser only for drag, focus, keys, touch, hover,
  multi-browser, clipboard or an exact geometry relation. No new phase-named
  browser file. Test doubles replay RECORDED REAL hub answers
  (`scripts/record_needs_you_fixture.py`, `web/src/test/recordedHub.ts`,
  `HOLDSPEAK_WIRE_WRITE`), never typed ones, and drive a press through to the
  RENDERED outcome. The sweep's `KNOWN_REDS` name single defects (strict: a heal
  fails until the entry is removed). Retired browser files are parked in
  `tests/e2e/_parked/` (not collected), never deleted. Run vitest from `web/`
  with `./node_modules/.bin/vitest`.

Run the relevant tests with these commands and read the output before
you open the PR. Type-check is not validation.

The repository `.mcp.json` declares only the `holdspeak` server; Delivery
Workbench MCP is not enabled in that file. A client that needs it can
run `.githooks/dw-mcp`.


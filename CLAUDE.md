# Working agreements for HoldSpeak

This file is loaded automatically by Claude Code when it opens this
repo. It tells you (the agent) the rules of the road.

Practical instructions for both brains and their workers: read [AGENTS.md](AGENTS.md)
for the common development flow, [web/AGENTS.md](web/AGENTS.md) before interface
work, and [holdspeak/AGENTS.md](holdspeak/AGENTS.md) before hub work. These guides
summarize the current agreements; older passages below do not restore a gate
superseded by the fast cycle.

## How we work now: the fast cycle (owner ruling 2026-10-12)

The owner, 2026-10-12: "I am still very unhappy with how rigidly we have been
going forward with everything… it doesn't seem to be an aggressive, yet with
checks and balances methodology… How can we make fast iterations here without
waiting HOURS for something of yours to finally hit the tape?" He adopted the
fast cycle the same day. It replaces the 2026-10-03 rules (one Astra round
BEFORE merge; the full suite before merge).

1. **Small changes.** One change = one app or one concern, a few files. Branch
   from `main` in your own worktree. Commit plainly.
2. **The quick check before merge, 2–4 minutes:** `scripts/quick_check.sh`
   (the web build, `vitest related` on the changed web files, pytest on the
   affected test files, the desk sweep at 1440 and 393, the canon guards; all
   under the lock with an isolated HOME). Green = open the PR and merge it at
   once. Red = fix first.
3. **Main is the owner's desk.** Every merge to main redeploys his running
   desk (the orchestrator's main watcher). There is no integration branch and
   no batch to wait for.
4. **The tape runs after the merge.** The watcher runs the WHOLE suite on each
   new main head. A red is traced to the merge that caused it and fixed forward
   at once; it does not block other merges.
5. **Astra reviews after the merge.** She reviews each merged change within
   minutes; her findings are fixed forward. Only a security or data-loss
   finding reverts the merge (`git revert`, one command).
6. **Kept:** tests never touch the owner's real HOME, DB or Keychain; every
   merge is revertible; if main breaks his desk, the desk goes back to the last
   green head. Update `pm/STATUS.md` at merge (open work, last merged).

- No contracts, no evidence files, no per-story status flips.
- A face (anything a user sees): the owner judges it LIVE on his desk; a
  mockup is only for picking a direction, and then in our own material
  (`docs/internal/UX-CANON.md`; the delight ruling of 2026-10-11).
- Never delete; park instead. Never push `main` directly (merge via PR).
- The git hooks are parked in `.githooks/_parked/` (see its README).
  The `dw` CLI still runs, to read the old roadmap: `.githooks/dw next`,
  `.githooks/dw context`.
- `pm/roadmap/` is history. Do not update it.

## The Seven Tenets (owner's charter 2026-09-19)

`docs/internal/CONSTITUTION.md` opens with the owner's Seven Tenets; they
outrank every article and every rule in this file. Measure every brief,
check and merge against them first: no over-engineering for safety; not
even pre-alpha (the creator has not used it once); help and accelerate,
never a million interfaces; ASD-STE100 (confirmed 2026-09-19) on product text and user docs; a component
framework in the manner of Intuition; Workbench 2.0+ on steroids; the
first user is a Senior Software Architect with reports.

## Two brains (owner ruling 2026-09-19)

**Astra is the reviewer, not a builder (owner ruling 2026-10-03: "let
Astra be the uber-reviewer").** Muad'Dib's workers build everything,
backend included. Astra owns no lanes and writes no product code; she
gives the one final review round of each PR (at most 2 iterations).
Text below that gives Astra lanes or file ownership is history.

This repo has two orchestrators of equal standing: Muad'Dib (Claude,
this harness) and Astra (`gpt-6-astra` via `codex exec --yolo`). Each
checks the other before anything either authored is acted on; each
orchestrates down to its own workers (Muad'Dib → Opus 5.5, `claude-opus-5-5` (owner ruling 2026-10-04) via
`.claude/agents/opus-worker.md`; Astra → `gpt-5.6-luna` at `xhigh`).
Canon: `docs/internal/TWO-BRAINS.md`. Astra's side of the same rules:
`AGENTS.md` (repo root; codex reads it). Channel: `scripts/astra <role>
<brief.md>` (roles check | lane | counsel | ask), or `/astra`.

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
- **One hub is one desk (Phase 16 B, #1046).** Every page a browser test opens on one hub sees the same windows; a rig that opens several pages on one hub, or resets a desk by clearing localStorage, calls `clear_hub_windows` (`tests/e2e/glass_infra.py`) first. Every rig hub sets the isolation switches (`HOLDSPEAK_AGENT_STATE=off`, `HOLDSPEAK_ACTIVE_TARGET=off`, `HOLDSPEAK_DESKTOP_NOTIFY=0`, `HOLDSPEAK_MACOS_CALENDAR=0`, `HOLDSPEAK_CLI_ENGINES=off`, `HOLDSPEAK_RESTART_CHECK=off` (glass hubs that share the owner's tmux), `HOLDSPEAK_SCREEN_RULES=off` (no agent screen is read), `HOLDSPEAK_CALLS=off` (no ai-phone is probed or listened to), `HOLDSPEAK_LINE=off` (no baresip is looked for or run; the Line is never the phone), `HOLDSPEAK_RECORDINGS=off` (no ffmpeg run, no Tailscale read, no keep sweep), `HOLDSPEAK_MIC_CHECK=off` (no microphone is opened before Start), `HOLDSPEAK_PROGRAMS=off` (the Programs engine does not tick: no step is handed, checked or merged), `HOLDSPEAK_PHONE=off` (no phone route is mounted, no ring timer or sweep runs, no push is sent), the keystores and agent config paths inside HOME): a new read of machine state needs a switch, default on. Two hub switches for the event log and the loop (PERF-HUB 2026-10-28): `HOLDSPEAK_EVENT_RETENTION_DAYS` (default 14; `0` keeps every row) prunes READ receipts from `pipeline_events` in a daemon thread (`holdspeak/db/pipeline_events_retention.py`; write receipts stay); `HOLDSPEAK_LOOP_WATCH=1` logs each handler that holds the event loop over 100 ms. A hub route runs its database and probe work through `run_in_threadpool`, never on the loop (fenced by `tests/unit/test_hub_loop_budget.py`).
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
- Generated docs: `scripts/gen_docs.sh` runs every generator. Three outputs
  are not in git (`docs/generated/api-reference.json`,
  `boundary-candidates.json`, `graph.json`): generate them when you need to
  read them. Atlas source references have no `line`; the cited text must be
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
  `uv run python scripts/test_lock.py -- <command>`. It waits for the previous
  run to finish, then runs yours. Under the lock use `-n 8` (measured 2026-10-11: the
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


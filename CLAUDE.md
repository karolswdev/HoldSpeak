# Working agreements for HoldSpeak

This file is loaded automatically by Claude Code when it opens this
repo. It tells you (the agent) the rules of the road.

## How we work now (owner ruling 2026-10-03)

The owner, 2026-10-03: "I feel like we've been paying the price of
working under delivery workbench that has been bogging us down
BIG-FREAKIN'-TIME ... I want us to move fast. Super-fast."

The commit gate is removed. The rules are:

1. Branch from `main` in your own worktree. Commit plainly.
2. Open a PR.
3. Astra gives one review of the PR (one check, one confirmation).
4. Merge. CI does not gate the merge.
5. At merge, update `pm/STATUS.md` (open work, last merged).

- No contracts, no evidence files, no per-story status flips.
- A face (anything a user sees) gets a canvas before build; the owner
  ratifies the canvas; build what was ratified (`docs/internal/UX-CANON.md`).
- Run the tests that cover your change, with an isolated HOME (see
  "Test commands"). Read the output.
- Never delete; park instead. Never push `main` directly.
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

This repo has two orchestrators of equal standing: Muad'Dib (Claude,
this harness) and Astra (`gpt-6-astra` via `codex exec --yolo`). Each
checks the other before anything either authored is acted on; each
orchestrates down to its own workers (Muad'Dib → Fable 5.1 (owner ruling 2026-10-03) via
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
- `docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` — parent plugin RFC.
- `docs/internal/PLAN_PHASE_MULTI_INTENT_ROUTING.md` — meeting-side multi-intent routing (MIR-01).
- `docs/internal/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` — dictation pipeline (DIR-01).
- `docs/internal/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` — web-first runtime migration.
- `pyproject.toml` — package contract.

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

Run the relevant tests with these commands and read the output before
you open the PR. Type-check is not validation.

The repository `.mcp.json` declares only the `holdspeak` server; Delivery
Workbench MCP is not enabled in that file. A client that needs it can
run `.githooks/dw-mcp`.


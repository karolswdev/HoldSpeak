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

- All tests: `uv run pytest -q`
- Doctor only: `uv run pytest -q tests/ -k doctor`
- A single phase's planned tests: see the relevant story file's "Test plan" section.
- Full suite the way CI sees it (isolated HOME, so local state and the
  owner's real DB stay out of it):
  `HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run pytest -q --ignore=tests/e2e/test_metal.py`
  `npm_config_cache` keeps the mermaid-docs renderer on the warm npm cache;
  without it every fresh-HOME run re-downloads mermaid-cli + Chromium into
  the throwaway HOME (gigabytes per run, and an interrupted download
  corrupts the npx lock).
  `PLAYWRIGHT_BROWSERS_PATH` is not optional: the isolated HOME hides the
  browser cache, and the three `tests/e2e/test_live_bus.py` tests error on
  "Executable doesn't exist" without it (green with it).
- Fast lane: add `-n auto` (pytest-xdist) to any of the above — the full
  suite drops from ~30-45 min serial to ~5-13 min parallel on the owner's
  machine. Prefer it for every full run. UAT conductor tests boot real
  product processes; each xdist worker scans its own port range
  (uat/conductor/runs.py), so parallel runs cannot cross-boot onto one
  port.
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
  read them. Atlas source references have no `line`; the fence finds the
  cited text in the cited file. Do not add count fences.
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


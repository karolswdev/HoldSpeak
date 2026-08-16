# HS-133-11 — The walk

- **Project:** holdspeak
- **Phase:** 133
- **Status:** backlog
- **Depends on:** HS-133-02..10
- **Unblocks:** —
- **Owner:** unassigned

## Problem

Unit tests prove dispatch; they do not prove the sidecar a client
actually meets. Phase exit requires the finished surface exercised live
(Article IX), through the real stdio transport, on a fresh HOME, with
the model-invoking path proven on real metal.

## Scope

### In

- A reusable walk harness committed to `scripts/` (e.g.
  `scripts/mcp_walk.py`): boots `uv run holdspeak-mcp` under an isolated
  HOME, performs initialize → tools/list → resources/list, asserts the
  82-tool / 24-resource catalogue counts and closed schemas, exercises
  at least one tool per family (reads on the fresh DB; safe writes:
  `settings.update` round-trip, `cadence.snooze` on a seeded loop,
  `plugin_job.retry` refusal on a running job) and the
  `holdspeak://cadence/status` resource read, capturing real JSON-RPC
  request/response pairs.
- The live `.43` leg (standing rule: prove LLM features on real metal):
  `ask.run` against the LAN llama.cpp destination, asserting the
  response's receipt names the executed model — control-vs-treatment
  against `ask.models`. Runs from the owner's machine outside the
  sandbox; the harness takes the endpoint from the environment.
- The full check chain through `dw evidence capture`; the harness output
  and JSON-RPC transcript land in the story evidence.
- Full-suite gate for the phase rides this story: the orchestrator's
  quiet-tree full run
  (`HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run pytest -q -n auto --ignore=tests/e2e/test_metal.py`)
  with failures diffed by name against the pre-phase baseline.

### Out

- Screenshot walking (no UI in this phase — the JSON-RPC transcript is
  this phase's "screenshots"). Load/perf testing.

## Acceptance criteria

- [ ] The committed harness runs green from a clean checkout, fresh
  HOME, and its transcript shows every family exercised over real
  stdio.
- [ ] The `.43` `ask.run` proof: receipt model == the destination's
  loaded model, captured live.
- [ ] Full suite: zero regressions against the pre-phase baseline
  (inherited reds diffed by name, loudly).
- [ ] Everything captured via `dw evidence capture`; this story cannot
  be closed by unit tests alone and cannot be waived.

## Test plan

- `HOME=$(mktemp -d) uv run python scripts/mcp_walk.py --json-out` (harness self-test)
- `.githooks/dw evidence capture holdspeak 133 11 -- <harness + suite commands>`

# Working agreements for HoldSpeak

This file is loaded automatically by Claude Code when it opens this
repo. It tells you (the agent) the rules of the road.

## PMO hygiene gate (pre-commit hook)

This repo uses [pmo-roadmap](https://github.com/) (installed locally
from `~/dev/reusable-processes/pmo-roadmap`). Before every commit:

1. Write `.tmp/CONTRACT.md` per the template in
   `pm/roadmap/PMO-CONTRACT.md` §"Contract template".
2. Set every checkbox to `[x]` only after honestly verifying each
   rule for **this** commit.
3. The pre-commit hook validates and deletes the file on success.

**One-time setup per fresh clone:**

```bash
git config core.hooksPath .githooks
```

(The installer set this for the original clone; fresh clones must
re-run it.)

**Methodology:** `pm/roadmap/roadmap-builder.md`.
**Rules canon:** `pm/roadmap/PMO-CONTRACT.md`.

A stale contract (older than `HEAD`) is rejected. An unchecked
contract is rejected. The file is deleted on every successful
commit so each commit requires a fresh one.

If the hook ever blocks you, read its stderr — it tells you exactly
which rule failed and what to fix.

## Roadmap

- **Project README:** `pm/roadmap/holdspeak/README.md`.
- **Current phase:** linked from the project README "Current phase" line.
- **Operating cadence:** every shipping commit updates the story
  header status, the phase's `current-phase-status.md` story-status
  row + "Where we are", this README's "Last updated" line, and any
  project-canon doc the story explicitly mentions. See
  `pm/roadmap/holdspeak/README.md` §"Operating cadence".

## Source canon

These are the docs phases must be grounded in. If any phase document
disagrees with one of these, canon wins:

- `README.md` — public install + usage surface.
- `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` — parent plugin RFC.
- `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` — meeting-side multi-intent routing (MIR-01).
- `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` — dictation pipeline (DIR-01).
- `docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` — web-first runtime migration.
- `pyproject.toml` — package contract.

## Test commands

- All tests: `uv run pytest -q`
- Doctor only: `uv run pytest -q tests/ -k doctor`
- A single phase's planned tests: see the relevant story file's "Test plan" section.

The `Tests ran` rule (PMO contract §3) requires you to actually run
the relevant tests via these commands and read the output before
flipping a story to `done`. Type-check is not validation.

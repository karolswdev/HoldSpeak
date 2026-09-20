---
name: holdspeak-desk
description: Use when changing objects, windows, commands, drop behavior or Desk components. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-desk

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `docs/internal/DESK_GRAMMAR.md`
- `web/ICON-DISCIPLINE.md`
- `web/src/desk/surface/contract.md`
- `docs/DESK_OBJECT_MODEL.md`

## Vocabulary and invariants

Domain truth, workspace layout, selection and command target are different state.

## Change path

Read the verb/drop/Info contracts. Use library controls and the common window frame. Pointer and keyboard entrances must reach the same command. Design before building; use scoped frontend tests named by the change.

Update `docs/DESK_ARCHITECTURE.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_docs_navigation.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_docs_navigation.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

No modal editing or new feature-local socket. Preserve compact, reduced-motion and non-drag paths. Python navigation tests do not validate a face.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

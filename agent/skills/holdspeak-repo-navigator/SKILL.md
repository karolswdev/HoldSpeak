---
name: holdspeak-repo-navigator
description: Use when locating a HoldSpeak capability or planning a cross-subsystem change. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-repo-navigator

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `docs/generated/REPOSITORY_MAP.md`
- `docs/CAPABILITIES.md`
- `docs/SYSTEM_ARCHITECTURE.md`

## Vocabulary and invariants

Source, capability, domain record, operation and Desk projection are distinct. Locate the current call path before choosing an edit.

## Change path

Map ingress → service → persistence → kernel adapter → UI. Keep domain state in its owner. Do not infer unused code from a single entry point.

Update `docs/SYSTEM_ARCHITECTURE.md` and the corresponding Philo capability metadata when behavior
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

An optional remote branch prevents an unconditional local-only claim.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

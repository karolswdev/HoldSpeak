---
name: holdspeak-capability-verifier
description: Use when checking whether a claimed HoldSpeak capability exists, works, or is released. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-capability-verifier

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `docs/internal/philo/data/README.md`
- `docs/CAPABILITIES.md`
- `tests/unit/doc_claims/registry.py`

## Vocabulary and invariants

Code presence, inspected assertions, executed tests, public release and owner observation are separate evidence axes.

## Change path

Inspect the route, service, schema and test assertions; update the relevant metadata row. Preserve unknowns; never promote status because a file exists.

Update `docs/CAPABILITIES.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_phase200_doc_claims.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_phase200_doc_claims.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

Do not equate packaging Beta with owner-verified usability.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

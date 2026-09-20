---
name: holdspeak-troubleshooter
description: Use when diagnosing configuration, capture, model, database or companion failures. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-troubleshooter

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `docs/TROUBLESHOOTING.md`
- `docs/OPERATIONS.md`
- `docs/STORAGE_AND_MIGRATIONS.md`

## Vocabulary and invariants

Unavailable, failed, waiting and indeterminate are distinct diagnoses.

## Change path

Follow the named repair and source check. Reproduce with a temporary config/database; preserve evidence before proposing repair. Do not restore, migrate or delete the owner’s state during a diagnostic walk.

Update `docs/TROUBLESHOOTING.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_doctor_command.py tests/unit/test_doctor_config_honesty.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_doctor_command.py tests/unit/test_doctor_config_honesty.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

Platform permissions and optional backends differ. Never infer success from process exit alone or run a test against the real HOME.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

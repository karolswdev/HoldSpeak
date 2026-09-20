---
name: holdspeak-release-auditor
description: Use when checking release claims, platform availability or schema compatibility. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-release-auditor

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `docs/RELEASING.md`
- `docs/PLATFORMS.md`
- `docs/generated/REPOSITORY_SNAPSHOT.md`

## Vocabulary and invariants

Source snapshot, artifact version, platform setup and public distribution are separate facts.

## Change path

Compare the exact release commit, manifests, migrations and generated capability evidence. Mark unobserved platforms unknown. Keep built companion code distinct from released distribution.

Update `docs/PLATFORMS.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_db_schema_policy.py tests/unit/test_api_surface.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_db_schema_policy.py tests/unit/test_api_surface.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

Never promise rollback compatibility without schema proof; never publish or tag as part of an audit unless the owner requested release.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

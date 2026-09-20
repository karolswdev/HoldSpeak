---
name: holdspeak-connector-author
description: Use when adding or changing a source connector or outbound actuator. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-connector-author

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `docs/CONNECTOR_DEVELOPMENT.md`
- `holdspeak/connector_sdk.py`
- `holdspeak/connector_runtime.py`
- `holdspeak/services/actuator_service.py`

## Vocabulary and invariants

Connector reads, previews, proposals, approval and effect execution are different operations.

## Change path

Choose the existing read or actuator seam. Bind execution to the exact authorized payload and target. Record retries, idempotency and failure at the owning service.

Update `docs/INTEGRATIONS.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_connector_sdk.py tests/unit/test_connector_runtime.py tests/unit/test_actuator_kernel.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_connector_sdk.py tests/unit/test_connector_runtime.py tests/unit/test_actuator_kernel.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

Never turn an extracted action into permission. Fixtures must not post to GitHub, Slack or another live service.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

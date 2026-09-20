---
name: holdspeak-plugin-author
description: Use when adding or changing a meeting-intelligence plugin. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-plugin-author

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `docs/PLUGIN_AUTHORING.md`
- `docs/MEETING_INTELLIGENCE.md`
- `holdspeak/plugins/router.py`

## Vocabulary and invariants

Plugin input, selected job, artifact schema, provider capability and actuator proposal are separate contracts.

## Change path

Use the current SDK and registration route. Add schema and source-attribution assertions. Treat invalid provider output as failure, not a fabricated artifact.

Update `docs/MEETING_INTELLIGENCE.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_plugin_sdk.py tests/unit/test_plugin_provider_admission.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_plugin_sdk.py tests/unit/test_plugin_provider_admission.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

A plugin result does not authorize a side effect. Do not bypass provider admission with a direct model client.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

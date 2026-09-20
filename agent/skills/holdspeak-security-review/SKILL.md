---
name: holdspeak-security-review
description: Use when reviewing data egress, credentials, authority or a new effect path. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-security-review

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `docs/SECURITY.md`
- `docs/AUTHORITY.md`
- `docs/SECURITY_MODEL.md`
- `holdspeak/kernel/admission.py`

## Vocabulary and invariants

Data, compute, authority, secrets and audit are five distinct boundaries.

## Change path

Trace the concrete payload through authority to dispatch and receipt. Identify control-mode changes and hard prerequisites separately. A user gesture can be authority; do not add a second approval only to fit a diagram.

Update `docs/AUTHORITY_MODEL.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_kernel_effect_fence.py tests/unit/test_actuator_kernel.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_kernel_effect_fence.py tests/unit/test_actuator_kernel.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

Never claim privacy from a LAN address or treat in-process plugins as sandboxed. Use denied-path assertions as well as success.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

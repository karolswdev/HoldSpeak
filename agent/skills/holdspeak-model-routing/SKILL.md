---
name: holdspeak-model-routing
description: Use when changing model registration, assignment, execution plans or destinations. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-model-routing

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `holdspeak/services/inference_assignment_service.py`
- `holdspeak/kernel/inference_runner.py`
- `docs/MODEL_RUNTIME.md`
- `docs/EXECUTION_DESTINATIONS.md`

## Vocabulary and invariants

Inventory, assignment, frozen plan, physical attempt and actual destination are separate facts.

## Change path

Preserve plan freezing and readiness validation. Substitute only where current policy allows and record the attempt/reason. Keep provider keys out of ordinary APIs and receipts.

Update `docs/MODEL_RUNTIME.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_phase143_inference_assignments.py tests/unit/test_web_inference_assignment_routes.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_phase143_inference_assignments.py tests/unit/test_web_inference_assignment_routes.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

Endpoint reachability is not model capability. Test remote branches with fixtures, never production secrets.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

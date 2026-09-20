---
name: holdspeak-kernel
description: Use when changing operation admission, claims, journaling, recovery or receipts. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-kernel

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `holdspeak/kernel/runtime.py`
- `holdspeak/kernel/broker.py`
- `holdspeak/kernel/executor.py`
- `docs/KERNEL.md`

## Vocabulary and invariants

Operation identity, claim, warrant, receipt, parent run and projection have different lifetimes.

## Change path

Follow the registered codec and existing executor seam. Preserve authenticated authority, single-winner claims and terminal evidence. Do not invent a parallel lifecycle or turn indeterminate into guessed success.

Update `docs/KERNEL.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_kernel_broker.py tests/unit/test_kernel_effect_fence.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_kernel_broker.py tests/unit/test_kernel_effect_fence.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

The cooperating Python runtime is not an OS sandbox. Preserve exact target and placement binding.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

---
name: holdspeak-dictation
description: Use when changing speech capture, dictation transforms, preview or text delivery. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-dictation

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `holdspeak/runtime/dictation_processing.py`
- `holdspeak/plugins/dictation/pipeline.py`
- `holdspeak/runtime/dictation_delivery.py`
- `docs/DICTATION_ARCHITECTURE.md`

## Vocabulary and invariants

Transcription, transformation, preview and delivery are separate stages. A candidate is not typed output.

## Change path

Trace the requested stage and its failure/fallback path. Preserve correction/replay provenance. Test output delivery without typing into the owner’s active app.

Update `docs/DICTATION_ARCHITECTURE.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_dictation_pipeline.py tests/unit/test_dictation_commit_boundary.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_dictation_pipeline.py tests/unit/test_dictation_commit_boundary.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

Wayland injection, macOS permissions and remote/model branches need explicit treatment; no unattended real-desktop test.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

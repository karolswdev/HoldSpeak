---
name: holdspeak-meetings
description: Use when changing capture, import, intelligence plugins or meeting aftercare. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-meetings

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `holdspeak/meeting_session`
- `holdspeak/plugins`
- `docs/MEETING_ARCHITECTURE.md`
- `docs/MEETING_INTELLIGENCE.md`

## Vocabulary and invariants

Capture, transcript, plugin job, typed artifact and accepted outcome are distinct.

## Change path

Follow session and plugin selection into the stored result. A queued job is not completed intelligence. Extraction is not authority to call GitHub or Slack.

Update `docs/MEETING_AFTERCARE.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_meeting_plugins.py tests/unit/test_meeting_capture_durability.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_meeting_plugins.py tests/unit/test_meeting_capture_durability.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

Do not send fixture transcripts to a real model endpoint or record the owner’s microphone.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.

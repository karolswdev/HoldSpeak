# Evidence — HS-22-06 Phase Exit And Product Handoff

Date: 2026-05-25

## Scope Completed

- Added Phase 22 final summary.
- Marked HS-22-06 done and Phase 22 closed.
- Updated the parent HoldSpeak roadmap to hand off into Phase 23 planning.
- Added a Phase 23 planning draft for the next AI PI companion UX pass.

## Validation

```text
.venv/bin/python -m pytest tests/unit/test_agent_context.py tests/unit/test_tmux_transport.py tests/unit/test_web_runtime.py tests/unit/test_typer.py tests/integration/test_web_dictation_settings_api.py -q
57 passed in 1.23s

scripts/aipi_test.sh -q
195 passed in 7.54s

git diff --check
passed
```

## Product Handoff

Product-ready now:

- AI PI can display a waiting Claude/Codex attention state from HoldSpeak.
- The bridge has a documented companion state model and gesture contract.
- AI PI can start the voice-reply path for a waiting agent.
- Replies can land in the intended Claude/Codex tmux pane and submit with
  Enter, including over SSH/tmux workflows where GUI focus is unavailable.
- The agent hook install guide documents tmux reply delivery.

Still experimental or Phase 23-bound:

- Long agent questions are still shortened for the current display path.
- Multiple simultaneous agent sessions are not yet distinguishable enough on
  the device.
- There is no session preview/browser surface for "which Claude/Codex am I
  answering?"
- `/api/companion/status` still needs a status-shape cleanup so companion
  readiness reflects the nested runtime state consistently.
- LCD marquee behavior is not yet wired into HoldSpeak's companion status.

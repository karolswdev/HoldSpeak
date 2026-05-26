# HS-23-04 Evidence — Device Browse Controls and Selected Target

**Date:** 2026-05-26.
**Story:** [story-04-device-browse-selected-target.md](./story-04-device-browse-selected-target.md).
**Result:** done.

## Gesture Contract

Outside a meeting:

- left single tap sends `agent_question` when companion status reports an agent
  is waiting;
- left double tap sends `agent_next` when companion status reports an agent is
  waiting;
- left single tap still sends `last_segment` when no agent is waiting;
- left double tap remains suppressed when no meeting and no agent target exist.

During a meeting, existing meeting gestures remain higher priority:

- left single tap bookmarks;
- left double tap cycles meeting stats.

## Selected Target

HoldSpeak now stores the selected waiting target in the agent-session registry
under `selected_agent_response`. `get_recent_awaiting_agent_session(...)`
prefers that selected target when it is still fresh, so the same selection is
used by:

- `/api/companion/status`;
- device `agent_question` query;
- device `agent_next` query;
- voice reply routing through tmux/text insertion.

When there is no selected target, the displayed/default target is newest-first.
The first cycle advances to the next waiting session and wraps after the end.

## Validation

```text
.venv/bin/python -m pytest tests/unit/test_agent_context.py tests/unit/test_agent_device.py tests/unit/test_web_runtime.py tests/integration/test_web_server.py::TestCompanionStatusEndpoint -q
52 passed in 0.70s

aipi-lite/.venv/bin/python -m pytest aipi-lite/tests/test_companion_gestures.py aipi-lite/tests/test_bookmark_gesture.py aipi-lite/tests/test_models.py aipi-lite/tests/test_companion_status.py -q
84 passed in 6.64s

scripts/aipi_test.sh -q
204 passed in 8.27s

git diff --check
passed
```

## Live Hardware Check

AI PI was powered on after the offline contract landed.

Observed:

- Bridge reconnected to `aipi-green.local` and repainted link/ready state.
- Companion status exposed `agent_next`, `agent_question`, and `agent_status`.
- Left single tap emitted `agent_question` and painted the selected Codex
  question.
- Left double tap emitted `agent_next` and cycled between:
  - `Codex | holdspeak | no tmux`;
  - `Claude | holdspeak | 1:0.0`.
- LCD repaint cadence was understandable, but repeated fast cycling can quickly
  bounce back to the no-tmux session.

Not yet complete:

- Final voice reply delivery into the Claude tmux pane remains HS-23-06 live
  dogfood. A voice attempt while Codex/no-tmux was selected exposed the
  HS-23-05 guard requirement.

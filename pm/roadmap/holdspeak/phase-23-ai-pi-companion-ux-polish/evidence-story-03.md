# HS-23-03 Evidence — Session Preview List Contract

**Date:** 2026-05-26.
**Story:** [story-03-session-preview-list.md](./story-03-session-preview-list.md).
**Result:** done.

## Contract

`/api/companion/status` now includes a preview list:

```text
agent.sessions.count
agent.sessions.selected_index
agent.sessions.items[]
```

Each item includes:

- `index`;
- `selected`;
- raw `session`;
- structured `identity` from `build_agent_identity_payload(...)`.

The active session remains available at `agent.session` and `agent.identity`.
The preview list is for browse/preview surfaces; it does not yet mutate the
answer target.

## Implementation

- `holdspeak/agent_context.py` adds
  `list_recent_awaiting_agent_sessions(...)`, sorted newest-first with an
  optional limit.
- `get_recent_awaiting_agent_session(...)` now delegates to that list helper
  with `limit=1`.
- `holdspeak/web_server.py` adds `agent.sessions` to the companion status
  payload and marks the selected item.
- Tests pin list ordering and companion status preview shape.

## Validation

```text
.venv/bin/python -m pytest tests/unit/test_agent_context.py tests/unit/test_agent_device.py tests/integration/test_web_server.py::TestCompanionStatusEndpoint -q
41 passed in 0.77s

aipi-lite/.venv/bin/python -m pytest aipi-lite/tests/test_companion_status.py -q
11 passed in 0.21s

scripts/aipi_test.sh -q
199 passed in 7.57s

.venv/bin/python -m pytest tests/unit/test_agent_context.py tests/unit/test_agent_device.py tests/unit/test_web_runtime.py tests/integration/test_web_server.py::TestCompanionStatusEndpoint -q
49 passed in 0.69s

git diff --check
passed
```

AI PI hardware remained offline for this work. Physical browse controls and
selected-target mutation are the next story.

# Evidence — HS-20-01 Agent Waiting Query Surface

- **Date:** 2026-05-24
- **Status:** done
- **Story:** [HS-20-01](./story-01-agent-waiting-query.md)

## What changed

- Added `holdspeak/agent_device.py` for LCD-safe device-facing summaries of captured Claude/Codex awaiting-response state.
- Added device query names:
  - `agent_status` — prefixed status such as `Codex waiting in HoldSpeak: ...`.
  - `agent_question` — latest captured assistant question only.
- Wired `holdspeak/web_runtime.py` device query handling to `get_recent_awaiting_agent_session(max_age_seconds=120)`.
- Documented the new query names in [Device Protocol](../../../../docs/DEVICE_PROTOCOL.md).
- Added unit and WebSocket integration coverage.

## Validation

```bash
.venv/bin/pytest -q tests/unit/test_agent_device.py tests/unit/test_agent_context.py tests/integration/test_device_audio_ingest.py
```

Result:

```text
48 passed in 1.39s
```

```bash
git diff --check
```

Result: passed.

## Notes

- This story deliberately reuses the existing device `query` frame and normal `status` response frame.
- No voice reply routing is included; that is HS-20-02.
- `No agent waiting` is returned when no fresh captured Claude/Codex question exists.

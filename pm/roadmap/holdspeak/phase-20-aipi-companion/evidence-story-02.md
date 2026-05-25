# Evidence — HS-20-02 AIPI Voice Reply To Waiting Agent

- **Date:** 2026-05-24
- **Status:** done
- **Story:** [HS-20-02](./story-02-aipi-voice-reply.md)

## What changed

- Added `target_profile_override_for_agent(...)` in `holdspeak/agent_device.py`.
- Updated `holdspeak/web_runtime.py` so captured voice-typing audio can run through the dictation pipeline.
- Device-originated voice typing now looks for a fresh awaiting Claude/Codex session and passes it into the dictation utterance.
- Waiting Codex sessions force target profile `codex_cli`; waiting Claude sessions force `claude_code`.
- Added a web-runtime unit test proving a device voice reply to a waiting Codex session is typed from the pipeline output and receives:
  - project root from the agent session;
  - target profile `codex_cli`;
  - captured agent context.
- Documented the setup requirement in [Claude/Codex Agent Hook Install](../../../../docs/AGENT_HOOK_INSTALL.md).

## Validation

```bash
.venv/bin/pytest -q tests/unit/test_agent_device.py tests/unit/test_web_runtime.py tests/unit/test_agent_context.py tests/integration/test_device_audio_ingest.py
```

Result:

```text
55 passed in 1.45s
```

```bash
git diff --check
```

Result: passed.

## Notes

- This story does not send replies through a Claude/Codex API. It routes the spoken reply through HoldSpeak's dictation pipeline and then uses the existing text insertion path.
- If text insertion is unavailable, the existing fallback behavior still applies.
- If the dictation pipeline is disabled or unavailable, the web runtime preserves the raw processed transcript.

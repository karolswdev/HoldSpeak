# Evidence — HS-17-02 — Query Last Segment

- **Date:** 2026-05-10
- **Status:** done
- **Story:** [HS-17-02](./story-02-query-last-segment.md)

## What changed

- Added `DeviceQueryFrame` with strict Pydantic validation.
- Added WS dispatch for `{"type":"query","name":"last_segment",...}`.
- Wired runtime callback responses as regular `status` frames.
- Implemented active-meeting lookup for the latest finalized segment from the querying device.
- Added visible fallback responses:
  - `No transcript yet`, `ttl_ms=5000`
  - `Unknown query: <name>`, `ttl_ms=3000`
- Extended `docs/DEVICE_PROTOCOL.md`.

## Verification

```bash
.venv/bin/pytest -q tests/unit/test_device_active_frames.py tests/integration/test_device_audio_ingest.py
```

Result: included in focused run, `170 passed in 1.56s`.

## Notes

- Historical saved-meeting lookup is deliberately not included because the current SQLite `segments` table does not persist `device_id`.
- Voice-typing transcript lookup remains out of scope until HoldSpeak has a durable per-device dictation transcript store.

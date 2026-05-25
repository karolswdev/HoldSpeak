# Evidence — HS-17-05 — Periodic Recording-Tick Status Emitter

- **Shipped:** 2026-05-10
- **Commit:** pending — see same commit as this evidence file
- **Owner:** karol

## Files touched

- `holdspeak/device_recording_tick.py` (new) — `RecordingTicker` class with daemon-thread scheduler. Cadence alignment via `next_tick_at += interval_s` so the ticker doesn't drift over the meeting's lifetime. Pure helper `_format_elapsed(seconds) -> "Recording MM:SS"` with cap at 99 minutes.
- `holdspeak/web_runtime.py`:
  - `import time` added.
  - New `RecordingTicker` instance created alongside `DeviceStatusEmitter`, sender wired to `device_status.broadcast(ids, text, ttl_ms=0)`.
  - `_start_meeting` calls `recording_ticker.start(started_at_monotonic=time.monotonic(), device_ids=attached_for_status)` immediately after the initial `Recording 00:00` broadcast.
  - `_stop_active_meeting` calls `recording_ticker.stop()` *before* the `Saving meeting...` broadcast so no stale tick can land after the user's been told the meeting is saving.
- `tests/unit/test_device_recording_tick.py` (new) — 19 cases (see "Acceptance criteria" in `story-05`).
- `docs/DEVICE_PROTOCOL.md` — section 6.2 (status frames during a meeting) updated: new `Recording MM:SS` periodic row, paragraph documenting cadence + cap + lifecycle.

## Verification artifacts

```
$ .venv/bin/python -m pytest tests/unit/test_device_recording_tick.py -q
19 passed in 1.70s

$ .venv/bin/python -m pytest tests/integration/test_device_status_pushback.py \
                              tests/integration/test_device_meeting_session.py \
                              tests/integration/test_device_audio_ingest.py \
                              tests/unit/test_device_recording_tick.py -q
47 passed in 3.27s
```

**Live-hardware verification (2026-05-10):** AIPI-Lite device on the LAN, bridge connected, HoldSpeak running with the new code. Started a meeting via `POST /api/meeting/start {"devices":["aipi-1"]}`, ran for 18 s, stopped. Bridge log captured the inbound status frames:

```
22:40:04.843  ws.status.recv  text="Recording 00:00"  ttl_ms=0   (meeting start)
22:40:09.843  ws.status.recv  text="Recording 00:05"  ttl_ms=0   (+5.000 s)
22:40:14.844  ws.status.recv  text="Recording 00:10"  ttl_ms=0   (+5.001 s)
22:40:19.843  ws.status.recv  text="Recording 00:15"  ttl_ms=0   (+5.000 s)
22:40:31.159  ws.status.recv  text="Saving meeting..." ttl_ms=0  (post-stop, no stale ticks)
```

Cumulative cadence drift across 3 ticks: **1 ms over 10 seconds** — well within tolerance. User confirmed the LCD displayed each tick correctly: "yep - it's tickin' alright. Fokking amazing."

## Acceptance criteria — re-checked

All 6 brackets `[x]` — see [`story-05-recording-tick-emitter.md`](./story-05-recording-tick-emitter.md).

## Deviations from plan

- Story originally specified "Integration test: fake WS client records ≥ 2 ticks during a simulated 12-second meeting." Shipped as 19 *unit* tests of the `RecordingTicker` class directly (cleaner isolation; full integration covered by the live-hardware verification above). The unit test `test_fires_periodic_ticks` is the moral equivalent — records ≥ 2 ticks over a 0.35 s simulated meeting at 0.1 s cadence.
- Format `Recording MM:SS` (zero-padded both fields) rather than `Recording M:SS` (story's exact spec). Zero-padding keeps the LCD width stable across the first minute (visually less jumpy at the 00:09 → 00:10 boundary).
- Added a `99:00` clamp at 100+ minute meetings — a tiny cosmetic concession to LCD width. Not in original spec; recorded here for honesty.

## Follow-ups

- **HS-17-06** (meeting title alternation) — extends this story's payload. Its acceptance reuses the same ticker; this story's `start/stop` lifecycle is the API HS-17-06 will plug into.
- The 5 s cadence is fixed at the constant `DEFAULT_TICK_INTERVAL_S`. If field experience suggests per-meeting customization, expose via meeting metadata. Not in v1.

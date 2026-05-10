# Evidence — HS-17-08 — Per-Segment Transcript Pushback

- **Shipped:** 2026-05-10
- **Commit:** pending — same commit as this evidence file
- **Owner:** karol

## Files touched

- `holdspeak/device_status.py`:
  - New `LCD_TEXT_MAX_CHARS = 30` constant.
  - New `truncate_for_lcd(text, max_len=30)` helper — handles None / empty / short / exact / exceed / ≤1 edges.
  - New `push_segment_to_devices(emitter, attached_ids, segment, *, ttl_ms=3000)` helper — duck-types `segment.speaker` + `segment.text`, formats as `f"{speaker}: {text}"`, truncates, broadcasts. Filters falsy IDs. Reusable by HS-17-07 / HS-17-09 / HS-17-12 etc.
  - `__all__` extended with the three new exports.
- `holdspeak/web_runtime.py`:
  - Import `push_segment_to_devices` alongside `DeviceStatusEmitter`.
  - `_on_meeting_segment(segment)` extended: after the existing web-server broadcast, reads `_active_meeting_session()` and its attached device IDs, calls `push_segment_to_devices(device_status, attached_ids, segment)`. Wrapped in try/except so a push failure can't break the web broadcast.
- `tests/unit/test_device_status_helpers.py` (new) — 19 cases (see above).

## Verification artifacts

```
$ .venv/bin/python -m pytest tests/unit/test_device_status_helpers.py -q
19 passed in 0.03s

$ .venv/bin/python -m pytest \
    tests/integration/test_device_status_pushback.py \
    tests/integration/test_device_meeting_session.py \
    tests/integration/test_device_audio_ingest.py \
    tests/unit/test_device_recording_tick.py \
    tests/unit/test_device_status_helpers.py -q
66 passed in 3.31s
```

**Live-hardware verification (2026-05-10):** HoldSpeak restarted with the new code, bridge connected to `aipi-green.local`, meeting `118aea56` started with the device attached. User held the right button and spoke. Bridge log captured the segment flash:

```
23:31:05.121  ws.status.recv   text="Karol: 컴백 컴백"  ttl_ms=3000
23:31:05.121  update_screen.ok msg="Karol: 컴백 컴백"
23:31:07.402  ws.status.recv   text="Recording 04:25"  ttl_ms=0   (sticky resumes)
23:31:07.402  update_screen.ok msg="Recording 04:25  "
23:31:20.036  ws.status.recv   text="Remote: ... ... ... ... ... .…"  ttl_ms=3000
23:31:20.036  update_screen.ok msg="Remote: ... ... ... ... ... .…"
```

User confirmed seeing each segment flash on the LCD bottom row during the meeting. The `Karol:` prefix comes from `segment.speaker = self.mic_label = "Karol"` (the bridge's `DEVICE_LABEL` env). The `Remote:` segment is HoldSpeak's system-audio leg picking up host machine noise + Whisper hallucinating `...` from it — exact `…` truncation visible in the payload (29 chars + ellipsis = 30, the LCD_TEXT_MAX_CHARS cap).

Whisper auto-detected the user's short utterance as Korean ("컴백 컴백" = "comeback comeback") — Whisper config quirk, not HoldSpeak's concern. The transcription mechanism still produced a finalized segment, which is what HS-17-08 cares about.

## Acceptance criteria — re-checked

All 6 brackets `[x]` — see [`story-08-per-segment-transcript-pushback.md`](./story-08-per-segment-transcript-pushback.md).

## Deviations from plan

- Story originally proposed extending `MeetingSession` directly. Implementation hooked `web_runtime`'s existing `_on_meeting_segment` callback instead — single point, no `meeting_session.py` churn, naturally covers all three segment paths (mic / system / device).
- Integration test originally proposed against a fake WS client. Shipped as unit tests for the pure helpers (truncate + push_segment) + live-hardware integration verification above. The unit tests cover the load-bearing logic; the live trace is the moral equivalent of an integration test.
- Speaker self-label filtering ("don't show `Karol:` on Karol's own device") was discussed in story notes but deferred: shipped without it, will revisit after multi-device field experience. Showing the speaker prefix is useful when multiple speakers attend the same meeting from different devices — the prefix becomes load-bearing.

## Follow-ups

- **Throttling for fast speech.** Live verification only saw one user-spoken segment per ~10s — too sparse to stress the cadence. The existing flash-replaces-flash mechanic in the bridge's `_paint_activity` should handle bursts, but worth observing during a fast-paced multi-speaker meeting.
- **Host system-audio segments are noise.** The `Remote: ... ... ...` segments are technically working as designed (Whisper transcribed something), but they're not useful content. Out of scope for HS-17-08; a separate story might want to filter empty/repetitive transcriptions at the meeting-session level.
- **HS-17-09 (realtime action items)** layers on top of this — if a segment classifies as an action, push `Action: <text>` instead of (or alongside) the per-segment `<speaker>: <text>` flash.

# Evidence — AIPI-4-06 — Last Transcript Gesture

- **Status:** bridge-side implementation complete; live hardware verification pending
- **Date:** 2026-05-10
- **Commit:** pending close-out commit on branch `mine` (working tree)
- **Owner:** karol

## Files touched

- `holdspeak_proto.py` — added strict `QueryFrame` model for `{"type":"query","name":"last_segment","at":...}`.
- `bridge/device.py` — left-button single-tap resolution now routes in-meeting taps to the existing bookmark event and out-of-meeting taps to `query:last_segment`. Existing AIPI-4-14 double-tap WIP remains layered above this path.
- `bridge/holdspeak.py` — outbound `query:last_segment` starts a 2s timeout; the next inbound `status` frame cancels it. Query response text is truncated to the 30-character LCD budget.
- `tests/test_models.py` — `QueryFrame` round-trip and validation coverage.
- `tests/test_bookmark_gesture.py` — single-tap in/out-of-meeting routing coverage.
- `tests/test_dispatch.py` — query timeout, timeout cancellation, and response truncation coverage.

## HoldSpeak dependency

Resolved by HoldSpeak HS-17 on 2026-05-10:

- `docs/DEVICE_PROTOCOL.md` documents `query:last_segment`.
- HoldSpeak accepts the query over `/api/devices/audio`.
- HoldSpeak replies with a normal `status` frame (`ttl_ms=5000`).
- Malformed query frames are logged/dropped without closing the WebSocket.

Reference:

```text
/home/karol/dev/HoldSpeak/pm/roadmap/holdspeak/phase-17-device-initiative/final-summary.md
```

## Verification artifacts

```text
$ .venv/bin/pytest -q tests/test_models.py tests/test_bookmark_gesture.py tests/test_dispatch.py
71 passed in 6.16s

$ .venv/bin/pytest -q tests/test_holdspeak_leg.py tests/test_device_methods.py tests/test_bookmark_gesture.py tests/test_dispatch.py tests/test_models.py
96 passed in 6.86s

$ .venv/bin/pytest -q
160 passed in 7.49s

$ .venv/bin/ruff check .
All checks passed!

$ git diff --check
passed
```

## Acceptance criteria

- [x] HoldSpeak dependency resolved by HS-17.
- [x] `QueryFrame` exists with `extra="forbid"` and `name: Literal["last_segment"]`.
- [x] Out-of-meeting single-tap emits the query.
- [x] In-meeting single-tap still routes to AIPI-4-01 bookmark.
- [x] Response paints through the existing `status` dispatch path.
- [x] Query response text truncates to 30 characters.
- [x] No response within 2s paints `Query timeout`.
- [ ] Live verification: complete a device-sourced meeting segment, leave meeting state, short-press left, and observe last segment text on LCD within roughly 1s.

## Notes

- The timeout path uses the current LVGL error symbol rather than the story's older ASCII `/!\` text. This matches AIPI-4-04/AIPI-4-11 LCD conventions.
- V1 has no request ID. Any inbound `status` frame after a query counts as the response and cancels the timeout, matching the story's no-correlation decision.
- Because AIPI-4-14 double-tap work is present in the working tree, a single-tap fires after the double-tap window resolves. That preserves double-tap detection without changing the AIPI-4-06 protocol.

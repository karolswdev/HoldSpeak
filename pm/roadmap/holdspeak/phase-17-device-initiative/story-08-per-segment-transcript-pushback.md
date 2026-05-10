# HS-17-08 — Per-Segment Transcript Pushback to Device LCD

- **Project:** holdspeak
- **Phase:** 17
- **Status:** done
- **Depends on:** HS-14-07 (device-status substrate); HS-17-05 (Recording-tick infrastructure for cadence/sticky/flash semantics)
- **Unblocks:** —
- **Owner:** unassigned

## Problem

During a meeting, HoldSpeak's transcription pipeline finalizes utterance segments at a steady rate (typically every 2-8 seconds per phrase). The AIPI-Lite device sees none of these in real time — its LCD shows the periodic `Recording MM:SS` tick (HS-17-05) but no transcript content. The user is holding a device that captured the audio, but the device is silent about what's being said.

This is the killer feature surfaced 2026-05-10 alongside HS-17-07: turn the device into a **live confirmation channel** during meetings. Every finalized utterance flashes briefly on the LCD so the speaker can verify the device is actually capturing intelligible speech (not muffled garble or dropped audio).

## Scope

### In

- New emitter: on `MeetingSession.add_segment(...)` (or wherever finalized segments land), push a `status` frame to all attached devices: `{type: status, text: <truncated segment text>, ttl_ms: 3000}`.
- Truncation at 30 chars + `…` (matches HS-17-06 / AIPI-4-06 LCD width budget).
- **Throttling:** segments fire faster than 5s during fast speech. The `ttl_ms: 3000` flash naturally truncates display time, and a new segment cancels the previous flash's revert (existing `_paint_activity` state machine in `bridge/holdspeak.py`). No further throttling needed at server side — let the device's revert mechanic do the work.
- Sticky baseline stays the `Recording MM:SS` tick from HS-17-05 — segments are flashes that revert to it.
- Speaker attribution: include the speaker label (or `{label}` placeholder per `DeviceStatusEmitter._render`) when available: `Karol: hello world`. Truncate the COMBINED string to 30 chars.
- Integration test in `tests/integration/test_device_segment_pushback.py`: fake WS records segment flashes over a simulated 3-segment meeting; asserts text/truncation/cadence.
- `docs/DEVICE_PROTOCOL.md` extended.

### Out

- Streaming partials (unfinalized hypotheses). Only finalized segments land on the LCD.
- Per-device filtering ("only show segments from speakers other than this device") — out for v1; could be a follow-up if multi-device meetings show speaker-source clutter.
- Audio-level visual cue alongside the text — that's AIPI-4-02 (mic meter).
- Segment editing / re-finalization re-paints — if HoldSpeak ever revises a segment, the older flash has already expired; no re-paint needed.

## Acceptance Criteria

- [x] `web_runtime.py:_on_meeting_segment` extended with a per-segment LCD push via the new `push_segment_to_devices` helper. No changes to `meeting_session.py` (the segment loop already calls `on_segment` for every finalized segment across all three transcription paths — mic, system, device-audio — so the single hook in `web_runtime` catches all).
- [x] Truncation at 30 chars + `…` via new `truncate_for_lcd(text, max_len=30)` in `device_status.py`. Reusable by HS-17-07 + HS-17-09 + HS-17-12 etc.
- [x] Speaker label resolved via `segment.speaker` (TranscriptSegment field — `mic_label` / `remote_label` / device's resolved label per the meeting_session code). Falls back to `"?"` when speaker is None/empty.
- [x] Unit tests: 19 cases in `tests/unit/test_device_status_helpers.py` covering `truncate_for_lcd` (parametrized over edges: empty, exact-max, exceed, short-max, max=0 fallback, None) + `push_segment_to_devices` (default ttl, truncation, missing speaker, empty text, no-devices no-op, falsy-id filter, multi-device, custom ttl, real-emitter integration). Suite regression on device-related tests: 66/66 passing.
- [x] `docs/DEVICE_PROTOCOL.md` updated with the per-segment row + cadence note.
- [x] Live verification (2026-05-10, against AIPI-Lite `aipi-green.local`): meeting started, user spoke into mic. Bridge log captured the segment flash at 23:31:05:
  - `ws.status.recv text="Karol: 컴백 컴백" ttl_ms=3000` (HoldSpeak push)
  - `update_screen.ok msg="Karol: 컴백 컴백"` (bridge paint)
  - Reverted to Recording-tick `Recording 04:25  ` at 23:31:07 (next 5s tick).
  - Additional `Remote: ... ... ... ... ... .…` segment from system-audio leg (truncated at 30 chars with ellipsis) demonstrates the speaker-leg-aware emit + truncation working under noise.

## Test Plan

- **Unit:** truncation + label-formatting helper (parametrized over edge cases: long speaker name, long text, both, empty label).
- **Integration:** fake WS + mocked MeetingSession; verify segment-flash ordering + cadence.
- **Manual:** AIPI-Lite hardware + a real meeting; check LCD reflects what you say.

## Notes

- **Cadence is the design risk.** Fast speech produces segments every 2-3s. The LCD's `_paint_activity` state machine handles flash-replaces-flash cleanly (newest paint cancels pending revert), but if segments fire faster than ~1Hz the device might never settle to the Recording sticky. That's *probably fine* — the user sees a constant stream of text, which is what they want — but worth observing in live test.
- **Speaker attribution gotcha.** The device that captured the audio might be the same device displaying it. Showing `Karol: <text>` on Karol's own device feels redundant. Consider stripping self-label if the attached device's label matches the speaker label. Defer the decision to live observation.
- **Multi-device meetings** (AIPI-4-03) get this for free: each attached device sees all segments, not just its own. Makes the "other person is talking" affordance visible.
- **Combines beautifully with HS-17-06** (meeting title in tick): tick payload alternates `Recording 12:34` / `<title>` / `<latest segment>` for a rich device-side view. Could fold them together as a refactor.

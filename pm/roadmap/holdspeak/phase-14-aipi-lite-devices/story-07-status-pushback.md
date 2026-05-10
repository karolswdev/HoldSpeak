# HS-14-07 - Server → Device Status Push-Back Protocol

- **Project:** holdspeak
- **Phase:** 14
- **Status:** done
- **Depends on:** HS-14-04
- **Unblocks:** HS-14-08
- **Owner:** unassigned

## Problem

Today the AIPI-Lite LCD shows `Listening...` / `Thinking...` /
final-reply text driven by the standalone bridge. Once the bridge
becomes a thin protocol translator (AIPI-2 in the AIPI-Lite
roadmap), HoldSpeak owns the application state. The device should
reflect HoldSpeak's view: meeting state ("Recording 12:34"),
voice-typing acknowledgments, bookmark confirmations, and so on.

This story owns the **server → device protocol**: the schema and
a handful of canonical events HoldSpeak emits during a session.
The bridge forwards these to the device's existing
`update_screen` ESPHome service. (The reverse direction —
buttons-as-events from the device — is also lit up here as a
small additional message type, since it shares the same control
channel.)

## Scope

- **In:**
  - Add to `holdspeak/device_audio_ws.py`: outbound status
    message schema:
    `{type: "status", text: str, ttl_ms: int = 0}` (ttl 0 means
    "until next status").
  - Define a small set of emitter call sites:
    - voice-typing: `Listening...` on start, `Thinking...` on
      stop, transcript snippet on completion (≤ ~80 chars).
    - meeting: `Recording 00:00` updated each minute,
      `Bookmark @ 12:34` on each bookmark, `Saving meeting...`
      on stop.
  - Inbound event message schema:
    `{type: "event", name: "long_press" | "double_tap" | ...,
       at: float}`. Long-press during an active meeting fires a
    bookmark via the existing `MeetingSession.add_bookmark`
    using `at` as the timestamp anchor.
  - Per-device label substitution: `{label}` placeholder in
    server-emitted text resolves to the device descriptor's
    label.
  - Integration test
    `tests/integration/test_device_status_pushback.py`: opens a
    WS, simulates a meeting start/bookmark/stop sequence,
    asserts the expected sequence of status messages arrived.

- **Out:**
  - Rich UI on the device side (eyes / icons / progress bars).
    LCD is plain text in phase 14.
  - Localization. English-only this phase; substitution
    pattern leaves the door open.
  - Long-running emitters across reconnect (status replay on
    reconnect). Reconnect = blank slate this phase.

## Acceptance Criteria

- [x] Server emits `Listening...` / `Thinking...` /
  transcript-snippet on voice-typing turns to the originating
  device.
- [x] During a meeting, the device receives a status update
  on bookmark and on save.
- [x] Inbound `event: "long_press"` during an active meeting
  creates a bookmark on the session.
- [x] `tests/integration/test_device_status_pushback.py` green.
- [ ] Old standalone-bridge LCD strings (`Listening...`,
  `Thinking...`) are now driven by the server, not the bridge —
  verified manually with the AIPI-Lite hooked up. *Pending
  manual smoke test against real hardware; closing this in
  HS-14-08's DoD pass.*

## Test Plan

- Unit: emitter helpers tested at unit level
  (`tests/unit/test_status_emitter.py`).
- Integration:
  `uv run pytest tests/integration/test_device_status_pushback.py`.
- Manual: AIPI-Lite + bridge connected; voice-type a sentence,
  watch LCD go through the full sequence; start a meeting,
  long-press during it, watch bookmark message; stop meeting,
  watch save message.

## Notes

- This story closes the loop visually. Once it lands, the
  AIPI-Lite is no longer running its own standalone LLM — it
  is a HoldSpeak satellite end-to-end, with HoldSpeak as the
  source of truth for what's on the screen.
- Long-press = bookmark is the most useful in-meeting button
  binding. Other gestures (double-tap, triple-tap) are
  reserved for future use; the protocol just ferries them.
- The bridge's job for this story (AIPI-Lite-side) is to
  translate inbound `status` messages into ESPHome
  `update_screen` service calls, and outbound device button
  events into `event` messages on the WS. Tracked in
  AIPI-2.

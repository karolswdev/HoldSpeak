# AIPI-2-03 - Control Mapping: Button Events → WS Start/Stop

- **Project:** aipi-lite
- **Phase:** 2
- **Status:** done
- **Depends on:** AIPI-2-01, AIPI-2-02
- **Unblocks:** AIPI-2-05, AIPI-2-06
- **Owner:** karol

## Problem

With the skeleton (01) and audio path (02) in place, voice typing
works end-to-end *if* something fires `start` and `stop` control
frames at the right moments. This story wires the device's right
button to those frames, replacing the legacy `voice_assistant.start`
/ `voice_assistant.stop` flow that the local bridge.py used to drive.

## Scope

### In

- Subscribe to the device's `right_button` `binary_sensor` state via
  aioesphomeapi.
- On `right_button` press → send WS frame `{"type":"start"}` to
  HoldSpeak. Trigger ESPHome `voice_assistant.start` on the device
  (so its mic capture begins; the captured frames flow through the
  audio path from story-02).
- On `right_button` release → send WS frame `{"type":"stop"}`. Trigger
  `voice_assistant.stop` on the device. HoldSpeak drains the audio
  queue and types the transcript into the focused app on the host.
- Handle inbound `{"type":"error","code":"session_busy"}` from
  HoldSpeak gracefully: log, surface to the device's LCD via
  `update_screen` with a brief "Busy" message, treat the press as a
  no-op. (This happens when another device or the host hotkey is
  already typing.)
- Existing **triple-tap = continuous mode** behaviour stays a local
  device-side toggle for now (see Notes). It does NOT map to a
  HoldSpeak meeting; meeting mode is host-driven (AIPI-2-05).

### Out

- Long-press = AP-mode entry — that's AIPI-1-05's left-button
  gesture and stays untouched.
- Mapping triple-tap to a HoldSpeak control frame — deferred
  decision, see phase decisions.
- Multi-button combos (both buttons together, etc.).
- Inbound `status` frames driving LCD richness — *available*
  (HS-14-07 shipped) but explicitly out of phase 2 to keep scope
  tight. Story-01's skeleton ships a no-op `status` handler stub.
- **Outbound `event` frames bridge → server.** HS-14-07 wired the
  server-side bookmark hook (`{"type":"event","name":"long_press"}` →
  `MeetingSession.add_bookmark`), but no device gesture in phase 2
  maps to it (right button is voice-typing; left button is AIPI-1
  AP-mode/factory-reset; triple-tap is local continuous mode). The
  bridge does NOT emit `event` frames in this phase — the
  server-side hook stays dormant. Wiring a gesture (e.g., a
  left-button quick-tap during a meeting) is a follow-up after
  field experience.

## Acceptance Criteria

- [x] Press the right button on the device → `_handle_va_start`
  enqueues a `StartFrame` onto the bridge's `control_queue`;
  `HoldSpeakLeg._control_sender` drains the queue and sends the
  JSON text frame to HoldSpeak. `control.sent` is logged with a
  preview. **Pending HoldSpeak running** for the
  `device.audio.session.start` server-side log verification.
- [x] Release the right button → `_handle_va_stop` enqueues a
  `StopFrame` AND fires
  `client.send_voice_assistant_event(VOICE_ASSISTANT_RUN_END)`
  so the firmware's `voice_assistant.on_end` trigger fires
  (continuous-mode re-arm). **Pending HoldSpeak running** for
  the end-to-end transcription-typed verification.
- [x] If HoldSpeak responds with `error: session_busy`, the bridge
  fires `on_session_busy` (set in `_run` to
  `device.update_screen("Busy")`); the LCD flashes "Busy" via
  the firmware's existing `update_screen` API service. The error
  doesn't kill the WS; the bridge logs `session_busy.handler.*`
  on success/error. The LCD reverts to whatever the firmware's
  next `on_press`/`on_release` writes (typically "Thinking..."
  on release), so the "Busy" message is naturally short-lived
  even without a manual TTL. **Pending HoldSpeak running.**
- [x] Existing **triple-tap continuous mode** untouched. The
  `continuous_mode` global + the firmware's `on_multi_click`
  handler stay as they are; bridge has no opinion about it.
  Continuous mode just means many start/stop cycles back-to-back
  from the bridge's perspective (each one a discrete WS session
  on HoldSpeak's side). **Inspected:** the diff doesn't touch
  `aipi.yaml`'s right-button handler; the bridge changes are
  additive. *Not tested on hardware* — pending the same
  hardware run as the rest.
- [ ] Right-button press while the bridge is reconnecting to
  HoldSpeak: control frames pile up in `control_queue` (cap
  100). On reconnect, the bound is enforced — overflow warns
  + drops with `control.queue.full`. Audio queue drains pre-
  session per AIPI-2-02 so stale audio doesn't leak across
  the reconnect. **Pending live verification.**
- [x] Hold-press + release with the bridge disconnected from
  the device: bridge logs aren't generated (no callback fires);
  ESPHome's local handlers in `aipi.yaml` (`Listening...` /
  `Thinking...`) keep working independently — they don't depend
  on the bridge being live. **Inspected:** the on_press /
  on_release handlers in `aipi.yaml` use only firmware-local
  actions (`switch.turn_off`, `lvgl.label.update`,
  `voice_assistant.start`); no API call requires the bridge.

## Test Plan

- **Unit:** pure event-mapping function — given a state-change event
  shape, returns the right WS frame. Easy to test with fixtures.
- **Integration (manual):**
  1. With HoldSpeak + bridge + device all live:
  2. Open a text editor with focus on the host machine.
  3. Press right button, say "hello world", release.
  4. Verify "hello world" appears in the editor within ~2 s.
  5. Trigger `session_busy`: in HoldSpeak's web UI, click the
     local-record hotkey to claim the session, then press the
     device's button. Confirm the LCD shows "Busy".
  6. Triple-tap the right button. Verify the LCD flips to "Always
     listening" and back, and that the bridge logs the toggle.

## Notes

- **The `continuous_mode` global in `aipi.yaml` survives this
  story unchanged.** It's a device-side persistent flag that
  controls whether `voice_assistant.start` re-arms after each
  utterance. Today it makes the device hot-mic indefinitely; with
  HoldSpeak in the loop, the same behaviour means "the bridge will
  see continuous start events from voice_assistant," which we'd
  translate into one long start-stream-stop cycle. The clean way
  is for the bridge to detect continuous mode (it can read the
  global via aioesphomeapi state) and convert it into one
  long-lived `start` until the user toggles back. **Implement
  this only if it's trivial; otherwise mark as known-issue and
  defer.**
- **`session_busy` UX:** the LCD's `update_screen` service already
  exists in `aipi.yaml`. The bridge calls it via aioesphomeapi:
  ```python
  await client.execute_service(update_screen_key, msg="Busy")
  ```
- The current `bridge.py` already drives `voice_assistant.start` /
  `voice_assistant.stop` — extract that pattern, then add the WS
  control-frame fork next to it.
- Do **not** map any new device gesture to "enter meeting mode" in
  this phase. Meeting mode is host-driven; the device is a passive
  participant. Decision documented in the phase status.

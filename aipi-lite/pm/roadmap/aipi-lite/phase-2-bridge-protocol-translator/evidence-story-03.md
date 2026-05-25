# Evidence — AIPI-2-03 — Control Mapping: Button Events → WS Start/Stop

- **Shipped:** 2026-05-07
- **Commit:** `2de1c18` (`feat(bridge): AIPI-2-03 control mapping (button → WS, session_busy → LCD)`)
- **Owner:** karol

## Files touched

- `bridge.py` (later `bridge/device.py` + `bridge/holdspeak.py`):
  - `DeviceLeg._handle_va_start` enqueues `StartFrame` on a 100-cap `control_queue`; `_handle_va_stop` enqueues `StopFrame` and fires `VoiceAssistantEventType.VOICE_ASSISTANT_RUN_END` to re-arm continuous mode.
  - `HoldSpeakLeg._control_sender` task drains `control_queue` → WS text frames; gathered alongside heartbeat / receiver / audio-sender / metrics tasks.
  - Inbound `error: session_busy` originally fired `on_session_busy` callback (`device.update_screen("Busy")`). **Replaced in AIPI-2-07** by the more general `on_link_update` / `on_activity_update` pair — `session_busy` now flashes `Busy  [?]` for 3 s via the activity state machine.
  - `DeviceLeg.update_screen(msg)` calls the firmware's existing `update_screen` API service (handle cached on connect post-AIPI-2-08).

## Verification artifacts

```
$ .venv/bin/python -m pytest -q
98 passed in 2.80s
```

Relevant unit-test coverage:
- `tests/test_device_methods.py` — `_handle_va_start`/`_stop`, `_enqueue_control` overflow, `update_screen` mock-APIClient coverage.
- `tests/test_holdspeak_leg.py` — control-frame forwarding through a fake `websockets.serve` server.
- `tests/test_dispatch.py` — `session_busy` → activity flash unit-tested directly (post-AIPI-2-07 generalisation).

**Live evidence** (2026-05-08, pre-package-split, with the original `on_session_busy` callback shape): button-press → "hello world" spoken → release → text typed into the focused host editor within ~2 s. See `evidence-story-02.md` for the same live trace; voice typing **is** control-mapping working end-to-end.

## Acceptance criteria — re-checked

- [x] Right-button press enqueues `StartFrame` → `control_queue` → drained by `_control_sender` to WS — verified live 2026-05-08; unit-tested in `test_device_methods.py` + `test_holdspeak_leg.py`.
- [x] Right-button release enqueues `StopFrame` AND fires `VOICE_ASSISTANT_RUN_END` — verified live 2026-05-08 (continuous-mode re-arm worked); unit-tested in `test_device_methods.py`.
- [x] `error: session_busy` paints "Busy" on the LCD — generalised in AIPI-2-07 to `Busy  [?]` flash for 3 s; unit-tested in `test_dispatch.py`. **Live `session_busy`-while-typing scenario not exercised on 2026-05-08** (single-device test); deferred per phase final-summary.
- [x] Triple-tap continuous mode untouched — `aipi.yaml` right-button handler diff inspected; bridge changes are additive. The 2026-05-08 live session ran in non-continuous mode; **continuous-mode loop with HoldSpeak in the path not live-smoked at phase close.**
- [~] Reconnect-with-control-frames-piling-up: `control_queue` cap of 100 enforced; overflow logs `control.queue.full` and drops. Unit-tested in `test_device_methods.py`. **Live "press during HoldSpeak reconnect" deferred.**
- [x] Bridge-disconnected-from-device hold-press: firmware's local LVGL handlers run independently — inspected `aipi.yaml`'s on_press / on_release (`switch.turn_off`, `lvgl.label.update`, `voice_assistant.start`); none require the bridge.

## Deviations from plan

- The `on_session_busy` single-callback API was generalised in AIPI-2-07 to `on_link_update` + `on_activity_update`. Net behavioural change: `Busy` is now a 3 s flash with revert to the sticky activity, not a manual one-shot. This is a strict UX improvement; recorded here so a reader looking at `2de1c18` doesn't get confused by the disappearance of `on_session_busy`.
- Continuous-mode + meeting-during-continuous-mode interactions deliberately not live-tested at phase close. See phase final-summary's deferred list.

## Follow-ups

- Wiring an outbound `event` frame (e.g., left-button quick-tap during a meeting → `MeetingSession.add_bookmark`) — the server hook is dormant; phase 2 explicitly excludes emitting `event` frames. Recorded in phase final-summary as an AIPI-3 candidate.

# Evidence — AIPI-4-08 — Link State Re-trigger on Device Reconnect

- **Shipped:** 2026-05-10
- **Commit:** pending close-out commit on branch `mine` (working tree)
- **Owner:** karol

## Files touched

### Bridge

- `bridge/holdspeak.py`:
  - New `_last_link_state: str | None = None` field tracking the most recent link state passed through `_call_link`.
  - `_call_link` updated to set `_last_link_state` *before* invoking the handler (so the state is stored even if the handler errors or is unset).
  - New async method `republish_link_state()` — no-op if no state set; else calls `_call_link(self._last_link_state)`.
- `bridge/device.py`:
  - New `on_device_ready: Callable[[], Awaitable[None]] | None` kwarg on `__init__`.
  - `_on_connect` calls `on_device_ready()` after `_cache_lcd_services`, `_cache_button_entities`, and `subscribe_states` complete. Handler errors are swallowed (LCD is UX, not correctness).
- `bridge/cli.py`:
  - `_run` wires `device.on_device_ready = holdspeak.republish_link_state` post-construction, alongside the existing late-bound `is_in_meeting` / `paint_bookmark_flash` wires.

### Tests

- `tests/test_link_retrigger.py` (new): 10 cases covering:
  - `republish_link_state()` no-op when no state set; state tracking via `_call_link`; tracking when handler is None; tracking when handler errors; re-fire of last state; latest-state-wins on multiple paints.
  - `DeviceLeg._on_connect` fires `on_device_ready` after cache; None-safe; error-swallowing.
  - End-to-end race recovery (handshake-then-device-connect sequence).

## Verification artifacts

```
$ .venv/bin/python -m pytest -q
141 passed in 2.83s

$ .venv/bin/ruff check .
All checks passed!
```

**Live-hardware verification (2026-05-10):** AIPI-Lite hardware, wireless, bridge restarted with device intentionally powered off to force the race.

```
22:25:00.212  config.loaded                ← bridge start
22:25:00.221  udp.listening                ← UDP audio port bound
22:25:00.224  handshake.send + connect.holdspeak.handshake.ok  ← HoldSpeak handshook
22:25:00.224  update_screen.skip  reason="service not cached"  ← the bug: silent no-op
                                                                because device offline
22:25:30.222  connect.device.error  ResolveTimeoutAPIError     ← device wasn't on yet
                                    [80 second gap]
22:26:20.536  connect.device.ok            ← user powered the device on
22:26:20.680  update_link.ok  state="[OK]"  ← AIPI-4-08 REPUBLISH FIRED 🎯
22:26:20.680  subscribe.voice_assistant.ok
```

The `update_link.ok state="[OK]"` paint at 22:26:20.680 is the load-bearing evidence: that paint would not have fired on pre-AIPI-4-08 code. User confirmed the LCD showed `HOLD [OK] Ready` after the bridge re-paint landed.

Bonus voice-typing verifications followed at 22:26:39 and 22:26:58 — transcripts `"Find out if everything's alright!"` and `"I want to talk to this device."` both arrived from HoldSpeak's status frames; confirms the audio/transcription path didn't regress from the link-fix code changes.

## Acceptance criteria — re-checked

All 6 brackets checked — see [`story-08-link-state-retrigger.md`](./story-08-link-state-retrigger.md).

## Deviations from plan

- None. Implementation matched the story's design (late-bound callback, idempotent republish, fail-soft on handler errors).

## Follow-ups

- **Republish on subsequent reconnects.** Currently fires only on the first `on_device_ready` call. If the device disconnects mid-session and reconnects, `_on_connect` runs again → `on_device_ready` fires again → republish fires again. So actually it already self-heals on subsequent reconnects. No follow-up needed unless field experience says otherwise.
- The 30-second `ResolveTimeoutAPIError` on each `connect.device.error` retry adds up if the device stays off for a long time. Not new behavior — pre-existing aioesphomeapi default. Not in scope here.

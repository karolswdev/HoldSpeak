# HS-17-05 — Periodic Recording-Tick Status Emitter

- **Project:** holdspeak
- **Phase:** 17
- **Status:** done
- **Depends on:** HS-14-07 (status pushback substrate)
- **Unblocks:** HS-17-06 (meeting title display extends this story's payload)
- **Owner:** unassigned

## Problem

HS-14-07 spec'd `"Recording 00:00 updated each minute"` as one of the canonical status frames pushed to attached AIPI-Lite devices. In practice (verified live 2026-05-10 against AIPI-Lite hardware in meeting `fa195fba`, duration 2:16) **only ONE Recording status frame fires** — at meeting start. No subsequent ticks observed during 2+ minutes of recording. Bookmark frames correctly carry their meeting-relative timestamps (server knows the clock), so it's specifically the periodic-status emitter that's missing.

Symptom: AIPI-Lite LCD shows `Recording 00:00` for the entire meeting duration, never updating. User can't tell from the device whether they're 30s or 30min into a meeting — UX-confusing.

User feedback 2026-05-10: "Shouldn't we refresh the recording status every 5 seconds? Or would that overload something about our process?" Analysis: 5s cadence = 12 calls/min, each ~10-50ms LAN roundtrip via cached service handle = trivially within budget. **5s is safe.** Follow-up device UX work later moved the default to 1s after LCD flash content got its own device-side zone.

## Scope

### In

- Implement (or fix) the periodic Recording-tick emitter in HoldSpeak's status-push code path (`holdspeak/device_audio_ws.py` or wherever the per-meeting-event status pushes are wired).
- **Cadence: current default every 1 second** (initially shipped at 5 seconds; tightened after AIPI-side LCD layout changes). Gives user a usable live timer without overloading the API.
- Format: `Recording M:SS` (e.g., `Recording 02:16`) to fit the LCD's ~24-char width.
- Ticker starts when a meeting starts with attached device(s); stops on meeting stop (handed off to HS-14-07's existing `Saving meeting...` status).
- Update `docs/DEVICE_PROTOCOL.md` to reflect the 5s cadence (was "each minute").

### Out

- Per-device customization of cadence (single global setting for v1).
- Sub-second ticks (overkill).
- Recording status plus other meeting metadata (HS-17-06 handles enrichment).

## Acceptance Criteria

- [x] Periodic Recording-tick fires on the configured interval during an active meeting with at least one attached device — `holdspeak/device_recording_tick.py` (`RecordingTicker` class with daemon thread, `next_tick_at += interval` cadence alignment so it doesn't drift). Current default is 1s.
- [x] Each tick is a status frame with `type: "status", text: "Recording MM:SS", ttl_ms: 0` — verified live, format `Recording 00:05`, `Recording 00:10`, `Recording 00:15`.
- [x] Ticker stops cleanly on meeting stop — `recording_ticker.stop()` called in `_stop_active_meeting` before the `Saving meeting...` broadcast.
- [x] Unit tests: 19 cases in `tests/unit/test_device_recording_tick.py` covering format helper (parametrized over 11 elapsed values), lifecycle (start with no devices, stop before start), periodic firing, stop signalling, restart-after-stop, replace-while-running, sender-exception-survival, cadence-alignment-no-drift.
- [x] `docs/DEVICE_PROTOCOL.md` updated — new Recording-tick row + paragraph documenting cadence + cap.
- [x] Live verification (2026-05-10, against AIPI-Lite hardware): 3 ticks at exactly 5.000-second intervals over an 18-second meeting; `Recording 00:00 → 00:05 → 00:10 → 00:15 → Saving meeting...`. Drift across 3 ticks: 1 ms cumulative.

## Test Plan

- **Unit:** ticker state machine + cadence with mocked clock.
- **Integration:** `tests/integration/test_device_recording_tick.py` — fake WS records all status frames over a 12s simulated meeting; assert ≥ 2 Recording ticks at expected cadence; ticker stops on meeting stop.
- **Manual (with AIPI-Lite hardware):** observe LCD during a real meeting.

## Notes

- HS-14-07's status emitter call sites are listed in `docs/PLAN_AIPI_LITE_DEVICES.md` (or sibling) under "Status emitter call sites". The Recording-tick should fire on a meeting-attached timer (asyncio task), not per-segment.
- 5s cadence picked based on AIPI-Lite user feedback 2026-05-10; matches typical meeting-app UX timing.
- Source of meeting clock: `MeetingState.started_at` minus `time.time()` gives the elapsed seconds for the format string.

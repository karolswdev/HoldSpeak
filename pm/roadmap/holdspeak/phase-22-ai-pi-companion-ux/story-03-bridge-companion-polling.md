# HS-22-03 — Bridge Companion Polling And Display Wiring

- **Project:** holdspeak
- **Phase:** 22
- **Status:** done
- **Depends on:** HS-22-01, HS-22-02
- **Unblocks:** HS-22-04
- **Owner:** unassigned

## Problem

HoldSpeak exposes `/api/companion/status`, and AI PI has an LCD middle zone, but
the unified bridge did not yet poll companion status or paint waiting-agent
state on the device. Claude/Codex could be waiting while AI PI still looked idle.

## Scope

### In

- Poll `/api/companion/status` from the AIPI bridge.
- Adapt companion status payloads into the HS-22 state model.
- Paint fresh waiting-agent questions into the LCD middle zone.
- Clear agent-owned middle text when the agent is no longer waiting.
- Keep existing WebSocket status/transcript LCD behavior intact.

### Out

- Gesture behavior changes.
- Firmware changes.
- Browser companion UI.
- Live voice-reply dogfood.

## Acceptance Criteria

- [x] Bridge polls `/api/companion/status` on a configurable cadence.
- [x] Agent waiting payloads become `CompanionSignals` and `LcdPlan` state.
- [x] Fresh Claude/Codex questions paint to the middle LCD zone.
- [x] Poller clears only agent text it previously painted, avoiding transcript flash clobber.
- [x] Device reconnect forces active agent state to repaint after LCD services are cached.
- [x] Focused tests cover payload adaptation, stale age, paint dedupe, clear, and forced repaint.

## Test Plan

- Focused AIPI tests:
  - `tests/test_companion_status.py`
  - `tests/test_companion_state.py`
  - `tests/test_companion_gestures.py`
  - `tests/test_settings.py`
- Full AIPI suite through `scripts/aipi_test.sh -q`.
- Bridge hardware preflight with a running HoldSpeak web runtime.

## Notes

- Implementation: `aipi-lite/bridge/companion_status.py`.
- Wiring: `aipi-lite/bridge/cli.py`.
- Config: `COMPANION_POLL_INTERVAL_S`, default `2`.
- This story intentionally does not remap gestures yet; HS-22-04 owns live
  agent voice-reply dogfood.

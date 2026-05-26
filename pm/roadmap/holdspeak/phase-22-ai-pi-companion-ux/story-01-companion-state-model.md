# HS-22-01 — Companion State Model And LCD Priority Contract

- **Project:** holdspeak
- **Phase:** 22
- **Status:** done
- **Depends on:** HS-20 companion server contract, HS-21 unified AIPI workflow
- **Unblocks:** HS-22-02, HS-22-03
- **Owner:** unassigned

## Problem

AI PI can receive HoldSpeak status frames and HoldSpeak can expose companion
readiness, but the device still lacks a product-level state model. Without that
model, meeting recording ticks, transcript flashes, agent-waiting questions,
link state, and errors can compete for the same tiny LCD.

## Scope

### In

- Define companion states:
  - disconnected;
  - idle/connected;
  - meeting recording;
  - agent waiting;
  - reply capture;
  - transcribing/rewrite pending;
  - error/busy;
  - stale/cleared.
- Define LCD zones and priority rules for each state.
- Define sticky vs flash vs cycle behavior and TTL/stale clearing.
- Identify which state is bridge-owned, firmware-owned, and HoldSpeak-owned.
- Add tests for pure state-priority formatting logic if code is introduced.

### Out

- Firmware gesture implementation.
- New wire frames.
- Live hardware dogfood.
- Browser companion panel.

## Acceptance Criteria

- [x] State model table exists with owner, trigger, display, and clear condition.
- [x] LCD priority rules cover meeting, agent, reply, transcript, link, and error states.
- [x] The contract explicitly handles stale captured agent questions.
- [x] Follow-up stories can implement bridge polling/display without redesigning state names.

## Test Plan

- Documentation review against current `aipi-lite/bridge/lcd.py`,
  `aipi-lite/bridge/device.py`, and HoldSpeak `/api/companion/status`.
- If logic lands, focused AIPI tests through `scripts/aipi_test.sh`.

## Notes

- This is intentionally the first Phase 22 story. We should not wire gestures
  until the display priority model is explicit.
- Contract draft: [companion-state-model.md](./companion-state-model.md).
- Bridge-side pure model: `aipi-lite/bridge/companion_state.py`.
- Evidence: [evidence-story-01.md](./evidence-story-01.md).

# HS-22-02 — Gesture Contract For Agent And Meeting Actions

- **Project:** holdspeak
- **Phase:** 22
- **Status:** done
- **Depends on:** HS-22-01 companion state model
- **Unblocks:** HS-22-03, HS-22-04
- **Owner:** unassigned

## Problem

AI PI already has useful device gestures, but Phase 22 adds agent-reply
behavior. Without a crisp gesture contract, the same physical button can mean
bookmark, last transcript, meeting-stat cycle, stale clear, or answer agent
depending on context. That ambiguity is the fastest way to make the device feel
untrustworthy.

## Scope

### In

- Define the primary gesture for answering a waiting Claude/Codex question.
- Define how existing meeting gestures behave while an agent is waiting.
- Define stale-question clear behavior.
- Define remote simulation names needed for bridge tests and hardware dogfood.
- Identify firmware-owned vs bridge-owned gesture decisions.

### Out

- Firmware implementation.
- Bridge companion polling.
- Live dogfood proof.
- New HoldSpeak server endpoints.

## Acceptance Criteria

- [x] Gesture table covers idle, meeting, agent waiting, reply capture, stale, and error/busy states.
- [x] Existing bookmark and meeting-cycle gestures retain deterministic behavior.
- [x] Agent reply gesture requires explicit user action and never sends autonomous replies.
- [x] Stale agent context has an explicit non-reply clear behavior.
- [x] HS-22-03 can implement bridge behavior without redefining gesture names.

## Test Plan

- Documentation review against `aipi-lite/bridge/device.py` current left-button and voice-assistant behavior.
- If remote simulation names or bridge helpers are introduced, focused AIPI tests through `scripts/aipi_test.sh`.

## Notes

- State names must come from [companion-state-model.md](./companion-state-model.md).
- Current device gestures to preserve:
  - left single tap during meeting emits bookmark (`long_press` wire event);
  - left single tap outside meeting queries `last_segment`;
  - left double tap during meeting emits `double_left_click`;
  - right-button voice assistant controls start/stop capture in firmware.
- Contract: [gesture-contract.md](./gesture-contract.md).
- Bridge-side pure model: `aipi-lite/bridge/companion_gestures.py`.
- Evidence: [evidence-story-02.md](./evidence-story-02.md).

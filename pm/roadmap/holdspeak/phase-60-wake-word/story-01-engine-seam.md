# HS-60-01 — The engine seam + config

- **Project:** holdspeak
- **Phase:** 60
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-60-02, HS-60-04
- **Owner:** unassigned

## Problem
There is no wake engine, no config for one, and CI must never depend on
the optional engine being installed.

## Scope
- **In:** `holdspeak/wake_word.py`: `WakeWordListener` with an injectable
  detector (`predict(frame_int16) -> score`) and frame source, detection
  at threshold with a refractory cooldown, idempotent pause/resume, a
  clean stop; the real openwakeword detector behind lazy imports +
  `wake_word_available()`; `download_wake_models()` (the explicit egress
  moment). `WakeWordConfig(enabled=False, model="hey_jarvis",
  threshold=0.5, armed_window_seconds=8.0, action="preview")` on
  `Config`; settings-route validation (threshold 0..1, action
  preview|type, window 2..30, non-empty model). `[wakeword]` extra in
  pyproject.
- **Out:** audio streams, the runtime loop, UX (HS-60-02/03).

## Acceptance criteria
- [ ] A fake detector + frame source drive detection, threshold edges,
      the refractory cooldown (no double-arm), pause/resume idempotence,
      and stop — with openwakeword absent.
- [ ] `wake_word_available()` is False-and-harmless without the extra;
      the real detector path imports lazily.
- [ ] Config round-trips with older-shape coercion; malformed values
      refuse with clean 400s at the settings boundary.
- [ ] The `[wakeword]` extra resolves (openwakeword + onnxruntime).

## Test plan
- Unit with fakes; settings-boundary integration; full suite (no extra
  in CI).

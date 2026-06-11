# HS-60-01 — The engine seam + config

- **Project:** holdspeak
- **Phase:** 60
- **Status:** done
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
- [x] A fake detector + frame source drive detection, threshold edges,
      the refractory cooldown (no double-arm; fire-again after), pause
      drains-never-scores, resume resets AND re-arms the cooldown,
      idempotence, stop, and exploding-observer survival — 15 tests, no
      engine import anywhere (locked).
- [x] `wake_word_available()` is False-and-harmless without the extra;
      the engine imports lazily (top-level-import lock).
- [x] Config round-trips with older-shape coercion and tolerant
      file-edit normalization; five malformed shapes refuse with clean
      400s that change nothing.
- [x] The `[wakeword]` extra ships and resolves (openwakeword ≥0.6 +
      onnxruntime; verified at scaffold on this machine).
      See `evidence-story-01.md`.

## Test plan
- Unit with fakes; settings-boundary integration; full suite (no extra
  in CI).

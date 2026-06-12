# Evidence — HS-60-01: The engine seam + config

**Date:** 2026-06-11
**Branch:** `phase-60-wake-word`

## 1. What shipped

- **`holdspeak/wake_word.py`**: `WakeWordListener` — a fully injectable
  detection loop (detector protocol + frame-source callable + clock), with
  the safety behaviors the phase conditions demand built in: detection at
  the threshold fires once and resets the detector; the **refractory
  cooldown** blocks the double-arm (openWakeWord scores stay hot for
  frames after a hit); **pause drains frames without scoring** (the audio
  source never backs up) and **resume resets the detector AND re-arms the
  cooldown** so stale buffered audio can never fire; an exploding
  `on_detect` never kills the loop; `start/stop` own a daemon thread,
  idempotently. The real engine (`OpenWakeWordDetector`, ONNX, one model
  one score, float32→int16 conversion at the boundary) hides behind lazy
  imports with `wake_word_available()`; `download_wake_models()` is THE
  one network moment, documented as such in its docstring.
- **`WakeWordConfig`** on `Config`: `enabled=False, model="hey_jarvis",
  threshold=0.5, armed_window_seconds=8.0, action="preview"`. File-edited
  values normalize tolerantly in `__post_init__` (clamps, action
  whitelist); the **settings route validates strictly** (action
  preview|type, threshold 0..1, window 2..30, non-empty model — clean
  400s, and a bad write changes nothing).
- **`[wakeword]` extra** in pyproject (openwakeword ≥0.6, pulling
  onnxruntime), resolved on this machine at scaffold.

## 2. Tests

`tests/unit/test_wake_word.py` — 15 tests, **all running with no engine
import**: threshold edges, the refractory double-arm block, fire-again
after cooldown, pause-drains-never-scores, resume-resets-and-rearms,
idempotent pause/resume, source-close ends the loop, start/stop join,
exploding-observer survival, the lazy-import lock (no top-level
openwakeword), config defaults-off + tolerant normalization + older-shape
coercion. `tests/integration/test_settings_wake_word.py` — 7 tests:
round-trip, the exact defaults shape, five strict refusals.

```
$ uv run pytest -q tests/unit/test_wake_word.py
15 passed
$ uv run pytest -q tests/integration/test_settings_wake_word.py
7 passed
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2705 passed, 17 skipped
```

(2683 → 2705: +22.) CI carries no `[wakeword]` extra and stays green by
construction.

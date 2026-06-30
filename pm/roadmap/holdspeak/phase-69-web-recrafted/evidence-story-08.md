# Evidence — HS-69-08: Reactive mic waveform

**Date:** 2026-06-30
**Verdict:** done. The cockpit gains a floating perceptual mic meter that reacts
to the server's additive `audio_level` frame during capture — proven on the
backend (the throttled broadcast) and the frontend (the canvas reacting + the
idle auto-hide).

## What shipped — backend (the additive frame)

The recorders already computed a 0..1 level per chunk; the callbacks were
discarded by stub lambdas. This wires them to a throttled broadcaster:

- **`holdspeak/web_runtime.py`** — `_emit_audio_level(level, source)`: guards on
  `self.server`, throttles to ~15 Hz (`time.monotonic`), clamps 0..1, and
  `self.server.broadcast("audio_level", {"level", "source"})` — so the wire frame
  is `{"type":"audio_level","data":{"level":…,"source":…}}` (the standard `data`
  envelope). Never raises (runs on the audio thread).
- The dictation recorder stub `on_level=lambda _level: None` →
  `on_level=lambda level: self._emit_audio_level(level, "dictation")`.
- **`holdspeak/runtime/meeting_glue.py`** — the meeting `on_mic_level` /
  `on_system_level` stubs → broadcast `"meeting_mic"` / `"meeting_system"`.

No new RMS math: the existing `AudioRecorder.on_level` / `MeetingSession` levels
are reused.

## What shipped — frontend (the meter)

- **`web/src/scripts/waveform.js`** — subscribes to `audio_level` on the shared
  runtime-bus; a rolling `Float32Array(48)` history rendered on a canvas via rAF:
  gamma-expanded (perceptual) mirrored bars, older bars dimmer, an accent radial
  peak glow on the loudest recent bar; settles flat + hides after ~700 ms of
  silence. Exposes `window.__hsWaveformLevel` for proof harnesses (no socket).
- **`web/src/components/Waveform.astro`** — a floating Signal-surface meter
  (`signal-card` + a mic glyph + the canvas), mounted in `AppLayout` so it rides
  every route; bottom-centre (Queue HUD is top-centre, Qlippy bottom-right — no
  collision); hidden at rest, reveals on `.is-active`.

## Proof

- **`screenshots/waveform-active.png`** — the meter floating over `/history`,
  revealed, the canvas full of reactive bars driven by a simulated speech
  envelope (`scripts/screenshot_phase69_waveform.py` pumps levels through the
  same entry the WS frame drives).
- **`screenshots/waveform-meter.png`** — the cropped meter: the accent mic glyph
  + the gamma-expanded mirrored bars with the peak glow.
- **Idle auto-hide** confirmed by the script (`still active after silence: False`).
- **Tests:** `tests/unit/test_audio_level_frame.py` (broadcast shape, throttle,
  clamp, no-server guard) + `test_web_runtime` + density guard + route pre-flight
  = **24 passed**. Build green.

## Honest note

The end-to-end with a real microphone is not exercised here (the mic-bound metal
test is excluded from the suite). The level math is the recorders' existing,
already-shipped computation; this story only throttles + broadcasts + visualizes
it, all of which are proven above.

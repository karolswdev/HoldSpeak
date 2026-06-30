# HS-69-08 — Reactive mic waveform

- **Status:** done
- **Priority:** MED
- **Depends on:** the additive server `audio_level` frame (built here)
- **Catalog pattern(s):** §7 waveform
- **Evidence:** [evidence-story-08.md](./evidence-story-08.md)

## Goal

A perceptual mic level meter on the cockpit that reacts during capture — the web
port of the iPad's gamma-expanded waveform (per-bar history, accent peak glow),
leaping on speech and flat on silence.

## Scope

- Per the Phase-69 carried-in decision, the SOURCE is a small **additive server
  `audio_level` WS frame**, never a new in-browser mic surface.
- Backend: the recorders already compute a 0..1 level per chunk (the callbacks
  were discarded by stub lambdas); a throttled `_emit_audio_level` broadcasts it.
- Frontend: a floating meter (canvas) that subscribes to `audio_level` on the
  shared runtime-bus and renders the bars; reveals on capture, hides on silence.

## Proof required

`audio_level` frame emitted (throttled, clamped); the meter's envelope leaps on
speech and settles flat on silence; accent peak glow.

## Done

Shipped and proven both ends. Backend: `_emit_audio_level` broadcasts
`{"type":"audio_level","data":{level,source}}` throttled to ~15 Hz and clamped
0..1, wired into the dictation recorder + both meeting channels (4 unit tests).
Frontend: a floating Signal meter (`Waveform.astro` + `waveform.js`) mounted in
AppLayout, reacting to the frame with gamma-expanded bars + a peak glow, hiding
after silence — screenshot-proven (`waveform-active.png`, `waveform-meter.png`),
the idle auto-hide confirmed. 24 passed across the audio/web_runtime/density/
pre-flight slices.

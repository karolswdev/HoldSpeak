# AIPI-5-02 — VAD-Driven Session End

- **Project:** aipi-lite
- **Phase:** 5
- **Status:** backlog
- **Depends on:** AIPI-5-01 (wake-word integration provides the session-trigger; VAD provides the session-end)
- **Unblocks:** AIPI-5-03
- **Owner:** karol

## Problem

With wake-word triggering sessions (AIPI-5-01), button-release no longer marks "stop." The session must end automatically when the user stops talking. ESPHome's `voice_assistant` integration supports `silence_detection`; this story wires it, tunes thresholds, and adds a max-duration cap to prevent runaway sessions.

## Scope

### In

- Enable `silence_detection: true` on `voice_assistant` in `aipi.yaml` (or whatever the equivalent ESPHome configuration key is; verify against current ESPHome version).
- Tune silence-detection threshold + duration via a 10-utterance hardware test. Default target: ~1.5 s of detected silence ends the session.
- On VAD-detected end, firmware fires `voice_assistant.on_end` → bridge already maps to `StopFrame` (no bridge code change for the end path).
- Maximum session duration cap (default 30 s) via ESPHome `script` + `delay` to prevent runaway sessions (e.g., wake-word fires from a TV in the background; nobody actually starts speaking; we don't want to send 5 min of TV audio to HoldSpeak).
- LCD flash on VAD-end: `Saving  ...` (existing symbol map from AIPI-2-07) for 1.5 s.
- Coexistence with button-press mode: VAD-end *only* applies when the session was started by wake-word (not by button-hold). Button-hold sessions keep button-release as their end signal. (Or: configurable — story-03 owns the cleaner toggle; this story may temporarily use a global, finalised in 5-03.)

### Out

- VAD threshold UI on the device (no LCD-side knob; threshold is a YAML config value in v1).
- VAD also during meetings — meetings keep streaming continuously.
- Adaptive VAD threshold (learned from environment noise floor) — out of scope; static threshold for v1.
- VAD on the bridge side (using the audio stream) — keep it on the device for latency + simplicity.

## Acceptance criteria

- [ ] `aipi.yaml` enables `silence_detection` on `voice_assistant`; threshold + duration set; values documented in YAML comments + story notes.
- [ ] 10-utterance tuning test: speak 10 utterances of varied length; record VAD-end accuracy (premature ends + late ends); pick threshold that minimizes both.
- [ ] Max session duration cap enforced (default 30 s via firmware-side `script` + `delay`).
- [ ] LCD flashes `Saving  ...` for 1.5 s on VAD-end.
- [ ] Coexistence: button-hold session uses button-release as end-signal; wake-word session uses VAD as end-signal. Verified live.
- [ ] Live verification: wake → speak → fall silent → session ends within ~1.5 s of silence; transcript types into focused app.
- [ ] Edge case verified: speak past max-duration → session forcibly ends at cap; transcript covers what was captured up to that point.

## Test plan

- **Unit:** none (firmware territory).
- **Manual (hardware):**
  1. 10-utterance tuning: vary speech-pause patterns (short utterance, long utterance, slow speaker, fast speaker, mid-sentence pause).
  2. Edge: speak continuously past the max-duration cap; verify session ends; transcript matches captured audio.
  3. Coexistence: alternately use button-hold and wake-word in the same session; verify each end-signal works for the corresponding start.

## Notes

- **Tuning is empirical.** Threshold values that work for one user/environment may not for another. Story should record the chosen value + the reasoning + a note on how to tune for a different environment.
- **ESPHome's `voice_assistant` config keys** vary slightly across versions; verify against the version pinned in this build before writing acceptance.
- **Why not VAD on the bridge side:** keeping VAD on-device means the device controls its own session lifecycle and sends `StopFrame` immediately. Bridge-side VAD would add network-roundtrip latency to the silence-detection decision — measurable user-visible lag.
- **Mid-sentence pause failure mode:** if the user pauses mid-thought for > 1.5 s, the session ends prematurely. A more sophisticated VAD would require a longer threshold or speech-recognition-based segmentation. For v1: accept the failure mode; users can re-wake to continue.
- **TV / background-audio false-trigger** is the main failure scenario for the max-duration cap. Wake-word from a TV → ~30 s of TV audio gets typed somewhere weird. Cap mitigates damage; doesn't eliminate it.

# HS-60-02 — Arm, capture, and the pipeline

- **Project:** holdspeak
- **Phase:** 60
- **Status:** done
- **Depends on:** HS-60-01
- **Unblocks:** HS-60-03, HS-60-06
- **Owner:** unassigned

## Problem
A detection must become a visible armed window, a captured utterance, and
a normal pipeline run whose default outcome is a preview, never typing.

## Scope
- **In:** web_runtime lifecycle (config-gated start; live start/stop on
  settings-applied; clean shutdown); on detect → `runtime_activity`
  state `armed` + a `wake_armed` broadcast (window seconds) → energy-VAD
  capture (begin on speech within the window, end on ~1.2 s silence or
  a 15 s cap, abandon silently when nothing is spoken) → the normal
  dictation pipeline. `action="preview"`: journal (source `wake`) +
  `wake_preview` broadcast carrying the result + a server-stored
  one-shot preview token — NEVER typed. `action="type"`: typed exactly
  like a hotkey run. The listener pauses during hold-to-talk recording
  and meeting capture, resumes after.
- **Out:** the UI surfaces (HS-60-03).

## Acceptance criteria
- [x] With fakes end to end: detect → armed activity + `wake_armed`
      broadcast → captured speech → the normal pipeline
      (`journal_source="wake"`) → preview broadcast with a one-shot
      burned-on-use token, and the typing spy verifiably empty; with
      `action="type"` the typing seam IS invoked with the pipeline
      result.
- [x] No speech in the window → silent disarm (the wake_disarmed
      activity only; the hand-off provably not called).
- [x] The floor model is the pause seam: a held floor silently blocks
      arming (tested), and the frame source self-heals pause/resume
      against `voice_session.active_owner` every read (the pause
      semantics themselves are HS-60-01-tested).
- [x] Disabled config → no listener construction (tested); the listener
      is also stopped in the shutdown finally and live-synced on
      settings-applied. See `evidence-story-02.md`.

## Test plan
- Unit/integration with fake listener + recorder + pipeline; full suite.

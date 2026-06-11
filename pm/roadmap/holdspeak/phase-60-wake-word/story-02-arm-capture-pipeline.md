# HS-60-02 — Arm, capture, and the pipeline

- **Project:** holdspeak
- **Phase:** 60
- **Status:** backlog
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
- [ ] With fakes end to end: detect → armed broadcast → captured speech
      → pipeline → preview journaled + broadcast, and the typing seam
      verifiably NOT invoked; with `action="type"` the typing seam IS
      invoked with the pipeline result.
- [ ] No speech in the window → silent disarm (no journal, no broadcast
      beyond the disarm).
- [ ] Hold-to-talk and meeting capture pause/resume the listener
      (tested at the seam).
- [ ] Disabled config → no listener construction (byte-identical lock).

## Test plan
- Unit/integration with fake listener + recorder + pipeline; full suite.

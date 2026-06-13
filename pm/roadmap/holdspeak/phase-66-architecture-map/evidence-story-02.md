# Evidence — HS-66-02: The dictation pipeline, diagrammed

**Date:** 2026-06-13
**Verdict:** done. The dictation section of `docs/ARCHITECTURE.md` carries
three diagrams, each traced against the shipped code and rendered.

## What shipped (three Mermaid diagrams)

1. **The end-to-end dictation flow.** The three entries (hotkey, wake word
   into the armed window, device audio over WebSocket) → capture →
   transcribe (local Whisper) → punctuation + spoken symbols → the
   voice-command branch (match → fire the bounded connector; no match →
   the pipeline) → the opt-in stages **in their real order and names**
   (`intent-router`, `project-rewriter`, `kb-enricher`, with the note that
   project-rewriter calls the LLM) → the wake preview-default fork (hotkey/
   device type directly; wake previews until you tap Type it) → type →
   journal. Off-by-default and opt-in paths are marked as such.
2. **The learning loop.** Run → journal (said/typed/route/latency) →
   review → one-tap correction → correction memory → nudges future
   routing; plus replay re-running an utterance through the updated
   pipeline. Module names on the stores (`db/journal.py`,
   `db/corrections.py`).
3. **The device path** (sequence diagram). The ESP32-S3 board on the same
   LAN streams 16 kHz frames over the device WebSocket; if a coding agent
   is awaiting a reply, the text goes into that session, else the focused
   app. This is the honest version of the launch-kit's "speak to a $30
   gadget" claim.

## Accuracy

Traced against `dictation_runner.py` (the stage list and order,
`run_dictation_pipeline`, `dispatch_voice_command`), `config.py`
(`_KNOWN_DICTATION_STAGES`, pipeline off by default), `wake_glue.py` (the
preview default), and `device_audio_ws.py`. No stale module names; opt-in
paths shown as opt-in.

## Proof

- Render guard green (4 blocks now); the dictation flow rendered to PNG
  and reviewed by eye (the branches read correctly).
- Voice guard green (13); full suite unaffected (docs-only; the guard
  already counted at HS-66-01).

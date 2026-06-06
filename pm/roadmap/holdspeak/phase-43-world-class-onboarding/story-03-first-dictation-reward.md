# HS-43-03 — First-dictation reward + Done

- **Project:** holdspeak
- **Phase:** 43
- **Status:** done (2026-06-06)
- **Depends on:** HS-43-01

## Problem
The first-dictation step is the emotional peak and is currently a placeholder. It
must feel like a genuine **reward** when text lands.

## Scope
- In: a live "hold your key and speak" target with a mic-activity ring fed by the
  `runtime_activity` WS (listening/transcribing/typing), and on success a real
  celebration — the ring resolves to a checkmark, the transcript types out, an
  accent burst — reduced-motion safe; sets/reflects the `first_run` milestone.
- Out: changing the dictation pipeline.

## Acceptance criteria
- [x] The step shows live dictation state (mic ripple + the actual hotkey) + a
      celebratory success with the transcript; reduced-motion safe; covered by a
      live WS Playwright capture + a source test.

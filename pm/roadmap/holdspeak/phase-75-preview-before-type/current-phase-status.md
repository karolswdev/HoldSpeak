# Phase 75 — Preview Before It Types (backlog candidate M)

**Status:** open — scaffolded 2026-07-02 (0/5).
**Owner call that opened it:** "Let's keep going" with the owner unable to
test; candidate M is the last live backlog row (owner-sourced, parked not
rejected) and is fully provable headless.

## Why

Dictation types the instant the pipeline finishes. Phase 60 built the
safer grammar for wake-word one-shots (arms-not-types: a one-shot preview
token + a Type-it consume) and the owner's original M framing asks for
exactly that on ordinary hold-key dictation: see it before it types,
commit or discard. Opt-in, default OFF — the current behavior stays
byte-identical.

## The seam (verified before scaffolding)

- `holdspeak/runtime/dictation_capture.py::_transcribe_and_type` is the
  ONE place ordinary dictation reaches `typer.type_text`.
- `holdspeak/runtime/wake_glue.py` holds the P60 pattern to generalize:
  one active preview at a time, a one-shot token store
  (`consume_wake_preview` burns it), a broadcast frame, journaling intact.
- `/api/dictation/wake/type` is the consume-route precedent.

## Stories

| ID | Story | Sev | Status | Depends |
|---|---|---|---|---|
| HS-75-01 | The hub fork: arm, don't type (opt-in) | HIGH | **done** (knob default-off locked byte-identical; one one-shot preview; routes on the wake contract; agent replies immediate; milestone on delivery; 7/7; see [evidence](./evidence-story-01.md)) | — |
| HS-75-02 | Type it / Discard on the cockpit and the desk | HIGH | todo | 01 |
| HS-75-03 | The settings knob (cockpit config) | MED | todo | 01 |
| HS-75-04 | Docs: the preview story | MED | todo | 01–03 |
| HS-75-05 | Closeout: the preview walk | HIGH | todo | 01–04 |

## Exit criteria

- [x] With the knob OFF (default), dictation behavior is byte-identical —
      locked by test, not by claim (HS-75-01).
- [x] With the knob ON, a finished dictation journals normally, arms ONE
      one-shot preview (token + `dictation_preview` broadcast), and types
      NOTHING until `/api/dictation/preview/type` consumes it; discard
      burns it (HS-75-01).
- [ ] Type it / Discard render on the dictation cockpit AND the desk
      front door (the one bus; no modal, no prose) (HS-75-02).
- [ ] The knob lives in the cockpit's settings with honest copy
      (HS-75-03).
- [ ] Entry-point docs speak the mode (HS-75-04).
- [ ] The preview walk: a real pipeline pass with a capturing typer —
      nothing typed while armed, Type-it delivers the exact text, discard
      delivers nothing (HS-75-05; the mic-in-hand pass is the owner's
      real-metal leg, recorded).

## Where we are

**2026-07-02 — HS-75-01 done (1/5).** The hub fork is in: the knob
(default off, locked byte-identical), the one-shot arm with the
broadcast, the consume/discard verbs on the wake security contract, the
agent-reply exclusion, and the milestone-on-delivery rule — 7/7 on the
real mixin methods. Next: the surfaces (HS-75-02).

**2026-07-02 — scaffolded (0/5).** Seam verified; the P60 pattern
generalizes without new architecture.

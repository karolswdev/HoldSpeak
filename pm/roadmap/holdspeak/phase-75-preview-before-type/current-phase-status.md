# Phase 75 — Preview Before It Types (backlog candidate M)

**Status:** **CLOSED — 5/5 (2026-07-02).** See [final-summary.md](./final-summary.md).
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
| HS-75-02 | Type it / Discard on the cockpit and the desk | HIGH | **done** (ONE shell surface on every route — the QueueHud idiom; keyboard-first; proven on / and /dictation with real broadcasts; see [evidence](./evidence-story-02.md)) | 01 |
| HS-75-03 | The settings knob (cockpit config) | MED | **done** (cockpit toggle + boundary + the loader fix the round-trip test caught — the knob would have reverted every restart; see [evidence](./evidence-story-03.md)) | 01 |
| HS-75-04 | Docs: the preview story | MED | **done** (GETTING_STARTED + DICTATION_COPILOT; guards 85 green; see [evidence](./evidence-story-04.md)) | 01–03 |
| HS-75-05 | Closeout: the preview walk | HIGH | **done** (real verbs behind the routes + a capturing typer: armed→Type it→exact text; discard→nothing; see [evidence](./evidence-story-05.md)) | 01–04 |

## Exit criteria

- [x] With the knob OFF (default), dictation behavior is byte-identical —
      locked by test, not by claim (HS-75-01).
- [x] With the knob ON, a finished dictation journals normally, arms ONE
      one-shot preview (token + `dictation_preview` broadcast), and types
      NOTHING until `/api/dictation/preview/type` consumes it; discard
      burns it (HS-75-01).
- [x] Type it / Discard render on the dictation cockpit AND the desk
      front door (the one bus; no modal, no prose) (HS-75-02 — one shell
      surface, every route).
- [x] The knob lives in the cockpit's settings with honest copy
      (HS-75-03 — plus the loader fix its round-trip test caught).
- [x] Entry-point docs speak the mode (HS-75-04).
- [x] The preview walk: a real pipeline pass with a capturing typer —
      nothing typed while armed, Type-it delivers the exact text, discard
      delivers nothing (HS-75-05; the mic-in-hand pass is the owner's
      real-metal leg, recorded).

## Where we are

**2026-07-02 — PHASE CLOSED (5/5).** The walk sealed it: real verbs
behind the routes, a capturing typer, nothing typed while armed, the
exact text on commit, nothing on discard. Two real bugs caught by the
phase's own tests (the loader dropping the knob; the manifest guard).
The mic-in-hand pass is the owner's leg.

**2026-07-02 — HS-75-04 done (4/5).** Docs speak the mode. One story
left: the preview walk.

**2026-07-02 — HS-75-03 done (3/5).** The knob is real: the cockpit
toggle, the boundary, and a loader fix the round-trip test caught (the
persisted value was silently dropped on load — the toggle would have
reverted every restart). Next: docs (04) + the walk (05).

**2026-07-02 — HS-75-02 done (2/5).** One shell card covers every route
(the QueueHud idiom) — the desk, the cockpit, everywhere — keyboard-first
with the P60 badge label and honest failure states. Next: the settings
knob (HS-75-03).

**2026-07-02 — HS-75-01 done (1/5).** The hub fork is in: the knob
(default off, locked byte-identical), the one-shot arm with the
broadcast, the consume/discard verbs on the wake security contract, the
agent-reply exclusion, and the milestone-on-delivery rule — 7/7 on the
real mixin methods. Next: the surfaces (HS-75-02).

**2026-07-02 — scaffolded (0/5).** Seam verified; the P60 pattern
generalizes without new architecture.

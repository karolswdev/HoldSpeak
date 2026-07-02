# HS-75-01 — The hub fork

- **Status:** done
- **Severity:**  arm, don't type (opt-in)
- **Depends on:** HIGH:—

## What

(See the phase status doc's exit criteria row for HS-75-01 — the scaffold
keeps the contract there; this file carries the build notes and the Done
record.)

## Test plan

- Story-specific tests per the exit criteria row; the full suite green at
  ship; every proof read, not assumed.

## Done

Shipped. `dictation.preview_before_type` (default off; the off-path
locked byte-identical by test); the fork sits after the pipeline pass so
journaling is intact; one one-shot token at a time, `dictation_preview`
broadcast, `Preview ready` activity, NOTHING typed; agent replies never
preview (the companion flow stays immediate); the milestone marks on
delivery, not on arm; `/api/dictation/preview/type|discard` carry the
wake/type security contract verbatim through new context callbacks. 7/7
on the real mixin methods + the real routes. See
[evidence-story-01.md](./evidence-story-01.md).

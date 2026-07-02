# Evidence — HS-75-05 — Closeout: the preview walk

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-75-preview-before-type`)

## The walk

The REAL runtime verbs behind the routes (`on_preview_type =
rig.type_dictation_preview`, not lambdas), a capturing typer, one browser
session on `/`:

1. A REAL `_transcribe_and_type` pass (stub transcriber, the knob on)
   armed the card — the browser showed EXACTLY the pipeline's text and
   **the typer had received nothing** (asserted); `05-walk-armed.png`.
2. **Type it** → the route → the real consume verb → the typer received
   exactly `"hello from the walk"`; the store empty; the card hid.
3. A second pass armed `"never type this"`; **Discard** burned it — the
   typer never saw it (asserted against the full typed list).
4. `location.pathname` stayed `/`; zero page errors.

The **mic-in-hand pass** (a real hotkey hold + real speech) needs a
microphone runtime and is the owner's real-metal leg, recorded in the
scaffold and the final summary.

## Acceptance criteria — re-checked

- [x] A real pipeline pass; nothing typed while armed; Type-it delivers
      the exact text; discard delivers nothing.
- [x] final-summary.md; the phase closes 5/5; the PR merges on a
      conclusion-checked green.

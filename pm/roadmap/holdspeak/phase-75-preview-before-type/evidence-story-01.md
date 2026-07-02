# Evidence — HS-75-01 — The hub fork: arm, don't type (opt-in)

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-75-preview-before-type`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **The knob**: `dictation.preview_before_type: bool = False` on
  `DictationConfig` — off by default, and the off-path is **locked
  byte-identical by test** (the typer receives immediately; no preview
  state; no broadcast).
- **The fork** (`dictation_capture._transcribe_and_type`): after the
  pipeline pass (journaling intact — the fork sits AFTER
  `_maybe_run_dictation_pipeline`), when the knob is on and the capture
  is not an agent-reply, `_arm_dictation_preview` stores ONE one-shot
  token (`dictation_previews`, cleared first — the P60
  one-active-at-a-time rule), broadcasts
  `dictation_preview {token, text}`, and sets the `Preview ready`
  activity. **Nothing types.** `on_complete` still receives the text
  (the device path shows the transcript).
- **Agent replies never preview**: answering the coder is an explicit,
  targeted act — the companion flow stays immediate (asserted).
- **The verbs**: `consume_dictation_preview` (burn),
  `type_dictation_preview` (consume → the normal typing path + the
  `Typed` activity + first-dictation mark — **the milestone marks on
  DELIVERY, not on arm**), `discard_dictation_preview`.
- **The routes**, mirroring `/api/dictation/wake/type`'s contract
  verbatim (server-minted token only; client text never accepted):
  `POST /api/dictation/preview/type` and `.../preview/discard`, wired
  through new `on_preview_type`/`on_preview_discard` callbacks
  (WebRuntimeCallbacks → WebContext → the runtime methods).

## Verification artifacts

- `tests/unit/test_dictation_preview.py` — **7 passed**, exercising the
  REAL mixin methods on a fake runtime self (the repo's existing
  delegate-test idiom):
  1. **OFF is byte-identical** (types immediately, zero preview state,
     zero broadcast, milestone marked);
  2. ON arms exactly one preview, types NOTHING, broadcasts the frame,
     milestone NOT marked;
  3. Type-it consumes exactly once (the burned token types nothing);
  4. discard burns without typing;
  5. one active preview at a time (the old token dies);
  6. agent-reply sessions never preview;
  7. the route contract (400 no token / 200 typed / 404 burned) against
     the real app.
- API manifest regenerated (the two new routes). Full suite at ship:
  **3087 passed, 37 skipped, 0 failures** (3080 + the 7 new).

## Acceptance criteria — re-checked

- [x] Off = byte-identical, locked by test.
- [x] On = journal + arm one one-shot preview + type nothing until the
      consume route commits; discard burns.
- [x] The wake/type security contract carried over verbatim.

## Deviations from plan

- None of substance; the agent-reply exclusion is a design call recorded
  here (the companion answer flow must stay immediate).

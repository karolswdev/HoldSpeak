# HS-83-01 — Ground this ask, on the web composer

- **Project:** holdspeak
- **Phase:** 83
- **Status:** done — 2026-07-07, see [`evidence-story-01.md`](./evidence-story-01.md).
- **Depends on:** the hub's `grounding` hydration (HSM-15-12, merged #277 —
  `holdspeak/web/routes/primitives/ask.py`, 5 tests in
  `tests/unit/test_web_routes_ask.py`).
- **Unblocks:** HS-83-02 (the chat composer reuses the picker), HS-83-04.

## Problem

Grounded 2026-07-07: the web ask composer
(`web/src/desk/components/AskPanel.tsx`, request built in
`web/src/desk/ask.ts` `runAsk`) sends `{prompt, lens, context, profile_id}` —
context is only the lasso'd cards, whole-card, no expansion, no gauge. The hub
can already hydrate a meeting's transcript, digest, and each bound artifact by
reference and refuse unknown ids by name; the web has no way to say so. The
iPad's owner ask ("select meetings, expand them, include any bound
artifacts... into the context of that q") applies verbatim to the web.

## The design

- **The picker.** A "Ground this ask" affordance on `AskPanel`: meetings listed
  (newest first, `/api/meetings`), each expanding to digest / transcript / its
  bound artifacts, each independently toggleable — the iOS `GroundingPicker`
  semantics, web-native rendering (React island component, desk idiom, no
  modal-scrim novel).
- **The gauge.** Live pricing from REAL fetched lengths (≈4 chars/token, the
  `OnDeviceBudget` estimator); the budget is the picked profile's
  `context_limit`. Past-budget refuses at the gauge.
- **The wire.** The run adds `grounding: {meeting_ids, artifact_ids, expand}`
  to the ask body — refs only; the hub hydrates (the web has no client-side
  hydration branch, by design). `expand = "full"` iff any transcript toggle is
  on.
- **Receipts.** The kept ask's provenance carries the grounding rows exactly as
  the hub folds them into `context_ids/titles`; the printed card shows what
  grounded the answer.
- **Refusals render.** A 400 (`unknown_ids`, bad expand, over the ref cap)
  renders as the honest error it is, naming what the hub named.

## Acceptance criteria

- [x] From the composer: select ≥1 meeting, expand it, toggle transcript and an
      artifact independently; the gauge re-prices live from fetched lengths.
      (Rig-driven; gauge/chip text asserted non-lying.)
- [x] The run's request body carries `grounding` refs; the answer reflects
      hub-hydrated content the request never shipped (control-vs-treatment on
      the live hub → .43). (Rig asserts the captured prompt's hydrated blocks
      vs an ids-only request; the live .43 treatment receipts ride the
      HSM-15-12 story header — the in-browser live beat is HS-83-04's walk.)
- [x] A kept grounded ask's artifact lists the grounding by name.
      (`groundingReceiptRows` join the pinned print context.)
- [x] Unknown ids / over-cap selections render the hub's refusal verbatim.
      (vitest: "grounding ids not on this hub (ghost)".)
- [x] Past-budget refuses at the gauge, before any run. (Ask disabled + the
      warning line; `overBudget` gates `ask()`.)
- [x] Screenshots: the picker open with expansion rows + gauge; a grounded
      printed card. (`screenshots/hs-83-01-*.png`.)

## Test plan

- Vitest on the request builder (refs shape, expand derivation, refusal
  rendering states) — `web/` test suite.
- Hub side already locked (`uv run pytest -q -k ask`).
- Live: control-vs-treatment against the hub on this Mac; screenshots.

## Notes

- Sibling of HSM-15-12; the envelope's block shape and refusal grammar are
  pinned there — this story adds no new wire, only the web's mouth for it.

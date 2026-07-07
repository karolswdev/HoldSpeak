# Evidence — HS-83-03: the models front door

**Date:** 2026-07-07. **Verdict: done.**

## What shipped

- **Hub:** `GET /api/models` — the runnable allow-list, ONE derivation
  (`_runnable_models` in `ask.py`) now shared by the ask route's
  model-override refusal and the new route: the hub's own configured model
  first, then each non-deleted profile's model, deduped by name. No client
  discovers capability by provoking the 400 anymore.
- **Web:** the store loads `/api/models` in the `loadAll` sweep (an older hub
  answers with an honest empty door); the rail grows a MODELS section under
  the personas — every runnable model is a chat you can open. A model chat IS
  an HS-83-02 thread: a synthetic persona (`modelchat:hub:<name>`), turns ride
  `/api/ask` pinned via the `model` override with the conversation packed
  client-side (`packModelTurn` — a model persona has no standing context by
  design; grounding is the thread's), harvest rides `/api/ask/keep`, the
  thread persists device-local under the model id.

## Receipts

- **Hub pytest:** `test_models_route_names_exactly_the_ask_allow_list` — hub
  row first, dedupe across two profiles serving the same model, and SET
  EQUALITY with the ask 400's `allowed_models`. Full sweep **3212 passed**
  (api-surface regenerated: `GET /api/models` + its web consumer — 246
  routes).
- **Vitest:** 57/57 — model-chat id round-trip, `packModelTurn` (no
  role/context; the conversation block), the pinned `/api/ask` wire with
  grounding refs.
- **The rig** (`scripts/screenshot_hs83_models.py`): the rail lists 2 model
  rows (hub row FIRST — asserted), one click opens a chat titled with the
  model, a turn runs pinned (the override resolved to the LAN profile at the
  engine seam) and the reply's badge wears the hub-reported
  `Qwen3.5-9B-Q6_K · 192.168.1.43`.
- **Screenshots:** `hs-83-03-rail-models.png`, `hs-83-03-model-chat.png`.
- The live in-browser beat (real .43 answer through the real bundle) closes
  with HS-83-04's walk; the model override itself was real-metal-proven
  against the live hub in HSM-15-11/15-13.

## Notes

- Correction on the record: the 83-02 evidence states its full sweep as
  "3215 passed" — the true figure was **3211** (the first write summed the
  drift-guard file's 5 re-run tests instead of the 1 fixed). Evidence files
  are write-once (the hook locks them to their story's shipping commit), so
  the correction lives here.

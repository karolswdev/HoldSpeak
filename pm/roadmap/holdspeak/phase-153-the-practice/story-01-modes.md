# HS-153-01 - Modes as recipes (kind, seeds, allow-lists, mode tabs)

- **Project:** holdspeak
- **Phase:** 153
- **Status:** backlog
- **Depends on:** HS-152-06
- **Unblocks:** HS-153-02, HS-153-03, HS-153-06
- **Owner:** unassigned

## Problem

A Thread with hands needs a practice: what it may touch and how it
speaks. warpdrv's "modes" become recipes (settled design D1) — one
binding through `threads.recipe_id`, no parallel `mode_id`, and the
executor's palette becomes the mode's allow-list ∩ the classification
map. Without a mode the palette is `CHAT_PALETTE` (152 addendum).

## Scope

- **In (data layer — LANDED `9cb769a9`, verify, do not rebuild):**
  additive `recipes.kind` (`'' | 'mode'`), `holdspeak/services/thread_modes.py`
  (mode lookup, allow-list ∩ classes, palette for a thread), seeds
  `hs-seed-mode-{desk,chase,draft,plan}` in `holdspeak/seeds/fresh-desk.yaml`
  with the S4 allow-lists, `tests/unit/test_thread_modes.py`.
- **In (this story):** the executor/palette seam — `ThreadService`
  offers `thread_modes.palette_for(thread)` instead of `CHAT_PALETTE`
  when a mode is bound (Draft = no `tools` key at all); the truth table
  still gates effects. `PATCH /api/threads/{id} {recipe_id}` binds a
  mode (applies from the NEXT turn — in-flight passes keep theirs).
  Composer head mode tabs (Desk · Chase · Draft · Plan · custom recipes
  of kind `mode`), colour from `avatar`, keyboard reachable; the bound
  mode's name in the pullout head; `threads.ts` state + `setMode()`.
- **Out:** guardrails per mode (03), slash `/mode` (02).

## Acceptance criteria

- [ ] Through the REAL coordinator (fake engine): a thread bound to `Draft` admits a payload with no `tools`; bound to `Chase`, the admitted palette contains `people.commitment.transition` and not `desk.delete`; a mid-turn switch changes nothing until the next turn.
- [ ] A mode's allow-list naming an unclassified tool is dropped, never offered (fail-closed, logged once).
- [ ] Glass 1440 + 393: mode tabs render, the active tab is marked, switching writes `recipe_id` (GET shows it), no horizontal overflow.

## Test plan

- **Unit:** `tests/unit/test_thread_modes.py` (extend: palette seam through `ThreadService.start_turn` with the real coordinator, the "next turn" rule).
- **Integration:** `tests/e2e/test_hs153_practice_glass.py` leg `modes`.
- **Manual / device:** story 06 walk leg (Desk→Chase on `.43`).

## Notes / open questions

- The seam is `_run_streaming_turn`/`start_turn` where `tool_schemas_for(CHAT_PALETTE)` is called (two sites; both go through one `palette_for`).
- Custom mode = any recipe the owner sets `kind='mode'` on in the recipe editor (one checkbox; no new editor).

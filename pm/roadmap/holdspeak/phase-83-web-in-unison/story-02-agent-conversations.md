# HS-83-02 — Agent conversations (the rail grows threads)

- **Project:** holdspeak
- **Phase:** 83
- **Status:** open
- **Depends on:** HS-83-01 (the grounding picker rides this composer too).
- **Unblocks:** HS-83-03 (a model chat IS one of these), HS-83-04.

## Problem

Grounded 2026-07-07: the web's `RecipeRail`
(`web/src/desk/components/RecipeRail.tsx`) is a single-prompt surface — tap a
persona, type one question, the output is ephemeral. No history, no
persistence, no context attachment. The iPad's `DioRecipeChat` is a living
multi-turn conversation with per-conversation grounding; the web personas are
the same synced recipes with half a mouth.

## The design

- **The thread.** Opening a persona opens a conversation: message list,
  composer, thinking state, harvest-to-desk on replies (the kept card mints the
  same run-born artifact shape a kept ask does). Assembly mirrors the iPad's
  `recipeReply`: `[ROLE]` + `[CONTEXT]` (manual/zone/KB per the recipe) +
  `[CONVERSATION SO FAR]` (last 12 turns) + `[USER]`, run through `/api/ask`
  with the recipe's `profile_id`.
- **Persistence.** `localStorage` keyed by persona id — the iPad's
  device-local posture (recipes sync; threads do not). Clear-chat is a first-
  class action.
- **Grounding rides.** The HS-83-01 picker sits on this composer; the selection
  persists per conversation and ships as `grounding` refs on every turn.
- **KB honesty.** The web assembly must not reintroduce the dead hint string:
  a recipe's KB renders hydrated content or the explicit non-hydrated marker
  (the 15-12 rider's grammar).
- **Egress honest.** Each reply's badge is the ask response's reported
  egress/model — per turn, never the app default.

## Acceptance criteria

- [ ] A persona opens to its conversation; turns accumulate; reload keeps the
      thread; clear-chat empties it.
- [ ] A turn's request carries role + standing context + the running
      conversation; the reply renders in-thread with the hub-reported egress.
- [ ] Grounding attached mid-conversation ships refs on the next turn and shows
      on the composer chip.
- [ ] A reply harvests to the desk as a run-born artifact with provenance.
- [ ] Screenshots: a grounded thread with mixed turns; the composer chip.

## Test plan

- Vitest: the turn assembler (block order, 12-turn window, KB marker), thread
  store round-trip.
- Live: one real multi-turn conversation against the hub → .43, grounded on an
  imported meeting; screenshots.

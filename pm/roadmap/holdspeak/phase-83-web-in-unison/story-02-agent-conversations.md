# HS-83-02 — Agent conversations (the rail grows threads)

- **Project:** holdspeak
- **Phase:** 83
- **Status:** done — 2026-07-07, see [`evidence-story-02.md`](./evidence-story-02.md).
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

- [x] A persona opens to its conversation; turns accumulate; reload keeps the
      thread; clear-chat empties it. (Rig: 4 turns survive a reload; vitest:
      thread round-trip + clear.)
- [x] A turn's request carries role + standing context + the running
      conversation; the reply renders in-thread with the hub-reported egress.
      (pytest: block order + system-channel role; rig: per-turn badge.)
- [x] Grounding attached mid-conversation ships refs on the next turn and shows
      on the composer chip. (Rig: turn 2's captured prompt hydrates the
      meeting; the chip reads "1 meeting".)
- [x] A reply harvests to the desk as a run-born artifact with provenance.
      (`/keep` + `_persist_run_artifact`; rig: the NEW beat on the desk.)
- [x] Screenshots: a grounded thread with mixed turns; the composer chip.
      (`hs-83-02-*.png`.)

## Test plan

- Vitest: the turn assembler (block order, 12-turn window, KB marker), thread
  store round-trip.
- Live: one real multi-turn conversation against the hub → .43, grounded on an
  imported meeting; screenshots.

## Notes (decided at build)

- The turn assembles SERVER-side (`POST /api/recipes/{id}/chat`) — the web has
  no client assembly branch, mirroring the refs-only grounding stance. The
  role rides `run_prompt`'s system channel (the transport-correct seat); every
  other block keeps the iPad grammar and order.
- `use_zone_context` is NOT assembled on web yet: the desk's zone membership
  isn't on the chat route's wire. A later story owns that contract; the field
  is ignored honestly, not faked.
- Harvest is explicit (`/keep`): a chat turn persists nothing — the run
  route's mint-per-call behavior stays the run route's.

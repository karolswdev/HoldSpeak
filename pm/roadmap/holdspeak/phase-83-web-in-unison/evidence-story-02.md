# Evidence — HS-83-02: agent conversations (the rail grows threads)

**Date:** 2026-07-07. **Verdict: done.**

## What shipped

- **Hub:** `POST /api/recipes/{id}/chat` — ONE conversational turn: the
  persona's standing context (`manual_context` + the KB honesty block —
  hydrated member content or `[KB: name — no hydrated members]`, the hint
  string stays dead), HSM-15-12 `grounding` refs hydrated with the SAME wire
  and refusal grammar as `/api/ask`, the last 12 turns, the question. The role
  rides the system channel (the transport-correct seat for `run_prompt`; the
  deliberate deviation from the iPad's single-prompt packing — noted, not
  hidden). Answers with the turn's honest egress + model + folded
  `context_ids/titles`; **persists NOTHING**. `POST /api/recipes/{id}/keep`
  mints the run-born artifact only when the human says keep
  (`_persist_run_artifact`, kind `recipe`).
- **Web:** `chat.ts` (device-local threads + per-conversation grounding in
  `localStorage` — the iPad AppStorage posture; recipes sync, threads don't),
  `PersonaChat.tsx` (docked pullout: bubbles, thinking beat, per-reply honest
  badge + Save to desk, the HS-83-01 `GroundingSection` on the composer,
  over-budget gates Send), the rail's avatars now open the conversation (the
  anchored single-prompt is retired), store gains `chatPersonaId` +
  `openChat/closeChat`.

## Receipts

- **Hub pytest:** `tests/unit/test_web_routes_recipe_chat.py` — 6 tests: block
  order (`[CONTEXT] < [GROUNDING] < [CONVERSATION SO FAR] < [USER]`), KB
  hydration AND the honesty marker, the 12-turn window (turn 0 falls off),
  grounding refusal naming `unknown_ids`, persists-nothing, keep mints the
  artifact with recipe lineage. Full sweep **3215 passed** (after the
  api-surface regen with the new consumers).
- **Vitest:** 54/54 — `chat.test.ts` locks thread/grounding round-trips, the
  turn wire (12-tail, grounding refs, refusal verbatim), harvest.
- **The rig** (`scripts/screenshot_hs83_chat.py`): a REAL two-turn
  conversation through the live route — turn 1 carries `[CONTEXT]` and no
  history; grounding attached MID-conversation; turn 2's captured prompt
  carries the hydrated `[MEETING: Q3 kickoff — 2026-07-06]` block AND
  `[CONVERSATION SO FAR]` in the pinned order; the reply harvested to a NEW
  desk artifact; the thread survives a reload.
- **Screenshots:** `hs-83-02-thread-grounded-composer.png` (the thread, the
  per-turn badge, the grounded composer chip + gauge),
  `hs-83-02-thread-harvested.png` (the BLUE LANTERN reply in-thread, the
  harvested artifact NEW on the desk).

## Notes

- Zone context (`use_zone_context`) is the one standing-context field the web
  turn does not assemble yet — the web desk's zone membership isn't wired
  into the chat route's inputs. Deliberately out: it needs the zone contract
  on the wire, not a guess. Filed in the story's Notes.
- Two new routes ⇒ `docs/api-surface.json` regenerated (245 routes; the
  drift guard caught the pre-consumer regen — the sweep's one red turned
  green by regenerating AFTER the web call sites existed).

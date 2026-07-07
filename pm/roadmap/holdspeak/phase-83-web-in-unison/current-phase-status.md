# Phase 83 — Web in Unison (the desk speaks back)

**Status:** OPEN (2/4) — opened 2026-07-07 on the owner's direction, the same
session HSM-15-12/15-13 shipped on iOS.

**Last updated:** 2026-07-07 (HS-83-02 done — personas grow threads: the chat
route assembles context + KB honesty + grounding + the 12-turn window
server-side and persists nothing; the rail opens conversations; device-local
persistence; harvest via /keep. Hub 3215 · vitest 54 · rig-proven · 2 shots).

## Why this phase exists

On 2026-07-06 the iPad earned two conversation surfaces, both riding
`POST /api/ask`:

- **HSM-15-12, the context envelope** — "Ground this ask": pick meetings on the
  composer, expand each to digest / transcript / its bound artifacts, gauge the
  cost live, and run with provenance-headed grounding. The hub hydrates
  references server-side (`grounding: {meeting_ids, artifact_ids, expand}`),
  refuses unknown ids by name, and folds the lineage into
  `context_ids/titles` (+ a `grounding` echo). Locked by 5 hub tests and a
  real-metal control-vs-treatment proof.
- **HSM-15-13, chat with the desktop's model** — every model the hub can run is
  a chat you can open, pinned via the manifest-bounded `model` override
  (HSM-15-11), through the ONE existing chat surface.

A survey the next morning confirmed the web desk is one full pass behind
(receipts in the story files): `AskPanel.tsx` posts only
`{prompt, lens, context, profile_id}` — no grounding, no gauge; `RecipeRail`
personas are single-prompt and ephemeral — no thread, no attachment; no surface
lists what the hub can run, and nothing opens a chat with a model. The hub half
of all of it is already built and tested. This phase is UI against proven
contracts — the cheapest parity debt this repo will ever pay, and the
Equilibrium lesson (HSM 18–23) says pay it before it compounds.

**One thesis:** every conversation surface the iPad earned this pass exists on
the web desk, riding the same wire.

## The design (pinned here so the stories don't fossilize four accidents)

- **The web always ships references.** The web talks to the hub it lives on, so
  there is no client-side hydration branch at all: every grounded web ask sends
  `grounding` refs and the hub hydrates from its own store. One code path.
- **The gauge is honest or absent.** The picker prices a selection from REAL
  fetched lengths (the same ≈4-chars/token estimator as `OnDeviceBudget`), not
  from guessed metadata: toggling a transcript/artifact fetches its text length
  before pricing it. A selection past the profile's context window refuses at
  the gauge — never silent truncation (the 15-12 overflow rule).
- **Threads are device-local.** Web agent conversations persist in
  `localStorage` per persona id — the exact posture of the iPad's `AppStorage`
  threads. Recipes sync; threads do not (the Phase-17 contract). Making threads
  a synced primitive is a deliberate future contract change, not a side effect
  of this phase.
- **The runnable set gets a route.** `GET /api/models` returns the SAME
  allow-list the ask route's 400 names (the hub's own model + its profiles'
  models, with each model's source), so no client ever discovers capability by
  provoking an error. New route ⇒ `docs/api-surface.json` regenerates; tests
  pin the set equals the ask allow-list.
- **A model chat is a persona.** The web mirrors iOS: picking a model opens the
  ONE chat surface with a transient persona (id `modelchat:desktop:<model>`)
  pinned via the ask route's `model` override. No parallel chat component.
- **Receipts unchanged.** Kept asks keep minting the locked provenance wire
  shape; grounding rows ride `context_ids/titles` exactly as the hub already
  returns them. Egress badges stay hub-REPORTED, never inferred.
- **Stack rules stand.** React islands in the Astro shell, desk-first, no new
  Alpine; edit `web/src`, build to verify, commit source only;
  screenshot-verify every surface before it ships.

## Story status

| ID | Story | Status | Story file |
|----|-------|--------|------------|
| HS-83-01 | Ground this ask, on the web composer | **done** (2026-07-07 — picker + gauge + refs wire; rig + 49 vitest + 2 shots) | [story-01](./story-01-ground-this-ask-on-the-web.md) |
| HS-83-02 | Agent conversations (the rail grows threads) | **done** (2026-07-07 — `/api/recipes/{id}/chat` + `/keep`; PersonaChat + device-local threads; grounding rides; rig + 6 pytest + 5 vitest + 2 shots) | [story-02](./story-02-agent-conversations.md) |
| HS-83-03 | The models front door (`/api/models` + chat-with-model) | open | [story-03](./story-03-the-models-front-door.md) |
| HS-83-04 | Docs + the live walk | open | [story-04](./story-04-docs-and-the-live-walk.md) |

## Where we are

**2026-07-07 (later still) — PERSONAS GROW THREADS (HS-83-02 done).** The rail's
avatars open CONVERSATIONS now (the anchored single-prompt is retired):
`PersonaChat` is the docked thread — bubbles, the thinking beat, a per-turn
HONEST badge (the hub's reported egress/model, never inferred), Save-to-desk
per reply, and the HS-83-01 grounding picker on the composer with
per-conversation persistence. The turn is ONE hub call:
`POST /api/recipes/{id}/chat` assembles the persona's standing context (manual
+ the KB honesty block — hydrated members or the explicit marker), the
HSM-15-12 grounding refs (same wire, same refusals as `/api/ask`), the last 12
turns, then the question — the role rides the system channel — and persists
NOTHING; `POST /api/recipes/{id}/keep` mints the run-born artifact only on the
human's keep. Threads are device-local (`localStorage` — the iPad AppStorage
posture; recipes sync, threads don't). Proof: the rig ran a real two-turn
conversation — grounding attached MID-thread hydrated the meeting into turn 2's
captured prompt in the pinned block order, the reply harvested to a NEW desk
artifact, and the thread survived a reload. Hub **3215** (the api-surface
drift guard caught a pre-consumer regen — regenerate AFTER the client call
sites exist), vitest **54**, 2 screenshots. `use_zone_context` stays honestly
unassembled on web (the zone contract isn't on this wire — noted in the
story). Next: HS-83-03 (the models front door — a model chat is one of THESE
threads with a pinned model).

Earlier — **2026-07-07 (later) — THE WEB COMPOSER GROUNDS ASKS (HS-83-01 done).** The
"Ground this ask" section sits on `AskPanel` under Runs-on: meetings expand to
digest / transcript / each bound artifact (independently toggleable, iPad
defaults — digest on, transcript opt-in), the gauge prices the selection from
REAL fetched lengths and refuses past the picked profile's window, and the run
ships REFERENCES ONLY (`grounding: {meeting_ids, artifact_ids, expand}`) — the
hub hydrates. Receipts: grounding rows join the kept ask's context; a 400
renders the hub's refusal naming `unknown_ids` verbatim. Proof: the house
Playwright rig (`scripts/screenshot_hs83_grounding.py`) drove the full arc and
ASSERTED the treatment — the engine-captured prompt contains the hydrated
`[MEETING: …]` / `[ARTIFACT: …]` blocks while the request carried ids only;
49/49 vitest; 2 screenshots. Next: HS-83-02 (the chat surface reuses this
picker) or HS-83-03's route half.

Earlier — **2026-07-07 — OPENED.** The gap survey is in the story files; the design is
pinned above; HS-83-01 is the first build (the picker + `grounding` refs on
`AskPanel`), HS-83-03's `/api/models` route can land independently. The proof
posture for every story: the live hub on this Mac (engine → the .43 llama.cpp),
screenshots of rendered pixels, control-vs-treatment for anything an LLM
answers.

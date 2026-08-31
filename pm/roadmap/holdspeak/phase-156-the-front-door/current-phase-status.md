# Phase 156 - The Front Door

**Last updated:** 2026-08-31.

## Goal

The desk earns its first minute: recommended packs A/B/C from the
hardware and what already exists, one confirmation wires everything
through the existing machinery, and the Library/Assignments engine
room folds underneath as the advanced layer (owner rulings 2026-08-31;
settled design D1–D7, incl. the topology map). OUTRANKS 155 The Crew.

## Scope

- **In:** the seven stories below (the council-ruled library reform is story 03, a prerequisite of the door and the topology); PR from `feat/the-front-door`.
- **Out:** new model catalog entries, network-wide LAN scanning,
  removing anything from the advanced layer, Phase 155.

## Exit criteria (evidence required)

- [ ] All seven stories done with evidence; the stopwatch bar met and measured (<60 s cold-owner to working chat + dictation, downloads excluded and reported); glass 1440+393; metal on `.43`; counsel zero open must-fix; sweep name-diff clean + the web contract green.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-156-01 | The recommendation (packs A/B/C from existing facts) | done | [story-01-the-recommendation](./story-01-the-recommendation.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-156-02 | One confirmation applies everything | done | [story-02-one-confirmation](./story-02-one-confirmation.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-156-03 | The library patterns (the reform's v1, the barrel, the fence) | in-progress | [story-03-the-library-patterns](./story-03-the-library-patterns.md) | - |
| HS-156-04 | The door surface (cards, plan, health strip, fold) | backlog | [story-04-the-door-surface](./story-04-the-door-surface.md) | - |
| HS-156-05 | Plain words (jargon purge, UX-evidence checklist) | backlog | [story-05-plain-words](./story-05-plain-words.md) | - |
| HS-156-06 | The topology (this Mac + nodes; configuration over the same authorities) | backlog | [story-06-the-topology](./story-06-the-topology.md) | - |
| HS-156-07 | The stopwatch walk and the close | backlog | [story-07-the-stopwatch-walk](./story-07-the-stopwatch-walk.md) | - |

## Where we are

HS-156-01 done. HS-156-02 in-progress: the apply engine, routes, DB
persistence, and 27 unit tests are built and passing (73 total with
recommendation + fence tests). The apply engine drives only existing
service seams (define_endpoint, download, set_assignment) -- no direct
DB writes. Fault injection proven: failure on item N -> plan records
the error, re-apply completes the remainder, nothing double-created.
The end-to-end assignment proof is BLOCKED-ON(fix/model-wiring-p0):
the define-endpoint context_ceiling=0 bug makes all profiles
incompatible at the assignment compat check. The test suite stubs the
assignment service to prove the calling shape. Awaiting orchestrator
commit + flip to done after P0 fix merges.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The door becomes a parallel authority | medium | the 02 fence: apply drives only existing service seams | a direct DB write in the apply path |
| Pack recommendations rot as the catalog moves | medium | fixture truth tables per hardware class; the recommender is pure | a pack that no longer fits its hardware class |
| The stopwatch bar slips into vibes | low | the rig measures wall clock; the bar is an exit criterion | a close without the number |

## Decisions made (this phase)

- 2026-08-31 - DESIGN COUNCIL ruling ratified into the charter (assets/design-council.md; voices: codex gpt-5.6-sol + Opus): surface/ promoted with a public barrel + contract.md, seven v1 delight patterns, the ratchet fence, visual gates first-class at three boundaries, the reform as story 03 before the door/topology - council-led per the owner's ruling - orchestrator synthesis, owner ratifies.

- 2026-08-31 - Two layers: packs A/B/C on top, the existing Library/Assignments as the advanced layer - owner ruling, verbatim in the settled design - never a parallel authority.
- 2026-08-31 - No network-wide LAN scanning; explicit endpoints only - custody posture - orchestrator.
- 2026-08-31 - The cloud never appears on the A path without an existing credential - the door never asks for an API key first - orchestrator.

## Decisions deferred

- Pack refresh after hardware changes - trigger: a real hardware upgrade on a configured desk - default: the desk proposes, never auto-changes.

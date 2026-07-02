# HS-73-07 — The agent rail: run from the world

- **Status:** todo
- **Priority:** MED (the intelligence verb, in-world)
- **Depends on:** HS-73-01, HS-73-03

## Goal

Personas run from the world and their results land in the world. A
right-edge avatar rail (iPad parity: the Agents rail, `DeskAgents.swift`)
lists the user's agents; running one plays the generation theater and the
result materializes on the stage. Today running an agent means finding its
card in the (soon-deleted) list appendix and using a drawer.

## Scope

- **In:** the rail; run-from-rail and run-from-pull-out; the theater; the
  result landing; the persona/coder boundary.
- **Out:** coder (live session) presence — `agent` ≠ `coder` per the
  Primitive Framework; the coder board stays on the page Phase 72 renames
  (`refreshCoders`, `desk-app.js:885`, keeps feeding whatever quiet
  presence the desk already shows, unchanged); chain/workflow authoring;
  drag-object-onto-agent as a run input (a natural follow-up — record it
  in the phase status doc as a deferred decision, do not build it here
  unless trivially cheap after the rail exists).

## Tasks

- [ ] `components/desk/DeskRail.astro` + `web/src/scripts/desk/rail.js`
      (factory-rendered, `is:global`): a slim right-edge rail of agent
      avatars (from `items.agent`; avatar/emoji + name-on-hover; the
      egress badge per agent via `profileEgress`, `desk-app.js:618`).
      Collapsed by default to avatars only; never a panel that eats the
      world.
- [ ] Run: tapping a rail avatar (or Run in the agent pull-out, HS-73-03)
      opens a minimal in-world prompt affordance (one input anchored to
      the rail — not a modal), then calls the existing run route
      (`POST /api/agents/{id}/run` — read the current `openRun` drawer
      logic in `desk-app.js` for the exact payload and reuse it verbatim).
- [ ] While running: the generation theater (Phase 69's orb +
      constellation, mounted by AppLayout) plays; the rail avatar shows a
      working state. Queue HUD behavior is untouched (it synthesizes from
      the same frames it always has).
- [ ] The result: if the run persists an artifact, refresh + `markNew` —
      it materializes on the stage and its pull-out opens. If the run
      returns only text (verify against the route's actual response
      shape), render it in the agent's pull-out with a copy affordance —
      never a toast with prose.
- [ ] Delete the run drawer once both run paths (rail, pull-out) are live
      (coordinate with the HS-73-04 inventory if that story has not yet
      merged).

## Proof required

Playwright/screenshots: rail visible with real agents; tap → prompt → run
against the `.43` endpoint (real-metal preferred, per the standing rule
that LLM-shaped features get a real-model proof) → theater plays → the
result lands in-world. The persona/coder boundary asserted: no coder
session appears in the rail. Route pre-flight + full suite +
`npm run build` green.

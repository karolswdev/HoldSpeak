# HS-73-07 — The agent rail: run from the world

- **Status:** todo
- **Priority:** MED (the intelligence verb, in-world)
- **Depends on:** HS-73-01, HS-73-04

## Goal

Personas run from the world and their results land in the world. A
right-edge avatar rail (iPad parity: the Agents rail, `DeskAgents.swift`)
lists the user's agents; running one plays the generation theater and the
result materializes on the stage.

## Scope

- **In:** the `AgentRail` component; run-from-rail and run-from-pull-out;
  the theater; the result landing; the persona/coder boundary.
- **Out:** coder (live session) presence — `agent` ≠ `coder` per the
  Primitive Framework; the coder board stays on the page Phase 72 renames;
  chain/workflow authoring; drag-object-onto-agent as a run input
  (recorded as a deferred decision in the status doc — do not build unless
  trivially cheap once the rail exists).

## Tasks

- [ ] `AgentRail`: a slim right-edge rail of agent avatars (from
      `items.agent`; name on hover; per-agent egress badge via the ported
      `profileEgress`). Collapsed to avatars by default; never a panel
      that eats the world.
- [ ] Run: tapping a rail avatar (or Run in the agent pull-out) opens a
      minimal in-world prompt input anchored to the rail — not a modal —
      then calls the existing run route (`POST /api/agents/{id}/run`).
      **Read the legacy `openRun` drawer logic in `desk-app.js` for the
      exact request payload and the response shape, and reuse both
      verbatim.**
- [ ] While running: the generation theater (Phase 69's shell widget)
      plays; the rail avatar shows a working state; Queue HUD behavior
      untouched.
- [ ] The result: if the run persists an artifact, refresh + materialize
      it with the NEW beat and open its pull-out. If the run returns only
      text (per the verified response shape), render it in the agent's
      pull-out with a copy affordance — never a toast with prose.
- [ ] Chain/workflow Run in their pull-outs rides the same path
      (`POST /api/chains/{id}/run`, the workflow run route) with the same
      landing behavior.

## Proof required

Screenshots/Playwright: the rail with real agents; tap → prompt → a run
against the `.43` endpoint (real-metal, per the standing rule for
LLM-shaped features) → theater → the result lands in-world. The
persona/coder boundary asserted: no coder session appears in the rail.
Route pre-flight + full suite + `npm run build` green.

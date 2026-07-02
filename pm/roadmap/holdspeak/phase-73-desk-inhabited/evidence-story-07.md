# Evidence — HS-73-07 — The agent rail: run from the world

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-73-desk-inhabited`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **`AgentRail`**: a slim right-edge rail of persona avatars (the iPad's
  Agents rail) — **personas only; a coder is a live session and is never
  railed** (the Primitive Framework rule). Each avatar wears its
  per-agent egress dot (profile-derived: green on-device / blue endpoint,
  the endpoint host in the hover title — the badge answers, no prose).
- **Tap → an anchored ask** (a popover beside the avatar, not a modal):
  focused input, Enter or Run fires the REAL
  `POST /api/agents/{id}/run`; the avatar pulses a working state while
  busy; the result renders in place with a **Copy affordance** (never a
  toast); Escape closes.
- The pull-out's Run (HS-73-04) and the rail share the same route and
  result treatment.

## The honest theater finding

The shell GenerationTheater listens to `intel_status/intel_token/
intel_complete` bus frames — and the persona-run route is a synchronous
engine call that **emits no frames today**, so the theater cannot honestly
fire on a rail run. Rather than faking frames from the client, the rail
carries its own working state, and "the run route should broadcast intel
frames" is recorded as a hub follow-up (out of this phase's scope — the
phase adds no new backend). The theater keeps firing where the hub
actually streams (meeting intel).

## Verification artifacts

- **The real-metal run (the story's crux, on the `.43` endpoint)**: from
  the rail UI in a real browser, the ask "Say the word 'desk' and nothing
  else." went through the hub's configured engine to the LAN endpoint and
  the REAL model answered `'desk'` — instruction followed, so the prompt
  demonstrably reached the model (the Phase-53 control-vs-treatment
  lesson). `07-rail-run-result.png`.
- The rail rendered exactly the persona (no coder lane); the anchored ask
  opened focused; Escape closed it; the Copy affordance present beside
  the result. Zero page errors.
- Build 18 pages; api-surface + pre-flight **7 passed**; full suite
  **3066 passed, 37 skipped, 0 failures**.

## Acceptance criteria — re-checked

- [x] Personas only, right-edge, egress dot per agent.
- [x] Anchored ask (no modal); the real run route; working state; result
      with copy.
- [x] Real-metal proof on `.43` with an instruction-following check.
- [x] The theater's behavior verified honestly (finding recorded, no
      client-side fakery).

## Deviations from plan

- The result stays in the anchored card rather than materializing as a
  world object: the run route persists nothing (output only), and
  inventing a client-side artifact would violate the phase's no-invented-
  state rule. When the hub persists run results, the HS-73-06 materialize
  beat is ready for them.

## Follow-ups

- Hub follow-up (recorded): broadcast intel frames from the /run routes so
  the theater plays for persona runs.
- HS-73-08: the cutover (delete the Alpine desk behind the verb
  inventory).

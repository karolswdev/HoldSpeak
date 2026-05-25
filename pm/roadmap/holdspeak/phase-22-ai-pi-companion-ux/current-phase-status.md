# Phase 22 — AI PI Companion UX

**Last updated:** 2026-05-24 (phase opened; current pickup is HS-22-01 companion state model).

## Goal

Make AI PI feel like a real HoldSpeak companion: a small physical surface that
shows the right local state at the right time and lets the user answer or act by
voice without guessing what the device is doing.

## Scope

### In

- Companion state model across idle, connected, meeting, agent-waiting, reply,
  and error states.
- LCD priority/cadence contract: sticky vs flash vs cycle vs stale clearing.
- Gesture contract for answering a waiting agent, showing questions, cycling
  meeting stats, bookmarking, and clearing stale context.
- Bridge behavior for `/api/companion/status`, agent query names, and display
  updates.
- Live hardware dogfood with a real Claude/Codex waiting-response loop.

### Out

- Autonomous replies to Claude/Codex without explicit user speech/action.
- Cross-network transport.
- Hosted assistant orchestration.
- New hardware design.
- Replacing HoldSpeak text insertion with a direct agent API transport.

## Exit criteria

- [ ] A companion state model is documented and implemented across bridge/display behavior.
- [ ] The button/gesture contract is documented and covered by bridge tests.
- [ ] AI PI can visibly show a waiting Claude/Codex question and clear stale state predictably.
- [ ] AI PI can initiate a voice reply to a waiting agent through the shipped HoldSpeak companion path.
- [ ] Live hardware dogfood records at least one real Claude/Codex answer flow.
- [ ] Phase closeout records what became product-ready and what remains experimental.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-22-01 | Companion state model and LCD priority contract | backlog | [story-01-companion-state-model.md](./story-01-companion-state-model.md) | — |
| HS-22-02 | Gesture contract for agent and meeting actions | backlog | — | — |
| HS-22-03 | Bridge companion polling and display wiring | backlog | — | — |
| HS-22-04 | Agent voice-reply hardware dogfood | backlog | — | — |
| HS-22-05 | Phase exit and product handoff | backlog | — | — |

## Where we are

Phase 20 shipped the HoldSpeak-side companion contract. Phase 21 brought the
AIPI-Lite firmware and bridge into this repo and defined the unified developer
workflow. Phase 22 starts by defining the actual physical companion UX contract
before changing firmware or bridge behavior.

Current pickup: HS-22-01, the companion state model and LCD priority contract.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| LCD shows stale or conflicting state | high | Define explicit priority and stale-clear rules before wiring behavior. | User cannot tell whether AI PI is waiting, recording, or idle. |
| Gestures become overloaded | medium | Keep one primary reply gesture and document conflicts with existing meeting gestures. | Users trigger bookmark/cycle/reply accidentally. |
| Reply lands in wrong target | high | Keep explicit user speech/action and reuse HoldSpeak's waiting-agent target context. | A spoken answer appears in the wrong app/session. |
| Bridge/device behavior diverges from HoldSpeak server contract | medium | Test against `/api/companion/status` and existing `query` / `status` frames. | Bridge invents parallel state outside HoldSpeak. |

## Decisions made

- 2026-05-24 — **Product-first phase.** Phase 22 starts with state/gesture/LCD UX before adding more substrate.
- 2026-05-24 — **No autonomous replies.** Device actions may initiate user speech capture, but replies remain user-driven.
- 2026-05-24 — **Use shipped server contract first.** Prefer `/api/companion/status` plus existing device `query` / `status` before adding new wire frames.

## Decisions deferred

- Whether the final reply gesture is press-and-hold, double-tap, or a left/right combination.
- Whether the bridge should poll companion status or HoldSpeak should push agent-waiting state.
- Whether a browser companion panel is needed alongside the physical device.

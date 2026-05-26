# Phase 22 — AI PI Companion UX

**Last updated:** 2026-05-25 (closed; Phase 23 planning opened for companion UX polish).

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
- tmux-pane reply delivery when hooks run inside tmux.

### Out

- Autonomous replies to Claude/Codex without explicit user speech/action.
- Cross-network transport.
- Hosted assistant orchestration.
- New hardware design.
- Replacing HoldSpeak text insertion with a direct agent API transport.

## Exit criteria

- [x] A companion state model is documented and implemented across bridge/display behavior.
- [x] The button/gesture contract is documented and covered by bridge tests.
- [x] AI PI can visibly show a waiting Claude/Codex question and clear stale state predictably.
- [x] AI PI can initiate a voice reply to a waiting agent through the shipped HoldSpeak companion path.
- [x] Live hardware dogfood records at least one real Claude/Codex answer flow.
- [x] Phase closeout records what became product-ready and what remains experimental.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-22-01 | Companion state model and LCD priority contract | done | [story-01-companion-state-model.md](./story-01-companion-state-model.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-22-02 | Gesture contract for agent and meeting actions | done | [story-02-gesture-contract.md](./story-02-gesture-contract.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-22-03 | Bridge companion polling and display wiring | done | [story-03-bridge-companion-polling.md](./story-03-bridge-companion-polling.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-22-04 | Agent voice-reply hardware dogfood | done | [story-04-agent-voice-reply-dogfood.md](./story-04-agent-voice-reply-dogfood.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-22-05 | tmux agent reply transport | done | [story-05-tmux-agent-reply-transport.md](./story-05-tmux-agent-reply-transport.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-22-06 | Phase exit and product handoff | done | [story-06-phase-exit-and-product-handoff.md](./story-06-phase-exit-and-product-handoff.md) | [evidence-story-06.md](./evidence-story-06.md) |

## Where we are

Phase 22 is closed. It shipped the AI PI companion state model, gesture
contract, bridge display wiring, live hardware dogfood, and tmux-pane reply
delivery for terminal agents.

Current pickup: Phase 23 companion UX polish.

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
- 2026-05-24 — **Partial dogfood is real signal.** Agent capture, AI PI
  display, physical capture, audio ingress, and transcription work. The next
  blocker is insertion back into Claude from a GUI-capable runtime.
- 2026-05-24 — **tmux over GUI focus.** GUI typing proves the loop, but tmux
  pane targeting is the practical local transport for terminal agents.

## Decisions deferred

- How long Claude/Codex prompts should marquee or window across AI PI.
- How to label and browse multiple simultaneous Claude/Codex sessions.
- Whether the bridge should continue polling companion status or HoldSpeak should push agent-waiting state.
- Whether a browser companion panel is needed alongside the physical device.

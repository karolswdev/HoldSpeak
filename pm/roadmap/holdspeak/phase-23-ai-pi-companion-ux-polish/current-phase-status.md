# Phase 23 — AI PI Companion UX Polish

**Last updated:** 2026-05-26 (Phase 23 closed).

## Goal

Make AI PI understandable and trustworthy during real agent work: long
Claude/Codex prompts should remain readable, multiple sessions should be
distinguishable, and the user should know what they are about to answer before
speaking.

## Scope

### In

- Long-question display behavior, including marquee or windowed text on the
  physical display.
- Multi-session identity for Claude/Codex sessions, including agent name,
  project/path, tmux session/window/pane, freshness, and answer target.
- Session preview/browse UX on AI PI and/or a compact web companion panel.
- Companion status API cleanup so readiness, insertion, runtime, and target
  confidence are reported consistently.
- Live dogfood with at least two Codex sessions and one Claude session.

### Out

- Autonomous replies without explicit user speech/action.
- Direct Claude/Codex API transport.
- Cross-network device reach.
- Hosted assistant orchestration.
- New hardware design.

## Exit criteria

- [x] Long Claude/Codex questions no longer appear as ambiguous truncated text on AI PI.
- [x] AI PI can identify which agent/session is waiting before the user answers.
- [x] The user can preview or cycle active sessions without losing the current answer target.
- [x] Companion status reports target confidence and runtime readiness consistently.
- [x] Live dogfood covers multiple simultaneous sessions and records the observed UX gaps.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-23-01 | Long prompt display and marquee/window contract | done | [story-01-long-prompt-display.md](./story-01-long-prompt-display.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-23-02 | Multi-session identity model | done | [story-02-multi-session-identity.md](./story-02-multi-session-identity.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-23-03 | Session preview list contract | done | [story-03-session-preview-list.md](./story-03-session-preview-list.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-23-04 | Device browse controls and selected target | done | [story-04-device-browse-selected-target.md](./story-04-device-browse-selected-target.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-23-05 | Reply target readiness guard | done | [story-05-reply-target-readiness-guard.md](./story-05-reply-target-readiness-guard.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-23-06 | Multi-agent live dogfood and phase closeout | done | [story-06-live-dogfood-and-closeout.md](./story-06-live-dogfood-and-closeout.md) | [evidence-story-06.md](./evidence-story-06.md) |

## Where we are

Phase 23 is closed. The interaction model is documented in
[interaction-model.md](./interaction-model.md): AI PI should be a physical
attention surface, voice reply trigger, and session selector for local agent
work, not a tiny chat console.

HS-23-01 through HS-23-06 are closed. Long questions now render as
deterministic windows instead of ambiguous clipped text. Waiting agent sessions
now expose a compact display identity plus structured target
transport/confidence through `/api/companion/status`, and companion status also
includes a newest-first preview list of waiting sessions. AI PI gestures now
have an offline-tested selected-target contract: outside a meeting, single tap
shows the selected agent question and double tap cycles the selected target.
The runtime now rejects voice capture when the selected agent target has no
delivery path, so unavailable targets no longer look replyable.

HS-23-06 live hardware dogfood confirmed session cycling, tmux reply delivery,
and post-reply transcript readability. It also exposed a middle-display race
where a spoken reply transcript was visible only briefly before the companion
poller repainted the agent waiting screen; the bridge now holds companion
middle-zone repaints until the status flash TTL expires.

See [final-summary.md](./final-summary.md) for the phase handoff.

## Product problems handled

| Problem | Phase 23 result | Remaining move |
|---|---|---|
| Agent responses/questions end with `...` | Long prompts now render as deterministic windows without ambiguous ellipses. | Consider firmware marquee or richer layout only if windows prove too coarse. |
| Two Codex sessions and one Claude session look the same | Status payloads and AI PI labels now include agent, project, tmux target, transport, and confidence. | Add a web companion overview for scanning all waiting sessions. |
| No preview of active sessions | AI PI can preview the selected session and cycle targets by gesture. | Add list/count/pin/dismiss controls in the next companion phase. |
| Top-level companion status can contradict nested runtime status | Runtime readiness and target confidence are now exposed consistently. | Keep tightening status naming as the web panel lands. |
| Polling works but feels coarse | Status flash holds prevent premature overwrite during fast transitions. | Decide whether to move display updates to push/repaint events. |

## Completed order

1. HS-23-01: long-text display contract.
2. HS-23-02: active-session and answer-target identity.
3. HS-23-03: session preview list contract.
4. HS-23-04: device browse controls and selected answer target.
5. HS-23-05: reply-target readiness guard.
6. HS-23-06: live dogfood and phase closeout.

## Decisions carried forward

- Replies remain user-driven. AI PI can help capture and route the answer, but
  it should not answer Claude/Codex autonomously.
- tmux is the primary terminal-agent transport when hook metadata is available.
- GUI text insertion remains a fallback, not the preferred path for terminal
  agent sessions.
- Polling remains acceptable until Phase 23 proves it is the reason the UX is
  unclear.

## Decisions made

- 2026-05-26 — **Limited device, powerful model.** AI PI's constraint is the
  product advantage: it should answer "who needs me, what are they asking, where
  will my answer go, and what happens if I act now?"
- 2026-05-26 — **Start with display confidence.** Long-prompt display lands
  before multi-session browsing because the user must first trust what the
  device is showing.
- 2026-05-26 — **Window long text before adding controls.** Bridge-side
  `[N/M]` question windows are enough to remove ambiguous truncation; richer
  browse/selection controls remain Phase 23 follow-up work.

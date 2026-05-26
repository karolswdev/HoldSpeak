# AI PI Companion Interaction Model

**Status:** working product thesis for Phase 23.
**Last updated:** 2026-05-26.

## Thesis

AI PI is powerful because it is limited. It should not try to become a tiny
computer, a chat app, or a full agent console. Its value is being a physical
attention surface for local work:

- it notices when an agent needs the user;
- it shows just enough context to make the next action safe;
- it captures a spoken response;
- it routes that response to the correct local session.

The product promise is not "answer agents from a tiny screen." The promise is
"stay in flow while local agents ask for clarification."

## Design Pressure

The display and buttons force useful discipline. Every feature must answer one
of four questions:

1. Who needs me?
2. What are they asking?
3. Where will my answer go?
4. What happens if I act now?

If a proposed feature does not improve one of those answers, it should stay off
the device or move to the web companion panel.

## Device Roles

### Attention Surface

AI PI should make agent-waiting state visible without requiring the user to
scan terminal panes. This is the first viewport for local agent interruption.

Minimum useful state:

- agent: `Codex` or `Claude`;
- project: short repo/project label;
- session identity: tmux session/window/pane when known;
- question preview;
- freshness or stale marker.

### Voice Reply Trigger

AI PI should remain user-driven. The device may initiate capture after an
explicit gesture, but it must not synthesize or send autonomous replies.

The reply path is:

```text
agent asks -> HoldSpeak captures hook state -> AI PI shows waiting state
-> user gestures/speaks -> HoldSpeak rewrites if enabled -> tmux/typing sends
```

### Session Selector

When multiple agents are active, AI PI must distinguish "current display" from
"answer target." Cycling and preview should be safe:

- cycling may browse sessions;
- answering should target the selected session;
- stale sessions should be visibly stale or skipped by default;
- the web companion can provide richer inspection.

## Product Constraints

- The LCD cannot be treated as a transcript viewer.
- Long text must be windowed, paged, or marquee-scrolled with stable labels.
- The primary interaction should work without a GUI terminal because tmux is the
  practical terminal-agent transport.
- Polling is acceptable while it is reliable and understandable; push updates
  are only needed if polling causes stale or confusing UX.
- The system should prefer confidence over cleverness. If target confidence is
  low, show that and require a safer user action.

## Phase 23 North Star

At the end of Phase 23, the user should be able to have two Codex sessions and
one Claude session active, glance at AI PI, understand which one is asking what,
preview or cycle if needed, answer by voice, and trust where that answer lands.


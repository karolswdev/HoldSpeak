# HS-23-04 — Device Browse Controls and Selected Target

- **Status:** done
**Opened:** 2026-05-26.
**Closed:** 2026-05-26.
**Owner:** Codex.

## Problem

HS-23-03 exposed a list of waiting sessions, but the physical interaction still
needed a safe way to browse that list and make voice replies target the selected
session. Without a selected target, multi-session preview would be informative
but not actionable.

## Outcome

AI PI can use existing gestures to inspect and cycle waiting agent sessions
outside a meeting:

- left single tap shows the selected agent question when an agent is waiting;
- left double tap cycles the selected waiting agent target;
- right hold-to-talk replies to the selected target because HoldSpeak resolves
  the active awaiting session through the persisted selection.

## Scope

### In

- Persist a selected waiting agent target in the local agent-session registry.
- Add a cycle helper that advances through recent waiting sessions.
- Add `agent_next` to the device query vocabulary.
- Route bridge gestures to `agent_question` and `agent_next` when companion
  status says an agent is waiting.
- Keep meeting gestures higher priority than agent browsing.
- Cover selected-target cycling and bridge gesture routing in tests.

### Out

- Hardware dogfood. AI PI is offline for this slice.
- Web companion panel UI.
- More advanced browse modes, such as previous/next direction or session
  dismissal.

## Acceptance Criteria

- [x] HoldSpeak can persist and retrieve a selected awaiting agent session.
- [x] Cycling from the default newest session advances to the next waiting
      session and wraps.
- [x] Device query `agent_next` advances the selected target and returns a
      status response.
- [x] Bridge single/double tap behavior distinguishes meeting, agent-waiting,
      and idle states.
- [x] Focused tests cover the selection helper, query model, gesture contract,
      and device-leg query routing.

## Closeout

Implemented 2026-05-26. See [evidence-story-04.md](./evidence-story-04.md).

# HS-23-03 — Session Preview List Contract

- **Status:** done
**Opened:** 2026-05-26.
**Closed:** 2026-05-26.
**Owner:** Codex.

## Problem

HS-23-02 gave one waiting session a trustworthy identity. Preview and browse
need the same contract for more than one session. Otherwise the device or web
companion would have to reconstruct labels and target confidence from raw hook
fields, which risks disagreement with the selected answer target.

## Outcome

HoldSpeak exposes a deterministic list of recent waiting agent sessions through
`/api/companion/status`. Each item carries the same compact identity and target
confidence payload used for the currently selected session.

## Scope

### In

- Add a reusable helper for listing recent awaiting agent sessions.
- Sort waiting sessions newest-first and support a small limit for companion
  surfaces.
- Include session preview items in `/api/companion/status`.
- Mark the currently selected newest session in that list.
- Cover list ordering, selected state, and per-item identity in tests.

### Out

- Physical button cycling on AI PI.
- Mutating the selected answer target.
- Web companion panel UI.
- Hardware dogfood. AI PI is offline for this slice.

## Acceptance Criteria

- [x] HoldSpeak can list recent awaiting sessions instead of only returning the
      newest one.
- [x] `/api/companion/status` exposes `agent.sessions.count`,
      `selected_index`, and preview `items`.
- [x] Each preview item includes the same structured `identity` payload as the
      selected session.
- [x] Tests cover newest-first ordering and companion status preview shape.
- [x] Evidence records validation and notes that physical browse controls remain
      follow-up work.

## Closeout

Implemented 2026-05-26. See [evidence-story-03.md](./evidence-story-03.md).

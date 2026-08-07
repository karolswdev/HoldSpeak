# Phase 125 — The Follow-Through

**Status:** active (1/10).

**Last updated:** 2026-08-07.

## The orchestrator

Opus 4.6 implements. Terra verifies against spec. The orchestrator
makes the done call.

## What we're building

Phase 124 gave the desk a nervous system: every service call observed,
recorded, correlated. But the desk still forgets what people promised.
Meetings end with action items scattered across aftercare payloads and
cadence loops. Decisions accept but produce no accountable commitment.
Nobody sees — in one place — what was agreed, who owes it, and what
has silently stalled.

Phase 125 closes that gap. Every meeting becomes a living execution
board: decisions bridge into commitments with owners and due dates,
aftercare enforces triage before loose ends go dark, and a single
Follow-Through surface answers "who owes what?" with provenance back
to the sentence where it was promised.

The result: the desk follows through. Nothing agreed upon gets lost.

## The architecture

```
Meeting ──→ Aftercare ──→ Triage (ownerless? undated? review?)
  │                          │
  ├── action_items ──────────┼──→ FollowThroughService.board()
  │                          │         │
  ├── decisions ─────────────┤    Now / Waiting / Unassigned / Overdue
  │     │                    │         │
  │     └── accept ──→ decision_commitments    │
  │                          │         │
  └── cadence_loops ─────────┘    provenance (segment, moment)
                                       │
                              ┌────────┴────────┐
                              │  Desk pullout   │
                              │  MCP tools      │
                              │  Monday brief   │
                              └─────────────────┘
```

## Why this phase exists

1. **The promise gap.** Meetings produce action items and decisions,
   but there is no unified view of what was agreed, who owns the next
   move, and what is overdue. Aftercare rolls up data; nobody triages
   it. (Constitution Article V.2: every attempt leaves a receipt.)

2. **The commitment gap.** `DecisionLifecycleService.transition()` can
   accept a decision, but acceptance creates no accountable action with
   an owner and a due date. The decision lives; the commitment doesn't.

3. **The visibility gap.** Action items live in `action_items`, decisions
   in `decisions`, loops in `cadence_loops`, project associations in
   `meeting_projects`. No single read model joins them into lanes a
   tech lead can scan on Monday morning.

4. **The provenance gap.** When a card says "you owe the API design by
   Thursday," there is no click-through to the meeting segment where
   that was promised. `resolve_provenance_segment()` exists but isn't
   surfaced on a board.

## Constitutional grounding

- **Article V.2:** "Every attempt leaves a receipt: who, what, where,
  outcome." Commitments are the receipt of a decision. Follow-through
  is the receipt of a promise.
- **Article VII.1:** "No prose in the UI." The board states what is
  owed, by whom, by when — in the fewest words.
- **Article VII.2:** "No modals. Everything is created and edited
  in-world." The Follow-Through surface edits in place.
- **Article I.1:** "The Desk is the operating surface." Follow-through
  is a Desk pullout, not a feature-owned screen.
- **Article IX:** "Proof over claim." The walk proves it.

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-125-01 | Wire SQLiteObserver into production composition | done | [story-01](story-01-wire-observer-production.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-125-02 | Board projection service | backlog | [story-02](story-02-board-projection-service.md) | — |
| HS-125-03 | Decision commitments | backlog | [story-03](story-03-decision-commitments.md) | — |
| HS-125-04 | Aftercare triage queue | backlog | [story-04](story-04-aftercare-triage.md) | — |
| HS-125-05 | Decision loop collection | backlog | [story-05](story-05-decision-loop-collection.md) | — |
| HS-125-06 | Due and stall semantics | backlog | [story-06](story-06-due-and-stall-semantics.md) | — |
| HS-125-07 | Write-through completion verbs | backlog | [story-07](story-07-write-through-completion.md) | — |
| HS-125-08 | Provenance on every card | backlog | [story-08](story-08-provenance-on-cards.md) | — |
| HS-125-09 | Desk surface and MCP tools | backlog | [story-09](story-09-desk-surface-and-mcp.md) | — |
| HS-125-10 | The walk | backlog | [story-10](story-10-the-walk.md) | — |

## Where we are

HS-125-01 done: all production service composition points now share a
`SQLiteObserver`, so real HTTP and MCP calls persist pipeline events.
HS-125-02 is next.

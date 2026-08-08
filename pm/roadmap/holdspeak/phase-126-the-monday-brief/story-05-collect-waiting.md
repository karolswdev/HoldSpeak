# HS-126-05 — Collect waiting work

- **Project:** holdspeak
- **Phase:** 126
- **Status:** done
- **Depends on:** HS-126-02
- **Unblocks:** HS-126-07
- **Owner:** unassigned

## The thesis (the bar)

Waiting is the desk's honest account of work that cannot advance on its own.
Bring blocked operational work together without mistaking passive history for
an active obligation.

### What changes

1. Collect pending actuator proposals.
2. Collect open, high-priority `cadence_loops` and unresolved projections.
3. Collect Delivery Workbench blockers through `MissionControlService`.
4. Collect overdue follow-through items.
5. Normalize and rank candidates with source references and the next waiting
   condition or action.

## Acceptance criteria

1. Each listed source contributes eligible Waiting candidates.
2. Closed, low-priority, resolved, and completed records are excluded.
3. Overdue follow-through is distinguishable from a normal pending item.
4. Each item opens its supporting record or identifies what must happen next.
5. Duplicate representations of one waiting obligation collapse predictably.

## Test plan

- Unit: seed each source and assert eligible items are collected.
- Unit: assert closed loops, resolved projections, and completed work are absent.
- Unit: assert overdue follow-through ranks ahead of ordinary pending work.
- Integration: collect from SQLite fixtures and MissionControlService test doubles.

# HS-125-03 — Decision commitments

- **Project:** holdspeak
- **Phase:** 125
- **Status:** done
- **Depends on:** HS-125-02
- **Unblocks:** HS-125-05, HS-125-07
- **Owner:** unassigned

## The thesis (the bar)

`DecisionLifecycleService.transition()` can accept a decision, but
acceptance creates no accountable action. The decision lives; the
commitment to act on it doesn't. This story bridges the gap: when a
decision is accepted, an optional commitment can be minted — a linked
action item with an owner and due date.

### Schema addition

```sql
CREATE TABLE decision_commitments (
    id          TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL REFERENCES decisions(id),
    action_item_id TEXT NOT NULL REFERENCES action_items(id),
    owner       TEXT,
    due_at      TEXT,
    status      TEXT NOT NULL DEFAULT 'open',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
```

Schema version: 38 → 39.

### Service changes

1. `FollowThroughService.commit_decision(principal, decision_id,
   owner, due_at)` — creates a `decision_commitments` row and a
   linked `action_items` row. The action item text is derived from
   the decision text.
2. `FollowThroughService.board()` — commitment-backed actions show
   their source `decision_id` on the card.
3. `DecisionLifecycleService.transition()` — no change to existing
   accept flow. Commitments are an opt-in step after acceptance.

### What this story does NOT do

- Auto-create commitments on accept (that's a future policy decision).
- Modify the decision model itself.

## Acceptance criteria

1. `commit_decision()` creates a `decision_commitments` row and a
   linked `action_items` row.
2. The board shows the commitment card with its source decision.
3. Accepting a decision without committing still works (no regression).
4. Schema migrates cleanly from v38.

## Test plan

- Unit: accept a decision, commit it, verify board shows the card
  with `decision_id`.
- Unit: accept without committing, verify no commitment row.
- Migration: v38 → v39 on a populated database.

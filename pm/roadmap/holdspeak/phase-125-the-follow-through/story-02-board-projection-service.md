# HS-125-02 — Board projection service

- **Project:** holdspeak
- **Phase:** 125
- **Status:** done
- **Depends on:** HS-125-01
- **Unblocks:** HS-125-06, HS-125-07, HS-125-08, HS-125-09
- **Owner:** unassigned

## The thesis (the bar)

There is no single read model that answers "what was agreed, who owes
it, and what is late?" Action items live in `action_items`, decisions
in `decisions`, loops in `cadence_loops`, project associations in
`meeting_projects`. This story creates `FollowThroughService` with a
`board()` method that joins these sources into typed lanes.

### FollowThroughService.board()

```python
class FollowThroughService:
    def board(
        self,
        principal: Principal,
        *,
        project_id: str | None = None,
        owner: str | None = None,
        state: str | None = None,
    ) -> FollowThroughBoard:
        ...
```

Returns a `FollowThroughBoard` with lanes:

| Lane | Source |
|------|--------|
| **Now** | Actions with `status=open` and `due <= today + 2d` |
| **Waiting** | Actions with `status=open` and `due > today + 2d` |
| **Unassigned** | Actions with no `owner` |
| **Overdue** | Actions with `due < today` and `status=open` |

Each card includes: text, owner, due date, source meeting ID, source
decision ID (if from a commitment), stale score (from cadence), and
deep-link reference.

### What this story does NOT do

- No commitment bridge (HS-125-03).
- No triage enforcement (HS-125-04).
- No provenance resolution (HS-125-08).
- No Desk surface (HS-125-09).

## Acceptance criteria

1. `FollowThroughService.board()` returns cards from `action_items`
   and `cadence_loops`, correctly bucketed into lanes.
2. Filtering by `project_id`, `owner`, and `state` works.
3. Cards include `meeting_id`, `decision_id` (if applicable), and
   stale score.
4. Empty board returns empty lanes, not an error.

## Test plan

- Unit: seed `action_items` with various due dates and statuses, call
  `board()`, assert lane membership.
- Unit: filter by project, assert only project-associated items appear.
- Unit: empty DB returns empty lanes.

# HS-125-07 — Write-through completion verbs

- **Project:** holdspeak
- **Phase:** 125
- **Status:** done
- **Depends on:** HS-125-06
- **Unblocks:** HS-125-09
- **Owner:** unassigned

## The thesis (the bar)

The board reads from multiple sources (`action_items`, `cadence_loops`,
`decision_commitments`), but mutations go to each source independently.
Marking an action done should atomically update both `action_items` and
its source-keyed cadence loop. This story adds write-through verbs to
`FollowThroughService`.

### Verbs

| Verb | action_items | cadence_loops | decision_commitments |
|------|-------------|---------------|---------------------|
| `done` | status=done | terminal | status=closed |
| `dismiss` | status=dismissed | terminal | status=closed |
| `snooze(until)` | snoozed_until=date | snoozed | — |
| `delegate(to)` | owner=to | — | owner=to |
| `reopen` | status=open | re-opened | status=open |

### Service methods

```python
class FollowThroughService:
    def complete(self, principal, card_id, verb, payload=None): ...
```

Single entry point. `card_id` resolves to its `action_item` and
any linked `cadence_loop` and `decision_commitment`. All updates
happen in one transaction.

### What this story does NOT do

- Add Desk UI for the verbs (HS-125-09).
- Add MCP tools for the verbs (HS-125-09).

## Acceptance criteria

1. `complete(card_id, "done")` marks the action, loop, and commitment
   as terminal in one transaction.
2. `complete(card_id, "reopen")` restores the action, loop, and
   commitment with lineage intact.
3. `complete(card_id, "delegate", {"to": "maya"})` updates owner across
   all linked records.
4. Board reflects the verb immediately after the call.

## Test plan

- Unit: each verb applied, verify all three tables updated.
- Unit: reopen after done, verify board shows the card again.
- Unit: delegate, verify owner changed in action + commitment.

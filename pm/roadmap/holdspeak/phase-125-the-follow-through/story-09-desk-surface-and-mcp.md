# HS-125-09 — Desk surface and MCP tools

- **Project:** holdspeak
- **Phase:** 125
- **Status:** done
- **Depends on:** HS-125-07, HS-125-08
- **Unblocks:** HS-125-10
- **Owner:** unassigned

## The thesis (the bar)

The Follow-Through board exists as a service. This story gives it a
Desk surface (pullout, not a feature-owned screen — Article I) and
MCP tools for programmatic access.

### Desk pullout

A Follow-Through pullout backed by `FollowThroughService.board()`:

- Lanes rendered as compact card lists (Now, Waiting, Unassigned,
  Overdue).
- Each card shows: text, owner, due date, source indicator (meeting
  icon / decision icon), stale score.
- Click provenance → opens meeting segment or decision moment.
- Inline verbs: done, dismiss, snooze, delegate, reopen — calling
  `FollowThroughService.complete()`.
- Owner and due date editable in-world (Article VII.2).

### MCP tools

| Tool | Description |
|------|-------------|
| `follow_through.board` | Returns the board (filterable by project, owner, state) |
| `follow_through.complete` | Applies a verb to a card |
| `follow_through.commit_decision` | Creates a commitment from an accepted decision |

### MCP resource

| Resource | Description |
|----------|-------------|
| `holdspeak://follow-through/board` | The current board as structured data |

All service calls flow through `@observed` and produce
`pipeline_events` with correlation.

## Acceptance criteria

1. Follow-Through pullout opens from the Desk, shows lanes with cards.
2. Inline verbs update the board without navigation.
3. Provenance click opens the source segment or moment.
4. MCP `follow_through.board` returns the same data as the pullout.
5. MCP `follow_through.complete` applies verbs successfully.
6. All MCP calls produce `pipeline_events`.

## Test plan

- Walk: open pullout, verify lanes, apply a verb, verify update.
- Walk: click provenance, verify segment opens.
- MCP: call `follow_through.board`, verify JSON structure.
- MCP: call `follow_through.complete`, verify board change.

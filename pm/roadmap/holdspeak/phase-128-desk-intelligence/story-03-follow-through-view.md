# HS-128-03 — Follow-Through view

- **Project:** holdspeak
- **Phase:** 128
- **Status:** done
- **Depends on:** HS-128-01
- **Unblocks:** HS-128-05, HS-128-07
- **Owner:** unassigned

## The thesis (the bar)

Follow-through is a readable execution board: each promise stays connected to
its owner, due state, and the words that made it, without leaving the pullout.

### What changes

1. Render `FollowThroughService.board()` as four lane groups using
   `SurfaceSection` and `SurfaceLedgerRow`.
2. Show owner chips, relative due dates, and source glyphs: `⌁` meeting and
   `◇` decision.
3. Give the focused row an inline verb bar: done, dismiss, snooze, delegate,
   and reopen.
4. Expand provenance in place and mark overdue rows with the accent border.

## Acceptance criteria

1. Four lane groups render from board data with zero generic card species.
2. Focus reveals only that row's inline verbs and each verb reaches its service.
3. Provenance expands in the same pullout and names its source.
4. Overdue state remains visible alongside owner and due date.

## Test plan

- Web: fixture all lanes, source kinds, focus state, and overdue state.
- Interaction: run every inline verb and assert the refreshed board projection.
- Service: assert board serialization carries ownership, due, and provenance.

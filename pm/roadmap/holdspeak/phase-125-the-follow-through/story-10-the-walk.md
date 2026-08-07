# HS-125-10 — The walk

- **Project:** holdspeak
- **Phase:** 125
- **Status:** backlog
- **Depends on:** HS-125-09
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Observability that isn't walked is a claim (Article IX). This story
is the end-to-end proof that follow-through works: from meeting close
through triage, commitment, board, verbs, provenance, and MCP — one
continuous walk that proves nothing gets lost.

### The walk script

`scripts/desk_walk/walk_follow_through_125.py` — a Playwright-based
walk using the existing walk harness (DeskPage, fixtures, assertions):

1. **Meeting → actions.** Create a meeting with action items (some
   ownerless, some with due dates, one overdue).
2. **Triage.** Open aftercare, verify triage queue shows the gaps.
   Assign an owner, set a due date.
3. **Decision → commitment.** Accept a decision, create a commitment
   with an owner and due date.
4. **Board.** Open Follow-Through pullout, verify all four lanes are
   populated correctly.
5. **Provenance.** Click a card's provenance link, verify the meeting
   segment opens.
6. **Verbs.** Mark one card done, one dismissed, one snoozed. Verify
   board updates.
7. **MCP.** Call `follow_through.board` via MCP, verify it matches the
   pullout state.
8. **Observer.** Query `pipeline_events` for the walk's correlation
   chain, verify all service calls were recorded.

### Screenshots

The walk captures screenshots at each step under
`scripts/desk_walk/screenshots/walk_125/`.

## Acceptance criteria

1. Walk completes end-to-end without assertion failures.
2. All four lanes populated from real meeting/decision data.
3. Provenance link resolves to the correct segment.
4. Verb application reflected in both pullout and MCP.
5. Pipeline events recorded for every service call in the walk.

## Test plan

- `uv run python scripts/desk_walk/walk_follow_through_125.py` passes.
- Screenshots captured and visually verified.

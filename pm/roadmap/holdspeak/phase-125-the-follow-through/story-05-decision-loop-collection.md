# HS-125-05 — Decision loop collection

- **Project:** holdspeak
- **Phase:** 125
- **Status:** backlog
- **Depends on:** HS-125-03
- **Unblocks:** HS-125-06
- **Owner:** unassigned

## The thesis (the bar)

`LoopCollector._collect_meeting_actions()` projects pending actions
into `cadence_loops`, but accepted decisions with open commitments
are not collected. Despite cadence supporting `meeting_decision` as
a `source_type`, nothing populates it. This story adds
`_collect_meeting_decisions()` so commitments appear in the cadence
brief.

### What changes

1. New `LoopCollector._collect_meeting_decisions()` method that queries
   `decision_commitments` with `status=open`, joins to `decisions` for
   text and meeting context, and upserts `cadence_loops` rows with
   `source_type="meeting_decision"`.
2. `LoopCollector.collect()` calls the new method alongside existing
   collection methods.
3. Idempotent: re-running collection for the same commitment does not
   duplicate loops.

### What this story does NOT do

- Change cadence scoring or staleness logic.
- Modify the brief rendering (the loop already appears in
  `CadenceService.brief()` via existing scoring).

## Acceptance criteria

1. An accepted decision with an open commitment produces a
   `cadence_loops` row with `source_type="meeting_decision"`.
2. Re-running `collect()` does not duplicate the loop.
3. Closing the commitment removes the loop from the active set.
4. Existing `_collect_meeting_actions()` behavior is unchanged.

## Test plan

- Unit: accept a decision, commit it, run `collect()`, verify
  `cadence_loops` row with correct `source_type`.
- Unit: run `collect()` twice, verify no duplicate.
- Unit: close commitment, run `collect()`, verify loop is terminal.

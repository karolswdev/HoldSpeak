# HS-171-02 — The cadence row

- **Project:** holdspeak
- **Phase:** 171
- **Status:** backlog
- **Depends on:** HS-171-01
- **Unblocks:** HS-171-03, HS-171-05, HS-171-06
- **Owner:** unassigned

## Problem

The scheduler exists (cadence/scheduler.py) but nothing runs unattended
on the owner's desk: cadence_loops 0, cadence_nudges 0, and
`next_evaluation_at` is null on all his watches (schema.py:2324). The
conductor runs the plugin queue loop and the cadence loop as two serial
daemon threads (web_runtime.py:519-534); a crash in one halts the other.
The arc says: "the scheduler stamps next_evaluation_at and the
unattended sweep actually runs on a cadence he sets in one row."

## Scope

- In:
  - The scheduler stamps `next_evaluation_at` after each evaluation
    (the column exists in the schema; the write is missing).
  - One cadence setting: the sweep interval ("every 15 min while I
    work, hourly otherwise") exposed in Settings as a single row
    built to the HS-171-01 artboard.
  - The five conductor loops (plugin queue, cadence tick, recording
    tick, watch refresh, transcription warm) become parallel threads
    with independent try/except boundaries; a crash in one logs and
    continues, never halts the others.
  - The cadence tick calls `refresh_due_watches` (the unattended
    sweep) on the interval the owner set.
  - Every tick is receipted through the pipeline observer (Article
    XI.2).
- Out:
  - New cadence loop types.
  - External effects from the sweep (reads only; Article V.1).
  - The UI for the cadence row beyond the single Settings row (the
    shade integration is HS-171-04).

## Acceptance criteria

- [ ] `next_evaluation_at` is stamped on watches after the sweep runs;
      verified by reading the schema row (Article IX.1).
- [ ] The cadence setting is exposed in Settings as one row matching
      the HS-171-01 artboard; the owner can change the interval.
- [ ] The five conductor loops run in parallel threads; killing one
      (simulated by raising in a test) does not halt the others.
- [ ] `refresh_due_watches` runs on the cadence interval; verified by
      a rig that asserts the call count over time.
- [ ] Every tick leaves a pipeline_events receipt (Article XI.2).
- [ ] Zero egress (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k cadence_row`
  - The scheduler stamps `next_evaluation_at` after evaluation.
  - Parallel conductor loops: one crashes, the others continue.
  - The cadence setting round-trips through the API.
- Integration: the rig boots a hub, waits for one tick, reads the
  `next_evaluation_at` column and the pipeline_events receipt.
- Manual: the owner's desk shows the cadence row in Settings.

## Notes / open questions

- The five loops named in the conductor: plugin queue
  (web_runtime.py:519), cadence (web_runtime.py:529), recording tick
  (web_runtime.py:231), and two more to identify in the startup path.
  If there are fewer than five, the story covers what exists.
- The existing `CadenceMixin._cadence_tick_once` already calls
  `_push_due_to_telegram` and `_maybe_push_daily_brief`
  (runtime/cadence.py:57-58); the sweep addition fits here.

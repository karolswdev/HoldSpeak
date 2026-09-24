# Check — Muad'Dib, 2026-09-24

Local Claude check of the narrow breakage case amendment. Read-only check; no worker or product changes.

Check complete. Report follows in the TWO-BRAINS §3 shape. I made no edits; the record under `checks/` is owed by whoever acts on this next (TWO-BRAINS §3, "a check is recorded in the tree").

**VERDICT: RATIFY-WITH-CONDITIONS**

**FINDINGS**

1. **Astra's diagnosis is correct.** The retained run's producer clock read `advance_days=0 now=2026-09-24T16:15:12` and `advance_days=1 now=2026-09-25T16:15:14` with `tz: null` (`assets/story-03-shots/real/browser/20260924T221450Z-…-1440/observation.json`, provenance.clock). The day-one brief window is 2026-09-23T17:00 to 16:15; the next-day brief `brief-a98dc6aa…` has `period_start 2026-09-24T17:00:00` and `sections.broke: []`. The two failed reads at 16:15 fall before the 17:00 close (`holdspeak/services/monday_brief_service.py:163-176`, `:557-575`). The face predicate passed on the decision row alone. No scoped-breakage identity was proved.

2. **The mechanism was not missing; it was bypassed.** The case already carries the precondition "run with rows/run_breakage_case.py: process-only TZ selects an evening hour…" (`docs/internal/philo/graph/atlas-phase3.json`, case `s5_next_day_brief_with_breakage`, preconditions[1]). The rig records prose preconditions as "recorded, not checked" (observation.json preconditions[1].note), and the command in `evidence-story-03.md:520` calls `graph_walk.py` directly. Phase 4's proof used the wrapper (`docs/internal/philo/phase-4/rows/run_breakage_case.py`): it picks `Etc/GMT±N` so the local hour is 20, asserts `17 <= hour < 23`, sets `TZ` before spawning, and exits nonzero otherwise. The rig captures `TZ` into provenance (`scripts/graph_walk.py:321`) and the hub subprocess inherits the environment (`scripts/graph_walk.py:1466-1480`), so the seam already reaches the producer.

3. **A fixed `TZ=UTC` is sufficient for this session but is time-dependent.** It holds only between 17:00 and 23:59 UTC, so today it is good for roughly ninety more minutes and the rerun prerequisite lives in the wall clock. The existing wrapper is reproducible at any UTC hour with no clock framework. Tenet 1 favors the wrapper over both a hardcoded zone and a new rig option. Weekday is not a caveat: `compute_window` puts any event after 17:00 local into the next day's lookback on every weekday, including Friday to Saturday and Sunday to Monday.

4. **"Blocked, never pass" already has a home in the comparator, not a check step.** `scripts/philo5_pairs.py:1019-1033` marks `breakage_scoped_ids` as `blocked` when the final brief's broke list is empty. Astra's note says equivalence "fails" missing; it blocks, which is the right semantics. The message does not name the overlap or the clock, so a reader cannot tell a rig prerequisite from a product gap.

5. **The unfit run is already recorded as a pass.** `evidence-story-03.md:520-533` lists the 22:14:50Z capture with exit 0 and `VERDICT: pass`. Keeping it unselected in the pair index is not enough; the evidence file reads as proof.

6. **`capture_match` exists only on `op` steps** (`scripts/graph_walk.py:3207-3260`); the `api` step reads `capture_path` alone (`:3345-3352`). The browser case cannot capture the failed item's id "by text" without a small rig extension. The existing setup check already pins `sections.broke.0.text` to `DecisionLifecycleService.get_decision failed`, so `capture_path: sections.broke.0.id` is enough and adds no rig code.

7. **The shelf write is sound.** `shelve` accepts any id in `monday_brief_items` including a broke row (`monday_brief_service.py:1164-1193`); `shelf()` with no brief id reads the latest brief (`:1195-1207`), so "final shelf empty" reads the new brief while the old brief's shelf rides in `before/after.brief_db`, which the comparator already diffs (`philo5_pairs.py:1000-1012`). The headless observation carries `brief_db` too. Ack placed after the day-one brief and before the same-day second Generate also proves the same-day brief keeps its shelf. Pre-fix, a source-only id would have carried the ack across briefs, so the addition genuinely strengthens the Phase 4 invariant rather than evading it.

**CONDITIONS**

1. Run the three cases (1440, 393, `.op`) through the existing wrapper, generalized by case, viewport, headless flag and out dir. Do not hardcode `TZ=UTC`. If Astra rules for a fixed zone anyway, the atlas precondition must state the 17:00 to 23:59 window in that zone.
2. Replace the prose precondition with one that names the wrapper, the hour window, and the rule "outside the window the run is BLOCKED, never PASS".
3. In the comparator, add an explicit overlap check that reads `provenance.clock.producer_clock_reads[0]` and `provenance.clock.tz`, and returns `blocked` with a message naming the producer clock when the first reading's hour is before 17. Keep `breakage_scoped_ids` as it is.
4. Add a note under the 22:14:50Z capture in `evidence-story-03.md` saying it is unselected and why, with the clock reads quoted. Do not delete it.
5. Use `capture_path: sections.broke.0.id` for the browser case, or extend `capture_match` to `api` steps with a fence. Either is lawful; the first is smaller.
6. Fence law still applies: show the new comparator overlap check turning `blocked` on the retained 22:14:50Z observation before it passes on the new runs.

**MISSED**

1. One 404 read lands twice in "broke": `DecisionLifecycleService.get_decision failed` and `PrimitiveService.get_decision failed`, both from the same `philo402-deliberately-absent` read. The observer records the wrapper and the primitive as separate failures. The comparator tolerates it, but the owner's brief would say "2 things broke" for one thing. Tenet 4 debt to record, not this story's fix.
2. The wrapper writes into the phase 4 assets dir; unparameterized reuse would put phase 5 runs in phase 4's tree and trip the orphan rules.
3. The `.op` sibling has no preconditions at all, so the wrapper condition must cover it explicitly.

**TUESDAY:** No face or product change. The owner's real Tuesday brief still looks back to Monday 17:00 as it did in Phase 132; this amendment only makes the rig honest about when it can prove that.

**UNKNOWN**

1. Whether `Etc/GMT` zones are present in this machine's tz database under `uv run`; Phase 4's logs show they were on 2026-09-24 07:2x UTC, and I did not re-run anything.
2. Whether the LAN engine is up right now for the three real-engine runs; I did not probe it.
3. Whether `HOLDSPEAK_EVIDENCE_WRITE=1` under the wrapper still lands the shots under phase 5; I read the wrapper, not a run.


## Astra response

Accepted all six conditions. The existing wrapper precondition was missed in the direct invocation. The phase5 wrapper reuses its process-only timezone method with explicit output paths; it does not move the machine clock. The case adds real old-item Ack and retains the original selector/trigger. The comparator must block absent overlap and compare old shelf to the new empty shelf. No product change is authorized by this amendment. Duplicate observer failures for one missing decision are recorded for PHILO-5-04.

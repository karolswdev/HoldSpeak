# PHILO-13-04 — Astra H-A3 lane record, r2

**Status:** DRAFT — UNCHECKED — awaiting Muad'Dib. Story 04 remains in-progress until H-A3 and A3-W are both merged.

LANE: Data + truth, Phase 13 story 04 (H-A3 only). Worktree `/Users/karol/dev/tools/wt-philo-13-a3h-astra`, branch `feat/philo-13-a3h-astra`; this is a separate PR for H-A3.

OUTCOME: `/api/meetings` list and search rows now carry `has_summary`, computed from the latest persisted `intel_snapshots.summary` and exposed through the existing `MeetingSummary` projection. The field is independent of current configuration and run status. A3-W owns the visible stored-summary rail and follows after this data handoff merges.

PROOF:

- Focused collection: **8 tests collected** across `tests/unit/test_philo13_a3h_meeting_summary.py` and `tests/unit/test_philo3_summary_detail.py`. [Collection output](assets/story-04-a3h/r2-focused-collection.txt).
- Focused run: **8 passed in 3.98s**, with isolated HOME. [Run output](assets/story-04-a3h/r2-focused-green.txt). No full suite ran.
- Both new fences were run separately against base `27b915538` with the same real-producer test module and isolated HOME. The persisted-config/run-status test and the list/search no-text-leak test each failed before the change at the explicit `rows[summarized_id]["has_summary"]` read with `KeyError: 'has_summary'`. [Config/status red](assets/story-04-a3h/r2-baseline-config-status-red.txt), [text-leak red](assets/story-04-a3h/r2-baseline-no-text-leak-red.txt).
- The green fences mint both meetings through the real import, deferred-admission and summary producers. One persists `The team reviewed the budget.`; the other remains queued without a snapshot. They read the real detail service and FastAPI list route, then issue an actual search request. The first test persists disabled settings with `Config.load/save`, changes the stored run status to `disabled`, and still requires list `has_summary=true`; both tests require false for the unsummarized row and ensure list/search never serialize the exact stored summary text.
- No face or CSS changed in H-A3; no screenshot applies to this data-only handoff.

LEDGER: The scalar query and detail loader both select the newest snapshot by `timestamp DESC`. The flag checks that this summary is non-empty after trim; it does not infer storage from `intel_status`, engine configuration or a UI response. The summary detail fixture now carries the boolean in its list cases so the existing real-producer wire comparison remains exact.

AMENDMENTS: Story 04 now names H-A3 and A3-W as separate acceptance steps and remains in-progress. `current-phase-status.md` records this handoff, the data-file/test ownership and the signed r2 conditions for H-A1, H-A2 and B0, including the B0→B2 rerun/F2 gate. The A3 PR is marked DRAFT and will say `r2 — awaiting Muad'Dib`.

UNKNOWN: A3-W's face rail, Muad'Dib's check, merged-main behavior and the owner's desk sitting are not verified. The handoff does not close Story 04 until both halves merge. No real send ran.

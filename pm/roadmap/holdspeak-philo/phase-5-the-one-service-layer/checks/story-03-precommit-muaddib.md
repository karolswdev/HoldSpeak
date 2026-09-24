**VERDICT: RATIFY-WITH-CONDITIONS** — the artifacts authenticate; guarded done, commit and PR push may proceed once the two small record conditions below are paid. No merge.

**FINDINGS**

1. **The r3 fence condition is paid by an honest red.** The retained old op runs at 22:28:57Z and 22:30:16Z stopped at setup, so no final next-day brief exists on that side. The comparator's real branch at `scripts/philo5_pairs.py:1288-1292` reads `blocked` for `next_day.breakage_causes` on the full old pair, which is the correct semantics and was expressly allowed by the r2 check ("fail or blocked"). The diagnostic red then calls the same two functions the real branch uses, `_breakage_text_detail_projection` and `_compare_exact`, on two real retained payloads: the old op's day-one brief and the browser's final brief. It FAILs on the 1-versus-2 cause set. Nothing was synthesised or promoted into a fake final reading, and it is labelled diagnostic in `pair-fences.txt`. The new pair passes with both exact causes present. Condition paid.
2. **Originals are never edited.** `verify_pair_fences.py` deep-copies pair entries, mutates in memory, and `verify_pairs.py` re-hashes every one of the 62 runs in `runs.json` against disk. Every pairs-input path and every faces.json observation is a run marked selected; no selected run is missing from disk and none on disk is unlisted except the five CAL calibration observations under `fences/op-calibration/`, which are correctly outside `runs.json`.
3. **The mutation reads the real field.** `last_op_read` returns `domain_response`, not the `response` alias, so the title-skew red proves the comparator reads what the producer wrote.
4. **Shelf refusal is recorded as ruled.** The refused pair carries `refusal_origin: transport_schema`, `registry_reached: false` on the op side and `service_registry`, `true` on the HTTP side. The phase status names it as PHILO-5-04 debt and excludes it from exit criterion 1. C1–C5 of that counsel paid.
5. **Breakage window and source conditions paid.** The wrapper touches only process `TZ`, refuses outside [17,23), both browser widths and the op run show `BREAKAGE_WINDOW`. The op case replaced the MCP read with the identical HTTP 404 seed, its `why` names `decisions.py:58-61`, the precondition states this is not a parity claim, and every subsequent step is canonical op. The 22:14:50Z pass carries the required unselected note with the clock reads quoted.
6. **Headless-chart conditions C1–C7 paid in tests.** Map fenced against live `exposure` (`test_philo5_graph_op.py:51`), resource envelope and resource refusal on a real hub (`:211`, `:346`), a1 pairs by `error_contains`, `restart_required` rejects missing flags (`:266`), engine assignment via concierge API steps in every summary sibling, replayed pairs carry receipt identity, seven CAL cases red-then-green.
7. **Counts verified.** 20 pairs (18 + 2 replay), all pass. 33 browser + 20 op selected, 9 unselected with reasons. 219 collected / 219 passed. atlas.json 81 cases, atlas-phase3.json 31, no archived flag. Graph check exit 0 with the 14 pre-existing subtype notes. No `holdspeak/` product file and no `pm/roadmap/holdspeak/` path in the diff.

**CONDITIONS**

1. Face verdict honesty in `faces.json`: the S4 393 entry has `face_verdict: null` and `glass_review: unverified-rendered-content`, which is correct. Keep the lane report's "PASS for retained face cases" row wording as is but add one clause naming that 10 of 33 browser observations carry no face verdict (protocol-only), so a reader cannot read 33 face passes. One sentence, no rerun.
2. Record in the lane report LEDGER that the five CAL calibration observations under `assets/story-03-shots/fences/op-calibration/` are fixture-hub records, intentionally outside `runs.json` and the hash check, so a later orphan sweep does not mistake them for unindexed product observations.

**MISSED**

1. The registry-reach unit fence (`test_real_hub_op_reaches_the_bound_registry`) composes the real root in-process and wraps `root.operations.invoke`; reach through the spawned-process hub rests on the actual op observations, which is sufficient but should be said in the story's Test plan wording.
2. The op `meeting.import` records no fixture sha256 on the step itself (headless-chart C8); the hash exists elsewhere in the observation and the browser fixture step records it. Low cost, note for 5-04.

**TUESDAY:** Unchanged for the owner. No face moved; the two-broke-rows-for-one-read and the SAVED-on-failed-import and the zero-decided toast remain his debts, correctly parked in 5-04.

**UNKNOWN:** I did not re-run any rig case, hub or the scoped suite; I read captured outputs, hashes and code paths only. Whether the LAN engine is still up is unprobed. Astra's glass readings are Astra's; no owner has seen a shot.


## Astra — conditions paid, 2026-09-24

1. Added the explicit face counts to the proof table. Recount of faces.json gives **33 observations, 20 face verdicts, 13 null face verdicts**. Counsel's literal count of 10 was an arithmetic error; the condition's intent is paid with the verified 13. S4 at 393 remains null / unverified-rendered-content.
2. Added the calibration records to LEDGER as fixture-hub evidence outside runs.json and its hash check. There are **six** records in fences/op-calibration (success, refusal, unresolved, never-completes, headless-face-block, restart-retains-read), plus the separate absent-op control in fences/op-removed. Counsel's literal five is corrected by this file census. No calibration record counts as an actual atlas run.
3. Paid MISSED 1 in the Test plan: the registry wrapper test composes the real root in-process; spawned-hub reach is evidenced by actual /api/mcp op runs. Paid MISSED 2 as a low-cost PHILO-5-04 record note: import fixture SHA256 is in observation provenance, not copied onto the op step. No product or rig change follows from that note.

The narrow corrections are factual counts and record wording, not a change to the settled design. The 219-test run and final pair fences remain the validation for the unchanged source. Guarded done, commit, push and PR are authorized by the verdict after these record conditions; merge remains held.

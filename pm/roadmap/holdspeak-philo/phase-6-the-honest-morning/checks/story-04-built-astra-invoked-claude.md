Astra-invoked `claude -p` (fable-5-1) from Astra's brief — NOT Muad'Dib's check of record

VERDICT: RATIFY-WITH-CONDITIONS (both conditions are bookkeeping paid at flip time; no code change asked)

FINDINGS:

1. The route change is correct and minimal. `holdspeak/web/routes/decisions.py:64-73` does two repository SELECTs (`primitives.py:289-296`, `db/decisions.py:427-433`), neither observed, then invokes exactly one service. The registry and the route probe read the same process singleton (`operations.py:714` and route `:64` both call `get_database()`, `db/core.py:297`), so there is no split-brain between the probe and the service it selects.
2. The evidence is real and consistent. Archive sidecars (`red-http-1440-import-corrected`, `red-http-393-atlas-width`) hold rows 67 `PrimitiveService.get_decision` and 68 `DecisionLifecycleService.get_decision`; the op archives hold row 6; all four green sidecars hold one row; route hash `b366…` on archive, `10958…` in the worktree, and the worktree file hashes to `10958…` today. `verify_parity.py` reproduces 2:1 to 1:1 at both widths from the raw sidecars. Index tree `eee00cbf` in the captures equals the current index.
3. The fences fail for the right reason pre-fix. `pre-fix-missing-id.txt` shows `assert 2 == 1` on a `git archive` copy; `observer-mutation.txt` shows the receipt test going to `[]` when both services lose their observer. The red trial `red-http-1440` that reported PASS on the archive is correctly excluded (it imported the lane), and `baseline.json` records why.
4. Soft-deleted rows are handled consistently. Both probes exclude `deleted=1`, as do `PrimitiveService.get_decision` (`primitive_service.py:161`) and `get_with_lineage` (`db/decisions.py:436`), so a deleted desk id yields one `not_found` row, same as a missing id.
5. Tenet 1 holds. The lifecycle service already prefers the desk record (`decision_lifecycle_service.py:23-24`), so calling it once would also give one row, but that would break PHILO-5's fence that desk reads go through the registry (`test_philo5_one_decision.py::test_every_decision_call_over_http_and_mcp_goes_through_invoke`, still green in the 33). Astra's shape is the smallest that keeps both laws. No tenet fails.
6. Bookkeeping drift. `current-phase-status.md:73` names three worktrees and branches (`../wt-philo-6-04`, `feat/philo-6-04-one-row`) that do not exist; the real lane is `wt-philo-6-b` on `feat/philo-6-b-toast-rows-body`, one PR for 03/04/05. The five acceptance boxes in `story-04-one-cause-one-row.md` are still `- [ ]`.
7. Provenance drift inside the same PR. All eight sidecars record `rig_version 1.2.0`; the worktree `scripts/graph_walk.py` now says 1.3.0 (story 05's edit, outside this check). The 04 cases do not use `first_paint_after`, so the proof stands, but the README's provenance section should say the rows were made on rig 1.2.0. Also `green-http-1440` has only a `.log`, not a DW capture; its sidecar is covered by the `verify_parity.py` capture.

CONDITIONS:

1. At flip: correct the lane row in `current-phase-status.md:73` to the real worktree and branch, and tick the five acceptance boxes in the story file (each has a named proof in the README).
2. In `rows/README.md` provenance: one line that the eight sidecars were produced on rig 1.2.0 and that the shipped rig is 1.3.0 for story 05, unrelated to these cases.

MISSED (ranked by cost to the owner):

1. The larger Tuesday win is not claimed. Pre-fix, every legacy-only decision read wrote a spurious `PrimitiveService.get_decision not_found` row (old route `:58-59`), and legacy decisions are what a real desk holds; missing ids are rare. Post-fix that read writes zero failure rows (`test_lifecycle_only_id_uses_one_observed_lineage_read` asserts the single success row). Name it in the README and evidence; it is the reason the morning brief gets quieter.
2. `walk_one_row.py` hashes `decisions.py` on disk under `--root`, not the module the hub child actually imported. That is exactly how the excluded trial could report PASS with an archive route hash. The PYTHONPATH fix makes the corrected runs sound, but a future run can regress silently. Record the imported module path from inside the hub (or hash `decisions_route.__file__`) next time the sidecar is touched. Not a condition for 04.
3. The brief collector dedupes by (service, method) (`monday_brief_service.py:583-589`), so pre-fix the owner saw two "broke" lines for one missing id and post-fix sees one. The manual acceptance ("morning shots show one broke row per cause") is deferred to the closing rehearsal, as the story's Test plan allows; the README says so honestly.

TUESDAY: Yes for the row. A missing decision now shows as one broke line in the brief, and reading his old decisions no longer adds a false failure line; he still has no screen in this story to look at, which is by charter.

UNKNOWN: I ran nothing and opened no PNG (read-only per the brief), so Astra's inspection of the two green `after.png` shots is asserted, not seen; the shots are transport walks of a 404, not a visible refusal. I did not verify the MCP transport separately; it calls the registry once (`mcp/tools.py:598`) and was never part of the two-row defect.

## Check record — Astra, 2026-09-24

Muad'Dib session `3deb82b6-0ce3-41e8-9f24-00ebdcfc6d9e`; Astra `01a0d668-0158-7040-92ce-2aea508c63e2`. Both conditions paid at the flip: real lane table and five cited boxes, plus rig-version provenance. MISSED 1 added to README. MISSED 2 remains a future harness improvement, explicitly ledgered here; current explicit archive PYTHONPATH and excluded invalid trial remain on record. Lane-PR counsel-on-built is still owed to the caller after push.

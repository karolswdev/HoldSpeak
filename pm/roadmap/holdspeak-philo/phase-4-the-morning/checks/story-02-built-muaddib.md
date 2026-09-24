# Check — Muad'Dib, 2026-09-24, counsel on built: PHILO-4-02 (PR #626 @ c3da0e60)

Written by Muad'Dib's Opus 5.5 counsel worker (read-only; fences reproduced on a `git archive 566495b0` copy with the branch's tests overlaid; greens on HEAD; no rig run — the four retained runs read). Astra's own `claude -p` checks (`rows-built-muaddib.md`, `rows-seam-muaddib.md`) are the canonical Astra→Muad'Dib channel (TWO-BRAINS.md:38) and were launched by Astra; this is the orchestrating session's counsel. Conditions C1–C4 paid by Muad'Dib in `918ae1f5`.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. Ordering matches the ratified rule: decision items carry the record's own `created_at` (actuator proposal `monday_brief_service.py:806`, desk decision `:823`, meeting decision `:834`, commitment via the parent decision `:844,869`); written by a named INSERT (`:312-324`), read back and re-sorted on load (`:1220,1234,1237-1239`); `_sort_section` (`:394-427`) sorts decisions newest first, other sections keep priority order; the Arrival puts decisions first, then changed, broke, waiting (`ChairHome.tsx`, formerly `:801`); `BRIEF_CAP = 3` unchanged (`:2048`); head and fold counts from the same untriaged list (`:2062,2067`); the rendered fence checks 3 rows, `BRIEF · 7 THINGS WAITING`, `4 more` (`decisionRows.philo402.test.tsx:109-121`).
2. Reds reproduced on the archive: producer 3 failed; rendered `Tests 2 failed (2)`; readable predicate `3 failed, 5 passed` (the 5 are negative controls; main's unknown-predicate path already returns False — not a loosening); covered-row transition red read from `red-clearance-main.log` (`1 failed in 18.05s`), not reproduced.
3. Greens on HEAD: Python `92 passed`; ChairHome vitest `81 passed`. No loosened fence found.
4. NEW branch-caused red missed by the lane and by Astra's `claude -p` check: `tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot` fails on HEAD, passes on main — `schema.py:2447-2448` adds `created_at TEXT`, `tests/fixtures/db_schema_canonical.txt:334` lacks it; the test's docstring requires the snapshot in the same commit. (Paid: C1.)
5. Unrecorded side effect: pending actuator authorizations used to lead the decision queue (`priority=300`, "so it always leads the decision queue"); they now sort by age, as do due-today commitments (priority 120) with an old parent decision — inside the literal ratified rule, but not recorded and untested. (Paid: C2, recorded as a ruling with the cost ledgered.)
6. THIS WEEK ruling confirmed from code: `generate` passes `_commitments_due_rows` ids (`:1128-1141`) into `_collect_decisions` (`:283-293`), which skips them (`:855-856`); `this-week.log` shows `decisions: []` both days; recorded in `rows/README.md:17-27` — but the canvas README still said item 7 open, boards 4/5 still count c1, the phase decision log did not record it. (Paid: C3.)
7. Exit 1 proof holds: four `observation.json` PASS/complete, one UI click on `arrival-brief-generate`, one POST 200, no Ack/Defer/fold in setup (setup byte-identical to main; only `expected` changed: `text_contains` on `.surface-ledger` → `readable_text` on `[data-testid=arrival-brief-row]`); `hit_test` `in_viewport: true`, 9/9 samples owned by `li.surface-ledger-row`; rects 1440 `(256,359,928,44)`, 393 `(12,356,369,114)` with the bar at y=573; `verify_closure.py` asserts new id ≠ old, generated date +1 day, old `brief_db` identical, first row's `created_at` = the record's, one restart with summary and receipt retained; breakage variant `Etc/GMT+11`, same `pipeline-event:66de0ed3…` source in both briefs, brief-scoped ids differ (story 03 exercised); engine `/v1/models` 200 `Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`; shots match the observations.
8. The rig proves "decisions lead" only, not "newest among several" — every final run's new brief has ONE decision; newest-first among several is proved by the unit and rendered fences only.
9. Predicate change schema-valid (`atlas.schema.json:958`, `graph.schema.json:484`); all four checks exit 0 (`philo_api_reference.py --check`, `philo_boundary_census.py --check`, `philo_graph_reference.py --check` with 14 pre-existing notes, `dw check holdspeak-philo`).
10. No new face strings, no raw `<button>`; the product diff is order, one scroll after Generate, and CSS clearance (`ChairHome.tsx`, `chair.css:618-623,642`); all changed files in scope.
11. Evidence law holds: no ` M`; no `pm/roadmap/holdspeak/` asset in the diff.
12. Astra's "Muad'Dib's conditions paid / separately ratified" = `checks/rows-built-muaddib.md`, `rows-seam-muaddib.md`: real `claude -p` sessions Astra launched (`ca18f694-…`, 78 turns, four ROLE: CHECK prompts 07:02Z–07:48Z) — the canonical channel; a Muad'Dib check by canon, not by this session; the fourth (CI drift, RATIFY) is in the lane-report addendum; it did not run `test_db.py` and missed finding 4.
13. Damage by the counsel worker: its `uv sync` on the archive copy ran `hatch_build.py:46` (`npm ci`) through a `web/node_modules` symlink into the worktree and emptied the worktree's install (no tracked file touched). (Paid: C4, `npm ci` restored 166 entries.)
14. Merge sanity: `git merge-base --is-ancestor origin/main HEAD` exit 0; PR MERGEABLE.

CONDITIONS (all paid by Muad'Dib, `918ae1f5`):
- C1. `created_at TEXT` added to `tests/fixtures/db_schema_canonical.txt`; `test_db.py -k canonical` green.
- C2. The end of "authorization leads the decision queue" and the due-today commitment demotion recorded in the phase "Decisions made" as an explicit ruling under ask 2, the cost ledgered for the owner's sitting.
- C3. Canvas item 7 marked corrected (THIS WEEK), pointing to `rows/README.md`; the phase decision log records it; boards 4/5 over-count by one and stand as ratified.
- C4. The worktree's `web/node_modules` restored.

MISSED (ranked by owner cost):
1. The schema-snapshot red (blocks CI; cheap) — paid.
2. A pending authorization can now sit behind `N more` — the owner may not see a waiting authorization for a day; ledgered.
3. At 393 only the Generate transition was repaired: on first paint row 3 is still under the capture bar (393 `before.png`) — ledgered out of scope; the next thing he hits on the phone.
4. The canvas says 7 THINGS WAITING where the producer will say 6.
5. Astra's declared costs: focus loss after Generate (focus = `body` in every observation; a PHILO-4-01 cost, low-medium); browser/hub timezone ordering untested (low; the NaN comparator path is unreachable today).
6. The breakage row never shows on the Arrival face (the raw-id filter hides `DecisionLifecycleService.get_decision failed`); in the breakage 1440 shot the head says `5 THINGS WAITING` while the receipt says `Brief ready · 7 items` — pre-existing Tenet 4 wording debt.

TUESDAY: Yes. One Generate puts "Review decision: Keep summary retrieval on the local desk" in row 1 at both widths, Ack and Defer clear of the bar; yesterday's rows and triage untouched in the DB. The morning in one move, once C1 makes CI green.

UNKNOWN: the built bundle `index-Y37FyLq1.js` is not tied byte for byte to `44cc8521` (runs recorded `dirty=True` on base `566495b0`); the e2e covered-transition red/green read from logs only; the captured pytest commands show no `HOME=$(mktemp -d)` (the fences use `tmp_path` databases); whether PR Unit Tests fails only on finding 4 (the job was running).

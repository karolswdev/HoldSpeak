# Inventory D — red tests and repo clutter

Date: 2026-10-03. Base: `origin/main` @ `6ccfa4e0d`. Worktree: `/Users/karol/dev/tools/wt-inv-d` (detached, read-only pass; no tracked file changed).
Machine note: load average was 77 during the runs (sibling inventory lanes). Wall times are slow. Each failure was run again alone to separate flaky from real.
Python note: local `uv run python` is 3.14.2. CI uses 3.12 (`.github/workflows/test.yml:24`).

## 1. Red tests

### 1.0 Totals

| Run | Result | Wall | Alone re-run |
|---|---|---|---|
| FAST (`-m "not slow"`, unit+integration+critical+web+mcp+uat) | 30 failed, 13228 passed, 38 skipped | 8 min 14 s | 29 fail again, 1 passes |
| tests/e2e (no test_metal) | 31 failed, 4 errors, 673 passed, 79 skipped, 4 xfailed | 15 min 15 s | 27 fail + 4 errors again, 4 pass |
| Web vitest baseline | 3263 passed, 0 failed. VERDICT baseline-subset, zero branch-new. 4 HEALED | 3 min 8 s | — |

By class (FAST + e2e, 65 red):

| Class | FAST | e2e | Sure? |
|---|---|---|---|
| STALE TEST (product changed on purpose) | 24 | 11 | FAST: yes, read the code. e2e: from the error text only |
| PRODUCT BUG (product or doc breaks its own rule) | 4 | 5 likely | FAST: yes. e2e: likely, not proven |
| FLAKY (passes alone) | 1 | 4 | yes |
| ENVIRONMENT | 1 | 0 | likely (Python 3.14 vs 3.12; not run on 3.12) |
| NOT CLASSIFIED (fails alone; cause not read) | 0 | 15 | — |

### 1.1 FAST — 30 failures, by cause

| # | Tests | Cause | Class | Size | Fix |
|---|---|---|---|---|---|
| F1 | `tests/unit/test_hs175_calendar_sources.py` ×6 (`TestCalendarSourcesRoute` ×2, `TestSourcesPayloadClocks` ×3, `TestDstEdgeSources` ×1) | The test double `_FakeEvent` (test file line 210) has no `attendees`. The product now writes `event.attendees` (`holdspeak/db/calendar_events.py:128`, added 2026-10-03 "include meeting attendees in list rows"). | STALE TEST | S | Add `attendees = []` to `_FakeEvent`. |
| F2 | `tests/unit/test_hs172_people_sources.py` ×5 (`TestBriefEnrichment` ×4, `TestNoPronounInWire` ×1) | The test makes its own `meetings` table (line 70) with no `parked` column. The product reads `m.parked` (`holdspeak/services/people_service.py:581`, `:858`). | STALE TEST | S | Add `parked INTEGER DEFAULT 0` to the test table, or build the DB with the real `Database`. |
| F3 | `tests/integration/test_live_action_item_triage.py` ×2 (`TestLiveFirstResolutionOrder`) | The double `_ArchiveSpy` (line 39) has no `_connection`. The product calls `db._connection()` (`holdspeak/services/needs_you_aggregate.py:750`). | STALE TEST | S | Give the spy a `_connection`, or use a real temp `Database`. |
| F4 | `test_phase143_routing_authority_census.py::test_ast_census_is_exact…`; `test_phase143_inference_capability_census.py` ×2 | The tests pin `file:line` sites. The lines moved (`holdspeak/mcp/tools.py:1020→1022`, `:1156` new, `:653`, `:659`). `pm/STATUS.md` already lists these as open work. | STALE TEST | M | Make the three census tests line-free (same change PR #763 made for the other maps), or re-anchor. |
| F5 | `test_philo3_summary_detail.py::test_summary_wire_fixture_matches_real_producer_states`; `test_philo6_01_import_badge.py::test_empty_vtt_import_leaves_import_failed_on_the_wire` | The vitest fixture is older than the producer. The producer now adds `attendees` to list rows. | STALE TEST | S | Write the fixtures again (`PHILO6_WRITE_FIXTURE=1`, and the philo3 equal). |
| F6 | `test_desk_locks.py::test_the_front_door_is_the_desk_with_the_guard`; `tests/integration/test_web_setup_route.py::test_dashboard_owns_first_value_without_redirecting` | Both look for the text `setup?.arrival_required` in the Desk route source. The source now uses `arrivalRequired`. | STALE TEST | S | Change the text the tests look for, or test the behaviour. |
| F7 | `tests/integration/test_web_history_archive.py::test_history_keeps_approval_and_export_governance` | Looks for `ConfirmVerb` in the Meetings face source. The face now has a `Park` Button (Phase 13 parking). | STALE TEST | S | Assert on the Park verb. |
| F8 | `test_decisions.py::test_meeting_delete_severs_source_without_deleting_decision` | `delete_meeting` now parks (`holdspeak/db/meetings.py:1282-1287`: `UPDATE meetings SET parked = 1`). The row stays, so `source_state` stays `linked`. The test expects `source_deleted`. | STALE TEST | S | Assert the parked result. Note: the `source_deleted` trigger (`holdspeak/db/schema.py:432`) now has no caller I found — unknown if that is wanted. |
| F9 | `test_philo9_compat.py::test_the_http_routes_keep_their_envelopes_and_statuses` | `/api/projects/{id}/updates` now also returns `latest_published_update_id`. The test wants exactly `{updates}`. In `pm/STATUS.md` open work. | STALE TEST | S | Add the key to the expected envelope. |
| F10 | `test_graph_walk_calibration.py::test_the_ui_vocabulary_is_closed_and_blocks_before_anything_fires` | The rig vocabulary gained `world_context_menu` and `set_input_files`. The test has the old closed set. | STALE TEST | S | Add the two verbs to the expected set. |
| F11 | `test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link` | Four docs link to generated files that left git today ("generated docs out of git"): `docs/API_REFERENCE.md:9`, `docs/SECURITY_MODEL.md:166`, `docs/generated/DOCUMENTATION_AUDIT_REPORT.md:88`, `docs/internal/philo/README.md:36`. | PRODUCT BUG (docs) | S | Change the four links to the command that makes the file, or drop them. |
| F12 | `test_interior_canon_guard.py::test_no_left_border_rails_in_web_css` | Five `border-left` rules against HS-101 canon rule 6: `web/src/desk/components/chrome-menus.css:727`, `:809`; `dock.css:408`, `:655`; `pullout.css:759`. | PRODUCT BUG | S | Use the aerogel inset, or allow-list the one `border-left-width: 0`. |
| F13 | `test_ux_canon_ratchet.py::test_ratchet` | `raw-ids` went 17 → 18. PeopleCore 12 → 13. | PRODUCT BUG | S | Remove the new raw id in PeopleCore, or write the ceiling again if it is wanted. |
| F14 | `test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift` | `web/src/desk/windowSend.tsx:295`: a failure text does not name the kept work, the next action and the destination. | PRODUCT BUG | S | Fix the copy at line 295. |
| F15 | `tests/integration/test_phase200_recipe_catalog.py::TestTheScheduledOwnerReallyFires::test_the_sweep_is_driven_by_a_wall_clock_loop` | The test reads integer constants from `co_consts`. On Python 3.14 small integers (60, 10) are not in `co_consts`. The loop is there (`holdspeak/runtime/heartbeat.py:86-91`). | ENVIRONMENT (likely; not run on 3.12) | S | Assert on `TICK_SECONDS` another way, or pin the local Python to 3.12. |
| F16 | `test_sequence_workflow_runner_migration.py::test_parent_cancel_fences_admission_and_late_output_while_child_receipts_survive` | Got 502, expected 409, under load. Passes alone. | FLAKY | M | Unknown cause; a race in the cancel path or the test timing. |

Count: F1–F10 = 24 STALE (6+5+2+3+2+2+1+1+1+1). F11–F14 = 4 PRODUCT BUG. F15 = 1 ENVIRONMENT. F16 = 1 FLAKY. Total 30.

All 24 STALE are size S except F4 (M). One worker can pay all of FAST in one PR.

### 1.2 tests/e2e — 35 red (31 failed + 4 errors), 14 files

| # | Tests | Cause (from the error text) | Class | Size | Fix |
|---|---|---|---|---|---|
| E1 | `test_hs175_settings_meetings_glass.py` ×4 errors (`TestSettingsCalendarSection`) | Fixture double `_Evt` has no `attendees`. Same cause as F1. | STALE TEST | S | Add `attendees` to `_Evt`. |
| E2 | `test_philo11_05b_meeting_faces_glass.py` ×2 | Strict-mode: `.desk-window [data-seat=meeting] [data-testid=send-well]` now matches 3 elements. | STALE TEST (selector) | S | Narrow the selector. |
| E3 | `test_hs152_hands_glass.py::test_allow_always_auto_admit` | Strict-mode: `.thread-composer-input` matches 2 threads. | STALE TEST (selector) | S | Scope to the thread region. |
| E4 | `test_hs144_door_glass.py::test_hs144_door_empty_and_error_shots` ×2 | Headline on a door error is now `Coverage incomplete`. The test wants `Nothing needs you`. | STALE TEST (likely; the new headline is the honest one) | S | Change the expected headline. |
| E5 | `test_hs163_steward_glass.py::test_dogfood_run_and_dedup[393]` | Shot is 19341 bytes; the test wants > 20000. | STALE TEST (byte-size fence) | S | Remove the byte floor or lower it. |
| E6 | `test_philo304_thought_foot_reflow.py::…[393-None]` | `[data-testid=arrival-develop-thought]` never shows at 393. The 1440 case passes alone. | STALE TEST (likely) or 393 PRODUCT BUG — not read | S/M | Read the Arrival at 393. |
| E7 | `test_hs176_journal_glass.py` ×4 `[393-852]` | No tab named `Journal` at 393. | NOT CLASSIFIED | M | Read the Speak window at 393. |
| E8 | `test_hs176_loop_glass.py` ×2 | 1440: text `Ship the queue for platform on schedule` ≠ `Ship the Q4 platform in October`. 393: tab list is empty. | NOT CLASSIFIED (393 shares E7's cause, likely) | M | Read with E7. |
| E9 | `test_hs202_03_species_glass.py` ×2 | The dock has a new `More AppIcons` control. 1440: Tab order ≠ DOM order. 393: `Agents` overlaps `More AppIcons` (48×54 px). | PRODUCT BUG (likely: overlap and Tab order are real rules) | M | Fix the overflow control's order and size at 393. |
| E10 | `test_hs171_shade_glass.py` ×2 | Dock badge shows at zero. UX canon: no counters of zero. | PRODUCT BUG (likely; could be a changed seed) | S/M | Hide the badge at zero, or fix the seed. |
| E11 | `test_philo10_04_send_face_glass.py::…[393]` | The `Retry` Button is covered by another element at 393. | PRODUCT BUG (likely) | M | Fix the layout at 393. |
| E12 | `test_hs201_summary_face_glass.py::test_the_summary_is_asked_for…` | Two lead verbs (`Run summary`, `Decide`); the test allows one. | NOT CLASSIFIED (rule break or new verb on purpose) | S | Owner or canon decides. |
| E13 | `test_hs172_arrival_glass.py::TestArrivalProposals::test_arrival_confirm_fires` | Headline stays `4 need you` after Confirm. | NOT CLASSIFIED | M | Read the confirm path. |
| E14 | `test_philo8_03_then_guard.py` ×4 | The undo receipt never shows; one case reports `fail` where `blocked` is expected. | NOT CLASSIFIED | M | Read the receipt path; one cause for all 4, likely. |
| E15 | `test_philo9_03_room_face_glass.py` ×2 | `[data-testid=room-body]` never shows. | NOT CLASSIFIED | M | Read the Room open path. |
| E16 | `test_graph_walk_smoke.py::…[case.j10.arrival_generate_brief.generated_empty]` | "the empty brief says so on the face" fails. | NOT CLASSIFIED | M | Read the J10 case. |
| E17 | `test_graph_walk_smoke.py::…[case.j10.route_generate_again.same_day_same_id]`; `test_hs202_first_use_smoke.py::test_first_use_fence[393-852]`; `test_philo13_13_dock_glass.py::TestLiveDock::…[1440]`; `test_philo304_thought_foot_reflow.py::…[1440-600]` | Fail in the full run, pass alone. | FLAKY (load) | — | Run again at normal load before any work. |

Count: STALE 11 (E1 4, E2 2, E3 1, E4 2, E5 1, E6 1). PRODUCT BUG likely 5 (E9 2, E10 2, E11 1). NOT CLASSIFIED 15 (E7 4, E8 2, E12 1, E13 1, E14 4, E15 2, E16 1). FLAKY 4. Total 35.

Pattern: 9 of the 31 hard failures are `393` only. The phone width is the weak face.

### 1.3 Web vitest

Green: 3263 passed, 0 failed. `tests/web-inherited-baseline.txt` lists 4 tests; all 4 now pass (HEALED). The baseline file can be made empty (S).

## 2. Parked and skipped

### 2.1 Skips seen in the runs

FAST: 38 skipped. e2e: 79 skipped, 4 xfailed.

| Group | Count | Why | Still wanted? |
|---|---|---|---|
| Retired-face glass tests, unconditional `@pytest.mark.skip` (`test_hs158_room_glass.py` 5, `test_hs159_interview_glass.py` 4+, `test_hs161_github_glass.py` 6+2, `test_hs166_jira_glass.py` 2, `test_hs168_sources_glass.py` 4, `test_hs14104/14105/14105a_*` 6) | ~29 | HS-169 retired the interview, the wizards and the 158 Room. The Thought Workbench replaced the 141 glass. | No. Dead code. Park the files (move to `tests/_parked/`). |
| HS-170 "PARKED" skips (Models module, Assignments, ModelLibraryCore, front-door cards, door-rail arm, scroll hint) | 8 | The face was parked in HS-170-03/04. | No. Park with the above. |
| `HOLDSPEAK_DOGFOOD=1` opt-in | 20 | Dogfood plumbing e2e. | Unknown. Nobody sets the flag in CI (not checked in nightly.yml in depth). |
| No `llama_cpp` / MLX / model file | 19 (FAST) | Optional extra not installed. | Yes (machine-specific). |
| Opt-in live `.43`, spoken e2e, dictation endpoint | 6 | Real-metal proofs. | Yes, on purpose. |
| "Owner's real DB not found" | 4 (FAST) | Tests that read the owner's real DB. Skip under isolated HOME. | Question: a test that only runs against the real DB never runs under the rules. Park. |
| `gh` / `acli` not signed in (isolated HOME) | 7 | Auth lives in the real HOME. | Yes. |
| UAT mesh harness cannot pair (`tests/uat/test_mesh_dispatch.py:85`, `test_induction_integration_43.py:118`) | 2 | "since HS-131-16 `mesh serve` requires an imported node pairing … but nodes.py still spawns it with --token-env". A broken harness under a skip. | Yes — this is a hidden PRODUCT/HARNESS BUG (M). |
| `test_interview_service.py:237` QUARANTINED #694 | 1 | `project.setup.finalize` is now CONFIG (owner's press). | Rewrite or park (S). |
| Other machine state (no rail events, no project map, no hub at :8778, mermaid, zeroconf, "No proposals generated") | ~11 | Environment. | Yes. |
| xfail strict (`test_hs200_meeting_outcomes_glass.py:493`, `:591`; 4 params) | 4 | "HS-201 ratified analysis-only summary amendment; parked proposal pipeline". | Park with the proposal pipeline. |

Markers in the tree: 327 lines with skip/xfail/importorskip (197 `importorskip`, 65 `pytest.skip(`, 42 `skipif`, 2 `xfail`). 7 files carry `mark.slow`. Web tests: 0 `.skip`/`.todo`.

### 2.2 Not collected

- `tests/e2e/live167…live176_walk.py`, `live200_voice_walk.py`: 11 walk scripts in the test tree (8 set `collect_ignore_glob`). They are scripts, not tests. Walks are "considered passed" (ruling 2026-09-19). Park.
- 18 non-test `.py` files in `tests/e2e` in total.

### 2.3 Parked code

| Dir | Files | What | Runs? | Still wanted? |
|---|---|---|---|---|
| `web/src/features/project-room/_parked/` | 23 | The retired setup interview + Jira/provider wizards (HS-169) | No. vitest excludes `**/_parked/**` (`web/vite.config.ts:113`). No importer. | No. History has it. |
| `web/src/desk/chair/_parked/` | 23 | The old Chair lanes + hero | No | No |
| `web/src/pages/cores/dictation/_parked/` | 4 | Old dictation parts | No | No |
| `.githooks/_parked/` | 4 | The Delivery Workbench commit gate, parked today | No | Keep (README says how to bring it back) |
| `scripts/_parked/` | 1 | README only. Nothing is parked there. | — | Keep or remove the empty rule |

Total parked web source: 50 files (32 non-test source files have no reachable importer).

## 3. Repo clutter, sized

### 3.1 Tracked files by area

26,913 tracked files, 2.5 GB in the working tree. `.git` is 2.8 GB.

| Area | Files | MB |
|---|---|---|
| `pm/` | 19,723 | 2,256.1 |
| `docs/` | 2,784 | 202.1 |
| `tests/` | 1,197 | 16.8 |
| `apple/` | 484 | 11.5 |
| `web/` | 1,208 | 11.0 |
| `holdspeak/` | 718 | 10.6 |
| `scripts/` | 178 | 2.4 |
| `aipi-lite/` | 127 | 1.6 |
| `gallery/` | 4 | 1.5 |
| `uat/` | 290 | 1.1 |
| all others | ~200 | ~2 |

The product (`holdspeak` + `web` + `tests` + `uat`) is 3,413 files and 39.5 MB. That is 13% of the files and 1.6% of the bytes. The other 98% is evidence and history.

By type: PNG 9,478 files / 1,947 MB. JSON 4,836 / 254 MB. SQLite 29 / 103 MB. JSONL 189 / 46 MB. Markdown 4,914 / 38 MB. `.log` 1,643 / 6.8 MB.

### 3.2 pm/roadmap

| Project | Files | MB |
|---|---|---|
| `holdspeak-philo` | 12,015 | 1,293.7 |
| `holdspeak` | 7,046 | 550.0 |
| `holdspeak-mobile` (dormant track) | 601 | 411.0 |
| `holdspeak-uat` | 56 | 1.2 |

Largest phases: philo phase-13 323 MB (2,152 files); philo phase-11 318 MB (3,499); mobile phase-14 189 MB (122); philo phase-10 151 MB; philo phase-9 107 MB; philo phase-5 103 MB; mobile phase-15 86 MB; philo phase-6 76 MB; holdspeak phase-129 62 MB.

Largest files: 21 of the top 25 are 4–5 MB iPad PNGs under `pm/roadmap/holdspeak-mobile/phase-1{4,5,6,7,8}*/screenshots/`. Also `docs/internal/philo/phase-7/grant-canvas/index.html` 7.3 MB; two `observation.json` of 4.7 MB under `docs/internal/philo/phase-6/body/`; `docs/internal/philo/graph/static-astra.json` 4.1 MB.

`pm/STATUS.md` says: "The old roadmap under `pm/roadmap/` is history; it is not updated."

### 3.3 Tracked junk

| Kind | Files | MB | Where |
|---|---|---|---|
| SQLite databases | 29 | 103.1 | All under `pm/roadmap/holdspeak-philo/phase-{5,6,7,9,10,11}*/assets/…` (`db-proof.sqlite`, `db-complete.sqlite`, `missing-op.sqlite`, `missing-browser.sqlite`) |
| `-shm` / `-wal` | 8 | 0.1 | Tracked: phase-5 `story-04-shots/final/20260925T001407Z-his-words-real/`, phase-5 `…/carried/verification/` (×2 dbs), phase-11 `story-07-shots/final/20261001T121534Z-rehearse-press393/` |
| `attempts/` dirs (failed tries) | 830 | 95.1 | phase-5 story-04 236 files / 51.6 MB; phase-8 story-03 231 / 19.1; phase-7 story-04 174 / 11.6; phase-9 story-06 164 / 11.6; phase-6 ×2 19 / 1.2; phase-13 h-c5 6 / 0.1 |
| `.log` files | 1,643 | 6.8 | philo phase-11 has 1,032 of them |
| Same-content copies (same blob hash) | 1,737 extra copies | 95.7 | Shots copied between `attempts/`, `final/`, `carried/` |

`.gitignore` has no rule for `*.sqlite-shm` / `*.sqlite-wal`. That is why the main checkout shows 16 untracked `-shm`/`-wal` files under phase-5 `attempts/`: a reader opened the tracked databases. 4 tests and 6 scripts open these proof databases (`tests/unit/test_philo_graph_atlas.py`, `test_philo10_send_job.py`, `test_philo7_file_and_find.py`, `test_philo9_room_job.py`).

No tracked `.DS_Store`, `.pyc`, `node_modules`, `.orig`, `.bak`, zip or tar.

### 3.4 Docs

`docs/`: 2,784 files, 202 MB. `docs/internal/` holds 2,367 of them.

Pure history (whole directories; no live reader except history tests):

| Dir | Files | MB | What |
|---|---|---|---|
| `docs/internal/philo/graph/` | 472 | 30.4 | Phase 2 graph audit output |
| `docs/internal/philo/phase-13/` | 414 | 25.2 | Grounding shots, closed phase |
| `docs/internal/philo/phase-6/` | 236 | 22.1 | Bodies + logs, closed |
| `docs/internal/philo/phase-3,4,5,7,8,9,10,11,12/` | 647 | 30.6 | Closed phases |
| `docs/internal/surface-inventory-2026-09-20/` | 408 | 41.7 | One-day inventory (287 PNG) |
| `docs/internal/inventory-2026-09-19/` | 6 | small | One-day inventory |
| `docs/internal/architect-assistant/` | 30 | 3.5 | Not read |
| `docs/internal/project-rooms/` | 18 | 0.4 | 11 handovers + SRS; arc merged |
| `docs/evidence/` | 189 | ~1.5 | PR evidence (`people-pr1`, `automations-pr461`) |

33 test files name `docs/internal/philo`. They pin this history in place.

Stale top-level docs in `docs/internal/` (55 files). Not touched since June–July and they name files that are gone:

- `PLAN_MEETING_MODE.md` (names `holdspeak/tui.py`, `holdspeak/config.py` — gone), `CROSS_PLATFORM_ROADMAP.md` (names `tests/integration/test_tui.py` — gone), `CROSS_PLATFORM_TASK_BOARD.md`, `LINUX_PORT_PLAN.md`, `LINUX_PORT_EXECUTION.md`, `RELEASE_HARDENING_CHECKLIST.md`, `PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md` — all last touched 2026-06-03 / 07-02.
- `MISSION_CONTROL_DESK.md` (names `holdspeak/delivery_workbench_map.py` — gone), `PLAN_INTEL_STREAMING.md`, `PLAN_MEETING_INTEL_PI.md` (names `holdspeak/intel.py`, `web/src/pages/LivePage.tsx` — gone), `PROZILLAOS_STUDY.md`, `AGENT_PROMPT_ADOPTION_…md`, `PLAN_PHASE_JIRA_DESK_SYNC.md` (13 of 29 named paths gone).
- `OPENWORKER_INTEGRATION_FEASIBILITY.md` (research; 29 of 45 paths are another repo's), `DOC_AUDIT_2026-06/08/09.md` (three dated audits), `INVENTORY-2026-09-19.md`, `SURFACE-INVENTORY-2026-09-20.md`, `OPERATIONAL-SURFACE-AUDIT.md` (dated audits).
- Careful: `CLAUDE.md` "Source canon" still names `PLAN_ARCHITECT_PLUGIN_SYSTEM.md`, `PLAN_PHASE_MULTI_INTENT_ROUTING.md`, `PLAN_PHASE_DICTATION_INTENT_ROUTING.md`, `PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`. All four are from June and name `holdspeak/config.py`, `holdspeak/intel.py`, `holdspeak/controller.py`, `holdspeak/meeting_session.py` — all gone (they are packages now or removed). Canon that describes a product that no longer has that shape.

User docs with dead references (rough signal from a path check; it does not resolve package-relative paths): `docs/DICTATION_COPILOT.md` (4 of 5), `docs/USER_GUIDE.md` (4 of 6; `.hs/*.md`), `docs/AIPI_LITE.md` (6 of 11), `docs/ARCHITECTURE.md` (5 of 17). Not verified one by one.

### 3.5 scripts/

178 files (163 at top level, 14 in `desk_walk/`, 1 in `_parked/`). 1.05 MB of it is phase-named.

- 74 top-level scripts have no live caller (no hit in `tests`, `uat`, `holdspeak`, `.github`, `pyproject.toml`, `CLAUDE.md`, `AGENTS.md`, `README.md`, `web/`, or another script). 387 KB. Among them: 14 `screenshot_phase69_*`/`screenshot_phase70_*`, 6 `screenshot_hs83–86_*`, 8 `phase93_*_evidence.py`, 6 `dogfood_*.py`, 5 `screenshot_aftercare_*`, `phase107/108_closeout_beats.py`, `phase70_closeout.py`, `phase70_tour.py`, `tui_demo.tape` (the TUI is gone), 3 `aipi_*.sh`.
- 70 scripts carry a phase or story number in the name. 34 of them still have a caller — most callers are history tests (see 3.7).
- Families that look like duplicates of one job: 35 scripts that walk or shoot (`walk_*` 11, `screenshot_*` ~40). `scripts/graph_walk.py` is the named replacement (`scripts/_parked/README.md`), and that README says no walk script met the park rule on 2026-09-22.

### 3.6 Dead web code

Import-graph walk from `web/index.html` and `web/atmospheres.html` over 537 non-test source files:

- 32 unreachable source files are inside `_parked/` (plus 18 parked tests).
- 4 unreachable outside `_parked/`: `web/src/features/workbench/model.ts` (3.6 KB), `web/src/pages/cores/history/AftercareGadgets.tsx` (1.3 KB), `web/src/pages/cores/index.ts` (0.5 KB), `web/src/runtime/frames.ts` (1.9 KB). No importer of any kind, tests included.
- Not covered: dead exports inside live files, dead CSS rules, `web/uat/`, `web/public/`.

### 3.7 History tests (found while sizing)

169 test files name `pm/roadmap`; 140 name pm asset paths; 33 name `docs/internal/philo`. These tests read closed-phase evidence. They hold 2.4 GB of history in place, and they are part of the 13,228-test FAST run. I did not measure their share of the 5 min 40 s. `pm/STATUS.md` already names the larger cost: "6,932 databases = most of the fast run".

### 3.8 Branches and worktrees

- `origin`: 548 branches. 537 are merged into `origin/main`. 9 are not: `codex/runtime-presence-indicators` (06-05), `holdspeak-mobile/hsm-25-mission-control` (07-04), `research/openworker-feasibility` (07-26), `agent/hs-113-forge-wave-1`, `…-wave-2` (08-02), `feat/hs142-existing-model-chooser` (08-21), `hold/hs143-10-slice5-swift-bridge` (08-25), `worktree-warpdrv-chat-port` (08-30), `feat/philo-13-web-quality-python` (10-02; the one open PR, #735).
- Local: 607 branches, 581 merged.
- Worktrees: 90 registered.
  - 42 "prunable": the directory is gone. `git worktree prune` clears them.
  - 38 present, HEAD merged into main, clean. Safe to remove. 4 are today's `wt-inv-a..d`.
  - 9 present with local changes (look before removing): `wt-philo-11-06` (71 changed paths), `wt-philo-13-b0-r2` (9), `wt-202-01-baseline` (4), `/private/tmp/holdspeak-c1-baseline.mRFbNp` (3), `wt-astra-747-info` (1), `wt-astra-747-slice2` (1), `wt-philo-11-05b` (1), `.claude/worktrees/agent-ac3c14fce99fa6f72` (1), and the main checkout (19 untracked).
  - 1 present, clean, HEAD not on main: `wt-astra-b4w-check-53a88cb3`.
- Disk: a worktree is 1.6 GB bare, 3.7–4.0 GB with `.venv` and `node_modules` (measured on three). 47 present worktrees ≈ 75–190 GB (estimate, not measured each). Disk is 80% full (186 GB free). `.claude/worktrees` 1.6 GB; `.tmp` 499 MB in the main checkout.

## 4. Proposed cleanup, in safe slices

Rule kept: nothing is deleted. "Park" = `git mv` into an archive place. "History only" = the file leaves the tree; git history keeps every byte, and `git show <sha>:<path>` reads it. No history rewrite in any slice (a rewrite of the 2.8 GB `.git` needs the owner's own word; I do not propose it now).

| # | Slice (one PR each) | How | Win | Risk |
|---|---|---|---|---|
| C1 | **Green FAST.** Pay F1–F10 (24 stale tests), F11–F14 (4 small product/doc fixes), F15. | Edit tests + 4 small product edits | FAST 30 red → 0 or 1 (F16 flaky). | Low. All S but F4 (M). |
| C2 | **Green e2e, part 1.** E1–E5 (10 stale) + run E17 again. | Edit tests | e2e 35 red → ~21. | Low. |
| C3 | **e2e, part 2: read and rule.** E6–E16 (21 tests, 11 causes). Most are 393-width. | One worker reads each on the glass; product fix or test fix | e2e → 0. | Medium. Needs the canon for E9, E10, E12. |
| C4 | **Local hygiene, no PR.** `git worktree prune`; remove the 38 merged clean worktrees; delete the 537 merged `origin` branches and 581 merged local ones (GitHub keeps the PR refs, so no commit is lost). | git only | 42 dead entries gone; ~60–150 GB of disk; 548 → 11 remote branches. | Low. Leave the 9 dirty and 1 unmerged for a look. |
| C5 | **Stop the SQLite noise.** Add `*.sqlite-shm`, `*.sqlite-wal` to `.gitignore`; take the 8 tracked ones out of the tree (history only; they are 0.1 MB of lock state). | `.gitignore` + `git rm --cached` | `git status` is clean in the main checkout (16 untracked lines gone). | None. |
| C6 | **Park dead tests.** Move the ~37 always-skipped retired glass tests, the 4 xfail tests, the 4 real-DB-only tests and the 11 `live*_walk.py` scripts to `tests/_parked/` (ignored by collection). | `git mv` | ~45 fewer collected tests; 11 scripts out of the test tree; skips that mean something. | Low. |
| C7 | **Park dead web code.** The three `_parked/` dirs (50 files) are parked already. Move the 4 unreachable files into a `_parked/` next to them. Empty `tests/web-inherited-baseline.txt` (4 healed). | `git mv` | 4 files; baseline at zero. | Low. |
| C8 | **Park dead scripts.** Move the 74 no-caller scripts to `scripts/_parked/` with one line each in its README. | `git mv` | `scripts/` 163 → 89 at top level. | Low. A caller in a doc under `pm/` or `docs/internal/` will point at the old path (history docs, not updated by rule). |
| C9 | **The big one: evidence out of the main tree.** Move `pm/roadmap/*/phase-*/assets`, `…/screenshots`, `attempts/`, the 29 SQLite files, and `docs/internal/philo/{graph,phase-*}`, `docs/internal/surface-inventory-2026-09-20/` to an archive that is not checked out with the code. Two ways: (a) an orphan branch `archive/evidence` in this repo (history only on `main`; every byte stays reachable on the branch); or (b) a second repo `holdspeak-evidence`. Keep the Markdown (stories, status, summaries) in place. | (a) or (b); owner picks | ~2.3 GB and ~20,000 files leave every checkout. A new worktree drops from 1.6 GB to ~0.1 GB and seconds to create (today: 26,913 files to write). `git status`/`grep` over the tree get fast. | High coupling: 169 test files read `pm/roadmap`, 33 read `docs/internal/philo`. C10 must land first or in the same PR. |
| C10 | **Park the history tests** that only read closed-phase evidence (the philo3–13 atlas/proof/pairs tests, `phase143_*census`, `test_dw_counterpart_contract`, …). | `git mv` to `tests/_parked/history/` after a read of each: keep any that guard live product behaviour | Unblocks C9. Test-time win not measured (see "not covered"). | Medium. Needs a per-file read: fence of the product, or fence of the paperwork? |
| C11 | **Park stale docs.** Move the 13 June–July plans named in 3.4 and the dated audits to `docs/internal/archive/`. Take the four June `PLAN_*` docs out of `CLAUDE.md` "Source canon" (or write them again). | `git mv` + 1 edit to `CLAUDE.md` | ~20 files out of the canon path; canon that is true. | Low, but `CLAUDE.md` is the owner's file: his word needed. |
| C12 | **Later, owner's word only:** history rewrite to drop the evidence blobs from `.git`. | `git filter-repo` | `.git` 2.8 GB → perhaps 0.3 GB. | Destroys SHAs for every branch and worktree. Not proposed now. |

If C9 is too much for now, the cheap half is: move only `attempts/` (830 files, 95 MB), the SQLite files (103 MB) and the dormant `holdspeak-mobile` screenshots (411 MB). That is ~610 MB for three `git mv`/branch moves, and it touches ~10 tests.

Order: C1, C2, C4, C5 at once (independent). Then C6, C7, C8. Then C10 → C9. C3 and C11 in parallel with anything.

## 5. Not covered

- The e2e NOT CLASSIFIED group (15 tests, E7–E16): I have the error text, not the cause. No browser session was opened to look.
- e2e class calls E4, E6, E9, E10, E11 are "likely", from the error text only.
- F15 was not run on Python 3.12 to confirm.
- FAST and e2e wall times are not clean numbers (load average 77). No `--durations` data; no per-test cost.
- The test-time win of C10 (history tests) and the "6,932 databases" cost are not measured.
- `tests/e2e/test_metal.py` and the `slow` tests were not run (by rule). The FULL nightly set was not run; `pm/STATUS.md` records "Last full Python run: 104 failed, 4 errors (not classified)" — the `slow`-marked part of that is still not classified.
- Docs: path-reference sampling only. I did not read the 2,367 files in `docs/internal`. `docs/internal/architect-assistant/` (30 files) was not read. The user-doc dead-reference numbers are a rough signal.
- Dead web code: file level only. No dead exports, CSS, or `web/public` assets. No dead Python modules in `holdspeak/` (not asked, not done).
- `apple/` (484 files, dormant iPad track), `aipi-lite/`, `gallery/`, `dogfood/`, `designer-handoff/`, `extensions/` (last touched 2026-04-29): sized, not judged.
- The 9 dirty worktrees: I counted changed paths; I did not read what the changes are.
- Whether the merged-branch count hides squash-merged branches that show as "not merged": the 9 unmerged were not inspected.

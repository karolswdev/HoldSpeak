# Evidence - PHILO-9-05

- **Story:** PHILO-9-05 - The atlas: assembly, rerun and equivalence
- **Status:** done
- **Date:** 2026-09-28
- **Branch:** `feat/philo-9-05` from main `79fdee3c` (stories 01, 02, 03, 04, 07 merged); round two merges origin/main `b2fd7e8b` (#687, story 06). The product under test is main: this story changes no product file.

## Round three — Codex Astra r2 on PR #688 @ `67ce9256` (RATIFY-WITH-CONDITIONS), paid

`checks/story-05-built-astra-r2.md` (verbatim). Codex verified 28/28, 69/69, 194 observations per base comparison, 10/10 mutations and the 435 fences. Three narrow conditions; no atlas rerun.

1. **`fences.sh` read `cut`'s status for the mutations** (`mrc=$?` after a pipe). Now `mrc=${pipestatus[1]}`. `assets/story-05-proof/exit_combos.sh` runs the script's own text with the two commands replaced by `(exit A)` / `(exit B)` (their pipes kept), for all four combinations, on the `67ce9256` script and on this one. Before: fences pass + mutations FAIL exits 0 (WRONG); after: exit 0 only when both pass (capture below).
2. **Export provenance (recorded; the historical observations are not edited).** The observations of the runs on an export (`base-294632c0/`, `red-1f332bc3/`) carry `provenance.revision` `b2fd7e8b` (or the branch head of that capture). The export is a `git archive` extracted under `.tmp/` inside this worktree, so the rig's `git rev-parse` found the ENCLOSING worktree, not the export's commit. The product that ran was the export's: `PYTHONPATH` = the export, its own web build. Codex Astra reconciled it independently: the 1,554 product source files of each export match its claimed commit (`294632c0`, `1f332bc3`), and both built-index hashes (`frontend_build`) match their observations. The `revision` field of those observations is misleading alone. Read it together with this note and the capture's command line (`ROOT=.tmp/main-294632c0`, `red_main.sh`'s `BASE`).
3. **PR #688's description** refreshed: the current counts, and s5 as an inherited input-precondition defect (not a timing flake).

## Round two — Codex Astra r1 on PR #688 @ `11a89a12` (DO-NOT-RATIFY), paid

`checks/story-05-built-astra-r1.md` (verbatim). Codex ran the five new cases serially at `11a89a12` and found them lawful and passing. Each finding and what paid it:

| # | Finding | Payment | Proof |
|---|---|---|---|
| 1 (blocking) | `rig_phase.sh:17` `${run:h:t}` named the batch, so each run overwrote the last: 1 of 28 and 1 of 69 observations kept; the base kept TSVs only | Every run now writes under its OWN directory (`rig_run.py`: `<label>/<case>--<width>/<run id>`, recorded in a `run_dir` column; a second run into one directory is refused); `rig_phase.sh` copies each row's own directory whole and counts rows = directories = observations, or exits 1. The originals were NOT recoverable (the `.tmp` run directories had been removed after round one), so every claimed run was RE-RUN serially on the merged tree `b2fd7e8b`, isolated HOME per run | captures 18:46:10Z (`retained: 28 rows, 28 run directories, 28 observations`) and 18:51:03Z (`retained: 69 …`); fence `tests/unit/test_philo9_atlas.py::test_every_claimed_run_keeps_its_own_observation[p9-merged, p78-merged, base-294632c0, base-merged]` (each row's directory holds an observation of THAT case, width and verdict; each face run kept a shot; no stray directory) |
| 2 | The census was not criterion-complete | "The census" below: every criterion of stories 01–04, 06 and 07 with an exact disposition (atlas case, `file::test`, or excluded with its reason); story 07's owner revoke, orphan, Remote Access OFF and archived states named by their glass tests, not excluded | the section below |
| 3 | The delivery face read only "Priya"; the Connections fence compared the face only | `case.p9.update.delivered_row` now reads its OWN click's answer (`trigger_route` `POST /api/updates/{update_id}/delivered`: 200, the delivery row for this update To Priya with an operation id, the owner's succeeded receipt targeting the update) AND the hub's stored update (`GET /api/projects/{project_id}/updates`: the delivery To Priya), beside the face's words. `test_the_pairs_read_the_same_values` compares BOTH Connections predicates (face row and twin facts: github, `never_checked`, no check time); `test_the_delivery_face_reads_its_own_clicks_durable_outcome` added. Mutations m9 (the face back to words only) and m10 (the twin's github state `never_checked` → `ready`, in `atlas-phase9-steward.json`) added | the fences capture: `baseline (unmutated): 46 passed`, **10 red, 0 missed** (m10: `test_the_pairs_read_the_same_values` FAILED); the delivered_row reruns pass at 1440 and 393 with all three parts |
| 4 | s5 was called a timing flake | Re-classified: an inherited INPUT-PRECONDITION defect of `case.closure.chain.s5_next_day_brief_more_opened` — the "N more" verb renders only when the brief holds more than `BRIEF_CAP` = 3 items (`web/src/desk/chair/ChairHome.tsx:2077`, `:2092`, `:2130`) and the case never makes four. BACKLOG row (`pm/roadmap/holdspeak/BACKLOG.md`, "PHILO-9-05 follow-ups"), with the 324 s summary wait on `294632c0` as its OWN row. Corrected figure: the round-one extra attempts pass **2 of 6 on each product** (merged main 0+0+2, `294632c0` 1+0+1), not 2 vs 3 | BACKLOG rows; round one's `base_diff.py` capture (18:27:47Z) keeps its honest exit 1 |
| 5 | `docs_nav.sh` exited 0 after a failure; the existing OpenAPI drift fence was not run | `docs_nav.sh` collects every check's exit code and exits 1 when any fails (an injected `false` made it exit 1); `fences.sh` now runs `tests/unit/test_api_surface.py`. The drift Codex attributes to stories 02 (`24576f25`) and 07 (`cfe26467`): their routes (`…/suggested-sources/{ref:path}/…`, the project grant, `…/delivered`) were not regenerated. Its first run here FAILED (`test_committed_manifest_matches_the_live_app`, capture 19:07:33Z, exit 1) — `docs/api-surface.json` / `docs/API_SURFACE.md` were stale too; regenerated (`scripts/gen_api_surface.py`), then `docs/API_REFERENCE.md`, `api-reference.json`, `graph.json`. origin/main (#687) merged first; every generated artifact rechecked after it | the fences and docs captures below |
The round-two closing captures: fences 19:44:19Z (435 passed incl. `test_api_surface.py`; mutations baseline 48 passed, 10 red, 0 missed), `base_diff.py` 19:44:18Z (0 pass→not-pass, exit 0), Documentation Navigation + OpenAPI 19:45:21Z (`checks failed: 0`).

## Summary

- **The census** (each story's criteria against the atlas; below).
- **The five authored gaps** (`docs/internal/philo/graph/atlas-phase9.json`, written by `assets/story-05-proof/add_atlas.py`): `case.p9.update.delivered_row.op`, `case.p9.grant.project_allowed`, `case.p9.grant_route.project_allowed`, `case.p9.grant.desk_reads_desk`, `case.p9.connections.never_checked_face`; two new states (`p9_grant_face`, `p9_connections_face`), two exclusions with reasons (the agent side of the grant; the face cases with no twin). Muad'Dib's brief authorized authoring only the gaps the census proves. It overrides the story's Scope line "Out: authoring a new face case" for the three face cases, and the story's Notes say so.
- **No fold.** `atlas-phase9-steward.json` (story 02) stays its own file. Story 02's retained observations (`docs/internal/philo/graph/observations/muaddib/20260928T1449*-case.p9.*`) name that path and its sha256, and the owner rules "never delete, park instead". The phase atlas is the two files.
- **The phase fences** (`tests/unit/test_philo9_atlas.py`, 48 tests after round two): the 16 general fences and the OpenAPI route check applied to BOTH Phase 9 files (the general fences read `atlas.json` only by default, the Phase 8 law), the counts over every atlas file, the story 05 ids, widths (face at 1440 and 393, the rest headless), the three equivalence pairs and their shared values, each admitted-write twin reading its receipt WITH its actor, every face case without a twin excluded by name, no optional trigger and no optional step but the gate's. `assets/story-05-proof/mutations.py`: 10 mutations, 10 red (round two: m9, m10; the unmutated baseline is run first and must be green). `tests/unit/test_philo_graph_atlas.py`: the `.op` sibling count 44 → 45, and `project.mark_update_delivered` / `project.list_updates` added to its producer and read sets.
- **Generated:** `docs/api-surface.json`, `docs/API_SURFACE.md`, `docs/API_REFERENCE.md` (round two), `docs/generated/openapi.json` (it was stale on main: the grant route `PUT/DELETE /api/settings/remote/delegations/{identity}/projects/{project_id}` and `POST /api/updates/{update_id}/delivered` were missing; the new route case's OpenAPI fence needs them), `api-reference.json`, `graph.json` (the OpenAPI hash), `repository-tree.json`.

## The census (round two: every criterion of stories 01–04, 06 and 07, Codex Astra r1 finding 2)

Disposition key: **ATLAS** = an atlas case (file); **GLASS** = a browser fence (`tests/e2e/...::test`); **BACKEND** = a unit or integration fence through the real hub (`tests/unit/...::test`); **EXCLUDED** = not an atlas case, with the reason. An atlas case is named only where one exists; a glass or backend fence is not atlas coverage.

### Story 01: the Room's operations on the contract

| # | Criterion | Disposition |
|---|---|---|
| 1 | Clean base install imports `holdspeak.mcp.tools` | BACKEND `tests/unit/test_philo9_base_install_imports_catalogue.py::test_clean_base_install_imports_the_mcp_catalogue`, `::test_base_dependencies_declare_jsonschema`. EXCLUDED from the atlas: an install, not a face or an operation |
| 2 | 18 MCP + 3 HTTP identities leave the residual set; a new residual identity fails | BACKEND `scripts/residual_census.py --check` (story 01 evidence captures), `tests/unit/test_philo9_contract.py::test_every_mcp_tool_and_http_route_of_the_slice_reaches_the_one_registry`. EXCLUDED: a census of constructors |
| 3 | The seven new tools match the charter; each equals its HTTP route in one hub and across a restart | BACKEND `tests/unit/test_philo9_room_contract.py::test_the_seven_tools_are_listed_with_the_charters_schemas`, `::test_the_seven_tools_equal_the_http_routes_in_one_hub_and_across_a_restart`, `::test_the_seven_tools_refuse_as_the_routes_do`, `::test_a_reused_command_id_with_a_different_body_is_idempotency_conflict_on_both`. ATLAS (the rig's op step): `tests/unit/test_philo9_rig_op.py::test_the_rig_drives_the_room_job_through_a_real_hub` |
| 4 | `kernel.receipt` in PROJECT and SWEEP; its own receipt read, a foreign one refused | BACKEND `tests/unit/test_philo9_room_contract.py::test_kernel_receipt_on_the_palette_reads_its_own_and_refuses_a_foreign_operation`. EXCLUDED from the atlas: needs an agent principal (the rig has only the owner's token) |
| 5 | "1 proposal waiting" (F22) | BACKEND `tests/unit/test_philo9_room_contract.py::test_f22_one_waiting_proposal_is_singular` |
| 6 | Discovery maps the job's phrases; no tool says the product sends | BACKEND `tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path`, `::test_no_project_tool_says_the_product_sends_the_update`, `::test_every_id_argument_names_where_its_value_comes_from` |
| 7 | `get_room` / Room route report a published update and a completed steward run | BACKEND `tests/unit/test_philo9_room_contract.py::test_f6_the_room_reports_a_published_update_and_a_completed_steward_run` |
| 8 | Muted project: one needs-you count on MCP and HTTP | BACKEND `tests/unit/test_philo9_room_contract.py::test_f13_one_needs_you_count_with_a_muted_project` |
| 9 | The delivery table: reconcile, insert-only, `project_updates` untouched, two rows in order | BACKEND `tests/unit/test_philo9_delivery_record.py::test_the_reconcile_creates_the_table_on_an_existing_database`, `::test_the_repository_has_no_update_or_delete_path`, `::test_a_delivery_never_writes_the_published_update`, `::test_the_untouched_fence_turns_red_on_a_delivery_that_writes_the_update`, `::test_two_deliveries_read_back_in_order_on_every_read` |
| 10 | A past-due milestone turns health and is in NEEDS YOU; RECEIPTS are writes | BACKEND `tests/unit/test_philo9_room_contract.py::test_f2_a_past_due_milestone_turns_health_and_is_in_needs_you`, `::test_f2_preservation_…`, `::test_f7_the_rooms_receipts_are_its_writes_not_its_reads`. ATLAS (face): `atlas-phase9.json` `case.p9.room_items.late_row` |
| 11 | Names, arguments, envelopes, refusals kept; palette refusal through dispatch | BACKEND `tests/unit/test_philo9_compat.py` (3 tests), `tests/unit/test_philo9_contract.py::test_the_project_palette_refuses_outside_and_admits_the_new_tools_through_dispatch` |

### Story 02: the steward and the connectors under Article XI

| # | Criterion | Disposition |
|---|---|---|
| 1 | 20 MCP + 3 HTTP identities leave the residual set | BACKEND `tests/unit/test_philo9_steward_admission.py::test_the_residual_set_paid_exactly_the_story_02_identities` |
| 2 | Accepting a GitHub / Jira suggestion leaves a resource AND a watch, or a named refusal with the suggestion pending; the MCP twin | BACKEND `tests/unit/test_philo9_steward_admission.py::test_a_github_suggestion_becomes_a_resource_and_a_watch[http,mcp]`, `::test_a_jira_suggestion_without_a_connected_account_is_refused_and_stays_pending[http,mcp]`, `::test_a_jira_suggestion_with_a_connected_account_becomes_a_resource_and_a_watch`. EXCLUDED from the atlas: the suggestion must be minted by the real scanner and a Jira account connected through a canned `acli` runner, a seam the rig's hub process does not have |
| 3 | No `unittest.mock` in product code | BACKEND `::test_no_product_module_imports_unittest_mock`, `::test_the_mock_import_fence_turns_red_on_a_mutation`. EXCLUDED: a static fence |
| 4 | COMPARE `review_id` = `open_review`'s | BACKEND `tests/unit/test_philo9_steward_lifecycle.py::test_l7_compare_and_proposal_creation_record_the_review_open_review_returned` |
| 5a | `connection.list` makes no provider call; each row's own checked-at time; "never checked"; Calendar and Models live | BACKEND `tests/unit/test_philo9_b1_connections.py::test_list_makes_no_provider_call`, `::test_list_on_a_fresh_hub_makes_no_provider_call`, `::test_each_remote_row_returns_its_own_stored_time`, `::test_no_stored_check_reads_never_checked`, `::test_calendar_and_models_read_live`. ATLAS: `atlas-phase9-steward.json` `case.p9.connections.never_checked` (op) |
| 5b | The Connections face: each row's age and "never checked" at 1440 and 393 | ATLAS (story 05): `atlas-phase9.json` `case.p9.connections.never_checked_face` (never checked only). GLASS for the checked AGE (two rows, two ages): `tests/e2e/test_philo9_b1_connections_glass.py::test_each_card_shows_its_own_age[1440,393]`, `::test_the_empty_jira_card_shows_its_own_state`. EXCLUDED from the atlas: a checked age needs a probed row whose stored time is set back (a canned `gh`/`acli` runner and a database seed of a time), which the rig's hub has no seam for |
| 5c | Confluence Recheck probes and stores its time; recheck admitted for github/jira/confluence, not calendar/models; Door count admitted | BACKEND `tests/unit/test_philo9_b1_connections.py::test_confluence_recheck_probes_and_stores_its_time`, `tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[…recheck…, door count]`. EXCLUDED from the atlas: a probe is egress through a canned runner |
| 6 | Four decide verbs admitted; an agent without a grant refused for each | BACKEND `::test_each_admitted_http_route_is_one_operation_with_one_receipt[decide *]`, `::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[decide *]` |
| 7 | The lifecycle beat's five points; a real restart; an agent's stop on another's run refused | BACKEND `tests/unit/test_philo9_steward_lifecycle.py` (l1–l7, a1, a4, a6), `tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once`, `tests/unit/test_philo9_steward_lifecycle.py::test_r4_1_an_agents_stop_of_the_owners_run_is_refused_with_a_receipt`. ATLAS: `case.p9.steward.run_receipted` (the completed run and its receipt) |
| 8 | Each mark: one admitted operation, receipt, one row; two marks two rows; a draft refused; an agent refused | BACKEND `tests/unit/test_philo9_mark_delivered.py::test_each_mark_is_one_admitted_operation_its_receipt_and_its_row`, `::test_two_marks_are_two_rows_and_two_receipts`, `::test_a_draft_is_refused_update_not_published_with_a_receipt_and_no_row`. ATLAS: `case.p9.update.mark_delivered_receipted`, `case.p9.update.delivered_row.op`, `case.p9.update.delivered_row` |
| 9 | Delivery idempotency (repeat, conflict, new key, no key, concurrent, restart) | BACKEND `tests/unit/test_philo9_mark_delivered.py::test_a_repeat_of_one_key_and_payload_answers_the_original`, `::test_one_key_with_a_changed_payload_is_refused_idempotency_conflict`, `::test_a_new_key_to_the_same_recipient_makes_a_second_row`, `::test_an_mcp_mark_without_a_key_is_a_new_delivery`, `::test_two_concurrent_requests_with_one_key_make_one_row`, `tests/unit/test_philo9_steward_restart.py::test_d1_a_delivery_replay_after_a_real_restart_answers_the_original` |
| 10 | The row's `operation_id` NOT NULL UNIQUE FK; project from the update; one transaction; rollback then replay once | BACKEND `tests/unit/test_philo9_mark_delivered.py::test_the_row_names_its_operation_not_null_unique_and_referenced`, `::test_a_mark_that_names_another_project_is_refused_and_the_project_comes_from_the_update`, `::test_a_failure_after_the_insert_leaves_no_row_no_state_no_receipt_and_a_replay_succeeds_once` |
| 11 | Discovery "mark it delivered" | BACKEND `tests/unit/test_philo9_discovery.py::test_mark_it_delivered_maps_to_its_tool` |
| 12 | Archive: one admitted operation, pause and unattended-off inside | BACKEND `tests/unit/test_philo9_steward_admission.py::test_archive_as_the_owner_is_one_operation_and_its_pause_and_unattended_off_are_inside`. ATLAS: `case.p9.project.archive_receipted` |
| 13 | Each admitted row one operation + one receipt on HTTP and MCP; refusal classes; exempt rows none | BACKEND `::test_each_admitted_http_route_is_one_operation_with_one_receipt`, `::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt`, `::test_the_exempt_rows_and_the_reads_make_no_operation`, `::test_a_contract_refusal_of_an_admitted_tool_leaves_its_receipt`, `::test_a_link_is_one_top_level_admission_and_its_meeting_watch_is_its_child` |
| 14 | Settings-issued PROJECT credential over HTTP refused with a receipt; protocol refusals receipt-less | BACKEND `::test_b2_a_project_credential_over_http_is_refused_with_a_receipt`, `::test_b2_protocol_refusals_stay_receipt_less`. EXCLUDED from the atlas: an agent principal |
| 15 | Without a grant an agent's admitted writes are refused (P3) | BACKEND `::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes`. EXCLUDED from the atlas: an agent principal |

### Story 03: the Room's face tells the truth

| # | Criterion | Disposition |
|---|---|---|
| 1 | Every caller opens the Room, one per face, 1440 and 393 | GLASS `tests/e2e/test_philo9_03_room_face_glass.py::test_the_meetings_project_button_opens_the_room`, `::test_the_chairs_project_button_opens_the_room`, `::test_the_shades_project_row_opens_the_room`. ATLAS: the palette's Open in every Room case. EXCLUDED as atlas cases: `excluded.p9.room_face_callers_and_receipts` (a meeting row no HTTP route seeds) |
| 2 | A past-due milestone AND a risk shown as drawn | ATLAS `case.p9.room_items.late_row` (the milestone). GLASS for the RISK row: `::test_a_late_milestone_and_a_risk_show_as_drawn`, `::test_the_late_words_are_the_canvas_words` |
| 3a | Mark delivered offered on return after Copy (R4-3) and after an earlier delivery; Copy then Mark (Priya), then again (Tomas): two rows read back; DELIVERED chip; double-click one row; pending→delivered transition | GLASS `::test_copy_then_mark_delivered_twice_reads_back_two_rows` (the return after Copy at its R4-3 step, both marks, the read-back, the chip, the double-click). ATLAS for ONE mark: `case.p9.update.delivered_row` (round two: reads the click's own answer and the hub's row). EXCLUDED as an atlas case: the return after Copy and a repeated delivery are several gestures on one face with a clipboard; the rig has no clipboard read |
| 3b | A mistaken delivery then a correct one: both shown, counted; a draft offers no Mark; no egress badge | GLASS `::test_copy_then_mark_delivered_twice_reads_back_two_rows`, `::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update`, `::test_a_refused_delivery_receipt_says_refused_and_why` |
| 4 | Steward counts equal the run; the review shown; "no effect allowed" | GLASS `::test_the_steward_counts_equal_the_run`, `::test_review_on_a_completed_run_opens_that_review_even_after_acceptance`. EXCLUDED as an atlas case (same exclusion) |
| 5 | RECEIPTS list the writes after each transition | GLASS `::test_receipts_list_the_writes_after_each_transition`, `::test_receipts_hold_only_this_rooms_work`. EXCLUDED as an atlas case (below the fold) |
| 6 | At 393 the Steward verb's centre hits the verb | ATLAS `case.p9.room_steward_verb.owned`. GLASS `::test_the_ask_well_covers_no_verb_or_head` |
| 7 | The update list's words per lifecycle | ATLAS `case.p9.update_list.head_updates`. GLASS `::test_the_update_list_words_fit_each_lifecycle` |
| 8 | Every verb the library Button; web baseline zero branch-new | GLASS: the raw-button census inside each test of `test_philo9_03_room_face_glass.py`; `scripts/check_web_baseline.py --run` (story 03 evidence). EXCLUDED: structural |

### Story 04: the desk debts

| # | Criterion | Disposition |
|---|---|---|
| 1 | Selection ≥ 3:1 at 1440 and 393 | GLASS `tests/e2e/test_philo9_04_desk_debts_glass.py::test_the_selection_is_visible` (+ editor, composer). EXCLUDED as an atlas case: `excluded.p9.selection_and_text_floor` (no computed-style predicate) |
| 2 | No list text under 12 px | GLASS `::test_the_list_text_is_12px_and_readable`, `::test_the_open_row_menu_text_is_12px`. EXCLUDED (same) |
| 3 | "SHOWN" for any count | ATLAS `case.p9.list_status.shown`. GLASS `::test_the_status_says_shown` |
| 4 | Every kept column in view at 393 | ATLAS `case.p9.list_columns.in_view`. GLASS `::test_every_kept_column_is_in_view` |
| 5 | Sort headers the library Button (mutation) | ATLAS `case.p9.list_sort.zone_pressed`. BACKEND `tests/unit/test_philo9_04_sort_button_fence.py`. GLASS `::test_the_sort_headers_are_the_library_button` |
| 6 | Row menu's last entry in view at 393 | ATLAS `case.p9.list_row_menu.delete_in_view`. GLASS `::test_the_row_menu_keeps_itself_in_view` |
| 7 | Matches the ratified canvas; web baseline zero branch-new | GLASS (all of the above); story 04 evidence web baseline capture. EXCLUDED: a review against a canvas |

### Story 06: the closing use (Codex)

| # | Criterion | Disposition |
|---|---|---|
| 1 | The launch matches the pinned contract | BACKEND `tests/unit/test_philo9_room_job.py::test_the_retained_sessions_are_isolated`, `::test_each_isolation_mutation_is_red`, `::test_the_driver_uses_the_phase7_fences_unchanged`. EXCLUDED from the atlas: a recorded client session, not a rig case |
| 2 | From the catalogue alone; zero repository reads; client events reconcile with hub exchanges | BACKEND `::test_every_retained_session_has_zero_reads_and_used_the_catalogue`, `::test_the_zero_read_fence_fails_on_the_phase5_logs`, `::test_every_client_call_pairs_with_one_hub_exchange_from_the_retained_records`, `::test_a_refused_call_without_the_failed_status_does_not_pair`, `::test_a_shell_command_in_a_retained_session_turns_the_fence_red`. EXCLUDED (same) |
| 3 | Every fixture value read back | BACKEND `::test_the_owner_job_reads_back_every_fixture_value`, `::test_each_content_mutation_is_red`, `::test_a_missing_or_extra_owner_write_is_red`, the fixture fences. EXCLUDED (same) |
| 4 | The AGENT leg | BACKEND `::test_the_agent_leg_refused_then_ran_inside_the_bound`, `::test_the_agent_heard_owner_only_for_mark_delivered_after_the_repair`. EXCLUDED (an agent principal) |
| 5 | Find it cold | BACKEND `::test_find_it_cold_took_project_list_after_the_discovery_repair` |
| 6 | The Room's face at 1440 and 393; the leak fence | BACKEND over retained shots and observations: `::test_the_room_face_shows_every_fixture_value_at_both_widths`, `::test_each_face_mutation_is_red`, `::test_every_face_shot_is_retained`, `::test_no_retained_story06_record_holds_an_email_or_a_token`, `::test_the_leak_fence_turns_red_on_a_planted_value` |
| 7 | The owner reviews the shots | EXCLUDED: the owner's act (reviewed 2026-09-28, story 06 evidence) |

### Story 07: the project delegation grant

| # | Criterion | Disposition |
|---|---|---|
| 1 | A real PROJECT credential over MCP and HTTP: refused without a grant, runs with a LIVE one naming the delegation | BACKEND `tests/unit/test_philo9_project_grant.py::test_run_is_refused_without_a_grant_and_runs_with_one_naming_the_delegation[mcp,http]`, `::test_publish_is_refused_without_a_grant_and_publishes_with_one[mcp,http]`, `::test_stop_of_its_own_run_is_refused_without_the_grant_and_stops_with_it[mcp,http]`. EXCLUDED from the atlas: `excluded.p9.agent_side_grant` (the rig speaks with the owner's token only) |
| 2 | Children as R4-1 settles; a revoke mid-run; stop on another actor's run refused | BACKEND `::test_an_agent_runs_children_each_naming_the_grant_and_the_policy`, `::test_a_revoke_mid_run_refuses_the_next_child_with_its_receipt_and_ends_the_run`, `::test_a_revoke_with_no_next_child_still_ends_the_run_refused_and_invents_no_child`, `::test_an_agent_cannot_stop_another_agents_run_in_the_same_project`, `::test_an_agent_named_like_the_owner_cannot_stop_the_owners_run`, `::test_an_agent_named_like_the_scheduler_cannot_stop_the_schedulers_run`. EXCLUDED (agent) |
| 3 | A grant on A does nothing on B; outside the bound refused; mark/archive/configure refused for an agent | BACKEND `::test_a_grant_on_project_a_does_nothing_on_project_b`, `::test_grants_on_two_projects_each_authorise_their_own_project`, `::test_a_granted_agent_cannot_stop_or_publish_project_b_objects_under_a_project_a_grant`, `::test_every_operation_outside_the_bound_stays_refused_with_a_live_grant`, `::test_mark_delivered_archive_and_configure_are_refused_for_an_agent_in_every_case`. EXCLUDED (agent) |
| 4 | Revoke, expiry, credential revoke end the grant; restart and reissue keep LIVE; the beat's interleavings; mutations | BACKEND `::test_revoke_and_expiry_move_the_code`, `::test_the_owners_credential_revoke_ends_the_project_grants_first_and_a_reissue_keeps_a_live_grant`, `tests/unit/test_philo9_project_grant_lifecycle.py` (10), `tests/unit/test_philo9_project_grant_restart.py::test_a_live_project_grant_survives_a_real_restart_and_a_reissue`, story 07 `mutations.py` M1–M15. The OWNER's side on the face — GLASS: the owner's Stop (revoke) `tests/e2e/test_philo9_07_project_grant_glass.py::test_allow_stop_refused_and_two_projects_on_the_rendered_row` (STOPPED, `owner_revoked`, the kernel's `project.delegation.revoke` receipt), expiry `::test_an_expired_grant_reads_stopped`, the credential revoke `::test_the_owner_revokes_a_credential_the_grant_ends_first_and_the_window_stays_put`. Not an atlas case: the owner-token limit does NOT exclude these (Codex Astra r1); they are proven by the named glass, not by the atlas |
| 5 | Grant and revoke owner-only, admitted, with receipts; an agent refused | BACKEND `::test_the_grant_operations_are_owner_only_admitted_and_in_no_palette`, `::test_a_malformed_grant_body_and_an_unknown_project_are_refused_with_receipts`, `::test_a_revoke_with_no_live_grant_is_refused_with_its_receipt`. ATLAS (owner grant): `case.p9.grant.project_allowed`, `case.p9.grant_route.project_allowed` |
| 6 | The grant face as ratified at 1440 and 393, incl. a LIVE grant with no credential row and Remote Access OFF, after each change; DESK reads DESK | ATLAS `case.p9.grant.project_allowed` (Allow), `case.p9.grant.desk_reads_desk`. GLASS for the orphan (a LIVE grant with no credential, Remote ON and OFF): `::test_live_grants_with_no_credential_show_on_and_off_and_the_last_stop_keeps_its_receipt[1440,393]`; Remote Access OFF with a credential: `::test_remote_off_keeps_a_credential_with_a_live_project_grant[1440,393]`; archived: `::test_archive_keeps_the_stop_and_its_receipt_on_and_off[1440,393]`; the wire `tests/unit/test_philo9_project_grant.py::test_a_desk_credential_reads_back_desk`, `::test_the_wire_projects_each_grant_and_lists_project_orphans_beside_desk_orphans`. Not atlas cases: proven by the named glass (an orphan needs a credential deleted by its own agent token, which the rig does not hold) |

## The counts (at this commit)

| File | Cases | Face | Op / route | Runs (1440 + 393 + headless) |
|---|---|---|---|---|
| `atlas.json` | 85 | — | — | 136 |
| `atlas-phase3.json` | 36 | — | — | 58 |
| `atlas-phase7.json` | 27 | 9 | 18 | 36 |
| `atlas-phase8.json` | 19 | 14 | 5 | 33 |
| `atlas-phase9.json` | 13 (8 + 5 new) | 11 | 2 | 24 |
| `atlas-phase9-steward.json` | 4 | 0 | 4 | 4 |
| total | 184 | | | 291 |

## The reruns (round two: on the merged tree `b2fd7e8b` = main with #687 + story 05's atlas; `--engine none`; every run its own hub, HOME and directory)

- **Phase 9, 28 runs, serial:** 28 of 28 pass (`assets/story-05-shots/p9-merged/`, each run's directory with its observation and shots; capture 18:46:10Z). Every face case passes at 1440 and 393; the 6 op/route cases pass headless.
- **Phase 7 and Phase 8, 69 runs, serial:** 69 of 69 pass (36 + 33; `p78-merged/`, observations and shots; capture 18:51:03Z).
- **The base atlas and Phase 3 (194 runs per product, 3 at a time; captures 19:11:15Z merged, 19:27:08Z `294632c0`):** the same instrument on an export of `294632c0` (main just before story 01, its own web build and package) and on the merged tree: 109 pass→pass, 77 blocked→blocked, 6 fail→fail, 1 not_applicable→not_applicable, and one row blocked→pass: s5 at 393 (the input-precondition defect, round two row 4). **0 runs pass before and not after** (`base_diff.py`, exit 0 this time; round one's capture exit 1 is kept). Every run's observation is kept (`base-294632c0/`, `base-merged/`); their shots are not (about 200 MB for 388 runs), named here. The first base-294632c0 capture of round two (19:11:10Z, exit 1) is a wrapper bug (`${ROOT:+--root $ROOT}` passed as one word), fixed and re-run (the next capture).
- Round one's parallel pass (load 18–23: `delete_twice.both_gone` 1440 and `list_status.shown` BLOCKED) is not evidence; its serial reruns are.

## The equivalence (face ↔ its twin, one build)

| Durable outcome | Browser (face) | Twin | Same values | Receipt with actor |
|---|---|---|---|---|
| Mark delivered, To Priya | `case.p9.update.delivered_row` pass ×2 (round two: the click's own 200, delivery row and owner's receipt; the hub's stored delivery; the face's words) | `case.p9.update.delivered_row.op` (MCP) pass; story 02's `mark_delivered_receipted` pass | recipient `Priya` (fenced); one delivery row whose `operation_id` is the mark's | `kernel.receipt.read`: `project.mark_update_delivered`, succeeded, `actor_kind` owner |
| Allow run and publish on a project | `case.p9.grant.project_allowed` pass ×2 (the route's 200 and the owner's receipt read on the face's own call; the ledger reads LIVE) | `case.p9.grant_route.project_allowed` (HTTP; the grant has no MCP tool by the charter) pass | the same route, identity and LIVE state (fenced) | `/api/kernel/read`: `project.delegation.grant`, succeeded, owner, target the project |
| Never checked | `case.p9.connections.never_checked_face` pass ×2 (face + `GET /api/connections`) | story 02's `case.p9.connections.never_checked` (MCP `connection.list`) pass | github `never_checked`, no check time — both predicates compared by the fence (m10 red) | a read: no operation, no receipt (the op case asserts none) |
| Steward run, archive | excluded (face: F3 glass) | story 02's op cases pass | — | receipts read in the op cases |

The api ↔ MCP equivalence of every durable outcome AND every refusal is the stories' own fences, rerun here on merged main: `test_philo9_compat.py`, `test_philo9_room_contract.py`, `test_philo9_mark_delivered.py`, `test_philo9_delivery_record.py`, `test_philo9_project_grant.py`, `test_philo9_steward_admission.py`, `test_philo9_rig_op.py`, `test_philo9_02_rig_op.py` (177 tests), inside the 424 passed of capture 17:51:45Z. No Phase 9 atlas case is a refusal case; the refusals' equivalence is in those fences, not in the atlas. **Real and replayed:** every atlas run here is `--engine none`; no case declares a provider replay, so no replayed run exists to keep apart.

## Red on main (the story 05 cases on `1f332bc3`, main before stories 02, 03, 07; round-two capture 19:07:24Z, every run's directory kept under `red-1f332bc3/<case>--<width>/`)

| Case | 1440 | 393 | Reading |
|---|---|---|---|
| `case.p9.grant.desk_reads_desk` | **fail** | **fail** | the wire: 0 rows match `{identity: desk-agent, palette: DESK}` (it reads `ALL`); the row's token reads `ALL` |
| `case.p9.connections.never_checked_face` | **fail** | **fail** | the chip reads `SIGN IN`; the list probed on read |
| `case.p9.update.delivered_row` | blocked | blocked | the update row's `[data-update-id=…]` is not on main's face (the click times out): story 03's own record, a new capability, no red claimed |
| `case.p9.grant.project_allowed` | blocked | blocked | no `Projects` Disclosure: a new capability, no red claimed |
| `case.p9.grant_route.project_allowed` | blocked (headless) | — | the route does not exist on main: never counted as a red |
| `case.p9.update.delivered_row.op` | blocked (headless) | — | `project.mark_update_delivered` does not exist on main: never counted as a red |

The two reds are for defects stories 02 and 07 already recorded red with their glass; these atlas reds corroborate them and claim nothing new.

## Unknown / not done

- The agent side of the grant is not an atlas case (the rig has no agent principal; rig work, excluded with the reason).
- The base atlas runs keep observations, not shots (size).
- Round one's s5 extra attempts (`base-flake-s5-more/`) kept TSVs only; their observations were lost with the round-one copier. The classification now rests on the code (`BRIEF_CAP`) and Codex's reproduction, not on those attempts.
- The 324 s summary wait on `294632c0` is not diagnosed (BACKLOG).

## Proof

### Captured run — 2026-09-28T17:51:45Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/fences.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9ae0eb82a0c0b2f7b1c93a72d5782aab94d507c2

```text
HEAD = 79fdee3c01d529c0f3f98ebc7d4b9620b7cfca06
........................................................................ [ 84%]
................................................................         [100%]
424 passed in 46.78s
m1 (23): RED - 7 failed, 36 passed in 0.49s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_every_case_reference_inside_the_atlas_resolves-atlas-phase9.json]', 'FAILED te
m2 (27): RED - 2 failed, 41 passed in 0.45s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_face_cases_carry_both_ruled_viewports-atlas-phase9.json]', 'FAILED tests/unit/
m3 (31): RED - 1 failed, 42 passed in 0.44s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_admitted_write_twin_reads_its_receipt_with_its_actor']
m4 (36): RED - 1 failed, 42 passed in 0.42s; ['FAILED tests/unit/test_philo9_atlas.py::test_no_trigger_is_optional_and_no_optional_step_is_the_outcome']
m5 (40): RED - 1 failed, 42 passed in 0.41s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_face_case_without_a_twin_is_excluded_with_a_reason']
m6 (44): RED - 1 failed, 42 passed in 0.39s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values']
m7 (50): RED - 1 failed, 42 passed in 0.43s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_every_desk_face_case_crosses_the_gate_first-atlas-phase9.json]']
m8 (54): RED - 2 failed, 41 passed in 0.46s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_api_step_exists_in_the_generated_openapi[atlas-phase9.json]', 'FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read
8 red, 0 missed
```

### Captured run — 2026-09-28T17:52:51Z

- **Command:** `env SHOTS=1 zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh p9-merged 1 docs/internal/philo/graph/atlas-phase9.json docs/internal/philo/graph/atlas-phase9-steward.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9ae0eb82a0c0b2f7b1c93a72d5782aab94d507c2

```text
HEAD = 79fdee3c01d529c0f3f98ebc7d4b9620b7cfca06; load { 5.76 6.22 8.38 }
✓ built in 4.73s
28 runs, 1 at a time; out /Users/karol/dev/tools/wt-philo-9-05/.tmp/s05/p9-merged
atlas-phase9.json	case.p9.list_status.shown	1440	pass	21	5.54	predicate: '2 SHOWN OF 2' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1156, 'y': 76, 'w': 95, 'h': 16}
atlas-phase9.json	case.p9.list_status.shown	393	pass	15	7.10	predicate: '2 SHOWN OF 2' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 29, 'y': 127, 'w': 95, 'h': 16}
atlas-phase9.json	case.p9.list_columns.in_view	1440	pass	22	6.70	predicate: 'PERSONAL' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 179, 'y': 174, 'w': 1082, 'h': 41}
atlas-phase9.json	case.p9.list_columns.in_view	393	pass	15	7.41	predicate: 'PERSONAL' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 19, 'y': 249, 'w': 355, 'h': 78}
atlas-phase9.json	case.p9.list_sort.zone_pressed	1440	pass	22	7.68	predicate: aria-pressed='true', wanted 'true'
atlas-phase9.json	case.p9.list_sort.zone_pressed	393	pass	15	9.48	predicate: aria-pressed='true', wanted 'true'
atlas-phase9.json	case.p9.list_row_menu.delete_in_view	1440	pass	21	8.41	predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 206, 'y': 847, 'w': 272, 'h': 28}
atlas-phase9.json	case.p9.list_row_menu.delete_in_view	393	pass	14	13.82	predicate: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 11, 'y': 797, 'w': 371, 'h': 44}
atlas-phase9.json	case.p9.room_items.late_row	1440	pass	9	12.30	predicate: 'DAYS LATE' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 668, 'y': 361, 'w': 125, 'h': 18}
atlas-phase9.json	case.p9.room_items.late_row	393	pass	9	10.94	predicate: 'DAYS LATE' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 31, 'y': 571, 'w': 125, 'h': 18}
atlas-phase9.json	case.p9.update_list.head_updates	1440	pass	10	9.87	predicate: 'UPDATES 1' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 43, 'y': 167, 'w': 71, 'h': 18}
atlas-phase9.json	case.p9.update_list.head_updates	393	pass	9	9.19	predicate: 'UPDATES 1' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 19, 'y': 531, 'w': 71, 'h': 18}
atlas-phase9.json	case.p9.update.delivered_row	1440	pass	10	8.08	predicate: 'Priya' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 39, 'y': 274, 'w': 770, 'h': 26}
atlas-phase9.json	case.p9.update.delivered_row	393	pass	10	7.43	predicate: 'Priya' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 348, 'w': 363, 'h': 72}
atlas-phase9.json	case.p9.room_steward_verb.owned	1440	pass	10	13.21	predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 731, 'y': 432, 'w': 68, 'h': 24}
atlas-phase9.json	case.p9.room_steward_verb.owned	393	pass	10	11.96	predicate: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 300, 'y': 350, 'w': 68, 'h': 24}
atlas-phase9.json	case.p9.grant.project_allowed	1440	pass	10	10.88	predicate: all_of: protocol_status: PUT /api/settings/remote/delegations/sweep-runner/projects/proj-8e553fb147c9 answered 200, wanted 200 (body sha256 aadd2a5f70f2); respons
atlas-phase9.json	case.p9.grant.project_allowed	393	pass	10	9.90	predicate: all_of: protocol_status: PUT /api/settings/remote/delegations/sweep-runner/projects/proj-7a9ab5aba923 answered 200, wanted 200 (body sha256 a7e135da0eb2); response 
atlas-phase9.json	case.p9.grant_route.project_allowed	op	pass	3	9.05	predicate: GET /api/settings/remote answered 200 with one row {'identity': 'sweep-runner', 'project_delegations.0.project_id': 'proj-b4121b0ddb9e', 'project_delegations.0.
atlas-phase9.json	case.p9.grant.desk_reads_desk	1440	pass	10	9.05	predicate: all_of: protocol_reads: GET /api/settings/remote answered 200 with one row {'identity': 'desk-agent', 'palette': 'DESK'} | readable_text: 'DESK' is readable in vie
atlas-phase9.json	case.p9.grant.desk_reads_desk	393	pass	10	8.19	predicate: all_of: protocol_reads: GET /api/settings/remote answered 200 with one row {'identity': 'desk-agent', 'palette': 'DESK'} | readable_text: 'DESK' is readable in view
atlas-phase9.json	case.p9.connections.never_checked_face	1440	pass	9	7.39	predicate: all_of: readable_text: 'NEVER CHECKED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 131, 'y': 190, 'w': 137, 'h': 18} | protocol_
atlas-phase9.json	case.p9.connections.never_checked_face	393	pass	9	6.41	predicate: all_of: readable_text: 'NEVER CHECKED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 24, 'y': 231, 'w': 137, 'h': 18} | protocol_rea
atlas-phase9.json	case.p9.update.delivered_row.op	op	pass	3	6.29	predicate: all 7 facts hold: observe_at updates holds; observe_at updates.0.deliveries holds; observe_at updates.0.deliveries.0.delivered_to holds; observe_at updates.0.delive
atlas-phase9-steward.json	case.p9.steward.run_receipted	op	pass	3	6.29	predicate: all 9 facts hold: observe_at run.state holds; observe_at operation_id holds; observe_at receipt.outcome holds; the trigger receipt holds; op read #0 (kernel.r
atlas-phase9-steward.json	case.p9.update.mark_delivered_receipted	op	pass	3	5.94	predicate: all 7 facts hold: observe_at updates holds; observe_at updates.0.deliveries holds; observe_at updates.0.deliveries.0.operation_id holds; observe_at 
atlas-phase9-steward.json	case.p9.project.archive_receipted	op	pass	3	5.94	predicate: all 5 facts hold: observe_at is_archived holds; the trigger success holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (ke
atlas-phase9-steward.json	case.p9.connections.never_checked	op	pass	3	5.63	predicate: all 4 facts hold: the trigger tools holds; the trigger tools holds; the trigger operation_id is absent; observe_at tools holds
TOTAL 28 runs: 28 pass, 0 not pass
```

### Captured run — 2026-09-28T18:08:57Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh p78-merged 1 docs/internal/philo/graph/atlas-phase7.json docs/internal/philo/graph/atlas-phase8.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9ae0eb82a0c0b2f7b1c93a72d5782aab94d507c2

```text
HEAD = 79fdee3c01d529c0f3f98ebc7d4b9620b7cfca06; load { 5.80 4.32 5.78 }
✓ built in 4.25s
69 runs, 1 at a time; out /Users/karol/dev/tools/wt-philo-9-05/.tmp/s05/p78-merged
atlas-phase7.json	case.p7.zone_create.visible	1440	pass	19	5.42	predicate: 'Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 96, 'w': 382, 'h': 26}
atlas-phase7.json	case.p7.zone_create.visible	393	pass	20	8.10	predicate: 'Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 74, 'w': 363, 'h': 26}
atlas-phase7.json	case.p7.zone_file.note_in_zone	1440	pass	10	8.52	predicate: 'Filed · Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1055, 'y': 161, 'w': 98, 'h': 18}
atlas-phase7.json	case.p7.zone_file.note_in_zone	393	pass	11	7.81	predicate: 'Filed · Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 33, 'y': 403, 'w': 98, 'h': 18}
atlas-phase7.json	case.p7.zone_file.refile_moves	1440	pass	12	7.17	predicate: 'Filed · Atlas zone B' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1055, 'y': 161, 'w': 109, 'h': 18}
atlas-phase7.json	case.p7.zone_file.refile_moves	393	pass	12	6.70	predicate: 'Filed · Atlas zone B' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 33, 'y': 403, 'w': 109, 'h': 18}
atlas-phase7.json	case.p7.zone_unfile.note_leaves	1440	pass	10	6.27	predicate: '+ Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1045, 'y': 189, 'w': 354, 'h': 170}
atlas-phase7.json	case.p7.zone_unfile.note_leaves	393	pass	10	6.27	predicate: '+ Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 23, 'y': 431, 'w': 347, 'h': 170}
atlas-phase7.json	case.p7.kb_create.visible	1440	pass	11	6.46	predicate: 'New Knowledge' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 145, 'w': 382, 'h': 26}
atlas-phase7.json	case.p7.kb_create.visible	393	pass	11	5.94	predicate: 'New Knowledge' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 123, 'w': 363, 'h': 26}
atlas-phase7.json	case.p7.kb_member.add_and_remove	1440	pass	10	5.40	predicate: '+ Atlas knowledge' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1045, 'y': 189, 'w': 354, 'h': 137}
atlas-phase7.json	case.p7.kb_member.add_and_remove	393	pass	10	5.09	predicate: '+ Atlas knowledge' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 23, 'y': 464, 'w': 347, 'h': 137}
atlas-phase7.json	case.p7.decision_status.review_list	1440	pass	12	4.76	predicate: 'Review decision: Atlas review decision' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 302, 'w': 928, 'h': 54}
atlas-phase7.json	case.p7.decision_status.review_list	393	pass	11	4.14	predicate: 'Review decision: Atlas review decision' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 383, 'w': 369, 'h': 103}
atlas-phase7.json	case.p7.decision_supersede.successor_visible	1440	pass	9	3.81	predicate: 'Supersedes Atlas old decision' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1037, 'y': 117, 'w': 370, 'h': 56}
atlas-phase7.json	case.p7.decision_supersede.successor_visible	393	pass	9	3.83	predicate: 'Supersedes Atlas old decision' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 449, 'w': 363, 'h': 112}
atlas-phase7.json	case.p7.decision_delete.gone	1440	pass	34	3.68	predicate: 'Removal committed' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 651, 'y': 748, 'w': 138, 'h': 27}
atlas-phase7.json	case.p7.decision_delete.gone	393	pass	25	6.81	predicate: 'Removal committed' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 127, 'y': 628, 'w': 138, 'h': 27}
atlas-phase7.json	case.p7.zone_create.visible.op	op	pass	3	7.53	predicate: all 5 facts hold: observe_at directory.id holds; observe_at directory.name holds; observe_at directory.parent_id holds; op read #0 (zone.list) <root> holds; the trig
atlas-phase7.json	case.p7.zone_file.note_in_zone.op	op	pass	3	7.01	predicate: all 10 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.rec
atlas-phase7.json	case.p7.zone_file.refile_moves.op	op	pass	4	7.01	predicate: all 16 facts hold: observe_at <root> holds; op read #0 (zone.members) <root> holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read
atlas-phase7.json	case.p7.zone_unfile.note_leaves.op	op	pass	3	6.53	predicate: all 17 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.re
atlas-phase7.json	case.p7.kb_create.visible.op	op	pass	3	6.32	predicate: all 4 facts hold: observe_at id holds; observe_at name holds; op read #0 (kb.list) <root> holds; the trigger operation_id is absent
atlas-phase7.json	case.p7.kb_member.add_and_remove.op	op	pass	3	6.32	predicate: all 15 facts hold: observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.op
atlas-phase7.json	case.p7.decision_status.review_list.op	op	pass	3	6.14	predicate: all 9 facts hold: observe_at status holds; observe_at id holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.rec
atlas-phase7.json	case.p7.decision_supersede.successor_visible.op	op	pass	3	6.14	predicate: all 6 facts hold: observe_at status holds; observe_at superseded_by holds; op read #0 (decision.read) id holds; op read #0 (decision.read) deleted h
atlas-phase7.json	case.p7.decision_supersede.receipt.op	op	pass	3	5.73	predicate: all 9 facts hold: observe_at objects.0.receipt.operation_id holds; observe_at objects.0.operation.name holds; observe_at objects.0.receipt.state holds; observ
atlas-phase7.json	case.p7.decision_delete.gone.op	op	pass	3	5.35	predicate: all 9 facts hold: observe_at <root> holds; op read #0 (decision.read) error holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1
atlas-phase7.json	case.p7.decision_create.receipt.op	op	pass	3	5.35	predicate: all 7 facts hold: observe_at objects.0.receipt.operation_id holds; observe_at objects.0.operation.name holds; observe_at objects.0.receipt.state holds; observe_a
atlas-phase7.json	case.p7.zone_file.refused_unknown_zone.op	op	pass	3	5.16	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0
atlas-phase7.json	case.p7.kb_member.refused_bad_ref.op	op	pass	3	5.16	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.rece
atlas-phase7.json	case.p7.decision_status.refused_invalid.op	op	pass	3	4.91	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.
atlas-phase7.json	case.p7.decision_delete.refused_unknown.op	op	pass	3	4.91	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.
atlas-phase7.json	case.j1.first_words_keep_as_note.kept.op	op	pass	3	4.75	predicate: all 5 facts hold: observe_at id holds; observe_at body_markdown holds; observe_at title holds; op read #0 (note.list) <root> holds; the trigger operation_i
atlas-phase7.json	case.j11.write_a_thought.window_open.op	op	pass	3	4.75	predicate: all 3 facts hold: observe_at thought.id holds; observe_at thought.working_note.id holds; the trigger operation_id is absent
atlas-phase7.json	case.j11.thought_keep.kept.op	op	pass	3	4.45	predicate: all 4 facts hold: observe_at id holds; observe_at body_markdown holds; op read #0 (note.list) <root> holds; the trigger operation_id is absent
atlas-phase8.json	case.p8.zone_create.second_unnamed	1440	pass	31	4.45	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 d6f02f4912cd) | protocol_reads: GET /api/directories answered 200 with on
atlas-phase8.json	case.p8.zone_create.second_unnamed	393	pass	17	5.27	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 594c0efd6558) | protocol_reads: GET /api/directories answered 200 with one
atlas-phase8.json	case.p8.zone_create.second_unnamed_floor	1440	pass	38	5.35	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 c82bd38c88f3) | protocol_reads: GET /api/directories answered 200 w
atlas-phase8.json	case.p8.zone_create.second_unnamed_floor	393	pass	23	7.34	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 235398b43be8) | protocol_reads: GET /api/directories answered 200 wi
atlas-phase8.json	case.p8.zone_rename.list	1440	pass	25	7.13	predicate: all_of: readable_text: 'Platform' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y': 297, 'w': 53, 'h': 24} | protocol_reads: GET /api/dir
atlas-phase8.json	case.p8.zone_rename.list	393	pass	14	7.19	predicate: all_of: readable_text: 'Platform' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 469, 'w': 90, 'h': 38} | protocol_reads: GET /api/direct
atlas-phase8.json	case.p8.zone_rename.name_taken_list	1440	pass	24	6.94	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y': 339, 'w': 112, 'h': 18} | protocol_reads
atlas-phase8.json	case.p8.zone_rename.name_taken_list	393	pass	14	8.39	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 498, 'w': 112, 'h': 18} | protocol_reads: G
atlas-phase8.json	case.p8.zone_rename.name_taken_floor	1440	pass	30	8.51	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1208, 'y': 167, 'w': 112, 'h': 18} | protocol_rea
atlas-phase8.json	case.p8.zone_rename.name_taken_floor	393	pass	20	9.34	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 14, 'y': 315, 'w': 112, 'h': 18} | protocol_reads: 
atlas-phase8.json	case.p8.zone_rename.f2_row	1440	pass	17	9.08	predicate: all_of: input_value: value is 'Inbox', wanted 'Inbox' | hit_target: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y':
atlas-phase8.json	case.p8.zone_rename.f2_row	393	pass	12	8.95	predicate: all_of: input_value: value is 'Inbox', wanted 'Inbox' | hit_target: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 29
atlas-phase8.json	case.p8.chair.no_new_zone	1440	pass	9	8.31	predicate: 'No matching tools or Desk items.' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 73, 'w': 382, 'h': 44}
atlas-phase8.json	case.p8.chair.no_new_zone	393	pass	9	7.41	predicate: 'No matching tools or Desk items.' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 51, 'w': 363, 'h': 44}
atlas-phase8.json	case.p8.list_delete.gone	1440	pass	36	6.90	predicate: all_of: protocol_reads: GET /api/decisions/decision_006112cbcf67 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 1440, 'height': 900
atlas-phase8.json	case.p8.list_delete.gone	393	pass	24	7.36	predicate: all_of: protocol_reads: GET /api/decisions/decision_2a1ce1a1fd8e answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 393, 'height': 852} 
atlas-phase8.json	case.p8.list_delete.undo	1440	pass	29	12.18	predicate: all_of: protocol_reads: GET /api/decisions/decision_3c3f50e840de answered 200 | readable_text: 'Restored Atlas list delete' is readable in viewport {'width': 1440, 'he
atlas-phase8.json	case.p8.list_delete.undo	393	pass	15	10.96	predicate: all_of: protocol_reads: GET /api/decisions/decision_d4b1b1103674 answered 200 | readable_text: 'Restored Atlas list delete' is readable in viewport {'width': 393, 'heig
atlas-phase8.json	case.p8.list_delete.long_list_393	1440	pass	35	10.01	predicate: all_of: protocol_reads: GET /api/decisions/decision_41eefcf445db answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 1440, 'he
atlas-phase8.json	case.p8.list_delete.long_list_393	393	pass	23	11.33	predicate: all_of: protocol_reads: GET /api/decisions/decision_1c045c940fa7 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 393, 'heig
atlas-phase8.json	case.p8.delete_twice.both_gone	1440	pass	43	10.92	predicate: all_of: protocol_reads: GET /api/decisions/decision_c27a569967f7 answered 404; GET /api/decisions/decision_af019cc65e3b answered 404 | readable_text: 'Removal co
atlas-phase8.json	case.p8.delete_twice.both_gone	393	pass	29	12.53	predicate: all_of: protocol_reads: GET /api/decisions/decision_d0af3dd821ea answered 404; GET /api/decisions/decision_4c467014e6b4 answered 404 | readable_text: 'Removal com
atlas-phase8.json	case.p8.delete_then_leave.gone	1440	pass	27	10.91	predicate: all_of: protocol_status: DELETE /api/decisions/decision_c36e490ad7f3 answered 200, wanted 200 (body sha256 766359e22f3d) | protocol_reads: GET /api/decisions/dec
atlas-phase8.json	case.p8.delete_then_leave.gone	393	pass	18	10.25	predicate: all_of: protocol_status: DELETE /api/decisions/decision_90d4e34cb884 answered 200, wanted 200 (body sha256 dc555afae025) | protocol_reads: GET /api/decisions/deci
atlas-phase8.json	case.p8.chair.delete_withheld	1440	pass	22	9.25	predicate: all_of: readable_text: 'Open the Floor or the list' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 96, 'w': 382, 'h': 26} | attr
atlas-phase8.json	case.p8.chair.delete_withheld	393	pass	16	9.02	predicate: all_of: readable_text: 'Open the Floor or the list' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 74, 'w': 363, 'h': 26} | attr_equ
atlas-phase8.json	case.p8.decision_heads.hidden	1440	pass	10	8.06	predicate: all_of: readable_text: 'DECISION CONTEXT' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1037, 'y': 117, 'w': 370, 'h': 94} | text_absent: 
atlas-phase8.json	case.p8.decision_heads.hidden	393	pass	10	7.75	predicate: all_of: readable_text: 'DECISION CONTEXT' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 439, 'w': 363, 'h': 122} | text_absent: 'CO
atlas-phase8.json	case.p8.zone_create.second_unnamed.op	op	pass	3	7.21	predicate: all 3 facts hold: observe_at <root> holds; observe_at <root> holds; the trigger operation_id is absent
atlas-phase8.json	case.p8.zone_rename.list.op	op	pass	3	6.71	predicate: all 3 facts hold: observe_at directory.id holds; observe_at directory.name holds; the trigger operation_id is absent
atlas-phase8.json	case.p8.zone_rename.name_taken_list.op	op	pass	3	6.25	predicate: all 3 facts hold: the trigger error holds; the trigger existing_name holds; observe_at directory.name holds
atlas-phase8.json	case.p8.list_delete.gone.op	op	pass	3	6.25	predicate: all 7 facts hold: observe_at <root> holds; op read #0 (decision.read) error holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1 (ke
atlas-phase8.json	case.p8.delete_twice.both_gone.op	op	pass	3	5.91	predicate: all 10 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.rec
TOTAL 69 runs: 69 pass, 0 not pass
```

### Captured run — 2026-09-28T18:24:42Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/red_main.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9ae0eb82a0c0b2f7b1c93a72d5782aab94d507c2

```text
base = 1f332bc3c85a8fdfd1a0c0ba9e5a113d61d17777
✓ built in 4.39s
case.p9.grant.project_allowed 1440 exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: ui step click on "button[aria-label='Projects: sweep-runner']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
case.p9.grant.project_allowed 393 exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: ui step click on "button[aria-label='Projects: sweep-runner']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
case.p9.grant_route.project_allowed op exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: capture_as 'grant_op': no value at 'operation_id' in the response of PUT /api/settings/remote/delegations/sweep-runner/projects/proj-b2e4c4d92528
case.p9.grant.desk_reads_desk 1440 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part protocol_reads: GET /api/settings/remote: 0 row(s) at 'credentials' match {'identity': 'desk-agent', 'palette': 'DESK'}; exactly one is required
case.p9.grant.desk_reads_desk 393 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part protocol_reads: GET /api/settings/remote: 0 row(s) at 'credentials' match {'identity': 'desk-agent', 'palette': 'DESK'}; exactly one is required
case.p9.connections.never_checked_face 1440 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part readable_text: 'NEVER CHECKED' NOT in observe_at text
case.p9.connections.never_checked_face 393 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part readable_text: 'NEVER CHECKED' NOT in observe_at text
case.p9.update.delivered_row.op op exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: capture_as 'mark_op': no value at 'operation_id' in the decoded response of operation 'project.mark_update_delivered'
```

### Captured run — 2026-09-28T18:27:47Z

- **Command:** `python3 pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/base_diff.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 9ae0eb82a0c0b2f7b1c93a72d5782aab94d507c2

```text
  76  before blocked         after blocked
   1  before blocked         after pass
   6  before fail            after fail
   1  before not_applicable  after not_applicable
   1  before pass            after blocked
 109  before pass            after pass
DIFF atlas-phase3.json case.closure.chain.s5_next_day_brief_more_opened 1440: pass -> blocked
     before: predicate: 'Keep summary retrieval on the local desk' in observe_at text
     after:  BLOCKED: ui step wait_for on '[data-testid=arrival-brief-more]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
DIFF atlas-phase3.json case.closure.chain.s5_next_day_brief_more_opened 393: blocked -> pass
     before: BLOCKED: ui step wait_for on '[data-testid=arrival-brief-more]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
     after:  predicate: 'Keep summary retrieval on the local desk' in observe_at text
194 runs; 1 pass before and not after
```

### Captured run — 2026-09-28T18:30:07Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 21b3b50712fde932b6e59418a7e26e1ae3c61203

```text
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:6> python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.004s

OK
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:6> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:7> python3 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:7> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:8> python3 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/initial-findings.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/source-checklist.md docs/internal/philo/SRS.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:8> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:9> python3 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:9> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:10> python3 scripts/philo_api_reference.py --check
API reference checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:10> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:11> python3 scripts/philo_boundary_census.py --check
Boundary candidate census checked
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:11> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:12> python3 scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:12> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:13> python3 scripts/philo_config_reference.py --check
Configuration declaration reference is current
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:13> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:14> python3 scripts/philo_graph_reference.py --check
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:14> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:15> python3 scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:15> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:16> python3 scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:16> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:17> python3 scripts/check_doc_coverage.py --check
Documentation coverage checked.
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:17> echo 'rc=0'
rc=0
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:18> .venv/bin/python scripts/philo_openapi_reference.py --check
OpenAPI: 572 paths
+pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:18> echo 'rc=0'
rc=0
```

### Captured run — 2026-09-28T18:46:10Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh p9-merged 1 docs/internal/philo/graph/atlas-phase9.json docs/internal/philo/graph/atlas-phase9-steward.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 87a8009459a9a0bf46c89018b7cc49378b1f0ee7

```text
HEAD = b2fd7e8ba9f9f90470e973fc36fe07d056825d85; load { 2.54 3.57 4.30 }
✓ built in 4.34s
28 runs, 1 at a time; out /Users/karol/dev/tools/wt-philo-9-05/.tmp/s05/p9-merged
atlas-phase9.json	case.p9.list_status.shown	1440	pass	21	2.82	predicate: '2 SHOWN OF 2' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1156, 'y': 76, 'w': 95, 'h': 16}	case.p9.list_status.shown--1440/20260928T184614Z
atlas-phase9.json	case.p9.list_status.shown	393	pass	15	4.56	predicate: '2 SHOWN OF 2' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 29, 'y': 127, 'w': 95, 'h': 16}	case.p9.list_status.shown--393/20260928T184636Z-cas
atlas-phase9.json	case.p9.list_columns.in_view	1440	pass	21	5.22	predicate: 'PERSONAL' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 179, 'y': 174, 'w': 1082, 'h': 41}	case.p9.list_columns.in_view--1440/20260928T184
atlas-phase9.json	case.p9.list_columns.in_view	393	pass	15	5.44	predicate: 'PERSONAL' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 19, 'y': 249, 'w': 355, 'h': 78}	case.p9.list_columns.in_view--393/20260928T184712Z-
atlas-phase9.json	case.p9.list_sort.zone_pressed	1440	pass	21	5.23	predicate: aria-pressed='true', wanted 'true'	case.p9.list_sort.zone_pressed--1440/20260928T184727Z-case.p9.list_sort.zone_pressed-muaddib-1440
atlas-phase9.json	case.p9.list_sort.zone_pressed	393	pass	15	4.84	predicate: aria-pressed='true', wanted 'true'	case.p9.list_sort.zone_pressed--393/20260928T184748Z-case.p9.list_sort.zone_pressed-muaddib-393
atlas-phase9.json	case.p9.list_row_menu.delete_in_view	1440	pass	20	4.42	predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 206, 'y': 847, 'w': 272, 'h': 28}	case.p9.list_row_menu.delete_in_v
atlas-phase9.json	case.p9.list_row_menu.delete_in_view	393	pass	15	4.34	predicate: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 11, 'y': 797, 'w': 371, 'h': 44}	case.p9.list_row_menu.delete_in_view
atlas-phase9.json	case.p9.room_items.late_row	1440	pass	9	4.91	predicate: 'DAYS LATE' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 668, 'y': 361, 'w': 125, 'h': 18}	case.p9.room_items.late_row--1440/20260928T184838
atlas-phase9.json	case.p9.room_items.late_row	393	pass	9	4.77	predicate: 'DAYS LATE' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 31, 'y': 571, 'w': 125, 'h': 18}	case.p9.room_items.late_row--393/20260928T184846Z-ca
atlas-phase9.json	case.p9.update_list.head_updates	1440	pass	10	4.42	predicate: 'UPDATES 1' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 43, 'y': 167, 'w': 71, 'h': 18}	case.p9.update_list.head_updates--1440/202609
atlas-phase9.json	case.p9.update_list.head_updates	393	pass	10	4.26	predicate: 'UPDATES 1' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 19, 'y': 531, 'w': 71, 'h': 18}	case.p9.update_list.head_updates--393/20260928T
atlas-phase9.json	case.p9.update.delivered_row	1440	pass	10	4.06	predicate: all_of: protocol_status: POST /api/updates/pupd_3522ca151ad949ce838b0397f2a1cb78/delivered answered 200, wanted 200 (body sha256 dd213215655c); response body contai
atlas-phase9.json	case.p9.update.delivered_row	393	pass	10	4.25	predicate: all_of: protocol_status: POST /api/updates/pupd_28af89ba671345e6bd2b5ac9e5fffe92/delivered answered 200, wanted 200 (body sha256 3312198c293b); response body contain
atlas-phase9.json	case.p9.room_steward_verb.owned	1440	pass	9	4.13	predicate: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 731, 'y': 432, 'w': 68, 'h': 24}	case.p9.room_steward_verb.owned--1440/20
atlas-phase9.json	case.p9.room_steward_verb.owned	393	pass	9	3.96	predicate: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 300, 'y': 350, 'w': 68, 'h': 24}	case.p9.room_steward_verb.owned--393/20260
atlas-phase9.json	case.p9.grant.project_allowed	1440	pass	10	4.05	predicate: all_of: protocol_status: PUT /api/settings/remote/delegations/sweep-runner/projects/proj-ed430e04a0b9 answered 200, wanted 200 (body sha256 92820c18f869); response
atlas-phase9.json	case.p9.grant.project_allowed	393	pass	9	4.05	predicate: all_of: protocol_status: PUT /api/settings/remote/delegations/sweep-runner/projects/proj-70df65cb9263 answered 200, wanted 200 (body sha256 ee5dbbecd081); response b
atlas-phase9.json	case.p9.grant_route.project_allowed	op	pass	3	4.06	predicate: GET /api/settings/remote answered 200 with one row {'identity': 'sweep-runner', 'project_delegations.0.project_id': 'proj-07bd4f2523c4', 'project_delegations.0.
atlas-phase9.json	case.p9.grant.desk_reads_desk	1440	pass	9	3.97	predicate: all_of: protocol_reads: GET /api/settings/remote answered 200 with one row {'identity': 'desk-agent', 'palette': 'DESK'} | readable_text: 'DESK' is readable in view
atlas-phase9.json	case.p9.grant.desk_reads_desk	393	pass	9	3.83	predicate: all_of: protocol_reads: GET /api/settings/remote answered 200 with one row {'identity': 'desk-agent', 'palette': 'DESK'} | readable_text: 'DESK' is readable in viewp
atlas-phase9.json	case.p9.connections.never_checked_face	1440	pass	8	4.08	predicate: all_of: readable_text: 'NEVER CHECKED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 131, 'y': 190, 'w': 137, 'h': 18} | protocol_
atlas-phase9.json	case.p9.connections.never_checked_face	393	pass	8	3.84	predicate: all_of: readable_text: 'NEVER CHECKED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 24, 'y': 231, 'w': 137, 'h': 18} | protocol_rea
atlas-phase9.json	case.p9.update.delivered_row.op	op	pass	3	3.79	predicate: all 7 facts hold: observe_at updates holds; observe_at updates.0.deliveries holds; observe_at updates.0.deliveries.0.delivered_to holds; observe_at updates.0.delive
atlas-phase9-steward.json	case.p9.steward.run_receipted	op	pass	3	3.79	predicate: all 9 facts hold: observe_at run.state holds; observe_at operation_id holds; observe_at receipt.outcome holds; the trigger receipt holds; op read #0 (kernel.r
atlas-phase9-steward.json	case.p9.update.mark_delivered_receipted	op	pass	3	3.72	predicate: all 7 facts hold: observe_at updates holds; observe_at updates.0.deliveries holds; observe_at updates.0.deliveries.0.operation_id holds; observe_at 
atlas-phase9-steward.json	case.p9.project.archive_receipted	op	pass	3	3.72	predicate: all 5 facts hold: observe_at is_archived holds; the trigger success holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (ke
atlas-phase9-steward.json	case.p9.connections.never_checked	op	pass	3	3.50	predicate: all 4 facts hold: the trigger tools holds; the trigger tools holds; the trigger operation_id is absent; observe_at tools holds	case.p9.connections.never_c
TOTAL 28 runs: 28 pass, 0 not pass
retained: 28 rows, 28 run directories, 28 observations
```

### Captured run — 2026-09-28T18:51:03Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh p78-merged 1 docs/internal/philo/graph/atlas-phase7.json docs/internal/philo/graph/atlas-phase8.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 87a8009459a9a0bf46c89018b7cc49378b1f0ee7

```text
HEAD = b2fd7e8ba9f9f90470e973fc36fe07d056825d85; load { 3.50 3.97 4.31 }
✓ built in 4.36s
69 runs, 1 at a time; out /Users/karol/dev/tools/wt-philo-9-05/.tmp/s05/p78-merged
atlas-phase7.json	case.p7.zone_create.visible	1440	pass	20	3.86	predicate: 'Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 96, 'w': 382, 'h': 26}	case.p7.zone_create.visible--1440/20260928T1851
atlas-phase7.json	case.p7.zone_create.visible	393	pass	20	5.00	predicate: 'Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 74, 'w': 363, 'h': 26}	case.p7.zone_create.visible--393/20260928T185128Z-c
atlas-phase7.json	case.p7.zone_file.note_in_zone	1440	pass	10	6.86	predicate: 'Filed · Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1055, 'y': 161, 'w': 98, 'h': 18}	case.p7.zone_file.note_in_zone--1440
atlas-phase7.json	case.p7.zone_file.note_in_zone	393	pass	10	6.27	predicate: 'Filed · Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 33, 'y': 403, 'w': 98, 'h': 18}	case.p7.zone_file.note_in_zone--393/2026
atlas-phase7.json	case.p7.zone_file.refile_moves	1440	pass	12	6.77	predicate: 'Filed · Atlas zone B' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1055, 'y': 161, 'w': 109, 'h': 18}	case.p7.zone_file.refile_moves--1
atlas-phase7.json	case.p7.zone_file.refile_moves	393	pass	12	6.39	predicate: 'Filed · Atlas zone B' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 33, 'y': 403, 'w': 109, 'h': 18}	case.p7.zone_file.refile_moves--393/2
atlas-phase7.json	case.p7.zone_unfile.note_leaves	1440	pass	10	5.78	predicate: '+ Atlas zone' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1045, 'y': 189, 'w': 354, 'h': 170}	case.p7.zone_unfile.note_leaves--1440/2
atlas-phase7.json	case.p7.zone_unfile.note_leaves	393	pass	10	5.36	predicate: '+ Atlas zone' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 23, 'y': 431, 'w': 347, 'h': 170}	case.p7.zone_unfile.note_leaves--393/202609
atlas-phase7.json	case.p7.kb_create.visible	1440	pass	11	5.05	predicate: 'New Knowledge' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 145, 'w': 382, 'h': 26}	case.p7.kb_create.visible--1440/20260928T1852
atlas-phase7.json	case.p7.kb_create.visible	393	pass	11	5.19	predicate: 'New Knowledge' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 123, 'w': 363, 'h': 26}	case.p7.kb_create.visible--393/20260928T185304Z-c
atlas-phase7.json	case.p7.kb_member.add_and_remove	1440	pass	10	5.11	predicate: '+ Atlas knowledge' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1045, 'y': 189, 'w': 354, 'h': 137}	case.p7.kb_member.add_and_remove-
atlas-phase7.json	case.p7.kb_member.add_and_remove	393	pass	10	4.96	predicate: '+ Atlas knowledge' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 23, 'y': 464, 'w': 347, 'h': 137}	case.p7.kb_member.add_and_remove--393
atlas-phase7.json	case.p7.decision_status.review_list	1440	pass	11	4.50	predicate: 'Review decision: Atlas review decision' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 302, 'w': 928, 'h': 54}	case.p7.dec
atlas-phase7.json	case.p7.decision_status.review_list	393	pass	11	4.50	predicate: 'Review decision: Atlas review decision' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 383, 'w': 369, 'h': 103}	case.p7.decis
atlas-phase7.json	case.p7.decision_supersede.successor_visible	1440	pass	9	4.19	predicate: 'Supersedes Atlas old decision' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1037, 'y': 117, 'w': 370, 'h': 56}	case.p7.dec
atlas-phase7.json	case.p7.decision_supersede.successor_visible	393	pass	9	3.77	predicate: 'Supersedes Atlas old decision' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 449, 'w': 363, 'h': 112}	case.p7.decisi
atlas-phase7.json	case.p7.decision_delete.gone	1440	pass	34	3.42	predicate: 'Removal committed' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 651, 'y': 748, 'w': 138, 'h': 27}	case.p7.decision_delete.gone--1440/2026
atlas-phase7.json	case.p7.decision_delete.gone	393	pass	25	6.36	predicate: 'Removal committed' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 127, 'y': 628, 'w': 138, 'h': 27}	case.p7.decision_delete.gone--393/2026092
atlas-phase7.json	case.p7.zone_create.visible.op	op	pass	3	7.67	predicate: all 5 facts hold: observe_at directory.id holds; observe_at directory.name holds; observe_at directory.parent_id holds; op read #0 (zone.list) <root> holds; the trig
atlas-phase7.json	case.p7.zone_file.note_in_zone.op	op	pass	3	7.67	predicate: all 10 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.rec
atlas-phase7.json	case.p7.zone_file.refile_moves.op	op	pass	4	7.21	predicate: all 16 facts hold: observe_at <root> holds; op read #0 (zone.members) <root> holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read
atlas-phase7.json	case.p7.zone_unfile.note_leaves.op	op	pass	3	7.21	predicate: all 17 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.re
atlas-phase7.json	case.p7.kb_create.visible.op	op	pass	3	8.31	predicate: all 4 facts hold: observe_at id holds; observe_at name holds; op read #0 (kb.list) <root> holds; the trigger operation_id is absent	case.p7.kb_create.visible.op--op/20
atlas-phase7.json	case.p7.kb_member.add_and_remove.op	op	pass	3	7.81	predicate: all 15 facts hold: observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.op
atlas-phase7.json	case.p7.decision_status.review_list.op	op	pass	3	7.81	predicate: all 9 facts hold: observe_at status holds; observe_at id holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.rec
atlas-phase7.json	case.p7.decision_supersede.successor_visible.op	op	pass	3	7.26	predicate: all 6 facts hold: observe_at status holds; observe_at superseded_by holds; op read #0 (decision.read) id holds; op read #0 (decision.read) deleted h
atlas-phase7.json	case.p7.decision_supersede.receipt.op	op	pass	3	7.26	predicate: all 9 facts hold: observe_at objects.0.receipt.operation_id holds; observe_at objects.0.operation.name holds; observe_at objects.0.receipt.state holds; observ
atlas-phase7.json	case.p7.decision_delete.gone.op	op	pass	3	6.84	predicate: all 9 facts hold: observe_at <root> holds; op read #0 (decision.read) error holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1
atlas-phase7.json	case.p7.decision_create.receipt.op	op	pass	3	6.84	predicate: all 7 facts hold: observe_at objects.0.receipt.operation_id holds; observe_at objects.0.operation.name holds; observe_at objects.0.receipt.state holds; observe_a
atlas-phase7.json	case.p7.zone_file.refused_unknown_zone.op	op	pass	3	6.45	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0
atlas-phase7.json	case.p7.kb_member.refused_bad_ref.op	op	pass	3	6.45	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.0.rece
atlas-phase7.json	case.p7.decision_status.refused_invalid.op	op	pass	3	6.10	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.
atlas-phase7.json	case.p7.decision_delete.refused_unknown.op	op	pass	3	6.10	predicate: all 8 facts hold: the trigger error holds; observe_at objects.0.receipt.operation_id holds; observe_at objects.0.receipt.state holds; observe_at objects.
atlas-phase7.json	case.j1.first_words_keep_as_note.kept.op	op	pass	3	6.17	predicate: all 5 facts hold: observe_at id holds; observe_at body_markdown holds; observe_at title holds; op read #0 (note.list) <root> holds; the trigger operation_i
atlas-phase7.json	case.j11.write_a_thought.window_open.op	op	pass	3	5.92	predicate: all 3 facts hold: observe_at thought.id holds; observe_at thought.working_note.id holds; the trigger operation_id is absent	case.j11.write_a_thought.window_
atlas-phase7.json	case.j11.thought_keep.kept.op	op	pass	3	5.92	predicate: all 4 facts hold: observe_at id holds; observe_at body_markdown holds; op read #0 (note.list) <root> holds; the trigger operation_id is absent	case.j11.thought_keep.k
atlas-phase8.json	case.p8.zone_create.second_unnamed	1440	pass	32	5.44	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 cf0b5aec4106) | protocol_reads: GET /api/directories answered 200 with on
atlas-phase8.json	case.p8.zone_create.second_unnamed	393	pass	17	6.47	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 b92144f8f295) | protocol_reads: GET /api/directories answered 200 with one
atlas-phase8.json	case.p8.zone_create.second_unnamed_floor	1440	pass	39	8.05	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 fa88c332a4fd) | protocol_reads: GET /api/directories answered 200 w
atlas-phase8.json	case.p8.zone_create.second_unnamed_floor	393	pass	23	7.87	predicate: all_of: protocol_status: POST /api/directories answered 201, wanted 201 (body sha256 9a951e732453) | protocol_reads: GET /api/directories answered 200 wi
atlas-phase8.json	case.p8.zone_rename.list	1440	pass	24	8.54	predicate: all_of: readable_text: 'Platform' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y': 297, 'w': 53, 'h': 24} | protocol_reads: GET /api/dir
atlas-phase8.json	case.p8.zone_rename.list	393	pass	14	9.76	predicate: all_of: readable_text: 'Platform' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 469, 'w': 90, 'h': 38} | protocol_reads: GET /api/direct
atlas-phase8.json	case.p8.zone_rename.name_taken_list	1440	pass	26	9.83	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y': 339, 'w': 112, 'h': 18} | protocol_reads
atlas-phase8.json	case.p8.zone_rename.name_taken_list	393	pass	14	10.31	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 498, 'w': 112, 'h': 18} | protocol_reads: 
atlas-phase8.json	case.p8.zone_rename.name_taken_floor	1440	pass	31	9.95	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1208, 'y': 167, 'w': 112, 'h': 18} | protocol_rea
atlas-phase8.json	case.p8.zone_rename.name_taken_floor	393	pass	21	10.89	predicate: all_of: readable_text: 'NAME TAKEN' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 14, 'y': 315, 'w': 112, 'h': 18} | protocol_reads:
atlas-phase8.json	case.p8.zone_rename.f2_row	1440	pass	18	10.32	predicate: all_of: input_value: value is 'Inbox', wanted 'Inbox' | hit_target: control owns all 9 hit points in viewport {'width': 1440, 'height': 900} with rect {'x': 237, 'y'
atlas-phase8.json	case.p8.zone_rename.f2_row	393	pass	12	9.86	predicate: all_of: input_value: value is 'Inbox', wanted 'Inbox' | hit_target: control owns all 9 hit points in viewport {'width': 393, 'height': 852} with rect {'x': 77, 'y': 29
atlas-phase8.json	case.p8.chair.no_new_zone	1440	pass	9	9.91	predicate: 'No matching tools or Desk items.' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 73, 'w': 382, 'h': 44}	case.p8.chair.no_new_zone--1
atlas-phase8.json	case.p8.chair.no_new_zone	393	pass	9	9.32	predicate: 'No matching tools or Desk items.' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 51, 'w': 363, 'h': 44}	case.p8.chair.no_new_zone--393/2
atlas-phase8.json	case.p8.list_delete.gone	1440	pass	35	8.65	predicate: all_of: protocol_reads: GET /api/decisions/decision_05992cf07592 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 1440, 'height': 900
atlas-phase8.json	case.p8.list_delete.gone	393	pass	24	8.81	predicate: all_of: protocol_reads: GET /api/decisions/decision_efb9d5e4bfe9 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 393, 'height': 852} 
atlas-phase8.json	case.p8.list_delete.undo	1440	pass	30	8.71	predicate: all_of: protocol_reads: GET /api/decisions/decision_6362da30895b answered 200 | readable_text: 'Restored Atlas list delete' is readable in viewport {'width': 1440, 'hei
atlas-phase8.json	case.p8.list_delete.undo	393	pass	15	9.52	predicate: all_of: protocol_reads: GET /api/decisions/decision_a1c15e9ad1f7 answered 200 | readable_text: 'Restored Atlas list delete' is readable in viewport {'width': 393, 'heigh
atlas-phase8.json	case.p8.list_delete.long_list_393	1440	pass	34	8.26	predicate: all_of: protocol_reads: GET /api/decisions/decision_eca9b96f0cd8 answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 1440, 'hei
atlas-phase8.json	case.p8.list_delete.long_list_393	393	pass	24	10.04	predicate: all_of: protocol_reads: GET /api/decisions/decision_4b02954f6d6d answered 404 | readable_text: 'Removal committed' is readable in viewport {'width': 393, 'heig
atlas-phase8.json	case.p8.delete_twice.both_gone	1440	pass	43	10.28	predicate: all_of: protocol_reads: GET /api/decisions/decision_99390eccd8b8 answered 404; GET /api/decisions/decision_00bd67806e37 answered 404 | readable_text: 'Removal co
atlas-phase8.json	case.p8.delete_twice.both_gone	393	pass	29	9.26	predicate: all_of: protocol_reads: GET /api/decisions/decision_2da1b044d205 answered 404; GET /api/decisions/decision_3f1438b3f848 answered 404 | readable_text: 'Removal comm
atlas-phase8.json	case.p8.delete_then_leave.gone	1440	pass	27	9.78	predicate: all_of: protocol_status: DELETE /api/decisions/decision_06f8b54b29af answered 200, wanted 200 (body sha256 9022e3bb277d) | protocol_reads: GET /api/decisions/deci
atlas-phase8.json	case.p8.delete_then_leave.gone	393	pass	18	8.70	predicate: all_of: protocol_status: DELETE /api/decisions/decision_9c7f3f8944a6 answered 200, wanted 200 (body sha256 d61e15198bf0) | protocol_reads: GET /api/decisions/decis
atlas-phase8.json	case.p8.chair.delete_withheld	1440	pass	22	8.01	predicate: all_of: readable_text: 'Open the Floor or the list' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1031, 'y': 96, 'w': 382, 'h': 26} | attr
atlas-phase8.json	case.p8.chair.delete_withheld	393	pass	16	7.32	predicate: all_of: readable_text: 'Open the Floor or the list' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 74, 'w': 363, 'h': 26} | attr_equ
atlas-phase8.json	case.p8.decision_heads.hidden	1440	pass	10	6.51	predicate: all_of: readable_text: 'DECISION CONTEXT' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1037, 'y': 117, 'w': 370, 'h': 94} | text_absent: 
atlas-phase8.json	case.p8.decision_heads.hidden	393	pass	10	6.04	predicate: all_of: readable_text: 'DECISION CONTEXT' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 439, 'w': 363, 'h': 122} | text_absent: 'CO
atlas-phase8.json	case.p8.zone_create.second_unnamed.op	op	pass	3	5.72	predicate: all 3 facts hold: observe_at <root> holds; observe_at <root> holds; the trigger operation_id is absent	case.p8.zone_create.second_unnamed.op--op/20260928T1906
atlas-phase8.json	case.p8.zone_rename.list.op	op	pass	3	5.72	predicate: all 3 facts hold: observe_at directory.id holds; observe_at directory.name holds; the trigger operation_id is absent	case.p8.zone_rename.list.op--op/20260928T190635Z-ca
atlas-phase8.json	case.p8.zone_rename.name_taken_list.op	op	pass	3	5.42	predicate: all 3 facts hold: the trigger error holds; the trigger existing_name holds; observe_at directory.name holds	case.p8.zone_rename.name_taken_list.op--op/202609
atlas-phase8.json	case.p8.list_delete.gone.op	op	pass	3	5.42	predicate: all 7 facts hold: observe_at <root> holds; op read #0 (decision.read) error holds; op read #1 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #1 (ke
atlas-phase8.json	case.p8.delete_twice.both_gone.op	op	pass	3	5.06	predicate: all 10 facts hold: observe_at <root> holds; observe_at <root> holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.rec
TOTAL 69 runs: 69 pass, 0 not pass
retained: 69 rows, 69 run directories, 69 observations
```

### Captured run — 2026-09-28T19:07:33Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/fences.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 87a8009459a9a0bf46c89018b7cc49378b1f0ee7

```text
HEAD = b2fd7e8ba9f9f90470e973fc36fe07d056825d85
=========================== short test summary info ============================
FAILED tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
1 failed, 432 passed in 49.16s
baseline (unmutated): 46 passed in 0.40s
m1 (24): RED - 7 failed, 39 passed in 0.47s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_every_case_reference_inside_the_atlas_resolves-atlas-phase9.json]', 'FAILED te
m2 (28): RED - 2 failed, 44 passed in 0.47s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_face_cases_carry_both_ruled_viewports-atlas-phase9.json]', 'FAILED tests/unit/
m3 (32): RED - 1 failed, 45 passed in 0.46s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_admitted_write_twin_reads_its_receipt_with_its_actor']
m4 (37): RED - 1 failed, 45 passed in 0.43s; ['FAILED tests/unit/test_philo9_atlas.py::test_no_trigger_is_optional_and_no_optional_step_is_the_outcome']
m5 (41): RED - 1 failed, 45 passed in 0.47s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_face_case_without_a_twin_is_excluded_with_a_reason']
m6 (45): RED - 1 failed, 45 passed in 0.49s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values']
m7 (51): RED - 1 failed, 45 passed in 0.49s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_every_desk_face_case_crosses_the_gate_first-atlas-phase9.json]']
m8 (55): RED - 2 failed, 44 passed in 0.46s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_api_step_exists_in_the_generated_openapi[atlas-phase9.json]', 'FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read
m9 (59): RED - 2 failed, 44 passed in 0.47s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values', 'FAILED tests/unit/test_philo9_atlas.py::test_the_delivery_face_reads_its_own_clicks_durable_ou
m10 (64): RED - 1 failed, 45 passed in 0.48s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values']
10 red, 0 missed
```

### Captured run — 2026-09-28T19:07:24Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/red_main.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 87a8009459a9a0bf46c89018b7cc49378b1f0ee7

```text
base = 1f332bc3c85a8fdfd1a0c0ba9e5a113d61d17777
✓ built in 4.37s
case.p9.update.delivered_row 1440 exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: ui step click on "[data-update-id='pupd_75643bae2453411ab09d303f962f5b1f']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
case.p9.update.delivered_row 393 exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: ui step click on "[data-update-id='pupd_62c43d757e9d49d5b1e5465374b9981d']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
case.p9.grant.project_allowed 1440 exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: ui step click on "button[aria-label='Projects: sweep-runner']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
case.p9.grant.project_allowed 393 exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: ui step click on "button[aria-label='Projects: sweep-runner']" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
case.p9.grant_route.project_allowed op exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: capture_as 'grant_op': no value at 'operation_id' in the response of PUT /api/settings/remote/delegations/sweep-runner/projects/proj-e44b90107bcc
case.p9.grant.desk_reads_desk 1440 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part protocol_reads: GET /api/settings/remote: 0 row(s) at 'credentials' match {'identity': 'desk-agent', 'palette': 'DESK'}; exactly one is required
case.p9.grant.desk_reads_desk 393 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part protocol_reads: GET /api/settings/remote: 0 row(s) at 'credentials' match {'identity': 'desk-agent', 'palette': 'DESK'}; exactly one is required
case.p9.connections.never_checked_face 1440 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part readable_text: 'NEVER CHECKED' NOT in observe_at text
case.p9.connections.never_checked_face 393 exit=1 VERDICT: fail terminal=settled | NOTE: predicate: all_of part readable_text: 'NEVER CHECKED' NOT in observe_at text
case.p9.update.delivered_row.op op exit=1 VERDICT: blocked terminal=None | NOTE: BLOCKED: capture_as 'mark_op': no value at 'operation_id' in the decoded response of operation 'project.mark_update_delivered'
```

### Captured run — 2026-09-28T19:11:10Z

- **Command:** `env OBS_ONLY=1 ROOT=.tmp/main-294632c0 zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh base-294632c0 3 docs/internal/philo/graph/atlas.json docs/internal/philo/graph/atlas-phase3.json`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 87a8009459a9a0bf46c89018b7cc49378b1f0ee7

```text
HEAD = b2fd7e8ba9f9f90470e973fc36fe07d056825d85; load { 3.16 5.03 5.71 }
product: the export at .tmp/main-294632c0
✓ built in 4.31s
Traceback (most recent call last):
  File "/Users/karol/dev/tools/wt-philo-9-05/pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_run.py", line 110, in <module>
    sys.exit(main())
             ~~~~^^
  File "/Users/karol/dev/tools/wt-philo-9-05/pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_run.py", line 91, in main
    runs = plan(args.files, set(args.case))
  File "/Users/karol/dev/tools/wt-philo-9-05/pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_run.py", line 36, in plan
    atlas = json.loads((ROOT / f).read_text())
                       ~~~~~~~~~~~~~~~~~~~~^^
  File "/Users/karol/.local/share/uv/python/cpython-3.13.14-macos-aarch64-none/lib/python3.13/pathlib/_local.py", line 546, in read_text
    return PathBase.read_text(self, encoding, errors, newline)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/.local/share/uv/python/cpython-3.13.14-macos-aarch64-none/lib/python3.13/pathlib/_abc.py", line 632, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors, newline=newline) as f:
         ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/.local/share/uv/python/cpython-3.13.14-macos-aarch64-none/lib/python3.13/pathlib/_local.py", line 537, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/Users/karol/dev/tools/wt-philo-9-05/--root .tmp/main-294632c0'
cp: .tmp/s05/base-294632c0/runs.tsv: No such file or directory
tail: .tmp/s05/base-294632c0/runs.tsv: No such file or directory
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh:27: no such file or directory: pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-shots/base-294632c0/runs.tsv
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh:28: no matches found: pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-shots/base-294632c0/*/*/
pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh:29: no matches found: pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-shots/base-294632c0/*/*/observation.json
retained: -1 rows, 0 run directories, 0 observations
RETENTION MISMATCH
```

### Captured run — 2026-09-28T19:11:15Z

- **Command:** `env OBS_ONLY=1 zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh base-merged 3 docs/internal/philo/graph/atlas.json docs/internal/philo/graph/atlas-phase3.json`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 87a8009459a9a0bf46c89018b7cc49378b1f0ee7

```text
HEAD = b2fd7e8ba9f9f90470e973fc36fe07d056825d85; load { 2.99 4.97 5.69 }
✓ built in 4.34s
194 runs, 3 at a time; out /Users/karol/dev/tools/wt-philo-9-05/.tmp/s05/base-merged
atlas.json	case.j1.first_words_continue_later.idle	1440	pass	10	3.07	predicate: data-testid='arrival-headline', wanted 'arrival-headline'	case.j1.first_words_continue_later.idle--1440/20260928T191120Z-case.j1.first_words_continue_later.idle
atlas.json	case.j1.first_words_continue_later.idle	393	pass	10	3.07	predicate: data-testid='arrival-headline', wanted 'arrival-headline'	case.j1.first_words_continue_later.idle--393/20260928T191120Z-case.j1.first_words_continue_later.idle-m
atlas.json	case.j1.first_words_continue_later.draft_custody	1440	fail	35	3.07	predicate: 'Save draft & continue' NOT in observe_at text	case.j1.first_words_continue_later.draft_custody--1440/20260928T191120Z-case.j1.first_words_continue_lat
atlas.json	case.j1.first_words_continue_later.draft_custody	393	fail	34	3.58	predicate: 'Save draft & continue' NOT in observe_at text	case.j1.first_words_continue_later.draft_custody--393/20260928T191129Z-case.j1.first_words_continue_later
atlas.json	case.j1.speech_readiness.ready	op	pass	3	3.58	predicate: /task_overrides/37/effective/status equals the declared value	case.j1.speech_readiness.ready--op/20260928T191129Z-case.j1.speech_readiness.ready-muaddib-1440
atlas.json	case.j1.first_words_speak.kept	1440	blocked	2	3.37	BLOCKED: boundary substitution 'browser_audio_device' (label "chromium --use-fake-device-for-media-stream --use-file-for-fake-audio-capture=<fixture> (boundary substitution: this
atlas.json	case.j1.first_words_speak.kept	393	blocked	2	3.37	BLOCKED: boundary substitution 'browser_audio_device' (label "chromium --use-fake-device-for-media-stream --use-file-for-fake-audio-capture=<fixture> (boundary substitution: this 
atlas.json	case.j1.first_words_keep_as_note.kept	1440	pass	7	3.34	predicate: 'Kept as a note.' in observe_at text	case.j1.first_words_keep_as_note.kept--1440/20260928T191137Z-case.j1.first_words_keep_as_note.kept-muaddib-1440
atlas.json	case.j1.first_words_keep_as_note.kept	393	pass	7	3.47	predicate: 'Kept as a note.' in observe_at text	case.j1.first_words_keep_as_note.kept--393/20260928T191144Z-case.j1.first_words_keep_as_note.kept-muaddib-393
atlas.json	case.j1.first_words_speak.permission_denied	1440	blocked	2	3.51	BLOCKED: boundary substitution 'browser_permission' (label 'playwright browser context with permissions=[] so getUserMedia raises NotAllowedError (the refusal is min
atlas.json	case.j1.first_words_speak.permission_denied	393	blocked	2	3.47	BLOCKED: boundary substitution 'browser_permission' (label 'playwright browser context with permissions=[] so getUserMedia raises NotAllowedError (the refusal is mint
atlas.json	case.j1.first_words_speak.unreachable_hub	1440	blocked	2	3.47	BLOCKED: boundary substitution 'transport_failure' (label 'playwright route interception aborting the dictation request only; production parsing, rendering and persist
atlas.json	case.j1.first_words_speak.unreachable_hub	393	blocked	2	3.47	BLOCKED: boundary substitution 'transport_failure' (label 'playwright route interception aborting the dictation request only; production parsing, rendering and persiste
atlas.json	case.j1.first_words_speak.mic_unsupported	1440	blocked	2	3.52	BLOCKED: boundary substitution 'browser_capability' (label 'an init script deleting mediaDevices before the page loads (browser-owned capability, substituted at the br
atlas.json	case.j1.first_words_speak.mic_unsupported	393	blocked	2	3.52	BLOCKED: boundary substitution 'browser_capability' (label 'an init script deleting mediaDevices before the page loads (browser-owned capability, substituted at the bro
atlas.json	case.j2.arrival_load.engines_both_missing	1440	fail	31	3.52	predicate: 'No engine yet' NOT in observe_at text	case.j2.arrival_load.engines_both_missing--1440/20260928T191159Z-case.j2.arrival_load.engines_both_missing-muaddib-1440
atlas.json	case.j2.arrival_load.engines_both_missing	393	fail	31	3.52	predicate: 'No engine yet' NOT in observe_at text	case.j2.arrival_load.engines_both_missing--393/20260928T191200Z-case.j2.arrival_load.engines_both_missing-muaddib-393
atlas.json	case.j2.arrival_load.summary_missing_only	1440	blocked	6	3.47	BLOCKED: POST /api/inference/assignments/set answered 400: {"code":"inference_assignment_invalid","message":"Assignment request has an invalid shape"}	case.j2.arrival_
atlas.json	case.j2.arrival_load.summary_missing_only	393	blocked	5	3.84	BLOCKED: POST /api/inference/assignments/set answered 400: {"code":"inference_assignment_invalid","message":"Assignment request has an invalid shape"}	case.j2.arrival_l
atlas.json	case.j2.arrival_load.read_unknown	1440	blocked	5	3.69	BLOCKED: boundary substitution 'route_failure' (label 'playwright route interception failing that one read; every other read stays real') is not implemented; a label alone sub
atlas.json	case.j2.arrival_load.read_unknown	393	blocked	5	3.63	BLOCKED: boundary substitution 'route_failure' (label 'playwright route interception failing that one read; every other read stays real') is not implemented; a label alone subs
atlas.json	case.j2.arrival_load.read_pending	1440	blocked	5	3.50	BLOCKED: boundary substitution 'route_failure' (label 'playwright route interception holding that one response open for the observation window') is not implemented; a label al
atlas.json	case.j2.arrival_load.read_pending	393	blocked	6	3.30	BLOCKED: boundary substitution 'route_failure' (label 'playwright route interception holding that one response open for the observation window') is not implemented; a label alo
atlas.json	case.j3.concierge_add_engine.add_ready	1440	blocked	16	3.30	BLOCKED: ui step click on '[data-testid=concierge-add-engine]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_add_engine.add_ready--144
atlas.json	case.j3.concierge_add_engine.add_ready	393	blocked	16	3.30	BLOCKED: ui step click on '[data-testid=concierge-add-engine]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_add_engine.add_ready--393/
atlas.json	case.j3.concierge_add_check.refused	1440	blocked	16	3.28	BLOCKED: ui step click on '[data-testid=concierge-add-engine]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_add_check.refused--1440/2026
atlas.json	case.j3.concierge_add_check.refused	393	blocked	16	3.67	BLOCKED: ui step click on '[data-testid=concierge-add-engine]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_add_check.refused--393/202609
atlas.json	case.j3.concierge_check.engine_unreachable	1440	blocked	19	3.67	BLOCKED: ui step click on '[data-testid^=concierge-check-]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_check.engine_unreachable
atlas.json	case.j3.concierge_check.engine_unreachable	393	blocked	18	3.78	BLOCKED: ui step click on '[data-testid^=concierge-check-]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_check.engine_unreachable-
atlas.json	case.j3.concierge_use_for_summaries.assigned_ready	1440	blocked	22	3.57	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: o
atlas.json	case.j3.concierge_use_for_summaries.assigned_ready	393	blocked	22	3.44	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: ob
atlas.json	case.j3.speech_missing.row_stays	1440	blocked	17	3.33	BLOCKED: POST /api/inference/assignments/clear answered 400: {"code":"inference_assignment_invalid","message":"Clear request has an invalid shape"}	case.j3.speech_missing.row_
atlas.json	case.j3.speech_missing.row_stays	393	blocked	17	2.94	BLOCKED: POST /api/inference/assignments/clear answered 400: {"code":"inference_assignment_invalid","message":"Clear request has an invalid shape"}	case.j3.speech_missing.row_s
atlas.json	case.j3.route_assignments_set.assigned_ready	op	fail	34	2.94	predicate: rows matching {'id': 'meeting.deferred_analysis', 'has_override': True} at /api/inference/assignments: before=0 after=0 (new=0; wanted >= 1)	case.j3.route_as
atlas.json	case.j3.profile_delete.profile_missing	1440	blocked	22	3.27	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: observe_at no
atlas.json	case.j3.profile_delete.profile_missing	393	blocked	22	3.45	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: observe_at not
atlas.json	case.j3.profile_unbind.binding_absent	op	blocked	2	3.62	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j3.profile_unbind.binding_absent--op/20260928T191349Z-case.j3.profile_unbind.binding_absent-muaddib-1440
atlas.json	case.j4.record_start.capture_recording	1440	blocked	5	3.62	BLOCKED: boundary substitution 'browser_audio_device' (label 'Synthetic architect meeting at a browser audio boundary. This rig has no microphone recorder; block without 
atlas.json	case.j4.record_start.capture_recording	393	blocked	6	3.81	BLOCKED: boundary substitution 'browser_audio_device' (label 'Synthetic architect meeting at a browser audio boundary. This rig has no microphone recorder; block without s
atlas.json	case.j4.meeting_stop.capture_finalized	op	blocked	7	3.75	BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/meeting_active', 'value': True} at 'protocol: GET /api/runtime/status' — /meeting_active = False, wanted
atlas.json	case.j4.meetings_import.imported	op	pass	12	4.01	predicate: /meetings/0/id equals the declared value	case.j4.meetings_import.imported--op/20260928T191402Z-case.j4.meetings_import.imported-muaddib-1440
atlas.json	case.j4.meeting_stop.transcription_absent	1440	blocked	13	4.01	BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/meeting_active', 'value': True} at 'protocol: GET /api/runtime/status' — /meeting_active = False, 
atlas.json	case.j4.meeting_stop.transcription_absent	393	blocked	13	4.17	BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/meeting_active', 'value': True} at 'protocol: GET /api/runtime/status' — /meeting_active = False, w
atlas.json	case.j5.meeting_open.route_disclosed	1440	pass	25	4.39	predicate: '192.168.1.43 · LAN' in observe_at text	case.j5.meeting_open.route_disclosed--1440/20260928T191414Z-case.j5.meeting_open.route_disclosed-muaddib-1440
atlas.json	case.j5.meeting_open.route_disclosed	393	pass	28	4.39	predicate: '192.168.1.43 · LAN' in observe_at text	case.j5.meeting_open.route_disclosed--393/20260928T191416Z-case.j5.meeting_open.route_disclosed-muaddib-393
atlas.json	case.j5.meeting_open.no_engine_no_verb	1440	pass	23	4.28	predicate: 'Run summary' absent at observe_at	case.j5.meeting_open.no_engine_no_verb--1440/20260928T191420Z-case.j5.meeting_open.no_engine_no_verb-muaddib-1440
atlas.json	case.j5.meeting_open.no_engine_no_verb	393	pass	18	3.46	predicate: 'Run summary' absent at observe_at	case.j5.meeting_open.no_engine_no_verb--393/20260928T191439Z-case.j5.meeting_open.no_engine_no_verb-muaddib-393
atlas.json	case.j6.run_summary.intel_queued	1440	pass	22	3.50	predicate: POST /api/meetings/c8f463b9/intelligence/run answered 200, wanted 200 (body sha256 2b21d1efa8db); response body contains the declared admission facts	case.j6.run_summa
atlas.json	case.j6.run_summary.intel_queued	393	pass	23	3.50	predicate: POST /api/meetings/aacb045a/intelligence/run answered 200, wanted 200 (body sha256 2bfd53051ddb); response body contains the declared admission facts	case.j6.run_summar
atlas.json	case.j6.run_summary.intel_running	op	blocked	2	3.71	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j6.run_summary.intel_running--op/20260928T191457Z-case.j6.run_summary.intel_running-muaddib-1440
atlas.json	case.j6.run_summary.intel_ready	op	blocked	2	3.65	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j6.run_summary.intel_ready--op/20260928T191459Z-case.j6.run_summary.intel_ready-muaddib-1440
atlas.json	case.j6.run_summary.intel_failed	1440	blocked	0	3.65	NOTE: the case declares a provider replay at 'tests/fixtures/philo3_summary_failure_reply.json', but this run was requested with --engine 'none'; replay is installed only for a
atlas.json	case.j6.run_summary.intel_failed	393	blocked	0	3.65	NOTE: the case declares a provider replay at 'tests/fixtures/philo3_summary_failure_reply.json', but this run was requested with --engine 'none'; replay is installed only for an
atlas.json	case.j6.run_summary.intel_retry	op	blocked	0	3.65	NOTE: the case declares a provider replay at 'tests/fixtures/philo3_summary_failure_reply.json', but this run was requested with --engine 'none'; replay is installed only for an e
atlas.json	case.j6.route_intelligence_run.refusal	op	blocked	2	3.65	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j6.route_intelligence_run.refusal--op/20260928T191501Z-case.j6.route_intelligence_run.refusal-muaddib-1
atlas.json	case.j7.hub_restart.intel_retained	op	blocked	2	3.92	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j7.hub_restart.intel_retained--op/20260928T191503Z-case.j7.hub_restart.intel_retained-muaddib-1440
atlas.json	case.j7.arrival_load.reload_persisted	1440	pass	29	3.92	predicate: observe_at text is 'The Synthetic Architect Meeting concluded with three decisions: Mayyachan to write the Migration Plan by Friday, Leo Martinez to test restart 
atlas.json	case.j7.arrival_load.reload_persisted	393	pass	33	3.92	predicate: observe_at text is 'The meeting established three decisions: using SQ for the local ledger, keeping summary retrieval on the local desk after hub restarts, and usi
atlas.json	case.j8.hotkey_option_r.other_app_delivery	op	not_applicable	0	3.93	NOTE: NOT APPLICABLE: UNEXERCISED by the rig: the trigger is a native global hotkey and the result is delivery into another application. Missing mechanism: a nat
atlas.json	case.j9.timer_sweep.receipt_resolved	op	pass	13	3.93	predicate: rows matching {'source_kind': 'pipeline_event', 'title__prefix': 'SWEEP'} at /api/desk/projections: before=0 after=1 (new=1; wanted >= 1)	case.j9.timer_sweep.receipt
atlas.json	case.j9.route_run_now.receipt_resolved	op	pass	3	4.08	predicate: rows matching {'source_kind': 'pipeline_event', 'detail_url': '/cadence'} at /api/desk/projections: before=0 after=1 (new=1; wanted >= 1)	case.j9.route_run_now.rece
atlas.json	case.j9.shade_open.door_present	1440	pass	9	3.99	predicate: 'SWEEP' in observe_at text	case.j9.shade_open.door_present--1440/20260928T191523Z-case.j9.shade_open.door_present-muaddib-1440
atlas.json	case.j9.shade_open.door_present	393	pass	9	4.47	predicate: 'SWEEP' in observe_at text	case.j9.shade_open.door_present--393/20260928T191532Z-case.j9.shade_open.door_present-muaddib-393
atlas.json	case.j9.shade_receipt_open.rhythm_face	1440	pass	10	4.52	predicate: windows after: ['Rhythm']	case.j9.shade_receipt_open.rhythm_face--1440/20260928T191534Z-case.j9.shade_receipt_open.rhythm_face-muaddib-1440
atlas.json	case.j9.shade_receipt_open.rhythm_face	393	pass	11	4.87	predicate: windows after: ['Rhythm']	case.j9.shade_receipt_open.rhythm_face--393/20260928T191539Z-case.j9.shade_receipt_open.rhythm_face-muaddib-393
atlas.json	case.j9.shade_open.door_absent	1440	blocked	6	4.87	BLOCKED: boundary substitution 'remote_origin_call' (label "a remote-origin call into the hub's own API from the run's harness, recorded as such; the event is produced by the rea
atlas.json	case.j9.shade_open.door_absent	393	blocked	6	5.12	BLOCKED: boundary substitution 'remote_origin_call' (label "a remote-origin call into the hub's own API from the run's harness, recorded as such; the event is produced by the real
atlas.json	case.j9.shade_open.door_stale	1440	blocked	41	5.12	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: observe_at not present
atlas.json	case.j9.shade_open.door_stale	393	blocked	44	5.03	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: observe_at not present 
atlas.json	case.j9.shade_acknowledge.acknowledged	1440	blocked	6	5.03	BLOCKED: the recorded provider reply is NOT installed in the hub process. Declare `reply` on the boundary step so the hub is booted with it (the seam is a module attribut
atlas.json	case.j9.shade_acknowledge.acknowledged	393	blocked	5	5.27	BLOCKED: the recorded provider reply is NOT installed in the hub process. Declare `reply` on the boundary step so the hub is booted with it (the seam is a module attribute
atlas.json	case.j9.shade_dismiss.dismissed	1440	blocked	6	5.25	BLOCKED: the recorded provider reply is NOT installed in the hub process. Declare `reply` on the boundary step so the hub is booted with it (the seam is a module attribute insid
atlas.json	case.j9.shade_dismiss.dismissed	393	blocked	6	5.31	BLOCKED: the recorded provider reply is NOT installed in the hub process. Declare `reply` on the boundary step so the hub is booted with it (the seam is a module attribute inside
atlas.json	case.j9.route_presentation_restore.restored	op	blocked	2	5.04	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j9.route_presentation_restore.restored--op/20260928T191612Z-case.j9.route_presentation_restore.res
atlas.json	case.j10.brief_latest.absent	1440	pass	9	4.80	predicate: 'No brief yet' in observe_at text	case.j10.brief_latest.absent--1440/20260928T191613Z-case.j10.brief_latest.absent-muaddib-1440
atlas.json	case.j10.brief_latest.absent	393	pass	9	4.83	predicate: 'No brief yet' in observe_at text	case.j10.brief_latest.absent--393/20260928T191623Z-case.j10.brief_latest.absent-muaddib-393
atlas.json	case.j10.arrival_generate_brief.populated	1440	pass	11	4.68	predicate: 'Review decision: Graph walk brief material J10' in observe_at text	case.j10.arrival_generate_brief.populated--1440/20260928T191628Z-case.j10.arrival_generate
atlas.json	case.j10.arrival_generate_brief.populated	393	pass	11	4.68	predicate: 'Review decision: Graph walk brief material J10' in observe_at text	case.j10.arrival_generate_brief.populated--393/20260928T191632Z-case.j10.arrival_generate_b
atlas.json	case.j10.arrival_generate_brief.generated_empty	1440	pass	10	4.55	predicate: 'No changes' in observe_at text	case.j10.arrival_generate_brief.generated_empty--1440/20260928T191634Z-case.j10.arrival_generate_brief.generated_empty-m
atlas.json	case.j10.arrival_generate_brief.generated_empty	393	pass	10	4.58	predicate: 'No changes' in observe_at text	case.j10.arrival_generate_brief.generated_empty--393/20260928T191639Z-case.j10.arrival_generate_brief.generated_empty-mua
atlas.json	case.j10.arrival_reload.reload_persisted	1440	pass	13	4.54	predicate: 'No changes' in observe_at text	case.j10.arrival_reload.reload_persisted--1440/20260928T191642Z-case.j10.arrival_reload.reload_persisted-muaddib-1440
atlas.json	case.j10.arrival_reload.reload_persisted	393	pass	12	4.54	predicate: 'No changes' in observe_at text	case.j10.arrival_reload.reload_persisted--393/20260928T191643Z-case.j10.arrival_reload.reload_persisted-muaddib-393
atlas.json	case.j10.arrival_generate_again.same_day_idempotent	1440	pass	191	4.89	predicate: unchanged result; the returned identity 'No changes' (headline='No changes') IS the one displayed at '[data-testid=arrival-brief-headline]' (respon
atlas.json	case.j10.arrival_generate_again.same_day_idempotent	393	pass	191	5.46	predicate: unchanged result; the returned identity 'No changes' (headline='No changes') IS the one displayed at '[data-testid=arrival-brief-headline]'
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-28T19:27:08Z

- **Command:** `env OBS_ONLY=1 ROOT=.tmp/main-294632c0 zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/rig_phase.sh base-294632c0 3 docs/internal/philo/graph/atlas.json docs/internal/philo/graph/atlas-phase3.json`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 87a8009459a9a0bf46c89018b7cc49378b1f0ee7

```text
HEAD = b2fd7e8ba9f9f90470e973fc36fe07d056825d85; load { 4.25 5.00 5.14 }
product: the export at .tmp/main-294632c0
✓ built in 4.49s
194 runs, 3 at a time; out /Users/karol/dev/tools/wt-philo-9-05/.tmp/s05/base-294632c0
atlas.json	case.j1.first_words_continue_later.idle	1440	pass	10	4.47	predicate: data-testid='arrival-headline', wanted 'arrival-headline'	case.j1.first_words_continue_later.idle--1440/20260928T192713Z-case.j1.first_words_continue_later.idle
atlas.json	case.j1.first_words_continue_later.idle	393	pass	10	4.47	predicate: data-testid='arrival-headline', wanted 'arrival-headline'	case.j1.first_words_continue_later.idle--393/20260928T192713Z-case.j1.first_words_continue_later.idle-m
atlas.json	case.j1.first_words_continue_later.draft_custody	1440	fail	35	4.47	predicate: 'Save draft & continue' NOT in observe_at text	case.j1.first_words_continue_later.draft_custody--1440/20260928T192713Z-case.j1.first_words_continue_lat
atlas.json	case.j1.first_words_continue_later.draft_custody	393	fail	34	4.32	predicate: 'Save draft & continue' NOT in observe_at text	case.j1.first_words_continue_later.draft_custody--393/20260928T192722Z-case.j1.first_words_continue_later
atlas.json	case.j1.speech_readiness.ready	op	pass	3	4.32	predicate: /task_overrides/37/effective/status equals the declared value	case.j1.speech_readiness.ready--op/20260928T192722Z-case.j1.speech_readiness.ready-muaddib-1440
atlas.json	case.j1.first_words_speak.kept	1440	blocked	2	4.29	BLOCKED: boundary substitution 'browser_audio_device' (label "chromium --use-fake-device-for-media-stream --use-file-for-fake-audio-capture=<fixture> (boundary substitution: this
atlas.json	case.j1.first_words_speak.kept	393	blocked	2	4.29	BLOCKED: boundary substitution 'browser_audio_device' (label "chromium --use-fake-device-for-media-stream --use-file-for-fake-audio-capture=<fixture> (boundary substitution: this 
atlas.json	case.j1.first_words_keep_as_note.kept	1440	pass	7	4.51	predicate: 'Kept as a note.' in observe_at text	case.j1.first_words_keep_as_note.kept--1440/20260928T192730Z-case.j1.first_words_keep_as_note.kept-muaddib-1440
atlas.json	case.j1.first_words_keep_as_note.kept	393	pass	7	4.55	predicate: 'Kept as a note.' in observe_at text	case.j1.first_words_keep_as_note.kept--393/20260928T192737Z-case.j1.first_words_keep_as_note.kept-muaddib-393
atlas.json	case.j1.first_words_speak.permission_denied	1440	blocked	2	4.53	BLOCKED: boundary substitution 'browser_permission' (label 'playwright browser context with permissions=[] so getUserMedia raises NotAllowedError (the refusal is min
atlas.json	case.j1.first_words_speak.permission_denied	393	blocked	2	4.53	BLOCKED: boundary substitution 'browser_permission' (label 'playwright browser context with permissions=[] so getUserMedia raises NotAllowedError (the refusal is mint
atlas.json	case.j1.first_words_speak.unreachable_hub	1440	blocked	2	4.53	BLOCKED: boundary substitution 'transport_failure' (label 'playwright route interception aborting the dictation request only; production parsing, rendering and persist
atlas.json	case.j1.first_words_speak.unreachable_hub	393	blocked	2	4.57	BLOCKED: boundary substitution 'transport_failure' (label 'playwright route interception aborting the dictation request only; production parsing, rendering and persiste
atlas.json	case.j1.first_words_speak.mic_unsupported	1440	blocked	2	4.57	BLOCKED: boundary substitution 'browser_capability' (label 'an init script deleting mediaDevices before the page loads (browser-owned capability, substituted at the br
atlas.json	case.j1.first_words_speak.mic_unsupported	393	blocked	2	4.57	BLOCKED: boundary substitution 'browser_capability' (label 'an init script deleting mediaDevices before the page loads (browser-owned capability, substituted at the bro
atlas.json	case.j2.arrival_load.engines_both_missing	1440	fail	31	4.57	predicate: 'No engine yet' NOT in observe_at text	case.j2.arrival_load.engines_both_missing--1440/20260928T192752Z-case.j2.arrival_load.engines_both_missing-muaddib-1440
atlas.json	case.j2.arrival_load.engines_both_missing	393	fail	31	4.76	predicate: 'No engine yet' NOT in observe_at text	case.j2.arrival_load.engines_both_missing--393/20260928T192754Z-case.j2.arrival_load.engines_both_missing-muaddib-393
atlas.json	case.j2.arrival_load.summary_missing_only	1440	blocked	6	4.76	BLOCKED: POST /api/inference/assignments/set answered 400: {"code":"inference_assignment_invalid","message":"Assignment request has an invalid shape"}	case.j2.arrival_
atlas.json	case.j2.arrival_load.summary_missing_only	393	blocked	6	4.62	BLOCKED: POST /api/inference/assignments/set answered 400: {"code":"inference_assignment_invalid","message":"Assignment request has an invalid shape"}	case.j2.arrival_l
atlas.json	case.j2.arrival_load.read_unknown	1440	blocked	6	4.57	BLOCKED: boundary substitution 'route_failure' (label 'playwright route interception failing that one read; every other read stays real') is not implemented; a label alone sub
atlas.json	case.j2.arrival_load.read_unknown	393	blocked	6	4.42	BLOCKED: boundary substitution 'route_failure' (label 'playwright route interception failing that one read; every other read stays real') is not implemented; a label alone subs
atlas.json	case.j2.arrival_load.read_pending	1440	blocked	6	4.22	BLOCKED: boundary substitution 'route_failure' (label 'playwright route interception holding that one response open for the observation window') is not implemented; a label al
atlas.json	case.j2.arrival_load.read_pending	393	blocked	6	4.22	BLOCKED: boundary substitution 'route_failure' (label 'playwright route interception holding that one response open for the observation window') is not implemented; a label alo
atlas.json	case.j3.concierge_add_engine.add_ready	1440	blocked	16	4.44	BLOCKED: ui step click on '[data-testid=concierge-add-engine]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_add_engine.add_ready--144
atlas.json	case.j3.concierge_add_engine.add_ready	393	blocked	16	4.44	BLOCKED: ui step click on '[data-testid=concierge-add-engine]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_add_engine.add_ready--393/
atlas.json	case.j3.concierge_add_check.refused	1440	blocked	16	4.97	BLOCKED: ui step click on '[data-testid=concierge-add-engine]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_add_check.refused--1440/2026
atlas.json	case.j3.concierge_add_check.refused	393	blocked	16	5.13	BLOCKED: ui step click on '[data-testid=concierge-add-engine]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_add_check.refused--393/202609
atlas.json	case.j3.concierge_check.engine_unreachable	1440	blocked	19	5.13	BLOCKED: ui step click on '[data-testid^=concierge-check-]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_check.engine_unreachable
atlas.json	case.j3.concierge_check.engine_unreachable	393	blocked	18	5.04	BLOCKED: ui step click on '[data-testid^=concierge-check-]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.	case.j3.concierge_check.engine_unreachable-
atlas.json	case.j3.concierge_use_for_summaries.assigned_ready	1440	blocked	22	4.87	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: o
atlas.json	case.j3.concierge_use_for_summaries.assigned_ready	393	blocked	22	5.28	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: ob
atlas.json	case.j3.speech_missing.row_stays	1440	blocked	17	5.28	BLOCKED: POST /api/inference/assignments/clear answered 400: {"code":"inference_assignment_invalid","message":"Clear request has an invalid shape"}	case.j3.speech_missing.row_
atlas.json	case.j3.speech_missing.row_stays	393	blocked	17	5.41	BLOCKED: POST /api/inference/assignments/clear answered 400: {"code":"inference_assignment_invalid","message":"Clear request has an invalid shape"}	case.j3.speech_missing.row_s
atlas.json	case.j3.route_assignments_set.assigned_ready	op	fail	34	5.37	predicate: rows matching {'id': 'meeting.deferred_analysis', 'has_override': True} at /api/inference/assignments: before=0 after=0 (new=0; wanted >= 1)	case.j3.route_as
atlas.json	case.j3.profile_delete.profile_missing	1440	blocked	22	5.37	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: observe_at no
atlas.json	case.j3.profile_delete.profile_missing	393	blocked	22	5.23	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: observe_at not
atlas.json	case.j3.profile_unbind.binding_absent	op	blocked	2	5.18	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j3.profile_unbind.binding_absent--op/20260928T192944Z-case.j3.profile_unbind.binding_absent-muaddib-1440
atlas.json	case.j4.record_start.capture_recording	1440	blocked	6	5.18	BLOCKED: boundary substitution 'browser_audio_device' (label 'Synthetic architect meeting at a browser audio boundary. This rig has no microphone recorder; block without 
atlas.json	case.j4.record_start.capture_recording	393	blocked	6	5.01	BLOCKED: boundary substitution 'browser_audio_device' (label 'Synthetic architect meeting at a browser audio boundary. This rig has no microphone recorder; block without s
atlas.json	case.j4.meeting_stop.capture_finalized	op	blocked	7	5.41	BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/meeting_active', 'value': True} at 'protocol: GET /api/runtime/status' — /meeting_active = False, wanted
atlas.json	case.j4.meetings_import.imported	op	pass	14	5.41	predicate: /meetings/0/id equals the declared value	case.j4.meetings_import.imported--op/20260928T192957Z-case.j4.meetings_import.imported-muaddib-1440
atlas.json	case.j4.meeting_stop.transcription_absent	1440	blocked	13	5.41	BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/meeting_active', 'value': True} at 'protocol: GET /api/runtime/status' — /meeting_active = False, 
atlas.json	case.j4.meeting_stop.transcription_absent	393	blocked	13	5.69	BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/meeting_active', 'value': True} at 'protocol: GET /api/runtime/status' — /meeting_active = False, w
atlas.json	case.j5.meeting_open.route_disclosed	1440	pass	24	5.84	predicate: '192.168.1.43 · LAN' in observe_at text	case.j5.meeting_open.route_disclosed--1440/20260928T193011Z-case.j5.meeting_open.route_disclosed-muaddib-1440
atlas.json	case.j5.meeting_open.route_disclosed	393	pass	35	5.84	predicate: '192.168.1.43 · LAN' in observe_at text	case.j5.meeting_open.route_disclosed--393/20260928T193011Z-case.j5.meeting_open.route_disclosed-muaddib-393
atlas.json	case.j5.meeting_open.no_engine_no_verb	1440	pass	20	5.69	predicate: 'Run summary' absent at observe_at	case.j5.meeting_open.no_engine_no_verb--1440/20260928T193014Z-case.j5.meeting_open.no_engine_no_verb-muaddib-1440
atlas.json	case.j5.meeting_open.no_engine_no_verb	393	pass	20	5.37	predicate: 'Run summary' absent at observe_at	case.j5.meeting_open.no_engine_no_verb--393/20260928T193034Z-case.j5.meeting_open.no_engine_no_verb-muaddib-393
atlas.json	case.j6.run_summary.intel_queued	1440	pass	22	5.37	predicate: POST /api/meetings/4f2bab1e/intelligence/run answered 200, wanted 200 (body sha256 a01b2c0b03f9); response body contains the declared admission facts	case.j6.run_summa
atlas.json	case.j6.run_summary.intel_queued	393	pass	21	5.31	predicate: POST /api/meetings/d39041c6/intelligence/run answered 200, wanted 200 (body sha256 2e5f8f3f5d70); response body contains the declared admission facts	case.j6.run_summar
atlas.json	case.j6.run_summary.intel_running	op	blocked	2	5.72	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j6.run_summary.intel_running--op/20260928T193055Z-case.j6.run_summary.intel_running-muaddib-1440
atlas.json	case.j6.run_summary.intel_ready	op	blocked	2	5.72	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j6.run_summary.intel_ready--op/20260928T193056Z-case.j6.run_summary.intel_ready-muaddib-1440
atlas.json	case.j6.run_summary.intel_failed	1440	blocked	0	5.72	NOTE: the case declares a provider replay at 'tests/fixtures/philo3_summary_failure_reply.json', but this run was requested with --engine 'none'; replay is installed only for a
atlas.json	case.j6.run_summary.intel_failed	393	blocked	0	5.72	NOTE: the case declares a provider replay at 'tests/fixtures/philo3_summary_failure_reply.json', but this run was requested with --engine 'none'; replay is installed only for an
atlas.json	case.j6.run_summary.intel_retry	op	blocked	0	5.72	NOTE: the case declares a provider replay at 'tests/fixtures/philo3_summary_failure_reply.json', but this run was requested with --engine 'none'; replay is installed only for an e
atlas.json	case.j6.route_intelligence_run.refusal	op	blocked	2	5.72	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j6.route_intelligence_run.refusal--op/20260928T193057Z-case.j6.route_intelligence_run.refusal-muaddib-1
atlas.json	case.j7.hub_restart.intel_retained	op	blocked	2	5.72	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j7.hub_restart.intel_retained--op/20260928T193058Z-case.j7.hub_restart.intel_retained-muaddib-1440
atlas.json	case.j7.arrival_load.reload_persisted	1440	pass	31	5.74	predicate: observe_at text is 'The Synthetic Architect Meeting concluded with three decisions: using SQ for the local ledger (assigned to Mayyachan), keeping summary retriev
atlas.json	case.j7.arrival_load.reload_persisted	393	pass	36	5.74	predicate: observe_at text is 'The meeting covered decisions regarding the local meeting ledger, migration planning, summary retrieval testing, and isolated rig tests. Specif
atlas.json	case.j8.hotkey_option_r.other_app_delivery	op	not_applicable	0	5.68	NOTE: NOT APPLICABLE: UNEXERCISED by the rig: the trigger is a native global hotkey and the result is delivery into another application. Missing mechanism: a nat
atlas.json	case.j9.timer_sweep.receipt_resolved	op	pass	13	5.68	predicate: rows matching {'source_kind': 'pipeline_event', 'title__prefix': 'SWEEP'} at /api/desk/projections: before=0 after=1 (new=1; wanted >= 1)	case.j9.timer_sweep.receipt
atlas.json	case.j9.route_run_now.receipt_resolved	op	pass	3	5.10	predicate: rows matching {'source_kind': 'pipeline_event', 'detail_url': '/cadence'} at /api/desk/projections: before=0 after=1 (new=1; wanted >= 1)	case.j9.route_run_now.rece
atlas.json	case.j9.shade_open.door_present	1440	pass	9	5.10	predicate: 'SWEEP' in observe_at text	case.j9.shade_open.door_present--1440/20260928T193122Z-case.j9.shade_open.door_present-muaddib-1440
atlas.json	case.j9.shade_open.door_present	393	pass	9	5.01	predicate: 'SWEEP' in observe_at text	case.j9.shade_open.door_present--393/20260928T193130Z-case.j9.shade_open.door_present-muaddib-393
atlas.json	case.j9.shade_receipt_open.rhythm_face	1440	pass	10	5.01	predicate: windows after: ['Rhythm']	case.j9.shade_receipt_open.rhythm_face--1440/20260928T193132Z-case.j9.shade_receipt_open.rhythm_face-muaddib-1440
atlas.json	case.j9.shade_receipt_open.rhythm_face	393	pass	10	5.41	predicate: windows after: ['Rhythm']	case.j9.shade_receipt_open.rhythm_face--393/20260928T193136Z-case.j9.shade_receipt_open.rhythm_face-muaddib-393
atlas.json	case.j9.shade_open.door_absent	1440	blocked	6	5.70	BLOCKED: boundary substitution 'remote_origin_call' (label "a remote-origin call into the hub's own API from the run's harness, recorded as such; the event is produced by the rea
atlas.json	case.j9.shade_open.door_absent	393	blocked	6	5.70	BLOCKED: boundary substitution 'remote_origin_call' (label "a remote-origin call into the hub's own API from the run's harness, recorded as such; the event is produced by the real
atlas.json	case.j9.shade_open.door_stale	1440	blocked	43	5.88	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: observe_at not present
atlas.json	case.j9.shade_open.door_stale	393	blocked	45	5.88	BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-run-intel'} at '[data-testid=arrival-run-intel]' — BLOCKED: observe_at not present 
atlas.json	case.j9.shade_acknowledge.acknowledged	1440	blocked	6	5.88	BLOCKED: the recorded provider reply is NOT installed in the hub process. Declare `reply` on the boundary step so the hub is booted with it (the seam is a module attribut
atlas.json	case.j9.shade_acknowledge.acknowledged	393	blocked	5	5.89	BLOCKED: the recorded provider reply is NOT installed in the hub process. Declare `reply` on the boundary step so the hub is booted with it (the seam is a module attribute
atlas.json	case.j9.shade_dismiss.dismissed	1440	blocked	6	6.14	BLOCKED: the recorded provider reply is NOT installed in the hub process. Declare `reply` on the boundary step so the hub is booted with it (the seam is a module attribute insid
atlas.json	case.j9.shade_dismiss.dismissed	393	blocked	6	5.86	BLOCKED: the recorded provider reply is NOT installed in the hub process. Declare `reply` on the boundary step so the hub is booted with it (the seam is a module attribute inside
atlas.json	case.j9.route_presentation_restore.restored	op	blocked	2	5.55	BLOCKED: headless mode refuses UI/face steps: no Page is opened	case.j9.route_presentation_restore.restored--op/20260928T193210Z-case.j9.route_presentation_restore.res
atlas.json	case.j10.brief_latest.absent	1440	pass	9	5.55	predicate: 'No brief yet' in observe_at text	case.j10.brief_latest.absent--1440/20260928T193212Z-case.j10.brief_latest.absent-muaddib-1440
atlas.json	case.j10.brief_latest.absent	393	pass	9	5.30	predicate: 'No brief yet' in observe_at text	case.j10.brief_latest.absent--393/20260928T193221Z-case.j10.brief_latest.absent-muaddib-393
atlas.json	case.j10.arrival_generate_brief.populated	1440	pass	11	5.68	predicate: 'Review decision: Graph walk brief material J10' in observe_at text	case.j10.arrival_generate_brief.populated--1440/20260928T193229Z-case.j10.arrival_generate
atlas.json	case.j10.arrival_generate_brief.populated	393	pass	11	5.38	predicate: 'Review decision: Graph walk brief material J10' in observe_at text	case.j10.arrival_generate_brief.populated--393/20260928T193230Z-case.j10.arrival_generate_b
atlas.json	case.j10.arrival_generate_brief.generated_empty	1440	pass	10	5.38	predicate: 'No changes' in observe_at text	case.j10.arrival_generate_brief.generated_empty--1440/20260928T193231Z-case.j10.arrival_generate_brief.generated_empty-m
atlas.json	case.j10.arrival_generate_brief.generated_empty	393	pass	10	5.23	predicate: 'No changes' in observe_at text	case.j10.arrival_generate_brief.generated_empty--393/20260928T193239Z-case.j10.arrival_generate_brief.generated_empty-mua
atlas.json	case.j10.arrival_reload.reload_persisted	1440	pass	13	5.23	predicate: 'No changes' in observe_at text	case.j10.arrival_reload.reload_persisted--1440/20260928T193240Z-case.j10.arrival_reload.reload_persisted-muaddib-1440
atlas.json	case.j10.arrival_reload.reload_persisted	393	pass	12	5.23	predicate: 'No changes' in observe_at text	case.j10.arrival_reload.reload_persisted--393/20260928T193241Z-case.j10.arrival_reload.reload_persisted-muaddib-393
atlas.json	case.j10.arrival_generate_again.same_day_idempotent	1440	pass	191	6.71	predicate: unchanged result; the returned identity 'No changes' (headline='No changes') IS the one displayed at '[data-testid=arrival-brief-headline]' (respon
atlas.json	case.j10.arrival_generate_again.same_day_idempotent	393	pass	191	6.71	predicate: unchanged result; the returned identity 'No changes' (headline='No changes') IS the one display
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-28T19:44:18Z

- **Command:** `python3 pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/base_diff.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0ccc23125892c3abfe8cb316c797cadfc4dee12b

```text
  77  before blocked         after blocked
   1  before blocked         after pass
   6  before fail            after fail
   1  before not_applicable  after not_applicable
 109  before pass            after pass
DIFF atlas-phase3.json case.closure.chain.s5_next_day_brief_more_opened 393: blocked -> pass
     before: BLOCKED: ui step wait_for on '[data-testid=arrival-brief-more]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
     after:  predicate: 'Keep summary retrieval on the local desk' in observe_at text
194 runs; 0 pass before and not after
```

### Captured run — 2026-09-28T19:44:19Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/fences.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0ccc23125892c3abfe8cb316c797cadfc4dee12b

```text
HEAD = b2fd7e8ba9f9f90470e973fc36fe07d056825d85
........................................................................ [ 99%]
...                                                                      [100%]
435 passed in 46.77s
baseline (unmutated): 48 passed in 0.50s
m1 (24): RED - 7 failed, 41 passed in 0.57s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_every_case_reference_inside_the_atlas_resolves-atlas-phase9.json]', 'FAILED te
m2 (28): RED - 2 failed, 46 passed in 0.52s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_face_cases_carry_both_ruled_viewports-atlas-phase9.json]', 'FAILED tests/unit/
m3 (32): RED - 1 failed, 47 passed in 0.50s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_admitted_write_twin_reads_its_receipt_with_its_actor']
m4 (37): RED - 1 failed, 47 passed in 0.50s; ['FAILED tests/unit/test_philo9_atlas.py::test_no_trigger_is_optional_and_no_optional_step_is_the_outcome']
m5 (41): RED - 1 failed, 47 passed in 0.50s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_face_case_without_a_twin_is_excluded_with_a_reason']
m6 (45): RED - 1 failed, 47 passed in 0.50s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values']
m7 (51): RED - 1 failed, 47 passed in 0.52s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_every_desk_face_case_crosses_the_gate_first-atlas-phase9.json]']
m8 (55): RED - 2 failed, 46 passed in 0.53s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_api_step_exists_in_the_generated_openapi[atlas-phase9.json]', 'FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read
m9 (59): RED - 2 failed, 46 passed in 0.50s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values', 'FAILED tests/unit/test_philo9_atlas.py::test_the_delivery_face_reads_its_own_clicks_durable_ou
m10 (64): RED - 1 failed, 47 passed in 0.50s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values']
10 red, 0 missed
```

### Captured run — 2026-09-28T19:45:21Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4d177d34ba6d6f5d29945df26b64081e6023d073

```text
.........
----------------------------------------------------------------------
Ran 9 tests in 0.003s

OK
rc=0  python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
rc=0  python3 scripts/check_docs.py
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
rc=0  python3 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/initial-findings.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/source-checklist.md docs/internal/philo/SRS.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Repository census: 5 outputs verified.
rc=0  python3 scripts/philo_repository_census.py --check
API reference checked
rc=0  python3 scripts/philo_api_reference.py --check
Boundary candidate census checked
rc=0  python3 scripts/philo_boundary_census.py --check
Doctor reference: 41 check functions
rc=0  python3 scripts/philo_doctor_reference.py --check
Configuration declaration reference is current
rc=0  python3 scripts/philo_config_reference.py --check
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
rc=0  python3 scripts/philo_graph_reference.py --check
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
rc=0  python3 scripts/validate_architecture.py
Architecture documentation checked (10 outputs).
rc=0  python3 scripts/generate_capability_docs.py --check
Documentation coverage checked.
rc=0  python3 scripts/check_doc_coverage.py --check
OpenAPI: 572 paths
rc=0  .venv/bin/python scripts/philo_openapi_reference.py --check
checks failed: 0
```

### Captured run — 2026-09-28T19:55:03Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/exit_combos.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3e160baa6e77b60cf88f525c07683bf55560f92d

```text
before fences=0 mutations=0 -> exit 0 (wanted 0): ok
before fences=0 mutations=1 -> exit 0 (wanted nonzero): WRONG
before fences=1 mutations=0 -> exit 1 (wanted nonzero): ok
before fences=1 mutations=1 -> exit 1 (wanted nonzero): ok
after fences=0 mutations=0 -> exit 0 (wanted 0): ok
after fences=0 mutations=1 -> exit 1 (wanted nonzero): ok
after fences=1 mutations=0 -> exit 1 (wanted nonzero): ok
after fences=1 mutations=1 -> exit 1 (wanted nonzero): ok
after: 0 wrong
```

### Captured run — 2026-09-28T19:55:10Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/fences.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e1d27dee931f8d3a0e0b8a1832024b9bf52a8397

```text
HEAD = 67ce9256daebd9180b5f0c4594ec86215f5b920d
........................................................................ [ 99%]
...                                                                      [100%]
435 passed in 44.70s
baseline (unmutated): 48 passed in 0.47s
m1 (24): RED - 7 failed, 41 passed in 0.56s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_every_case_reference_inside_the_atlas_resolves-atlas-phase9.json]', 'FAILED te
m2 (28): RED - 2 failed, 46 passed in 0.52s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_face_cases_carry_both_ruled_viewports-atlas-phase9.json]', 'FAILED tests/unit/
m3 (32): RED - 1 failed, 47 passed in 0.51s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_admitted_write_twin_reads_its_receipt_with_its_actor']
m4 (37): RED - 1 failed, 47 passed in 0.50s; ['FAILED tests/unit/test_philo9_atlas.py::test_no_trigger_is_optional_and_no_optional_step_is_the_outcome']
m5 (41): RED - 1 failed, 47 passed in 0.52s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_face_case_without_a_twin_is_excluded_with_a_reason']
m6 (45): RED - 1 failed, 47 passed in 0.55s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values']
m7 (51): RED - 1 failed, 47 passed in 0.53s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_general_fences_hold_for_each_phase9_file[test_every_desk_face_case_crosses_the_gate_first-atlas-phase9.json]']
m8 (55): RED - 2 failed, 46 passed in 0.53s; ['FAILED tests/unit/test_philo9_atlas.py::test_every_api_step_exists_in_the_generated_openapi[atlas-phase9.json]', 'FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read
m9 (59): RED - 2 failed, 46 passed in 0.51s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values', 'FAILED tests/unit/test_philo9_atlas.py::test_the_delivery_face_reads_its_own_clicks_durable_ou
m10 (64): RED - 1 failed, 47 passed in 0.51s; ['FAILED tests/unit/test_philo9_atlas.py::test_the_pairs_read_the_same_values']
10 red, 0 missed
```

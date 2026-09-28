# Evidence - PHILO-9-02

- **Story:** PHILO-9-02 - The steward and the connectors under Article XI
- **Status:** done
- **Date:** 2026-09-28
- **Branch:** `feat/philo-9-02-steward-connectors` from main `d05e0eb5`.
- **Red on main:** an export of main `d05e0eb5` (`git archive` into `.tmp/main-copy`; the fence files copied in; `assets/story-02-proof/run_main.sh.txt`). A missing symbol, an unknown tool or a 404 for a new route is never counted as a red; new capability has no red.

## What was built

- **The Room's kernel path** (`holdspeak/services/project_kernel.py`, `holdspeak/kernel/project.py`, `holdspeak/kernel/project_codec.py`): one `OperationSpec` per admitted Room operation. An OWNER call is the owner's gesture (approved inline); an AGENT call is refused `project_delegation_required` at admission WITH a receipt, at the one check point story 07's grant plugs into (`kernel/project.py` `grant_code`); a SCHEDULER only inside the hub's steward service. A call with `command_id` is keyed from it, so a retry reaches the same kernel operation (same payload: the original answer and receipt; changed payload: `idempotency_conflict`); a replay whose operation was abandoned (its terminal transaction rolled back) is taken over and closed once. A service method can end its operation itself WITH its domain write in one transaction (`KernelHandle.terminal(effect=...)`), or detach it for asynchronous work. The desk's atomic broker closures now also scope the Room's operations (`desk_broker.is_desk`).
- **Admission enforced** (story 01's rows, `Admission.enforced` now true) and **24 new descriptor rows** (`holdspeak/room_operations.py`): the 20 MCP identities (steward 5, nudges 3, watches 7, suggested sources 3, connections 2), the HTTP-only Door count, watch update and watch baseline, and `project.mark_update_delivered` (MCP and `POST /api/updates/{id}/delivered`). Each bound at hub composition to the hub's `ProjectStewardService`, `WatchService`, `SuggestedSourceService` (now composed by the hub), `ConnectionsService`, `ProjectDoorService` or `ProjectUpdateService`; the MCP family and `mcp/tools.py` reach them through the one registry, the HTTP routes likewise.
- **The steward on the contract** (`holdspeak/services/steward_contract.py`, the RATIFIED beat): the pending handle (`{run_id, operation_id, state, receipt: null}`; `steward_runs.operation_id` + `authority_json`, additive); one terminal receipt per run in the same transaction as the run row, with the stop re-read under it; stop its own admitted operation (the flag and its receipt in one transaction; bound to the stored run's requester for an agent: `steward_run_owner_required`); each executed policy slot a `project.steward.effect` child and each accepted proposal a `project.decide_proposal` child (the run's actor, `project-steward:<run>:<authority_sha256>`, the claim re-checks the stop and the policy digest; `kernel.receipt` carries `authority_details` from the frozen snapshot); the policy write records its owner operation (`steward_policies.configure_operation_id`, also stamped by archive); a run acts under its FROZEN policy; the conductor runs as SCHEDULER under the recorded policy (`steward_policy_required` without one); the trigger is admitted, returns its handle, its runs are its children and its receipt carries the outcomes; startup recovery on the hub's composed service ends every non-terminal Room operation, children first, with the run row interrupted in the same transaction.
- **F9:** the three nudge tools on the hub's steward service; no `unittest.mock` in product code.
- **F20:** COMPARE and proposal creation read `review_id`.
- **F5, F16, F17:** `{ref:path}` routes; `SuggestedSourceService.add` → `ProjectService.add_source_watch`: the resource (`integration:<provider>:<ref>`, relationship `source`), the armed watch (the rows `create_from_setup` writes, carved into `_arm_source_watch_in_txn`) and the accepted suggestion in ONE transaction, or a named refusal (`jira_connection_required`) with the suggestion pending.
- **B1** (the sub-lane): `connection.list` a cached read (per-row `last_checked_at` and `checked_age_seconds`, `never_checked`); Calendar and Models live; Confluence Recheck a real probe; the Connections face words in the existing chips. Also: the GitHub login stored with the probe (`external_connection_ref`) so the cached card still names the account; the hub's and the MCP composition's `ConnectionsService` now get the Confluence adapter.
- **B2** (`holdspeak/principals.py` `room_agent_submit`): the exact method and route patterns of the admitted and conditional Room operations get `AGENT_SUBMIT` at the edge; the conditional routes' adapters re-apply OWNER to the exempt form (`web/routes/_room_kernel.py`); an admitted route reads its own body, so a malformed one is `invalid_arguments` WITH a receipt, never FastAPI's 422.
- **Law 9, the same-key race as a class:** `journal_atomic.create_operation` (moved out of `journal.py`) takes `BEGIN IMMEDIATE` before the replay lookup; `ProjectService._command_txn` takes it before writing and looks again (`_CommandRaced` → the replay path) in all twelve command methods; `Broker.submit` no longer re-runs admission for a replayed still-admitting operation.
- **The link's `watch.create`** is written as the link operation's child.
- Generated: `docs/generated/operations.json` (92 operations), `api-reference.json`, `boundary-candidates.json`, `docs/MCP_SIDECAR.md` (237 tools), `tests/fixtures/db_schema_canonical.txt`, `residual-set.json`; the rig's `op` map; two atlas line anchors (`atlas.json`, `composition.py:548` → `:577`).

## Measurements

- **Residual identities 263 → 240** (MCP 205 → 185; HTTP 58 → 55; constructions 59 → 56): exactly the 20 MCP and 3 HTTP identities, paid under `PHILO-9-02` (fence `test_the_residual_set_paid_exactly_the_story_02_identities`).
- **Public MCP tools 236 → 237** (`project.mark_update_delivered`).

## Named behaviour changes (compatibility)

- An admitted call's answer (and a refusal of one) now also carries `operation_id` and `receipt`.
- The steward start answers `{success, run_id, operation_id, state, receipt}`; the trigger answers its pending handle `{success, operation_id, state, receipt}` instead of `evaluate_outcomes`/`run_outcomes` (they are in its terminal receipt's outcome, `{"evaluated", "deferred", "runs"}`).
- The steward policy write over MCP now applies the HTTP route's ranges (max_retries ≤ 100 and so on); its event's producer is `ProjectStewardService` for both transports.
- A GitHub/Jira/Confluence row that was never checked reads `never_checked` (the Door reads it as not connected: its existing "NOT SET UP" chip) until a Recheck stores a check.
- A PUT of a policy for an unknown project answers 404 (was a 500 on the foreign key).

## Stated plainly (unpaid, not built, or not verified)

- A model draft's `inference.invoke` is NOT yet a child of the `draft_update` effect (no model runs on an isolated HOME); a child's execution deadline is not clamped to its run's; the engine's `run_once` seam stays non-admitted (every product path is admitted). BACKLOG rows added.
- `nudge.send` was fenced on its refusal path only (`nudge_not_found`, with its receipt); a real `gh pr comment` send was not run.
- No issued palette excludes the Room's tools, so the MCP palette refusal of an admitted Room tool is unreachable today (BACKLOG).
- L4 has no red on main (its injection seam is new); it is proven by mutations M14/M15. Delivery (D1/D2) is new capability: no red claimed.
- `GET /api/providers/github/connection` still probes on read (`provider.*` deferred; BACKLOG).
- Inherited reds, identical on main: the five Phase 143 census fences (BACKLOG, PHILO-9-01) and `tests/e2e/test_hs171_shade_glass.py::test_shade_artboard_{1440,393}` (font sizes; red on the main export with its own built bundle).

## The criteria → their proof

| Criterion | Red on main | Green (fence) |
|---|---|---|
| 20 MCP + 3 HTTP identities leave the residual set | the set lists them | `test_the_residual_set_paid_exactly_the_story_02_identities`; census `--check` |
| GitHub `example/payments` and Jira `PAY-123` → resource AND watch, or named refusal + pending; MCP twin | 404; `accepted_no_watch`, 0 resources/watches; MCP `svc` unbound | `test_a_github_suggestion_becomes_a_resource_and_a_watch[http,mcp]`, `test_a_jira_suggestion_without_a_connected_account_is_refused_and_stays_pending[http,mcp]`, `test_a_jira_suggestion_with_a_connected_account_becomes_a_resource_and_a_watch` |
| No `unittest.mock` in product code (AST, mutation) | `mcp/tools.py` imports it | `test_no_product_module_imports_unittest_mock`, `test_the_mock_import_fence_turns_red_on_a_mutation` |
| Steward run's COMPARE `review_id` = `open_review`'s | `""` | `test_l7_compare_and_proposal_creation_record_the_review_open_review_returned` |
| `connection.list` cached; per-row time; never checked; Calendar/Models live; face 1440/393; Confluence real probe; recheck admitted for remote, not local; Door count admitted | gh probed on every read; one newest time; "Off"; 0 Confluence calls | `test_philo9_b1_connections.py` (7), `tests/e2e/test_philo9_b1_connections_glass.py` (2), `test_each_admitted_*[github recheck, confluence recheck, jira recheck, door count]`, `test_the_exempt_rows_and_the_reads_make_no_operation` |
| Four decide verbs admitted; agent refused for each | accepted with no row | `test_each_admitted_http_route_…[decide accept/edit_accept/defer/dismiss]`, `test_an_agent_without_a_grant_…[decide *]` |
| Lifecycle five points; real restart; agent stop on another's run refused (R4-1) | no operation handle/receipt; domain-only recovery | `test_philo9_steward_lifecycle.py` (24), `test_philo9_steward_restart.py` (5 restart points), `test_r4_1_…` |
| Each mark one operation + receipt + row; two marks two rows; draft refused; agent refused | new capability | `test_philo9_mark_delivered.py`, `test_an_agent_without_a_grant_…[delivered]` |
| Idempotency (repeat, conflict, new key, no key, concurrent, restart) | new capability | `test_philo9_mark_delivered.py`, `test_d1_a_delivery_replay_after_a_real_restart_answers_the_original` |
| NOT NULL UNIQUE FK; project from the update; one transaction; rollback then replay once | new capability | `test_the_row_names_its_operation_…`, `test_a_mark_that_names_another_project_…`, `test_a_failure_after_the_insert_…` |
| Discovery "mark it delivered" | strict xfail | `test_mark_it_delivered_maps_to_its_tool` (mark removed) |
| Archive one operation; pause + unattended-off inside | zero rows | `test_archive_as_the_owner_…` |
| Each admitted row one op + one receipt on HTTP and MCP; refusal classes; exempt none; no double admission; mutations | zero operations | `test_each_admitted_http_route_…` (29), `test_each_admitted_mcp_tool_…` (20), `test_a_contract_refusal_…`, `test_b2_a_malformed_…`, `test_a_link_is_one_top_level_…`; mutations M1–M28 |
| HTTP PROJECT credential: Door count, Door create with sources, GitHub recheck refused with receipt; protocol refusals receipt-less | 403 `principal_right_required`, 0 rows | `test_b2_a_project_credential_over_http_is_refused_with_a_receipt`, `test_b2_protocol_refusals_stay_receipt_less` |
| Agent without a grant refused through dispatch (P3) | succeeds, 0 rows | `test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[unattended on, archive, …]` |
| Law 9 (the carried race) | IntegrityError; two change rows | `test_philo9_command_race.py` (3) |

## Proof

### Captured run — 2026-09-28T13:28:52Z

- **Command:** `bash .tmp/run_main.sh tests/unit/test_philo9_steward_admission.py tests/unit/test_philo9_steward_lifecycle.py tests/unit/test_philo9_steward_restart.py tests/unit/test_philo9_command_race.py tests/unit/test_philo9_b1_connections.py -q -n 8 -rf --tb=no`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** e5a4bbeea7c88a26ee0aff25c479a79db5c2b4a6

```text
bringing up nodes...
bringing up nodes...

FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF.FFFFFFFFFFFFFFFFFFFFF.FFFFFFFFF.FFFFFFFFF [ 61%]
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF                           [100%]
=========================== short test summary info ============================
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[suggested add]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[nudge send]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[accept review]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[door create with sources]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch baseline]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[resource add]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[trigger]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[decide accept]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[decide edit_accept]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[delivered]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[archive]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[resource remove]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch evaluate]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[github recheck]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[policy write]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[unlink]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[link]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[decide defer]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[door count]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[confluence recheck]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[run]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[publish]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch pause]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch resume]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[link]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[run]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[nudge send]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[suggested add]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[decide dismiss]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch update]
FAILED tests/unit/test_philo9_steward_admission.py::test_a_link_is_one_top_level_admission_and_its_meeting_watch_is_its_child
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[decide dismiss]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch retire]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch evaluate]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch retire]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[delivered]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[policy write]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[trigger]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[archive]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[accept review]
FAILED tests/unit/test_philo9_steward_admission.py::test_archive_as_the_owner_is_one_operation_and_its_pause_and_unattended_off_are_inside
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[decide dismiss]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[decide accept]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[decide defer]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[run]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[suggested add]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[unattended on]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[watch pause]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_reads_and_exempt_edits_keep_todays_behaviour
FAILED tests/unit/test_philo9_steward_admission.py::test_b2_a_project_credential_over_http_is_refused_with_a_receipt
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[decide edit_accept]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[publish]
FAILED tests/unit/test_philo9_steward_admission.py::test_b2_a_malformed_identifiable_write_is_refused_invalid_arguments_with_a_receipt
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[resource add]
FAILED tests/unit/test_philo9_steward_admission.py::test_a_github_suggestion_becomes_a_resource_and_a_watch[mcp]
FAILED tests/unit/test_philo9_steward_admission.py::test_a_jira_suggestion_without_a_connected_account_is_refused_and_stays_pending[http]
FAILED tests/unit/test_philo9_steward_admission.py::test_a_jira_suggestion_without_a_connected_account_is_refused_and_stays_pending[mcp]
FAILED tests/unit/test_philo9_steward_admission.py::test_a_jira_suggestion_with_a_connected_account_becomes_a_resource_and_a_watch
FAILED tests/unit/test_philo9_steward_admission.py::test_the_residual_set_paid_exactly_the_story_02_identities
FAILED tests/unit/test_philo9_steward_admission.py::test_no_product_module_imports_unittest_mock
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l1_a_start_returns_the_run_and_its_operation_non_terminal_while_it_works[http]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l1_a_start_returns_the_run_and_its_operation_non_terminal_while_it_works[mcp]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch rules]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch pause]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l1_one_run_and_one_operation_for_a_command_key_under_concurrent_replay
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch rules]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[github recheck]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l2_a_second_start_is_refused_with_its_own_receipt_and_no_spare_queued_run
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[publish]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[delivered]
FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[github recheck]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l4_a_stop_committed_before_completion_wins
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[archive]
FAILED tests/unit/test_philo9_steward_admission.py::test_a_contract_refusal_of_an_admitted_tool_leaves_its_receipt
FAILED tests/unit/test_philo9_steward_admission.py::test_a_github_suggestion_becomes_a_resource_and_a_watch[http]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch resume]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch test]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch test]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[jira recheck]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_refused_start_has_its_receipt_and_no_run[disabled]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_refused_start_has_its_receipt_and_no_run[unknown project]
FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[decide defer]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l7_compare_and_proposal_creation_record_the_review_open_review_returned
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a6_the_trigger_returns_its_pending_handle_and_its_runs_are_its_children
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_r4_1_an_agents_stop_of_the_owners_run_is_refused_with_a_receipt
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_refused_start_has_its_receipt_and_no_run[cooldown]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l5_stop_is_its_own_operation_and_the_run_ends_cancelled_with_its_own_receipt
FAILED tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[running]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l4_a_completion_committed_before_a_stop_wins_and_the_stop_is_refused
FAILED tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[stopping]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_fault_inside_the_terminal_transaction_rolls_all_three_writes_back
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a1_each_executed_effect_is_a_child_with_the_runs_actor_and_frozen_authority
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_known_failure_ends_the_run_failed_with_one_receipt
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a4_an_identical_re_save_does_not_stop_the_run
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a4_a_first_policy_saved_during_a_no_policy_owner_run_does_not_stop_it
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a6_a_scheduled_run_without_a_recorded_policy_is_refused_steward_policy_required
FAILED tests/unit/test_philo9_b1_connections.py::test_list_on_a_fresh_hub_makes_no_provider_call
FAILED tests/unit/test_philo9_b1_connections.py::test_each_remote_row_returns_its_own_stored_time
FAILED tests/unit/test_philo9_b1_connections.py::test_no_stored_check_reads_never_checked
FAILED tests/unit/test_philo9_b1_connections.py::test_calendar_and_models_read_live
FAILED tests/unit/test_philo9_b1_connections.py::test_confluence_recheck_probes_and_stores_its_time
FAILED tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[insert]
FAILED tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[queued]
FAILED tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[child]
FAILED tests/unit/test_philo9_command_race.py::test_the_kernel_replay_lookup_holds_the_write_lock
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l5_a_stop_between_two_proposal_acceptances_prevents_the_second
FAILED tests/unit/test_philo9_steward_restart.py::test_d1_a_delivery_replay_after_a_real_restart_answers_the_original
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a4_a_disabled_policy_cuts_the_run_off
FAILED tests/unit/test_philo9_command_race.py::test_a_room_command_replay_holds_the_write_lock
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a1_a_forged_child_is_refused_with_a_receipt
FAILED tests/unit/test_philo9_command_race.py::test_a_room_command_race_on_a_delete_answers_the_original_true_twice
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a4_a_changed_policy_refuses_the_next_child_and_the_run_ends_refused
FAILED tests/unit/test_philo9_b1_connections.py::test_list_makes_no_provider_call[http]
FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a6_a_scheduled_run_acts_as_the_scheduler_under_the_recorded_policy
FAILED tests/unit/test_philo9_b1_connections.py::test_list_makes_no_provider_call[mcp]
115 failed, 3 passed in 190.30s (0:03:10)
```

### Captured run — 2026-09-28T13:32:08Z

- **Command:** `.tmp/iso.sh .venv/bin/python scripts/residual_census.py --check --root .tmp/main-copy`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** e5a4bbeea7c88a26ee0aff25c479a79db5c2b4a6

```text
NEW residual identity (not in the set): ('http', 'holdspeak/web/routes/projects.py::build_projects_router.api_add_suggested_source', 'SuggestedSourceService')
NEW residual identity (not in the set): ('http', 'holdspeak/web/routes/projects.py::build_projects_router.api_dismiss_suggested_source', 'SuggestedSourceService')
NEW residual identity (not in the set): ('http', 'holdspeak/web/routes/projects.py::build_projects_router.api_suggested_sources', 'SuggestedSourceService')
NEW residual identity (not in the set): ('mcp', 'connection.list', '')
NEW residual identity (not in the set): ('mcp', 'connection.recheck', '')
NEW residual identity (not in the set): ('mcp', 'nudge.dismiss', '')
NEW residual identity (not in the set): ('mcp', 'nudge.send', '')
NEW residual identity (not in the set): ('mcp', 'project.add_suggested_source', '')
NEW residual identity (not in the set): ('mcp', 'project.configure_steward', '')
NEW residual identity (not in the set): ('mcp', 'project.dismiss_suggested_source', '')
NEW residual identity (not in the set): ('mcp', 'project.get_steward_run', '')
NEW residual identity (not in the set): ('mcp', 'project.run_steward', '')
NEW residual identity (not in the set): ('mcp', 'project.steward.trigger', '')
NEW residual identity (not in the set): ('mcp', 'project.stop_steward', '')
NEW residual identity (not in the set): ('mcp', 'project.suggested_sources', '')
NEW residual identity (not in the set): ('mcp', 'project.watch.evaluate', '')
NEW residual identity (not in the set): ('mcp', 'project.watch.inspect', '')
NEW residual identity (not in the set): ('mcp', 'project.watch.pause', '')
NEW residual identity (not in the set): ('mcp', 'project.watch.resume', '')
NEW residual identity (not in the set): ('mcp', 'project.watch.retire', '')
NEW residual identity (not in the set): ('mcp', 'project.watch.set_rules', '')
NEW residual identity (not in the set): ('mcp', 'project.watch.test', '')
NEW residual identity (not in the set): ('mcp', 'steward.nudges', '')
RESIDUAL FENCE RED: 23 problem(s) against /Users/karol/dev/tools/wt-philo-9-02/.tmp/main-copy
```

### Captured run — 2026-09-28T13:32:10Z

- **Command:** `.tmp/iso.sh .venv/bin/python scripts/residual_census.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e5a4bbeea7c88a26ee0aff25c479a79db5c2b4a6

```text
RESIDUAL FENCE GREEN: 240 identities match /Users/karol/dev/tools/wt-philo-9-02
```

### Captured run — 2026-09-28T13:32:16Z

- **Command:** `.tmp/iso.sh .venv/bin/python -m pytest -q -n 8 -p no:cacheprovider tests/integration/test_hs165_mcp_walk.py tests/integration/test_kernel_real_hub.py tests/integration/test_principal_separation.py tests/integration/test_steward_routes.py tests/integration/test_update_routes.py tests/integration/test_watch_compounding.py tests/mcp/test_hs168_connection_tools.py tests/unit/test_db.py tests/unit/test_docs_navigation.py tests/unit/test_door_routes.py tests/unit/test_hs167_close_fixes.py tests/unit/test_hs167_debts.py tests/unit/test_hs167_walk_fixes.py tests/unit/test_hs168_connections_service.py tests/unit/test_hs168_walk_fixes.py tests/unit/test_hs169_door.py tests/unit/test_hs169_room_copy.py tests/unit/test_hs169_wire.py tests/unit/test_hs172_loop_wire.py tests/unit/test_hs173_health_wire.py tests/unit/test_hs173_nudge_wire.py tests/unit/test_hs175_door_orphan.py tests/unit/test_hs175_meeting_watch.py tests/unit/test_kernel_broker.py tests/unit/test_kernel_effect_fence.py tests/unit/test_phase200_one_composition_root.py tests/unit/test_phase200_watch_arming.py tests/unit/test_philo_census.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo5_graph_op.py tests/unit/test_philo5_the_loop.py tests/unit/test_philo7_article_xi.py tests/unit/test_philo7_atlas.py tests/unit/test_philo7_compat.py tests/unit/test_philo7_contract.py tests/unit/test_philo7_discovery.py tests/unit/test_philo7_grant_lifecycle.py tests/unit/test_philo7_grant_restart.py tests/unit/test_philo7_membership_decisions.py tests/unit/test_philo7_round_two.py tests/unit/test_philo8_atlas.py tests/unit/test_philo9_02_rig_op.py tests/unit/test_philo9_b1_connections.py tests/unit/test_philo9_command_race.py tests/unit/test_philo9_compat.py tests/unit/test_philo9_contract.py tests/unit/test_philo9_delivery_record.py tests/unit/test_philo9_discovery.py tests/unit/test_philo9_mark_delivered.py tests/unit/test_philo9_rig_op.py tests/unit/test_philo9_room_contract.py tests/unit/test_philo9_steward_admission.py tests/unit/test_philo9_steward_lifecycle.py tests/unit/test_philo9_steward_restart.py tests/unit/test_project_mcp_commands.py tests/unit/test_project_mcp_driver.py tests/unit/test_project_mcp_palette.py tests/unit/test_project_mcp.py tests/unit/test_project_service_characterization.py tests/unit/test_project_setup_service.py tests/unit/test_steward_conductor.py tests/unit/test_steward_effects.py tests/unit/test_steward_engine.py tests/unit/test_steward_run_due.py tests/unit/test_steward_schema.py tests/unit/test_watch_evaluate_due.py tests/unit/test_watch_graduation_schema.py tests/unit/test_watch_legacy_compat.py tests/unit/test_watch_no_third_door.py tests/unit/test_watch_service.py tests/web/test_hs168_connections_routes.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** e5a4bbeea7c88a26ee0aff25c479a79db5c2b4a6

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  3%]
........................................................................ [  7%]
........................................................................ [ 10%]
........................................................................ [ 14%]
........................................................................ [ 18%]
........................................................................ [ 21%]
...................................................................F.... [ 25%]
........................................................................ [ 29%]
........................................................................ [ 32%]
........................................................................ [ 36%]
........................................................................ [ 39%]
........................................................................ [ 43%]
........................................................................ [ 47%]
........................................................................ [ 50%]
........................................................................ [ 54%]
........................................................................ [ 58%]
........................................................................ [ 61%]
........................................................................ [ 65%]
........................................................................ [ 68%]
........................................................................ [ 72%]
........................................................................ [ 76%]
........................................................................ [ 79%]
........................................................................ [ 83%]
........................................................................ [ 87%]
........................................................................ [ 90%]
...........s............................................................ [ 94%]
........................................................................ [ 98%]
.......................................                                  [100%]
=================================== FAILURES ===================================
________________________ test_committed_join_is_current ________________________
[gw6] darwin -- Python 3.13.11 /Users/karol/dev/tools/wt-philo-9-02/.venv/bin/python

joined = ({'cases': [{'applicability': 'applicable', 'completion_bound_s': 120, 'edge_ids': ['edge.route.meeting_capture_recove..._shelf.refused', 'case-revision: live-astra ran an older revision of case.j10.route_brief_generate.load_failure', ...])

    def test_committed_join_is_current(joined):
        """--check's own comparison: the file on disk is the join of the inputs."""
        graph, _ = joined
>       assert (ROOT / gen.OUTPUT).read_text(encoding="utf-8") == gen.render(graph)
E       assert '{\n "schema_...n  }\n ]\n}\n' == '{\n "schema_...n  }\n ]\n}\n'
E         
E         Skipping 1239 identical leading characters in diff, use -v to show
E         Skipping 6306571 identical trailing characters in diff, use -v to show
E         - sha256": "b5be3420d75aa7e7bd829b9688d1c0d6a8d8b96bf3d51e3a1c2a124f067a56e9"
E         + sha256": "3f392bb4be9a0ad690beb142b16bdc4667f31a5c965290f14e9cf62a919497f1"
E             },

tests/unit/test_philo_graph_reference.py:108: AssertionError
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:493: Owner's real DB not found (CI or isolated HOME)
FAILED tests/unit/test_philo_graph_reference.py::test_committed_join_is_current
1 failed, 1981 passed, 1 skipped in 116.95s (0:01:56)
```

### Captured run — 2026-09-28T13:34:30Z

- **Command:** `.tmp/iso.sh .venv/bin/python -m pytest -q -n 8 -p no:cacheprovider tests/integration/test_hs165_mcp_walk.py tests/integration/test_kernel_real_hub.py tests/integration/test_principal_separation.py tests/integration/test_steward_routes.py tests/integration/test_update_routes.py tests/integration/test_watch_compounding.py tests/mcp/test_hs168_connection_tools.py tests/unit/test_db.py tests/unit/test_docs_navigation.py tests/unit/test_door_routes.py tests/unit/test_hs167_close_fixes.py tests/unit/test_hs167_debts.py tests/unit/test_hs167_walk_fixes.py tests/unit/test_hs168_connections_service.py tests/unit/test_hs168_walk_fixes.py tests/unit/test_hs169_door.py tests/unit/test_hs169_room_copy.py tests/unit/test_hs169_wire.py tests/unit/test_hs172_loop_wire.py tests/unit/test_hs173_health_wire.py tests/unit/test_hs173_nudge_wire.py tests/unit/test_hs175_door_orphan.py tests/unit/test_hs175_meeting_watch.py tests/unit/test_kernel_broker.py tests/unit/test_kernel_effect_fence.py tests/unit/test_phase200_one_composition_root.py tests/unit/test_phase200_watch_arming.py tests/unit/test_philo_census.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo5_graph_op.py tests/unit/test_philo5_the_loop.py tests/unit/test_philo7_article_xi.py tests/unit/test_philo7_atlas.py tests/unit/test_philo7_compat.py tests/unit/test_philo7_contract.py tests/unit/test_philo7_discovery.py tests/unit/test_philo7_grant_lifecycle.py tests/unit/test_philo7_grant_restart.py tests/unit/test_philo7_membership_decisions.py tests/unit/test_philo7_round_two.py tests/unit/test_philo8_atlas.py tests/unit/test_philo9_02_rig_op.py tests/unit/test_philo9_b1_connections.py tests/unit/test_philo9_command_race.py tests/unit/test_philo9_compat.py tests/unit/test_philo9_contract.py tests/unit/test_philo9_delivery_record.py tests/unit/test_philo9_discovery.py tests/unit/test_philo9_mark_delivered.py tests/unit/test_philo9_rig_op.py tests/unit/test_philo9_room_contract.py tests/unit/test_philo9_steward_admission.py tests/unit/test_philo9_steward_lifecycle.py tests/unit/test_philo9_steward_restart.py tests/unit/test_project_mcp_commands.py tests/unit/test_project_mcp_driver.py tests/unit/test_project_mcp_palette.py tests/unit/test_project_mcp.py tests/unit/test_project_service_characterization.py tests/unit/test_project_setup_service.py tests/unit/test_steward_conductor.py tests/unit/test_steward_effects.py tests/unit/test_steward_engine.py tests/unit/test_steward_run_due.py tests/unit/test_steward_schema.py tests/unit/test_watch_evaluate_due.py tests/unit/test_watch_graduation_schema.py tests/unit/test_watch_legacy_compat.py tests/unit/test_watch_no_third_door.py tests/unit/test_watch_service.py tests/web/test_hs168_connections_routes.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e5a4bbeea7c88a26ee0aff25c479a79db5c2b4a6

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  3%]
........................................................................ [  7%]
........................................................................ [ 10%]
........................................................................ [ 14%]
........................................................................ [ 18%]
........................................................................ [ 21%]
........................................................................ [ 25%]
........................................................................ [ 29%]
........................................................................ [ 32%]
........................................................................ [ 36%]
........................................................................ [ 39%]
........................................................................ [ 43%]
........................................................................ [ 47%]
........................................................................ [ 50%]
........................................................................ [ 54%]
........................................................................ [ 58%]
........................................................................ [ 61%]
........................................................................ [ 65%]
........................................................................ [ 68%]
........................................................................ [ 72%]
........................................................................ [ 76%]
........................................................................ [ 79%]
........................................................................ [ 83%]
........................................................................ [ 87%]
........................................................................ [ 90%]
........................................................................ [ 94%]
........................................................................ [ 98%]
...........s...........................                                  [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:493: Owner's real DB not found (CI or isolated HOME)
1982 passed, 1 skipped in 127.11s (0:02:07)
```

### Captured run — 2026-09-28T13:36:38Z

- **Command:** `.tmp/iso.sh .venv/bin/python .tmp/mutate.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e5a4bbeea7c88a26ee0aff25c479a79db5c2b4a6

```text
RED (caught): M1 admission not enforced (the registry runs admitted rows without the kernel) [holdspeak/operations.py] -> FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch rules] | FAILED tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch test] | 49 failed in 825.02s (0:13:45)
RED (caught): M2 the grant check point grants every agent [holdspeak/kernel/project.py] -> FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[unattended on] | FAILED tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[watch pause] | 13 failed in 9.05s
RED (caught): M3 B2: the edge keeps OWNER for the Room's admitted routes [holdspeak/principals.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_admission.py:535: AssertionError: ('project.door.count', {'error': 'principal_right_required', 'missing_right': 'owner', 'principal': 'agent', 'principal_identity': 'remote-project-agent', ...}) | FAILED tests/unit/test_philo9_steward_admission.py::test_b2_a_project_credential_over_http_is_refused_with_a_receipt | 1 failed in 1.20s
RED (caught): M4 B2: the adapter drops the exempt form's OWNER right [holdspeak/web/routes/project_door.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_admission.py:554: AssertionError: {"projectId":"proj-06f70cb89647"} | FAILED tests/unit/test_philo9_steward_admission.py::test_b2_protocol_refusals_stay_receipt_less | 1 failed in 1.20s
RED (caught): M5 B2: a malformed body is FastAPI's (no receipt) [holdspeak/web/routes/_room_kernel.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_admission.py:127: AssertionError: [] | FAILED tests/unit/test_philo9_steward_admission.py::test_b2_a_malformed_identifiable_write_is_refused_invalid_arguments_with_a_receipt | 1 failed in 21.24s
RED (caught): M6 source addition arms no watch [holdspeak/services/project_service.py] -> FAILED tests/unit/test_philo9_steward_admission.py::test_a_github_suggestion_becomes_a_resource_and_a_watch[http] | FAILED tests/unit/test_philo9_steward_admission.py::test_a_github_suggestion_becomes_a_resource_and_a_watch[mcp] | 2 failed in 1.86s
RED (caught): M7 a Jira suggestion accepted without a connection [holdspeak/services/suggested_source_service.py] -> FAILED tests/unit/test_philo9_steward_admission.py::test_a_jira_suggestion_without_a_connected_account_is_refused_and_stays_pending[http] | FAILED tests/unit/test_philo9_steward_admission.py::test_a_jira_suggestion_without_a_connected_account_is_refused_and_stays_pending[mcp] | 2 failed in 1.85s
RED (caught): M8 the link's meeting watch is a second top-level admission [holdspeak/services/watch_service.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_admission.py:422: AssertionError: [{'authority_basis': 'authenticated_principal+declared_capability+hard_prerequisites+interruption_policy', 'name': 'pr...","watch_id":"w_df9092b5f5e9","project_id":"proj-b1e2deea1bef","connector_id":"meeting","why":"meeting linked"}', ...}] | FAILED tests/unit/test_philo9_steward_admission.py::test_a_link_is_one_top_level_admission_and_its_meeting_watch_is_its_child | 1 failed in 1.20s
RED (caught): M9 archive does not stamp the policy's owner operation [holdspeak/services/project_service.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_admission.py:443: AssertionError: assert 'op_a48563d6d...53e3bbec5b53e' == 'op_79adbc542...daac12b51f397' | FAILED tests/unit/test_philo9_steward_admission.py::test_archive_as_the_owner_is_one_operation_and_its_pause_and_unattended_off_are_inside | 1 failed in 1.25s
RED (caught): M10 F20: COMPARE reads the old key [holdspeak/services/project_steward_service.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_lifecycle.py:389: AssertionError: (['prev_4d4ca045d7a342e8a2631ee9349982a1', 'prev_4d4ca045d7a342e8a2631ee9349982a1'], {'proposal_count': 0, 'proposals': [], 'review_id': ''}) | FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l7_compare_and_proposal_creation_record_the_review_open_review_returned | 1 failed in 1.28s
RED (caught): M11 L1: the command key is not derived (a replay is a new operation) [holdspeak/services/project_kernel.py] -> FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l1_one_run_and_one_operation_for_a_command_key_under_concurrent_replay | FAILED tests/unit/test_philo9_mark_delivered.py::test_a_repeat_of_one_key_and_payload_answers_the_original | 2 failed in 1.90s
RED (caught): M12 L1: the start writes its receipt at once (no pending handle) [holdspeak/services/steward_contract.py] -> FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l1_a_start_returns_the_run_and_its_operation_non_terminal_while_it_works[http] | FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l1_a_start_returns_the_run_and_its_operation_non_terminal_while_it_works[mcp] | 2 failed in 1.83s
RED (caught): M13 L3: the run row is written outside the terminal transaction [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_lifecycle.py:268: assert False | FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_fault_inside_the_terminal_transaction_rolls_all_three_writes_back | 1 failed in 21.23s
RED (caught): M14 L4: completion does not re-read the stop under its transaction [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_lifecycle.py:314: AssertionError: assert ('completed',...completed', 1) == ('interrupted...requested', 1) | FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l4_a_stop_committed_before_completion_wins | 1 failed in 1.25s
RED (caught): M15 L4: stop does not re-read a terminal run [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_lifecycle.py:323: AssertionError: {"success":true,"run_id":"pstrun_48ccd4c824f75d75b31dcdfa95b42019","operation_id":"op_c30076b7dd394543b7f9383e1225ef29","receipt":{"receipt_id":"rcpt_e9689127ab6f4efb81ee27c6e6347804","operation_id":"op_c30076b7dd394543b7f9383e1225ef29","state":"succeeded","outcome":"stop_requested","result_ref":"steward_run:pstrun_48ccd4c824f75d75b31dcdfa95b42019","created_at":1790603505.732404,"actor_kind":"owner","actor_identity":"owner-session","delegator_kind":"","delegator_identity":"","authority_basis":
RED (caught): M16 L5: no boundary check before a child (inside the proposal batch) [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_lifecycle.py:359: AssertionError: assert [('project.de...', 'refused')] == [('project.de... 'succeeded')] | FAILED tests/unit/test_philo9_steward_lifecycle.py::test_l5_a_stop_between_two_proposal_acceptances_prevents_the_second | 1 failed in 6.74s
RED (caught): M17 A1: a child does not name the run's frozen authority [holdspeak/kernel/project_codec.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_lifecycle.py:410: AssertionError: assert 'authenticate...uption_policy' == 'project-stew...d93aad944a010' | FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a1_each_executed_effect_is_a_child_with_the_runs_actor_and_frozen_authority | 1 failed in 6.62s
RED (caught): M18 A4: the policy digest is not checked [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_lifecycle.py:452: AssertionError: assert ('completed',..., 'completed') == ('interrupted...licy_changed') | FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a4_a_changed_policy_refuses_the_next_child_and_the_run_ends_refused | 1 failed in 1.26s
RED (caught): M19 A4: a running run reads the live policy (a later save enlarges it) [holdspeak/services/project_steward_service.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_lifecycle.py:480: AssertionError: assert [{'authority_...effect', ...}] == [] | FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a4_a_first_policy_saved_during_a_no_policy_owner_run_does_not_stop_it | 1 failed in 1.27s
RED (caught): M20 A6: a scheduler start needs no recorded policy [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_lifecycle.py:542: KeyError: 'code' | FAILED tests/unit/test_philo9_steward_lifecycle.py::test_a6_a_scheduled_run_without_a_recorded_policy_is_refused_steward_policy_required | 1 failed in 1.21s
RED (caught): M21 R4-1: stop is not bound to the stored run's requester [holdspeak/kernel/project_codec.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_lifecycle.py:578: AssertionError: {'code': 'project_delegation_required', 'error': 'The kernel refused project.stop_steward: project_delegation_required...t-agent', 'actor_kind': 'agent', 'authority_basis': 'refused_at_admission', 'created_at': 1790603527.766939, ...}, ...} | FAILED tests/unit/test_philo9_steward_lifecycle.py::test_r4_1_an_agents_stop_of_the_owners_run_is_refused_with_a_receipt | 1 failed in 1.25s
RED (caught): M22 L6: the startup recovery is not wired [holdspeak/web_server.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_steward_restart.py:179: AssertionError: {'op_93011b66525d4a4b9461e714cb61a561': ('op_93011b66525d4a4b9461e714cb61a561', 'project.run_steward', 'claimed', '', None)} | FAILED tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[running] | 1 failed in 3.01s
RED (caught): M23 D2: the delivery row is inserted outside the terminal transaction [holdspeak/services/project_update_service.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_mark_delivered.py:252: AssertionError: {'operation_id': 'op_20a523096f04470ba3bdf455d862e82e', 'outcome': 'failed', 'state': 'failed'} | FAILED tests/unit/test_philo9_mark_delivered.py::test_a_failure_after_the_insert_leaves_no_row_no_state_no_receipt_and_a_replay_succeeds_once | 1 failed in 1.21s
RED (caught): M24 D2: delivered_at is the write time, not the confirmation time [holdspeak/services/project_update_service.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_mark_delivered.py:263: AssertionError: assert '2026-09-28T13:52:17+00:00' == '2026-09-28T13:52:16+00:00' | FAILED tests/unit/test_philo9_mark_delivered.py::test_a_failure_after_the_insert_leaves_no_row_no_state_no_receipt_and_a_replay_succeeds_once | 1 failed, 2 passed in 3.57s
RED (caught): M25 D1: a replay of a mark's key makes a second row [holdspeak/services/project_update_service.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_mark_delivered.py:160: KeyError: 'delivery' | FAILED tests/unit/test_philo9_mark_delivered.py::test_a_repeat_of_one_key_and_payload_answers_the_original | 1 failed in 1.27s
RED (caught): M26 law 9: the kernel's replay lookup holds no write lock [holdspeak/kernel/journal_atomic.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_command_race.py:92: AssertionError: the loser raised instead of replaying: [IntegrityError('UNIQUE constraint failed: kernel_operations.principal_identity, kernel_operations.idempotency_key')] | FAILED tests/unit/test_philo9_command_race.py::test_the_kernel_replay_lookup_holds_the_write_lock | 1 failed in 0.42s
RED (caught): M27 law 9: a Room command's write takes no lock and does not look again [holdspeak/services/project_service.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_command_race.py:123: AssertionError: a caller raised: [IntegrityError('UNIQUE constraint failed: project_changes.id')] | FAILED tests/unit/test_philo9_command_race.py::test_a_room_command_replay_holds_the_write_lock | 1 failed in 0.44s
RED (caught): M28 law 9: a replay of an admitting operation re-runs its admission [holdspeak/kernel/broker.py] -> /Users/karol/dev/tools/wt-philo-9-02/tests/unit/test_philo9_mark_delivered.py:205: AssertionError: ['{"error":"operation_already_terminal"}', '{"success":true,"delivery":{"id":"pdel_8fbd4d8d2135cec3","update_id":"pupd...ability+hard_prerequisites+interruption_policy","target_ref":"project_update:pupd_75914594c905489480d0f4c8ca586005"}}'] | FAILED tests/unit/test_philo9_mark_delivered.py::test_two_concurrent_requests_with_one_key_make_one_row | 1 failed in 1.24s
MUTATIONS: 28 run, 0 missed
```

### Captured run — 2026-09-28T13:52:45Z

- **Command:** `.tmp/iso.sh env HOLDSPEAK_EVIDENCE_WRITE=1 .venv/bin/python -m pytest -q -n 4 -p no:cacheprovider tests/e2e/test_philo9_b1_connections_glass.py tests/e2e/test_hs168_connections_glass.py tests/e2e/test_hs169_door_glass.py tests/e2e/test_hs174_door_confluence_glass.py -rf`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e5a4bbeea7c88a26ee0aff25c479a79db5c2b4a6

```text
bringing up nodes...
bringing up nodes...

ss.............                                                          [100%]
13 passed, 2 skipped in 39.50s
```

### Captured run — 2026-09-28T13:53:41Z

- **Command:** `bash .tmp/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e5a4bbeea7c88a26ee0aff25c479a79db5c2b4a6

```text
== gen_operations_json.py --check
OK docs/generated/operations.json
== gen_mcp_sidecar_doc.py --check
wrote docs/MCP_SIDECAR.md
  237 tools across 42 families
== check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
== philo_repository_census.py --check
Repository census: 5 outputs verified.
== philo_api_reference.py --check
API reference checked
== philo_boundary_census.py --check
Boundary candidate census checked
== philo_doctor_reference.py --check
Doctor reference: 41 check functions
== philo_config_reference.py --check
Configuration declaration reference is current
== philo_graph_reference.py --check
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
== validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
== generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
== check_doc_coverage.py --check
Documentation coverage checked.
== residual_census.py --check
RESIDUAL FENCE GREEN: 240 identities match /Users/karol/dev/tools/wt-philo-9-02
Documentation navigation: 3 files checked; local targets and Markdown headings resolve.
DOCS RC=0
```

### Captured run — 2026-09-28T13:54:00Z

- **Command:** `.tmp/iso.sh .venv/bin/python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e5a4bbeea7c88a26ee0aff25c479a79db5c2b4a6

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2931 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-28T13:54:37Z

- **Command:** `.tmp/iso.sh .venv/bin/python -m pytest --collect-only -q -p no:cacheprovider tests/unit/test_philo9_steward_admission.py tests/unit/test_philo9_steward_lifecycle.py tests/unit/test_philo9_steward_restart.py tests/unit/test_philo9_mark_delivered.py tests/unit/test_philo9_command_race.py tests/unit/test_philo9_02_rig_op.py tests/unit/test_philo9_b1_connections.py tests/e2e/test_philo9_b1_connections_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e5a4bbeea7c88a26ee0aff25c479a79db5c2b4a6

```text
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[accept review]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[archive]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[confluence recheck]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[decide accept]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[decide defer]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[decide dismiss]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[decide edit_accept]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[delivered]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[door count]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[door create with sources]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[github recheck]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[link]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[nudge send]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[policy write]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[publish]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[resource add]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[resource remove]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[run]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[suggested add]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[trigger]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[unlink]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch baseline]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch evaluate]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch pause]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch resume]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch retire]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch rules]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch test]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_http_route_is_one_operation_with_one_receipt[watch update]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[accept review]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[archive]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[decide defer]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[decide dismiss]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[delivered]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[github recheck]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[jira recheck]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[link]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[nudge send]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[policy write]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[publish]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[run]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[suggested add]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[trigger]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch evaluate]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch pause]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch resume]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch retire]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch rules]
tests/unit/test_philo9_steward_admission.py::test_each_admitted_mcp_tool_is_one_operation_with_one_receipt[watch test]
tests/unit/test_philo9_steward_admission.py::test_the_exempt_rows_and_the_reads_make_no_operation
tests/unit/test_philo9_steward_admission.py::test_a_link_is_one_top_level_admission_and_its_meeting_watch_is_its_child
tests/unit/test_philo9_steward_admission.py::test_archive_as_the_owner_is_one_operation_and_its_pause_and_unattended_off_are_inside
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[archive]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[decide accept]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[decide defer]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[decide dismiss]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[decide edit_accept]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[delivered]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[github recheck]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[publish]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[resource add]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[run]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[suggested add]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[unattended on]
tests/unit/test_philo9_steward_admission.py::test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes[watch pause]
tests/unit/test_philo9_steward_admission.py::test_an_agent_reads_and_exempt_edits_keep_todays_behaviour
tests/unit/test_philo9_steward_admission.py::test_b2_a_project_credential_over_http_is_refused_with_a_receipt
tests/unit/test_philo9_steward_admission.py::test_b2_protocol_refusals_stay_receipt_less
tests/unit/test_philo9_steward_admission.py::test_b2_a_malformed_identifiable_write_is_refused_invalid_arguments_with_a_receipt
tests/unit/test_philo9_steward_admission.py::test_a_contract_refusal_of_an_admitted_tool_leaves_its_receipt
tests/unit/test_philo9_steward_admission.py::test_a_github_suggestion_becomes_a_resource_and_a_watch[http]
tests/unit/test_philo9_steward_admission.py::test_a_github_suggestion_becomes_a_resource_and_a_watch[mcp]
tests/unit/test_philo9_steward_admission.py::test_a_jira_suggestion_without_a_connected_account_is_refused_and_stays_pending[http]
tests/unit/test_philo9_steward_admission.py::test_a_jira_suggestion_without_a_connected_account_is_refused_and_stays_pending[mcp]
tests/unit/test_philo9_steward_admission.py::test_a_jira_suggestion_with_a_connected_account_becomes_a_resource_and_a_watch
tests/unit/test_philo9_steward_admission.py::test_the_residual_set_paid_exactly_the_story_02_identities
tests/unit/test_philo9_steward_admission.py::test_no_product_module_imports_unittest_mock
tests/unit/test_philo9_steward_admission.py::test_the_mock_import_fence_turns_red_on_a_mutation
tests/unit/test_philo9_steward_lifecycle.py::test_l1_a_start_returns_the_run_and_its_operation_non_terminal_while_it_works[http]
tests/unit/test_philo9_steward_lifecycle.py::test_l1_a_start_returns_the_run_and_its_operation_non_terminal_while_it_works[mcp]
tests/unit/test_philo9_steward_lifecycle.py::test_l1_one_run_and_one_operation_for_a_command_key_under_concurrent_replay
tests/unit/test_philo9_steward_lifecycle.py::test_l2_a_second_start_is_refused_with_its_own_receipt_and_no_spare_queued_run
tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_known_failure_ends_the_run_failed_with_one_receipt
tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_refused_start_has_its_receipt_and_no_run[disabled]
tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_refused_start_has_its_receipt_and_no_run[cooldown]
tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_refused_start_has_its_receipt_and_no_run[unknown project]
tests/unit/test_philo9_steward_lifecycle.py::test_l3_a_fault_inside_the_terminal_transaction_rolls_all_three_writes_back
tests/unit/test_philo9_steward_lifecycle.py::test_l5_stop_is_its_own_operation_and_the_run_ends_cancelled_with_its_own_receipt
tests/unit/test_philo9_steward_lifecycle.py::test_l4_a_stop_committed_before_completion_wins
tests/unit/test_philo9_steward_lifecycle.py::test_l4_a_completion_committed_before_a_stop_wins_and_the_stop_is_refused
tests/unit/test_philo9_steward_lifecycle.py::test_l5_a_stop_between_two_proposal_acceptances_prevents_the_second
tests/unit/test_philo9_steward_lifecycle.py::test_l7_compare_and_proposal_creation_record_the_review_open_review_returned
tests/unit/test_philo9_steward_lifecycle.py::test_a1_each_executed_effect_is_a_child_with_the_runs_actor_and_frozen_authority
tests/unit/test_philo9_steward_lifecycle.py::test_a1_a_forged_child_is_refused_with_a_receipt
tests/unit/test_philo9_steward_lifecycle.py::test_a4_a_changed_policy_refuses_the_next_child_and_the_run_ends_refused
tests/unit/test_philo9_steward_lifecycle.py::test_a4_an_identical_re_save_does_not_stop_the_run
tests/unit/test_philo9_steward_lifecycle.py::test_a4_a_first_policy_saved_during_a_no_policy_owner_run_does_not_stop_it
tests/unit/test_philo9_steward_lifecycle.py::test_a4_a_disabled_policy_cuts_the_run_off
tests/unit/test_philo9_steward_lifecycle.py::test_a6_a_scheduled_run_acts_as_the_scheduler_under_the_recorded_policy
tests/unit/test_philo9_steward_lifecycle.py::test_a6_a_scheduled_run_without_a_recorded_policy_is_refused_steward_policy_required
tests/unit/test_philo9_steward_lifecycle.py::test_a6_the_trigger_returns_its_pending_handle_and_its_runs_are_its_children
tests/unit/test_philo9_steward_lifecycle.py::test_r4_1_an_agents_stop_of_the_owners_run_is_refused_with_a_receipt
tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[insert]
tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[queued]
tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[running]
tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[stopping]
tests/unit/test_philo9_steward_restart.py::test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once[child]
tests/unit/test_philo9_steward_restart.py::test_d1_a_delivery_replay_after_a_real_restart_answers_the_original
tests/unit/test_philo9_mark_delivered.py::test_each_mark_is_one_admitted_operation_its_receipt_and_its_row[http]
tests/unit/test_philo9_mark_delivered.py::test_each_mark_is_one_admitted_operation_its_receipt_and_its_row[mcp]
tests/unit/test_philo9_mark_delivered.py::test_two_marks_are_two_rows_and_two_receipts
tests/unit/test_philo9_mark_delivered.py::test_a_draft_is_refused_update_not_published_with_a_receipt_and_no_row[http]
tests/unit/test_philo9_mark_delivered.py::test_a_draft_is_refused_update_not_published_with_a_receipt_and_no_row[mcp]
tests/unit/test_philo9_mark_delivered.py::test_a_mark_that_names_another_project_is_refused_and_the_project_comes_from_the_update
tests/unit/test_philo9_mark_delivered.py::test_a_repeat_of_one_key_and_payload_answers_the_original
tests/unit/test_philo9_mark_delivered.py::test_one_key_with_a_changed_payload_is_refused_idempotency_conflict
tests/unit/test_philo9_mark_delivered.py::test_a_new_key_to_the_same_recipient_makes_a_second_row
tests/unit/test_philo9_mark_delivered.py::test_an_mcp_mark_without_a_key_is_a_new_delivery
tests/unit/test_philo9_mark_delivered.py::test_two_concurrent_requests_with_one_key_make_one_row
tests/unit/test_philo9_mark_delivered.py::test_the_row_names_its_operation_not_null_unique_and_referenced
tests/unit/test_philo9_mark_delivered.py::test_a_failure_after_the_insert_leaves_no_row_no_state_no_receipt_and_a_replay_succeeds_once
tests/unit/test_philo9_mark_delivered.py::test_a_delivery_leaves_the_published_update_untouched
tests/unit/test_philo9_command_race.py::test_the_kernel_replay_lookup_holds_the_write_lock
tests/unit/test_philo9_command_race.py::test_a_room_command_replay_holds_the_write_lock
tests/unit/test_philo9_command_race.py::test_a_room_command_race_on_a_delete_answers_the_original_true_twice
tests/unit/test_philo9_02_rig_op.py::test_the_rig_reads_the_receipt_of_each_admitted_steward_write
tests/unit/test_philo9_b1_connections.py::test_list_makes_no_provider_call[http]
tests/unit/test_philo9_b1_connections.py::test_list_makes_no_provider_call[mcp]
tests/unit/test_philo9_b1_connections.py::test_list_on_a_fresh_hub_makes_no_provider_call
tests/unit/test_philo9_b1_connections.py::test_each_remote_row_returns_its_own_stored_time
tests/unit/test_philo9_b1_connections.py::test_no_stored_check_reads_never_checked
tests/unit/test_philo9_b1_connections.py::test_calendar_and_models_read_live
tests/unit/test_philo9_b1_connections.py::test_confluence_recheck_probes_and_stores_its_time
tests/e2e/test_philo9_b1_connections_glass.py::test_each_card_shows_its_own_age[1440]
tests/e2e/test_philo9_b1_connections_glass.py::test_each_card_shows_its_own_age[393]

135 tests collected in 0.38s
```

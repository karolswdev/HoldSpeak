# Evidence - PHILO-9-07

- **Story:** PHILO-9-07 - The project delegation grant (canvas first)
- **Status:** done
- **Date:** 2026-09-28
- **Branch:** `feat/philo-9-07` on story 02's head `aeae7bd8` (story 02 built, not yet merged).
- **Red on main:** exports of main `1f332bc3` (`git archive origin/main`): `assets/story-07-proof/red_main.sh` (the backend fences, with the test helpers they import) and `red_face.sh` (the glass fences, main's own bundle built from main's web source). A 404 for the new grant route is never counted as a red; the reds are the assertions that run BEFORE any grant.

## Summary

- **The grant** (`holdspeak/kernel/project.py`, `holdspeak/services/project_delegation.py`): the sibling table `kernel_project_delegations` (Phase 7's columns plus `project_id`; one LIVE per agent and project; the terms with the operations stored in the row), additive. The one check is Phase 7's `desk.check_row` (a `table` argument added) plus the project; the codes `project_delegation_required` → `_expired` → `_revoked`; the terms hash is the imported schedule `_hash` with the expiry inside. `project.delegation.grant` / `.revoke`: Room kernel operations, owner-only (`owner_principal_required` with a receipt for an agent), admitted, the table write and the receipt in one transaction (`KernelHandle.terminal(effect=...)`), HTTP only (`PUT`/`DELETE /api/settings/remote/delegations/{identity}/projects/{project_id}`), in no MCP palette.
- **The agent's bound** (`holdspeak/kernel/project_codec.py`, `holdspeak/kernel/desk_broker.py`): admission by identity AND project, the project resolved from the stored run or update; the grant id and hash frozen on the operation; approval and the claim re-check THAT row (never a newer G2). `PROJECT_GRANT_OPERATIONS` = `{project.run_steward, project.stop_steward, project.publish_update}`; every other admitted Room row stays refused for an agent.
- **R4-1, the run's children** (`holdspeak/services/steward_contract.py`, `holdspeak/kernel/causation.py`): an agent's run freezes its grant beside the owner's policy (`authority_json.grant`, `authority_terms.grant_id/grant_sha256`); each child acts as the agent on the steward's trusted path (the one alternative to an owner continuation) and names `project-steward:<run>:<authority_sha256>`; its approval and its claim re-check the frozen grant, so after a revoke the next child is refused WITH its receipt and the run ends `refused`; with no next child, the run's boundary or its completion callback ends it `refused`. `kernel.receipt` names the grant and the policy in one answer.
- **Lifecycle:** optional `expires_at`; owner revoke; the owner's credential revoke (Settings and `DELETE /api/principals/agents/{identity}`) ends every LIVE project grant FIRST, each with its receipt (`credential_revoked`); identity-keyed, so a restart and a reissue keep a LIVE grant.
- **The wire** (`GET /api/settings/remote`): `credentials[].palette` is the ISSUED name (DESK reads DESK; `AgentCredential.palette_name`); `credentials[].project_delegations`; `project_delegations[]` orphans beside Phase 7's `delegations[]`.
- **The face** (`web/src/pages/cores/SettingsCore.tsx`), as the ratified canvas draws it: set A words (`PROJECT_GRANT_WORDS`); the library `Disclosure` `▸ Projects` opens one `GadgetRow` per project in the row's own expansion; the closed row names its one live project or `N PROJECTS`; the desk chip and verb only on DESK/ALL (or where a desk grant is LIVE); project orphans with `Stop run and publish`, Remote Access ON and OFF; the credential revoke's receipt names `CREDENTIAL REVOKED` and the project. Species fix: the Disclosure trigger is the Button's `chrome` variant with no `.btn` base, so it never got the HS-202-05 44 px halo; `disclosure.css` gives the default variant the halo inside a narrow `surface` container.
- **Board 11's offset:** in the product the Settings window's top does not move after a credential revoke (fenced at 1440 and 393). The canvas harness's 58 px was not traced further.

## The criteria → their proof

| Criterion | Red on main | Green (fence) |
|---|---|---|
| Real PROJECT credential, MCP and HTTP: run, publish refused `project_delegation_required` with a receipt without a grant; with a LIVE grant each executes, its receipt naming the delegation; stop likewise | run/publish over MCP SUCCEED with no receipt (`assert False` on "refused"); over HTTP 403 `principal_right_required`, no receipt. Stop: its no-grant case needs a run the agent started, so it has no separate red on main | `test_run_is_refused_without_a_grant_and_runs_with_one_naming_the_delegation[mcp,http]`, `test_publish_is_refused_…[mcp,http]`, `test_stop_of_its_own_run_is_refused_without_the_grant_and_stops_with_it[mcp,http]` |
| Children only as R4-1 settles, each naming grant and policy; revoke mid-run refuses the next child with a receipt, run terminal; stop on another actor's run refused | new capability (no grant on main) | `test_an_agent_runs_children_each_naming_the_grant_and_the_policy`, `test_a_revoke_mid_run_refuses_the_next_child_with_its_receipt_and_ends_the_run`, `test_a_revoke_with_no_next_child_still_ends_the_run_refused_and_invents_no_child`, `test_an_agent_cannot_stop_another_agents_run_in_the_same_project`, `test_a_direct_proposal_decision_stays_refused_although_the_run_may_accept` |
| A on B nothing; outside the bound refused with the grant; mark delivered, archive, configure_steward refused in every case (R4-2) | new capability | `test_a_grant_on_project_a_does_nothing_on_project_b`, `test_grants_on_two_projects_each_authorise_their_own_project`, `test_a_granted_agent_cannot_stop_or_publish_project_b_objects_under_a_project_a_grant`, `test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[13]`, `test_mark_delivered_archive_and_configure_are_refused_for_an_agent_in_every_case` |
| Revoke, expiry, credential revoke; restart and reissue keep LIVE; the interleavings; a mutation of each check turns its fence red | new capability | `test_philo9_project_grant_lifecycle.py` (15), `test_revoke_and_expiry_move_the_code`, `test_the_owners_credential_revoke_ends_the_project_grants_first_and_a_reissue_keeps_a_live_grant`, `test_philo9_project_grant_restart.py` (a real process kill and a new process); `mutations.py` M1–M13 all RED |
| Grant and revoke owner-only, admitted, receipts; an agent refused | new capability | `test_the_grant_operations_are_owner_only_admitted_and_in_no_palette`, `test_a_malformed_grant_body_and_an_unknown_project_are_refused_with_receipts`, `test_a_revoke_with_no_live_grant_is_refused_with_its_receipt` |
| The face as ratified at 1440 and 393, incl. a LIVE grant with no credential and Remote Access OFF, fenced after each change; DESK reads DESK | no `Projects` Disclosure (test 1 times out waiting for it at 1440 and 393); `desk-agent` reads ALL (`test_a_desk_credential_reads_back_desk`: `{'desk-agent': 'ALL'}`) | `tests/e2e/test_philo9_07_project_grant_glass.py` (5 × 2 widths), `test_a_desk_credential_reads_back_desk`, `test_philo9_project_grant_face_rule.py` |

## Round three (Codex Astra r1 @7a432a29, DO-NOT-RATIFY; `checks/story-07-built-astra-r1.md`)

| Finding | Red (export of 7a432a29, `assets/story-07-proof/red_r3.sh`) | Green |
|---|---|---|
| 1. Stop compared the requester string only: a PROJECT credential named `owner-session` stopped an OWNER run over MCP and HTTP | both regressions: the impostor's stop SUCCEEDED (`success: True`) for the owner's and for the scheduler's run | `test_an_agent_named_like_the_owner_cannot_stop_the_owners_run`, `test_an_agent_named_like_the_scheduler_cannot_stop_the_schedulers_run` (MCP + HTTP each; `steward_run_owner_required` with a receipt, no stop flag); own-agent stop still succeeds (`test_stop_of_its_own_run_…`); M14 |
| 2. An archived project's LIVE grant lost its Stop row | the archived line absent at 1440 and 393 (the locator for `project-archived` times out) | `TestArchivedProjectGrant::test_archive_keeps_the_stop_and_its_receipt_on_and_off[1440,393]` (ON and OFF; Stop → the line goes, the receipt kept and read from the kernel); canvas board 12; M15 |
| 5. The model limit | — | the beat and the BACKLOG name Codex's observed result |

Under "Round three (after the two fixes)", the first `mutations.py` capture (exit 1) found M8's original text gone (the stop check moved into `_agent_started`); M8 is retired, subsumed by M14, and the rerun is 14 run, 0 missed. The first `docs_checks.sh` capture (exit 1) showed `api-reference.json` and `boundary-candidates.json` drift; both were regenerated and the rerun is `DOCS RC=0`.

The first `red_r3.sh` capture below failed the glass case on a missing word in the fence's own fallback table (`KeyError: 'archived'`), not on the face; the fence was corrected and the second capture is the red.

## Not paid / notes

- The grant lifecycle beat is written AS-BUILT by Muad'Dib's ruling (2026-09-28): `design/project-grant-beat.md`; Codex Astra checks it with the built PR.
- Round two: story 02's round two (`7119cfd9`) merged in; the captures below the heading "Merged tree" are the re-runs on the merged tree.
- Story 02's, routed to its lane by Muad'Dib (not fixed here): `tests/unit/test_philo5_the_loop_r2.py::test_every_braced_declaration_has_a_producer_here` fails on story 02's head `aeae7bd8` and passes on main `1f332bc3`.
- An agent run drafts deterministically only (the named limit): Codex Astra r1 observed `inference.invoke` refused `parent_continuation_identity_required` under an AGENT run, no engine dispatched, the draft `deterministic:no_output`; BACKLOG.
- A credential revoke ending both a desk grant and project grants shows one receipt in the footer (BACKLOG row).
- The web-unit capture's standalone `npx vitest run` reported 1 failed of 2931 while the baseline run and `npm run check` in the same capture were 2931/2931 green; its name was not printed, and a rerun alone was 323 files / 2931 passed. Unknown flake, not identified.
- A model draft's `inference.invoke` under an AGENT run was not exercised (no model on an isolated HOME; story 02's BACKLOG row stands).

## Proof

### Captured run — 2026-09-28T15:11:01Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/green.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5b164b49a251b14e48463ed4190fc59bca751bf3

```text
53 tests collected in 0.72s
........................................................................ [ 88%]
........................................................................ [ 96%]
.............................                                            [100%]
893 passed in 84.39s (0:01:24)
```

### Captured run — 2026-09-28T15:12:34Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/red_main.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5b164b49a251b14e48463ed4190fc59bca751bf3

```text
main = 1f332bc3c85a8fdfd1a0c0ba9e5a113d61d17777
FAILED tests/unit/test_philo9_project_grant_restart.py::test_a_live_project_grant_survives_a_real_restart_and_a_reissue
36 failed, 1 error in 9.18s
FAIL  tests.unit.test_philo9_project_grant_lifecycle :: collection failure
FAIL  test_a_granted_agent_cannot_stop_or_publish_project_b_objects_under_a_project_a_grant :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[decide edit_accept] :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[decide defer] :: AssertionError: {"detail":"Not Found"}
FAIL  test_run_is_refused_without_a_grant_and_runs_with_one_naming_the_delegation[mcp] :: AssertionError: the agent's call succeeded without a grant: {'run_id': 'pstrun_838aa6e138194bf58f621e30a65444b9', 'success': True}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[archive] :: AssertionError: {"detail":"Not Found"}
FAIL  test_stop_of_its_own_run_is_refused_without_the_grant_and_stops_with_it[mcp] :: AssertionError: {"detail":"Not Found"}
FAIL  test_a_grant_on_project_a_does_nothing_on_project_b :: AssertionError: {"detail":"Not Found"}
FAIL  test_publish_is_refused_without_a_grant_and_publishes_with_one[mcp] :: AssertionError: the agent's call succeeded without a grant: {'success': True, 'update': {'body_md': '## Progress\n\nNo focus items in this window.\n\n## Decisions\n\nNo decisions in this window.\n\n## Risks & Blockers\n\
FAIL  test_stop_of_its_own_run_is_refused_without_the_grant_and_stops_with_it[http] :: AssertionError: {"detail":"Not Found"}
FAIL  test_publish_is_refused_without_a_grant_and_publishes_with_one[http] :: AssertionError: {'code': 'principal_right_required', 'error': 'principal_right_required', 'missing_right': 'owner', 'principal': 'agent', ...}
FAIL  test_grants_on_two_projects_each_authorise_their_own_project :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[decide dismiss] :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[accept review] :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[delivered] :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[decide accept] :: AssertionError: {"detail":"Not Found"}
FAIL  test_run_is_refused_without_a_grant_and_runs_with_one_naming_the_delegation[http] :: AssertionError: {'code': 'principal_right_required', 'error': 'principal_right_required', 'missing_right': 'owner', 'principal': 'agent', ...}
FAIL  test_mark_delivered_archive_and_configure_are_refused_for_an_agent_in_every_case :: AssertionError: ('none', 'project.mark_update_delivered', {'code': -32005, 'data': {'code': 'MCP-005', 'tool': 'project.mark_update_delivered'}, 'message': "Tool 'project.mark_update_delivered' is not in the configured p
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[trigger] :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[unattended on] :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[suggested add] :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[github recheck] :: AssertionError: {"detail":"Not Found"}
FAIL  test_an_agent_runs_children_each_naming_the_grant_and_the_policy :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[link] :: AssertionError: {"detail":"Not Found"}
FAIL  test_every_operation_outside_the_bound_stays_refused_with_a_live_grant[resource add] :: AssertionError: {"detail":"Not Found"}
FAIL  test_a_revoke_with_no_next_child_still_ends_the_run_refused_and_invents_no_child :: AssertionError: {"detail":"Not Found"}
FAIL  test_revoke_and_expiry_move_the_code :: AssertionError: {"detail":"Not Found"}
FAIL  test_the_owners_credential_revoke_ends_the_project_grants_first_and_a_reissue_keeps_a_live_grant :: AssertionError: {"detail":"Not Found"}
FAIL  test_a_revoke_with_no_live_grant_is_refused_with_its_receipt :: AssertionError: {"detail":"Not Found"}
FAIL  test_an_agent_cannot_stop_another_agents_run_in_the_same_project :: AssertionError: {"detail":"Not Found"}
FAIL  test_a_revoke_mid_run_refuses_the_next_child_with_its_receipt_and_ends_the_run :: AssertionError: {"detail":"Not Found"}
FAIL  test_a_direct_proposal_decision_stays_refused_although_the_run_may_accept :: AssertionError: {"detail":"Not Found"}
FAIL  test_the_grant_operations_are_owner_only_admitted_and_in_no_palette :: AssertionError: {"detail":"Not Found"}
FAIL  test_a_live_project_grant_survives_a_real_restart_and_a_reissue :: AssertionError: {'detail': 'Not Found'}
FAIL  test_a_malformed_grant_body_and_an_unknown_project_are_refused_with_receipts :: AssertionError: {"detail":"Not Found"}
FAIL  test_a_desk_credential_reads_back_desk :: AssertionError: {'all-agent': 'ALL', 'desk-agent': 'ALL'}
FAIL  test_the_wire_projects_each_grant_and_lists_project_orphans_beside_desk_orphans :: AssertionError: {"detail":"Not Found"}
```

### Captured run — 2026-09-28T15:12:56Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/red_face.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5b164b49a251b14e48463ed4190fc59bca751bf3

```text
main = 1f332bc3c85a8fdfd1a0c0ba9e5a113d61d17777
FAILED tests/e2e/test_philo9_07_project_grant_glass.py::TestProjectGrantGlass::test_the_owner_revokes_a_credential_the_grant_ends_first_and_the_window_stays_put[393]
10 failed in 37.39s
FAIL  test_allow_stop_refused_and_two_projects_on_the_rendered_row[1440] :: playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 8000ms exceeded.
FAIL  test_allow_stop_refused_and_two_projects_on_the_rendered_row[393] :: playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 8000ms exceeded.
FAIL  test_an_expired_grant_reads_stopped[1440] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_an_expired_grant_reads_stopped[393] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_live_grants_with_no_credential_show_on_and_off_and_the_last_stop_keeps_its_receipt[1440] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_live_grants_with_no_credential_show_on_and_off_and_the_last_stop_keeps_its_receipt[393] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_remote_off_keeps_a_credential_with_a_live_project_grant[1440] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_remote_off_keeps_a_credential_with_a_live_project_grant[393] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_the_owner_revokes_a_credential_the_grant_ends_first_and_the_window_stays_put[1440] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_the_owner_revokes_a_credential_the_grant_ends_first_and_the_window_stays_put[393] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
```

### Captured run — 2026-09-28T15:13:53Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/red_face.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5b164b49a251b14e48463ed4190fc59bca751bf3

```text
main = 1f332bc3c85a8fdfd1a0c0ba9e5a113d61d17777
FAILED tests/e2e/test_philo9_07_project_grant_glass.py::TestProjectGrantGlass::test_the_owner_revokes_a_credential_the_grant_ends_first_and_the_window_stays_put[393]
10 failed in 36.31s
FAIL  test_allow_stop_refused_and_two_projects_on_the_rendered_row[1440] :: playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 8000ms exceeded. | ger-row").filter(has=locator(".surface-ledger-primary").filter(has_text="sweep-runner")).first.locator("button").filter(has_text="Projects").first to be visible
FAIL  test_allow_stop_refused_and_two_projects_on_the_rendered_row[393] :: playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 8000ms exceeded. | ger-row").filter(has=locator(".surface-ledger-primary").filter(has_text="sweep-runner")).first.locator("button").filter(has_text="Projects").first to be visible
FAIL  test_an_expired_grant_reads_stopped[1440] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_an_expired_grant_reads_stopped[393] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_live_grants_with_no_credential_show_on_and_off_and_the_last_stop_keeps_its_receipt[1440] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_live_grants_with_no_credential_show_on_and_off_and_the_last_stop_keeps_its_receipt[393] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_remote_off_keeps_a_credential_with_a_live_project_grant[1440] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_remote_off_keeps_a_credential_with_a_live_project_grant[393] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_the_owner_revokes_a_credential_the_grant_ends_first_and_the_window_stays_put[1440] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
FAIL  test_the_owner_revokes_a_credential_the_grant_ends_first_and_the_window_stays_put[393] :: AssertionError: HTTP 404: {'status': 404, 'payload': {'detail': 'Not Found'}}
```

### Captured run — 2026-09-28T15:14:34Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/glass.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5b164b49a251b14e48463ed4190fc59bca751bf3

```text
..........                                                               [100%]
10 passed in 73.02s (0:01:13)
1-never-1440.png
1-never-393.png
10-last-orphan-stopped-1440.png
10-last-orphan-stopped-393.png
11-credential-revoked-1440.png
11-credential-revoked-393.png
2-live-1440.png
2-live-393.png
3-live-open-1440.png
3-live-open-393.png
4-stopped-1440.png
4-stopped-393.png
5-expired-1440.png
5-expired-393.png
6-orphan-1440.png
6-orphan-393.png
7-orphan-off-1440.png
7-orphan-off-393.png
7b-off-credential-1440.png
7b-off-credential-393.png
8-refused-1440.png
8-refused-393.png
9-two-projects-1440.png
9-two-projects-393.png
```

### Captured run — 2026-09-28T15:15:53Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/mutations.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5b164b49a251b14e48463ed4190fc59bca751bf3

```text
RED (caught): M1 admission looks up any project's LIVE grant for the agent [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:293: AssertionError: {'code': 'project_delegation_required', 'error': 'The kernel refused project.publish_update: project_delegation_requir...-agent', 'actor_kind': 'agent', 'authority_basis': 'refused_at_admission', 'created_at': 1790608555.3630989, ...}, ...} | FAILED tests/unit/test_philo9_project_grant.py::test_grants_on_two_projects_each_authorise_their_own_project | 1 failed in 1.54s
RED (caught): M2 approval and the claim read the latest LIVE row, not the frozen id (G2 for G1) [holdspeak/kernel/project.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[revoke-project_delegation_revoked] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[regrant-project_delegation_revoked] | 3 failed, 1 passed in 1.17s
RED (caught): M3 no re-check at the claim [holdspeak/kernel/project_codec.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[expire-project_delegation_expired] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[regrant-project_delegation_revoked] | 3 failed in 0.86s
RED (caught): M4 approval never re-checks the agent's grant [holdspeak/kernel/project.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_admission_and_approval_refuses_the_approval[revoke-project_delegation_revoked] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_admission_and_approval_refuses_the_approval[expire-project_delegation_expired] | 2 failed in 0.69s
RED (caught): M5 the expiry is outside the hash [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant_lifecycle.py:125: AssertionError: assert 'sha256:e87df...9bf5c7aa7ef6b' == 'sha256:42b11...5dd38a93f6a93' | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_the_expiry_and_the_project_are_inside_the_hash | 1 failed in 0.54s
RED (caught): M6 a running agent run never re-checks its frozen grant [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:485: AssertionError: {'authority_basis': 'project-delegation:projdeleg_8abe98f86d6a4e7db98439a12a8d8570:sha256:6a671321e33ae3f40ecac624a459...888b1b52a86db94', 'delegator_identity': 'owner-session', 'delegator_kind': 'owner', 'name': 'project.run_steward', ...} | FAILED tests/unit/test_philo9_project_grant.py::test_a_revoke_with_no_next_child_still_ends_the_run_refused_and_invents_no_child | 1 failed in 1.37s
RED (caught): M7 a lost grant stops the run BEFORE the child is attempted (no child receipt) [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:465: AssertionError: [{'authority_basis': 'project-steward:pstrun_bdb81a4729065a1e9e30360cb501fa48:sha256:29093d74f837b5dc533bbbc8d3dfe063e...4acee31552', 'delegator_identity': 'owner-session', 'delegator_kind': 'owner', 'name': 'project.decide_proposal', ...}] | FAILED tests/unit/test_philo9_project_grant.py::test_a_revoke_mid_run_refuses_the_next_child_with_its_receipt_and_ends_the_run | 1 failed in 6.81s
RED (caught): M8 stop is not bound to the run's requester [holdspeak/kernel/project_codec.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:500: AssertionError: {'operation_id': 'op_8a9e8e6fd14245658f2571e4fc565b66', 'receipt': {'actor_identity': 'second-project-agent', 'actor_k...8c2b0b68', 'created_at': 1790608572.629554, ...}, 'run_id': 'pstrun_16fb7dbb816651e5b2a0ee38028f12fb', 'success': True} | FAILED tests/unit/test_philo9_project_grant.py::test_an_agent_cannot_stop_another_agents_run_in_the_same_project | 1 failed in 1.34s
RED (caught): M9 an agent may grant (not owner-only) [holdspeak/kernel/project_codec.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:578: AssertionError: {"error":"project_delegation_required","detail":"The kernel refused project.delegation.grant: project_delegation_required","status":403,"operation_id":"op_ed6e55342ff642088ed6c1feeaea1623","receipt":{"receipt_id":"rcpt_03ea207a091c41109d0649e46e2e2681","operation_id":"op_ed6e55342ff642088ed6c1feeaea1623","state":"refused","outcome":"project_delegation_required","result_ref":"","created_at":179060857
RED (caught): M10 the credential revoke leaves the project grants LIVE [holdspeak/web/routes/mcp_http.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:557: AssertionError: assert [] == ['Hiring loop...dger cutover'] | FAILED tests/unit/test_philo9_project_grant.py::test_the_owners_credential_revoke_ends_the_project_grants_first_and_a_reissue_keeps_a_live_grant | 1 failed in 1.42s
RED (caught): M11 the palette is reverse-mapped (DESK = ALL) [holdspeak/web/routes/mcp_http.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:607: AssertionError: {'all-agent': 'ALL', 'desk-agent': 'ALL'} | FAILED tests/unit/test_philo9_project_grant.py::test_a_desk_credential_reads_back_desk | 1 failed in 1.27s
RED (caught): M12 the projection reads the stored state (no expiry) [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant_lifecycle.py:248: AssertionError: assert ['LIVE'] == ['EXPIRED'] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_the_projection_says_what_the_kernel_would_answer | 1 failed in 0.46s
RED (caught): M13 an agent's steward child is refused (no trusted child path) [holdspeak/kernel/causation.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:399: AssertionError: {'authority_json': '{"authority_sha256": "sha256:a629d28959700d636f1d9c09b412479150ca0aa8dd0e56c889135efaa3240d55", "a...09-28T15:16:21+00:00', 'created_at': '2026-09-28T15:16:21+00:00', 'id': 'pstrun_f9c5feb3089554f7bc2549dbb3e98307', ...} | FAILED tests/unit/test_philo9_project_grant.py::test_an_agent_runs_children_each_naming_the_grant_and_the_policy | 1 failed in 1.27s
MUTATIONS: 13 run, 0 missed
```

### Captured run — 2026-09-28T15:16:22Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5b164b49a251b14e48463ed4190fc59bca751bf3

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
RESIDUAL FENCE GREEN: 240 identities match /Users/karol/dev/tools/wt-philo-9-07
OK
Documentation navigation: 2 files checked; local targets and Markdown headings resolve.
DOCS RC=0
```

### Captured run — 2026-09-28T15:16:41Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/web_unit.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5b164b49a251b14e48463ed4190fc59bca751bf3

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
⎯⎯⎯⎯⎯⎯⎯ Failed Tests 1 ⎯⎯⎯⎯⎯⎯⎯
 Test Files  1 failed | 322 passed (323)
      Tests  1 failed | 2930 passed (2931)
   Duration  58.02s (transform 42.47s, setup 45.23s, import 176.67s, tests 186.71s, environment 174.23s)
token gate: clean (11 allow-listed exceptions, all in use)
 Test Files  323 passed (323)
      Tests  2931 passed (2931)
✓ built in 4.47s
bundle gate passed (Desk JS 1334649 B; Desk CSS 323919 B; source maps 0)
baseline=0 vitest=0 check=0
```

### Merged tree (story 02 round two, `7119cfd9`, merged)

### Captured run — 2026-09-28T15:27:11Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/green.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0b6453cc6cf264b1a13cfa7f3147af8690b0c00f

```text
53 tests collected in 1.15s
........................................................................ [ 88%]
........................................................................ [ 95%]
...........................................                              [100%]
979 passed in 154.94s (0:02:34)
```

### Captured run — 2026-09-28T15:29:49Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/glass.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0b6453cc6cf264b1a13cfa7f3147af8690b0c00f

```text
..........                                                               [100%]
10 passed in 95.67s (0:01:35)
1-never-1440.png
1-never-393.png
10-last-orphan-stopped-1440.png
10-last-orphan-stopped-393.png
11-credential-revoked-1440.png
11-credential-revoked-393.png
2-live-1440.png
2-live-393.png
3-live-open-1440.png
3-live-open-393.png
4-stopped-1440.png
4-stopped-393.png
5-expired-1440.png
5-expired-393.png
6-orphan-1440.png
6-orphan-393.png
7-orphan-off-1440.png
7-orphan-off-393.png
7b-off-credential-1440.png
7b-off-credential-393.png
8-refused-1440.png
8-refused-393.png
9-two-projects-1440.png
9-two-projects-393.png
```

### Captured run — 2026-09-28T15:31:31Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/mutations.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0b6453cc6cf264b1a13cfa7f3147af8690b0c00f

```text
RED (caught): M1 admission looks up any project's LIVE grant for the agent [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:293: AssertionError: {'code': 'project_delegation_required', 'error': 'The kernel refused project.publish_update: project_delegation_requir...t-agent', 'actor_kind': 'agent', 'authority_basis': 'refused_at_admission', 'created_at': 1790609492.639384, ...}, ...} | FAILED tests/unit/test_philo9_project_grant.py::test_grants_on_two_projects_each_authorise_their_own_project | 1 failed in 1.34s
RED (caught): M2 approval and the claim read the latest LIVE row, not the frozen id (G2 for G1) [holdspeak/kernel/project.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[revoke-project_delegation_revoked] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[regrant-project_delegation_revoked] | 3 failed, 1 passed in 1.31s
RED (caught): M3 no re-check at the claim [holdspeak/kernel/project_codec.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[expire-project_delegation_expired] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[regrant-project_delegation_revoked] | 3 failed in 1.18s
RED (caught): M4 approval never re-checks the agent's grant [holdspeak/kernel/project.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_admission_and_approval_refuses_the_approval[revoke-project_delegation_revoked] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_admission_and_approval_refuses_the_approval[expire-project_delegation_expired] | 2 failed in 0.87s
RED (caught): M5 the expiry is outside the hash [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant_lifecycle.py:125: AssertionError: assert 'sha256:b69bb...d328fec7d51f9' == 'sha256:4c05c...0fbbef7018ec2' | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_the_expiry_and_the_project_are_inside_the_hash | 1 failed in 0.68s
RED (caught): M6 a running agent run never re-checks its frozen grant [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:485: AssertionError: {'authority_basis': 'project-delegation:projdeleg_33b7a2c20e754b908a4804b520bce28a:sha256:e7b60f9538c6493606c3f03af5f9...972cae4806afada', 'delegator_identity': 'owner-session', 'delegator_kind': 'owner', 'name': 'project.run_steward', ...} | FAILED tests/unit/test_philo9_project_grant.py::test_a_revoke_with_no_next_child_still_ends_the_run_refused_and_invents_no_child | 1 failed in 1.90s
RED (caught): M7 a lost grant stops the run BEFORE the child is attempted (no child receipt) [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:465: AssertionError: [{'authority_basis': 'project-steward:pstrun_b073950470e25887ba8b28c7d5cf574b:sha256:e9decccc9426837124382f9194bd36174...e168fd858f', 'delegator_identity': 'owner-session', 'delegator_kind': 'owner', 'name': 'project.decide_proposal', ...}] | FAILED tests/unit/test_philo9_project_grant.py::test_a_revoke_mid_run_refuses_the_next_child_with_its_receipt_and_ends_the_run | 1 failed in 7.53s
RED (caught): M8 stop is not bound to the run's requester [holdspeak/kernel/project_codec.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:500: AssertionError: {'operation_id': 'op_a2245dd56fcf4c4791a36a6b13ef9007', 'receipt': {'actor_identity': 'second-project-agent', 'actor_k...85a773bc', 'created_at': 1790609512.821099, ...}, 'run_id': 'pstrun_e3658e7af74b526392fb6b1fe26fbd7b', 'success': True} | FAILED tests/unit/test_philo9_project_grant.py::test_an_agent_cannot_stop_another_agents_run_in_the_same_project | 1 failed in 1.44s
RED (caught): M9 an agent may grant (not owner-only) [holdspeak/kernel/project_codec.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:578: AssertionError: {"error":"project_delegation_required","detail":"The kernel refused project.delegation.grant: project_delegation_required","status":403,"operation_id":"op_3be11c157f3a42b0b6e386fcd2b9507f","receipt":{"receipt_id":"rcpt_bec9c432408444b39efe1f27ca4071fd","operation_id":"op_3be11c157f3a42b0b6e386fcd2b9507f","state":"refused","outcome":"project_delegation_required","result_ref":"","created_at":179060951
RED (caught): M10 the credential revoke leaves the project grants LIVE [holdspeak/web/routes/mcp_http.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:557: AssertionError: assert [] == ['Hiring loop...dger cutover'] | FAILED tests/unit/test_philo9_project_grant.py::test_the_owners_credential_revoke_ends_the_project_grants_first_and_a_reissue_keeps_a_live_grant | 1 failed in 1.71s
RED (caught): M11 the palette is reverse-mapped (DESK = ALL) [holdspeak/web/routes/mcp_http.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:607: AssertionError: {'all-agent': 'ALL', 'desk-agent': 'ALL'} | FAILED tests/unit/test_philo9_project_grant.py::test_a_desk_credential_reads_back_desk | 1 failed in 1.72s
RED (caught): M12 the projection reads the stored state (no expiry) [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant_lifecycle.py:248: AssertionError: assert ['LIVE'] == ['EXPIRED'] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_the_projection_says_what_the_kernel_would_answer | 1 failed in 0.69s
RED (caught): M13 an agent's steward child is refused (no trusted child path) [holdspeak/kernel/causation.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:399: AssertionError: {'authority_json': '{"authority_sha256": "sha256:988dbfbd191c723513c1c39f203bf4a928465c9c64c4c01ecd00c03d8aab5c3c", "a...09-28T15:32:05+00:00', 'created_at': '2026-09-28T15:32:05+00:00', 'id': 'pstrun_4ba63353413c58c3b5b9470327a118f3', ...} | FAILED tests/unit/test_philo9_project_grant.py::test_an_agent_runs_children_each_naming_the_grant_and_the_policy | 1 failed in 1.53s
MUTATIONS: 13 run, 0 missed
```

### Captured run — 2026-09-28T15:32:06Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0b6453cc6cf264b1a13cfa7f3147af8690b0c00f

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
RESIDUAL FENCE GREEN: 240 identities match /Users/karol/dev/tools/wt-philo-9-07
OK
Documentation navigation: 2 files checked; local targets and Markdown headings resolve.
DOCS RC=0
```

### Captured run — 2026-09-28T15:32:32Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/web_unit.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0b6453cc6cf264b1a13cfa7f3147af8690b0c00f

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
 Test Files  323 passed (323)
      Tests  2931 passed (2931)
   Duration  31.95s (transform 15.70s, setup 28.97s, import 90.52s, tests 91.11s, environment 100.73s)
token gate: clean (11 allow-listed exceptions, all in use)
 Test Files  323 passed (323)
      Tests  2931 passed (2931)
✓ built in 4.29s
bundle gate passed (Desk JS 1334649 B; Desk CSS 323919 B; source maps 0)
baseline=0 vitest=0 check=0
```

### Captured run — 2026-09-28T15:58:18Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/red_r3.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5f7fc0817b38d04f6285da42c95dcf4b5fdd2184

```text
FAILED tests/e2e/test_philo9_07_project_grant_glass.py::TestArchivedProjectGrant::test_archive_keeps_the_stop_and_its_receipt_on_and_off[393]
4 failed in 19.46s
FAIL  test_an_agent_named_like_the_owner_cannot_stop_the_owners_run :: AssertionError: {'operation_id': 'op_5d9f193621594aa2b49e3bc65a34e5a8', 'receipt': {'actor_identity': 'owner-session', 'actor_kind': '...d810e3b', 'created_at': 1790611107.8013282, ...}, 'run_id': 'pstrun_a33a6547b2e35fb
FAIL  test_an_agent_named_like_the_scheduler_cannot_stop_the_schedulers_run :: AssertionError: {'operation_id': 'op_c3271d61c87444df85a75a51e017d7df', 'receipt': {'actor_identity': 'local-steward-conductor', 'acto...f69feaf', 'created_at': 1790611108.5167282, ...}, 'run_id': 'pstrun_ce83ac0521ec5b8
FAIL  test_archive_keeps_the_stop_and_its_receipt_on_and_off[1440] :: KeyError: 'archived'
FAIL  test_archive_keeps_the_stop_and_its_receipt_on_and_off[393] :: KeyError: 'archived'
```

### Captured run — 2026-09-28T15:58:55Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/red_r3.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5f7fc0817b38d04f6285da42c95dcf4b5fdd2184

```text
FAILED tests/e2e/test_philo9_07_project_grant_glass.py::TestArchivedProjectGrant::test_archive_keeps_the_stop_and_its_receipt_on_and_off[393]
4 failed in 27.85s
FAIL  test_an_agent_named_like_the_owner_cannot_stop_the_owners_run :: AssertionError: {'operation_id': 'op_a5f22ba19953488ab2a1392372b31a26', 'receipt': {'actor_identity': 'owner-session', 'actor_kind': '...99b8132d', 'created_at': 1790611137.094513, ...}, 'run_id': 'pstrun_81bcecc53c16505
FAIL  test_an_agent_named_like_the_scheduler_cannot_stop_the_schedulers_run :: AssertionError: {'operation_id': 'op_fa3396466a70452eb331e7df2cd5dca7', 'receipt': {'actor_identity': 'local-steward-conductor', 'acto...39a7c30', 'created_at': 1790611137.7293901, ...}, 'run_id': 'pstrun_347e1afa3c1351e
FAIL  test_archive_keeps_the_stop_and_its_receipt_on_and_off[1440] :: playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 8000ms exceeded. | er(has_text="sweep-runner")).first.locator("[data-testid=\"project-line-proj-1e05eddab5ff\"]").locator("[data-testid=\"project-archived\"]").first to be visible
FAIL  test_archive_keeps_the_stop_and_its_receipt_on_and_off[393] :: playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 8000ms exceeded. | er(has_text="sweep-runner")).first.locator("[data-testid=\"project-line-proj-d5220dd9b678\"]").locator("[data-testid=\"project-archived\"]").first to be visible
```

### Round three (after the two fixes)

### Captured run — 2026-09-28T15:59:45Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/green.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5f7fc0817b38d04f6285da42c95dcf4b5fdd2184

```text
55 tests collected in 0.72s
........................................................................ [ 88%]
........................................................................ [ 95%]
.............................................                            [100%]
981 passed in 96.05s (0:01:36)
```

### Captured run — 2026-09-28T16:01:23Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/glass.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5f7fc0817b38d04f6285da42c95dcf4b5fdd2184

```text
............                                                             [100%]
12 passed in 108.16s (0:01:48)
1-never-1440.png
1-never-393.png
10-last-orphan-stopped-1440.png
10-last-orphan-stopped-393.png
11-credential-revoked-1440.png
11-credential-revoked-393.png
12-archived-off-1440.png
12-archived-off-393.png
12-archived-on-1440.png
12-archived-on-393.png
12-archived-stopped-1440.png
12-archived-stopped-393.png
2-live-1440.png
2-live-393.png
3-live-open-1440.png
3-live-open-393.png
4-stopped-1440.png
4-stopped-393.png
5-expired-1440.png
5-expired-393.png
6-orphan-1440.png
6-orphan-393.png
7-orphan-off-1440.png
7-orphan-off-393.png
7b-off-credential-1440.png
7b-off-credential-393.png
8-refused-1440.png
8-refused-393.png
9-two-projects-1440.png
9-two-projects-393.png
```

### Captured run — 2026-09-28T16:03:17Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/mutations.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 5f7fc0817b38d04f6285da42c95dcf4b5fdd2184

```text
RED (caught): M1 admission looks up any project's LIVE grant for the agent [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:293: AssertionError: {'code': 'project_delegation_required', 'error': 'The kernel refused project.publish_update: project_delegation_requir...-agent', 'actor_kind': 'agent', 'authority_basis': 'refused_at_admission', 'created_at': 1790611398.7067578, ...}, ...} | FAILED tests/unit/test_philo9_project_grant.py::test_grants_on_two_projects_each_authorise_their_own_project | 1 failed in 1.29s
RED (caught): M2 approval and the claim read the latest LIVE row, not the frozen id (G2 for G1) [holdspeak/kernel/project.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[revoke-project_delegation_revoked] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[regrant-project_delegation_revoked] | 3 failed, 1 passed in 1.13s
RED (caught): M3 no re-check at the claim [holdspeak/kernel/project_codec.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[expire-project_delegation_expired] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[regrant-project_delegation_revoked] | 3 failed in 0.75s
RED (caught): M4 approval never re-checks the agent's grant [holdspeak/kernel/project.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_admission_and_approval_refuses_the_approval[revoke-project_delegation_revoked] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_admission_and_approval_refuses_the_approval[expire-project_delegation_expired] | 2 failed in 0.63s
RED (caught): M5 the expiry is outside the hash [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant_lifecycle.py:125: AssertionError: assert 'sha256:70a9f...f44e92099a63a' == 'sha256:90bc2...546a954a051e6' | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_the_expiry_and_the_project_are_inside_the_hash | 1 failed in 0.55s
RED (caught): M6 a running agent run never re-checks its frozen grant [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:485: AssertionError: {'authority_basis': 'project-delegation:projdeleg_1aa3be8ff93e486a89bc8a588e6ec370:sha256:29541a1fad49629cbaf41f1a0d76...7f1446bcd8af9c1', 'delegator_identity': 'owner-session', 'delegator_kind': 'owner', 'name': 'project.run_steward', ...} | FAILED tests/unit/test_philo9_project_grant.py::test_a_revoke_with_no_next_child_still_ends_the_run_refused_and_invents_no_child | 1 failed in 1.29s
RED (caught): M7 a lost grant stops the run BEFORE the child is attempted (no child receipt) [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:465: AssertionError: [{'authority_basis': 'project-steward:pstrun_ce38f0c171d35a2f8cb4d8e1bb130232:sha256:0ae27a34bf88201f8ba9f0440af81fee4...c81e70bbf3', 'delegator_identity': 'owner-session', 'delegator_kind': 'owner', 'name': 'project.decide_proposal', ...}] | FAILED tests/unit/test_philo9_project_grant.py::test_a_revoke_mid_run_refuses_the_next_child_with_its_receipt_and_ends_the_run | 1 failed in 6.73s
ERROR M8 stop is not bound to the run's requester: the original text occurs 0 times in holdspeak/kernel/project_codec.py
RED (caught): M9 an agent may grant (not owner-only) [holdspeak/kernel/project_codec.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:578: AssertionError: {"error":"project_delegation_required","detail":"The kernel refused project.delegation.grant: project_delegation_required","status":403,"operation_id":"op_ed39022f098f46e9ad7e5b69343a8feb","receipt":{"receipt_id":"rcpt_0e1b49f9bdfe4dc68e3c018434a8996f","operation_id":"op_ed39022f098f46e9ad7e5b69343a8feb","state":"refused","outcome":"project_delegation_required","result_ref":"","created_at":179061141
RED (caught): M10 the credential revoke leaves the project grants LIVE [holdspeak/web/routes/mcp_http.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:557: AssertionError: assert [] == ['Hiring loop...dger cutover'] | FAILED tests/unit/test_philo9_project_grant.py::test_the_owners_credential_revoke_ends_the_project_grants_first_and_a_reissue_keeps_a_live_grant | 1 failed in 1.22s
RED (caught): M11 the palette is reverse-mapped (DESK = ALL) [holdspeak/web/routes/mcp_http.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:607: AssertionError: {'all-agent': 'ALL', 'desk-agent': 'ALL'} | FAILED tests/unit/test_philo9_project_grant.py::test_a_desk_credential_reads_back_desk | 1 failed in 1.23s
RED (caught): M12 the projection reads the stored state (no expiry) [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant_lifecycle.py:248: AssertionError: assert ['LIVE'] == ['EXPIRED'] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_the_projection_says_what_the_kernel_would_answer | 1 failed in 0.48s
RED (caught): M13 an agent's steward child is refused (no trusted child path) [holdspeak/kernel/causation.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:399: AssertionError: {'authority_json': '{"authority_sha256": "sha256:32488cb7a14f4d8cec01db73223b6b3e5b26e9159ee1ed6d4a3a2c0285592f8f", "a...09-28T16:03:44+00:00', 'created_at': '2026-09-28T16:03:44+00:00', 'id': 'pstrun_2cee30a2c8ae58df8c9c56b7a1b7a44b', ...} | FAILED tests/unit/test_philo9_project_grant.py::test_an_agent_runs_children_each_naming_the_grant_and_the_policy | 1 failed in 1.29s
RED (caught): M14 stop compares the requester string only (an agent named owner-session stops the owner's run) [holdspeak/kernel/project_codec.py] -> FAILED tests/unit/test_philo9_project_grant.py::test_an_agent_named_like_the_owner_cannot_stop_the_owners_run | FAILED tests/unit/test_philo9_project_grant.py::test_an_agent_named_like_the_scheduler_cannot_stop_the_schedulers_run | 2 failed in 1.90s
RED (caught): M15 the face lists active projects only (an archived project's LIVE grant loses its Stop) [web/src/pages/cores/SettingsCore.tsx] -> /Users/karol/dev/tools/wt-philo-9-07/.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 8000ms exceeded. | FAILED tests/e2e/test_philo9_07_project_grant_glass.py::TestArchivedProjectGrant::test_archive_keeps_the_stop_and_its_receipt_on_and_off[1440] | 1 failed in 18.22s
MUTATIONS: 15 run, 1 missed
```

### Captured run — 2026-09-28T16:04:07Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 5f7fc0817b38d04f6285da42c95dcf4b5fdd2184

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
API reference drift: docs/generated/api-reference.json
rc=1
== philo_boundary_census.py --check
boundary census drift
rc=1
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
RESIDUAL FENCE GREEN: 240 identities match /Users/karol/dev/tools/wt-philo-9-07
OK
Documentation navigation: 2 files checked; local targets and Markdown headings resolve.
DOCS RC=1
```

### Captured run — 2026-09-28T16:04:25Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/web_unit.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5f7fc0817b38d04f6285da42c95dcf4b5fdd2184

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
 Test Files  323 passed (323)
      Tests  2931 passed (2931)
   Duration  37.06s (transform 16.93s, setup 34.92s, import 104.43s, tests 102.55s, environment 122.06s)
token gate: clean (11 allow-listed exceptions, all in use)
 Test Files  323 passed (323)
      Tests  2931 passed (2931)
✓ built in 4.48s
bundle gate passed (Desk JS 1334649 B; Desk CSS 323919 B; source maps 0)
baseline=0 vitest=0 check=0
```

### Captured run — 2026-09-28T16:08:02Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/mutations.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5f7fc0817b38d04f6285da42c95dcf4b5fdd2184

```text
RED (caught): M1 admission looks up any project's LIVE grant for the agent [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:293: AssertionError: {'code': 'project_delegation_required', 'error': 'The kernel refused project.publish_update: project_delegation_requir...t-agent', 'actor_kind': 'agent', 'authority_basis': 'refused_at_admission', 'created_at': 1790611683.944627, ...}, ...} | FAILED tests/unit/test_philo9_project_grant.py::test_grants_on_two_projects_each_authorise_their_own_project | 1 failed in 1.41s
RED (caught): M2 approval and the claim read the latest LIVE row, not the frozen id (G2 for G1) [holdspeak/kernel/project.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[revoke-project_delegation_revoked] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[regrant-project_delegation_revoked] | 3 failed, 1 passed in 0.95s
RED (caught): M3 no re-check at the claim [holdspeak/kernel/project_codec.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[expire-project_delegation_expired] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_approval_and_the_claim_refuses_the_claim[regrant-project_delegation_revoked] | 3 failed in 0.77s
RED (caught): M4 approval never re-checks the agent's grant [holdspeak/kernel/project.py] -> FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_admission_and_approval_refuses_the_approval[revoke-project_delegation_revoked] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_a_change_between_admission_and_approval_refuses_the_approval[expire-project_delegation_expired] | 2 failed in 0.63s
RED (caught): M5 the expiry is outside the hash [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant_lifecycle.py:125: AssertionError: assert 'sha256:b70ab...a5d2cf77eb148' == 'sha256:1a00d...41c66462d827e' | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_the_expiry_and_the_project_are_inside_the_hash | 1 failed in 0.47s
RED (caught): M6 a running agent run never re-checks its frozen grant [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:485: AssertionError: {'authority_basis': 'project-delegation:projdeleg_30bc58cd10db446596ace7016ee4831f:sha256:f62b6ce3121b54527438110d2cfc...45912ba7aa053f7', 'delegator_identity': 'owner-session', 'delegator_kind': 'owner', 'name': 'project.run_steward', ...} | FAILED tests/unit/test_philo9_project_grant.py::test_a_revoke_with_no_next_child_still_ends_the_run_refused_and_invents_no_child | 1 failed in 1.31s
RED (caught): M7 a lost grant stops the run BEFORE the child is attempted (no child receipt) [holdspeak/services/steward_contract.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:465: AssertionError: [{'authority_basis': 'project-steward:pstrun_360fe82fa6195c549d337ceadbe7502b:sha256:eea3071b0199a24f4115462f19a12e0c5...35ff250558', 'delegator_identity': 'owner-session', 'delegator_kind': 'owner', 'name': 'project.decide_proposal', ...}] | FAILED tests/unit/test_philo9_project_grant.py::test_a_revoke_mid_run_refuses_the_next_child_with_its_receipt_and_ends_the_run | 1 failed in 6.76s
RED (caught): M9 an agent may grant (not owner-only) [holdspeak/kernel/project_codec.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:578: AssertionError: {"error":"project_delegation_required","detail":"The kernel refused project.delegation.grant: project_delegation_required","status":403,"operation_id":"op_a57a0b3021c2418aba8fe0a366398d9d","receipt":{"receipt_id":"rcpt_4552197e2d6247c28b8833a345909170","operation_id":"op_a57a0b3021c2418aba8fe0a366398d9d","state":"refused","outcome":"project_delegation_required","result_ref":"","created_at":179061169
RED (caught): M10 the credential revoke leaves the project grants LIVE [holdspeak/web/routes/mcp_http.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:557: AssertionError: assert [] == ['Hiring loop...dger cutover'] | FAILED tests/unit/test_philo9_project_grant.py::test_the_owners_credential_revoke_ends_the_project_grants_first_and_a_reissue_keeps_a_live_grant | 1 failed in 1.23s
RED (caught): M11 the palette is reverse-mapped (DESK = ALL) [holdspeak/web/routes/mcp_http.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:607: AssertionError: {'all-agent': 'ALL', 'desk-agent': 'ALL'} | FAILED tests/unit/test_philo9_project_grant.py::test_a_desk_credential_reads_back_desk | 1 failed in 1.22s
RED (caught): M12 the projection reads the stored state (no expiry) [holdspeak/kernel/project.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant_lifecycle.py:248: AssertionError: assert ['LIVE'] == ['EXPIRED'] | FAILED tests/unit/test_philo9_project_grant_lifecycle.py::test_the_projection_says_what_the_kernel_would_answer | 1 failed in 0.52s
RED (caught): M13 an agent's steward child is refused (no trusted child path) [holdspeak/kernel/causation.py] -> /Users/karol/dev/tools/wt-philo-9-07/tests/unit/test_philo9_project_grant.py:399: AssertionError: {'authority_json': '{"authority_sha256": "sha256:1524eb481b43bad2318a1fcd86157c8e3ad3276ef95fac9fc56a8c5f90662f1e", "a...09-28T16:08:26+00:00', 'created_at': '2026-09-28T16:08:26+00:00', 'id': 'pstrun_4e5d0520e3bf5db59a84fcfa72caff76', ...} | FAILED tests/unit/test_philo9_project_grant.py::test_an_agent_runs_children_each_naming_the_grant_and_the_policy | 1 failed in 1.41s
RED (caught): M14 stop compares the requester string only (an agent named owner-session stops the owner's run) [holdspeak/kernel/project_codec.py] -> FAILED tests/unit/test_philo9_project_grant.py::test_an_agent_named_like_the_owner_cannot_stop_the_owners_run | FAILED tests/unit/test_philo9_project_grant.py::test_an_agent_named_like_the_scheduler_cannot_stop_the_schedulers_run | 2 failed in 1.93s
RED (caught): M15 the face lists active projects only (an archived project's LIVE grant loses its Stop) [web/src/pages/cores/SettingsCore.tsx] -> /Users/karol/dev/tools/wt-philo-9-07/.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 8000ms exceeded. | FAILED tests/e2e/test_philo9_07_project_grant_glass.py::TestArchivedProjectGrant::test_archive_keeps_the_stop_and_its_receipt_on_and_off[1440] | 1 failed in 20.06s
MUTATIONS: 14 run, 0 missed
```

### Captured run — 2026-09-28T16:08:51Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-proof/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5f7fc0817b38d04f6285da42c95dcf4b5fdd2184

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
RESIDUAL FENCE GREEN: 240 identities match /Users/karol/dev/tools/wt-philo-9-07
OK
Documentation navigation: 2 files checked; local targets and Markdown headings resolve.
DOCS RC=0
```

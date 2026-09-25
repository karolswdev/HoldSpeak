# Evidence - PHILO-7-02

- **Story:** PHILO-7-02 - Membership and decisions under Article XI
- **Status:** done
- **Date:** 2026-09-25
- **Branch:** `feat/philo-7-02-article-xi` from main `9800a603`; step 1 `e432fc0d`; steps 2-7 `b26494cd`; main `c806c380` (the RATIFIED grant canvas, PR #658) merged in `2f94b35e`; the face and the records in the closing commit.
- **Lane:** the Fedaykin (Opus 5.5) for Muad'Dib. Astra's check on built is owed.

## What was built

- **Nine descriptors** (`holdspeak/operations.py`, "PHILO-7-02: membership and the remaining decision operations"): `zone.file`, `zone.unfile`, `zone.members`, `kb.member.add`, `kb.member.remove`, `kb.members`, `decision.delete`, `decision.status`, `decision.supersede`, each naming its real `PrimitiveService` method and its admission; `decision.create`/`update` now declare `admitted`, `decision.read`/`list` `exempt`; `("decision", "delete")` joins `DESK_OPERATIONS`. The ONE new read: `kernel.receipt.read` (MCP tool `kernel.receipt`), bound to `services/kernel_read_service.py` over the same `kernel.read` as `GET /api/kernel/read`.
- **Transports over `invoke`:** the membership routes (`web/routes/primitives/directories.py`, `kbs.py`), decision delete/status/supersede (`primitives/decisions.py`), the MCP membership tools, `decision.supersede`, `desk.delete`/`desk.verb desk.delete kind=decisions` (`mcp/tools.py`), the `holdspeak://zones/{id}/members` resource (`mcp/resources.py`). Every bypass retired.
- **Found and repaired:** in the hub `POST /api/decisions/{id}/supersede` was answered by the lifecycle router (`web/routes/decisions.py`, included first), whose desk branch wrote both rows by hand with no contract and no `desk_changed` frame; it now calls `decision.supersede`.
- **The kernel path** (`services/desk_kernel.py`): submit under the transport's principal (payload fixed; ids a create or a supersede would mint minted first) → approve inline (OWNER) or by the kernel under a LIVE desk delegation (AGENT) → the desk executor claims (the grant re-checked AT THE CLAIM) → the service writes once → one terminal receipt (`succeeded`; `refused` naming the service's rule; `failed`). The registry's `invoke` runs it for every call its descriptor admits (`OperationRegistry._admits`; the Thought note by stored state).
- **The lifecycle beat, built as checked** (`kernel/desk.py`, `desk_codec.py`, `desk_broker.py`, `journal_atomic.py`): `check_row` (required → expired → revoked), `by_identity` (admission; the historical fallback for the code only), `by_basis` (approval and the claim; `split(":", 2)`), frozen basis `desk-delegation:<id>:<terms_sha256>`, `terms_sha256 = _hash(terms, expires_at)` imported from `services/schedule_delegation.py`; T1-T9 atomic on ONE connection under `BEGIN IMMEDIATE`, with `strict`/`decision`/`warrant_revoked`/`effect`; `create_refused_with_receipt`; the approval branch for the operation's own agent actor; T6 startup recovery (`web_server.py` startup); `KernelRefused` gains `provenance` and `receipt`. `DESK_GRANT_OPERATIONS` (15) and `DESK_KERNEL_OPERATIONS` (+2) as the beat names them.
- **The grant** (R1, R5): `kernel_desk_delegations` (one additive table, one unique partial index on LIVE per identity, one lookup index; `db/schema.py`), `delegation.grant`/`delegation.revoke` (owner-only kernel operations, their own receipts; the grant-table write inside the receipt transaction), `PUT`/`DELETE /api/settings/remote/delegations/{identity}` (edge right `AGENT_SUBMIT`), durable-first owner credential revokes (`DELETE /api/principals/agents/{identity}`, `DELETE /api/settings/remote/credentials/{id}`; `AgentCredentialStore.identity_for_id`), and the ledger fields on `GET /api/settings/remote`.
- **Refusal receipts (R2):** class 3 in `invoke` (`OperationRegistry.consequential`, `.refuse`); class 4 at the adapters (`update_args` via the registry; `mcp/tools.py` `refuse_before_invoke` for the schema refusal, non-object arguments (also `mcp/server.py`) and the palette refusal; the HTTP non-object body on the admitted decision routes); the protocol boundary leaves none.
- **The face** (the owner-ratified canvas, set A, `assets/story-02-canvas/README.md`): `web/src/pages/cores/SettingsCore.tsx` — `GRANT_WORDS` (the one constant the fences read), the grant chip (`FILING ALLOWED` success / `FILING STOPPED` idle / none when never granted), the grant verb (`Allow filing` / `Stop filing`), the refusal chip (`CANNOT ALLOW` / `CANNOT STOP` + the cause token, `data-code`), rows with no credential (`NO CREDENTIAL`, Stop only while LIVE), the caption `AGENTS · N ACTIVE CREDENTIALS`, `Revoke credential`, the visibility rule (remote OFF keeps credential rows with a LIVE grant and every grant row), the footer's CENTRE receipt Button whose face is the library `Receipt`, toggling a `SurfaceWell` `RECEIPT` under Remote access that survives its row; `settingsPrefs.tsx` `PrefStatusBar` carries it; `surface.css` `.prefs-grant-receipt` and `.prefs-module` 8 px bottom (the fence found `Issue credential` 1 px under the footer). The library CSS of PR #658 is used, not duplicated.
- **The rig:** `scripts/graph_walk.py` maps eight new operations; `decision.status` is HTTP only (`OP_HTTP_ONLY`, blocked by name); `desk.delete` carries every argument in `data`.

## Measurements (two, never one)

- **Residual identities:** 293 -> **284**; MCP 232 -> **223** (identities 1, 6, 25, 28-33); HTTP 61 -> 61 (no route builds a service: the grant routes call functions). `RESIDUAL FENCE GREEN: 284 identities`. The 9 are in the set's `paid` under `PHILO-7-02`.
- **Public MCP tools:** 228 -> **229** (`kernel.receipt`), recorded in `public_tools_added`.

## The compatibility tables (base main `9800a603` → built)

Principal cases: OWNER = the Desk's HTTP session and the loopback MCP owner; AGENT = a remote credential over `/api/mcp`; NODE and a missing principal reach these operations through NO transport (the edge gives a node `NODE_LINK` only and refuses the unauthenticated), only through a partially wired harness or a direct registry call.

| Operation(s) | Principal | Base main | Built |
|---|---|---|---|
| every ADMITTED row (decision create/update/status/supersede/delete; zone.file/unfile; kb.member.add/remove; kb.create with members or an id; kb.update with members; zone.create with an id; zone.update with parent_id; zone.delete; a Thought's note delete) | OWNER, HTTP and MCP | executes; no operation, no receipt | executes once; ONE operation + ONE terminal receipt; the envelope unchanged plus `operation_id` and `receipt` (success and refusal) |
| the same | AGENT (DESK credential), MCP | executes; no receipt | **THE ONE NAMED CHANGE (R1):** without a LIVE grant for that identity and operation — refused at admission (`desk_delegation_required`, `_revoked`, `_expired`) with a receipt, nothing written, nothing waiting; with one — executes at once with a receipt naming `desk-delegation:<id>:<sha256:…>`, `delegator_kind=owner` |
| the same | NODE (no transport) | executes | refused `declared_capability_required` (403) with a receipt (the charter's class 1). Stated because it is a refusal where main accepted, for a principal no transport produces. One harness assertion changed (`tests/unit/test_web_routes_thoughts.py`: a node's Thought-note delete, refused on main by the Thought service 422, now refused by the kernel first, 403) |
| the same | missing principal (no transport) | executes | refused `principal_required` by name, no receipt (no authenticated principal to journal); `tests/integration/test_one_place_relationships.py` now sets the owner, as the hub does |
| every EXEMPT row and every read | any | unchanged | unchanged: zero operations (fenced) |
| decision supersede, HTTP in the hub | OWNER | the lifecycle router wrote both rows by hand, no `desk_changed` frame | the contract's `decision.supersede`; the same `{decision}` 201 envelope; the two frames now fire |
| `desk.delete` (MCP) | any | `{kind, id}` | adds an optional `data` object (a Thought's note revisions); any other field refused by the contract by name. A widening |
| the membership tools, supersede, desk.delete decisions (MCP) | any | the service by hand | the declared operations; the same envelopes (`{deleted, id}` kept for unfile/remove) plus the kernel fields |
| a raw `/api/kernel/submit` of a desk operation name | AGENT | `operation_type_unregistered` refusal (the name was unknown) | `desk_operation_service_required` refusal, with a receipt |
| `GET /api/settings/remote` | OWNER | credentials without grant fields | `credentials[].delegation`, `delegations[]` (additive) |
| the Remote Access face | OWNER | caption `CREDENTIALS · N ACTIVE`; verb `Revoke`; the ledger only when ON | the ratified canvas; two vitest cases updated to the ratified words (`remoteAccess.test.tsx`) |

Not changed, recorded: an HTTP filing of a tombstoned Thought's note still answers 500 (main's `except` misses `ConflictError`); it now leaves its refusal receipt (`thought_tombstoned`). BACKLOG-worthy; not in this story's scope.

## The fences and their reds (`docs/internal/philo/phase-7/article-xi/`)

- `red-main-step1-contract.txt`: the step-1 recording fences on a `git archive` copy of main: `assert [] == ['zone.file', …]` (HTTP) and `assert [] == ['zone.file', 'zone.members', …]` (MCP): the one registry never saw these calls.
- `red-main-residual.txt`: `RESIDUAL FENCE RED: 9 problem(s)` — each a NEW residual identity on main (the nine paid).
- `red-main-behaviour.txt`: 31 behavioural fences (`tests/unit/test_philo7_article_xi.py`, `test_philo7_grant_restart.py`, and the admission fence that replaced `test_philo5_the_loop.py:618`) run on the main copy: 31 failed. `AssertionError: []` = zero operations and zero receipts; the agent's unguarded filing on main answered a membership record; the grant route answered 404; the restart fence `assert 404 == 200`; the admission fence `HTTP: one operation and one receipt per decision write`. Two fences are green on main by design (the exempt rows, the protocol boundary): their reds are mutations.
- `red-mutations.txt`: 27 kernel/service mutations and 2 face mutations, each applied, run and reverted by copy (no git verb), every one red: e.g. m1 approval by identity → `DID NOT RAISE` (F2); m2 no expiry in the hash → equal hashes (F3); m3 `split(":")` → `None == (…)` (F3); m7 no desk `validate_claim` → the claim succeeded (F6-F8); m8 raise before the receipt → `'awaiting_decision' == 'refused'` (F10); m12 `strict=False` → `'desk_delegation_revoked' == 'operation_already_terminal'` (F10e); m14 two-step T1 → `1 == 0` rows after the fault (F20); m17 an effect opening a second connection → `a second connection opened inside an atomic write` (F24); m18 the grant write committed outside the receipt transaction → `('REVOKED', …) == ('LIVE', …)` (F21b); m19 the chip from the stored column → `'LIVE' == 'EXPIRED'` (F15); m20 spec capability `owner` → `declared_capability_required` instead of `owner_principal_required` (F16); m21 the hook in `AgentCredentialStore.revoke` → `['REVOKED'] == ['LIVE']` (F14); m22 the credential removed first → `[]` (F21a); m23 an exempt row admitted; m24 every refusal consequential; m25 no class-4 receipt for non-object MCP arguments; m26 the orphan row reads the stored state → `['LIVE'] == ['EXPIRED']` (F23); m27 startup recovery skipped → `[] == [('indeterminate', …)]` (F11, the real restart); mf1 the receipt well inside the removable ledger → the well is gone with the row; mf2 the chip following `active` → a chip where none was granted.
- `red-face.txt`: the six glass fences against the face AS ON MAIN (main's `SettingsCore.tsx`, `settingsPrefs.tsx`, `surface.css`, rebuilt), over the branch's hub: every one red on its first rendered probe (no grant verb, no grant chip, no grant row without a credential).

### The lifecycle fences (`tests/unit/test_philo7_grant_lifecycle.py`, the real broker with an injected clock)

F1, F2, F3, F4, F5+F5b, F5c, F6/F7/F8 (parametrized), F9a/b/c (parametrized), F10, F10b, F10c, F10d, F10e, F11, F17, F18, F19, F20 (T1; and T3, T4, T5, T6, T7, T9, the delegation owner-only refusal — a trigger that aborts the receipt INSERT, so a two-step write is caught ended-without-receipt), F21b (past the warrant's deadline, the grant asserted separately), F24 (every connection the database hands out recorded; T4's row carries `decision='reject'`), F15 (the chip iff the kernel admits), and the raw-submission refusal.

### Through the real hub (`tests/unit/test_philo7_article_xi.py`)

Admission for every admitted row on HTTP and MCP (every alias once); the hidden effects fenced by effect (a zone delete that unfiles; `member_ids` adding and removing; `kb.create` over an id clearing memberships; a zone move by `parent_id` and by `zone.create` over an id; a Thought tombstone unfiling, HTTP and MCP); the exempt rows at zero; the AGENT path through a DESK credential issued by the real settings route, from a non-loopback host (no grant → refused; granted → executes naming the grant; revoked; expired; another identity; a stored set without the operation; `decision.delete` under the grant, R5); F16/F16b (an agent's grant/revoke → `owner_principal_required` with a receipt; unauthenticated → 401, no receipt; malformed → `invalid_arguments`); the owner's grant and revoke (one operation each; revoke with nothing LIVE → `desk_delegation_required` 409 with a receipt); refusal classes 2, 3 and 4 (every class-4 path) and the protocol boundary; the readback (HTTP and MCP answer the same receipt; another agent's read refused `principal_read_scope_required`; the read makes no operation; `kernel.receipt` in DESK, refused outside it through dispatch with no receipt); F12 (a reissue keeps the grant; the old token 401); F14 (self-revoke and TTL cleanup leave it LIVE); F21a (a fault between the revoke's commit and the credential removal: grant REVOKED `credential_revoked`, the token refused `desk_delegation_revoked`, the retry writes no second operation); F22/F23 at the API (listed with no credential; stored LIVE past expiry reads EXPIRED; the same with the switch OFF).

### The REAL restart (`tests/unit/test_philo7_grant_restart.py`)

A hub PROCESS (`MeetingWebServer` under uvicorn, isolated HOME and DB) grants G1 through the real route; SIGKILL; a desk write is left `awaiting_decision` in the same database; a NEW process boots: its startup ended that write `indeterminate` / `hub_restart_during_decision` with a receipt (F11), and a new credential for the same identity files a note under G1 (F13).

### The face, as rendered (`tests/e2e/test_philo7_02_grant_glass.py`, 1440 and 393)

Through the real hub, routes and kernel: never granted (no chip; `Allow filing`; `AGENTS`); Allow (the ALLOWED chip `data-state=success`; `Stop filing`; the foot receipt `ALLOWED`, its operation id the kernel's `delegation.grant`); Stop (STOPPED `idle`; `owner_revoked`); a refused Stop after another owner request revoked first (`CANNOT STOP` + `NO GRANT`, `data-code=desk_delegation_required`; foot `REFUSED`; the well: REFUSED, STOP FILING, NO GRANT, the identity, BY OWNER, the same operation id as the kernel's refusal; no modal); `Revoke credential` on a LIVE grant (the grant revoked first, `credential_revoked`; the ledger gone; the foot receipt owned and its well SUCCEEDED); a grant with no credential with the switch OFF (the row with `NO CREDENTIAL`, ALLOWED, Stop; a credential row without a grant hidden; Stop → the row and the ledger gone, the foot receipt owned). After each: `readable_text` (visible, in the viewport, nothing covering the centre and corners), every Button in Remote access and the footer receipt owned by `elementFromPoint` AND a real `pointermove` at the centre and four corners (the 44 px target at 393), the scroll-edge case, no text under 12 px in Remote access and the footer, no `desk writes`. Shots: `assets/story-02-shots/` (the rendered rows, both widths).

## Not done, and uncertain

- **The face was built after the owner's canvas ratification in this lane;** the owner has not seen the built face. Its shots are in `assets/story-02-shots/`.
- **`delegations[]` scope:** built as the RATIFIED README says (LIVE in storage). A mid-lane coordinator message said "LIVE-or-historical"; that contradicts board 7 and F23. One line (`services/desk_delegation.py` `views`) changes if ruled otherwise.
- The 12 px scan covers Remote access and the footer, not the whole Settings window (the canvas's whole-window scan had no Runtime/Mesh/Desk sections).
- F23's rendered orphan case with an EXPIRED stored-LIVE grant is fenced at the API (`test_f22_f23_…`) and by the face's state rule; not shot in the browser (it needs a clock past `expires_at`; the API fence waits 0.7 s).
- The stdio in-process `handle_message` (tests only; the sidecar proxies to the hub) does not write the class-4 receipt for non-object arguments; the real path (`/api/mcp`) does.
- The HS-174 palette label (a DESK credential shown as `ALL`) is inherited (BACKLOG, "PHILO-7-02 canvas follow-ups").
- Not run: the full suite (CI's job). The lane ran the scoped set (below), the web baseline and the glass rigs.
- The steps were committed as step 1 + steps 2-7 + the face, not one commit per step: the kernel seam, the grant and admission were built together (the registry's admission and class 3 share one function).

### Captured run — 2026-09-25T20:21:37Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.BmDll7ZBZ4 npm_config_cache=/Users/karol/.npm uv run pytest -q -n 8 -p no:cacheprovider tests/integration/test_hs165_mcp_walk.py tests/integration/test_one_place_relationships.py tests/integration/test_phase143_placement_adoption_matrix.py tests/integration/test_phase143_voice_resolution_adoption.py tests/integration/test_phase200_one_composition_root_processes.py tests/integration/test_phase200_working_context.py tests/integration/test_refinement_coordinator_kernel.py tests/unit/test_api_surface.py tests/unit/test_brief_mcp.py tests/unit/test_db_primitives.py tests/unit/test_design_system_guard.py tests/unit/test_desk_seed.py tests/unit/test_directory_name_uniqueness.py tests/unit/test_door_mcp.py tests/unit/test_door_read_model.py tests/unit/test_door_routes.py tests/unit/test_door_transport_parity.py tests/unit/test_event_linked_arm.py tests/unit/test_hs174_reach_wire.py tests/unit/test_kernel_effect_fence.py tests/unit/test_mcp_phase133_surface.py tests/unit/test_mcp_phase133.py tests/unit/test_mcp_registration_characterization.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_mcp_thoughts.py tests/unit/test_mcp_tools.py tests/unit/test_notes_tag_query.py tests/unit/test_phase143_production_adoption.py tests/unit/test_phase200_one_composition_root.py tests/unit/test_phase200_working_context_index.py tests/unit/test_phase200_working_context.py tests/unit/test_philo_architecture.py tests/unit/test_philo_census.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo_graph_schema.py tests/unit/test_philo5_codex_seams.py tests/unit/test_philo5_compat.py tests/unit/test_philo5_graph_op.py tests/unit/test_philo5_his_words.py tests/unit/test_philo5_loop_compat.py tests/unit/test_philo5_one_decision.py tests/unit/test_philo5_pairs.py tests/unit/test_philo5_rehearsal_capture.py tests/unit/test_philo5_rig_import_boundary.py tests/unit/test_philo5_the_loop_r2.py tests/unit/test_philo5_the_loop.py tests/unit/test_philo7_compat.py tests/unit/test_philo7_contract.py tests/unit/test_philo7_discovery.py tests/unit/test_philo7_rename_repair.py tests/unit/test_philo7_shelf_alignment.py tests/unit/test_primitive_contract.py tests/unit/test_project_mcp_palette.py tests/unit/test_refinement_context_service.py tests/unit/test_refinement_coordinator.py tests/unit/test_refinement_default_context.py tests/unit/test_refinement_thought_service.py tests/unit/test_residual_service_admission.py tests/unit/test_resourceful_service.py tests/unit/test_thought_workbench_backend.py tests/unit/test_thread_decide_always.py tests/unit/test_thread_family.py tests/unit/test_thread_people_fence.py tests/unit/test_thread_tool_gate.py tests/unit/test_thread_tool_loop.py tests/unit/test_voice_resolve.py tests/unit/test_web_routes_primitives.py tests/unit/test_web_routes_sync_primitives.py tests/unit/test_web_routes_thoughts.py tests/unit/test_philo7_rig_faithful.py tests/unit/test_philo7_membership_decisions.py tests/unit/test_philo7_article_xi.py tests/unit/test_philo7_grant_lifecycle.py tests/unit/test_philo7_grant_restart.py tests/unit/test_db.py tests/unit/test_kernel_broker.py tests/unit/test_schedule_delegations.py tests/integration/test_decision_records.py tests/integration/test_gate_threat_model.py tests/integration/test_hs174_runner_loopback.py tests/integration/test_kernel_real_hub.py tests/integration/test_principal_separation.py tests/unit/test_coder_gate.py tests/unit/test_inference_kernel.py tests/unit/test_inference_runner.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_mesh_relay_queue.py tests/unit/test_one_path_provenance.py tests/unit/test_phase143_inference_fallback_controller.py tests/unit/test_phase143_meeting_live_cutover.py tests/unit/test_session_receipts.py tests/unit/test_speech_side_door_admission.py tests/unit/test_actuator_kernel.py tests/unit/test_desktop_type_text_kernel.py tests/unit/test_external_egress_kernel.py tests/unit/test_people_store_setup_kernel.py tests/unit/test_process_input_kernel.py tests/unit/test_process_spawn_kernel.py tests/unit/test_subprocess_exec_kernel.py tests/unit/test_workbench_triage_kernel.py tests/unit/test_frontend_density_guard.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 146e085d4faec31119e434c65d6b2aa1f78b702e

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  3%]
........................................................................ [  7%]
........................................................................ [ 11%]
........................................................................ [ 14%]
........................................................................ [ 18%]
........................................................................ [ 22%]
........................................................................ [ 25%]
........................................................................ [ 29%]
........................................................................ [ 33%]
........................................................................ [ 36%]
........................................................................ [ 40%]
........................................................................ [ 44%]
........................................................................ [ 48%]
........................................................................ [ 51%]
........................................................................ [ 55%]
........................................................................ [ 59%]
........................................................................ [ 62%]
........................................................................ [ 66%]
........................................................................ [ 70%]
........................................................................ [ 73%]
........................................................................ [ 77%]
........................................................................ [ 81%]
........................................................................ [ 85%]
........................................................................ [ 88%]
........................................................................ [ 92%]
........................................................................ [ 96%]
........................................................................ [ 99%]
..                                                                       [100%]
1946 passed in 92.00s (0:01:31)
```

### Captured run — 2026-09-25T20:23:18Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.6wcr1aeYzD HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider tests/e2e/test_philo7_02_grant_glass.py tests/e2e/test_hs174_remote_settings_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5a38f4dd32a5551c4e809e75b660e2327728ebb0

```text
..........                                                               [100%]
10 passed in 48.51s
```

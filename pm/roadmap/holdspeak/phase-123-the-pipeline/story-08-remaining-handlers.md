# HS-123-08 — Remaining handlers

- **Project:** holdspeak
- **Phase:** 123
- **Status:** done
- **Depends on:** HS-123-01
- **Unblocks:** HS-123-12
- **Owner:** unassigned

## The thesis (the bar)

A small route cluster is not an exception to the application boundary. The
remaining audit contains cadence state, sync merge, actuator proposals,
mission-control actions, mesh relay, memory search, setup, gate receipts,
coder steering, delivery PR proposals, invocation cancellation, workflow/chain
execution, and profile target extension paths. Some are high-consequence or
complex even though their route count is low.

When this ships, every audited operation has one named principal-aware service
owner. Routes parse transport input, call that service, map shared HS-123-01
errors, and serialize the unchanged external response.

## Phase 122 pattern to follow

Apply the completed service pattern consistently:

1. Compose services once with the database and narrow domain collaborators. No
   service constructor or public method receives `WebContext`, FastAPI
   request/response types, or a router.
2. Every public operation takes `Principal` first. It returns a transport-
   neutral result or raises a shared `ServiceError` code; routes retain the
   established HTTP status/body mapping.
3. Move authorization, persistence, state machines, merge logic, external
   effects, execution, approvals, receipts, and provenance behind the service.
   A route must not coordinate two services to recreate a business operation.
4. Preserve current API contracts, state names, idempotency rules, and receipt
   behavior. This is an extraction, not a product-policy rewrite.

## Audited handler map

Current source line numbers are recorded below. The audit supplied earlier line
anchors; use handler and route identity rather than treating a shifted line
number as a scope change.

### Cadence — `holdspeak/web/routes/cadence.py`

Service owner: extend `CadenceService`.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 80 | `status` — `GET /status` | `CadenceService.status(principal)` | Medium — current cadence state/visibility. |
| 101 | `loops` — `GET /loops` | `CadenceService.list_loops(principal, filters)` | Medium — preserve filtering/order. |
| 109 | `brief` — `GET /brief` | `CadenceService.brief(principal)` | Medium — retain briefing projection. |
| 129 | `closeout` — `GET /closeout` | `CadenceService.closeout(principal)` | Medium — retain closeout derivation. |
| 150 | `closeout_apply` — `POST /closeout/apply` | `CadenceService.apply_closeout(principal, payload)` | High — state mutation/receipt semantics. |
| 165 | `history` — `GET /history` | `CadenceService.history(principal, filters)` | Medium — ordering and redaction. |
| 171 | `audit` — `GET /audit` | `CadenceService.audit(principal, filters)` | Medium — audit visibility/order. |
| 179 | `loop_detail` — `GET /loops/{loop_id}` | `CadenceService.get_loop(principal, loop_id)` | Medium — access/not-found behavior. |

Later cadence actuator routes (`snooze`, `kill`, `close`, `reply`, `run-now`)
are outside the supplied direct-database audit. Do not regress them; if moving
shared cadence helpers requires touching them, route them through the same
service rather than creating a parallel path.

### Sync — `holdspeak/web/routes/sync.py`

Service owner: new `SyncService`.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 477 | `api_sync_pull` — `GET /api/sync/pull` | `SyncService.pull(principal, cursor_or_state)` | **Complex** — preserve envelope, cursor, filtering, and sync state. |
| 595 | `api_sync_push` — `POST /api/sync/push` | `SyncService.push(principal, changes, cursor_or_state)` | **Complex** — retain last-write-wins conflict merge, transaction/receipt, and malformed-change failures. |

`pull` and `push` must share one merge/serialization vocabulary. Put
last-write-wins comparison and conflict recording inside `SyncService`; do not
calculate winners in the route. Add a conflicting-state service test that
asserts the existing winner, loser/conflict record, and response shape.

### Desk actuators — `holdspeak/web/routes/desk_actuators.py`

Service owner: new `ActuatorProposalService`.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 105 | `api_desk_slack_propose` — `POST /api/desk/actuators/slack/propose` | `ActuatorProposalService.propose_slack(principal, payload)` | High — target validation, proposal/provenance, no premature side effect. |
| 181 | `api_decide_desk_slack` — `POST /api/desk/actuators/slack/{proposal_id}/decision` | `ActuatorProposalService.decide_slack(principal, proposal_id, decision)` | **Complex** — approval state machine, Slack effect, receipt/failure. |
| 210 | `api_desk_webhook_propose` — `POST /api/desk/actuators/webhook/propose` | `ActuatorProposalService.propose_webhook(principal, payload)` | High — validate egress/proposal payload. |
| 268 | `api_decide_desk_webhook` — `POST /api/desk/actuators/webhook/{proposal_id}/decision` | `ActuatorProposalService.decide_webhook(principal, proposal_id, decision)` | **Complex** — approval, delivery, receipt/failure/idempotency. |
| 288 | `api_desk_github_propose` — `POST /api/desk/actuators/github/propose` | `ActuatorProposalService.propose_github(principal, payload)` | High — validate repository/action and proposal provenance. |
| 356 | `api_decide_desk_github` — `POST /api/desk/actuators/github/{proposal_id}/decision` | `ActuatorProposalService.decide_github(principal, proposal_id, decision)` | **Complex** — approval, GitHub effect, receipt/failure/idempotency. |

### Mission control — `holdspeak/web/routes/missioncontrol.py`

Service owner: `MissionControlService` (new or an explicitly named extension
of the existing domain service).

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 297 | `api_missioncontrol_rails_size` — `POST /api/missioncontrol/rails/size` | `MissionControlService.set_rails_size(principal, payload)` | Medium — validate/persist presentation/rail state. |
| 331 | `api_missioncontrol_story_propose` — `POST /api/missioncontrol/story/propose` | `MissionControlService.propose_story(principal, payload)` | High — proposal/provenance and authorization. |
| 463 | `api_missioncontrol_decision` — `POST /api/missioncontrol/proposals/{proposal_id}/decision` | `MissionControlService.decide_proposal(principal, proposal_id, decision)` | High — lifecycle guard, effect/receipt behavior. |

### Mesh — `holdspeak/web/routes/mesh.py`

Service owner: new or extended `MeshService`.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 58 | `api_mesh_inbox` — `GET /api/mesh/inbox` | `MeshService.list_inbox(principal, filters)` | Medium — relay visibility/order. |
| 146 | `api_mesh_relay_claim` — `POST /api/mesh/relay/claim` | `MeshService.claim_relay(principal, payload)` | High — atomic claim/ownership and conflict behavior. |
| 162 | `api_mesh_relay_complete` — `POST /api/mesh/relay/{job_id}/complete` | `MeshService.complete_relay(principal, job_id, payload)` | High — claimed-state guard, durable result/receipt. |
| 185 | `api_mesh_relay_fail` — `POST /api/mesh/relay/{job_id}/fail` | `MeshService.fail_relay(principal, job_id, payload)` | High — claimed-state guard, error provenance/retry state. |

### Memory — `holdspeak/web/routes/memory.py`

Service owner: extend `MemoryService`.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 26 | `search_memory` — `GET /search` | `MemoryService.search(principal, query, filters)` | Medium — preserve principal refusal, result ranking/filtering, and response shape. |

### Setup — `holdspeak/web/routes/setup.py`

Service owner: new `SetupService` with injected runtime/model-discovery
collaborators.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 29 | `api_setup_status` — `GET /api/setup/status` | `SetupService.status(principal)` | Medium — setup state projection. |
| 87 | `api_setup_runtime_test` — `POST /api/setup/runtime-test` | `SetupService.test_runtime(principal, payload)` | High — validate target, invoke runtime safely, preserve diagnostic result. |
| 102 | `api_onboarding_disposition` — `PUT /api/setup/onboarding` | `SetupService.set_onboarding_disposition(principal, payload)` | Medium — durable onboarding state. |
| 117 | `api_first_value_start` — `POST /api/setup/first-value/start` | `SetupService.start_first_value(principal, payload)` | High — create attempt/state/provenance. |
| 141 | `api_first_value_finish` — `POST /api/setup/first-value/{attempt_id}/finish` | `SetupService.finish_first_value(principal, attempt_id, payload)` | High — attempt state guard and durable completion. |

The later first-value event/runtime-options/model-discovery routes remain
existing behavior. Reuse the service seam if a shared helper is moved; do not
leave a route-owned duplicate of setup state logic.

### Gate — `holdspeak/web/routes/system/gate_routes.py`

Service owner: `GateService` (or a named extension of the existing authority/
gate boundary; it must be distinguishable from the HTTP router).

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 85 | `api_gate_propose` — `POST /api/gate/proposals` | `GateService.propose(principal, payload)` | High — proposal validation/provenance. |
| 147 | `api_gate_read` — `GET /api/gate/proposals/{proposal_id}` | `GateService.get_proposal(principal, proposal_id)` | Medium — visibility/not-found behavior. |
| 176 | `api_gate_list` — `GET /api/gate/proposals` | `GateService.list_proposals(principal, filters)` | Medium — ordering/filtering. |
| 184 | `api_gate_decide` — `POST /api/gate/proposals/{proposal_id}/decide` | `GateService.decide(principal, proposal_id, payload)` | High — decision transition, effect, receipt. |
| 230 | `api_gate_receipt` — `POST /api/gate/proposals/{proposal_id}/receipt` | `GateService.record_receipt(principal, proposal_id, payload)` | High — immutable receipt/provenance rules. |
| 252 | `api_gate_usage` — `POST /api/gate/usage` | `GateService.record_usage(principal, payload)` | Medium — authorization and audit integrity. |
| 275 | `api_session_receipt` — `GET /api/sessions/{session_key}/receipt` | `GateService.get_session_receipt(principal, session_key)` | Medium — receipt visibility. |
| 284 | `api_gate_audit` — `GET /api/gate/audit` | `GateService.audit(principal, filters)` | Medium — ordered/redacted audit projection. |

### Coder steering — `holdspeak/web/routes/system/coder_steering_routes.py`

Service owner: extend `CoderService`.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 536 | `api_coder_steering_audit` — `GET /api/coders/steering/audit` | `CoderService.steering_audit(principal, filters)` | Medium — preserve audit visibility/order. |
| 553 | `api_coder_keep_note` — `POST /api/coders/{key}/keep-note` | `CoderService.keep_note(principal, key, payload)` | High — node authorization, durable note/provenance. |

### Delivery PRs — `holdspeak/web/routes/delivery_prs.py`

Service owner: new `DeliveryPRService` or a clearly named delivery extension.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 180 | `api_delivery_pr_launch_input` — `POST /api/delivery/prs/launches/{launch_id}/input` | `DeliveryPRService.submit_launch_input(principal, launch_id, payload)` | High — launch state guard and input provenance. |
| 226 | `api_delivery_pr_draft_review` — `POST /api/delivery/prs/{source_id}/{number}/draft-review` | `DeliveryPRService.draft_review(principal, source_id, number, payload)` | **Complex** — PR retrieval, model/kernel path, draft/provenance/receipt. |
| 348 | `api_delivery_pr_propose` — `POST /api/delivery/prs/{source_id}/{number}/propose` | `DeliveryPRService.propose(principal, source_id, number, payload)` | High — proposal and PR identity validation. |
| 408 | `api_delivery_pr_decide` — `POST /api/delivery/prs/proposals/{proposal_id}/decide` | `DeliveryPRService.decide(principal, proposal_id, payload)` | High — approval/effect/receipt semantics. |

### Invocations — `holdspeak/web/routes/primitives/invocations.py`

Service owner: extend `PrimitiveService` or add `InvocationService` if
cancellation/runtime collaborators make it a distinct boundary.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 45 | `api_list_invocations` — `GET /api/invocations` | `InvocationService.list(principal, filters)` | Medium — visibility/order. |
| 54 | `api_get_invocation` — `GET /api/invocations/{invocation_id}` | `InvocationService.get(principal, invocation_id)` | Medium — access/not-found. |
| 65 | `api_cancel_invocation` — `POST /api/invocations/{invocation_id}/cancel` | `InvocationService.cancel(principal, invocation_id, payload)` | High — runtime cancel state and receipt/failure behavior. |

### Chain and workflow runs — `holdspeak/web/routes/primitives/chains.py`, `workflows.py`

Service owner: extend `PrimitiveService` or use named `ChainService` and
`WorkflowService`; do not leave orchestration in the route.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| `chains.py:101` | `api_run_chain` — `POST /api/chains/{chain_id}/run` | `ChainService.run(principal, chain_id, payload)` | **Complex** — authorization, graph/step execution, invocation persistence, receipts/errors. |
| `workflows.py:104` | `api_run_workflow` — `POST /api/workflows/{workflow_id}/run` | `WorkflowService.run(principal, workflow_id, payload)` | **Complex** — authorization, graph execution, invocation persistence, receipts/errors. |

### Profile extensions — `holdspeak/web/routes/primitives/profiles.py`

Service owner: extend existing `ProfileService`.

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 131 | `api_list_inference_targets` — `GET /api/inference-targets` | `ProfileService.list_inference_targets(principal)` | Medium — target visibility and secret-safe projection. |
| 138 | `api_probe_target` — `POST /api/inference-targets/{target_id}/probe` | `ProfileService.probe_inference_target(principal, target_id, payload)` | High — access, controlled runtime probe, diagnostic redaction. |

## Implementation sequence

1. Read each full route module and trace its current database, runtime,
   inference, actuator, gate, and receipt collaborators before moving logic.
2. Introduce the named services above with explicit principal methods. Reuse an
   existing service only when the operations share a cohesive domain and
   collaborators; name the public methods regardless.
3. Extract complex paths as indivisible service operations: sync pull/push,
   actuator decisions, relay claim/complete/fail, gate decisions/receipts,
   PR drafting, and chain/workflow runs. Do not leave preflight, merge, or
   external side effects in a route.
4. Preserve error mapping at the adapter edge using HS-123-01 shared service
   errors. Wire all services at the application composition root.
5. Add direct service tests for authorization/denial, invalid input, not-found
   or conflict, state transitions, duplicate/idempotent actions, external
   failure, and exact receipt/provenance behavior; retain route contract tests.

## Acceptance criteria

- [ ] Every handler in every table has a named service owner, explicit
      `Principal` parameter, and a route adapter that invokes that owner.
- [ ] `SyncService.pull`/`push` retain last-write-wins merge behavior; a
      conflicting-state test proves the winning result, conflict/loser record,
      and response shape.
- [ ] Actuator, mission-control, mesh, gate, delivery, invocation, and setup
      mutations retain their authorization, state guards, idempotency, external
      effect, provenance, and receipt/failure semantics.
- [ ] Chain/workflow run endpoints preserve execution, authorization,
      invocation persistence, and receipt behavior through service calls.
- [ ] Memory search and profile target/probe reads preserve access control and
      redact credentials/diagnostic secrets.
- [ ] No affected handler accesses the database directly or implements domain
      state/merge/execution logic. Services import neither routes, FastAPI, nor
      `WebContext`.
- [ ] Focused tests and `uv run pytest -q` pass.

## Builder verification

```bash
rg -n "class (CadenceService|SyncService|ActuatorProposalService|MissionControlService|MeshService|SetupService|GateService|DeliveryPRService|InvocationService)|def (pull|push|run|probe_inference_target|claim_relay|decide|record_receipt)" holdspeak/services
! rg -n "get_database\(|ctx\.get_database" holdspeak/web/routes/cadence.py holdspeak/web/routes/sync.py holdspeak/web/routes/desk_actuators.py holdspeak/web/routes/missioncontrol.py holdspeak/web/routes/mesh.py holdspeak/web/routes/memory.py holdspeak/web/routes/setup.py holdspeak/web/routes/system/gate_routes.py holdspeak/web/routes/system/coder_steering_routes.py holdspeak/web/routes/delivery_prs.py holdspeak/web/routes/primitives/invocations.py holdspeak/web/routes/primitives/chains.py holdspeak/web/routes/primitives/workflows.py holdspeak/web/routes/primitives/profiles.py
! rg -n "holdspeak\.web\.routes|WebContext|fastapi" holdspeak/services/*service.py
uv run pytest -q
```

The final broad import grep may surface pre-existing services outside this
story. If so, run it against the service modules changed by this story and
record unrelated failures separately rather than weakening this story's rule.

## Files in scope

- `holdspeak/services/cadence_service.py`
- New: `holdspeak/services/sync_service.py`
- New: `holdspeak/services/actuator_proposal_service.py`
- New or extended: `mission_control_service.py`, `mesh_service.py`,
  `setup_service.py`, `gate_service.py`, `delivery_pr_service.py`, and
  `invocation_service.py`
- `holdspeak/services/coder_service.py`
- `holdspeak/services/profile_service.py`
- `holdspeak/services/primitive_service.py` and/or named chain/workflow
  services
- Affected route modules listed in the handler tables
- Application composition wiring and related service, route, merge, execution,
  receipt, and integration tests

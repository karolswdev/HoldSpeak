# HS-143-09 — Tool Capability Foundation and Safe Routing

**Status:** executable research plan for the already-ruled contract  
**Scope boundary:** Story 09 only. This plan does not adopt Agent, Recipe, Workbench, Sequence, Workflow, or owner-MCP execution; those remain Story 10/11 work. A model is never made an owner principal or a route controller.

## 1. Obligation register

This register records **42 binding obligations**. “New” means Story 09 must supply the missing executable authority; “compose” means reuse an existing Phase-143 primitive without weakening its law.

| # | Source | Binding obligation | Story-09 implementation consequence |
| ---: | --- | --- | --- |
| 1 | S09 acceptance 1; catalog §Turn capability authority | “Fallback cannot expand palette, scope, budgets, policy, or egress.” | Freeze one private lease before any model step. Every step/fallback uses its lease ID/hash and the frozen route/operation plan; no current assignment, policy, registry, or configuration read may broaden it. |
| 2 | S09 acceptance 2; catalog §§309–315, 370–374 | “Receipted effects are adopted; unknown effect completion never falls back.” | Bind a durable effect-child/receipt reference to the ToolCall and adopt it idempotently. An unreceipted post-dispatch effect is `effect_indeterminate`/terminal, not retry or fallback. |
| 3 | S09 acceptance 3; architecture §Tool-bearing fallback | “Tool service outage is a typed result, not automatically a model failure.” | Preserve a typed `tool_unavailable_or_stale` result and make model advance contingent on the frozen table, not a blanket provider failure mapping. |
| 4 | S09 acceptance 4; catalog §§411–416; architecture kill criterion 6 | Required tools refuse before dispatch when no qualified profile exists. | Assignment/save compatibility and route preflight must require the exact qualified deployment manifest plus executable foundation. Refusal creates zero model/provider/tool child. |
| 5 | S09 acceptance 5; catalog §§340–345 | “Every model step and tool call is separately admitted and receipted.” | A model step is a new exact request plan and `InferenceRunner` child; each ToolCall is an independently Broker-admitted child. No adapter request loop or tool execution exists under another child receipt. |
| 6 | catalog §§202–239 | Capability descriptors come from the same canonical application operations as MCP, but materialize an authority-specific `MODEL_TURN` projection. | Introduce a server-side capability projection/registry adapter over canonical descriptors. The model sees a deterministic small subset only; it never receives the MCP sidecar/token, full catalog, generic `list_tools`/`call_tool`, credentials, Settings/People/permission mutation/arbitrary Desk CRUD, or a capability outside the lease. |
| 7 | catalog §§241–254 | Ask/Add & ask next authorize evidence reads and candidate builders, not mutations; YOLO immediate effects still need exact typed owner intent. | Lease classes/effect modes are closed. `execute_if_policy_admits` requires an exact owner-intent receipt covering effect class/target/scope; the application service/Broker, not model prose, decides admission. Permission/grant mutation and approval are structurally ineligible. |
| 8 | catalog §§264–275 | `TurnCapabilityLease@1` is unexportable and server verified; provider gets only selected names/descriptions/recursively closed schemas. | Persist normalized canonical terms, terms hash, nonce privately in `turn_capability_leases`; expose a separately constructed provider tool dialect that omits lease/nonce/owner/policy/MCP data. Restart validates persisted terms/hash and named-refuses missing/corrupt/mismatched terms; never rebuilds from current state. |
| 9 | catalog §§277–299 | The lease binds listed identity/revision/intent/policy/capability/scope/data/placement/egress/budget/deadline terms. | Validate a closed `TurnCapabilityLease@1` canonical payload before insert. Require exact `capability_id`, revision, descriptor/schema hashes, service operation, class/mode, scope/data/placement/egress and every max/budget/deadline field; do not store open capability blobs. |
| 10 | catalog §§301–307 | Bootstrap Thought cap: at most 12 definitions, 4 provider steps, 6 calls, 1 effect proposal, 2 parallel commutative reads, 32 KiB/result, 64 KiB aggregate bytes, 8K aggregate tokens, 30 seconds; typed operations may reduce only. | Make these server maximums, validated against the frozen typed-operation bounds. Calls cannot mint model turns, capabilities, leases, or budget. |
| 11 | catalog §§309–320 | Verify liveness/epoch/identity/membership/revision/`MODEL_TURN`/closed arguments/hash/scope/budget/policy before Broker admission. Stable `(turn_id, provider_tool_call_id, capability_revision, canonical_args_sha256)` replays; same call ID changed capability/arguments refuses. | Use a durable unique replay key and canonical JSON/hash. Validate native calls before any Broker child. Capability search, if later added, may return capped metadata but cannot expand this lease; selection requires a new turn/lease. |
| 12 | catalog §§322–331 | A single transaction/CAS reserves ordinals, call slots, worst-case call/aggregate bytes/tokens/effects and Stop fence before Broker child admission; unknown completion keeps a reservation. | ToolTurn reservation is the budget authority. Settle only from immutable child receipts; oversized result is a typed refusal/result, never truncation. Insert parallel results into the next model request by provider-call/tool-call ordinal, never completion time. |
| 13 | catalog §§333–345 | `ToolTurnController` is server-owned; drivers translate exactly one frozen request and return exactly one structured model output/candidate/tool-call candidate. | New controller owns the multi-step state machine. It composes `InferenceFallbackController` + `InferenceRunner`; it does not construct engines, issue provider requests, or let drivers/adapters/MCP loop. Tool result is capped, hashed, persisted and treated as untrusted before a later model child. |
| 14 | catalog §§347–359 | Durable hub-local evidence has CapabilityLease, ToolTurn, ModelStep and ToolCall shape. | Add private immutable/carefully fenced ledgers whose rows carry the listed IDs/hashes/states/receipts/results, plus an effect-child binding if needed to make the Story acceptance’s explicit effect ledger reconstructible (see ORCH-CALL 2). |
| 15 | catalog §§361–375 | Closed progression and one terminal winner; malformed/unknown/budget/deadline/refusal/unavailable are typed, no hidden retry. Stop fences before best-effort cancellation. Crash/restart reconciles receipts but no automatic model egress without proved replay safety. Sync has zero execution. | Implement legal transitions and atomic terminal election. Reuse controller Stop semantics and sync deny-lists; treat unreceipted model/tool/effect boundary as indeterminate. |
| 16 | catalog §§378–380 | HTTP/MCP/Desk use one controller application method; MODEL_TURN cannot see owner resources. | Keep an internal service API as the authority seam. Do not add an owner-MCP token/catalog path in this story. Future transport adapters call it rather than duplicate state machines. |
| 17 | catalog §§411–421 | Optional non-qualified deployment runs frozen with palette zero and exact “Answering from the Note and attached context only.” Required capability gets “Use an AI with tool use”; unavailable/denied/stale/exhausted is typed and may continue only when schema/receipt names the limitation. | Distinguish optional zero-palette model turn from required-tool pre-dispatch refusal. Produce receipt/projection facts for later UI; do not silently retarget a deployment. |
| 18 | architecture §§199–210 | Tool-bearing structural compatibility requires executable foundation **and an exact qualified deployment manifest**; offline evaluation alone is insufficient. | Extend `ModelProfileRevision.capability_manifest` validation/projection and assignment incompatibility with explicit tool qualification evidence, bound through the existing deployment capability hash. Legacy v1 profiles stay incompatible. |
| 19 | architecture §§228–296 | Route plan freezes ordered deployments/boundary/policy content-free; every later tool model step gets a newly exact private request plan from immutable material. | Tool parent freezes one route chain at admission; every step freezes its own `OperationAdmittedRouteRequestPlan@1` from the same route plus prior canonical, capped tool results. No post-failure material reread, summary, truncation, or retarget. |
| 20 | architecture §§298–322 | Retry/fallback uses frozen policy/budgets and new children; policy cannot broaden tool/effect authority. | Reuse `InferenceFallbackController` reservations per model step and retain its token/cost/attempt law. Tool lease budgets are separate and must be included in route evidence rather than current controller’s deliberate `tool_budget_evidence_missing` refusal. |
| 21 | architecture disposition table (rows `invalid_tool_call`, `tool_unavailable_or_stale`, effect/unknown/permission/Stop) | Invalid native tool call can take bounded corrective model step and only then a tool-qualified fallback; service outage is not model-repaired by default; permission/policy/owner cancel/deadline/unknown/effect indeterminate never fall back. | Add an explicit tool-turn disposition classifier/bridge, not a catch-all mapping to `provider_permanent`. Fallback filter requires every candidate to qualify for the frozen lease palette/dialect. |
| 22 | architecture §§342–345 | Boundary crossing needs saved visible chain and receipt names attempts/skips/actual egress. Local is not a waiver. | Pass existing frozen route boundary evidence into every model-step route receipt; tool-child egress/placement must be narrower/equal to its capability lease. |
| 23 | architecture §§347–363 | A malformed native call may correct/fallback only to another tool-qualified model; read-only typed unavailable may feed same/fallback model in frozen lease/budget; receipted effect adopts; Stop/expiry/permission/approval/unknown terminalizes; parallel ordering survives fallback. | Part B’s exact fallback table implementation and integration proofs. |
| 24 | architecture §§364–403 | `InferenceFallbackController` remains above `InferenceRunner`, reservation is required before primary/retry/dialect child, and controller never invokes a provider. | ToolTurn delegates physical attempts through the existing route controller/runtime bridge; do not duplicate or bypass physical invocation. |
| 25 | architecture §§424–428 | DTOs/request bodies recursively closed/versioned; stable request IDs/payload hashes; replays return immutable effect evidence; owner resources absent from MODEL_TURN. | Use narrow typed request/result objects and idempotency command ledgers. No public strings become controller authority. |
| 26 | architecture kill criteria 2–7, 10–12 | No hidden adapter retry/fallback, Runner bypass, unknown/effectful advance, unqualified required-tool selection, browser law, transport divergence, or unexplainable receipt. | Add static/behavioral censuses and receipts as focused proofs; use service/controller policy only. |
| 27 | architecture adversarial matrix §§564–591 | Cover malformed correction, qualified fallback, outage, receipt adoption, unknown effect, permission denial and crash/Stop/restart parity. | Required test matrix in slices A5/B4 below. |
| 28 | S09 test plan | Unit: confusables/schema drift/expiry-revocation/palette escalation; integration: model/tool/effect crashes, Stop races, adoption; manual: exact tools/effect/model-fallback disclosures. | These are non-negotiable proof families, not aspirational UI work. |
| 29 | S09 note | Part B cannot advertise or execute tools until Part A controller/service/ledger tests pass. | A hard implementation checkpoint: B commits only after named A test gate succeeds and it remains a prerequisite test group in B runs. |
| 30 | S09 out of scope | Owner MCP tokens/catalogs and route-controller ownership of tool calls are excluded. | No owner transport credentials/catal​og APIs; `InferenceFallbackController` keeps model attempt authority only, while `ToolTurnController` owns model/tool turn composition. |
| 31 | catalog §§136–154 | Deployment reports tool qualification separately: `structured_tool_use`, `qualified_palette`, eval revision, dialect; no executable promise before the Foundation and real qualification. | Qualified-manifest shape must carry these immutable facts and route code must require `qualified`, a positive sufficient palette, and exact deployment binding; no claim string alone is enough. |
| 32 | catalog §§407–409 | Receipt names exact human tool operations/source-result receipts and distinguishes proposed from executed effects. | Persist safe display labels/provenance references in owner projection, but provider dialect and lease JSON remain private. |
| 33 | catalog §418–421 | Tool unavailable/denied/stale/exhausted returns typed result; a limited final answer only if its schema and receipt explicitly name limitation. | Define typed result schema and final-result validator before permitting continuation; otherwise return governed retryable/owner-terminal/indeterminate. |
| 34 | catalog §§425–449 | Evaluation must prove no-tool, confusable, schemas, grounding, replay, result injection, effect separation, cardinality, budgets/races/tamper/restart/transport parity. | Unit and integration fixtures cover the Story subset; model-eval publication itself is not invented here, but exact manifest admission is fail-closed. |
| 35 | architecture §234–236 | Long-lived tool parent route freezes at parent admission, later step plan freezes from immutable child material. | Use the Story-08 parent-route bundle and refusal seam rather than inventing a second parent-routing authority. |
| 36 | architecture §270–274 | Post-admission tokenizer/template/serialization/context/deployment drift is integrity refusal, not fallback. | Reconstruct each step plan/lease/hash before dispatch; route only frozen deployment revisions. |
| 37 | catalog §329 | Oversized result never silently truncates or consumes unreserved budget. | A strict size checker refuses the result or returns named typed limitation before persistence/model replan. |
| 38 | catalog §306 | A platform ceiling increase is a reviewed policy revision, never a model request. | The controller validates maximums; provider-native request cannot change them. |
| 39 | catalog §318 | Capability discovery cannot expand active lease. | No dynamic `tools=` expansion or catalog rediscovery loop. |
| 40 | architecture §501 | No fallback copy/claim before durable reservation. | Receipt/progress source is durable ToolTurn/route reservation, not driver events. |
| 41 | architecture §§387–390 | Crash with unreceipted physical call is indeterminate and never blind-replayed; restart cannot build from current state. | Reconciliation reads durable children/receipts and canonical hashes only. |
| 42 | catalog §374–375; architecture kill criterion 11 | Sync never runs/resumes/Stops/reconciles a hub-local tool turn. | Mark every new authority table hostile to sync and prove zero egress in sync fixtures. |

### Acceptance-criterion proof map

| Story acceptance criterion | Primary proof(s) |
| --- | --- |
| Palette/scope/budget/policy/egress never expands | A2 lease canonicalization and A3 atomic reservation tests; B2 frozen route + qualified-fallback tests; tampered/escalated term reconstruction tests. |
| Receipted effects adopt; unknown effect never falls back | A4 Broker-child/effect mapping and restart-adoption tests; B4 crash-after-effect-receipt and unknown-effect completion integration fixtures. |
| Tool outage is typed, not automatic model failure | A4 typed ToolCall result taxonomy; B3/B4 same-model limited answer and no automatic fallback fixture. |
| Required tools refuse before dispatch without qualified profile | B1 exact manifest compatibility/preflight tests assert zero Runner/provider/tool child. |
| Separate model/tool admission and receipt | A4 child ledger/replay/cardinality tests and B2 per-step `InferenceRunner` child/ToolCall Broker child receipt tests. |

## 2. Current-tree inventory

### 2.1 What actually exists today

There is **no native model tool-call loop in the current product tree**. The only provider calls use text/structured-output parameters and neither pass `tools=` nor consume provider `tool_calls`/`function_call` output:

| Surface | Reality and locations | Story-09 disposition |
| --- | --- | --- |
| Meeting Intel / generic persona engine | `holdspeak/intel/engine.py:273-283` local `Llama.create_chat_completion`; `:293-334` OpenAI-compatible request; streaming twins `:353-421`. Requests have messages/temperature/token fields only. `run_prompt` at `:423-459` is text-only. | Reusable physical model waist only. Do **not** add a provider loop here; a later dialect adapter receives one frozen ToolTurn model-step request and returns one structured candidate. |
| Canonical model adapter | `holdspeak/kernel/prompt_adapter.py:7-27` calls exactly one `engine.run_prompt`, emits text/provider/model. | Reusable pattern for one physical child, but insufficient as a tool adapter because it cannot carry/parse a native tool candidate. New adapter contract needed in Part B. |
| Dictation OpenAI-compatible provider | `holdspeak/plugins/dictation/runtime_openai_compatible.py:100-172` classify and `:174-212` rewrite issue plain chat completion requests. | No tool use; retain as separately routed Story-08 adopter. No Story-09 adoption. |
| Recipe/Agent model execution | `holdspeak/services/recipe_service.py:68-124` constructs only prompt payloads and invokes `CanonicalPromptAdapter`; the record has a persisted `tools: list[str]` field at `holdspeak/db/models/knowledge.py:94-115`/`holdspeak/db/models/__init__.py:644-665`, but `RecipeService._recipe_fields` only round-trips it (`recipe_service.py:175-178`). No execution path reads it to call a model/provider tool. | Explicitly **Story 10**. Do not wire stored recipe tools to the new controller here. |
| Workbench/Agent/Workflow/Sequence | They remain legacy/v1 or their own routed parents; the Phase delivery map assigns them to Story 10. `story-10-agents-workbenches-recipes-adoption.md:18-22` says tool-bearing steps are owned by Story 09 but their adoption stays Story 10. | No surface migration in Story 09. Part B supplies the reusable controller and qualification route that Story 10 will call. |
| Owner MCP catalog | `holdspeak/mcp/tools.py` and `holdspeak/mcp/families/*` expose owner transport tools; kernel runtime registers `ToolCallCodec` at `holdspeak/kernel/runtime.py:57,87`. `holdspeak/kernel/tool_call.py:23-129` is a redacted owner/agent gate proposal hold, not a model-turn tool executor. | Descriptor source/semantic precedent only. The model must never receive this catalog/token/generic authority. |
| Existing route law | `holdspeak/services/inference_assignment_service.py:1577-1613` deliberately returns `structured_tools_unsupported` (`:1593-1596`); `holdspeak/services/inference_route_plan_service.py:1320-1335` applies it during frozen-route construction. | This is the intentional fail-closed seam Story 09 replaces with exact qualification, not an omission to bypass. |

### 2.2 Reuse map: Story 05–08 primitives

| Existing primitive | Locations | What Story 09 composes, unchanged |
| --- | --- | --- |
| Frozen content-free route and exact private request plan | `holdspeak/services/inference_route_plan_service.py:807-835` (one-shot freeze), `:1260-1385` (reconstruct exact profile/binding/deployment and preflight); schema `holdspeak/db/schema.py:2527-2692`. | Freeze parent route once; derive one exact operation request plan per model step. Keep current assignment/profile/config out of execution/restart. |
| `InferenceFallbackController` + routed runtime bridge | `holdspeak/services/inference_fallback_controller.py:40-158` start, `:174-390` reserve and existing refusal of missing tool-budget evidence at `:318-319`, `:2025-2066` `RoutedAttemptRuntime`; schema `db/schema.py:2771-2939`. | Keep the sole model physical-attempt/Stop/deadline/receipt authority above `InferenceRunner`. Each tool model step composes it; it never owns a tool call. |
| Physical provider waist | `holdspeak/kernel/inference_runner.py:62-75` request/outcome/runner and its routed attempt runtime injection; `holdspeak/intel/engine.py:305-328` explicitly has one physical cloud request per admitted child. | Every model physical attempt stays a separately admitted `inference.invoke@1` child with controller reservation. |
| Service-owned adoption/evidence | `holdspeak/services/inference_adoption_service.py` is the established pattern for private immutable material/evidence/result adoption; tables at `db/schema.py:2694-2769`. | Model-step tool material/result sources should follow its freeze/reconstruct/private-storage conventions rather than accept caller hashes. |
| Parent route bundles and pre-route refusal | `holdspeak/services/inference_parent_route_bundle_service.py:100-192` parent/refusal seam; `:194-259` atomic bundle start; `:859-1245` Stop handoff; tables from `db/schema.py:2993`. | Use one parent/bundle and its Stop/refusal recording seam for an adopted tool turn; do not create another parent controller. |
| Service-only route policy and refusal recording from Story 08 | `holdspeak/services/inference_parent_route_bundle_service.py:136-192` and parent/bundle integrity checks; `holdspeak/services/inference_parent_route_bundle_service.py:405-428` architecture-defined application boundary; Story-08 service policy tests in `tests/unit/test_phase143_meeting_route_primitives.py:413-681`. | Tool turns receive a dedicated service policy/evidence provider and record a named pre-route refusal, rather than inheriting owner global/group policy or hiding a failed freeze. |
| Parent Stop / terminal fencing | `InferenceParentRouteBundleService.fence_cancel` around `:859-991` and `request_stop_handoff` around `:992-1245`; `InferenceFallbackController` reservation fence at `:217-240`, `:1247-1255`. | ToolTurn reservation joins this same transaction/CAS boundary before tool Broker admission; physical cancellation remains best effort after durable fence. |
| Additive schema/reconcile precedent | `holdspeak/db/reconcile.py:241-323` is the parent-kind CHECK rebuild precedent; `:326-439` applies additive schema and rebuild before canonical DDL. Parent kind vocabulary is at `holdspeak/db/schema.py:2970-2991`. | Add new tables additively. If `tool.turn` needs a `kernel_parent_runs.kind` value, use a semantic DDL rebuild like `_rebuild_kernel_parent_runs_for_kind_drift`, with row-loss/idempotency/trigger proof; SQLite cannot `ALTER` the CHECK. |

### 2.3 Genuinely new authority and schema work

The current route attempt tables reserve a `tool_call_budget` field but intentionally reject nonzero tool budget evidence (`inference_fallback_controller.py:318-319`), and have no lease/ToolTurn/model-step/tool-call/effect authority. Story 09 therefore needs the following **new** private schema family, all immutable or terminal-fenced and all sync-refused:

1. `turn_capability_leases` — `lease_id`, canonical normalized terms JSON, terms SHA-256, nonce/epoch private material, created/expiry/state/revocation facts. The canonical terms include the complete ruled lease shape.
2. `tool_turns` — `turn_id`, parent operation/bundle and frozen route identity/hash, lease identity/hash, frozen budgets, state/revision/terminal code/final result/Stop provenance/deadlines. It is the cross-boundary terminal-election and reservation authority.
3. `tool_turn_model_steps` — turn + ordinal, derived operation request plan/hash, route execution/attempt references, lease hash, state, child receipt/result hash and canonical request-result material references. It proves new exact planning for each step.
4. `tool_turn_tool_calls` — turn + tool ordinal + provider-call ordinal/ID, capability revision, lease hash, canonical args hash, reservation amounts/state, Broker child/receipt/result hashes, typed disposition, deterministic replay uniqueness.
5. `tool_turn_effect_children` — only if the effect is not safely reconstructible as a closed subset of `tool_turn_tool_calls`; binds a ToolCall to its Broker effect/proposal child, policy/owner-intent receipt reference, disposition, adopted immutable receipt and result hash. See [ORCH-CALL 2].
6. Immutable command/transition rows (or one closed event/command family) for start/reserve/model-step/tool-call/settle/stop/reconcile, analogous to `inference_route_execution_commands`/`transitions`; no public payload can mint their authority.
7. A closed `tool_qualification` member in the **existing** `ModelProfileRevision.capability_manifest`, bound to the already checked exact deployment capability hash. It must encode at least the ruled `structured_tool_use`, `qualified_palette`, `tool_eval_revision`, and `native_tool_dialect`, plus a manifest version/hash. Legacy-v1 manifests remain zero/unqualified. This changes the current narrow `{revision, sha256, claims}` validation at `holdspeak/services/model_profile_service.py:1016-1061`; it is an additive representation migration and must preserve old profile rows as unqualified rather than invent qualification.
8. If the adopted parent gets a distinct `tool.turn` kind, the `kernel_parent_runs.kind` CHECK must be widened through the reconcile rebuild above. This is not an ordinary additive column change.
9. Canonical DDL snapshot update: `tests/fixtures/db_schema_canonical.txt`, guarded by `tests/unit/test_db.py:1731-1758`, plus fresh/upgraded/reconcile/sync tests.

No new owner-MCP credential/catalog table belongs here. No change makes the browser a source of tool qualifications, lease terms, or fallback law.

## 3. Part A — Tool Capability Foundation slices

### A1. Closed capability projection and qualified-manifest gate

**Implement**

- Add an internal, composition-owned registry adapter that derives `MODEL_TURN` capability projections from canonical application operation descriptors. It yields only deterministic candidates with recursively closed argument schemas and safe human names.
- Add closed types/validators for `TurnCapabilityLease@1`, capability class/effect mode, scope/egress/placement/data-class terms, tool qualification manifest, and provider-native tool candidate/result envelopes.
- Extend profile-manifest parsing and `InferenceAssignmentService._incompatibility` so `requires.structured_tools=True` requires executable Foundation composition plus an exact qualified deployment manifest with sufficient palette and dialect. Keep profile route/assignment evidence bound to the manifest hash.
- Teach route preflight to return the named required-tool refusal before Runner dispatch; optional tools must be able to choose palette zero on the already frozen deployment.

**Focused proofs**

- Extend `tests/unit/test_phase143_inference_capability_registry.py` for closed recursive tool schemas, confusable capability IDs, and MODEL_TURN non-discovery of owner operations.
- Extend `tests/unit/test_phase143_inference_route_plans.py` and `tests/unit/test_phase143_production_adoption.py` for exact qualified manifest / palette sufficiency, schema/manifest drift, legacy refusal, optional zero palette, and required-tool zero-child refusal.
- Add planned `tests/unit/test_phase143_tool_capability_lease.py` for canonical hash stability, forged/cross-turn/stale/revoked/expired lease failure, palette escalation and provider projection privacy.

### A2. Durable lease and ToolTurn transaction authority

**Implement**

- Add the lease, turn, command/transition and reservation tables; implement a server-only `ToolTurnController` with start/replay/reconstruct/Stop/reconcile APIs and a dedicated service principal.
- Freeze lease terms and route/boundary/policy/owner-intent references in one transaction. Verify store/hash before every restart/read; do not reconstruct from mutable profile/config/policy/descriptor state.
- Enforce the bootstrap maxima and lower typed-operation bounds. Atomically reserve model-step ordinal, provider-call/tool-call ordinal, slots, worst-case result bytes/tokens and effect quota with Stop/deadline/terminal fence.
- Make all newly introduced authority tables hostile to sync and model-visible projections omit canonical terms, nonce, owner identity, policy proof and MCP transport facts.

**Focused proofs**

- Planned `tests/unit/test_phase143_tool_turn_controller.py`: exact startup/replay, terms tamper/missing body refusal, −1/equality/+1 bounds, concurrent last-slot reservation, epoch/revocation/expiry, terminal winner and Stop/reservation race.
- Extend `tests/unit/test_reconcile.py` for add-only fresh/upgraded reconciliation and, if applicable, parent-kind CHECK rebuild; extend `tests/unit/test_db.py` for canonical snapshot.
- Extend `tests/unit/test_phase143_inference_fallback_controller.py` only where it must prove that existing route reservations still fail closed without a tool-turn lease (no broadening of generic controller). Add sync-denial assertions in the new controller test following `:1491-1505` there.

### A3. Model-step child planning boundary

**Implement**

- Give ToolTurn an internal model-step planner/evidence provider. Parent admission freezes the route chain and lease once; each planned model step derives a new private exact request plan from immutable owner material plus ordered, capped, hashed untrusted tool results.
- Compose one `InferenceFallbackController` execution per model step. It supplies all physical attempt reservations to `InferenceRunner`; the ToolTurn records only the step/execution/receipt linkage and remains above but not inside provider dispatch.
- Reject post-freeze deployment/template/tokenizer/route/lease drift as integrity refusal. Do not reuse provider-native request bytes across fallback deployments.

**Focused proofs**

- Planned `tests/unit/test_phase143_tool_turn_model_steps.py`: every step has a new request-plan hash, frozen route/lease hash on every child, exact 0/1/N physical-child cardinality, and parallel reverse completion yields the same next-step request hash/order.
- Reuse/extend `tests/unit/test_phase143_inference_route_plans.py` for no current-settings reconstruction and exact plan references.
- Reuse/extend `tests/unit/test_phase143_inference_fallback_controller.py` for a routed model step’s reservation/claim/bind/dispatch/settle lifecycle rather than creating a second Runner path.

### A4. Tool-call admission, result validation and effect receipt adoption

**Implement**

- Receive exactly one structured native tool-call candidate from the model adapter. Before any Broker submission validate lease liveness/epoch/turn/deployment/operation identity, exact capability membership/revision/schema hash, `MODEL_TURN` principal, closed argument schema/canonical hash, object/data/placement/egress scope, remaining reservation and current policy.
- Persist one ToolCall reservation and deterministic replay key. Same key adopts the immutable prior receipt; changed ID/capability/arguments refuses.
- Submit the canonical application service/Broker child under `MODEL_TURN`, validate/cap/hash/persist its result as untrusted data, and settle budget from the immutable child receipt. Oversize is typed and never truncates.
- For candidate/proposal/effect operations, bind owner-intent/policy admission and durable effect/proposal child receipt. On restart adopt a receipted effect exactly once. A missing post-dispatch receipt stays indeterminate/reserved and cannot advance model route.

**Focused proofs**

- Planned `tests/unit/test_phase143_tool_turn_controller.py`: closed/schema-drifted/confusable/unknown arguments, same-ID changed args refusal, service result byte/token ceilings, effect quota, `MODEL_TURN` owner-resource denial, typed outage versus model failure, and receipt adoption/idempotence.
- Planned `tests/integration/test_phase143_tool_turn_boundaries.py`: crash at model→tool reservation, Broker admission→effect, tool receipt→next model plan; restart adopts only known receipts and terminalizes unknown completion.
- Reuse `tests/unit/test_kernel_broker.py`, `tests/unit/test_one_path_spine.py`, and `tests/unit/test_phase143_inference_fallback_controller.py` for the actual separately admitted child and zero-bypass/cancel facts rather than reimplementing Broker assertions.

### A5. A→B hard gate

**Do not begin Part B implementation until this focused command is green and its output is read:**

```bash
uv run --python 3.13.11 pytest -q \
  tests/unit/test_phase143_tool_capability_lease.py \
  tests/unit/test_phase143_tool_turn_controller.py \
  tests/unit/test_phase143_tool_turn_model_steps.py \
  tests/integration/test_phase143_tool_turn_boundaries.py \
  tests/unit/test_phase143_inference_capability_registry.py \
  tests/unit/test_phase143_inference_route_plans.py \
  tests/unit/test_phase143_inference_fallback_controller.py \
  tests/unit/test_reconcile.py tests/unit/test_db.py
```

The four `test_phase143_tool_*` files are planned names; the existing tests named above are the current-tree composition guards. The gate must prove controller/service/ledger behavior, not merely collect/import. It is the story’s explicit “Part B cannot advertise or execute” line.

## 4. Part B — Tool-qualified routing and safe fallback slices

### B1. Exact qualified deployment routing

**Implement**

- Finish the A1 manifest predicate in the actual assignment save/resolution/preflight path. A required-tools capability is unsavable/unselectable when no entry has the exact qualified manifest, sufficient `qualified_palette`, frozen native dialect and executable Foundation composition. Existing saved invalid entries project one repair and refuse before dispatch.
- When tools are optional, freeze the selected deployment exactly as assignment chose it: qualified entries may receive a bounded lease; an unqualified entry receives a palette-zero lease and the durable disclosure fact `answering_from_note_and_attached_context_only`. No model substitution occurs.
- Freeze tool-qualified status into route/step evidence. Any fallback entry used after a tool-related correction is checked against the same lease palette, scope, boundary and dialect requirements.

**Focused proofs**

- Extend `tests/unit/test_phase143_inference_assignment_service.py` if present in the tree’s assignment test family, otherwise add planned `tests/unit/test_phase143_tool_qualified_assignment.py`; include exact save refusal, broken saved entry projection, optional zero-palette frozen execution and no current manifest upgrade.
- Extend `tests/unit/test_phase143_inference_route_plans.py` for frozen qualified-manifest hash and zero provider child on missing qualification.

### B2. ToolTurn parent composition and separately receipted model routing

**Implement**

- Compose a ToolTurn parent through `InferenceParentRouteBundleService`: one parent route chain at admission, exact pre-route refusal on failure, parent Stop handoff and route receipt reuse. If a `tool.turn` parent kind is used, widen the parent-kind vocabulary through the proven reconcile rebuild.
- For each model step, create exact immutable material/evidence, execute its frozen assignment with `InferenceFallbackController`/`InferenceRunner`, and write the corresponding `ModelStep` receipt. Do not put an adapter retry, a provider loop, or model-selected route leg behind it.
- Produce a private owner-safe ToolTurn receipt that links model steps/tool calls/effects and separately names actual model/boundary, attempted/skipped route legs, human tool names and proposed versus executed effect.

**Focused proofs**

- Planned `tests/unit/test_phase143_tool_turn_routing.py`: parent/bundle exactness; every model step maps to an `inference.invoke@1` child and every ToolCall maps to one Broker child; receipt reconstructs after restart without current assignment/config reads.
- Extend `tests/unit/test_phase143_meeting_route_primitives.py` only for generic parent-bundle/Stop semantics, keeping meeting-specific behavior untouched.

### B3. Ruled tool-qualified correction and fallback table

Apply the architecture’s tool-bearing fallback rules as explicit classified cases:

| Event | Model/tool action | Fallback rule and proof |
| --- | --- | --- |
| Malformed/unknown/schema-drifted native tool call | No tool dispatch; record typed `invalid_tool_call`. | May consume only the frozen bounded corrective model step. If it advances, next route entry must be tool-qualified for the same frozen lease. Test changed-ID/payload, confusable capability, closed nested schema and one correction boundary. |
| Valid commutative read succeeds | Cap/hash/persist untrusted result; derive next exact model step in original provider/tool ordinal. | Same or qualified fallback model may receive it only inside lease/aggregate budgets. Test reverse completion produces identical next request hash. |
| Read-only tool typed unavailable/stale/exhausted | Persist typed result/receipt, not a generic provider error. | May be supplied to same/fallback model only when frozen final schema/receipt explicitly permit the named limitation. No default model retry/fallback for service/network outage. |
| Tool service/network failure | Produce typed service outcome. | It is **not** automatic model failure. Test zero route advance unless an explicit model/tool-dialect-specific frozen disposition authorizes it. |
| Receipted proposed/executed effect | Adopt exact receipt and bind it to ToolCall/effect child. | Never repeat on correction/fallback/restart. Owner sees proposal/execution separately. |
| Unknown effect completion | Preserve indeterminate reservation. | Terminal (`effect_indeterminate`); zero retry/fallback/re-execution. |
| Permission denial/policy refusal/approval refusal, Stop, lease expiry or deadline | Typed terminal. | Zero later model/tool egress; Stop fence wins before best-effort cancellation. |
| Tool-qualified model failure after safely settled read result | Existing `InferenceFallbackController` classifies a frozen model-step disposition. | It can advance only to a frozen entry that is tool-qualified and has identical/narrower lease terms; no palette/scope/budget/policy/egress expansion. |

**Focused proofs**

- Planned `tests/unit/test_phase143_tool_turn_routing.py`: all rows above, tool-qualified-only fallback, optional/no-tool answer text fact, exact receipt ordering and one model-step corrective budget.
- Extend `tests/unit/test_phase143_inference_fallback_controller.py` only with bridge-level disposition classification/route reservation evidence; retain its existing generic disposition table as authoritative model-attempt law.

### B4. End-to-end adversarial and disclosure proof

**Implement/test**

- Drive fake adapters/services through model→tool→model, model crash, tool crash, effect crash, receipt crash, Stop/model race, Stop/tool reservation race, and restart reconciliation. Assert no physical egress after the durable terminal winner.
- Add receipt projection fields needed for the later UI manual walk: exact tools used; source/result receipts one disclosure away; proposed/executed effect distinct; actual model attempts/fallback reason/boundary; palette-zero reason. Do not implement Story-13 glass here.
- Confirm HTTP/MCP/Desk are merely future callers of the same application controller and `MODEL_TURN` discovers no owner resources; sync never executes/resumes/reconciles.

**Focused proofs**

```bash
uv run --python 3.13.11 pytest -q \
  tests/unit/test_phase143_tool_capability_lease.py \
  tests/unit/test_phase143_tool_turn_controller.py \
  tests/unit/test_phase143_tool_turn_model_steps.py \
  tests/unit/test_phase143_tool_turn_routing.py \
  tests/integration/test_phase143_tool_turn_boundaries.py \
  tests/unit/test_phase143_inference_capability_registry.py \
  tests/unit/test_phase143_inference_route_plans.py \
  tests/unit/test_phase143_inference_fallback_controller.py \
  tests/unit/test_phase143_meeting_route_primitives.py \
  tests/unit/test_phase143_production_adoption.py \
  tests/unit/test_one_path_spine.py tests/unit/test_kernel_broker.py \
  tests/unit/test_reconcile.py tests/unit/test_db.py
```

The manual/device leg, once a real adopter exists, is constrained to the ruled wording/facts: exact tools used, proposed vs executed effect, and model-fallback disclosure. It must not claim “Tool use qualified” or expose lease JSON/MCP dialects.

## 5. Risks and containment

| Risk | Failure mode | Containment/proof |
| --- | --- | --- |
| Model boundary crash | Driver may have sent a request after durable intent but before receipt. | Reuse `InferenceFallbackController` dispatch-intent classification; unresolved physical outcome is indeterminate and never advanced/replayed. |
| Tool boundary crash | Broker child may be admitted/executed but receipt link is absent. | Reservation remains indeterminate; reconciliation searches immutable Broker/receipt evidence only. No current-policy reconstruction or duplicate call. |
| Effect boundary crash | Effect could have completed once. | Separate adopted effect child/receipt linkage; known receipt adopts, unknown completion terminalizes. This is the highest-priority integration fixture. |
| Parallel reads race budgets/order | Simultaneous final slots can over-spend or completion order can alter model bytes. | One `BEGIN IMMEDIATE`/CAS reservation for all worst-case quotas and ordinal insertion. Test simultaneous last slots and reverse completion hash equality. |
| Stop race | A late result/pending dispatch could publish or start fallback after Stop. | ToolTurn Stop joins reservation/terminal election; parent bundle and route controller fence first, then best-effort cancel. Test Stop-v-model, Stop-v-tool admission, deadline-v-result. |
| Tool-service outage mislabeled as model failure | Model fallback creates unnecessary egress or hides missing evidence. | Typed ToolCall result taxonomy separated from `InferenceFallbackController` provider dispositions; dedicated no-auto-advance test. |
| Manifest/lease drift | A current profile qualifies after the turn began or a changed schema executes. | Frozen hash/revision reconstruction, route step plan and lease binding; all mismatch conditions named integrity refusal. |
| Recipe/agent scope creep | Persisted `RecipeRecord.tools` tempts direct wiring. | Keep it inert in Story 09. Story 10 owns its parent/adoption; tests ensure no new recipe/Workbench provider tools parameter or controller call. |
| Schema migration destroys owner data | Parent-kind CHECK cannot alter in place. | Reuse semantic replacement-table savepoint pattern, copy all live columns/rows, preserve dependents, prove idempotent no-op and data retention. |
| Receipt disclosure leaks authority | Lease/owner/token/policy terms accidentally project to UI/MCP. | Separate private canonical ledger from owner-safe receipt and provider tool schemas; non-discovery/redaction tests. |

## 6. [ORCH-CALL] — bounded implementation tie-breaks

These are choices the ruled text leaves at implementation granularity. They are recommendations, not new counsel questions.

1. **Lease capability source.** Recommended: add a small composition-owned `MODEL_TURN` projection adapter over existing canonical application-operation descriptors/MCP semantics, rather than make `mcp.tools.TOOLS` itself the lease registry. It preserves shared semantics while structurally excluding owner transport fields and keeps Story 11 transport work out.
2. **Effect ledger representation.** Recommended: add `tool_turn_effect_children` as a narrow mapping table even though the ruled ledger sketch names four primary entities. Story scope expressly calls for effect child ledgers, and a mapping makes adopted-versus-indeterminate effect truth restart-reconstructible without overloading ToolCall rows. It contains references/hashes/receipt state, never effect payloads.
3. **Lease versus route-plan ownership.** Recommended: ToolTurn freezes one parent route plan and one lease at parent admission; each model step freezes a *new* private operation request plan and starts one existing `InferenceFallbackController` execution. This directly follows architecture §228–236 and lets the existing controller remain physical-attempt authority.
4. **Qualified manifest encoding.** Recommended: evolve `capability_manifest` from its current exact `{revision, sha256, claims}` body to a closed versioned body with `claims` plus `tool_qualification { structured_tool_use, qualified_palette, tool_eval_revision, native_tool_dialect, sha256 }`; bind its full hash to deployment as current profile/deployment binding already does. Old manifests become `unavailable`/palette 0 rather than being backfilled as qualified.
5. **Foundation readiness predicate.** Recommended: use composition registration of the concrete `ToolTurnController`/projection service as the executable-foundation proof, checked server-side in assignment/route preflight. A manifest alone remains insufficient, matching “offline evaluation alone is insufficient.”
6. **Bootstrap operation.** Recommended: expose an internal test/service-owned `tool.turn` parent/evidence provider first, not `Ask`, Recipe, Workbench, or MCP. It supplies a real executable Part-B seam while preserving the explicit adopter boundaries; Story 10 decides which existing surface first invokes it.
7. **Parent kind.** Recommended: add `tool.turn` to `kernel_parent_runs.kind` and use `InferenceParentRouteBundleService` rather than a parallel parent table. Use the existing parent-kind CHECK rebuild on upgrade and prove preservation. If the orchestrator judges an internal test parent sufficient, defer the CHECK change until the first real adopter but retain the same bundle contract.
8. **Tool result continuation representation.** Recommended: make the controller accept only a closed typed result envelope that includes `available|unavailable|denied|oversize|indeterminate`, capped safe result material/hash, and a `final_answer_may_name_limitation` flag frozen by the operation schema. Default false, so an outage cannot leak through as an ordinary answer.
9. **Native dialect adapter contract.** Recommended: define a provider-neutral internal `ToolModelAdapter` with `render(frozen request, provider tools) -> one request` and `parse(one response) -> exactly one closed answer/tool-call candidate`; do not retrofit `MeetingIntel`/`CanonicalPromptAdapter` into a loop. Provider-specific native tool dialect support lands as a selected qualified adapter implementation only.
10. **Test layout.** Recommended: use four new focused modules named in this plan (`test_phase143_tool_capability_lease.py`, `test_phase143_tool_turn_controller.py`, `test_phase143_tool_turn_model_steps.py`, `test_phase143_tool_turn_routing.py`) plus one integration boundary module. This keeps foundation, state/ledger, model planning, and fallback behavior independently gateable before a production adopter exists.

## 7. Orchestrator dispositions on the [ORCH-CALL]s (2026-08-25)

All ten recommendations ACCEPTED as written, decided by the
orchestrator as tie-breaker (no counsel round — the design is ruled;
these are implementation granularity). One strengthening: call 7 lands
the `tool.turn` parent kind NOW, through the existing
`kernel_parent_runs` CHECK rebuild proven in Story 08 (old-shape-DB
preservation proof required), not deferred — one schema touch, not
two. Calls 4 and 8 are load-bearing honesty rules and are restated as
binding: an old manifest is NEVER backfilled as tool-qualified
(palette 0 / unavailable), and the typed tool-result envelope's
`final_answer_may_name_limitation` defaults FALSE so an outage cannot
leak into an ordinary answer. Construction proceeds: A1+A2 in one
round, A3+A4 in one round, then the A5 gate with an opus verification
leg (Terra-paired-with-opus law) before any Part B work.

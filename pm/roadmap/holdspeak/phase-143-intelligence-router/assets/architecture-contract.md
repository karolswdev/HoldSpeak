# Phase 143 architecture contract — profiles, assignments, and fallback

**Status:** ratified charter authority (owner and architecture review,
2026-08-21).
**Depends on:** Phase 130 placement truth, Phase 131 one admission path, and
Phase 142 inference setup/artifact/deployment truth. Story 09 implements the
Tool Capability Foundation contract ruled in
`proposals/inference-catalog-and-context-policy.md` before tool routing ships.

## Decision

HoldSpeak will have one reusable model library and one server-owned capability
assignment system.

* A **model profile revision** describes reusable execution intent: the model
  or artifact identity, provider/runtime family, context support, and governed
  capability evidence. It contains no key, local path, or live readiness.
* A **profile binding** is hub-local configuration that binds one exact model
  profile revision to an exact deployment head/revision, secret slot, and
  readiness observation. Every execution still captures the existing immutable
  `DeploymentRevision`; this phase does not create a second execution registry.
* A **capability** describes one typed job HoldSpeak may ask intelligence to do.
  It declares requirements, operation/result contracts, and owner-facing group.
* An **assignment** (`InferenceAssignment@1`) connects a capability or capability group to an ordered
  profile chain. The first entry is primary; later entries are fallbacks.
* A **route plan** (`InferenceRoutePlan@1`) is the immutable, content-free resolution of an assignment
  for one parent turn/session/job. It contains exact deployment revisions and
  fallback law. No engine, adapter, or browser resolves a profile after freeze.
* A **fallback controller** advances the frozen plan only for a closed,
  explicitly eligible terminal disposition. Every provider-reaching try remains
  a separately admitted and receipted `inference.invoke@1` child.

There is no second inference gateway, deployment-revision registry, tool
authority, or browser-authored routing truth.

`CapabilityRoutePolicy` is prose for assignment policy, not another persisted
type. `ResolvedCapabilityRoutePlan` is prose for a resolved route, not another
table/DTO. The only canonical persisted names are `InferenceAssignment@1` and
`InferenceRoutePlan@1`.

## The owner vocabulary

Owner glass uses **Models**, **Providers**, and **Assignments**.

* **Models** — intelligence available to HoldSpeak.
* **Providers** — OpenRouter, Anthropic, OpenAI-compatible endpoints, private
  servers, paired devices, and their credential/readiness facts.
* **Assignments** — which models do which HoldSpeak jobs, including fallbacks.

Primary UI does not say target, route revision, adapter, profile ID, deployment
revision, or `openAICompatible`. Those remain technical Details terms.

## Canonical capability registry

The server owns a versioned, deterministic registry. Feature modules register
definitions at composition time; the web client never invents a capability.

```text
InferenceCapabilityDefinition@1 {
  id, revision, label, group_id, group_label, description,
  operation_contract {name, version, definition_origin},
  input_modalities[], output_kind, output_schema_sha256,
  context_support: exact|bounded|unavailable,
  requires {structured_output, structured_tools, vision, audio,
            minimum_context_tokens, capability_classes[]},
  allowed_boundaries[], permitted_retry_policy_ids[], default_retry_policy_id,
  fallback_dispositions[], owner_visibility,
  source_module, schema_sha256
}
```

IDs are stable ASCII slugs. Definitions are recursively closed, canonically
encoded, hash-bound, and duplicate/confusable IDs refuse startup. Removing or
changing a requirement is a new definition revision. An invocation freezes the
exact definition revision and schema hash.

### Bootstrap taxonomy

| Group | Capability IDs | Existing seam |
|---|---|---|
| Thoughts & notes | `thought.interview`, `thought.synthesis`, `ask.answer` | refinement coordinator, Ask service |
| Writing & dictation | `speech.intent_classify`, `speech.rewrite`, `speech.punctuate` | `speech_session.plan` |
| Speech recognition | `speech.transcribe`; internal `speech.preload` | Whisper session plans; `speech.preload` is lifecycle work with `owner_visibility=internal`, never an assignable row |
| Meetings | `meeting.live_analysis`, `meeting.bookmark_label`, `meeting.auto_title`, `meeting.deferred_analysis`, `meeting.plugin.<id>` | `MeetingIntelPlan` |
| Agents & tools | `agent.plan`, `agent.tool_turn`, `agent.code`, `workbench.item`, `recipe.run`, `recipe.chat`, `voice.reference_resolve` | parent runners and admitted children |
| Background | `background.rails_summary`, `background.cadence_draft`, `decision.promotion_draft`, `delivery.pr_review_draft` | bounded service principals |

Plugin capabilities join through a bounded registry adapter and carry the
plugin definition revision. Arbitrary runtime strings cannot create a route.

## Profile, binding, and deployment authority

The phase reuses Phase 142's model artifact, deployment head, and immutable
`DeploymentRevision` laws.

```text
ModelProfileRevision@2 {
  profile_id, revision, sha256, label,
  provider_family, runtime_family, model_or_artifact_identity,
  supported_modalities[], context_support,
  tokenizer_template_requirements,
  capability_manifest {revision, sha256, claims[]},
  safe_presentation, created_at
}

ProfileBinding@1 {
  binding_id, revision, profile_id, profile_revision,
  deployment_head_id, deployment_revision_id,
  secret_slot?, endpoint_binding?, local_artifact_binding?, enabled,
  configuration_revision, readiness_observation_id, updated_at
}
```

A local downloaded artifact, existing GGUF/MLX model, OpenRouter model,
Anthropic model, private OpenAI-compatible model, paired device, or mesh node
can become a profile only through its canonical setup/application service. Its
hub-specific path, endpoint, secret, and readiness become a binding, not profile
identity. Secrets remain in the existing profile key store. Absolute local
locators, tokens, and endpoint credentials never enter profile revisions,
assignments, route plans, ordinary projections, sync, or receipts.

Profile readiness is observation, not immutable execution proof. Assignment
save validates compatibility against current profile evidence and an enabled
binding; invocation resolution validates again and freezes an exact
`DeploymentRevision`. Historical v1 `ProfileRecord` rows adapt to one legacy
profile revision plus one local binding without changing their stored bytes.

`ProfileService` and its replacement application methods enforce OWNER at the
service boundary. HTTP's default principal is not authority. AGENT and
MODEL_TURN cannot enumerate, probe, create, update, delete, bind, or assign
profiles through HTTP, MCP, or direct service calls.

## Assignment hierarchy and precedence

Assignments are sparse overrides, never a capability × model matrix.

```text
invocation override
  -> subject override (Thought / Workbench / Agent / Recipe / Project)
  -> exact capability assignment
  -> capability-group assignment
  -> global AI assignment
```

The first defined assignment wins as a whole ordered chain. Layers are not
concatenated. `Use default` deletes the sparse override and the projection
always names the effective chain and the layer it inherited from.

The first slice is hub-local. V2 model-profile revisions, bindings,
assignments/routes, readiness, hardware, credentials, artifact locators, and
fallback execution do not sync. Historical v1 profile/deployment bytes and
immutable nonsecret deployment revision metadata retain only their already
ruled receipt-resolution sync law. Sync import never creates a v2 profile,
binding, readiness fact, assignment, acquisition, probe, or invocation.

```text
InferenceAssignment@1 {
  id, scope {kind, subject_id?}, capability_id|group_id|global,
  entries[] {ordinal, profile_id, profile_revision?},
  retry_policy_id?, revision, created_at, updated_at
}
```

Entries are unique and bounded (initial maximum four). Saving is one atomic CAS
over the entire ordered chain; dragging/reordering never autosaves partial
order. Empty chains are forbidden. Deleting the final fallback leaves the
primary; clearing the assignment means inherit.

An exact-capability assignment may select one policy permitted by that
capability. Group/global assignments primarily store the chain and resolve each
capability with its own default policy. They may store a policy override only
when the server proves the exact policy revision is permitted by every affected
capability. The server projects the compatibility/policy intersection; the
browser never computes it.

At resolution, an inherited chain that cannot satisfy the exact capability
produces named `no_compatible_assignment`; entries never silently disappear or
become fallback skips. **Use default** previews the effective
capability-specific chain/policy before clearing an override. Registry growth
cannot retroactively bless a group/global assignment: any new incompatible
capability appears as a visible issue until the owner repairs or overrides it.

### Fresh and upgraded default law

A fresh hub with no assignment projects **No default model** and one repair,
**Choose default**. Adding, downloading, detecting, or connecting the first
model never assigns it. The server may project an exact starter bundle, but it
is applied only by one explicit **Apply setup** action whose preview names every
group chain and boundary.

Upgrade maps each valid legacy primary into a one-leg assignment for its exact
family, preserving effective behavior. Missing or dangling legacy targets do
not guess a replacement; they project **No default model** or a group issue and
one **Choose model** repair. With no effective route, invocation refuses before
planning/egress as `no_assignment`; non-AI work remains available.

## Compatibility and qualification

An assignment entry is structurally compatible only when its durable profile
claims can satisfy the capability. Whether it is executable for a particular
operation is decided later by that operation's private admitted-request plan.
Structural compatibility requires:

* capability definition and operation/result schema revision;
* profile claims the required modalities and structured dialect;
* the deployment declares `exact|bounded` context support capable of planning
  this operation; actual material fit is not guessed during assignment save;
* tool-bearing work has an executable Tool Capability Foundation and an exact
  qualified deployment manifest; offline evaluation alone is insufficient;
* the profile boundary is one the capability can lawfully use.

Per-operation preflight eligibility then observes binding enabled/current, exact
deployment resolution, placement/egress/principal policy, credential presence,
artifact/runtime readiness, resource leases, revocation, and the exact material
fit. These volatile facts never change profile identity.

Runtime lease/capacity pressure is exclusively an operation-time observation
classified `local_capacity_unavailable`. It is never assignment-save
compatibility and cannot prevent saving an otherwise compatible chain.

The assignment editor filters normal choices to compatible profiles and
normally excludes unavailable bindings, but shows a configured entry that later
becomes incompatible/unavailable in place with one repair. A server projection
may explicitly mark a compatible unavailable candidate `savable_with_repair`;
the UI must show that issue before Save. Direct HTTP/MCP calls cannot save an
incompatible or unprojected chain.

## Frozen route plan

Every inference parent freezes one content-free route plan before child
admission. It freezes capability, ordered deployments, boundaries, and policy,
but never future material. One-shot operations atomically freeze the route plan
and a private admitted-request plan from their immutable material snapshot.
Long-lived meeting/speech/tool parents freeze the route chain at parent
admission; each later child/model step freezes a new private request plan from
that child's immutable material before its ServiceContract admission.

```text
InferenceRoutePlan@1 {
  id, sha256, capability {id, revision, schema_sha256},
  source {assignment_id, assignment_revision, inherited_from},
  entries[] {
    ordinal, profile_id, profile_revision, binding_revision,
    deployment_revision_id, capability_manifest_sha256,
    boundary, context_support
  },
  retry_policy {id, revision, sha256, per_entry_attempts, total_attempts,
                eligible_dispositions[]},
  operation_policy_revision, created_at, deadline_at
}
```

```text
OperationAdmittedRouteRequestPlan@1 {
  id, sha256, route_plan_id, operation_id, material_snapshot_sha256,
  entries[] {
    route_leg_ordinal,
    eligibility: executable|known_preflight_unavailable|known_context_overflow,
    reason_code?, admitted_request_id?, admitted_request_sha256?,
    context_plan_sha256?, serialized_request_sha256?
  },
  created_at, deadline_at
}
```

The private operation plan retains every configured leg and its frozen
eligibility. Only executable legs carry admitted-request references. All legs
are evaluated against the same immutable material snapshot; different
tokenizers/templates may yield different valid serializations. Fallback never
rereads, summarizes, truncates, or changes owner material after primary failure.
A known planning-time overflow may advance only to an already exact-planned
larger leg under explicit policy. Any post-admission tokenizer, template,
serialization, context, or deployment drift is integrity refusal and cannot
retry or fall back.

The route and private operation plans store IDs, hashes, boundaries, budgets,
eligibility, and revisions—not prompts,
Note bodies, transcript text, audio, tool results, keys, or local paths. The
kernel parent snapshot carries their summaries/hashes. Every child repeats the
exact route plan ID, operation request-plan ID, leg ordinal, deployment
revision, and physical-attempt ordinal. Durable private references suffice for
restart without exposing owner material through the route projection.

Changing a profile, assignment, capability definition, policy, or model while
a run is active affects the next parent only. It never retargets an admitted
child. Replay adopts the same receipt; it does not resolve current settings.

## Retry and fallback law

Retry means another physical attempt on the same frozen entry. Fallback means
advancing to the next frozen entry. Both consume bounded parent budgets and
create new admitted/receipted children.

The server owns an immutable, canonically hashed retry-policy registry:

```text
InferenceRetryPolicyDefinition@1 {
  id, revision, sha256, permitted_capability_ids[],
  per_entry_attempts, total_physical_attempts, deadline_ms,
  token_budget?, cost_budget?, tool_call_budget?,
  retryable_dispositions[], fallback_dispositions[]
}
```

A capability declares its permitted policy IDs and one default. An assignment
may select only from that set; the route freezes the exact policy revision and
hash. Policy selection never broadens capability boundary/tool/effect authority.

Default budgets are conservative and capability-specific. The platform does
not hard-code “three attempts everywhere.” A typical text/tool capability may
allow two attempts on the primary and one on each fallback, with a hard total,
deadline, token, cost, and tool-call ceiling.

### Disposition table

| Disposition | Same-entry retry | Next fallback | Law |
|---|---:|---:|---|
| `preflight_unavailable` | no | only when the frozen policy explicitly allows `skip_unavailable` and the next entry is currently eligible | zero physical call; receipt names skip |
| `known_no_generation_transient` | bounded yes | yes after retry budget | failure proven before request send, or explicit provider no-generation response such as 429 |
| `dispatch_outcome_unknown` | no | no | disconnect/read timeout after send or any state where generation may have occurred |
| `provider_permanent` | no | policy may allow | authentication/config failure normally nominates repair instead |
| `invalid_typed_output` | one corrective attempt if declared | yes to another schema-qualified entry | raw invalid output never publishes |
| `invalid_tool_call` | bounded corrective model step | yes only to another tool-qualified entry | tool args never execute before validation |
| `context_overflow` | no | only to a frozen entry with a larger provable envelope | a smaller model is never offered as repair |
| `local_capacity_unavailable` | no | only when boundary policy permits the next entry | no silent local→cloud crossing |
| `tool_unavailable_or_stale` | no model retry by default | only when failure is model/tool-dialect-specific and next entry is qualified; service outage is not repaired by a different model | typed tool result may allow a limited final answer |
| `permission_denied` / `policy_refused` | no | no | model choice cannot manufacture authority |
| `owner_cancelled` / `deadline_exhausted` | no | no | terminal winner fences later work |
| `physical_outcome_unknown` / `effect_indeterminate` | no | no | never risk duplicate provider/effect execution; aliases classify to the same terminal family as dispatch-outcome-unknown |
| `owner_terminal` | no | no | expected stop/edit/completion is not failure |

Fallback can change privacy boundary only when the owner saved that exact chain
with the boundary disclosure visible. The receipt names every attempted/skipped
entry and actual egress. A local fallback is used only when it meets the same
capability contract; “local” is not a waiver for tools, context, or schemas.

### Tool-bearing fallback

`Ask` or generic model prose never authorizes an effect. Tool turns use the
server-owned `ToolTurnController`, durable private capability lease, and
separately admitted model/tool children ruled in the catalog/context proposal.

* A malformed native tool call may consume a corrective model step and then
  advance to another **tool-qualified** model.
* A read-only tool's typed unavailable result may be fed to the same/fallback
  model only within the frozen lease and aggregate budgets.
* A tool service/network failure is not automatically a model failure.
* A receipted effect is adopted, never repeated by a fallback model.
* Unknown effect completion, permission denial, approval refusal, Stop, or
  lease expiry terminalizes the turn without model fallback.
* Parallel read results retain provider-call ordinal order when replanned for a
  fallback deployment; completion order never changes request identity.

## Controller and durable evidence

One `InferenceFallbackController` lives above `InferenceRunner`; engines and
provider adapters never loop, retry, or choose another deployment internally.

```text
resolve assignment -> freeze plan -> reserve entry/attempt
  -> admit InferenceRunner child -> receipt
  -> classify closed disposition under plan policy
  -> terminalize OR reserve next attempt/entry
```

```text
inference_route_plans
  plan_id, plan_sha256, capability_id/revision, assignment_id/revision,
  entries_json, retry_policy_json, state, deadline_at, created_at

inference_route_attempts
  plan_id, route_leg_ordinal, physical_attempt_ordinal, child_invocation_id,
  deployment_revision_id, state, disposition, receipt_id,
  reserved_at, terminal_at
```

Reservation, Stop fencing, terminal election, and budget decrement happen in
one transaction/CAS. Crash with an unreceipted physical call becomes
indeterminate and never blind-replays. Restart may reconcile durable receipts;
it cannot reconstruct a plan from current Config/profile state.

Route-leg ordinal and physical-attempt ordinal are distinct. A provider dialect
compatibility child may consume another physical attempt on leg 1 without
colliding with the first physical attempt on leg 2.

The controller owns a durable attempt-reservation authority; `InferenceRunner`
remains the physical waist. Before admitting a primary, same-leg retry, or
provider-dialect compatibility child, Runner requests/resumes an exact
reservation `{plan_id, leg_ordinal, physical_attempt_ordinal, purpose}` from the
controller. That transaction validates Stop/deadline/terminal state and debits
the frozen total/per-leg budget. Runner cannot mint an unbudgeted compatibility
child, and the controller never constructs an engine or invokes a provider.
Legacy one-leg callers use an adapter reservation until their parent migrates.

## Application and transport boundary

`InferenceRoutingApplicationService` owns registry, assignment, plan, and
receipt projections. Feature services ask it to resolve/freeze; HTTP, MCP, and
Desk call the same methods.

```text
get_model_library() -> {library}
get_assignments() -> {assignments}
get_capability(id) -> {capability}
get_assignment(scope, capability_or_group) -> {assignment}
set_assignment(request_id, expected_revision, scope, subject,
               capability_or_group, entries[], retry_policy_id) ->
               {receipt, assignments}
clear_assignment(...) -> {receipt, assignments}
resolve_assignment_preview(scope, subject, capability) -> {resolution}
get_route_receipt(plan_id) -> {route_receipt}
```

All DTOs and request bodies are recursively closed and versioned. Mutations use
stable request IDs, payload hashes, and narrow assignment revisions. Replays
return immutable effect evidence plus a fresh projection; changed payloads
refuse. Resources and tools are OWNER-only and absent from MODEL_TURN. Events
are advisory; GET reconstructs current truth.

## Owner experience

Settings contains two jobs:

1. **Models** — download local models, register existing artifacts, connect
   OpenRouter/Anthropic/custom providers, inspect readiness, and test synthetic
   input. Adding a model makes it available; it does not silently rewrite every
   assignment.
2. **Assignments** — choose which models perform HoldSpeak jobs.

The default Assignments glass stays bounded as capabilities grow:

```text
Assignments                                      1 issue
Default for AI work       Quick Qwen → Deep Qwen
Thoughts & notes          Uses default · Quick Qwen → Deep Qwen
Writing & dictation       Tiny Qwen → Quick Qwen
Speech recognition        This device
Meetings                  This device → Deep Qwen
Agents & tools            Uses default · Quick Qwen → Deep Qwen
Background                Uses default · Quick Qwen → Deep Qwen
Show task overrides
```

The stable roster is exactly those seven assignment rows. Each inheriting group
also names its effective chain. **Show task overrides** reveals capability
leaves with the initial filter **Overrides & issues**. Adding the twentieth
capability does not lengthen default glass. Internal lifecycle capabilities
such as `speech.preload` never appear.

Clicking a row opens one editor/sheet:

```text
Writing & dictation
○ Use default   Quick Qwen → Deep Qwen
● Custom
1  Tiny Qwen                    Ready
2  Quick Qwen        Fallback  Ready
   Add fallback
Fallbacks run only for the failure types shown in Details.
Cancel                           Save assignment
```

The model chooser reuses the task-first library picker and filters by server
compatibility. Reordering supports drag and Move up/down. One atomic Save is
the sole primary. Cloud boundary changes show one terse warning beside the
affected entry. Broken saved entries remain visible with one repair.

Subject surfaces reuse `AssignmentSummary`/`AssignmentEditor`:

```text
Model  Uses Thoughts default · Quick Qwen + 1 fallback   Change
```

They never implement their own selector or mutate global defaults. In-flight
work continues under its frozen plan; the changed summary says **Next run**.

### Owner-visible runtime truth

* `Quick Qwen failed. Trying Deep Qwen (2 of 3)…`
* `Deep Qwen completed this after Quick Qwen failed.`
* `All 3 models failed. This task didn’t complete.` — only when all three made
  physical attempts and produced known failures; skipped entries get exact
  skipped/unavailable copy.
* `Quick Qwen refused this run. No fallback was attempted.`
* `Cancelled. No fallback was attempted.`
* `We can’t confirm whether Quick Qwen ran. No fallback was attempted.`
* `Fallback 2 can send this Note and attached context to OpenRouter.` The
  material noun is capability-specific: transcript, audio, or tool-result data
  is named when that is the projected input.

No copy claims a fallback until the controller durably reserves that entry.

## Migration and deletion law

The phase begins with a generated pointer/resolver/dispatch census. Existing
Config and object fields remain authoritative until their capability family
migrates once. Each migration has one marker and mapping, then consumers stop
reading the old pointer; indefinite dual-read/dual-write is forbidden.

The existing `MeetingIntelPlan` ordered-revision implementation is the proved
pattern to generalize, not a second permanent plan type. During migration it may
adapt from the canonical plan, but after its family crosses, capability route
resolution has one source.

Legacy profile records remain reusable identities. Mutable `InferenceTarget`
resolution ends before admission; immutable `DeploymentRevision` remains the
runner contract. Workbench/Recipe/Agent inheritance is migrated without
changing its visible effective destination until the owner edits an assignment.

The existing mutable `inference.run` target-resolution path is retired or made
a legacy adapter that produces one frozen one-leg plan before admission. The
existing workflow labels `fallbackOnDevice` and `retryThenQueue` are not model
fallback—they currently carry input forward—and must be renamed or removed
rather than treated as precedent.

Deleting a profile refuses while referenced by any assignment, active route
plan, acquisition/deployment head, or historical artifact requirement. The
repair lists assignments that must change. Soft deletion cannot erase receipt
resolution.

## Performance and accessibility budgets

* Models/Assignments shell from cache: next frame, under 100 ms.
* Local authoritative projection: target under 300 ms.
* Open assignment editor/model chooser: under 100 ms.
* Save acknowledgement: under 300 ms on local hub.
* Route resolution before admission: target under 10 ms p95 from local SQLite;
  no network, model load, provider probe, or artifact scan.
* Fallback decision after terminal receipt: under 50 ms before next child
  admission; physical provider latency is reported separately.
* 393px: all targets at least 44px, no horizontal overflow, model names wrap,
  sticky Save stays inside the sheet, and ordering works without drag.
* Keyboard: arrows/select in model lists; Move up/down for order; Escape returns
  focus; Mod+Enter invokes the one focused primary only.

## Kill criteria

The phase cannot close if any of the following remains:

1. A capability resolves a mutable profile after admission.
2. An engine/provider adapter performs a hidden retry or fallback.
3. A physical model call bypasses `InferenceRunner`.
4. An unknown/indeterminate/effectful outcome advances fallback.
5. Local→cloud fallback occurs without a saved visible boundary crossing.
6. A tool-incompatible deployment can be saved or selected for required tools.
7. Browser code invents capability compatibility, readiness, or fallback law.
8. Config and the assignment store remain competing authority after migration.
9. The default UI grows one permanent row per capability or becomes a matrix.
10. HTTP/MCP/Desk produce different assignment, plan, attempt, or receipt truth.
11. Sync import starts/resumes inference or rewrites hub-local assignments.
12. A receipt cannot explain primary, attempts, fallback reason, actual model,
    boundary, and terminal outcome without reading current settings.

## Required adversarial matrix

Tests must cover at least:

* every registry definition and every production inference call site belongs to
  exactly one capability; unknown/confusable/unregistered IDs refuse;
* precedence at every layer, clear-to-inherit, dangling subject, concurrent CAS,
  changed-payload replay, and unrelated-assignment concurrency;
* profile edit/removal, capability revision, schema drift, runtime/artifact
  replacement, credential loss, and readiness changes before/after plan freeze;
* every disposition row above at budget −1/equality/+1, including Stop/result,
  deadline/result, restart, and lost-response races;
* provider failure on primary then local success; local capacity skip to a
  visibly authorized cloud entry; forbidden boundary crossing refusal;
* malformed tool call correction, tool-qualified fallback, tool service outage,
  effect receipt adoption, unknown effect completion, and permission denial;
* exact context fit under different fallback tokenizers without reusing
  provider-native serialization; no silent truncation;
* two concurrent plans sharing a profile, local runtime lease pressure, route
  edit while active, and no DispatchContext cross-bind;
* HTTP/MCP reciprocal fixtures, owner denial, MODEL_TURN non-discovery, event
  loss then GET, restart receipt reconstruction, and sync zero egress;
* fresh and upgraded databases, every legacy pointer family, no dual authority,
  and a generated zero-bypass census;
* 1440/393/200%-zoom glass for library, provider connection, assignment groups,
  leaf overrides, compatible chooser, reorder, broken entry, boundary warning,
  fallback progress/success/exhaustion/refusal/indeterminate, focus, screen
  reader names, reduced motion, and no overflow.

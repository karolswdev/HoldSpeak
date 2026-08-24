# Story 08 / Phase E — background adopter design candidate

**Status:** pre-counsel design candidate, 2026-08-24.  This is an adoption
slice, not a second planner/controller/gateway.  It reuses the frozen
route-plan → fallback-controller → Runner waist and leaves legacy-authority
deletion to **Phase F**.

## Decision boundary

Article XI applies even when an invocation is small, local, or initiated by a
loop: model work is consequential, must be admitted before it acts, and ends
in a terminal receipt including refusal and unknown (`docs/internal/CONSTITUTION.md:123-139`).
The Phase-E rule is therefore:

1. admit one parent plus its complete frozen route bundle atomically through
   `InferenceParentRouteBundleService.start()` / `start_in_transaction()`;
2. only after that commit stage private prompt material with
   `RoutedInferenceCoordinator.admit_on_frozen_route()` and execute it through
   `RoutedInferenceCoordinator.execute()`;
3. use the frozen-definition semantic adapter, controller reservation, and
   post-election materializer; and
4. derive any egress truth from frozen route entries, never a requested target,
   `RuntimeProfile`, or a local default.

The machinery already does the necessary work: bundle start persists the parent
and every member on one connection (`services/inference_parent_route_bundle_service.py:176-202,379-520`);
frozen-route admission stages private material and starts the controller in its
one transaction (`services/inference_adoption_service.py:965-1082`); execution
reserves controller-owned attempts and only publishes after settlement/election
(`services/inference_adoption_service.py:1284-1405`).  No raw prompt, decision
text, diff, or rail-event bytes belong in a parent/bundle/receipt—only stable
IDs, revision/hash, count, and content-free references.

**Failure law, common to every slice.** `KernelRefused` remains a refusal.  The
closed adapter explicitly re-raises it rather than converting it to malformed
provider output (`services/inference_semantic_adapters.py:105-121`).  This is
not cosmetic: C1 proved that recording a route refusal while leaving a
background job immediately queued produced a CPU/SQLite spin, unbounded refusal
ledger, starvation, and false “processed” progress
(`assets/story-08-c1-checkpoint-counsel-round1.md:51-80`).  Thus a refusal
creates one terminal parent/route receipt, zero model child, and an honest
adopter disposition; it is never a provider retry, never silently retried in a
tight loop, and never shown as successful/local.  Known transient provider
outcomes may use the frozen `retry.background.standard` controller policy;
indeterminate dispatch stays terminal/unknown under the controller rather than
starting another physical call.

This is YOLO/single-user work: no new queue, taxonomic migration ceremony,
compatibility UI, profile synthesis, or backwards-compatibility theater.  The
ledger/receipt is the degradation surface; no new background-status glass is
introduced here.

## Inventory — actual remaining doors

The Phase-143 product-runner census names exactly these four entrances
(`tests/unit/test_phase143_inference_capability_census.py:172-212`).  All four
already pass through the old `InferenceRunner`, so they have an older admitted
parent/child receipt shape.  **None is router-adopted:** the four capability
IDs are present in the registry, but none is in
`ADOPTED_CAPABILITIES`/`EXECUTING_CAPABILITIES`, which causes a routed admission
to refuse today (`services/inference_adoption_service.py:41-70,153-161,195-203`),
and the only closed SERVICE policies currently registered are meeting queue,
wake, and parentless preload (`services/inference_service_route_policy.py:158-239`).

| Adopter / actual call site | Current authority path | Router state |
| --- | --- | --- |
| **Rails observer** — `holdspeak/rails_observer.py:268`, called from the enabled loop at `holdspeak/web_server.py:1088-1149` | The loop creates SERVICE `rails-observer` with basis `rails-observer:journal-only` (`web_server.py:1099-1103`). `build_profile_summarizer()` reads `Config.rails_observer.profile_id`, calls `resolve_placement(... profile_id or "this_machine")`, captures a deployment revision, then directly calls `broker.inference_runner.invoke` (`rails_observer.py:237-274`). | Unrouted. Its planned ID is `background.rails_summary` (`test_phase143_inference_capability_census.py:179-181`), but the direct resolver/profile pointer remains authority. |
| **Cadence draft** — `holdspeak/services/cadence_service.py:284`, reached only by `get_loop()` when `use_llm` is enabled (`cadence_service.py:177-209`) | This is not an autonomous brief/audit model loop: `run_now`, `brief`, `closeout`, and `audit` are deterministic (`cadence_service.py:65-81,167-175`). The sole model call is an authenticated caller’s next-action draft. It globally calls `resolve_placement(self._db)`, captures that target, starts `cadence.next-action-draft`, then directly invokes the Runner (`cadence_service.py:211-242,264-302`). | Unrouted. Its census ID is `background.cadence_draft` (`test_phase143_inference_capability_census.py:188-190`), but global placement chooses the model. |
| **Decision promotion draft** — `holdspeak/services/decision_lifecycle_service.py:81`, called only by the owner route `holdspeak/web/routes/decisions.py:75-78` | This is an owner gesture to draft an artifact from an already-accepted decision, not the meeting-decision-record creation path. The service requires OWNER, reads request `inference_target_id`/`this_machine`, resolves/captures it, starts `decision.promotion-draft`, and directly invokes the Runner (`decision_lifecycle_service.py:56-81`). | Unrouted. Its census ID is `decision.promotion_draft` (`test_phase143_inference_capability_census.py:191-193`); the request placement override remains authority. |
| **Delivery PR-review draft** — `holdspeak/web/routes/delivery_prs.py:252`, inside `api_delivery_pr_draft_review` (`delivery_prs.py:215-266`) | An authenticated delivery action reads body `inference_target_id`/`this_machine`, resolves/captures it, starts `delivery.pr-review-draft`, then directly invokes the Runner (`delivery_prs.py:239-265`). It drafts only; the prompt expressly says it must not claim posting/approval/merge (`delivery_prs.py:244-249`). | Unrouted. Its census ID is `delivery.pr_review_draft` (`test_phase143_inference_capability_census.py:209-211`); the request placement override remains authority. |

The registry and adapter groundwork is already declared, rather than needing new
capability names: all four definitions are revision 2 and use
`retry.background.standard` (`inference_capabilities.py:1044-1048,1074-1077`).
Their exact v2 semantic results are already closed: Rails returns
`{"summary": string}`; Cadence, decision promotion, and PR review each return
`{"draft": string}` (`inference_capabilities.py:942-953`; `services/inference_semantic_adapters.py:213-255`).

## Per-adopter cutover

### 1. Rails observer — actual background SERVICE work

- **Capability and principal.** Adopt `background.rails_summary@2`.  Register
  the one missing sealed policy, proposed as `rails-observer@1`: SERVICE
  identity `rails-observer`; fixed authority basis
  `rails-observer:journal-only`; parent kind `rails.observer-batch`; only
  `rails.observer-batch@1`, `inference.invoke@1`, and `inference.cancel@1`;
  capability-only assignment source; boundaries intersecting the capability.
  It must not inherit group/global authority.  This follows the closed-policy
  contract—SERVICE is default-deny and exact capability rows only
  (`inference_service_route_policy.py:1-8,33-70,98-155`).  Register the one
  new parent codec/operation name alongside the existing cadence, decision,
  and delivery parent kinds (`kernel/runtime.py:73-85,129-137`); do not reuse
  an unrelated parent kind.
- **Atomic freeze.** After `new_events()` yields a nonempty batch but before
  `summarize_batch()` calls a model, hash its canonical local rendering and use
  deterministic `rails-batch:{batch_sha}` command/invocation identities.
  Start one `rails.observer-batch` parent and one-member bundle with content-free
  `{event_batch_sha256, event_count, observer_config_source_sha256}` input.
  Stage the system/user prompt only under the frozen member; no Config/profile
  read is permitted after marker/bundle admission.  Reuse the current journal
  projection/materializer only after the elected result; make its note identity
  batch-hash derived so a restart can replay rather than duplicate a journal
  entry or egress.
- **Adapter, failure, egress.** Wrap the existing prompt leaf in
  `adapter_for_frozen_definition(... background.rails_summary ...)`; it yields
  exactly `{"summary": text}`.  A refusal/unavailable/invalid/unknown result
  writes the already-existing event-only journal form—`summarize_batch()` and
  `journal_body()` define that truthful degradation
  (`rails_observer.py:100-127`)—with the route/parent receipt reference.  There
  is no Rails queue and no retry loop.  A successful journal’s egress badge,
  and any receipt-facing placement, is the widest boundary across its frozen
  member route entries; a missing/corrupt member refuses instead of defaulting
  “local.”

### 2. Cadence — OWNER request-time draft, not scheduler authority

- **Capability and principal.** Adopt `background.cadence_draft@2` under the
  authenticated **OWNER** passed into `get_loop`; retain existing
  `cadence.next-action-draft` as the parent kind.  Do not fabricate a Cadence
  SERVICE principal: current code explicitly says request-time intelligence is
  caller authority, not scheduler authority (`cadence_service.py:211-220`).
- **Atomic freeze.** Once the loop and `loop_revision` are read, use a
  deterministic command/invocation identity from `(loop.id, loop_revision)` and
  atomically start its parent plus one `background.cadence_draft` route member.
  The content-free parent snapshot remains the existing loop ID/source/revision
  shape (`cadence_service.py:233-237`).  Only then stage the prompt and execute
  the frozen route through the controller; remove `resolve_placement()` and
  direct Runner execution from this new path.
- **Adapter, failure, egress.** The adapter returns `{"draft": text}`; feed
  `draft` to the existing `next_action_from_output()` materializer.  Refusal,
  unavailable route, no elected result, or off-contract draft returns the
  existing deterministic next action (`cadence_service.py:189-209,287-302`),
  while the receipt holds the reason.  It does not enqueue work or report that
  deterministic output as LLM-generated.  The `placement`/egress value comes
  from the frozen route’s widest leg, never the present global default.

### 3. Decision promotion — OWNER-initiated artifact draft

- **Capability and principal.** Adopt `decision.promotion_draft@2` under the
  authenticated **OWNER** that requested `/draft-with-model`; keep the existing
  `decision.promotion-draft` parent kind.  This is not a SERVICE migration and
  must not inherit a background service assignment.
- **Atomic freeze.** Validate/promote-read the decision first, then atomically
  start parent plus one route using deterministic identities from
  `(decision_id, decision.updated_at, normalized_artifact_type)`.  Parent input
  keeps only those identities/revisions, as the current parent does
  (`decision_lifecycle_service.py:73-78`); decision/rationale prompt bytes are
  staged only after route freeze.  The request’s target override has no role in
  this branch.
- **Adapter, failure, egress.** `adapter_for_frozen_definition()` returns exactly
  `{"draft": text}`.  The existing artifact materializer may persist only the
  elected draft.  On refusal/unavailable/unknown/invalid result, leave the
  accepted decision unchanged, create no artifact, and return a named draft
  refusal with the terminal receipt; it never reports a promoted artifact.  The
  returned inference placement/badge derives from frozen route legs.

### 4. Delivery PR review — OWNER-initiated review draft

- **Capability and principal.** Adopt `delivery.pr_review_draft@2` under the
  authenticated **OWNER** gesture that asks for the draft; retain
  `delivery.pr-review-draft` parent kind.  Phase E should make the route assert
  OWNER rather than relying on the current route’s bare
  `request.state.principal` pass-through (`delivery_prs.py:239,247`).
- **Atomic freeze.** Fetch and hash review material first.  Atomically start
  parent plus one route with deterministic identity
  `(source_id, number, material_revision, diff_sha256)`, preserving the current
  content-free parent evidence (`delivery_prs.py:243-249`).  Stage bounded
  linked-text/diff prompt bytes only after freeze.  A repeated request with the
  same material replays the route/receipt rather than sending a second PR diff.
- **Adapter, failure, egress.** The adapter yields exactly `{"draft": text}`;
  post-election materialization remains a review **draft**, never a post/approve/
  merge effect.  Refusal/unavailable/unknown/invalid result returns a named
  draft failure and receipt, leaves the PR untouched, and never makes a false
  review card.  Any returned placement/egress comes from the frozen route’s
  legs, not `body.inference_target_id`.

## Migration and authority posture

| Surface | Marker / migration | New-work refusal or unavailable result |
| --- | --- | --- |
| Rails | One minimal `rails-observer-route-assignments` family. Read the one saved `Config.rails_observer.profile_id`, write the exact `background.rails_summary` capability assignment and marker in one transaction only when it maps without guessing. No synthetic profile, download, readiness probe, or new table. | Append/retain the event-only journal plus receipt reference; do not spin, block rails observation, or invent a summary. |
| Cadence | **No marker.** `CadenceConfig.use_llm` is an enable flag, not a saved route pointer (`config/integrations.py:27-51`); current placement is the global resolver. Do not fabricate a migration/default assignment. New routed use needs an exact owner capability assignment. | Return the existing deterministic next action; loop read and cadence brief/audit remain usable. |
| Decision promotion | **No marker.** `payload.inference_target_id` is a per-request override, not saved migration source (`decision_lifecycle_service.py:71-73`). New work needs its exact owner capability assignment. | Keep the decision; create no artifact; return named refusal/receipt. |
| Delivery PR review | **No marker.** Body `inference_target_id` is likewise a transient request override (`delivery_prs.py:239-243`). New work needs its exact owner capability assignment. | Keep the PR unchanged; return named refusal/receipt and no review draft. |

Phase E may retain the legacy direct resolver/Runner branches as fenced v1
compatibility/read/replay code while migrated/new work uses the router.  **Phase
F, not E, deletes** the direct `resolve_placement` / RuntimeProfile / request
override authority and closes the routing-authority census.  No generic
“background migration” marker, schema-default assignment, profile synthesis,
or new migration table is justified.

## Smallest honest slices and focused proofs

1. **Rails bundle and sealed SERVICE policy.** Add the parent kind, exact
   service policy, one-member atomic bundle, deterministic batch replay, and
   event-only degradation.  Extend `tests/unit/test_rails_observer.py`,
   `tests/integration/test_rails_observer_live.py`,
   `tests/unit/test_phase143_inference_route_plans.py`,
   `tests/unit/test_phase143_inference_fallback_controller.py`, and
   `tests/unit/test_phase143_inference_capability_census.py`.  Prove policy
   default-deny/no group inheritance, assignment edit after freeze, one physical
   call/terminal receipt, refusal=no child, restart=no duplicate egress/note,
   and frozen-route—not-default—egress.
2. **Cadence owner draft.** Replace its global resolver/direct child with the
   one-member owner bundle and `{draft}` materializer.  Extend
   `tests/unit/test_residual_service_admission.py`,
   `tests/integration/test_cadence_routes.py`,
   `tests/unit/test_phase143_inference_route_plans.py`, and
   `tests/unit/test_phase143_inference_fallback_controller.py`.  Prove caller
   ownership, frozen assignment despite edit, deterministic fallback on refusal,
   no scheduler/service escalation, and no second child on unknown.
3. **Decision promotion.** Route the owner draft without changing decision
   lifecycle semantics.  Extend `tests/unit/test_decision_record_service.py`,
   `tests/unit/test_decision_records_routes.py`,
   `tests/unit/test_phase143_inference_route_plans.py`, and
   `tests/unit/test_phase143_inference_fallback_controller.py`.  Prove owner
   requirement, no request-target retarget, elected `{draft}` only, cancellation/
   refusal leaves no artifact, and durable receipt/egress truth.
4. **Delivery PR review.** Route the owner draft and preserve its strictly
   non-posting behavior.  Extend `tests/integration/test_delivery_campaign.py`,
   `tests/unit/test_delivery_read_model.py`, `tests/unit/test_one_path_spine.py`,
   `tests/unit/test_phase143_inference_route_plans.py`, and
   `tests/unit/test_phase143_inference_fallback_controller.py`.  Prove OWNER
   gate, diff-hash replay/no duplicate egress, assignment edit after freeze,
   `{draft}` validation, refusal/no false review, and frozen-route egress.

Every slice updates the exact Phase-143 runner/call-site census if a direct
Runner entrance disappears or the controller-owned entrance moves; the census
is intentionally literal and fail-closed (`tests/unit/test_phase143_inference_capability_census.py:54-57,557-580`).

## Questions for counsel (three only)

1. Rails has an explicit saved `profile_id` but historically treats blank as the
   `this_machine` sentinel (`config/integrations.py:82-102`; `rails_observer.py:253-256`).
   Ratify the proposed no-guess rule—migrate only a nonblank exact pointer and
   degrade a blank enabled observer—or permit that documented sentinel to become
   one exact visible capability assignment.
2. Ratify that Cadence’s sole real model call remains OWNER request-time work,
   with no new SERVICE policy for deterministic scheduler/brief/audit paths.  If
   autonomous Cadence drafting is wanted later, it needs a separately named
   capability, principal, bounded-delegation basis, parent kind, and receipt—not
   a quiet widening of this slice.
3. Ratify immediate new-work assignment authority for decision/delivery despite
   their legacy per-request target overrides: missing assignment honestly
   refuses, rather than Phase E synthesizing a default or preserving a parallel
   mutable override.  Phase F then removes the residual legacy code.

---

# Counsel ruling (Sol, 2026-08-24): RATIFY-WITH-AMENDMENTS

One capped design round. Architecture ratified (bundle/policy/controller
reuse; Rails one-member SERVICE bundle with batch-hash replay; three
OWNER request-time drafts; no marker for the owner drafts; Phase F owns
deletion; four-slice split). Question rulings: (1) blank Rails
`profile_id` = the documented `this_machine` sentinel — CONVERT it
exactly once (see amendment E1); (2) Cadence stays OWNER request-time
only — no SERVICE policy, no quiet widening; (3) decision/delivery get
immediate exact assignment authority — missing assignment refuses
honestly; a nonblank legacy override is rejected BY NAME. Sol's
substantive catch: `InferenceParentRouteBundleService.start()` resolves
policy before creating a parent shell, so a pre-route refusal today is
a thrown ValidationError with zero receipts — amendment E2 requires an
explicit refusal-recording seam. The three amendments below are
counsel's exact required text and are binding over any conflicting
statement above.

## Counsel amendments

### E1. Rails blank-sentinel continuity

For `rails-observer-route-assignments` only, blank
`Config.rails_observer.profile_id` has the documented meaning
`this_machine`; it is not an absent or ambiguous selector. In one
transaction, migration reads that saved sentinel, reuses or writes the
minimum owner-visible local Model Library profile and binding that
name the exact historically effective same-device deployment, writes
the exact `background.rails_summary` capability assignment, and writes
the family marker.

The conversion MUST NOT choose another model, add a fallback leg, add
cloud or remote consent, invent an endpoint or secret, download or
load a model, or probe a destination. If the exact saved same-device
deployment cannot be named without guessing, migration writes no
partial profile, binding, assignment, or marker and the enabled
observer writes its event-only journal with the named refusal receipt.
This narrow sentinel conversion supersedes Phase E's general
no-profile-synthesis sentence only for this exact saved local meaning.

### E2. Truthful refusal accounting

The statement that every refusal creates "zero model child" is
replaced by the following distinction.

A refusal before any route can be frozen—including missing exact
assignment, incompatible profile or binding, and denied SERVICE
policy—records exactly one content-free terminal adopter/parent
refusal receipt under the deterministic request identity. It creates
no bundle, route, execution, or model child.
`InferenceParentRouteBundleService.start()` currently performs this
preflight before creating its parent shell, so Phase E MUST add or
reuse an explicit refusal-recording seam; a thrown `ValidationError`,
debug log, or deterministic fallback without a receipt is
insufficient.

Once a route execution or physical attempt exists, its durable rows
are preserved. An attempt-time `KernelRefused`, permission denial,
invalid result, or provider disposition keeps its actual child/attempt
receipt and settles through the controller; it is never rewritten as
"zero child." Only dispositions expressly allowed by the frozen retry
policy may advance. Policy refusal is terminal, and dispatch
uncertainty remains terminal/unknown with no second physical call.

Every adopter applies its event-only journal, deterministic Cadence
action, no-artifact decision response, or no-review delivery response
only after the corresponding terminal refusal or route receipt is
durable.

### E3. Retired request overrides and focused proofs

For new routed decision-promotion and delivery-review requests,
`inference_target_id` is not routing authority. An absent or blank
field uses the exact OWNER capability assignment. A nonblank field
returns the named refusal `inference_request_target_override_retired`
with a terminal refusal receipt; it is neither honored nor silently
ignored. Existing stored request and receipt bytes remain readable.

Without adding a new slice, focused proof MUST cover:

- blank Rails sentinel conversion to one exact visible local
  assignment and marker;
- unmappable Rails sentinel producing event-only journal plus receipt
  and no partial migration;
- missing-assignment refusal for all four adopters producing one
  terminal receipt and zero route/model child;
- attempt-time refusal preserving the real child/attempt receipt;
- decision and delivery legacy target overrides neither retargeting
  nor disappearing silently.

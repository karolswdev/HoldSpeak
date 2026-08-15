# HS-131-07 design — Remaining service callers use one admitted invocation

**Status:** RATIFIED-AS-AMENDED (Sol, 2026-08-10) — the four amendments in the Sol ruling below are binding on implementation  
**Decision boundary:** migrate exactly Rails summary, Decision promotion, Delivery PR review, and voice resolution to HS-131-03's broker-owned `InferenceRunner`. Each actual provider dispatch is `inference.invoke@1`; domain work remains outside the runner and its projection cannot finalize before that child's terminal receipt.

## Context

The bounded census is the four direct seams in `rails_observer.py:237-256`, `services/decision_lifecycle_service.py:60-96`, `web/routes/delivery_prs.py:215-333`, and `voice_resolver.py:209-296` as supplied by `services/workbench_service.py:328-370`. They currently resolve mutable targets/build Intel or inject a direct prompt callable. Ask is the model: capture a deployment revision, hash a versioned `ServiceContract`, invoke the broker-owned runner, stage the domain result, then finalize only after its receipt (`services/ask_service.py:119-142`).

Use one generic kernel operation, `inference.invoke@1`, not four domain codecs. Its `ServiceContract` distinguishes the caller, payload version, and canonical hash while `InferenceInvokeCodec` preserves one boundary vocabulary (`kernel/inference_invoke.py:30-112`). This adds no domain branch to `InferenceRunner` or `broker.py`.

## 1. Rails observer summary

- Replace `build_profile_summarizer()`'s target resolution and `intel.run_prompt` (`rails_observer.py:237-256`) with a runner-backed summarizer. Its contract is `holdspeak.rails-summary@1`; canonical payload contains the fixed system prompt, rendered bounded events, temperature/max tokens, selected profile/target reference, and event-batch hash.
- The call is a root invocation: there is no user domain operation or native Rails lifecycle to invent, so `parent_operation_id=""`. The journal note is the staged `rails-journal` projection; its event batch and generated summary finalize only after the invocation receipt. A refused/failed/cancelled call retains the current honest event-only degraded entry, never a fabricated summary.
- The hub loop must pass an authenticated, narrow observer principal from its existing local-runtime identity (named `rails-observer` in receipt actor identity), with read/propose-only observer authority and `authority_basis=rails-observer:read-only`. It must not synthesize `OWNER`, use the selected profile as a principal, or name an owner as actor/delegator. The receipt therefore honestly records an ambient observer performing a read-only summary, not an owner action.
- Preserve both guardrails in the module header: no observer is enabled by migration, it still consumes events only, and its sole post-receipt write is a tagged note (`rails_observer.py:1-14,130-141`). A journal note is not Rails write authority; any action remains an existing actuator proposal.

## 2. Decision promotion draft

- Replace the direct Intel branch at `decision_lifecycle_service.py:79-89` with `holdspeak.decision-promotion-draft@1`. Its payload canonically includes immutable decision/meeting grounding revisions, normalized artifact type, prompt, and output limit. Capture the requested placement's deployment revision before forming `InvocationRequest`.
- Retain the existing decision-promotion lifecycle/native result record as the real `decision.promotion-draft@1` parent, opened with the authenticated owner route principal. The runner creates one `inference.invoke@1` child with that parent operation/capability; do not retain the present generic `inference.run@1` outer operation as a pretend domain parent.
- Stage `db.decisions.promote(... body_markdown=output, review_status="draft", model_assisted=True)` as the artifact-draft projection. The existing decision receipt closes the domain promotion and references the child operation, invocation ID, deployment revision, and child terminal receipt/outcome; it does not manufacture a second inference terminal receipt. Existing promotion validation, refusal, approval, and artifact contract remain unchanged.

## 3. Delivery PR-review draft

- Replace `intel.run_prompt` at `delivery_prs.py:293-298` with `holdspeak.delivery-pr-review@1`. Canonical payload is the source/PR identity, material revision, diff SHA-256, linked grounding revisions, review prompt, and token limit; the diff body is dispatched as payload, not copied into the admission journal.
- Retain the Delivery lifecycle/native review record as authenticated route-principal parent `delivery.pr-review-draft@1`, not the current generic `inference.run@1` placeholder at `:252-280`. Its admitted invocation child carries `parent_operation_id`; parent result metadata links the exact child receipt rather than duplicating it.
- Stage `persist_pr_review_artifact()` (`:303-311`) as the review-text/artifact projection. Only a succeeded child receipt permits finalization and the response's `artifact_id`; failure, refusal, cancellation, and indeterminate outcome persist no review draft and preserve the current classified error path.

## 4. Voice reference resolution

- Keep `voice_reference_resolve@1` as the existing authenticated proposal/session parent (`workbench_service.py:353-364`), including its existing arm/confirmation path. It remains a proposal: successful references never execute an armed effect.
- Replace only `run_prompt_fn` in `resolve_voice_references()` (`voice_resolver.py:255-278`) with a runner-backed callable rather than redesigning its parsing/retry API. Each actual retry is a separately admitted `inference.invoke@1` child of the same voice parent, contract `holdspeak.voice-reference-resolve@1`, and `attempt_ordinal` matching the resolver attempt. The contract payload contains transcript hash, bounded zone-catalog hash, prompt/retry index, selected resolver target, limits, and timeout.
- Resolve/capture the deployment revision once after the existing readiness check and pass it to that callable. Stage the final `ResolverResult`/resolution JSON as the request projection; return references only after the winning child receipt and projection finalize. Empty catalog/transcript stays the existing no-model success and creates no invocation child.
- The authenticated request principal remains actor on the voice parent and children. Remove the fallback `Principal(OWNER, "voice_resolver")`: absent principal is a refusal, not a silent elevation. The existing parent receipt records the child linkage; arming still occurs only in its existing confirmation flow.

## 5. Shared exact-revision dispatch and cancellation

`InferenceRunner.invoke()` is the sole provider gateway (`kernel/inference_runner.py:166-223`): it admits, claims, constructs the engine with `build_intel_for_revision`, dispatches, then writes one terminal child receipt. All four migrations use its broker-owned shared instance and `CanonicalPromptAdapter`, as Ask does (`ask_service.py:46-55`). `build_intel_for_revision()` consumes frozen revision fields for local, cloud, and mesh (`inference_targets.py:552-581`); no migrated path may call `resolve_inference_target`/`build_intel_for_target` after admission.

For mesh specifically, delete any relay-side target/profile/authority re-resolution from this path. The relay receives the admitted deployment revision/warrant and validates it; its adapter is built only from that revision's endpoint, model, node, and boundary. Local, cloud, and mesh therefore expose the same child receipt vocabulary and immutable revision reference.

No new cancel route is justified: these are short request/background calls with existing deadlines, and none exposes a durable caller-owned cancellation API. The runner watchdog and existing parent cancellation are sufficient. On cancellation races, the runner's terminal-receipt winner is authoritative (`inference_runner.py:72-165,198-255`); `ProjectionStager.finalize()` must adopt only that winner. Thus a late Rails note, promotion artifact, PR review, or voice JSON cannot publish after cancellation/indeterminate outcome. Existing parent cancellation, where present, must pass its parent context to the child so it fences new retry admission.

## Invariants

1. Every provider dispatch in the four-call census is exactly one admitted `inference.invoke@1`, identified by its versioned service contract and exact deployment revision.
2. Domain parents remain domain operations and link child receipts; they never stand in for the invocation or duplicate its terminal receipt.
3. Rails is opt-in, event-read-only, and observer-actor only; migration cannot confer owner or effect authority.
4. Voice references are proposals; receipt success does not bypass confirmation/arming.
5. No domain-specific condition enters `InferenceRunner` or `kernel/broker.py`; staged domain projections finalize only after the terminal receipt winner.

## Test matrix

| Acceptance criterion / invariant | Planned focused proof |
| --- | --- |
| Four census callers have no direct Intel execution | `tests/unit/test_intel_egress_invariant.py` plus focused Decision and Delivery lifecycle tests assert runner child cardinality and no `build_intel_for_target` path |
| Rails root provenance, off-by-default/read-only, receipt-gated note | `tests/integration/test_rails_observer_live.py` |
| Decision parent/linkage and draft finalization | focused Decision lifecycle test: child receipt precedes artifact; refusal/cancel has no artifact |
| Delivery parent/linkage and review persistence | focused Delivery PR-route test: immutable diff hash/revision and no artifact on non-success |
| Voice retries, proposal-only confirmation, no owner fallback | `tests/unit/test_voice_resolve.py` |
| Local/cloud/mesh exact admitted revision and shared vocabulary | `tests/unit/test_intel_egress_invariant.py`; one configured mesh integration execution when harness is available |
| Late cancellation cannot publish projection | focused runner/cardinality tests for all four projection publishers |

## Recorded notes

- **HS-131-10 fence finding — Cadence direct LLM:** `services/cadence_service.py:131` builds Intel directly through `_cadence_llm`. It is outside this finite census and is not migrated here. It blocks HS-131-10 closure until a charter amendment assigns an explicit owner story; do not silently expand HS-131-07.
- Recipe chat is already on the admitted path: `services/ask_service.py` identifies the established `InferenceRunner`/`InvocationRequest` pattern; implementation should grep the Recipe service only to confirm its existing migration, not duplicate it.
- Below the yolo bar unless a concrete failure appears: durable cancellation endpoints for these transient operations, cross-process observer identity rotation, and retry deduplication beyond the resolver's current bounded retry chain.

## Open questions for Sol

1. Ratify the narrow authenticated Rails observer principal/authority basis, and identify the exact runtime principal issuer if the existing hub identity has a canonical name different from `rails-observer`.
2. Ratify new real domain parent names `decision.promotion-draft@1` and `delivery.pr-review-draft@1`, replacing their current generic `inference.run@1` placeholders while retaining their native records.
3. Ratify runner-backed voice retries as one child per attempt under `voice_reference_resolve@1`, including refusal on a missing request principal rather than the current owner fallback.
4. Confirm whether an existing parent-cancellation hook already supplies `parent_context`; if not, add the minimal parent-to-child cancellation propagation outside the runner/broker.

## Sol ruling

**Verdict: RATIFY-AS-AMENDED.** The generic admitted-invocation spine is the
right design. Four amendments are required to prevent dishonest provenance,
child work escaping parent cancellation, retry-contract breakage, and
mesh-side silent retargeting.

### Amendments (binding)

1. **Create and inject an explicit non-owner `rails-observer` service
   principal at hub-loop startup, authorize it only for `inference.invoke@1`
   and the tagged journal projection, and record
   `authority_basis=rails-observer:journal-only` (not `:read-only`).**
   `build_profile_summarizer(profile_id)` receives no principal today, so
   the claimed existing runtime identity does not exist at that seam;
   "read-only" would be receipt-dishonest because the observer deliberately
   writes a journal note (while retaining no Rails mutation or owner
   authority).
2. **For every Decision, Delivery, and Voice child, claim the real domain
   parent first, retain its trusted `parent_context`, and pass that context
   to `InferenceRunner.invoke()` on every attempt, refusing when the context
   is absent or revoked.** `parent_operation_id` alone provides lineage but
   no cancellation authority; only a supplied `parent_context` selects
   `submit_trusted_child()` — the minimal mechanism preventing a new child
   or voice retry from escaping a cancelled parent.
3. **Implement the voice runner-backed callable so each attempt stages its
   raw output, waits for that child's terminal receipt, finalizes and
   returns the resulting string to the existing parser, maps deadline
   cancellation to `TimeoutError`, and maps other non-success outcomes to an
   exception.** The resolver expects a synchronous string-returning callable
   and owns parsing/retries; returning an outcome object or exposing
   pre-receipt output would respectively break retries or permit a
   late/dishonest resolution.
4. **Replace the mesh worker's own configured-provider resolution with a
   relay dispatch envelope carrying the admitted deployment revision and
   warrant, and have the worker validate that envelope and construct
   execution only from the frozen revision before dispatch.** The worker
   currently calls `build_configured_meeting_intel()` for its own
   resolution with no admitted-revision/warrant validation — silent
   retargeting under the new contract. The envelope is generic transport;
   no domain conditionals in kernel code, no warrants inside the hashed
   service payload.

### Key verifications from the ruling

- The voice owner-elevation fallback EXISTS at
  `services/workbench_service.py:354`
  (`principal or Principal(PrincipalKind.OWNER, "voice_resolver")`) —
  removal ratified; missing authentication refuses.
- The generic `inference.run@1` placeholder parents in Decision/Delivery
  pretend to be domain parents while naming inference — replacement with
  `decision.promotion-draft@1` / `delivery.pr-review-draft@1` ratified,
  provided their broker `decide()` hooks have NO native
  decision-accept/PR-approve/artifact-create semantics (execution
  authorization only).
- One generic `inference.invoke@1` + versioned ServiceContracts preferred
  over four domain codecs; parent codecs describe lifecycle only, never
  dispatch.
- No new cancel routes; runner terminal-receipt election + ProjectionStager
  suffice once Amendments 2 and 3 land.

### Open-question rulings

1. Rails principal: ratified as amended — explicitly issue `rails-observer`
   as a non-owner journal-only service principal at hub-loop startup.
2. Parent names ratified with no native approval side effects in decide().
3. Voice: one child per actual attempt, same authenticated request
   principal, missing principal refused, no OWNER fallback.
4. No automatic parent-cancellation hook exists in invoke(); implement the
   explicit parent-context propagation of Amendment 2.

### Sol recorded notes

- No cross-process Rails identity rotation or durable identity subsystem
  for this story.
- Retry dedup beyond the existing bounded three-attempt voice chain stays
  below the bar.
- Cadence remains recorded against HS-131-10; it must not expand this
  story.
- The mesh admission-context transport stays provider-neutral; no
  special-casing of the four domains in kernel code.

### Orchestrator disposition

All four amendments ADOPTED — each names a real-use defect class (dishonest
receipt provenance, cancellation escape, broken retry contract / late
publication, silent mesh retargeting), so none falls to the yolo bar as a
recorded note. Amendment 4 is the largest: it changes legacy mesh-worker
behavior ("whatever provider this node currently selects") by design — that
behavior is precisely the silent retargeting this phase exists to kill.

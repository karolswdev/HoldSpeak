# HS-131-07 — The remaining direct callers join the spine

- **Project:** holdspeak
- **Phase:** 131
- **Status:** done
- **Depends on:** HS-131-02, HS-131-03
- **Unblocks:** HS-131-10
- **Owner:** unassigned

## Problem

Issue #450 named five run families, but Article XI applies to every model call.
Rails summary, Decision promotion, Delivery review, and voice resolution use a
mix of direct calls and private lifecycle adapters. Some already produce a good
outer receipt; none should remain a second execution path once the shared runner
exists.

## Scope

### In

- Route Rails observer summarization in `holdspeak/rails_observer.py:237-256`
  through the runner while preserving its read-only, off-by-default authority
  semantics.
- Adapt Decision promotion in
  `holdspeak/services/decision_lifecycle_service.py:61-97` and Delivery PR
  review in `holdspeak/web/routes/delivery_prs.py:260-325` to the runner. Keep
  their existing parent lifecycle and native result records; remove the private
  model execution seam.
- Route Workbench voice resolution in
  `holdspeak/services/workbench_service.py:336-351` and
  `holdspeak/voice_resolver.py:213-274` through an invocation child of the
  authenticated voice proposal/session. Voice still arms; it does not gain new
  effect authority.
- The pre-charter execution census bounds this story to Rails observer,
  Decision promotion, Delivery PR review, voice resolution, and their
  local/cloud/mesh dispatch. A later fence finding is not silently absorbed: it
  blocks HS-131-10 and requires a charter amendment with an explicit owner
  story.
- Make local, cloud, and mesh execution all reach the same runner/gateway. Remote
  execution validates the admitted revision/warrant; it does not re-resolve
  target or authority.
- Preserve each domain's current approval, refusal, retry, and persistence
  semantics while replacing only the inference execution path.

### Out

- Meeting live/deferred/plugin calls, owned by HS-131-08.
- Dictation transcription/classification/rewrite calls, owned by HS-131-09.
- New Rails, Decision, Delivery, or voice product behavior.
- Reclassifying non-model effects as inference.

## Acceptance criteria

- [ ] Rails, Decision promotion, Delivery PR review, and voice resolution invoke
  models only through the runner.
- [ ] Existing parent/domain receipts reference invocation children rather than
  duplicating or replacing their terminal receipts.
- [ ] Rails remains read-only and off by default; migration cannot grant it a
  write effect or owner authority.
- [ ] Voice resolution has model-invocation evidence but still requires the
  existing confirmation path before any armed effect executes.
- [ ] Decision and Delivery keep their existing authority and native result
  contracts; no second approve/decide path appears.
- [ ] Local, cloud, and mesh provider calls execute the exact admitted deployment
  revision and produce the same boundary vocabulary.
- [ ] The bounded pre-charter finite-service list is fully migrated. Any new
  direct caller found later blocks closure and appears in an explicit charter
  amendment rather than expanding this story after the fact.
- [ ] No domain-specific conditional is added to the runner or kernel broker.

## Test plan

- Unit: focused Decision lifecycle, Delivery PR, voice resolver, egress, and
  runner cardinality tests; `uv run pytest -q tests/unit/test_voice_resolve.py tests/unit/test_intel_egress_invariant.py`.
- Integration: `uv run pytest -q tests/integration/test_rails_observer_live.py`
  plus one Decision promotion and Delivery review against the LAN model; one
  mesh execution if the configured mesh harness is available.
- Manual / device: exercise one call from each domain and query its parent,
  invocation child, deployment revision, and terminal receipt.

## Notes / open questions

A pre-existing outer lifecycle is retained only if it names a real domain
operation. It cannot be counted as the model invocation's child admission.

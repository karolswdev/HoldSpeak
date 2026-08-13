# HS-131-13 hostile verification — fix round

## Verdict

**RATIFY FOR STORY CLOSE**

No sustained realistic blocker remains under the requested yolo-mode bar. The two prior production defects are repaired without adding a service-specific branch to the generic runner.

## Fix-round integrity

- Verified supplied fix-round patch SHA-256:
  `e17575d4abb51d4e44128466babc11a0e1f849c94ce3e00b4ac8dbc5e05c1992`.
- Audit stayed in scratch-isolated `HOME`, `TMPDIR`, and pytest `--basetemp`; no real home database, network, stage, commit, push, or roadmap/evidence mutation was used.

## Sustained-blocker result

None.

### Frozen local construction now holds

`holdspeak/inference_targets.py` constructs the `this_machine` engine directly as `MeetingIntel(provider="local", model_path=<frozen revision path>)`. It no longer reaches `configured_meeting_intel`, `build_configured_meeting_intel`, `Config.load()`, or a mutable current model after the revision is captured.

The original production-path Cadence retarget reproduction now reports the frozen and actual engine paths as the same captured `A` path after mutable config was changed to `B`:

```text
frozen_revision_model_path= .../cadence-captured-A.gguf
actual_engine_model_path= .../cadence-captured-A.gguf
same= True
```

The repaired production regression test likewise uses the real revision-to-engine factory chain and asserts the constructor sees only `{"provider": "local", "model_path": model_a}` after config has changed to `model_b`.

A separate real-claim edge probe made `MeetingIntel`, the configured factory, and `Config.load` fatal. A frozen same-device revision with no `model_path` raised `KernelRefused("inference_local_deployment_model_unknown")` before any construction or mutable-config read. Through the real runner it became one terminal `refused` child, with zero construction and zero dispatch.

### Outer task cancellation now durably wins

`CadenceService._drafted_next_action` handles `asyncio.CancelledError` before its generic failure arm, calls the controller cancellation route, and re-raises the cancellation. The controller persists the parent cancellation, fences/signals the live child, and the registered `cadence-next-action` stager discard rule prevents late publication.

Both race orderings are exercised in `tests/unit/test_residual_service_admission.py`:

1. cancel while the provider thread is blocked, then release it;
2. cancel after the provider has already made a durable stage, then recover.

The original blocked-provider production reproduction now reports:

```text
request_task=cancelled
after_cancel_parent_receipts= [..., 'cancelled']
after_provider_child_receipts= [..., 'succeeded']
before_recovery_stages= [..., 'STAGED']
after_recovery_stages= [..., 'DISCARDED']
```

Thus the child preserves its honest provider receipt while the parent is honestly cancelled and neither normal finalization nor recovery can publish the draft.

The cancellation fallback was additionally exercised against real terminal parent receipts. For pre-existing `succeeded`, `failed`, `cancelled`, `refused`, and `indeterminate` receipts, a simulated cancellation-route exception left the existing outcome unchanged. The fallback receipt guard does not convert an already-terminal operation to `cancelled`.

## Architecture, deletion, census, and schema checks

- Cadence owns only prompt/domain shaping and staged projection; `InferenceRunner` remains domain-blind and has no Cadence branch.
- Cadence uses the authenticated request caller; no owner or scheduler principal is manufactured. The unauthenticated route remains deterministic with no provider construction, parent, or child.
- The Decisions route no longer holds an engine, `run_prompt` callable, or `model_generator` injection seam. The dormant Delivery `prepare_pr_review` helper is absent.
- `build_intel_for_target` has no symbol, import compatibility shim, or executable caller. `LEGACY_UNCONTEXTUAL` is mechanically pinned only to the residual mesh receiver scope owned later in the amendment wave.
- The census reports **134 classified sites**, including **38 named findings** and **zero unregistered**. This is the intended reduction from the owner package's 145/48 baseline: the 10 HS-131-13 finding pins (Cadence 2, Decisions 2, Delivery 1, retired legacy factory 5) are gone, along with the factory's final non-finding vocabulary site. Mutation coverage still emits exact `UNREGISTERED_MODEL_EXECUTION` messages for aliases, first-class callable references, literal `getattr` doors, and reintroduced Decisions seams.
- The focused schema/snapshot tests passed. The prior isolated v56-to-v57 replay reached schema version 57, included `cadence.next-action-draft`, and created its backup.

## Focused evidence read

All tests below ran against the patched worktree using scratch-isolated environment paths.

1. Core admission/census/context/spine/provenance/cardinality/deployment/schema selection:

```text
169 passed in 39.46s
one-path census: 134 sites {'gateway': 1, 'witness-mint': 2,
'gateway-binding': 1, 'allowlist': 68, 'seam': 24, 'finding': 38,
'unregistered': 0}
```

Log: `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13113-fix-core.log`

2. Every other modified unit-test rig, including Ask, recipes, Decisions, meeting deferred/live/plugin paths, egress, and web routes:

```text
176 passed in 56.46s
```

Log: `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13113-fix-broad-rig.log`

3. Direct real-claim/refusal and parent-fallback probe:

```text
missing_frozen_local=refused_by_named_reason_before_construction
cancel_fallback_preserves_prior_terminal=succeeded,failed,cancelled,refused,indeterminate
runner_missing_frozen_local=one_refused_child_zero_construction_zero_dispatch
```

Log: `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13113-fix-edges.log`

4. Original adversarial reproductions:

Log: `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13113-fix-original-repros.log`

## Recorded nonblocking observation

The generic runner deliberately normalizes all engine-factory `KernelRefused` exceptions to a terminal `refused` outcome without placing the reason in `InvocationOutcome.error` or the receipt. Therefore, the missing-path edge's named reason is present at the factory boundary, while the runner receipt is the established generic `refused` form. A current same-device target with no configured path is unavailable before Cadence can admit a parent, so this cannot silently retarget or dispatch a model; the direct persisted-revision probe confirmed zero construction/dispatch. This is a broader receipt-detail policy, not a realistic remaining HS-131-13 safety or integrity blocker.

# Phase 143 generated surface and fallback census

**Regenerated:** 2026-08-26 on `feat/hs143-13-assignments`. This is the executable companion to
`repository-census.md`: `tests/unit/test_phase143_surface_fallback_census.py`
fails when a new private selector, recovery helper, or browser routing-pointer
surface lacks a reviewed classification.

Story 143-07 adds `holdspeak/services/ask_service.py` as the controller-winner
application-projection owner; `_routed_projection` decorates an already elected
physical result and never selects or advances a route.

## Classification rule

Each surface/family below has **exactly one Phase 143 story** as its migration
owner.  “Fallback” is reserved for an advance to a different frozen model-route
leg.  It does not mean an owner pressing a button, queue rescheduling, lexical
output preservation, a provider dialect change, or a workflow label that carries
input forward.

**Story 143-10 convergence:** its execution services have no `_target` or
`_invoke` local selector helper. `fallbackOnDevice` and `retryThenQueue` are
boundary decode aliases only; the executable workflow vocabulary is `carry`,
`hold`, `skip`, or an explicit failure. The source scanner and the exact-empty
Swift executable-policy invariant remain fail-closed.

## Owner routing controls

| Surface/family | Current controls and source anchors | Current authority | One migration story |
|---|---|---|---|
| Profile library and credential identity | `holdspeak/services/profile_service.py`, `holdspeak/services/profile_key_service.py`, `holdspeak/intel/providers.py`, `holdspeak/inference_targets.py` | `ProfileRecord`, key slot, legacy profile factory | 143-03 |
| Model Library availability and acquisition | `holdspeak/services/{model_library_service,inference_acquisition_service,inference_setup_service}.py`, `holdspeak/web/routes/model_library.py`, `web/src/pages/cores/{ModelLibraryCore,modelLibrary}.ts*` | one server-owned availability projection and library commands; provider/profile adapters retain no assignment authority | 143-12 |
| Thoughts and Ask destination | `holdspeak/config/integrations.py`, `holdspeak/services/ask_service.py`, `holdspeak/services/inference_setup_service.py`, `web/src/desk/ask.ts`, `web/src/desk/store/dataSlice.ts` | legacy persisted migration input and remaining transport compatibility; Thought glass now reads canonical assignments | 143-07 |
| Dictation/rewrite/punctuation destination | `holdspeak/config/model.py`, `holdspeak/speech_session/plan.py`, `holdspeak/plugins/dictation/assembly.py`, `holdspeak/target_profile.py` | `dictation.runtime.profile_id` and typed runtime policy; Dictation glass now reads canonical assignments | 143-07 |
| Meetings destination and bound route evidence | one-time `holdspeak/config/meeting.py` migration input; `holdspeak/services/meeting_deferred_queue_binding.py`; `holdspeak/meeting_session/deferred_bound.py` | C1 parent/bundle members are the deferred execution authority; `MeetingIntelPlan` is display-only persisted history | 143-08 |
| Deferred meeting/background jobs | `holdspeak/intel_queue.py`, `holdspeak/services/meeting_intel_service.py`, `holdspeak/services/settings_service.py` | queue schedule/recovery controls | 143-08 |
| Workbench, Recipe, Agent and workflow placement | canonical `InferenceAssignmentService` / `RoutedInferenceCoordinator` / `InferenceParentRouteBundleService`; compatibility inputs in `holdspeak/services/{recipe_service,sequence_workflow_service,support,workbench_runner,workbench_service}.py`; listed web transports | frozen assignment/route/controller evidence; retired request fields refuse and legacy record writes translate once | 143-10 |
| HTTP/MCP/browser pointer transport and types | `holdspeak/mcp/`, `holdspeak/web/routes/`, `web/src/desk/{api,detail-types,store/types}.ts`, `web/src/pages/cores/core-types.ts` | transport/projection only; must not resolve a route | 143-11 |
| Assignment editor shell | `web/src/pages/cores/{ContextualAssignment,SettingsCore,AssignmentEditor,AssignmentModelChooser,assignmentExperience}.ts*` | canonical assignment summary/editor; Recipe and Workbench contextual subjects reuse it; Model Library remains availability-only | 143-13 |
| Generic route/failure law and physical attempts | `holdspeak/kernel/{inference_runner,projection_stager}.py`, `holdspeak/intel/engine.py` | runner physical attempt and provider compatibility seam | 143-06 |
| Baseline false positives/non-inference selectors | `holdspeak/desktop_presence.py`, `holdspeak/speaker_intel.py`, `holdspeak/plugins/dictation/builtin/project_rewriter.py` | renderer, speaker, and input selection—not model routing | 143-01 |

## Recovery mechanism census

| Mechanism | Anchors | Classification and truth | One migration story |
|---|---|---|---|
| Bound Meeting route members | `holdspeak/services/meeting_deferred_queue_binding.py`, `holdspeak/meeting_session/deferred_bound.py` | **true model-route fallback**: any ordered candidates are frozen in durable bundle evidence. No v1 plan is resolved or replayed after admission. | 143-08 |
| Generic same-leg/next-leg control | `holdspeak/kernel/inference_runner.py:_cancelled_before_retry`, `holdspeak/kernel/projection_stager.py:_retry_stage` | Controller-owned physical-attempt and receipt semantics. The future controller decides bounded retry versus a later frozen leg; no provider/engine loop may do so. | 143-06 |
| `max_tokens` dialect learning | `holdspeak/intel/engine.py:_compatibility_retry`, `holdspeak/kernel/provider_signals.py` | **provider dialect attempt**: a typed compatibility signal creates a distinct admitted child. It is neither a second model nor model-route fallback. | 143-06 |
| Dictation `response_format` dialect learning | `holdspeak/speech_session/provider.py`, `holdspeak/plugins/dictation/runtime_openai_compatible.py` | **provider dialect attempt**: retrying without `response_format` is a separately admitted classify child. It is not a model change. | 143-07 |
| Deferred meeting job backoff | `holdspeak/intel_queue.py:_compute_retry_delay_seconds`, `holdspeak/intel_queue.py:_retry_or_fail_job` | **scheduling retry**: a later queued job/parent, not another same-turn provider attempt or a model-route fallback. | 143-08 |
| Meeting recovery button | `holdspeak/services/meeting_intel_service.py:_retry`, `web/src/meetings/MeetingIntelRecovery.tsx` | **explicit owner retry**: an owner asks to recover retained meeting work. It cannot silently advance a model chain. | 143-08 |
| Thoughts/Ask “Try again” | `holdspeak/services/refinement_coordinator.py`, `holdspeak/services/ask_service.py`, `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx` | **explicit owner retry**: a new visible invocation/turn; preserve the old terminal receipt. | 143-07 |
| Dictation lexical recovery | `holdspeak/dictation_telemetry.py:_fallback_category`, `holdspeak/plugins/dictation/`, `holdspeak/web/routes/dictation/` | **lexical degradation**: deterministic retained words/rules when classifier or runtime fails. Never call it a profile/model fallback. | 143-07 |
| Dictation runner publication backstop | `holdspeak/dictation_runner.py` | **lexical degradation**: the original words are published through the admitted session fence after pipeline failure. This protects words; it does not try another model. | 143-07 |
| Runtime `auto` backend choice | `holdspeak/plugins/dictation/runtime.py`, `holdspeak/speech_session/plan.py` | Preflight runtime selection (for example, `auto` chooses `llama_cpp` when MLX is unavailable), not retry and not a route-leg fallback. The frozen plan records the resulting target. | 143-07 |
| Whisper preload / silent-audio load | `holdspeak/transcribe.py`, `holdspeak/speech_session/{session,transcription}.py`, `holdspeak/services/inference_adoption_service.py` | One P=1 MLX lifecycle route, derived from an exact frozen capability-only `speech.transcribe` assignment. Its frozen candidates/stages stop on cancellation, refusal, deadline, indeterminate disposition, or exhaustion; no warm selects another model or retries an unknown provider send. Faster-whisper remains constructor-inseparable and has no fictional preload. | 143-08 |
| Persisting a completed speech callback | `holdspeak/speech_session/fence.py` | Storage-delivery retry of the exact completed callback, not inference execution or route fallback. | 143-08 |
| Fully-adopted session validation carrier | `holdspeak/speech_session/session.py:_routed_session_validation_plan` | Inert validation/history `SpeechSessionPlan` for both-marker non-device sessions: no deployment legs, no resolver call, no route selection. The atomic bundle is the sole execution authority. | 143-08 |
| Endpoint-health refusal | `holdspeak/intel/endpoint_health.py`, `holdspeak/meeting_session/live_readiness.py` | Readiness/circuit-breaker refusal before egress. It can expose an already frozen meeting leg, but cannot synthesize a model fallback. | 143-08 |
| Python workflow `fallbackOnDevice` / `retryThenQueue` | `holdspeak/services/support.py` decode boundary; `holdspeak/services/sequence_workflow_service.py` canonical execution | **Python fake workflow label retired from execution**: saved aliases decode exactly once to `carry` / `hold`; Sequence/Workflow emits only truthful local dispositions and never `fell_back`. Neither selects another model nor queues work. | 143-10 |
| Swift WorkflowRunner legacy `fallbackOnDevice` / `retryThenQueue` wire values | `apple/Sources/RuntimeCore/Workbench/WorkflowRunner.swift` | **Swift dormant/client fallback retired in Story 06**: every model-backed step now makes at most one provider or mesh call. Source/UI actions are `hold`, `holdForRoute`, and `carry`; old raw values remain only so saved Blueprints decode unchanged. An injected legacy fallback is never called. | 143-06 |
| Swift BlueprintInterpreter legacy `fallbackOnDevice` / `retryThenQueue` wire values | `apple/Sources/RuntimeCore/Workbench/BlueprintInterpreter.swift` | **Swift dormant/client fallback retired in Story 06**: a failure either carries the exact input or stops after one call for higher-level routing. The interpreter neither retries nor calls an alternate provider. | 143-06 |

## Guarded private decisions

The test AST-walks all backend private functions whose names indicate fallback or
retry, plus route/profile/target/placement selectors with route evidence.  Every
current match is deliberately classified here; sources are grouped by the one
story that owns their migration.

| Story | Guarded backend anchors |
|---|---|
| 143-01 | `holdspeak/desktop_presence.py`, `holdspeak/plugins/dictation/builtin/project_rewriter.py`, `holdspeak/speaker_intel.py` |
| 143-03 | `holdspeak/commands/doctor.py`, `holdspeak/inference_targets.py`, `holdspeak/intel/engine.py`, `holdspeak/intel/providers.py`, `holdspeak/services/model_profile_service.py`, `holdspeak/services/profile_key_service.py`, `holdspeak/services/profile_service.py` |
| 143-04 | `holdspeak/services/inference_assignment_service.py` (canonical sparse resolver) |
| 143-05 | `holdspeak/services/inference_route_plan_service.py` (canonical immutable resolver, persistence, and reconstruction) |
| 143-06 | `holdspeak/services/inference_fallback_controller.py` (durable route-attempt settlement and exact receipt reconstruction) |
| 143-06 | `holdspeak/intel/engine.py`, `holdspeak/kernel/inference_runner.py`, `holdspeak/kernel/projection_stager.py` |
| 143-07 | `holdspeak/dictation_telemetry.py`, `holdspeak/plugins/dictation/assembly.py`, `holdspeak/plugins/dictation/builtin/project_rewriter.py`, `holdspeak/plugins/dictation/runtime_mlx.py`, `holdspeak/services/inference_setup_service.py`, `holdspeak/target_profile.py` |
| 143-08 | `holdspeak/intel_queue.py`, `holdspeak/meeting_session/intel_plan.py`, `holdspeak/services/{inference_adoption_service,meeting_intel_service}.py` |
| 143-10 | `holdspeak/delivery/factory_launch.py`, `holdspeak/services/recipe_service.py`, `holdspeak/services/sequence_workflow_service.py`, `holdspeak/services/support.py`, `holdspeak/services/workbench_runner.py` |
| 143-12 | `holdspeak/services/model_library_service.py`, `holdspeak/services/inference_acquisition_service.py`, `holdspeak/services/inference_setup_service.py`, `holdspeak/web/routes/primitives/profiles.py` (private-target side-door refusal) |

## Guarded web routing consumers

`tests/unit/test_phase143_surface_fallback_census.py` inventories every
production `web/src` TypeScript module containing a snake-case pointer,
camel-case selector (`inferenceTargetId`, `intelProfileId`, `profileId`, or
`resolverProfileId`), or an import/definition of `RunsOnPicker`.  A surface is
classified as `inference-route`, `display-transport`, or `unrelated`; only the
first category may participate in a future assignment migration.

| Classification | Surfaces | One migration story |
|---|---|---|
| inference-route | `web/src/desk/ask.ts`, `web/src/desk/store/dataSlice.ts` | 143-07; Thought and Dictation owner glass migrated to contextual canonical assignments |
| inference-route | `web/src/pages/cores/SettingsCore.tsx`, `web/src/pages/cores/AssignmentEditor.tsx`, `web/src/pages/cores/AssignmentModelChooser.tsx`, `web/src/pages/cores/assignmentExperience.ts` | 143-13 |
| display-transport | `web/src/desk/api.ts`, `web/src/desk/components/Pullout.tsx`, `web/src/desk/detail-types.ts`, `web/src/desk/infoContract.ts`, `web/src/desk/store/types.ts`, `web/src/lib/primitives.ts`, `web/src/pages/cores/core-types.ts` | 143-11 / 143-10 display contracts; no browser placement writer remains |
| display-transport | `web/src/pages/cores/ModelLibraryCore.tsx`, `web/src/pages/cores/modelLibrary.ts` | 143-12 availability transport; selection never writes an assignment pointer |
| unrelated | `web/src/desk/components/DeliveryBoard.tsx`, `web/src/desk/deliveryFactory.ts` | 143-01 |

Adding another production routing consumer—or a private selector/recovery
helper—fails the focused test until it is classified above and assigned exactly
one story. The guard does not grant runtime authority; it preserves the census
boundary until the target story implements its one-way migration.

The same test scans every Swift `case .fallbackOnDevice`,
`case .retryThenQueue`, and `policy.maxRetries` execution site. The live set is
now exactly zero; a synthetic rogue runner proves any reintroduced client-owned
fallback branch or retry loop fails closed. Legacy strings may exist only as
non-executing wire raw values.

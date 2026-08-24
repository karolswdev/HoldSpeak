# Phase 143 generated routing-authority census

**Generated baseline:** 2026-08-21 from production `holdspeak/**` anchors on
merged `main`. This is the checked-in review fixture for HSEGHS001HS104-143-01;
it records today's authority, not the intended Phase 143 design. Test coverage:
`tests/unit/test_phase143_routing_authority_census.py`.

**Story 143-07 delta (2026-08-22):** post-marker Ask/Thought execution no
longer reads request-time selectors or Config. Speech's routed adapter resolves
only the controller-reserved immutable `DeploymentRevision` named by the issued
dispatch context (`speech_session/provider.py`); that lookup is execution
evidence, not mutable placement authority.

**Story 143-08 Phase-F delta (2026-08-24):** Meeting v1 plan resolution,
legacy deferred admission, and direct-runner recovery are deleted. Persisted v1
plan bytes are display-only history; deferred execution reconstructs only a C1
parent and frozen route bundle.

## Classification vocabulary

| Classification | Meaning |
| --- | --- |
| mutable assignment pointer | A persisted or request-time selection that can choose a target after it is changed. It must have one migration owner. |
| immutable evidence | A frozen revision, receipt, or plan reference. It is execution proof, never a new routing selector. |
| display | A projection, diagnostic, or serialized explanation of an already-resolved choice. |
| credential/provider identity | Secret-slot, provider, endpoint, runtime, or readiness identity. It cannot become assignment authority. |
| unrelated | A different domain's use of “profile”, including target-application and agent-launch profiles. |
| legacy-delete | A compatibility writer or old fallback whose assignment effect must disappear, rather than be adapted as new authority. |

## Production site inventory

| Family | Production anchors | Classification | Migration story |
| --- | --- | --- | --- |
| ProfileRecord mutable destination fields | `holdspeak/services/profile_service.py:ProfileService`; `holdspeak/inference_targets.py:target_from_profile` | mutable assignment pointer | 143-03 |
| Deployment head selected by a future profile binding | `holdspeak/services/inference_acquisition_service.py:_activate`; `holdspeak/deployment_revisions.py:_artifact_revision_for_identity` | mutable assignment pointer | 143-03 |
| Thoughts and Ask default/request pointer | `holdspeak/config/integrations.py:ThoughtsConfig.inference_target_id`; `holdspeak/inference_targets.py:resolve_thought_placement`; `holdspeak/services/refinement_coordinator.py:_admission_claim`; `holdspeak/services/refinement_application_service.py:get_workbench`; `holdspeak/services/refinement_thought_service.py:_validate_current_admission_under_write_fence`; `holdspeak/services/ask_service.py:AskService.ask` | mutable assignment pointer | 143-07 |
| Writing and dictation runtime pointer | `holdspeak/config/model.py:LLMRuntimeConfig.profile_id`; `holdspeak/intel/providers.py:effective_dictation_llm`; `holdspeak/speech_session/plan.py:DictationSessionPlanResolver` | mutable assignment pointer | 143-07 |
| Meeting intelligence pointer and provider placement | Historical compatibility input remains visible at `holdspeak/config/meeting.py:MeetingConfig.intel_profile_id` and `holdspeak/intel/providers.py:effective_intel_cloud`; execution uses only `holdspeak/services/meeting_deferred_queue_binding.py:MeetingDeferredQueueBinder` and `holdspeak/meeting_session/deferred_bound.py:BoundDeferredIntelJob` | mutable assignment pointer | 143-08 |
| Recipe and agent default pointer | `holdspeak/db/models/__init__.py:RecipeRecord.profile_id`; `holdspeak/services/recipe_service.py:RecipeService._target`; `holdspeak/services/schedule_delegation.py:_terms`; `holdspeak/inference_targets.py:resolve_placement` | mutable assignment pointer | 143-10 |
| Workbench execution pointer | `holdspeak/db/models/workbench.py:WorkbenchRecord.profile_id`; `holdspeak/services/workbench_runner.py:WorkbenchRunner`; `holdspeak/services/workbench_service.py`; `holdspeak/deployment_revisions.py:resolve_workbench_deployment_revision` (raw SQLite snapshot) | mutable assignment pointer | 143-10 |
| Workbench voice-resolver pointer | `holdspeak/db/models/workbench.py:WorkbenchRecord.resolver_profile_id`; `holdspeak/services/workbench_service.py:resolve_voice_references` | mutable assignment pointer | 143-10 |
| Recipe, Sequence, and Workflow request placement override | `holdspeak/services/recipe_service.py:RecipeService.run`; `holdspeak/services/sequence_workflow_service.py:SequenceWorkflowService._target`; MCP Sequence adapters | mutable assignment pointer | 143-10 |
| Kernel `inference.run` requested target selector | `holdspeak/kernel/inference.py:InferenceInvokeCodec.decode/authorize`; `requested_target_id` is decoded at line 86 and resolved at line 103 | mutable assignment pointer | 143-10 |
| Decision and delivery request placement override | `holdspeak/services/decision_lifecycle_service.py:draft_promoted_with_model`; `holdspeak/web/routes/delivery_prs.py:api_delivery_pr_draft_review` | mutable assignment pointer | 143-08 |
| Rails observer background pointer | `holdspeak/config/integrations.py:RailsObserverConfig.profile_id`; `holdspeak/rails_observer.py:build_profile_summarizer`; `holdspeak/web_server.py` | mutable assignment pointer | 143-08 |
| Cadence background global resolver | `holdspeak/services/cadence_service.py:_drafted_next_action`; `holdspeak/inference_targets.py:resolve_placement` | mutable assignment pointer | 143-08 |
| Local model acquisition availability receipt | `holdspeak/services/inference_acquisition_service.py:_activate`; `holdspeak/services/inference_setup_service.py` | credential/provider identity | 143-03 |
| V1 profile and workbench sync payload | `holdspeak/services/sync_service.py:SYNC_REGISTRY`; `holdspeak/services/sync_service.py:_MERGEABLE`; `holdspeak/services/sync_service.py:pull` | mutable assignment pointer | 143-11 |
| Settings Thoughts and writing legacy pointer writers | `holdspeak/services/settings_service.py:SettingsService.update_settings`; dictation/thoughts pointer normalization | mutable assignment pointer | 143-07 |
| Settings meeting and background legacy pointer writers | `holdspeak/services/settings_service.py:SettingsService.update_settings`; meeting/rails pointer normalization | mutable assignment pointer | 143-08 |
| DeploymentRevision ID in runner, lease, and receipts | `holdspeak/deployment_revisions.py:resolve_deployment_revision`; `holdspeak/kernel/inference_runner.py`; `holdspeak/kernel/local_runtime_lease.py` | immutable evidence | — |
| Frozen meeting and speech plan entries | `holdspeak/meeting_session/intel_plan.py:decode_meeting_intel_plan_v1` is a display-only history decoder; `holdspeak/meeting_session/deferred_bound.py:BoundDeferredIntelJob` and `holdspeak/speech_session/plan.py` reconstruct immutable execution evidence | immutable evidence | — |
| InferenceTarget and placement response DTOs | `holdspeak/inference_targets.py:InferenceTarget.to_dict`; `holdspeak/services/ask_service.py:_ask_projection`; `holdspeak/services/recipe_service.py:_chat_projection` | display | — |
| Doctor, desk, and MCP destination views | `holdspeak/commands/doctor.py`; `holdspeak/services/desk_service.py`; `holdspeak/mcp/resources.py` | display | — |
| Endpoint/profile key slot and key custody | `holdspeak/intel/providers.py:profile_key_env`; `holdspeak/services/profile_key_service.py:ProfileKeyService`; `holdspeak/profile_key_store.py` | credential/provider identity | 143-03 |
| Provider/runtime/readiness facts | `holdspeak/inference_targets.py:DeploymentIdentity`; `holdspeak/intel/providers.py:resolve_intel_provider`; `holdspeak/services/profile_service.py:probe_inference_target` | credential/provider identity | 143-03 |
| Target-application profiles for dictation | `holdspeak/target_profile.py`; `holdspeak/config/meeting.py:target_profile_override`; `holdspeak/desktop_typing.py` | unrelated | — |
| MIR plugin-routing profile | `holdspeak/config/meeting.py:routing_profile`; `holdspeak/plugins/router.py`; `holdspeak/intel_queue.py` | unrelated | — |
| Delivery agent launch profile | `holdspeak/delivery/factory_launch.py`; `holdspeak/kernel/process_spawn.py` | unrelated | — |
| Legacy config endpoint migration | `holdspeak/config/core.py:migrate_legacy_endpoints`; legacy `intel_cloud_*` and `openai_compatible_*` fields | legacy-delete | 143-03 |
| Old dictation auto-placement fallback labels | `holdspeak/plugins/dictation/assembly.py` | legacy-delete | 143-07 |
| Old meeting auto-placement fallback labels | Legacy placement resolution and v1 plan construction are deleted; `holdspeak/meeting_session/intel_plan.py:decode_meeting_intel_plan_v1` is history-only | legacy-delete | 143-08 |

The migration-story column is deliberately singular for every mutable family.
Story 143-04 owns the common assignment store/resolver and seed migration.
Stories 143-07, 143-08, and 143-10 own removal of their product families'
legacy selectors; none may create a second authority while doing so.

## Machine-checked source equality

`test_phase143_routing_authority_census.py` parses every production Python AST
and requires exact equality with this ledger's source baseline. It deliberately
includes imports as well as calls: an imported resolver is a route authority
edge even if the physical call is conditional. The guard covers the execution
waist (`kernel/inference_invoke.py`, `kernel/inference_runner.py`) and its
projection revalidation (`kernel/projection_stager.py`) as immutable revision
evidence, never as a mutable selector.

| Source family | Exact observed production sites | Classification |
| --- | --- | --- |
| Public routing resolver definitions | `deployment_revisions.py:202,224`; `inference_targets.py:497,551,591`; `intel/providers.py:666` | resolver authority |
| Placement / deployment resolver imports and uses | `deployment_revisions.py:205,214`; `inference_targets.py:585,602`; `intel/__init__.py:60`; `intel/providers.py:193,235,337,864`; `kernel/inference.py:9,103`; `kernel/inference_invoke.py:10,92`; `kernel/inference_runner.py:7,317`; `kernel/projection_stager.py:133,134`; `rails_observer.py:249,255`; `services/ask_service.py:146,147`; `services/cadence_service.py:222,226`; `services/decision_lifecycle_service.py:67,71`; `services/inference_setup_service.py:23,184`; `services/model_profile_service.py:682,689`; `services/profile_service.py:131,132`; `services/recipe_service.py:130,131,173,174`; `services/schedule_delegation.py:9,18`; `services/sequence_workflow_service.py:31,33`; `services/settings_service.py:68,76`; `services/workbench_runner.py:30,31`; `services/workbench_service.py:167,171,378,379`; `speech_session/plan.py:452,461,611,620`; `web/routes/delivery_prs.py:234,241` | resolver authority |
| Thought direct resolver callers | `services/refinement_application_service.py:63,64,70,71`; `services/refinement_coordinator.py:222,223`; `services/refinement_thought_service.py:609,615` | mutable Thoughts pointer, 143-07 |
| Config/record mutable pointer attributes | `config/core.py:135,158`; `config/integrations.py:22,23`; `config/meeting.py:143,144`; `db/models/__init__.py:1095`; `db/models/workbench.py:139`; `services/inference_setup_service.py:181,603,604,608`; `services/settings_service.py:567,816`; `services/workbench_service.py:376,379,401,422,471` | mutable assignment pointer |
| Every `profile_id` attribute read | Exact AST baseline: 43 sites classified as 23 mutable assignment pointers, 13 display reads, 2 immutable profile/assignment proofs, and 5 credential/provider identity reads; no unclassified `profile_id` read is permitted. Routing reads include Config runtime, Recipe/Workbench/sequence, sync, plan, and Rails; DTO/doctor reads remain display; v2 profile hash reconstruction and assignment compatibility evidence are immutable; provider readiness remains identity. | semantic classification, fail-closed |
| Kernel `inference.run` target handoff | `kernel/inference.py:86,103,147` (`requested_target_id` decode, `resolve_inference_target`, receipt) | mutable request selector until Story 143-10 removes late routing; the receipt is immutable evidence afterward |

The guard's mutation fixture adds a new `resolve_late_inference_target` public
helper, the exact `requested_target_id` late read used by the current kernel,
and a public `profile_id` read beneath `kernel/inference.py`; all are rejected
until the source baseline and this ledger receive explicit review. This
prevents a late selector from being introduced under a neutral name after the
Phase 143 routing waist is adopted.

## Resolver and precedence ledger

| Resolver / writer | Current precedence or effect | Phase 143 treatment |
| --- | --- | --- |
| `resolve_placement` | invocation → workbench → recipe/agent → `this_machine` | 143-04 supplies canonical infrastructure only; 143-07/08/10 remove each consumer's selector and 143-05 freezes its result. |
| `resolve_thought_placement` | `Config.thoughts.inference_target_id` becomes the workbench tier | 143-07 migrates today's single `thought.interview` operation, whose result is a question-or-synthesis union; any independently assignable synthesis operation requires a distinct admitted call. |
| Meeting compatibility intake / bound deferred reconstruction | the saved `intel_profile_id` is consumed only by one-time assignment migration; the claimed queue row is reconstructed from a durable parent and route bundle | 143-08 deletes mutable placement resolution and retains a v1 display decoder only. |
| `effective_dictation_llm` / speech plan resolver | one runtime profile controls classify/rewrite/punctuate | 143-07 migrates typed writing/dictation capability assignments. |
| `RecipeService._target` | request override → Workbench → Recipe profile → global | 143-10 replaces the subject selector for agents/workbenches/recipes. |
| `resolve_workbench_deployment_revision` | re-reads workbench and recipe profile fields from one SQLite snapshot | 143-10 retires dual subject reads; 143-05 freezes the chosen deployment revision. |
| `WorkbenchService.resolve_voice_references` | `resolver_profile_id` directly chooses an invocation target | 143-10 migrates to `voice.reference_resolve`. |
| `schedule_delegation._terms` | resolves stored Workbench/Recipe pointers before scheduler delegation | 143-10 removes subject selector reads before delegated execution. |
| `SequenceWorkflowService._target` | accepts an `inference_target_id`/`requested_placement` body field | 143-10 adopts the canonical invocation override layer. |
| `DecisionLifecycleService.draft_promoted_with_model` and `api_delivery_pr_draft_review` | accept/request a target directly for background drafting | 143-08 migrates these request selectors with their background capabilities. |
| `build_profile_summarizer` | Rails profile or hard-coded `this_machine` | 143-08 migrates to `background.rails_summary`. |
| `CadenceService._drafted_next_action` | re-resolves the global target for bounded service inference | 143-08 migrates to `background.cadence_draft`. |
| `InferenceAcquisitionApplicationService._activate` | download/use-existing writes an artifact, deployment head, and availability receipt | 143-03 makes no Config, subject, or assignment mutation. |

## Profile authority and sync boundary

| ID | Current production seam | Treatment |
| --- | --- | --- |
| `PROFILE_SERVICE_OWNER_ENFORCEMENT` | `holdspeak/services/profile_service.py:ProfileService` now checks `PrincipalKind.OWNER` before every profile/target list, lookup, mutation, or probe. | Story 143-03 closed the former direct-service/HTTP/MCP discovery gap. |
| `PROFILE_SYNC_PATH_BEARING_SEAM` | `holdspeak/services/sync_service.py:SYNC_REGISTRY` syncs historical v1 `profile`; `_MERGEABLE["profiles"]` includes `model_file` and `base_url`; pull serializes profile rows. | Historical v1 remains the compatibility case. V2 profile revisions/bindings are hub-local and hostile import refuses; Story 143-11 owns retirement of the v1 path-bearing wire seam. |

## Legacy assignment ownership

Story 143-04 owns only the canonical assignment persistence, precedence, and
one-way migration infrastructure. It does **not** own product-family removals.
Story 143-03 separates profile/setup availability from assignment; 143-07 owns
Thoughts/Ask/writing; 143-08 owns meetings, speech, background, decision, and
delivery; and 143-10 owns Agents, Workbenches, Recipes, sequence/workflow, and
voice resolution. Sync migration (143-11) removes routing and path-bearing v2
state from the wire; it does not invent a remote assignment.

`SettingsService.update_settings` is the shared transport seam through which
the present Settings UI writes several product-family pointers. Story 143-13
replaces those controls with Assignment glass; Stories 143-07 and 143-08 remove
the corresponding Thoughts/writing and meeting/background pointer mutations
from the service contract. The UI never becomes a second assignment service.

# Phase 143 generated routing-authority census

**Regenerated:** 2026-08-25 from production `holdspeak/**` anchors on
`feat/hs143-10-placement-adoption`. This is the checked-in, fail-closed review
fixture for HSEGHS001HS104-143-01. Test coverage:
`tests/unit/test_phase143_routing_authority_census.py`.

**Story 143-10 convergence:** Recipe, Workbench, voice, Sequence, and Workflow
now admit through the canonical assignment/coordinator seam. Their retained
legacy fields are migration/write-through inputs and frozen-route projections,
not Python execution selectors. The exact-empty adopter fork scan rejects a
new resolver/import, `_target`/`_invoke`, or direct Runner entrance.

**Story 143-07 delta (2026-08-22):** post-marker Ask/Thought execution no
longer reads request-time selectors or Config. Speech's routed adapter resolves
only the controller-reserved immutable `DeploymentRevision` named by the issued
dispatch context (`speech_session/provider.py`); that lookup is execution
evidence, not mutable placement authority.

**Story 143-08 Phase-F delta (2026-08-24):** Meeting v1 plan resolution,
legacy deferred admission, and direct-runner recovery are deleted. Persisted v1
plan bytes are display-only history; deferred execution reconstructs only a C1
parent and frozen route bundle. Post-marker Settings hides/refuses Meeting and
Rails selectors; Rails recurrent execution derives provenance solely from its
frozen bundle. Fully adopted owner/wake speech never invokes the v1 resolver,
and text-entry egress reads the frozen provider routes even without a
transcription member.

## Classification vocabulary

| Classification | Meaning |
| --- | --- |
| mutable assignment pointer | A persisted or request-time selection that can choose a target after it is changed. It must have one migration owner. |
| immutable evidence | A frozen revision, receipt, or plan reference. It is execution proof, never a new routing selector. |
| display | A projection, diagnostic, or serialized explanation of an already-resolved choice. |
| credential/provider identity | Secret-slot, provider, endpoint, runtime, or readiness identity. It cannot become assignment authority. |
| unrelated | A different domain's use of “profile”, including target-application and agent-launch profiles. |
| legacy-delete | A compatibility writer or old fallback whose assignment effect must disappear, rather than be adapted as new authority. |
| migration source | Retained saved bytes consumed once by a named marker migration; never a Settings or runtime selector afterward. |
| refusal fence | A retained request field whose only lawful effect is a named pre-route refusal. |

## Phase F closure ledger

| Door/status | Post-F treatment | Evidence anchor |
| --- | --- | --- |
| D1–D5 eliminated | v1 Meeting planning, live execution, direct runner, and unbound recovery have no production entrance. | `MeetingDeferredQueueBinder` + `BoundDeferredIntelJob` reconstruct C1 evidence only. |
| D6 eliminated as authority; K3 retained | Meeting `intel_profile_id`/`intel_provider` remain saved migration bytes only before `meeting-route-assignments`; afterward GET omits and PATCH refuses them, with no placement projection. | `SettingsService` family marker gate. |
| D7 eliminated as authority; K3 retained | Rails `profile_id` remains startup migration evidence only before `rails-observer-route-assignments`; it is absent from subsequent settings/runtime provenance. | `build_profile_summarizer` receives no profile/config hash. |
| D8 closed | This ledger preserves eliminated, K-fenced, and other-story rows rather than deleting evidence cosmetically. | `test_phase143_routing_authority_census.py`. |
| K4–K7 retained | Partial-marker and paired-device speech retain the legacy plan/child path; both-marker owner/wake work uses an atomic bundle, and egress is routes-first. | `speech_session/session.py`, `speech_session/provider.py`. |
| K8 retained refusal | A nonblank Decision/delivery request target records `inference_request_target_override_retired`, with no route/bundle/child/provider. | Decision service and delivery HTTP proofs. |
| Other-story rows retained | Thoughts/writing (143-07), Recipes/Workbench (143-10), sync (143-11), and kernel entrances retain their owner rows. | Production inventory below. |

## Production site inventory

| Family | Production anchors | Classification | Migration story |
| --- | --- | --- | --- |
| ProfileRecord mutable destination fields | `holdspeak/services/profile_service.py:ProfileService`; `holdspeak/inference_targets.py:target_from_profile` | mutable assignment pointer | 143-03 |
| Deployment head selected by a future profile binding | `holdspeak/services/inference_acquisition_service.py:_activate`; `holdspeak/services/model_library_service.py:_ensure_provider_deployment`; `holdspeak/deployment_revisions.py:_artifact_revision_for_identity` | mutable assignment pointer | 143-03 |
| Thoughts and Ask default/request pointer | `holdspeak/config/integrations.py:ThoughtsConfig.inference_target_id`; `holdspeak/inference_targets.py:resolve_thought_placement`; `holdspeak/services/refinement_coordinator.py:_admission_claim`; `holdspeak/services/refinement_application_service.py:get_workbench`; `holdspeak/services/refinement_thought_service.py:_validate_current_admission_under_write_fence`; `holdspeak/services/ask_service.py:AskService.ask` | mutable assignment pointer | 143-07 |
| Writing and dictation runtime pointer | `holdspeak/config/model.py:LLMRuntimeConfig.profile_id`; `holdspeak/intel/providers.py:effective_dictation_llm`; `holdspeak/speech_session/plan.py:DictationSessionPlanResolver` | mutable assignment pointer | 143-07 |
| Meeting migration source | Saved `holdspeak/config/meeting.py:MeetingConfig.intel_profile_id` and `intel_provider` may be read exactly once by `RoutedInferenceCoordinator.migrate_meeting_route_assignments`; post-marker Settings hides/refuses them and execution uses only `MeetingDeferredQueueBinder` / `BoundDeferredIntelJob`. | migration source | 143-08 |
| Recipe legacy selector migration/write-through | `holdspeak/db/models/__init__.py:RecipeRecord.profile_id`; `holdspeak/services/recipe_service.py:_write_legacy_profile_compatibility`; canonical `RoutedInferenceCoordinator.admit` | migration source | 143-10 |
| Workbench legacy execution migration/write-through | `holdspeak/db/models/workbench.py:WorkbenchRecord.profile_id`; `holdspeak/services/workbench_runner.py:WorkbenchRunner`; canonical `InferenceParentRouteBundleService` | migration source | 143-10 |
| Workbench voice legacy migration/write-through | `holdspeak/db/models/workbench.py:WorkbenchRecord.resolver_profile_id`; `holdspeak/services/workbench_service.py:resolve_voice`; canonical `InferenceParentRouteBundleService` | migration source | 143-10 |
| Recipe, Sequence, and Workflow request placement fence | `holdspeak/services/recipe_service.py:RecipeService._reject_retired_selector`; `holdspeak/services/sequence_workflow_service.py:SequenceWorkflowService._reject_retired_selector` reject nonblank legacy request selectors before route freeze. | refusal fence | 143-10 |
| Kernel `inference.run` historical reader | `holdspeak/kernel/inference.py:InferenceRunCodec` refuses every new admission and retains only historical native/receipt projection. | display | 143-10 |
| Decision and delivery request target fence | `holdspeak/services/decision_lifecycle_service.py:draft_promoted_with_model`; `holdspeak/web/routes/delivery_prs.py:api_delivery_pr_draft_review` read a nonblank target only to refuse `inference_request_target_override_retired`. | refusal fence | 143-08 |
| Rails observer migration source | `holdspeak/config/integrations.py:RailsObserverConfig.profile_id` is consumed once by `migrate_rails_observer_route_assignments`; `build_profile_summarizer` and `web_server` receive no profile/config hash thereafter. | migration source | 143-08 |
| Cadence background global resolver | `holdspeak/services/cadence_service.py:_drafted_next_action`; `holdspeak/inference_targets.py:resolve_placement` | mutable assignment pointer | 143-08 |
| Local model acquisition availability receipt | `holdspeak/services/inference_acquisition_service.py:_activate`; `holdspeak/services/inference_setup_service.py` | credential/provider identity | 143-03 |
| V1 profile and workbench sync payload | `holdspeak/services/sync_service.py:SYNC_REGISTRY`; `holdspeak/services/sync_service.py:_MERGEABLE`; `holdspeak/services/sync_service.py:pull` | mutable assignment pointer | 143-11 |
| Settings Thoughts and writing legacy pointer writers | `holdspeak/services/settings_service.py:SettingsService.update_settings`; dictation/thoughts pointer normalization | mutable assignment pointer | 143-07 |
| Settings Meeting/Rails migration-source guard | `holdspeak/services/settings_service.py:SettingsService.update_settings`; pre-marker values normalize as saved migration evidence, while post-marker PATCH refuses and GET omits the selectors. | migration source | 143-08 |
| DeploymentRevision ID in runner, lease, and receipts | `holdspeak/deployment_revisions.py:resolve_deployment_revision`; `holdspeak/kernel/inference_runner.py`; `holdspeak/kernel/local_runtime_lease.py` | immutable evidence | — |
| Frozen meeting and speech plan entries | `holdspeak/meeting_session/intel_plan.py:decode_meeting_intel_plan_v1` is a display-only history decoder; `holdspeak/meeting_session/deferred_bound.py:BoundDeferredIntelJob` and `holdspeak/speech_session/plan.py` reconstruct immutable execution evidence | immutable evidence | — |
| InferenceTarget and placement response DTOs | `holdspeak/inference_targets.py:InferenceTarget.to_dict`; `holdspeak/services/ask_service.py:_ask_projection`; `holdspeak/services/recipe_service.py:_chat_projection` | display | — |
| Doctor, desk, and MCP destination views | `holdspeak/commands/doctor.py`; `holdspeak/services/desk_service.py`; `holdspeak/mcp/resources.py` | display | — |
| Endpoint/profile key slot and key custody | `holdspeak/intel/providers.py:profile_key_env`; `holdspeak/services/profile_key_service.py:ProfileKeyService`; `holdspeak/profile_key_store.py`; `holdspeak/services/model_library_service.py:_connect_provider` | credential/provider identity | 143-03 |
| Model Library provider replay/receipt ledger | `holdspeak/services/model_library_service.py:_provider_command`; `model_library_provider_commands` records nonsecret draft fingerprints and owner-safe receipts only. | credential/provider identity | 143-12 |
| Provider/runtime/readiness facts | `holdspeak/inference_targets.py:DeploymentIdentity`; `holdspeak/intel/providers.py:resolve_intel_provider`; `holdspeak/services/profile_service.py:probe_inference_target`; `holdspeak/services/model_library_service.py:_ensure_provider_readiness` | credential/provider identity | 143-03 |
| Target-application profiles for dictation | `holdspeak/target_profile.py`; `holdspeak/config/meeting.py:target_profile_override`; `holdspeak/desktop_typing.py` | unrelated | — |
| MIR plugin-routing profile | `holdspeak/config/meeting.py:routing_profile`; `holdspeak/plugins/router.py`; `holdspeak/intel_queue.py` | unrelated | — |
| Delivery agent launch profile | `holdspeak/delivery/factory_launch.py`; `holdspeak/kernel/process_spawn.py` | unrelated | — |
| Legacy config endpoint migration | `holdspeak/config/core.py:migrate_legacy_endpoints`; legacy `intel_cloud_*` and `openai_compatible_*` fields | legacy-delete | 143-03 |
| Old dictation auto-placement fallback labels | `holdspeak/plugins/dictation/assembly.py` | legacy-delete | 143-07 |
| Old meeting auto-placement fallback labels | Legacy placement resolution and v1 plan construction are eliminated; `holdspeak/meeting_session/intel_plan.py:decode_meeting_intel_plan_v1` is history-only. | immutable evidence | 143-08 |

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
| Public routing resolver definitions | `deployment_revisions.py:202,224`; `inference_targets.py:496,550,590`; `intel/providers.py:666` | resolver authority |
| Placement / deployment resolver imports and uses | Exact current AST baseline is enforced in `test_phase143_routing_authority_census.py`; F no longer has a Rails runtime resolver/config-provenance edge, while its pre-marker Meeting display compatibility helper remains marker-gated. | resolver authority / K3 compatibility |
| Thought direct resolver callers | `services/refinement_application_service.py:63,64,70,71`; `services/refinement_coordinator.py:309,310`; `services/refinement_thought_service.py:640,681` | mutable Thoughts pointer, 143-07 |
| Config/record routing-pointer attributes | `config/core.py:135,158`; `config/integrations.py:22,23`; `config/meeting.py:143,144`; `services/settings_service.py:636,885`; workbench records/services. The Meeting settings read is post-marker-gated; its retained config field is K3 evidence. | guarded pointer census |
| Every `profile_id` attribute read | Exact AST baseline: 33 sites classified as 9 mutable assignment pointers, 4 migration/write-through sources, 13 display reads, 2 immutable profile/assignment proofs, and 5 credential/provider identity reads; no unclassified `profile_id` read is permitted. | semantic classification, fail-closed |
| Retired `inference.run` admission | `kernel/inference.py:InferenceRunCodec.validate/authorize/admit` always refuse `inference_run_retired`; historical native and receipt projections remain readable without a target handoff. | retirement fence / historical display |

The guard's mutation fixture adds a new `resolve_late_inference_target` public
helper, a synthetic `requested_target_id` late read, and a public `profile_id`
read beneath `kernel/inference.py`; all are rejected until the source baseline
and this ledger receive explicit review. This prevents a late selector from
being introduced under a neutral name after the Phase 143 routing waist is
adopted.

## Retained source anchors

The exact guard also keeps these production seams visible by name:
`holdspeak/inference_targets.py:resolve_placement`,
`holdspeak/inference_targets.py:resolve_thought_placement`,
`holdspeak/intel/providers.py:effective_intel_cloud`,
`holdspeak/intel/providers.py:effective_dictation_llm`,
`holdspeak/meeting_session/intel_plan.py:decode_meeting_intel_plan_v1`,
`holdspeak/speech_session/plan.py:DictationSessionPlanResolver`,
`holdspeak/deployment_revisions.py:resolve_workbench_deployment_revision`,
`holdspeak/services/schedule_delegation.py:_terms`,
`holdspeak/services/sequence_workflow_service.py:SequenceWorkflowService._freeze_parent_routes`,
`holdspeak/services/decision_lifecycle_service.py:draft_promoted_with_model`,
`holdspeak/web/routes/delivery_prs.py:api_delivery_pr_draft_review`,
`holdspeak/services/cadence_service.py:_drafted_next_action`,
`holdspeak/services/settings_service.py:SettingsService.update_settings`, and
`holdspeak/services/inference_acquisition_service.py:_activate`.

## Resolver and precedence ledger

| Resolver / writer | Current precedence or effect | Phase 143 treatment |
| --- | --- | --- |
| `resolve_placement` | invocation → workbench → recipe/agent → `this_machine` | 143-04 supplies canonical infrastructure only; 143-07/08/10 remove each consumer's selector and 143-05 freezes its result. |
| `resolve_thought_placement` | `Config.thoughts.inference_target_id` becomes the workbench tier | 143-07 migrates today's single `thought.interview` operation, whose result is a question-or-synthesis union; any independently assignable synthesis operation requires a distinct admitted call. |
| Meeting compatibility intake / bound deferred reconstruction | the saved `intel_profile_id` is consumed only by one-time assignment migration; the claimed queue row is reconstructed from a durable parent and route bundle | 143-08 deletes mutable placement resolution and retains a v1 display decoder only; post-marker Settings omits/refuses the selector. |
| `effective_dictation_llm` / speech plan resolver | one runtime profile controls classify/rewrite/punctuate | 143-07 migrates typed writing/dictation capability assignments. |
| `RoutedInferenceCoordinator.admit` | exact recipe subject/capability assignment → immutable route/operation plan | Story 143-10 is the sole Python selection seam for Recipe run/chat. Retired request selectors refuse. |
| `InferenceParentRouteBundleService` | exact Workbench subject/capability assignment → immutable parent route bundle | Workbench item and memory children consume the frozen member; they do not re-read Workbench/Recipe pointers. |
| `WorkbenchService.resolve_voice` | `voice.reference_resolve` assignment → immutable parent/bundle route | Voice consumes a controller reservation and projects only frozen egress evidence. |
| `schedule_delegation._terms` | enable-time frozen route terms | Story 143-10 persists the admitted route at enablement; fire-time execution never selects current placement. |
| `SequenceWorkflowService._freeze_parent_routes` / `_reject_retired_selector` | freezes one canonical route per Sequence step or Workflow node at parent admission; nonblank `inference_target_id`/`requested_placement` is refused before routing. | 143-10 removes local target selection and executes only admitted frozen child routes. |
| `DecisionLifecycleService.draft_promoted_with_model` and `api_delivery_pr_draft_review` | accept/request a target directly for background drafting | 143-08 migrates these request selectors with their background capabilities. |
| `build_profile_summarizer` | exact `background.rails_summary` assignment → frozen parent/bundle route | 143-08 retains no profile or `this_machine` input after the Rails marker. |
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

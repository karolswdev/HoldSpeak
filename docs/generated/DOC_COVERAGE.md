# Philo documentation coverage

<!-- GENERATED FILE: scripts/check_doc_coverage.py -->

Source snapshot: `675401a857b85336d4acaa8c65383dfc9636e4c8`.

The report keeps path presence, inspected assertions and executed tests separate.
A record is partially evidenced when one same-row assertion has a recorded passing test; this does not certify the whole capability.
Documentation paths are classified by file name; a path does not establish semantic coverage.

Missing shards: **none**.
Validation errors at generation: **0**.

| Measure | Present / total or count |
| --- | ---: |
| Source paths | 252 / 252 |
| Test paths | 191 / 191 |
| Documentation paths | 221 / 221 |
| Assertions inspected | 191 |
| Tests executed | 163 |
| Records with an executed assertion | 73 |
| Semantic records unresolved | 74 |

## Documentation classes

| Class | Existing linked paths |
| --- | ---: |
| api | 0 |
| operational | 65 |
| security | 19 |

## Record coverage

| ID | Kind | Sources | Tests | Assertions | Executed | Docs | Semantics |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `runtime.kernel_admit` | capabilities | 3/3 | 2/2 | 2 | 2 | 1 | partially_evidenced |
| `runtime.kernel_recover` | capabilities | 3/3 | 3/3 | 3 | 2 | 1 | partially_evidenced |
| `runtime.inference_attempt` | capabilities | 4/4 | 3/3 | 3 | 3 | 1 | partially_evidenced |
| `authority.principal_routes` | capabilities | 3/3 | 3/3 | 3 | 3 | 2 | partially_evidenced |
| `authority.policy_resolution` | capabilities | 3/3 | 3/3 | 3 | 3 | 2 | partially_evidenced |
| `storage.sqlite_reconcile` | capabilities | 3/3 | 4/4 | 4 | 4 | 0 | partially_evidenced |
| `storage.backup_restore` | capabilities | 2/2 | 2/2 | 2 | 2 | 1 | partially_evidenced |
| `operations.doctor` | capabilities | 3/3 | 0/0 | 0 | 0 | 2 | unresolved |
| `negative.kernel_content_exclusion` | capabilities | 3/3 | 3/3 | 3 | 3 | 1 | partially_evidenced |
| `negative.authority.agent_no_decide` | capabilities | 2/2 | 2/2 | 2 | 2 | 2 | partially_evidenced |
| `negative.storage_preserve_unknown_tables` | capabilities | 2/2 | 2/2 | 2 | 2 | 1 | partially_evidenced |
| `voice.capture` | capabilities | 2/2 | 1/1 | 1 | 1 | 1 | partially_evidenced |
| `voice.transcribe` | capabilities | 3/3 | 2/2 | 2 | 2 | 2 | partially_evidenced |
| `voice.command_dispatch` | capabilities | 1/1 | 1/1 | 1 | 1 | 1 | partially_evidenced |
| `voice.dictation_pipeline` | capabilities | 3/3 | 2/2 | 2 | 2 | 1 | partially_evidenced |
| `voice.delivery` | capabilities | 2/2 | 3/3 | 3 | 3 | 1 | partially_evidenced |
| `meeting.capture` | capabilities | 3/3 | 2/2 | 2 | 2 | 1 | partially_evidenced |
| `meeting.import` | capabilities | 2/2 | 3/3 | 3 | 3 | 1 | partially_evidenced |
| `meeting.intelligence` | capabilities | 5/5 | 8/8 | 8 | 8 | 0 | partially_evidenced |
| `meeting.aftercare` | capabilities | 2/2 | 3/3 | 3 | 3 | 0 | partially_evidenced |
| `model.registry` | capabilities | 2/2 | 1/1 | 1 | 1 | 1 | partially_evidenced |
| `model.assignment` | capabilities | 5/5 | 2/2 | 2 | 2 | 1 | partially_evidenced |
| `model.route_plan` | capabilities | 3/3 | 2/2 | 2 | 2 | 2 | partially_evidenced |
| `model.execution` | capabilities | 3/3 | 3/3 | 3 | 3 | 2 | partially_evidenced |
| `model.destination_readiness` | capabilities | 2/2 | 3/3 | 3 | 3 | 1 | partially_evidenced |
| `model.cancel_receipts` | capabilities | 3/3 | 2/2 | 2 | 2 | 2 | partially_evidenced |
| `voice.correction_memory` | capabilities | 1/1 | 1/1 | 1 | 1 | 1 | partially_evidenced |
| `voice.replay` | capabilities | 1/1 | 2/2 | 2 | 2 | 1 | partially_evidenced |
| `voice.learning_digest` | capabilities | 1/1 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `voice.prebrief_selection` | capabilities | 1/1 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `voice.symbol_settings` | capabilities | 1/1 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `voice.language_settings` | capabilities | 1/1 | 1/1 | 1 | 0 | 0 | unresolved |
| `voice.wake` | capabilities | 1/1 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `voice.browser_remote_dictation` | capabilities | 2/2 | 2/2 | 2 | 2 | 2 | partially_evidenced |
| `meeting.decision_lifecycle` | capabilities | 3/3 | 8/8 | 8 | 8 | 0 | partially_evidenced |
| `meeting.action_lifecycle` | capabilities | 1/1 | 1/1 | 1 | 1 | 0 | partially_evidenced |
| `model.download` | capabilities | 1/1 | 2/2 | 2 | 2 | 1 | partially_evidenced |
| `model.inventory` | capabilities | 2/2 | 2/2 | 2 | 2 | 1 | partially_evidenced |
| `meeting.plugin.requirements_extractor` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.action_owner_enforcer` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.mermaid_architecture` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.adr_drafter` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.milestone_planner` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.dependency_mapper` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.scope_guard` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.customer_signal_extractor` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.incident_timeline` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.risk_heatmap` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.stakeholder_update_drafter` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.runbook_delta` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.decision_announcement_drafter` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `meeting.plugin.decision_capture` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `desk.open` | capabilities | 3/3 | 1/1 | 1 | 0 | 1 | unresolved |
| `desk.arrange` | capabilities | 2/2 | 2/2 | 2 | 0 | 1 | unresolved |
| `desk.inspect` | capabilities | 2/2 | 2/2 | 2 | 0 | 0 | unresolved |
| `desk.execute` | capabilities | 2/2 | 2/2 | 2 | 0 | 0 | unresolved |
| `desk.drop` | capabilities | 2/2 | 2/2 | 2 | 0 | 0 | unresolved |
| `desk.persist` | capabilities | 2/2 | 1/1 | 1 | 0 | 0 | unresolved |
| `desk.runtime` | capabilities | 2/2 | 2/2 | 2 | 0 | 1 | unresolved |
| `desk.native_host` | capabilities | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `agents.thread_persistent` | capabilities | 3/3 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `agents.thread_tool_loop` | capabilities | 3/3 | 3/3 | 3 | 0 | 0 | unresolved |
| `agents.interview` | capabilities | 3/3 | 3/3 | 3 | 3 | 0 | partially_evidenced |
| `agents.mcp_http` | capabilities | 3/3 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `knowledge.grounding` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `knowledge.memory_search` | capabilities | 3/3 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `workflows.linear_run` | capabilities | 2/2 | 3/3 | 3 | 3 | 0 | partially_evidenced |
| `coder.observation` | capabilities | 3/3 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `coder.reply_and_draft` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `coder.gate` | capabilities | 3/3 | 4/4 | 4 | 4 | 0 | partially_evidenced |
| `integration.activity_connectors` | capabilities | 4/4 | 3/3 | 3 | 3 | 0 | partially_evidenced |
| `integration.github_readonly` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `integration.jira_confluence_calendar` | capabilities | 3/3 | 3/3 | 3 | 2 | 0 | partially_evidenced |
| `integration.actuators` | capabilities | 3/3 | 3/3 | 3 | 3 | 0 | partially_evidenced |
| `companion.ipad_client` | capabilities | 3/3 | 2/2 | 2 | 0 | 0 | unresolved |
| `companion.aipi_audio_control` | capabilities | 3/3 | 2/2 | 2 | 0 | 0 | unresolved |
| `companion.qlippy_presence` | capabilities | 2/2 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `runtime.kernel` | components | 2/2 | 0/0 | 0 | 0 | 0 | unresolved |
| `runtime.inference` | components | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `authority.edge` | components | 1/1 | 0/0 | 0 | 0 | 2 | unresolved |
| `storage.sqlite` | components | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `operations.doctor` | components | 1/1 | 0/0 | 0 | 0 | 2 | unresolved |
| `voice.speech_session` | components | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `voice.dictation_runner` | components | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `meeting.session` | components | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `meeting.plugin_host` | components | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `model.capability_registry` | components | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `model.assignment_service` | components | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `model.route_execution` | components | 1/1 | 0/0 | 0 | 0 | 2 | unresolved |
| `model.destination_resolver` | components | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `desk.shell` | components | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `desk.world` | components | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `desk.window` | components | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `desk.verb_registry` | components | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `surface.library` | components | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `desk.runtime` | components | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `runtime.sqlite` | integrations | 1/1 | 2/2 | 2 | 2 | 0 | partially_evidenced |
| `runtime.provider_routes` | integrations | 1/1 | 2/2 | 2 | 2 | 2 | partially_evidenced |
| `operations.remote_health` | integrations | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `voice.to_model` | integrations | 1/1 | 1/1 | 1 | 1 | 2 | partially_evidenced |
| `meeting.to_model` | integrations | 1/1 | 1/1 | 1 | 1 | 0 | partially_evidenced |
| `model.to_destination` | integrations | 1/1 | 1/1 | 1 | 1 | 1 | partially_evidenced |
| `meeting.external_actuators` | integrations | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `desk.api` | integrations | 1/1 | 1/1 | 1 | 0 | 1 | unresolved |
| `desk.runtime_bus` | integrations | 1/1 | 1/1 | 1 | 0 | 1 | unresolved |
| `desk.local_workspace` | integrations | 1/1 | 1/1 | 1 | 0 | 0 | unresolved |
| `desk.native_future` | integrations | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `integration.connector_registry` | integrations | 1/1 | 1/1 | 1 | 1 | 0 | partially_evidenced |
| `integration.github_read` | integrations | 1/1 | 1/1 | 1 | 1 | 0 | partially_evidenced |
| `integration.jira_confluence_read` | integrations | 2/2 | 1/1 | 1 | 0 | 0 | unresolved |
| `integration.calendar_local` | integrations | 1/1 | 1/1 | 1 | 1 | 0 | partially_evidenced |
| `integration.actuator_external` | integrations | 1/1 | 1/1 | 1 | 1 | 0 | partially_evidenced |
| `integration.ipad_hub` | integrations | 1/1 | 1/1 | 1 | 0 | 0 | unresolved |
| `integration.aipi_bridge` | integrations | 1/1 | 1/1 | 1 | 0 | 0 | unresolved |
| `domain.meeting` | domain_model | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `domain.actuator_proposal` | domain_model | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `domain.kernel_operation` | domain_model | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `domain.process_view` | domain_model | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `domain.inference_attempt` | domain_model | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `voice.speech_session_plan` | domain_model | 1/1 | 0/0 | 0 | 0 | 2 | unresolved |
| `meeting.meeting_state` | domain_model | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `meeting.plugin_run` | domain_model | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `meeting.artifact_lineage` | domain_model | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `model.runtime_profile` | domain_model | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `model.inference_assignment` | domain_model | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `model.route_execution` | domain_model | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `desk.world_object` | domain_model | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `desk.window_state` | domain_model | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `desk.verb` | domain_model | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `desk.receipt` | domain_model | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `boundary.edge_to_kernel` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 2 | unresolved |
| `boundary.kernel_to_executor` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `boundary.executor_to_provider` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 2 | unresolved |
| `voice.local_capture_to_transcription` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `meeting.capture_to_intelligence` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `model.local_boundary` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `model.remote_boundary` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 2 | unresolved |
| `model.secret_boundary` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 2 | unresolved |
| `meeting.actuator_boundary` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `desk.browser_to_api` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `desk.browser_to_runtime` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 1 | unresolved |
| `desk.browser_to_storage` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `desk.browser_to_future_host` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `trust.thread_model` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `trust.connector_runtime` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `trust.actuator_egress` | trust_boundaries | 1/1 | 0/0 | 0 | 0 | 0 | unresolved |
| `trust.companion_hub` | trust_boundaries | 2/2 | 0/0 | 0 | 0 | 0 | unresolved |

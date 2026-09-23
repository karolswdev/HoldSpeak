# Capabilities

<!-- GENERATED FILE: scripts/generate_capability_docs.py -->

Source snapshot: `675401a857b85336d4acaa8c65383dfc9636e4c8`.

This catalogue is generated from the Philo metadata shards. Status, evidence and release availability are separate fields.
Missing shards: **none**.

| Capability | Name | Purpose | Status | Exposure | Evidence | Owner observed | Egress |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `runtime.kernel_admit` | Admit bounded operation | Turn a declared request into an idempotent, authority-bound operation record. | experimental | integration | source_and_assertions_inspected | no | local |
| `runtime.kernel_recover` | Recover runtime work | Resolve interrupted parent, liveness and publication state after startup. | experimental | operator | source_and_assertions_inspected | no | local |
| `runtime.inference_attempt` | Run one physical inference attempt | Bind one provider attempt to a deployment revision, route boundary and receipt. | experimental | integration | source_and_assertions_inspected | no | possible |
| `authority.principal_routes` | Derive principals and route rights | Authenticate owner, agent and node callers and apply route-specific rights. | experimental | integration | source_and_assertions_inspected | no | local |
| `authority.policy_resolution` | Resolve operation control mode | Evaluate hard invariants, grants, control mode and feature defaults for a concrete effect. | experimental | user | source_and_assertions_inspected | no | local |
| `storage.sqlite_reconcile` | Reconcile SQLite shape | Bring an existing database toward the declared additive schema shape on open. | experimental | operator | source_and_assertions_inspected | no | local |
| `storage.backup_restore` | Back up and restore the database | Create a timestamped SQLite backup and safely replace the database from a validated backup. | experimental | operator | source_and_assertions_inspected | no | local |
| `operations.doctor` | Run operator diagnostics | Report environment, database, connector, authority and host readiness with actionable fixes. | experimental | operator | source_inspected | no | possible |
| `negative.kernel_content_exclusion` | Reject named stream-content keys in generic kernel material | Reject the named audio, PCM and token keys recursively; this is not semantic secret or prompt classification. | internal | internal | source_and_assertions_inspected | no | local |
| `negative.authority.agent_no_decide` | Deny agent decision and posture authority | Keep agent credentials limited to their submit/read/usage/self-revoke scope. | internal | internal | source_and_assertions_inspected | no | local |
| `negative.storage_preserve_unknown_tables` | Preserve unknown tables during general reconciliation | Retain unrecognized tables and their rows during the general shape repair. | internal | internal | source_and_assertions_inspected | no | local |
| `voice.capture` | Voice capture | Admit an owner speech session and collect an utterance for processing. | experimental | user | source_and_assertions_inspected | no | local |
| `voice.transcribe` | Speech transcription | Turn admitted local speech audio into a transcript. | experimental | user | source_and_assertions_inspected | no | local |
| `voice.command_dispatch` | Voice command dispatch | Match a complete configured utterance and invoke its configured voice-command connector. | experimental | user | source_and_assertions_inspected | no | possible |
| `voice.dictation_pipeline` | Dictation processing pipeline | Apply configured intent, project rewrite, and knowledge enrichment stages while preserving text on ordinary failure. | experimental | user | source_and_assertions_inspected | no | possible |
| `voice.delivery` | Dictation delivery | Commit processed text to preview, focused input, or an admitted agent destination under one operation policy. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.capture` | Meeting capture | Persist a meeting before capture, transcribe live audio, checkpoint segments, and hand off a final record. | experimental | user | source_and_assertions_inspected | no | local |
| `meeting.import` | Meeting import | Turn audio or a transcript file into a normal persisted meeting that can be searched, exported, and analyzed. | experimental | user | tests_executed | no | possible |
| `meeting.intelligence` | Meeting intelligence chain | Summarize a saved meeting and retain its summary, route receipt, and analysis artifacts. | experimental | user | tests_executed | no | possible |
| `meeting.aftercare` | Meeting aftercare | Compare current and previous meeting artifacts and return read-only decisions, actions, closures, and provenance. | experimental | user | source_and_assertions_inspected | no | local |
| `model.registry` | Inference capability registry | Define canonical model operations, modalities, output kinds, revisions, retry policies, and fallback dispositions. | internal | developer | source_and_assertions_inspected | no | local |
| `model.assignment` | Inference assignment | Store sparse owner assignments for capability groups without executing providers or selecting fallback at run time. | internal | user | source_and_assertions_inspected | no | local |
| `model.route_plan` | Frozen inference route | Freeze ordered capability, deployment, retry, and boundary facts before a physical model child runs. | internal | developer | source_and_assertions_inspected | no | local |
| `model.execution` | Inference route execution | Reserve and run the next lawful physical model attempt from immutable route evidence, with bounded fallback. | internal | developer | source_and_assertions_inspected | no | possible |
| `model.destination_readiness` | Inference destination readiness | Resolve a named destination and derive readiness from its own model, endpoint, key, manifest, or worker facts. | experimental | operator | source_and_assertions_inspected | no | local |
| `model.cancel_receipts` | Inference cancellation and receipts | Perform admitted cancellation and persist privacy-safe terminal outcomes for attempts and placement. | internal | developer | source_and_assertions_inspected | no | possible |
| `voice.correction_memory` | Dictation correction memory | Store bounded user corrections and apply matching routing or text corrections to later dictation. | experimental | user | source_and_assertions_inspected | no | local |
| `voice.replay` | Dictation journal replay | Rerun a stored transcript through current processing without typing or creating a new journal row. | experimental | user | source_and_assertions_inspected | no | possible |
| `voice.learning_digest` | Dictation learning digest | Summarize real correction and journal reach over a selected time window. | experimental | user | source_and_assertions_inspected | no | local |
| `voice.prebrief_selection` | Dictation pre-brief selection | Park one recent activity record for the next dictation and consume it once. | experimental | user | source_and_assertions_inspected | no | local |
| `voice.symbol_settings` | Spoken symbol settings | Store normalized spoken-symbol replacements for dictation text processing. | experimental | user | source_and_assertions_inspected | no | local |
| `voice.language_settings` | Speech language settings | Validate and normalize a Whisper language code, name, or auto-detect setting. | experimental | user | source_and_assertions_inspected | no | local |
| `voice.wake` | Wake word capture | Listen for a configured wake word and create a bounded preview typing path. | experimental | user | source_and_assertions_inspected | no | local |
| `voice.browser_remote_dictation` | Browser and remote dictation | Admit browser microphone intervals and deliver processed text through a remote focused or agent target. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.decision_lifecycle` | Meeting decision lifecycle | Read, accept, reject, supersede, promote, and draft artifacts from meeting decisions with receipts. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.action_lifecycle` | Meeting action lifecycle | List, review, edit, and triage meeting action items with owner and status fields. | experimental | user | source_and_assertions_inspected | no | possible |
| `model.download` | Model download | Start an owner-authorized catalog-pinned model acquisition without changing assignments. | experimental | operator | source_and_assertions_inspected | no | possible |
| `model.inventory` | Model inventory | List model library and connected destination metadata without exposing paths or secrets. | experimental | operator | source_and_assertions_inspected | no | local |
| `meeting.plugin.requirements_extractor` | Requirements extractor | Extract typed requirements from a meeting transcript window. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.action_owner_enforcer` | Action owner enforcer | Extract action items and identify missing owners or due dates. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.mermaid_architecture` | Mermaid architecture generator | Generate a typed Mermaid architecture or sequence artifact from a meeting transcript. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.adr_drafter` | ADR drafter | Draft typed architecture decision records from a meeting transcript. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.milestone_planner` | Milestone planner | Extract typed milestones, deliverables, and dependencies from a meeting transcript. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.dependency_mapper` | Dependency mapper | Extract typed dependency edges from a meeting transcript. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.scope_guard` | Scope guard | Classify transcript items as in scope or out of scope with rationale. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.customer_signal_extractor` | Customer signal extractor | Extract and classify customer signals from a meeting transcript. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.incident_timeline` | Incident timeline | Extract ordered incident events from a meeting transcript. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.risk_heatmap` | Risk heatmap | Extract typed risks with impact, likelihood, mitigation, and owner fields. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.stakeholder_update_drafter` | Stakeholder update drafter | Draft a typed stakeholder update from a meeting transcript. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.runbook_delta` | Runbook delta | Draft typed runbook changes from a meeting transcript. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.decision_announcement_drafter` | Decision announcement drafter | Draft typed announcements for recorded meeting decisions. | experimental | user | source_and_assertions_inspected | no | possible |
| `meeting.plugin.decision_capture` | Decision capture | Capture typed decisions, open questions, and bounded transcript provenance. | experimental | user | source_and_assertions_inspected | no | possible |
| `desk.open` | Open Desk | Open the Workbench surface and its current workspace. | built_unreleased | user | source_and_assertions_inspected | no | local |
| `desk.arrange` | Arrange windows | Move, resize, snap, minimize, maximize and restore Desk windows. | built_unreleased | user | source_and_assertions_inspected | no | local |
| `desk.inspect` | Inspect Desk object | Open a selected object in a named window surface with identity, state, provenance and verbs. | partial | user | source_and_assertions_inspected | no | possible |
| `desk.execute` | Run a Desk verb | Offer and run a named operation for the current Desk context. | partial | user | source_and_assertions_inspected | no | possible |
| `desk.drop` | Drop Desk object or file | Apply a named internal or external drop effect only when the source and target contract allows it. | partial | user | source_and_assertions_inspected | no | possible |
| `desk.persist` | Persist workspace | Restore and save the local Desk arrangement with a bounded versioned shape. | built_unreleased | user | source_and_assertions_inspected | no | local |
| `desk.runtime` | Reflect runtime state | Keep Desk surfaces truthful while the single runtime bus connects, reconnects or is offline. | partial | user | source_and_assertions_inspected | no | local |
| `desk.native_host` | Native Desk host seam | Provide bounded display, filesystem and host integration capabilities when a native adapter is later adopted. | planned | integration | source_inspected | no | possible |
| `agents.thread_persistent` | Persistent Thread chat | Save a multi-turn assistant conversation with branches, drafts, refs and kept results. | experimental | user | source_and_assertions_inspected | no | possible |
| `agents.thread_tool_loop` | Persistent Thread tool loop | Offer a bounded MCP tool palette inside a Thread turn and retain tool results and receipts. | experimental | user | source_and_assertions_inspected | no | possible |
| `agents.interview` | Interview conversation | Use one owner-only Thread mode to record sourced facts and reviewable suggestions. | experimental | user | source_and_assertions_inspected | no | possible |
| `agents.mcp_http` | MCP HTTP and sidecar tools | Expose the shared service/tool catalogue to MCP clients with authenticated dispatch. | experimental | integration | source_and_assertions_inspected | no | possible |
| `knowledge.grounding` | Grounded evidence hydration | Resolve explicit meetings, artifacts, projects, rails and optional memory matches into bounded evidence blocks. | experimental | user | source_and_assertions_inspected | no | possible |
| `knowledge.memory_search` | Long-horizon memory search | Search retained notes, meetings, decisions, threads, projects and workbench items with principal-scoped filters. | experimental | user | source_and_assertions_inspected | no | local |
| `workflows.linear_run` | Linear Workflow run | Run a validated linear workflow with frozen route evidence, child receipts and a retained artifact. | experimental | user | source_and_assertions_inspected | no | possible |
| `coder.observation` | Coder session observation | Show active Claude/Codex sessions and bounded, hash-gated pane output. | experimental | user | source_and_assertions_inspected | no | local |
| `coder.reply_and_draft` | Coder reply and draft | Draft, keep, edit and explicitly deliver a reply to one verified Coder process target. | experimental | user | source_and_assertions_inspected | no | possible |
| `coder.gate` | Coder Gate held tool call | Hold a matched risky Coder tool call for owner decision with bounded previews, idempotency and fail-closed recovery. | experimental | operator | source_and_assertions_inspected | no | possible |
| `integration.activity_connectors` | Activity connector packs | Preview and run local-first activity connector packs with explicit permissions and scoped rows. | experimental | developer | source_and_assertions_inspected | no | possible |
| `integration.github_readonly` | GitHub read-only activity | Read imported GitHub PR/issue and CI activity through an allowlisted gh CLI. | experimental | integration | source_and_assertions_inspected | no | possible |
| `integration.jira_confluence_calendar` | Jira, Confluence and calendar reads | Read supported Jira/Confluence resources and derive calendar meeting candidates with explicit source boundaries. | experimental | integration | source_and_assertions_inspected | no | possible |
| `integration.actuators` | Approval-gated external actuators | Turn reviewed text or artifacts into owner-authorized GitHub, Slack or webhook effects with receipts. | experimental | user | source_and_assertions_inspected | no | possible |
| `companion.ipad_client` | iPad hub client | Capture, review, import, approve and inspect HoldSpeak work from a typed native client. | built_unreleased | user | source_and_assertions_inspected | no | possible |
| `companion.aipi_audio_control` | AIPI-Lite audio and control companion | Forward device audio and expose meeting/status/Coder controls through a separate bridge. | experimental | user | source_and_assertions_inspected | no | possible |
| `companion.qlippy_presence` | Qlippy presence | Reflect selected attention states and egress posture through the optional mascot surface. | experimental | user | source_and_assertions_inspected | no | local |

## Reading the catalogue

A source path proves that a file was inspected. A test assertion proves what was inspected. A passing execution and owner observation are separate evidence. An unverified or missing shard stays visible in the generated metadata.

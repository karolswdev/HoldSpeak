# Directory — The Desk, the Mesh, the Agents

> **Auto-derived** by the 8-agent inventory sweep (Opus 4.8, 2026-07-08) from the
> phase record, then to be **verified on real glass** by the sweep story. This is the
> *starting map*, not the final ledger: the ✅/❓/— marks are the record's claim, and
> every ❓ (and every contested ✅) is exactly what the human checks on the device.

the newest territory — the desk as front door, the workbench, ask/grounding, runtime profiles, the mesh edge, the belt, steering/factory, sync, and the cross-surface handoff arcs. Feeds sweep story **HSU-2-04**.

**113 capabilities** — 55 must-test, 44 should-test, 14 spot-check.

Surfaces: ✅ record says present · ❓ unknown, verify on device · — record says not on this surface.

| P | web | iPad | iPhone | Capability | Key | Phases | State recipe(s) |
|---|---|---|---|---|---|---|---|
| 🔴 | ✅ | ❓ | ❓ | File a GitHub issue from an approved proposal | `actuators.connector.github_issue` | HS-38 | `meeting-just-ended-open-actions`, `proposal-pending-approval` |
| 🔴 | ✅ | ❓ | ❓ | POST to an allow-listed webhook from an approved proposal | `actuators.connector.webhook_post` | HS-38 | `meeting-just-ended-open-actions`, `proposal-pending-approval` |
| 🔴 | ✅ | ❓ | ❓ | Actuators stay off unless master switch + per-project allow-list enable them | `actuators.governance.gate` | HS-37 | `meeting-just-ended-open-actions`, `proposal-pending-approval` |
| 🔴 | ✅ | ❓ | ❓ | Approve or reject a proposed side effect (propose→approve→execute) | `actuators.proposal.approve_execute` | HS-37 | `meeting-just-ended-open-actions`, `proposal-pending-approval` |
| 🔴 | ✅ | ❓ | ❓ | Send a meeting digest or follow-up draft to Slack | `actuators.slack.send` | HS-61 | `meeting-just-ended-open-actions`, `slack-webhook-configured`, `proposal-pending-approval` |
| 🔴 | ❓ | ✅ | ❓ | Have AI draft an answer to a coder, then approve-then-inject | `agents.answer_coder.ai_drafted` | HSM-17-05,HSM-17-04 | `mesh-node-alive`, `agent-pane-awaiting-input`, `model-installed-on-device` |
| 🔴 | ✅ | ✅ | ❓ | Answer a waiting coding agent by voice from your device | `agents.answer_coder.by_voice` | HSM-13-02,HSM-13-04,HSM-13-01 | `mesh-node-alive`, `agent-pane-awaiting-input`, `hub-reachable-on-lan` |
| 🔴 | — | ✅ | ❓ | Point the iPad/iPhone at your desktop server as a companion | `agents.companion.pair_desktop` | HSM-12-01,HSM-12-03 | `mesh-node-alive`, `hub-reachable-on-lan` |
| 🔴 | ✅ | ✅ | ❓ | See your live coding agents on the desk and their questions | `agents.desk.live_coders` | HSM-17-02,HSM-17-03,HSM-15-08 | `mesh-node-alive`, `agent-pane-awaiting-input`, `hub-reachable-on-lan` |
| 🔴 | — | ❓ | ✅ | Dictate into any focused Mac app from the device | `agents.dictation.into_your_mac` | HSM-15-01,HSM-13-01 | `mesh-node-alive`, `hub-reachable-on-lan`, `focused-mac-app` |
| 🔴 | ❓ | ✅ | ❓ | See all mesh jobs and pending approvals in one queue | `agents.mesh.queue_inbox` | HSM-15-03,HSM-15-04 | `mesh-node-alive`, `proposal-pending-approval`, `hub-reachable-on-lan` |
| 🔴 | ✅ | ✅ | ❓ | Ask AI over lassoed context and keep or bin the printed card | `ask.atom.lasso_ask_keep` | HSM-16-09,HSM-16-04 | `seeded-desk`, `model-installed-on-device` |
| 🔴 | ✅ | ✅ | ❓ | Authenticated arrival on a token-guarded hub | `ask.web.token_auth_arrival` | HS-83-04 | `token-guarded-hub` |
| 🔴 | ✅ | ❓ | ❓ | HANDOFF: approve a story flip from the desk (dw gate) | `belt.approval_leg` | HS-82-05 | `proposal-pending-approval`, `belt-with-registered-rails-repo` |
| 🔴 | ✅ | ✅ | ❓ | Lasso a pile of objects and Ask AI about exactly that pile | `desk.ask-ai.grounded-on-pile` | HS-73,HS-83 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Live coding agents appear on the desk as objects that demand you when blocked | `desk.coders.agents-on-the-desk` | HS-87,HS-89 | `agent-pane-awaiting-input` |
| 🔴 | ✅ | ✅ | ❓ | Answer a blocked agent by typing, speaking, dropping a record, or AI-drafting | `desk.coders.answer-grounded-or-ai-drafted` | HS-78,HS-87 | `agent-pane-awaiting-input`, `meeting-just-ended-open-actions` |
| 🔴 | ✅ | ✅ | ❓ | Upgrades back your database up before touching it and refuse newer-build data | `desk.data.schema-safe-upgrades` | HS-50 | `fresh-desk` |
| 🔴 | ✅ | ✅ | ❓ | Open the DeskOS diorama as the app front door | `desk.diorama.front_door` | HSM-14-19,HSM-14-22,HSM-14-23 | `seeded-desk`, `fresh-desk` |
| 🔴 | ✅ | ✅ | ❓ | holdspeak doctor reports what is actually broken | `desk.doctor.honest-readout` | HS-50,HS-84 | `first-run-no-model`, `intel-endpoint-dead` |
| 🔴 | ✅ | ✅ | ❓ | The Desk is the front door: every mode's output lives as an object in one world | `desk.front-door.spatial-objects` | HS-73,HS-83 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ✅ | Profile shapes sync across your surfaces so the same named profile is available everywhere | `desk.sync.profile-shape-across-surfaces` | HS-84,HSM-17 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Run an agent persona from the rail | `desk.web.agent_rail_run` | HS-73-07 | `seeded-desk`, `mesh-node-alive` |
| 🔴 | ✅ | ✅ | ❓ | Answer a waiting coder by voice | `desk.web.answer_waiting_coder` | HS-78-03 | `agent-pane-awaiting-input` |
| 🔴 | ✅ | ✅ | ❓ | Create a primitive in-world (no dialog) | `desk.web.create_in_world` | HS-73-03 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | The Desk is the web front door | `desk.web.front_door` | HS-71,HS-73-02 | `fresh-desk`, `seeded-desk` |
| 🔴 | ✅ | ❓ | ❓ | One first-run arrival (/welcome) | `desk.web.one_arrival` | HS-70-03,HS-73-02 | `first-run-no-model`, `fresh-desk` |
| 🔴 | ✅ | ✅ | ❓ | Hold-to-talk voice on every desk input | `desk.web.transcribe_everywhere` | HS-78-01,HS-78-02 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Kill a session from the desk (consent-gated) | `factory.kill` | HS-90-01,HS-90-03 | `agent-session-live`, `agent-pane-armed` |
| 🔴 | ✅ | ❓ | ❓ | HANDOFF: web run → hub relay → mesh worker | `mesh.handoff.web_run_to_node` | HS-85-01,HS-85-02,HS-85-03 | `mesh-node-alive` |
| 🔴 | ✅ | ✅ | ❓ | A profile names a mesh node (meshNode kind) | `mesh.profile_node` | HS-85-02,HS-85-04 | `mesh-node-alive`, `mesh-node-just-died` |
| 🔴 | ❓ | ❓ | ❓ | Turn any machine into a mesh edge (holdspeak mesh serve) | `mesh.serve_node` | HS-85-03 | `mesh-node-alive` |
| 🔴 | ✅ | ✅ | ✅ | The hold-bar teleprompter on the iPhone dictate surface | `mobile.desk.compact.hold_bar_teleprompter` | HSM-20-04 | `seeded-desk`, `mesh-node-alive` |
| 🔴 | — | ✅ | ✅ | The desk renders as a filtered lane on the iPhone | `mobile.desk.compact.lane` | HSM-20-01,HSM-20-02 | `seeded-desk`, `fresh-desk` |
| 🔴 | — | ✅ | ✅ | Flip one toggle to serve the mesh from the phone | `mobile.mesh.serve.consent_toggle` | HSM-25-02 | `mesh-node-alive`, `first-run-no-model` |
| 🔴 | ✅ | ✅ | ✅ | A desk ask executes on the phone's own model, badged mesh | `mobile.mesh.serve.execute_ask` | HSM-25-01,HSM-25-03 | `mesh-node-alive` |
| 🔴 | ✅ | ✅ | ✅ | Pick the active runtime profile on the iPad | `mobile.profiles.active_picker` | HSM-24-01,HSM-24-02 | `seeded-desk`, `first-run-no-model` |
| 🔴 | ✅ | ✅ | ✅ | A profile's API key never leaves the device / never syncs | `mobile.profiles.key_never_syncs` | HSM-24-01,HSM-24-06 | `seeded-desk`, `mesh-node-alive` |
| 🔴 | ✅ | ✅ | ✅ | Manage the profile list and assign per-agent profiles on the iPad | `mobile.profiles.manage_advanced` | HSM-24-03 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Attach, arm, and steer a live agent session from the iPad | `mobile.steering.attach_arm_steer` | HSM-26-03,HSM-27-02 | `agent-pane-awaiting-input`, `mesh-node-alive` |
| 🔴 | ✅ | ✅ | ❓ | Spawn, rename, and kill agent sessions from the iPad | `mobile.steering.factory_lifecycle` | HSM-27-01,HSM-27-02 | `agent-pane-awaiting-input`, `mesh-node-alive` |
| 🔴 | ✅ | ✅ | ❓ | Send raw keys to an agent pane from the iPad key palette | `mobile.steering.key_palette` | HSM-27-01,HSM-27-02 | `agent-pane-awaiting-input` |
| 🔴 | ✅ | ✅ | ❓ | Steer an agent on any machine via the iPad node relay | `mobile.steering.node_relay` | HSM-27-01,HSM-27-02 | `mesh-node-alive`, `agent-pane-awaiting-input` |
| 🔴 | ✅ | ✅ | ✅ | One honest egress badge on every mobile surface | `mobile.trust.egress.badge` | HSM-21-01,HSM-21-02,HSM-21-04 | `seeded-desk`, `intel-endpoint-dead` |
| 🔴 | ✅ | ✅ | ❓ | Author a runnable graph (blueprint) on the iPad and sync it to the hub | `mobile.workbench.graph.author` | HSM-22-01,HSM-22-04 | `seeded-desk`, `mesh-node-alive` |
| 🔴 | ✅ | ❓ | ❓ | Qlippy sliding cards for four moments | `qlippy.decision_cards` | HS-56 | `presence-and-mascot-enabled`, `proposal-pending-approval`, `meeting-just-ended-open-actions` |
| 🔴 | ✅ | ✅ | ❓ | Runtime profiles editor (/profiles) | `runtime.web.profiles_editor` | HS-84-01,HS-84-03 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Arm and steer a session (consent-gated) | `steering.arm_steer` | HS-87-02,HS-87-03 | `agent-session-live`, `agent-pane-armed`, `agent-pane-recycled` |
| 🔴 | ✅ | ✅ | ❓ | HANDOFF: steer a session on another machine | `steering.cross_machine` | HS-89-03,HS-90-02 | `remote-steer-node-alive`, `remote-steer-node-offline` |
| 🔴 | ✅ | ❓ | ❓ | Ground a steer with a desk object | `steering.ground` | HS-87-04 | `agent-session-live`, `agent-pane-armed`, `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Send any key to a session (key palette) | `steering.keys` | HS-89-01,HS-90-02 | `agent-session-live`, `agent-pane-armed`, `agent-runaway` |
| 🔴 | ✅ | ✅ | ❓ | Watch a live agent session from the desk | `steering.peek` | HS-87-01 | `agent-session-live`, `agent-pane-awaiting-input` |
| 🔴 | ✅ | ✅ | ❓ | Have a meeting captured on one device appear on another | `sync.content.cross_device` | HSM-10-01,HSM-10-02,HSM-10-03,HSM-10-04 | `mesh-node-alive`, `two-devices-paired` |
| 🔴 | ✅ | ✅ | ✅ | All 10 primitive kinds round-trip across the sync wire byte-faithfully | `sync.integrity.roundtrip` | HSM-23-04 | `seeded-desk`, `mesh-node-alive` |
| 🔴 | ✅ | ✅ | ✅ | The iPad store refuses a newer schema and backs up before migrating | `sync.storage.refuse_newer` | HSM-23-01,HSM-23-02 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Approve/reject proposals live during a meeting | `actuators.live.pending_actions_panel` | HS-38 | `mesh-node-alive`, `proposal-pending-approval` |
| 🟡 | ❓ | ✅ | ❓ | Answer a coder from dropped meeting/artifact context | `agents.answer_coder.dropped_context` | HSM-17-04 | `mesh-node-alive`, `agent-pane-awaiting-input`, `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | Pick which waiting coder your answer goes to | `agents.companion.board_select_target` | HSM-13-03 | `mesh-node-alive`, `multiple-agents-awaiting` |
| 🟡 | ✅ | ✅ | ❓ | Start and stop desktop meetings from the device | `agents.companion.meetings_remote_control` | HSM-12-02 | `mesh-node-alive`, `hub-reachable-on-lan` |
| 🟡 | ❓ | ❓ | ❓ | Run a workflow step on a chosen mesh node | `agents.mesh.runs_on_dispatch` | HSM-15-02,HSM-15-04 | `mesh-node-alive`, `hub-reachable-on-lan`, `model-installed-on-device` |
| 🟡 | ✅ | ✅ | ❓ | Speak to fill the Ask composer (and any input) by voice | `ask.composer.speak_to_fill` | HSM-16-09,HSM-16-04 | `seeded-desk`, `mic-permission-granted` |
| 🟡 | ✅ | ✅ | ❓ | Ground an ask with priced references | `ask.web.ground_this_ask` | HS-83-01 | `seeded-desk`, `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ✅ | ❓ | Persistent persona conversations | `ask.web.persona_threads` | HS-83-02 | `seeded-desk`, `mesh-node-alive` |
| 🟡 | ✅ | ❓ | ❓ | Imported meetings receive typed plugin artifacts | `belt.approval.import_run_chain` | HS-80-01 | `seeded-desk`, `imported-meeting-no-artifacts` |
| 🟡 | ✅ | ✅ | ❓ | The delivery belt / mission-control conveyor | `belt.conveyor` | HS-82-03,HS-82-04,HS-86-04 | `seeded-desk`, `belt-with-registered-rails-repo` |
| 🟡 | ✅ | ✅ | ❓ | Lasso objects into a bundle and file them | `desk.diorama.lasso_bundle_file` | HSM-14-19,HSM-16-04 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | Spill a meeting into its parts on the desk | `desk.diorama.meeting_spill` | HSM-14-20,HSM-14-22 | `seeded-desk`, `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ✅ | ❓ | Create and use knowledge bases and directories on the desk | `desk.knowledge_bases` | HSM-14-22,HSM-16-02 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Open a chat pinned to any model the hub can run | `desk.models.open-a-model-chat` | HS-84,HS-85 | `seeded-desk`, `mesh-node-alive` |
| 🟡 | ✅ | ❓ | ❓ | Talk to your personas: a persistent conversation, each reply badged for where it ran | `desk.personas.conversation-thread` | HS-83,HS-87 | `seeded-desk` |
| 🟡 | ❓ | — | — | Qlippy the mascot: opt-in desktop presence that only interrupts for moments that need you | `desk.presence.qlippy-opt-in` | HS-56,HS-41 | `proposal-pending-approval`, `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ✅ | ❓ | Author a recipe (persona/chain) in-world without modals | `desk.recipes.in_world_authoring` | HSM-17-08,HSM-16-04 | `seeded-desk` |
| 🟡 | ✅ | — | — | Four doors, not fourteen (Home/Dictation/Meetings/Studio) | `desk.web.four_doors_ia` | HS-70-01,HS-70-06 | `fresh-desk`, `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | Primitives render as floating sprites with depth | `desk.web.objects_float` | HS-71-03,HS-73-01 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | Open an object into a pull-out | `desk.web.pullout_open` | HS-73-04 | `seeded-desk`, `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ✅ | ❓ | The Record orb drives the hub recorder | `desk.web.record_orb` | HS-73-06 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | File objects into zones and dive in | `desk.web.zones_file_dive` | HS-71-05,HS-73-05 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | Build a visual intelligence workflow on the Workbench | `desk.workbench.visual_builder` | HSM-14-15,HSM-14-16 | `seeded-desk`, `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ✅ | ❓ | Spawn and rename sessions from the desk | `factory.spawn_rename` | HS-90-01,HS-90-03 | `seeded-desk`, `agent-session-live` |
| 🟡 | ✅ | ❓ | ❓ | Mesh liveness on every surface | `mesh.liveness_everywhere` | HS-85-04 | `mesh-node-alive`, `mesh-node-just-died` |
| 🟡 | ✅ | ✅ | ❓ | Run-born artifacts materialize on the iPad desk without duplicating | `mobile.artifacts.run_born.materialize` | HSM-18-07 | `seeded-desk`, `mesh-node-alive` |
| 🟡 | ✅ | ✅ | ❓ | The rails belt renders on the iPad diorama | `mobile.belt.diorama.render` | HSM-26-02 | `seeded-desk`, `mesh-node-alive` |
| 🟡 | ❓ | ✅ | ✅ | The capture canvas at compact width with tap-to-tack | `mobile.desk.compact.capture_canvas` | HSM-20-03 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ✅ | The migrating pull-out on compact width | `mobile.desk.compact.pullout` | HSM-20-02 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | Steering actions are audited and readable back on the iPad | `mobile.steering.audit_trail` | HSM-26-01,HSM-27-01 | `agent-pane-awaiting-input` |
| 🟡 | ✅ | ✅ | ❓ | Pick and attach to any agent pane from the iPad | `mobile.steering.pane_picker` | HSM-27-01,HSM-27-02 | `agent-pane-awaiting-input` |
| 🟡 | ✅ | ✅ | ❓ | GitHub tile tells the truth about paired vs configured | `mobile.trust.github.honesty` | HSM-21-03 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Qlippy ambient presence dock | `qlippy.presence_dock` | HS-56 | `fresh-desk`, `presence-and-mascot-enabled` |
| 🟡 | ✅ | ❓ | ❓ | Ground any run on the rails | `rails.ground_run` | HS-88-01,HS-88-02 | `belt-with-registered-rails-repo`, `agent-session-live` |
| 🟡 | ✅ | ❓ | ❓ | Honest doctor + one egress badge derivation | `runtime.doctor_egress` | HS-84-04 | `seeded-desk`, `intel-endpoint-dead` |
| 🟡 | ✅ | ❓ | ❓ | Meeting-intel and dictation run on a picked profile | `runtime.pick_everywhere` | HS-84-01,HS-84-02 | `seeded-desk`, `mesh-node-alive` |
| 🟡 | ✅ | — | ❓ | A run answer becomes a real artifact | `runtime.run_born_artifact` | HS-74-01,HS-74-04 | `seeded-desk`, `mesh-node-alive` |
| 🟡 | ✅ | ✅ | ❓ | Attach to any tmux pane | `steering.attach_any_pane` | HS-89-02,HS-90-02 | `hand-started-tmux-pane` |
| 🟡 | ✅ | ❓ | ❓ | The steering audit trail | `steering.audit` | HS-87-06,HS-89-04 | `agent-session-live` |
| 🟡 | ✅ | ❓ | ❓ | Classify what a session surfaces | `steering.classify` | HS-87-05 | `agent-pane-awaiting-input`, `proposal-pending-approval` |
| 🟡 | ✅ | ✅ | ❓ | See which of your nodes can run which model | `sync.capability.model_manifest` | HSM-16-08 | `mesh-node-alive`, `model-installed-on-device` |
| 🟡 | ✅ | ✅ | ❓ | Have knowledge bases and directories flow across surfaces | `sync.organization.kb_directory_travels` | HSM-16-02,HSM-16-05 | `seeded-desk`, `two-devices-paired` |
| 🟡 | ✅ | ✅ | ✅ | The readiness / doctor panel in iPad Settings | `sync.storage.doctor_panel` | HSM-23-03 | `seeded-desk`, `first-run-no-model` |
| 🟡 | ✅ | ✅ | ❓ | The /workbench node canvas | `workbench.web.node_canvas` | HS-69-10,HS-69-11 | `seeded-desk` |
| ⚪ | ✅ | ❓ | ❓ | The models front door (open a chat on any model) | `ask.web.models_door` | HS-83-03 | `seeded-desk`, `mesh-node-alive` |
| ⚪ | ✅ | ❓ | ❓ | Belt station lights + evidence in place | `belt.receipts` | HS-86-03,HS-86-04 | `belt-with-registered-rails-repo` |
| ⚪ | ❓ | ❓ | ❓ | Fire your saved agents and crews against the live transcript | `desk.ambient_recorder_agents` | HSM-14 | `seeded-desk`, `recording-in-progress`, `saved-agent-exists` |
| ⚪ | ✅ | ✅ | ❓ | Arrange desk objects by drag, persisted per-device | `desk.web.free_placement` | HS-71-04,HS-73-04 | `seeded-desk` |
| ⚪ | ✅ | ✅ | ❓ | Reactive mic waveform meter | `desk.web.mic_waveform` | HS-69-08 | `seeded-desk` |
| ⚪ | ✅ | ✅ | ❓ | Qlippy lives on the desk (opt-in) | `desk.web.qlippy_life` | HS-71-06 | `seeded-desk` |
| ⚪ | ✅ | ✅ | ❓ | The always-on Queue HUD | `desk.web.queue_hud` | HS-69-07,HS-77-02 | `seeded-desk` |
| ⚪ | ✅ | — | — | HANDOFF: remote node rail-events → hub observer | `mesh.handoff.node_events_to_hub` | HS-88-04 | `mesh-node-alive` |
| ⚪ | ✅ | ✅ | ❓ | The rails journal renders on the iPad diorama | `mobile.belt.rails.journal` | HSM-26-04 | `seeded-desk` |
| ⚪ | ✅ | ✅ | ❓ | The run UI renders the hub's warning on unhonored graph features | `mobile.workbench.run.warning` | HSM-22-02,HSM-22-03 | `seeded-desk` |
| ⚪ | ❓ | — | — | Qlippy native desktop HUD overlay | `qlippy.native_hud_overlay` | HS-56,HS-41 | `presence-and-mascot-enabled`, `proposal-pending-approval`, `linux-or-macos-desktop` |
| ⚪ | ✅ | ❓ | ❓ | The ambient rails journal (opt-in) | `rails.observer_journal` | HS-88-03 | `belt-with-registered-rails-repo`, `mesh-node-alive` |
| ⚪ | ✅ | ✅ | ✅ | The cross-surface JSON-Schema contract spine (parity foundation) | `sync.contracts.parity_spine` | HSM-24-01,HSM-26-01 | `seeded-desk` |
| ⚪ | ✅ | ✅ | ❓ | The generation theater | `workbench.web.generation_theater` | HS-69-09,HS-81-02 | `seeded-desk`, `mesh-node-alive` |

Priority: 🔴 must-test · 🟡 should-test · ⚪ spot-check · ⬛ skip.

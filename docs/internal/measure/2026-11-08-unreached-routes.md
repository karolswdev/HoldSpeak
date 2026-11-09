# Routes with no web or iOS caller, 2026-11-08

Written from `scripts/gen_api_surface.py` on branch `tools/api-surface-census` (base `origin/main` 2b0296340). 163 of 828 routes have `consumers == []`.

The census reads the web (`web/src`, not `_parked`, not tests) and the iOS app (`apple/Sources`, `apple/App`). It does not read other callers: the CLI, hooks, the MCP proxy, the Line node, the phone app, walk and fixture scripts. Where the fixed part of a path is named in `holdspeak/`, `scripts/` or `apple/` outside the route modules, the line says so (`named in`). A name is text, not a proven call: read it before you park the route.

Format: method, path, handler module.

**Evening pass (branch `refactor/park-unreached-routes`).** Each API line now ends with one word: `parked` (the handler is under `holdspeak/web/routes/_parked/`, its tests under `tests/_parked/`), `kept: <caller>` (a real client calls it), or `left: <reason>` (no product caller found, but a test, an atlas case, another lane or a security review holds it). 15 parked, 56 kept, 63 left. A route a test only uses for setup was left, not parked: park it together with that test.

**Late-evening pass (branch `refactor/park-left-routes`, #PR_NUM).** Each of the 63 `left` lines was read again: 23 parked with their tests (cases moved to `tests/_parked/`, or the setup now seeds through the service or the store), 21 kept as declared http exposures, 8 left for a security review (gate, kernel, principals), 10 left for other lanes (meetings, people, workbenches), 1 left as a link (`/api/invocations/{id}`). Now: 38 parked, 77 kept, 19 left.

## API routes (134)

- POST `/api/activity/extension/events` web.routes.activity.enrichment: **kept: the Firefox extension (extensions/firefox/background.js:36)**
- DELETE `/api/activity/meeting-candidates` web.routes.activity.candidates: **parked (#PR_NUM, the left-routes pass)**
- POST `/api/activity/meeting-candidates` web.routes.activity.candidates: **parked (#PR_NUM, the left-routes pass)**
- POST `/api/activity/project-rules` web.routes.activity.rules (named in: holdspeak/web/announce.py): **parked (#PR_NUM, the left-routes pass)**
- POST `/api/activity/project-rules/preview` web.routes.activity.rules (named in: holdspeak/web/announce.py): **parked (#PR_NUM, the left-routes pass)**
- PUT `/api/activity/project-rules/{rule_id}` web.routes.activity.rules (named in: holdspeak/web/announce.py): **parked (#PR_NUM, the left-routes pass)**
- GET `/api/agents/capabilities` web.routes.system.agent_capabilities (named in: holdspeak/agent_capabilities.py): **parked**
- PATCH `/api/all-action-items/{item_id}/review` web.routes.meetings.action_items (named in: scripts/dogfood_meeting_aftercare.py, scripts/needs_you_faces_fixture.py, scripts/philo13_needs_you_fixture.py): **left: other lane**
- POST `/api/authority/evaluate` web.routes.authority (named in: holdspeak/web/announce.py): **parked**
- GET `/api/authority/grants` web.routes.authority (named in: holdspeak/principals.py): **parked**
- POST `/api/authority/grants` web.routes.authority (named in: holdspeak/principals.py): **parked**
- DELETE `/api/authority/grants/{grant_id}` web.routes.authority (named in: holdspeak/principals.py): **parked**
- GET `/api/authority/grants/{grant_id}/uses` web.routes.authority (named in: holdspeak/principals.py): **parked**
- POST `/api/brief/items/{item_id}/shelf` web.routes.monday_brief (named in: holdspeak/operations.py): **kept: declared (an http exposure in holdspeak/*operations.py)**
- GET `/api/brief/shelf` web.routes.monday_brief (named in: holdspeak/operations.py, scripts/philo5_pairs.py): **kept: declared (an http exposure in holdspeak/*operations.py)**
- POST `/api/cadence/closeout/apply` web.routes.cadence: **parked (#PR_NUM, the left-routes pass)**
- GET `/api/cadence/loops/{loop_id}` web.routes.cadence (named in: holdspeak/db/projections.py, scripts/phase107_closeout_beats.py, scripts/record_chair_rhythm_fixture.py, scripts/walk_working_desk_legs.py): **parked (#PR_NUM, the left-routes pass)**
- POST `/api/cadence/run-now` web.routes.cadence (named in: scripts/walk_working_desk.py, scripts/walk_working_desk_legs.py): **parked (#PR_NUM, the left-routes pass)**
- GET `/api/calendar/events` web.routes.calendar_events: **parked (#PR_NUM, the left-routes pass)**
- DELETE `/api/calendar/events/{event_id}/link` web.routes.calendar_events: **parked (#PR_NUM, the left-routes pass)**
- POST `/api/calendar/events/{event_id}/link` web.routes.calendar_events: **parked (#PR_NUM, the left-routes pass)**
- POST `/api/calls/line/enrol` web.routes.calls (named in: holdspeak/line/node.py, holdspeak/principals.py, scripts/record_line_fixtures.py): **kept: the Line node (holdspeak/line/node.py)**
- POST `/api/calls/line/events` web.routes.calls (named in: holdspeak/line/node.py, holdspeak/principals.py): **kept: the Line node (holdspeak/line/node.py)**
- POST `/api/calls/line/hello` web.routes.calls (named in: holdspeak/line/node.py, holdspeak/principals.py, scripts/record_line_fixtures.py): **kept: the Line node (holdspeak/line/node.py)**
- POST `/api/calls/line/next` web.routes.calls (named in: holdspeak/line/node.py, holdspeak/principals.py): **kept: the Line node (holdspeak/line/node.py)**
- GET `/api/chains` web.routes.primitives.chains (named in: scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: the UAT conductor seeds and probes them (uat/conductor/induction/seeds.py:40-41, probes.py:144,149); atlas case p13.chain.pullout; MCP desk.* kind=chains/workflows calls the same service methods**
- POST `/api/chains` web.routes.primitives.chains (named in: scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: the UAT conductor seeds and probes them (uat/conductor/induction/seeds.py:40-41, probes.py:144,149); atlas case p13.chain.pullout; MCP desk.* kind=chains/workflows calls the same service methods**
- DELETE `/api/chains/{chain_id}` web.routes.primitives.chains (named in: scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: the UAT conductor seeds and probes them (uat/conductor/induction/seeds.py:40-41, probes.py:144,149); atlas case p13.chain.pullout; MCP desk.* kind=chains/workflows calls the same service methods**
- GET `/api/chains/{chain_id}` web.routes.primitives.chains (named in: scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: the UAT conductor seeds and probes them (uat/conductor/induction/seeds.py:40-41, probes.py:144,149); atlas case p13.chain.pullout; MCP desk.* kind=chains/workflows calls the same service methods**
- PUT `/api/chains/{chain_id}` web.routes.primitives.chains (named in: scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: the UAT conductor seeds and probes them (uat/conductor/induction/seeds.py:40-41, probes.py:144,149); atlas case p13.chain.pullout; MCP desk.* kind=chains/workflows calls the same service methods**
- POST `/api/channels/sends` web.routes.channels (named in: holdspeak/channel_operations.py, holdspeak/principals.py, scripts/record_room_wires.py): **kept: declared (an http exposure in holdspeak/*operations.py)**
- POST `/api/concierge/retry` web.routes.concierge (named in: holdspeak/services/needs_you_membership.py): **kept: the Needs-you engine-failure row hands it as a verb href (holdspeak/services/needs_you_membership.py:479)**
- POST `/api/decision-records/{record_id}/dispute` web.routes.decision_records: **parked (#PR_NUM, the left-routes pass)**
- POST `/api/decision-records/{record_id}/supersede` web.routes.decision_records: **parked (#PR_NUM, the left-routes pass)**
- POST `/api/decisions/{decision_id}/reject` web.routes.decisions (named in: holdspeak/operations.py, holdspeak/principals.py, scripts/graph_walk.py, scripts/hs109_03_live_proof.py, …): **parked (#PR_NUM, the left-routes pass)**
- POST `/api/delivery/node/disconnect` web.routes.delivery_node (named in: holdspeak/web/announce.py): **parked**
- POST `/api/delivery/node/heartbeat` web.routes.delivery_node (named in: holdspeak/commands/node_serve.py, holdspeak/web/announce.py): **kept: holdspeak/commands/node_serve.py**
- POST `/api/delivery/node/hello` web.routes.delivery_node (named in: holdspeak/commands/node_serve.py, holdspeak/web/announce.py): **kept: holdspeak/commands/node_serve.py**
- GET `/api/delivery/terminal/commands/{command_id}` web.routes.delivery_terminal (named in: scripts/phase94_delivery_campaign.py): **parked (#PR_NUM, the left-routes pass)**
- POST `/api/delivery/terminal/targets` web.routes.delivery_terminal (named in: scripts/phase94_delivery_campaign.py): **parked (#PR_NUM, the left-routes pass)**
- WS `/api/devices/audio` device_audio_ws (named in: holdspeak/commands/device.py, holdspeak/device_audio.py, holdspeak/device_audio_ws.py, holdspeak/principals.py, …): **kept: holdspeak/commands/device.py (the device CLI)**
- DELETE `/api/dictation/corrections` web.routes.dictation.pipeline: **parked**
- DELETE `/api/dictation/project-kb` web.routes.dictation.kb (named in: scripts/dogfood_project_knowledge.py): **parked**
- GET `/api/directories/{directory_id}` web.routes.primitives.directories (named in: holdspeak/operations.py, scripts/philo7_file_and_find.py, scripts/philo7_pairs.py, scripts/record_chrome_palette.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- GET `/api/directories/{directory_id}/members` web.routes.primitives.directories (named in: holdspeak/operations.py, scripts/philo7_file_and_find.py, scripts/philo7_pairs.py, scripts/record_chrome_palette.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- POST `/api/door/items` web.routes.door: **kept: atlas case brief_reading.source.held_action_source sets up through it (graph walk)**
- GET `/api/gate/audit` web.routes.system.gate_routes: **left: security review**
- GET `/api/gate/config` web.routes.system.gate_routes: **left: security review**
- POST `/api/gate/proposals` web.routes.system.gate_routes (named in: holdspeak/coder_gate.py, holdspeak/db/schema/cadence_agents.py, holdspeak/principals.py): **kept: the coder gate hook (holdspeak/coder_gate.py:295,329,505,543,853,884)**
- GET `/api/gate/proposals/{proposal_id}` web.routes.system.gate_routes (named in: holdspeak/coder_gate.py, holdspeak/db/schema/cadence_agents.py, holdspeak/principals.py): **kept: the coder gate hook (holdspeak/coder_gate.py:295,329,505,543,853,884)**
- POST `/api/gate/proposals/{proposal_id}/receipt` web.routes.system.gate_routes (named in: holdspeak/coder_gate.py, holdspeak/db/schema/cadence_agents.py, holdspeak/principals.py): **kept: the coder gate hook (holdspeak/coder_gate.py:295,329,505,543,853,884)**
- POST `/api/gate/usage` web.routes.system.gate_routes (named in: holdspeak/coder_gate.py, holdspeak/principals.py): **kept: the coder gate hook (holdspeak/coder_gate.py:295,329,505,543,853,884)**
- POST `/api/inference-targets` web.routes.primitives.profiles (named in: holdspeak/doctor.py, scripts/record_chrome_palette.py, scripts/record_room_wires.py, scripts/settings_walk_139.py, …): **kept: the UAT conductor (uat/conductor/induction/recipes.py:322, seeds.py:42) and the Ask route tests set up through it**
- GET `/api/inference/defaults` web.routes.inference_assignments: **parked (#PR_NUM, the left-routes pass)**
- POST `/api/inference/defaults/use-proposal` web.routes.inference_assignments: **parked (#PR_NUM, the left-routes pass)**
- POST `/api/intel/process` web.routes.meetings.intel (named in: holdspeak/intel_queue.py, holdspeak/intel_queue_conductor.py): **left: other lane**
- GET `/api/intel/summary` web.routes.meetings.intel: **left: other lane**
- PUT `/api/intents/override` web.routes.dictation.intents: **parked (#PR_NUM, the left-routes pass)**
- GET `/api/invocations/{invocation_id}` web.routes.primitives.invocations (named in: holdspeak/db/projections.py): **left: linked (holdspeak/db/projections.py:446 hands it as source_api)**
- GET `/api/kbs/{kb_id}` web.routes.primitives.kbs (named in: holdspeak/operations.py, scripts/philo7_pairs.py, scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: declared (an http exposure in holdspeak/*operations.py)**
- GET `/api/kbs/{kb_id}/members` web.routes.primitives.kbs (named in: holdspeak/operations.py, scripts/philo7_pairs.py, scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: declared (an http exposure in holdspeak/*operations.py)**
- POST `/api/kernel/executor/claim` web.routes.system.kernel_routes (named in: holdspeak/web/announce.py): **left: security review**
- POST `/api/kernel/executor/operations/{operation_id}/receipt` web.routes.system.kernel_routes (named in: holdspeak/web/announce.py): **left: security review**
- GET `/api/kernel/executor/operations/{operation_id}/reconcile` web.routes.system.kernel_routes (named in: holdspeak/web/announce.py): **left: security review**
- POST `/api/kernel/operations/{operation_id}/decide` web.routes.system.kernel_routes (named in: holdspeak/principals.py): **left: security review**
- POST `/api/kernel/submit` web.routes.system.kernel_routes (named in: holdspeak/kernel/desk.py, holdspeak/kernel/project.py, holdspeak/principals.py, scripts/hs109_06_process_window_walk.py): **left: security review**
- POST `/api/mcp` web.routes.mcp_http (named in: holdspeak/delivery/agent_mcp.py, holdspeak/delivery/pi_launch.py, holdspeak/mcp/aio.py, holdspeak/mcp/long_tools.py, …): **kept: the MCP proxy (holdspeak/mcp/server.py, delivery/agent_mcp.py)**
- POST `/api/meetings/{meeting_id}/export/slack` web.routes.meetings.aftercare (named in: apple/App/CompanionShellApp.swift, apple/Sources/Contracts/Aftercare.swift, apple/Sources/Contracts/MeetingArtifact.swift, apple/Sources/Contracts/MeetingFacets.swift, …): **left: other lane**
- GET `/api/meetings/{meeting_id}/followup-draft` web.routes.meetings.aftercare (named in: apple/App/CompanionShellApp.swift, apple/Sources/Contracts/Aftercare.swift, apple/Sources/Contracts/MeetingArtifact.swift, apple/Sources/Contracts/MeetingFacets.swift, …): **left: other lane**
- POST `/api/missioncontrol/rails/remote-events` web.routes.missioncontrol: **parked**
- GET `/api/model-profiles` web.routes.primitives.model_profiles (named in: scripts/surface_interaction_walk.py): **kept: atlas cases j3.profile_delete, j3.profile_unbind set up through them (graph walk)**
- POST `/api/model-profiles` web.routes.primitives.model_profiles (named in: scripts/surface_interaction_walk.py): **kept: atlas cases j3.profile_delete, j3.profile_unbind set up through them (graph walk)**
- DELETE `/api/model-profiles/{profile_id}` web.routes.primitives.model_profiles (named in: scripts/surface_interaction_walk.py): **kept: atlas cases j3.profile_delete, j3.profile_unbind set up through them (graph walk)**
- GET `/api/model-profiles/{profile_id}` web.routes.primitives.model_profiles (named in: scripts/surface_interaction_walk.py): **kept: atlas cases j3.profile_delete, j3.profile_unbind set up through them (graph walk)**
- DELETE `/api/model-profiles/{profile_id}/binding` web.routes.primitives.model_profiles (named in: scripts/surface_interaction_walk.py): **kept: atlas cases j3.profile_delete, j3.profile_unbind set up through them (graph walk)**
- POST `/api/model-profiles/{profile_id}/binding` web.routes.primitives.model_profiles (named in: scripts/surface_interaction_walk.py): **kept: atlas cases j3.profile_delete, j3.profile_unbind set up through them (graph walk)**
- POST `/api/model-profiles/{profile_id}/probe` web.routes.primitives.model_profiles (named in: scripts/surface_interaction_walk.py): **kept: atlas cases j3.profile_delete, j3.profile_unbind set up through them (graph walk)**
- POST `/api/model-profiles/{profile_id}/revisions` web.routes.primitives.model_profiles (named in: scripts/surface_interaction_walk.py): **kept: atlas cases j3.profile_delete, j3.profile_unbind set up through them (graph walk)**
- POST `/api/onboarding/agents/use-all` web.routes.onboarding (named in: holdspeak/onboarding_operations.py): **kept: declared (an http exposure in holdspeak/*operations.py)**
- GET `/api/people/relationships/{relationship_id}/notes` web.routes.people (named in: scripts/people_walk.py, scripts/people_walk_full.py, scripts/philo13_b4_fixture.py, scripts/record_chrome_palette.py, …): **left: other lane**
- POST `/api/phone/calls` web.routes.phone (named in: holdspeak/principals.py, holdspeak/services/needs_you_membership.py, scripts/record_phone_fixtures.py): **kept: the phone app wire (holdspeak/phone/contract.py:201, phone/events.py:6, phone/actions.py:7) and Needs-you verb hrefs (needs_you_membership.py)**
- GET `/api/phone/calls/{call_id}` web.routes.phone (named in: holdspeak/principals.py, holdspeak/services/needs_you_membership.py, scripts/record_phone_fixtures.py): **kept: the phone app wire (holdspeak/phone/contract.py:201, phone/events.py:6, phone/actions.py:7) and Needs-you verb hrefs (needs_you_membership.py)**
- GET `/api/phone/devices` web.routes.phone (named in: holdspeak/phone/contract.py, holdspeak/phone/devices.py, holdspeak/principals.py, scripts/record_phone_fixtures.py): **kept: the phone app wire (holdspeak/phone/contract.py:201, phone/events.py:6, phone/actions.py:7) and Needs-you verb hrefs (needs_you_membership.py)**
- POST `/api/phone/devices` web.routes.phone (named in: holdspeak/phone/contract.py, holdspeak/phone/devices.py, holdspeak/principals.py, scripts/record_phone_fixtures.py): **kept: the phone app wire (holdspeak/phone/contract.py:201, phone/events.py:6, phone/actions.py:7) and Needs-you verb hrefs (needs_you_membership.py)**
- GET `/api/phone/events` web.routes.phone (named in: holdspeak/phone/events.py, holdspeak/principals.py, scripts/record_phone_fixtures.py): **kept: the phone app wire (holdspeak/phone/contract.py:201, phone/events.py:6, phone/actions.py:7) and Needs-you verb hrefs (needs_you_membership.py)**
- POST `/api/phone/messages/{message_id}/decide` web.routes.phone (named in: holdspeak/phone/actions.py, holdspeak/principals.py, holdspeak/services/needs_you_membership.py, holdspeak/web/announce.py, …): **kept: the phone app wire (holdspeak/phone/contract.py:201, phone/events.py:6, phone/actions.py:7) and Needs-you verb hrefs (needs_you_membership.py)**
- POST `/api/phone/messages/{message_id}/wait` web.routes.phone (named in: holdspeak/phone/actions.py, holdspeak/principals.py, holdspeak/services/needs_you_membership.py, holdspeak/web/announce.py, …): **kept: the phone app wire (holdspeak/phone/contract.py:201, phone/events.py:6, phone/actions.py:7) and Needs-you verb hrefs (needs_you_membership.py)**
- WS `/api/phone/ws` web.routes.phone (named in: holdspeak/principals.py): **kept: the phone app wire (holdspeak/phone/contract.py:201, phone/events.py:6, phone/actions.py:7) and Needs-you verb hrefs (needs_you_membership.py)**
- POST `/api/principals/agents` web.routes.system.gate_routes (named in: holdspeak/coder_gate.py, holdspeak/principals.py): **kept: the coder gate hook (holdspeak/coder_gate.py:295,329,505,543,853,884)**
- DELETE `/api/principals/agents/{identity}` web.routes.system.gate_routes (named in: holdspeak/coder_gate.py, holdspeak/principals.py): **left: security review**
- DELETE `/api/principals/self` web.routes.system.gate_routes (named in: holdspeak/coder_gate.py, holdspeak/principals.py): **kept: the coder gate hook (holdspeak/coder_gate.py:295,329,505,543,853,884)**
- POST `/api/profiles` web.routes.primitives.profiles (named in: holdspeak/inference_targets.py, scripts/walk_hs84_live.py, scripts/walk_hs85_live.py, scripts/walk_hsm25_live.py): **parked**
- DELETE `/api/profiles/{profile_id}` web.routes.primitives.profiles (named in: holdspeak/inference_targets.py, scripts/walk_hs84_live.py, scripts/walk_hs85_live.py, scripts/walk_hsm25_live.py): **parked**
- PUT `/api/profiles/{profile_id}` web.routes.primitives.profiles (named in: holdspeak/inference_targets.py, scripts/walk_hs84_live.py, scripts/walk_hs85_live.py, scripts/walk_hsm25_live.py): **parked**
- GET `/api/programs/{program_id}/requirements/{requirement_id}/evidence` web.routes.programs (named in: holdspeak/commands/program.py, holdspeak/program_operations.py, holdspeak/sdk/programs.py, holdspeak/services/needs_you_membership.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- POST `/api/project-setups` web.routes.project_setup: **kept: HTTP twin of MCP project.setup (tests/integration/test_provider_routes.py mounts it)**
- POST `/api/projects` web.routes.projects (named in: .githooks/workbench/app.js, holdspeak/agent_operations.py, holdspeak/operations.py, holdspeak/principals.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- POST `/api/projects/{project_id}/items` web.routes.projects (named in: .githooks/workbench/app.js, holdspeak/agent_operations.py, holdspeak/operations.py, holdspeak/principals.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- PATCH `/api/projects/{project_id}/items/{item_id}` web.routes.projects (named in: .githooks/workbench/app.js, holdspeak/agent_operations.py, holdspeak/operations.py, holdspeak/principals.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- POST `/api/projects/{project_id}/items/{item_id}/transition` web.routes.projects (named in: .githooks/workbench/app.js, holdspeak/agent_operations.py, holdspeak/operations.py, holdspeak/principals.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- DELETE `/api/projects/{project_id}/meetings/{meeting_id}` web.routes.projects (named in: .githooks/workbench/app.js, holdspeak/agent_operations.py, holdspeak/operations.py, holdspeak/principals.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- GET `/api/providers/confluence/connections` web.routes.providers: **kept: HTTP twin of an MCP provider_* tool (TestJiraMcpParity, TestJiraDiscoverMcpParity); jira recheck also scripts/record_room_wires.py:1163**
- POST `/api/providers/confluence/validate` web.routes.providers (named in: holdspeak/web/announce.py): **kept: HTTP twin of an MCP provider_* tool (TestJiraMcpParity, TestJiraDiscoverMcpParity); jira recheck also scripts/record_room_wires.py:1163**
- POST `/api/providers/github/validate-repo` web.routes.providers (named in: holdspeak/web/announce.py): **kept: HTTP twin of an MCP provider_* tool (TestJiraMcpParity, TestJiraDiscoverMcpParity); jira recheck also scripts/record_room_wires.py:1163**
- GET `/api/providers/jira/connections` web.routes.providers (named in: scripts/record_room_wires.py): **kept: HTTP twin of an MCP provider_* tool (TestJiraMcpParity, TestJiraDiscoverMcpParity); jira recheck also scripts/record_room_wires.py:1163**
- POST `/api/providers/jira/connections/{ref}/recheck` web.routes.providers (named in: scripts/record_room_wires.py): **kept: HTTP twin of an MCP provider_* tool (TestJiraMcpParity, TestJiraDiscoverMcpParity); jira recheck also scripts/record_room_wires.py:1163**
- POST `/api/providers/jira/search` web.routes.providers (named in: holdspeak/web/announce.py): **kept: HTTP twin of an MCP provider_* tool (TestJiraMcpParity, TestJiraDiscoverMcpParity); jira recheck also scripts/record_room_wires.py:1163**
- POST `/api/providers/jira/validate-scope` web.routes.providers (named in: holdspeak/web/announce.py): **kept: HTTP twin of an MCP provider_* tool (TestJiraMcpParity, TestJiraDiscoverMcpParity); jira recheck also scripts/record_room_wires.py:1163**
- GET `/api/reach/packages` web.routes.briefing: **parked**
- GET `/api/recipes/{recipe_id}` web.routes.primitives.recipes (named in: apple/Sources/Providers/Desktop/HTTPDesktopClient.swift, apple/Sources/Providers/Providers.swift, apple/Tests/ProvidersTests/DesktopClientTests.swift, scripts/record_chrome_palette.py, …): **parked (#PR_NUM, the left-routes pass)**
- POST `/api/recipes/{recipe_id}/chat` web.routes.primitives.recipes (named in: apple/Sources/Providers/Desktop/HTTPDesktopClient.swift, apple/Sources/Providers/Providers.swift, apple/Tests/ProvidersTests/DesktopClientTests.swift, scripts/record_chrome_palette.py, …): **parked (#PR_NUM, the left-routes pass)**
- POST `/api/recipes/{recipe_id}/invocations/{invocation_id}/cancel` web.routes.primitives.recipes (named in: apple/Sources/Providers/Desktop/HTTPDesktopClient.swift, apple/Sources/Providers/Providers.swift, apple/Tests/ProvidersTests/DesktopClientTests.swift, scripts/record_chrome_palette.py, …): **parked (#PR_NUM, the left-routes pass)**
- GET `/api/recordings/{recording_id}` web.routes.recordings (named in: holdspeak/web/announce.py, scripts/record_recordings_fixtures.py): **kept: scripts/record_recordings_fixtures.py:69,75 records the web fixtures through it**
- GET `/api/scheduled-recordings/{schedule_id}` web.routes.scheduled_recordings (named in: scripts/door_walk_hs144.py, scripts/schedule_walk_hs136.py): **parked (#PR_NUM, the left-routes pass)**
- POST `/api/skills` web.routes.primitives.workbenches: **left: other lane**
- DELETE `/api/skills/{skill_id}` web.routes.primitives.workbenches: **left: other lane**
- POST `/api/steward/trigger` web.routes.steward (named in: holdspeak/principals.py, holdspeak/room_operations.py, holdspeak/services/watch_service.py): **kept: declared (an http exposure in holdspeak/*operations.py)**
- GET `/api/thoughts/default-context` web.routes.primitives.thoughts: **kept: HTTP twin of MCP thought.get_default_context (test_refinement_default_context.py fences the pair)**
- GET `/api/thoughts/{thought_id}` web.routes.primitives.thoughts (named in: holdspeak/operations.py, scripts/door_walk_hs144.py, scripts/philo5_pairs.py, scripts/record_chrome_palette.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- POST `/api/threads/{thread_id}/compact` web.routes.threads (named in: holdspeak/mcp/tools.py, holdspeak/services/ask_desk.py, scripts/door_walk_hs144.py, scripts/record_chrome_palette.py, …): **parked**
- POST `/api/walks` web.routes.walks (named in: holdspeak/web/announce.py, scripts/walk.py): **kept: scripts/walk.py (the Walk)**
- GET `/api/walks/{walk_id}` web.routes.walks (named in: holdspeak/web/announce.py, scripts/walk.py): **kept: scripts/walk.py (the Walk)**
- GET `/api/watches/{watch_id}` web.routes.watches (named in: holdspeak/principals.py, holdspeak/room_operations.py, holdspeak/services/watch_service.py, scripts/record_needs_you_fixture.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- PATCH `/api/watches/{watch_id}` web.routes.watches (named in: holdspeak/principals.py, holdspeak/room_operations.py, holdspeak/services/watch_service.py, scripts/record_needs_you_fixture.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- POST `/api/watches/{watch_id}/baseline` web.routes.watches (named in: holdspeak/principals.py, holdspeak/room_operations.py, holdspeak/services/watch_service.py, scripts/record_needs_you_fixture.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- PUT `/api/watches/{watch_id}/rules` web.routes.watches (named in: holdspeak/principals.py, holdspeak/room_operations.py, holdspeak/services/watch_service.py, scripts/record_needs_you_fixture.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- POST `/api/watches/{watch_id}/test` web.routes.watches (named in: holdspeak/principals.py, holdspeak/room_operations.py, holdspeak/services/watch_service.py, scripts/record_needs_you_fixture.py, …): **kept: declared (an http exposure in holdspeak/*operations.py)**
- DELETE `/api/workbenches/{workbench_id}` web.routes.primitives.workbenches (named in: scripts/automations_walk.py, scripts/record_chrome_palette.py, scripts/surface_census_walk.py, scripts/walk_working_desk_legs.py): **left: other lane**
- POST `/api/workbenches/{workbench_id}/runs/{parent_operation_id}/cancel` web.routes.primitives.workbenches (named in: scripts/automations_walk.py, scripts/record_chrome_palette.py, scripts/surface_census_walk.py, scripts/walk_working_desk_legs.py): **left: other lane**
- GET `/api/workflows` web.routes.primitives.workflows (named in: scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: the UAT conductor seeds and probes them (uat/conductor/induction/seeds.py:40-41, probes.py:144,149); atlas case p13.chain.pullout; MCP desk.* kind=chains/workflows calls the same service methods**
- POST `/api/workflows` web.routes.primitives.workflows (named in: scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: the UAT conductor seeds and probes them (uat/conductor/induction/seeds.py:40-41, probes.py:144,149); atlas case p13.chain.pullout; MCP desk.* kind=chains/workflows calls the same service methods**
- DELETE `/api/workflows/{workflow_id}` web.routes.primitives.workflows (named in: scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: the UAT conductor seeds and probes them (uat/conductor/induction/seeds.py:40-41, probes.py:144,149); atlas case p13.chain.pullout; MCP desk.* kind=chains/workflows calls the same service methods**
- GET `/api/workflows/{workflow_id}` web.routes.primitives.workflows (named in: scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: the UAT conductor seeds and probes them (uat/conductor/induction/seeds.py:40-41, probes.py:144,149); atlas case p13.chain.pullout; MCP desk.* kind=chains/workflows calls the same service methods**
- PUT `/api/workflows/{workflow_id}` web.routes.primitives.workflows (named in: scripts/record_chrome_palette.py, scripts/surface_census_walk.py): **kept: the UAT conductor seeds and probes them (uat/conductor/induction/seeds.py:40-41, probes.py:144,149); atlas case p13.chain.pullout; MCP desk.* kind=chains/workflows calls the same service methods**

## Pages, documents and token links (29)

A browser opens these by URL (address bar, link, QR code). A fetch never calls them, so `consumers == []` is expected here.

- GET `/` web.routes.pages
- GET `/activity` web.routes.pages
- GET `/b/{token}` web.routes.briefing
- GET `/cadence` web.routes.pages
- GET `/commands` web.routes.pages
- GET `/companion` web.routes.pages
- GET `/conductor` web.routes.pages
- GET `/design/components` web.routes.pages
- GET `/desk` web.routes.pages
- GET `/dictation` web.routes.pages
- GET `/docs` fastapi.applications
- GET `/docs/dictation-runtime` web.routes.pages
- GET `/docs/oauth2-redirect` fastapi.applications
- GET `/history` web.routes.pages
- GET `/live` web.routes.pages
- GET `/meetings` web.routes.pages
- GET `/models` web.routes.pages
- GET `/openapi.json` fastapi.applications
- GET `/presence` web.routes.pages
- GET `/profiles` web.routes.pages
- GET `/r/{recording_id}/{token}/{name}` web.routes.recordings
- GET `/redoc` fastapi.applications
- GET `/settings` web.routes.pages
- GET `/setup` web.routes.pages
- GET `/studio` web.routes.pages
- GET `/terminals` web.routes.pages
- GET `/w/{token}` web.routes.walks
- GET `/welcome` web.routes.pages
- GET `/workbench` web.routes.pages

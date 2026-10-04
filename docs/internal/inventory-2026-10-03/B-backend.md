# Inventory B — the backend

Date: 2026-10-03. Commit: `6ccfa4e0d` (origin/main). Read-only. Paths are relative to the repository root.

Method: static reads, an import graph built with `ast`, `scripts/gen_docs.sh`, and two boots of a real hub (`holdspeak web --no-open`) on a throwaway HOME, port 48731. The hub was queried over HTTP and over `POST /api/mcp`. No test suite was run.

## 0. Headline counts

- Python modules in `holdspeak/`: 706 files, 258,180 lines.
- HTTP surface: 717 routes in 100 families (688 OpenAPI operations on the live hub, plus pages and 3 WebSockets). The generated reference matches the live hub.
- Routes with a web caller: 498. Tests only: 122. Other caller only: 76 (30 of these are called by the Swift app, the Firefox extension or the device firmware). Orphans: 19 product routes, plus `/redoc` and `/docs/oauth2-redirect`.
- Services: 124 modules, 86,745 lines in `holdspeak/services/`.
- MCP tools: 246 (65 in `holdspeak/mcp/tools.py`, 181 in 21 family modules). 16 resources. `tools.py` is 1,345 lines now, not 6.4k.
- Application operations (the shared contract): 103 (`docs/generated/operations.json`).
- CLI: 2 entry points (`pyproject.toml` `[project.scripts]`), 19 subcommands of `holdspeak`.
- Background loops: 16 found. 13 run in a default boot. 2 are never started by default (cadence, wake word). 1 starts but does nothing by default (rails observer). 8 more threads start only per event.

## 0.1 The ten most important findings

1. **Ten MCP tools fail on every call in the real product.** `workbench.run`, `recipe.run`, `ask.run`, `cadence.get_loop`, `sequence.run`, `workflow.run`, `watch.refresh`, `reaction.process` answer `async MCP tools cannot execute inside an active event loop`. `thought.refine` and `thought.answer_and_continue` answer `MCP refinement runtime is not started`. Cause: the hub route runs a tool on the event loop unless its operation declares `blocking_io` (`holdspeak/web/routes/mcp_http.py:216-221`), and each `_run` helper refuses when a loop is running (`holdspeak/mcp/tools.py:810-815`, `families/ask.py:90`, `families/cadence.py:170`, `families/sequence.py:74`, `families/reactions.py:61`). The stdio sidecar is only a proxy to that route (`holdspeak/mcp/server.py:1-40`), so there is no transport where these tools work. `configure_runtime` for thoughts has no product caller (`holdspeak/mcp/families/thought.py:215`; callers are `tests/unit/test_mcp_thoughts.py:288` and `tests/integration/_mcp_walk_server.py:73` only). Proof: live calls, section 4.3.
2. **Every scheduled loop that should run does run.** The 2026-09-13 audit's two missing callers are paid: the intel drainer starts (`holdspeak/web_server.py:1393-1397`) and the heartbeat sweeps (`holdspeak/runtime/heartbeat.py:71`). Boot log, section 1.1.
3. **MCP no longer talks to the database by hand.** Only 3 direct `db.` calls remain in `holdspeak/mcp/` (`tools.py:1127`, `tools.py:1132`, `families/thread.py:57`). The owner's ruling is met at the service level.
4. **But MCP still builds its own services in many places.** Ten families and four core services never ask the composition root. The worst: `heartbeat.run_now` builds a bare `WatchService` (`holdspeak/mcp/families/heartbeat.py:90`), which `holdspeak/runtime/heartbeat.py:22-45` says loses the Jira adapter wired to the real `acli` runner.
5. **There are two watch systems.** `ReactionService` watches (`/api/automations/watches`, tools `watch.*`, ticked by `holdspeak/workbench_conductor.py:575-578`) and `WatchService` watches (`/api/watches`, tools `project.watch.*`, ticked by the heartbeat). 14 of 22 `automations` routes have no web caller.
6. **There are three decision surfaces.** `web/routes/decisions.py` (8 routes), `web/routes/decision_records.py` (9), `web/routes/primitives/decisions.py` (7). `decisions.py:66-67,100` reads two tables by hand to tell them apart.
7. **219 routes have no web caller (31%).** Whole families are test-only: `primitives.model_profiles` (8 routes, 0 web), `desk_actuators` (7, 0 web), `dictation.project_docs` (5, 0 web), `mesh` (5, callers are the CLI and Swift only), most of `activity.enrichment` (9 of 14), `cadence` (7 of 13).
8. **1,062 lines of dead duplicate models.** `holdspeak/db/models/{actions,activity,infra,knowledge,meeting,workbench}.py` have no importer; their classes also exist in `holdspeak/db/models/__init__.py`.
9. **With nothing configured, only dictation and recording work.** Whisper `base` downloads and loads on first boot. All 7 AI assignment rows are `no_assignment`. Summaries, briefs with model text, Ask and thoughts need an engine the owner must set. The first-run screen points at `runs-on-destinations` because the default model path `~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf` does not exist (`holdspeak/config/meeting.py:36`).
10. **25 MCP tools have no test that names them**, including all 5 `concierge.*` tools and all 8 Jira/Confluence `provider.*` tools. `recipe.chat` is retired but still listed (`holdspeak/mcp/tools.py:267`, `tools.py:1023-1029`).

## 1. Background processes and loops

"Default boot" means `holdspeak` or `holdspeak web` with a fresh HOME.

| # | Name | Started at | What it does | Runs in a default boot? | Evidence | Verdict |
|---|---|---|---|---|---|---|
| 1 | Web server thread (uvicorn) | `holdspeak/web_server.py:424` | Serves HTTP, WebSocket, MCP | Yes | Boot log: `Meeting web server started: http://127.0.0.1:48731`; 688 operations served | ALIVE |
| 2 | Heartbeat (`HoldSpeakHeartbeat`) | `holdspeak/runtime/heartbeat.py:71`, called from `holdspeak/runtime/ownership.py:150` | Every 60 s checks if a sweep is due; a sweep evaluates due watches, refreshes calendar, may notify | Yes, if this hub owns the database | Boot log: `heartbeat sweep: watches=0 rooms=0 held=False duration=3ms`; `tests/unit/test_hs171_heartbeat_wire.py` | ALIVE |
| 3 | Intel queue drainer (`HoldSpeakIntelQueue`) | `holdspeak/web_server.py:1393-1397` → `holdspeak/intel_queue.py:877` | Every 15 s runs queued meeting-intelligence jobs | Yes, if owner | Boot log: `Intel queue drainer started (poll 15s)`; `tests/unit/test_phase200_intel_drain.py` | ALIVE (idle with no engine: jobs wait) |
| 4 | Workbench conductor | `holdspeak/web_server.py:1348` → `holdspeak/workbench_conductor.py:515` | Every 60 s: scheduled workbenches, Reaction watches and reactions, Resourceful tick, steward `run_due` and cadence projections (`workbench_conductor.py:533-645`) | Yes | Boot log: `Workbench conductor started`. No test names `start_conductor` | ALIVE |
| 5 | Scheduled recording conductor | `holdspeak/web_server.py:1371` → `holdspeak/scheduled_recording_conductor.py:126` | Every 60 s arms and starts scheduled recordings; timers stop them (`:274`, `:562`) | Yes | Boot log: `Scheduled recording conductor started`. No test names the start function | ALIVE |
| 6 | Calendar ingest conductor | `holdspeak/web_server.py:1383` → `holdspeak/calendar_ingest_conductor.py:1084` | One refresh at boot; later refreshes ride the heartbeat sweep. The own thread (`:223`) is retired (`:1087-1093`) | Object yes, thread no | `tests/unit/test_hs175_calendar_wire.py`; shutdown log `Calendar ingest conductor stopped` | ALIVE through the heartbeat. `CalendarIngestConductor.start()` and `_loop` are dead code |
| 7 | MIR plugin queue (`HoldSpeakMirPluginQueue`) | `holdspeak/web_runtime.py:500` | Every 0.6 s runs deferred meeting-plugin jobs (`holdspeak/runtime/plugin_queue.py:120-125`) | Yes | Thread start is unconditional. No test names the loop | ALIVE, idle by default: the intent router is opt-in (`holdspeak/config/meeting.py:93`; setup status says `MIR-01 routing pipeline disabled (opt-in)`) |
| 8 | Cadence engine (`HoldSpeakCadenceEngine`) | `holdspeak/runtime/ownership.py:144` | Ticks open loops, pushes the daily brief | No. `cadence.enabled` defaults to False (`holdspeak/config/integrations.py:205`) | `holdspeak/runtime/cadence.py:19-38` | NEVER STARTED by default |
| 9 | Duration broadcaster | `holdspeak/web_server.py:1295` | Every 1 s sends the meeting duration frame | Yes | `web_server.py:1480-1490`. No test | ALIVE; does nothing with no meeting |
| 10 | Coder frames watcher | `holdspeak/web_server.py:1296` | Every 2 s stats the agent-session file, sends a frame on change | Yes | `web_server.py:1505-1545`. No test | ALIVE; does nothing unless agent hooks write |
| 11 | Rails observer | `holdspeak/web_server.py:1297` | Tails Delivery Workbench events and writes journal notes with a model | Loop yes, work no. `rails_observer.enabled` defaults to False (`holdspeak/config/integrations.py:261`) | `web_server.py:1547-1553` | STARTED BUT DOES NOTHING by default |
| 12 | Kernel liveness | `holdspeak/web_server.py:1315-1316` | Every 1 s ends work whose executor stopped reporting | Yes | `web_server.py:1492-1503`; `tests/unit/test_phase200_meeting_outcomes.py` | ALIVE |
| 13 | Refinement coordinator heartbeat | `holdspeak/web_server.py:1300` → `holdspeak/services/refinement_coordinator.py:89` | Keeps thought-refinement leases alive, recovers at boot | Yes | `tests/unit/test_refinement_coordinator.py` | ALIVE |
| 14 | Transcriber warm-up (one shot) | `holdspeak/web_runtime.py:507` → `holdspeak/runtime/transcriber_state.py:211` | Loads Whisper at boot | Yes | Boot log: `MLX model loaded from mlx-community/whisper-base-mlx` | ALIVE |
| 15 | Wake word listener | `holdspeak/wake_word.py:86`, synced at `holdspeak/web_runtime.py:534` | Listens for "hey jarvis" | No. `wake_word.enabled` defaults to False (`holdspeak/config/device.py:70`) | `tests/unit/test_wake_word.py` | NEVER STARTED by default |
| 16 | Hotkey listener | `holdspeak/web_runtime.py:514-519` | Hold-to-talk dictation | Yes, if the OS grants the permission | Setup status: `global-hotkey pass` | ALIVE |

Per-event threads (start only when their event happens; not checked live): recording ticker `holdspeak/device_recording_tick.py:100`; meeting transcribe `holdspeak/meeting_session/session.py:606`; meeting intel `holdspeak/meeting_session/intel_analysis.py:53`; steward run `holdspeak/services/steward_contract.py:254` and trigger drain `:592`; thread turn `holdspeak/services/thread_service.py:587`; factory launch watcher `holdspeak/delivery/factory_launch.py:980`; MCP refinement runtime `holdspeak/mcp/refinement_runtime.py:49` (never started in the hub, finding 1).

Separate processes, started by hand: `holdspeak mesh serve` (`holdspeak/commands/mesh_serve.py`, 628 lines), `holdspeak node` (`holdspeak/commands/node_serve.py`, 546 lines), `holdspeak-mcp` (proxy, `holdspeak/mcp/server.py`). Not booted in this inventory.

### 1.1 Boot evidence (throwaway HOME, 2026-10-03)

```
20:47:24 | INFO | holdspeak.main | HoldSpeak web mode starting (no_open=True)
20:47:30 | INFO | holdspeak.web_runtime | intel.llm_capability enabled=False
20:47:30 | INFO | holdspeak.db.reconcile | Schema reconciled to version 80 (changed=True)
20:47:31 | INFO | holdspeak.web_server | Seeded 10 built-in skills
20:47:31 | INFO | holdspeak.workbench_conductor | Workbench conductor started
20:47:31 | INFO | holdspeak.scheduled_recording_conductor | Scheduled recording conductor started
20:47:31 | INFO | holdspeak.intel_queue_conductor | Intel queue drainer started (poll 15s)
20:47:31 | INFO | holdspeak.web_server | Meeting web server started: http://127.0.0.1:48731
20:47:42 | INFO | holdspeak.runtime.heartbeat | heartbeat sweep: watches=0 rooms=0 held=False duration=3ms
20:49:21 | INFO | holdspeak.calendar_ingest_conductor | Calendar ingest conductor stopped
20:49:21 | INFO | holdspeak.workbench_conductor | Workbench conductor stopped
20:49:21 | INFO | holdspeak.scheduled_recording_conductor | Scheduled recording conductor stopped
20:49:21 | INFO | holdspeak.intel_queue_conductor | Stopping the intel drainer; waiting up to 60s for an in-flight model call to finish.
```

Second boot (network allowed): `20:53:31 | INFO | holdspeak.transcribe | MLX model loaded from mlx-community/whisper-base-mlx via model-holder`. The first boot ran with `HF_HUB_OFFLINE=1` (my setting) and the warm-up failed with `LocalEntryNotFoundError`; that is what a machine with no network sees.

Limit: the log names the conductors that log a start line. Loops 7, 9, 10, 11, 12 write no start line; their "runs" verdict rests on the unconditional start call, not on a log line.

### 1.2 CLI entry points

`holdspeak = holdspeak.main:main`, `holdspeak-mcp = holdspeak.mcp.server:main` (`pyproject.toml` `[project.scripts]`).

Subcommands of `holdspeak` (parsers at `holdspeak/main.py:84-443`, dispatch at `holdspeak/main.py:454-574`): `web` (default), `meeting`, `history`, `actions`, `intel`, `dictation`, `agent-hook`, `gate`, `cadence`, `control-mode`, `device-psk`, `memory`, `doctor`, `import`, `mesh serve`, `node`, `backup`, `restore`, `seed`. Only `web` was run. The others were not run; their liveness is unknown.

## 2. Route families

Source: `docs/generated/api-reference.json` (717 routes), checked against the live hub's `/openapi.json` (the only differences are `:path` spellings, pages and WebSockets).

How a caller was found: the route path, with each `{param}` as a wildcard, searched as text in `web/src` (non-test), in web tests, in `tests/` and `uat/`, in `apple/`, `extensions/`, `aipi-lite/`, `agent/`, `scripts/`, `dogfood/`, and in backend Python outside the route files.

Limits: the search is lexical. A web client that builds a URL from parts is missed (false "no caller"). A path that appears in `holdspeak/principals.py` or `holdspeak/operations.py` is an authority map entry, not a caller, but counts in "other". The HTTP method is not checked. MCP does not call HTTP routes; it calls the same services, so the last column names the tools that do the same job.

| Family | Routes | With a web caller | Tests only | Other caller only (CLI, Swift app, extension, scripts, backend text) | Orphans | MCP tools for the same job |
|---|---|---|---|---|---|---|
| device_audio_ws | 1 | 0 | 0 | 1 | 0 | none |
| fastapi.applications | 4 | 0 | 0 | 2 | 2 | none |
| activity.candidates | 6 | 4 | 2 | 0 | 0 | none |
| activity.enrichment | 14 | 2 | 10 | 2 | 0 | none |
| activity.ledger | 7 | 5 | 2 | 0 | 0 | none |
| activity.nudges | 4 | 2 | 1 | 1 | 0 | nudge.* |
| activity.plugin_jobs | 5 | 3 | 2 | 0 | 0 | plugin_job.* |
| activity.rules | 6 | 4 | 2 | 0 | 0 | none |
| authority | 7 | 2 | 1 | 2 | 2 | none |
| automations | 22 | 8 | 14 | 0 | 0 | reaction.*, watch.*, event.list, practice_recipe.* |
| cadence | 13 | 4 | 7 | 2 | 0 | cadence.* |
| calendar_events | 3 | 2 | 1 | 0 | 0 | none |
| calendar_snapshot | 2 | 2 | 0 | 0 | 0 | none |
| calendar_sources | 1 | 1 | 0 | 0 | 0 | none |
| channels | 11 | 11 | 0 | 0 | 0 | channel.* |
| concierge | 6 | 6 | 0 | 0 | 0 | concierge.* |
| connections | 2 | 2 | 0 | 0 | 0 | connection.* |
| constitutional | 3 | 3 | 0 | 0 | 0 | none |
| core | 2 | 2 | 0 | 0 | 0 | none |
| decision_records | 9 | 7 | 2 | 0 | 0 | decision_record.* |
| decisions | 8 | 6 | 1 | 1 | 0 | decision.* |
| delivery | 4 | 1 | 1 | 2 | 0 | none |
| delivery_attempts | 2 | 2 | 0 | 0 | 0 | none |
| delivery_dossiers | 3 | 1 | 1 | 1 | 0 | none |
| delivery_factory | 3 | 3 | 0 | 0 | 0 | none |
| delivery_node | 5 | 1 | 2 | 2 | 0 | none |
| delivery_prs | 9 | 8 | 0 | 0 | 1 | none |
| delivery_terminal | 5 | 2 | 1 | 2 | 0 | none |
| desk_actuators | 7 | 0 | 5 | 2 | 0 | none |
| desk_seed | 2 | 2 | 0 | 0 | 0 | none |
| dictation.agent | 5 | 1 | 3 | 1 | 0 | none |
| dictation.blocks | 6 | 4 | 0 | 2 | 0 | none |
| dictation.floor | 3 | 2 | 1 | 0 | 0 | none |
| dictation.intents | 4 | 3 | 1 | 0 | 0 | none |
| dictation.kb | 4 | 3 | 0 | 1 | 0 | none |
| dictation.pipeline | 14 | 14 | 0 | 0 | 0 | dictation.*, pipeline.* |
| dictation.project_docs | 5 | 0 | 3 | 2 | 0 | none |
| door | 1 | 1 | 0 | 0 | 0 | door.* |
| follow_through | 3 | 2 | 0 | 0 | 1 | follow_through.* |
| front_door | 4 | 4 | 0 | 0 | 0 | none |
| inference_assignments | 5 | 5 | 0 | 0 | 0 | inference_assignment.* |
| mcp_http | 9 | 8 | 0 | 1 | 0 | (the transport itself) |
| meeting_import | 1 | 1 | 0 | 0 | 0 | meeting.import |
| meetings.action_items | 7 | 1 | 4 | 2 | 0 | none |
| meetings.aftercare | 6 | 3 | 1 | 2 | 0 | none |
| meetings.crud | 12 | 11 | 0 | 0 | 1 | meeting.* |
| meetings.insights | 3 | 2 | 1 | 0 | 0 | none |
| meetings.intel | 8 | 4 | 3 | 1 | 0 | meeting.run_intelligence |
| meetings.live | 5 | 4 | 1 | 0 | 0 | none |
| meetings.speakers | 3 | 1 | 2 | 0 | 0 | none |
| memory | 2 | 2 | 0 | 0 | 0 | memory.search |
| mesh | 5 | 0 | 0 | 5 | 0 | none |
| missioncontrol | 10 | 8 | 1 | 1 | 0 | none |
| model_library | 7 | 6 | 1 | 0 | 0 | model_library.* |
| monday_brief | 5 | 4 | 0 | 1 | 0 | monday_brief.* |
| pages | 19 | 19 | 0 | 0 | 0 | none |
| people | 26 | 25 | 1 | 0 | 0 | people.* |
| primitives.ask | 5 | 4 | 1 | 0 | 0 | ask.* |
| primitives.chains | 7 | 6 | 1 | 0 | 0 | sequence.* |
| primitives.decisions | 7 | 7 | 0 | 0 | 0 | desk.* (kind=decisions) |
| primitives.directories | 8 | 7 | 0 | 1 | 0 | zone.* |
| primitives.invocations | 3 | 1 | 0 | 1 | 1 | none |
| primitives.kbs | 8 | 7 | 0 | 1 | 0 | kb.* |
| primitives.model_profiles | 8 | 0 | 7 | 0 | 1 | none |
| primitives.notes | 5 | 5 | 0 | 0 | 0 | desk.* (kind=notes) |
| primitives.profiles | 11 | 3 | 6 | 2 | 0 | none |
| primitives.recipes | 9 | 7 | 1 | 1 | 0 | recipe.* |
| primitives.thoughts | 20 | 20 | 0 | 0 | 0 | thought.* |
| primitives.workbenches | 25 | 24 | 0 | 0 | 1 | workbench.* |
| primitives.workflows | 7 | 6 | 0 | 0 | 1 | workflow.* |
| project_briefs | 8 | 8 | 0 | 0 | 0 | project.* (brief) |
| project_door | 2 | 2 | 0 | 0 | 0 | project.get_room |
| project_reviews | 5 | 5 | 0 | 0 | 0 | project.open_review etc. |
| project_setup | 12 | 8 | 4 | 0 | 0 | project.setup.* |
| project_updates | 7 | 7 | 0 | 0 | 0 | project.*update* |
| projections | 2 | 2 | 0 | 0 | 0 | none |
| projects | 35 | 27 | 3 | 5 | 0 | project.* |
| proposals | 7 | 6 | 1 | 0 | 0 | proposal.* |
| providers | 16 | 11 | 1 | 1 | 3 | provider.* |
| repositories | 10 | 2 | 4 | 0 | 4 | none |
| roadmaps | 4 | 4 | 0 | 0 | 0 | none |
| scheduled_recordings | 6 | 6 | 0 | 0 | 0 | scheduled_recording.* |
| setup | 14 | 7 | 6 | 0 | 1 | inference.* |
| steward | 10 | 8 | 0 | 2 | 0 | project.*steward*, steward.* |
| sync | 2 | 1 | 0 | 1 | 0 | none |
| system.agent_capabilities | 1 | 0 | 0 | 1 | 0 | none |
| system.coder_factory_routes | 2 | 2 | 0 | 0 | 0 | none |
| system.coder_steering_routes | 16 | 7 | 0 | 8 | 1 | none |
| system.coders | 6 | 2 | 1 | 3 | 0 | coder.* |
| system.gate_routes | 12 | 4 | 3 | 5 | 0 | none |
| system.health | 3 | 3 | 0 | 0 | 0 | none |
| system.kernel_routes | 7 | 2 | 3 | 1 | 1 | kernel.* |
| system.settings | 6 | 6 | 0 | 0 | 0 | settings.* |
| system.settings_secrets | 3 | 3 | 0 | 0 | 0 | none |
| system.voice | 7 | 7 | 0 | 0 | 0 | none |
| system.voice_stream | 1 | 1 | 0 | 0 | 0 | none |
| system.ws | 1 | 1 | 0 | 0 | 0 | none |
| threads | 18 | 17 | 1 | 0 | 0 | thread.*, interview.* |
| tts | 3 | 3 | 0 | 0 | 0 | none |
| watches | 10 | 5 | 1 | 4 | 0 | project.watch.* |

### 2.1 Orphan routes (no caller found in web, tests, Swift app, extension, scripts or backend text)

- POST /api/authority/evaluate — holdspeak/web/routes/authority.py:70
- GET /api/authority/grants/{grant_id}/uses — holdspeak/web/routes/authority.py:137
- POST /api/coders/relay/{node}/arm — holdspeak/web/routes/system/coder_steering_routes.py:316
- POST /api/delivery/prs/launches/{launch_id}/input — holdspeak/web/routes/delivery_prs.py:174
- POST /api/follow-through/commit-decision — holdspeak/web/routes/follow_through.py (line not extracted)
- POST /api/inference/acquisitions/{job_id}/cancel — holdspeak/web/routes/setup.py:175
- POST /api/invocations/{invocation_id}/cancel — holdspeak/web/routes/primitives/invocations.py:53
- GET /api/kernel/executor/operations/{operation_id}/reconcile — holdspeak/web/routes/system/kernel_routes.py:114
- POST /api/meetings/{meeting_id}/capture/recover — holdspeak/web/routes/meetings/crud.py:195
- POST /api/model-profiles/{profile_id}/revisions — holdspeak/web/routes/primitives/model_profiles.py:80
- GET /api/providers/confluence/connections — holdspeak/web/routes/providers.py:454
- GET /api/providers/confluence/discover — holdspeak/web/routes/providers.py:497
- POST /api/providers/confluence/validate — holdspeak/web/routes/providers.py:540
- GET /api/repositories/{repository_id}/branches — holdspeak/web/routes/repositories.py:349
- POST /api/repositories/{repository_id}/checkout — holdspeak/web/routes/repositories.py:362
- GET /api/repositories/{repository_id}/file/{path:path} — holdspeak/web/routes/repositories.py:268
- PUT /api/repositories/{repository_id}/file/{path:path} — holdspeak/web/routes/repositories.py:286
- POST /api/workbenches/{workbench_id}/runs/{parent_operation_id}/cancel — holdspeak/web/routes/primitives/workbenches.py:233
- POST /api/workflows/runs/{parent_operation_id}/cancel — holdspeak/web/routes/primitives/workflows.py:67

### 2.2 Routes with test callers only (no product caller found)

- PATCH /api/action-items/{item_id} — holdspeak/web/routes/meetings/action_items.py:39
- PATCH /api/action-items/{item_id}/edit — holdspeak/web/routes/meetings/action_items.py:47
- PATCH /api/action-items/{item_id}/review — holdspeak/web/routes/meetings/action_items.py:43
- GET /api/activity/annotations — holdspeak/web/routes/activity/enrichment.py:53
- POST /api/activity/domains — holdspeak/web/routes/activity/ledger.py:36
- DELETE /api/activity/domains/{domain} — holdspeak/web/routes/activity/ledger.py:41
- PUT /api/activity/enrichment/connectors/{connector_id} — holdspeak/web/routes/activity/enrichment.py:28
- DELETE /api/activity/enrichment/connectors/{connector_id}/annotations — holdspeak/web/routes/activity/enrichment.py:43
- DELETE /api/activity/enrichment/connectors/{connector_id}/candidates — holdspeak/web/routes/activity/enrichment.py:48
- GET /api/activity/enrichment/connectors/{connector_id}/runs — holdspeak/web/routes/activity/enrichment.py:66
- GET /api/activity/enrichment/github/preview — holdspeak/web/routes/activity/enrichment.py:71
- POST /api/activity/enrichment/github/run — holdspeak/web/routes/activity/enrichment.py:75
- GET /api/activity/enrichment/jira/preview — holdspeak/web/routes/activity/enrichment.py:81
- POST /api/activity/enrichment/jira/run — holdspeak/web/routes/activity/enrichment.py:85
- POST /api/activity/enrichment/pipelines/{pipeline_id}/run — holdspeak/web/routes/activity/enrichment.py:61
- GET /api/activity/meeting-candidates/preview — holdspeak/web/routes/activity/candidates.py:26
- PUT /api/activity/meeting-candidates/{candidate_id}/status — holdspeak/web/routes/activity/candidates.py:40
- POST /api/activity/nudges/select/clear — holdspeak/web/routes/activity/nudges.py:33
- POST /api/activity/project-rules/apply — holdspeak/web/routes/activity/rules.py:48
- POST /api/activity/project-rules/preview — holdspeak/web/routes/activity/rules.py:43
- PATCH /api/all-action-items/{item_id}/edit — holdspeak/web/routes/meetings/action_items.py:63
- POST /api/ask/{invocation_id}/cancel — holdspeak/web/routes/primitives/ask.py:77
- DELETE /api/authority/grants/{grant_id} — holdspeak/web/routes/authority.py:128
- GET /api/automations/events — holdspeak/web/routes/automations.py (line not extracted)
- GET /api/automations/practice-recipes — holdspeak/web/routes/automations.py (line not extracted)
- GET /api/automations/practice-recipes/{recipe_id} — holdspeak/web/routes/automations.py (line not extracted)
- GET /api/automations/practice-recipes/{recipe_id}/plan — holdspeak/web/routes/automations.py (line not extracted)
- GET /api/automations/presets — holdspeak/web/routes/automations.py (line not extracted)
- GET /api/automations/reactions — holdspeak/web/routes/automations.py (line not extracted)
- POST /api/automations/reactions — holdspeak/web/routes/automations.py (line not extracted)
- POST /api/automations/reactions/process — holdspeak/web/routes/automations.py (line not extracted)
- PUT /api/automations/reactions/{reaction_id}/enabled — holdspeak/web/routes/automations.py (line not extracted)
- GET /api/automations/watches — holdspeak/web/routes/automations.py (line not extracted)
- POST /api/automations/watches — holdspeak/web/routes/automations.py (line not extracted)
- POST /api/automations/watches/{watch_id}/baseline — holdspeak/web/routes/automations.py (line not extracted)
- PUT /api/automations/watches/{watch_id}/enabled — holdspeak/web/routes/automations.py (line not extracted)
- POST /api/automations/watches/{watch_id}/test — holdspeak/web/routes/automations.py (line not extracted)
- GET /api/cadence/audit — holdspeak/web/routes/cadence.py (line not extracted)
- GET /api/cadence/brief — holdspeak/web/routes/cadence.py (line not extracted)
- GET /api/cadence/closeout — holdspeak/web/routes/cadence.py (line not extracted)
- POST /api/cadence/closeout/apply — holdspeak/web/routes/cadence.py (line not extracted)
- POST /api/cadence/loops/{loop_id}/close — holdspeak/web/routes/cadence.py (line not extracted)
- POST /api/cadence/loops/{loop_id}/kill — holdspeak/web/routes/cadence.py (line not extracted)
- POST /api/cadence/loops/{loop_id}/snooze — holdspeak/web/routes/cadence.py (line not extracted)
- GET /api/calendar/events — holdspeak/web/routes/calendar_events.py (line not extracted)
- POST /api/chains/runs/{parent_operation_id}/cancel — holdspeak/web/routes/primitives/chains.py:69
- POST /api/coders/clear-stale — holdspeak/web/routes/system/coders.py:376
- POST /api/decision-records/{record_id}/dispute — holdspeak/web/routes/decision_records.py (line not extracted)
- POST /api/decision-records/{record_id}/supersede — holdspeak/web/routes/decision_records.py (line not extracted)
- POST /api/decisions/{decision_id}/reject — holdspeak/web/routes/decisions.py (line not extracted)
- GET /api/delivery/events — holdspeak/web/routes/delivery.py:122
- GET /api/delivery/node/commands — holdspeak/web/routes/delivery_node.py:154
- POST /api/delivery/node/disconnect — holdspeak/web/routes/delivery_node.py:145
- GET /api/delivery/phases/{project}/{phase}/dossier — holdspeak/web/routes/delivery_dossiers.py:145
- POST /api/delivery/terminal/node/results — holdspeak/web/routes/delivery_terminal.py:220
- POST /api/desk/actuators/github/propose — holdspeak/web/routes/desk_actuators.py (line not extracted)
- POST /api/desk/actuators/github/{proposal_id}/decision — holdspeak/web/routes/desk_actuators.py (line not extracted)
- POST /api/desk/actuators/slack/propose — holdspeak/web/routes/desk_actuators.py (line not extracted)
- POST /api/desk/actuators/webhook/propose — holdspeak/web/routes/desk_actuators.py (line not extracted)
- POST /api/desk/actuators/webhook/{proposal_id}/decision — holdspeak/web/routes/desk_actuators.py (line not extracted)
- GET /api/dictation/agent-context — holdspeak/web/routes/dictation/agent.py:45
- POST /api/dictation/agent-context/clear — holdspeak/web/routes/dictation/agent.py:110
- POST /api/dictation/agent-context/summarize — holdspeak/web/routes/dictation/agent.py:141
- GET /api/dictation/floor — holdspeak/web/routes/dictation/floor.py:61
- GET /api/dictation/project-doc-suggestion — holdspeak/web/routes/dictation/project_docs.py:75
- POST /api/dictation/project-doc-suggestion/apply — holdspeak/web/routes/dictation/project_docs.py:90
- POST /api/dictation/project-doc-suggestion/dismiss — holdspeak/web/routes/dictation/project_docs.py:119
- GET /api/gate/audit — holdspeak/web/routes/system/gate_routes.py:160
- GET /api/gate/config — holdspeak/web/routes/system/gate_routes.py:169
- DELETE /api/inference-targets/{target_id} — holdspeak/web/routes/primitives/profiles.py:192
- GET /api/inference-targets/{target_id} — holdspeak/web/routes/primitives/profiles.py:119
- PUT /api/inference-targets/{target_id} — holdspeak/web/routes/primitives/profiles.py:132
- POST /api/inference-targets/{target_id}/probe — holdspeak/web/routes/primitives/profiles.py:86
- DELETE /api/inference-targets/{target_id}/secret — holdspeak/web/routes/primitives/profiles.py:174
- PUT /api/inference-targets/{target_id}/secret — holdspeak/web/routes/primitives/profiles.py:153
- GET /api/inference/acquisitions/{job_id} — holdspeak/web/routes/setup.py:164
- GET /api/inference/capabilities — holdspeak/web/routes/setup.py:142
- GET /api/inference/capabilities/{capability_id} — holdspeak/web/routes/setup.py:153
- POST /api/inference/model-library/connect-paired-device — holdspeak/web/routes/model_library.py:126
- GET /api/inference/setup — holdspeak/web/routes/setup.py:133
- POST /api/intel/retry/{meeting_id} — holdspeak/web/routes/meetings/intel.py:82
- GET /api/intel/summary — holdspeak/web/routes/meetings/intel.py:72
- PUT /api/intents/override — holdspeak/web/routes/dictation/intents.py:61
- POST /api/kernel/executor/claim — holdspeak/web/routes/system/kernel_routes.py:90
- POST /api/kernel/executor/operations/{operation_id}/receipt — holdspeak/web/routes/system/kernel_routes.py:98
- POST /api/kernel/operations/{operation_id}/decide — holdspeak/web/routes/system/kernel_routes.py:45
- POST /api/meetings/{meeting_id}/export/slack — holdspeak/web/routes/meetings/aftercare.py:48
- POST /api/meetings/{meeting_id}/intel-recovery/retry — holdspeak/web/routes/meetings/intel.py:114
- GET /api/meetings/{meeting_id}/plugin-runs — holdspeak/web/routes/meetings/insights.py:38
- POST /api/missioncontrol/rails/remote-events — holdspeak/web/routes/missioncontrol.py:208
- GET /api/model-profiles — holdspeak/web/routes/primitives/model_profiles.py:42
- POST /api/model-profiles — holdspeak/web/routes/primitives/model_profiles.py:50
- DELETE /api/model-profiles/{profile_id} — holdspeak/web/routes/primitives/model_profiles.py:96
- GET /api/model-profiles/{profile_id} — holdspeak/web/routes/primitives/model_profiles.py:64
- DELETE /api/model-profiles/{profile_id}/binding — holdspeak/web/routes/primitives/model_profiles.py:144
- POST /api/model-profiles/{profile_id}/binding — holdspeak/web/routes/primitives/model_profiles.py:112
- POST /api/model-profiles/{profile_id}/probe — holdspeak/web/routes/primitives/model_profiles.py:128
- GET /api/people/history — holdspeak/web/routes/people.py (line not extracted)
- POST /api/plugin-jobs/{job_id}/cancel — holdspeak/web/routes/activity/plugin_jobs.py:44
- POST /api/plugin-jobs/{job_id}/retry-now — holdspeak/web/routes/activity/plugin_jobs.py:39
- DELETE /api/principals/agents/{identity} — holdspeak/web/routes/system/gate_routes.py:57
- POST /api/project-setups/{session_id}/proposals/{proposal_id}/clarify — holdspeak/web/routes/project_setup.py (line not extracted)
- POST /api/project-setups/{session_id}/proposals/{proposal_id}/deselect — holdspeak/web/routes/project_setup.py (line not extracted)
- POST /api/project-setups/{session_id}/proposals/{proposal_id}/select — holdspeak/web/routes/project_setup.py (line not extracted)
- POST /api/project-setups/{session_id}/proposals/{proposal_id}/test — holdspeak/web/routes/project_setup.py (line not extracted)
- GET /api/projects/{project_id}/action-items — holdspeak/web/routes/projects.py:462
- GET /api/projects/{project_id}/briefings — holdspeak/web/routes/projects.py:67
- GET /api/projects/{project_id}/proposals — holdspeak/web/routes/proposals.py:88
- GET /api/projects/{project_id}/summary — holdspeak/web/routes/projects.py:453
- POST /api/providers/confluence/connections/{ref}/recheck — holdspeak/web/routes/providers.py:474
- POST /api/recipes/{recipe_id}/invocations/{invocation_id}/cancel — holdspeak/web/routes/primitives/recipes.py:165
- POST /api/repositories/{repository_id}/commit — holdspeak/web/routes/repositories.py:323
- POST /api/repositories/{repository_id}/stage — holdspeak/web/routes/repositories.py:304
- GET /api/repositories/{repository_id}/status — holdspeak/web/routes/repositories.py:339
- GET /api/repositories/{repository_id}/tree — holdspeak/web/routes/repositories.py:254
- GET /api/setup/hub-default-summary — holdspeak/web/routes/setup.py:58
- GET /api/setup/runtime-options — holdspeak/web/routes/setup.py:125
- GET /api/speakers/{speaker_id} — holdspeak/web/routes/meetings/speakers.py:45
- PATCH /api/speakers/{speaker_id} — holdspeak/web/routes/meetings/speakers.py:54
- POST /api/stop — holdspeak/web/routes/meetings/live.py:119
- GET /api/threads/{thread_id}/interview/promotions — holdspeak/web/routes/threads.py:108
- GET /api/watches — holdspeak/web/routes/watches.py:44
## 3. Services

The table counts importing files, from the `ast` import graph. "Test importers" counts files in `tests/`, `uat/`, `scripts/`.

### 3.1 The worst duplications

1. **Service composition is written three times.** The hub composes in `holdspeak/web_server.py` (for example `_gh_watch_service_kwargs`, `web_server.py:349`). `holdspeak/runtime/room_composition.py:13-50` composes the same Room services again as a fallback. `holdspeak/mcp/families/project.py:1067-1170` composes them a third time ("same wiring as web context" is the docstring on each builder). The three can drift.
2. **MCP paths that never ask the composition root.** `holdspeak/mcp/tools.py:945-948` (RecipeService, EventQueryService, DeskService, DecisionRecordService built bare on every call), `tools.py:1107-1116`, `tools.py:1146`, `tools.py:1257`; families `heartbeat.py:82-91`, `memory.py:40`, `settings.py:60`, `coder.py:58`, `concierge.py:137,164-166`, `interview.py:52`, `reactions.py:70`, `sequence.py:96,131`, `people.py:238`, `thread.py`. Families that do ask the root: ask, cadence, door, inference, inference_assignments, model_library, plugin_job, project, thought, channel, practice_recipe.
3. **The model-setup trio is built by hand in four places.** `InferenceSetupApplicationService` + `InferenceAcquisitionApplicationService` + `ModelLibraryApplicationService`: `holdspeak/mcp/tools.py:1107-1108`, `holdspeak/mcp/families/concierge.py:164-166`, `holdspeak/mcp/families/model_library.py:166-168`, `holdspeak/mcp/families/inference.py:41-42`.
4. **The `_run` helper is copied five times** (and is the broken one): `holdspeak/mcp/tools.py:810`, `families/ask.py:90`, `families/cadence.py:170`, `families/sequence.py:74`, `families/reactions.py:61`. A sixth variant is `families/thought.py:226`.
5. **Two watch systems** (finding 5): `holdspeak/services/reaction_service.py` (581 lines) and `holdspeak/services/watch_service.py` (1,730 lines).
6. **Three decision surfaces** (finding 6): `holdspeak/services/decision_record_service.py` (646), `holdspeak/services/decision_lifecycle_service.py` (211), the primitive decisions through `primitive_service.py`.
7. **Routes that still read the database by hand** (the rest go through services): `holdspeak/web/routes/front_door.py:93,127,225,254,331,407,417`; `holdspeak/web/routes/calendar_events.py:41,44,81,86,109,111`; `holdspeak/web/routes/decisions.py:66,67,100`; 5 calls in `holdspeak/web/routes/actuator_shared.py`.
8. **Two action-item route sets for one job.** `/api/action-items/{id}` (+`/edit`, `/review`) at `holdspeak/web/routes/meetings/action_items.py:39-47` and `/api/all-action-items/{id}` (+`/edit`, `/review`) at `:55-63`. Neither set has a web caller for the PATCH routes.
9. **Three model-target vocabularies.** `/api/profiles` (web-called), `/api/inference-targets` (6 of its routes test-only, `holdspeak/web/routes/primitives/profiles.py:86-192`), `/api/model-profiles` (8 routes, 0 web callers, `holdspeak/web/routes/primitives/model_profiles.py:42-144`; service `model_profile_service.py`, 1,441 lines).
10. **Only 17 of 108 route files use the operations contract.** `registry.invoke` appears 56 times in routes (`holdspeak/web/routes/projects.py` 14, `primitives/thoughts.py` 5, …) and 27 times in `holdspeak/mcp/tools.py`; 2 in families. The rest of both transports call service methods directly, each with its own argument handling.

Services with no route and no MCP importer are reached only through other services or the runtime; that is normal for helpers. `holdspeak/services/thread_tool_protocol.py` (85 lines) has no importer at all.

### 3.2 Service table

| Service module | Lines | Route importers | MCP importers | Service importers | Other product importers | Test importers |
|---|---|---|---|---|---|---|
| project_service | 4967 | 2 | 4 | 5 | 3 | 64 |
| inference_adoption_service | 3008 | 0 | 0 | 4 | 2 | 9 |
| project_update_service | 2562 | 0 | 2 | 3 | 2 | 15 |
| project_steward_service | 2511 | 0 | 1 | 1 | 2 | 15 |
| inference_assignment_service | 2499 | 2 | 3 | 4 | 2 | 84 |
| thread_service | 2397 | 2 | 0 | 0 | 0 | 14 |
| inference_route_plan_service | 2099 | 0 | 0 | 16 | 3 | 8 |
| inference_fallback_controller | 2088 | 0 | 0 | 4 | 2 | 4 |
| project_delta_service | 1926 | 0 | 2 | 0 | 2 | 16 |
| refinement_thought_service | 1904 | 1 | 1 | 6 | 1 | 26 |
| concierge_service | 1801 | 1 | 1 | 2 | 0 | 9 |
| tool_turn_controller | 1746 | 0 | 0 | 1 | 0 | 6 |
| watch_service | 1730 | 1 | 2 | 4 | 4 | 21 |
| jira_provider | 1729 | 0 | 1 | 5 | 1 | 5 |
| inference_parent_route_bundle_service | 1674 | 1 | 0 | 7 | 7 | 6 |
| sync_service | 1604 | 1 | 0 | 2 | 1 | 20 |
| project_setup_service | 1602 | 0 | 1 | 1 | 1 | 12 |
| monday_brief_service | 1534 | 1 | 2 | 1 | 2 | 24 |
| people_service | 1510 | 3 | 1 | 4 | 1 | 22 |
| model_profile_service | 1441 | 1 | 0 | 4 | 0 | 12 |
| refinement_context_service | 1381 | 0 | 0 | 5 | 1 | 8 |
| recipe_catalog | 1218 | 1 | 1 | 0 | 0 | 3 |
| preparation_brief_service | 1201 | 1 | 0 | 0 | 1 | 4 |
| confluence_provider | 1177 | 0 | 1 | 1 | 1 | 1 |
| proposal_bridge_service | 1115 | 1 | 1 | 0 | 1 | 8 |
| front_door_service | 1111 | 1 | 0 | 0 | 0 | 2 |
| inference_acquisition_service | 1041 | 0 | 4 | 1 | 1 | 19 |
| settings_service | 1034 | 1 | 1 | 0 | 1 | 10 |
| heartbeat_service | 993 | 1 | 2 | 1 | 1 | 8 |
| meeting_service | 936 | 6 | 2 | 0 | 2 | 20 |
| needs_you_aggregate | 927 | 1 | 0 | 6 | 1 | 9 |
| model_library_service | 917 | 1 | 3 | 0 | 1 | 20 |
| thread_tools | 875 | 0 | 0 | 2 | 0 | 13 |
| calendar_snapshot_service | 844 | 3 | 0 | 0 | 0 | 3 |
| sequence_workflow_service | 841 | 2 | 1 | 0 | 0 | 1 |
| channel_email | 780 | 0 | 0 | 1 | 0 | 5 |
| steward_contract | 755 | 0 | 0 | 1 | 0 | 1 |
| follow_through_service | 746 | 2 | 3 | 6 | 1 | 24 |
| watch_sources | 709 | 0 | 1 | 6 | 1 | 12 |
| workbench_service | 690 | 2 | 2 | 2 | 1 | 14 |
| inference_setup_service | 688 | 1 | 4 | 3 | 1 | 23 |
| door_service | 657 | 0 | 1 | 0 | 1 | 11 |
| decision_record_service | 646 | 1 | 2 | 2 | 0 | 15 |
| mesh_relay_authority | 645 | 0 | 0 | 1 | 0 | 1 |
| interview_service | 638 | 1 | 1 | 2 | 0 | 3 |
| channel_service | 634 | 0 | 1 | 1 | 1 | 4 |
| primitive_service | 620 | 2 | 2 | 1 | 3 | 20 |
| channel_cli | 601 | 0 | 0 | 3 | 0 | 8 |
| ask_service | 600 | 1 | 1 | 2 | 0 | 10 |
| refinement_coordinator | 590 | 0 | 1 | 1 | 1 | 5 |
| project_kernel | 585 | 1 | 0 | 10 | 1 | 6 |
| reaction_service | 581 | 1 | 1 | 3 | 2 | 16 |
| scheduled_recording_service | 578 | 1 | 1 | 0 | 0 | 3 |
| document_sources | 569 | 0 | 0 | 1 | 0 | 3 |
| recall_service | 549 | 1 | 0 | 0 | 0 | 3 |
| project_evidence_collector | 545 | 0 | 1 | 0 | 2 | 18 |
| channel_slack | 543 | 0 | 0 | 2 | 0 | 7 |
| tool_capability_service | 541 | 0 | 0 | 7 | 0 | 4 |
| connections_service | 522 | 0 | 1 | 0 | 2 | 3 |
| github_provider | 516 | 0 | 1 | 4 | 1 | 10 |
| room_people_service | 480 | 1 | 0 | 1 | 0 | 4 |
| channel_contract | 475 | 0 | 0 | 6 | 0 | 9 |
| support | 474 | 0 | 0 | 4 | 1 | 6 |
| thread_modes | 458 | 1 | 0 | 1 | 1 | 14 |
| resourceful_service | 445 | 1 | 0 | 0 | 1 | 1 |
| recipe_service | 416 | 1 | 2 | 0 | 0 | 8 |
| room_health_service | 410 | 0 | 0 | 2 | 0 | 1 |
| workbench_runner | 381 | 0 | 0 | 1 | 1 | 12 |
| thread_practice | 367 | 0 | 0 | 1 | 0 | 5 |
| project_door_service | 347 | 0 | 0 | 0 | 2 | 3 |
| attention_ranking | 331 | 0 | 0 | 1 | 0 | 1 |
| inference_semantic_adapters | 325 | 0 | 0 | 1 | 4 | 1 |
| meeting_deferred_queue_binding | 325 | 0 | 0 | 0 | 1 | 8 |
| suggested_source_service | 320 | 0 | 1 | 0 | 2 | 2 |
| cadence_service | 306 | 1 | 2 | 0 | 1 | 6 |
| meeting_intel_service | 304 | 1 | 1 | 1 | 2 | 18 |
| brief_carry | 302 | 1 | 0 | 2 | 0 | 2 |
| inference_service_route_policy | 293 | 0 | 0 | 1 | 0 | 1 |
| route_probe | 292 | 1 | 0 | 0 | 0 | 2 |
| mesh_service | 285 | 0 | 0 | 0 | 1 | 4 |
| refinement_application_service | 277 | 1 | 2 | 0 | 2 | 4 |
| tool_model_adapter | 261 | 0 | 0 | 3 | 0 | 3 |
| mission_control_service | 249 | 0 | 0 | 0 | 1 | 2 |
| tool_turn_service | 237 | 0 | 0 | 1 | 0 | 2 |
| desk_kernel | 236 | 0 | 0 | 2 | 1 | 2 |
| inference_owner_draft | 230 | 1 | 0 | 2 | 0 | 0 |
| agent_turn_service | 229 | 0 | 0 | 1 | 1 | 4 |
| dictation_service | 223 | 1 | 2 | 0 | 1 | 1 |
| decision_lifecycle_service | 211 | 1 | 0 | 1 | 0 | 11 |
| person_overlay | 200 | 1 | 1 | 1 | 0 | 1 |
| credential_service | 199 | 1 | 0 | 0 | 1 | 2 |
| profile_service | 199 | 1 | 0 | 2 | 0 | 7 |
| meeting_route_projection | 198 | 0 | 0 | 3 | 3 | 14 |
| observer | 198 | 2 | 0 | 42 | 3 | 11 |
| project_delegation | 194 | 2 | 0 | 0 | 0 | 1 |
| authority_service | 193 | 1 | 0 | 0 | 1 | 1 |
| coder_service | 191 | 3 | 1 | 0 | 1 | 0 |
| gate_service | 155 | 0 | 0 | 0 | 1 | 3 |
| delivery_service | 149 | 1 | 0 | 0 | 1 | 2 |
| meeting_aftercare_service | 141 | 1 | 0 | 0 | 1 | 2 |
| activity_enrichment_service | 139 | 1 | 0 | 0 | 0 | 0 |
| desk_delegation | 134 | 2 | 0 | 0 | 0 | 1 |
| event_query_service | 132 | 0 | 2 | 0 | 0 | 4 |
| schedule_delegation | 130 | 0 | 0 | 4 | 2 | 4 |
| actuator_service | 108 | 0 | 0 | 0 | 1 | 0 |
| invocation_service | 108 | 1 | 0 | 0 | 0 | 1 |
| setup_service | 107 | 0 | 0 | 0 | 1 | 4 |
| interview_contracts | 93 | 0 | 1 | 3 | 0 | 5 |
| thread_tool_protocol | 85 | 0 | 0 | 0 | 0 | 0 |
| profile_key_service | 70 | 0 | 0 | 1 | 1 | 7 |
| service_event_ledger | 68 | 0 | 0 | 11 | 1 | 3 |
| inference_capability_service | 67 | 0 | 1 | 0 | 2 | 1 |
| activity_meeting_candidate_service | 62 | 1 | 0 | 0 | 0 | 0 |
| desk_service | 54 | 2 | 2 | 0 | 0 | 7 |
| errors | 52 | 65 | 13 | 92 | 4 | 106 |
| sqlite_observer | 52 | 0 | 0 | 0 | 2 | 14 |
| activity_ledger_service | 48 | 1 | 0 | 0 | 0 | 0 |
| memory_service | 48 | 0 | 1 | 0 | 1 | 3 |
| activity_rules_service | 47 | 1 | 0 | 0 | 0 | 0 |
| plugin_job_service | 44 | 1 | 1 | 0 | 1 | 0 |
| projection_service | 43 | 1 | 0 | 0 | 1 | 3 |
| activity_nudge_service | 35 | 1 | 0 | 0 | 0 | 0 |
| kernel_read_service | 23 | 0 | 2 | 0 | 1 | 0 |
| inference_outcomes | 19 | 0 | 0 | 2 | 0 | 0 |

Total: 124 modules, 86745 lines.
## 4. MCP tools

### 4.1 Counts

246 tools on the live hub (`tools/list` over `POST /api/mcp`), 16 resources. No family failed to load (`DEGRADED_FAMILIES` empty). No duplicate names.

By prefix: project 50, thought 18, people 17, provider 13, cadence 11, workbench 10, meeting 9, channel 9, desk 8, model_library 7, decision_record 5, scheduled_recording 5, reaction 5, watch 5, inference_assignment 5, concierge 5, recipe 4, monday_brief 4, ask 4, plugin_job 4, heartbeat 4, interview 4, zone 3, kb 3, settings 3, follow_through 3, coder 3, practice_recipe 3, and 14 prefixes with 1 or 2 tools.

### 4.2 Which bypass services

None bypass the service layer in the sense of the owner's ruling, with three exceptions that touch repositories directly: `holdspeak/mcp/tools.py:1127` (`db.automations.list_provider_connections`), `holdspeak/mcp/tools.py:1132` (`db.cadence.list_loops`), `holdspeak/mcp/families/thread.py:57` (`db.threads.patch`). `holdspeak/mcp/resources.py` has 3 more direct reads.

What remains is the composition bypass in 3.1 items 1 to 3: the tool calls a service, but a service it built itself.

### 4.3 Broken (proved on the live hub at this commit)

| Tool | Answer | Source |
|---|---|---|
| `workbench.run` | `async MCP tools cannot execute inside an active event loop` | `holdspeak/mcp/tools.py:988`, `:1312` |
| `recipe.run` | same | `holdspeak/mcp/tools.py:1022` |
| `ask.run` | same | `holdspeak/mcp/families/ask.py:136` |
| `cadence.get_loop` | same | `holdspeak/mcp/families/cadence.py:202` |
| `sequence.run` | same | `holdspeak/mcp/families/sequence.py:108` |
| `workflow.run` | same | `holdspeak/mcp/families/sequence.py:143` |
| `watch.refresh` | same | `holdspeak/mcp/families/reactions.py:80` |
| `reaction.process` | same | `holdspeak/mcp/families/reactions.py:95` |
| `thought.refine` | `MCP refinement runtime is not started` | `holdspeak/mcp/families/thought.py:288`, `holdspeak/mcp/refinement_runtime.py:43` |
| `thought.answer_and_continue` | same | `holdspeak/mcp/families/thought.py:325` |

The calls used placeholder ids. The refusal comes before the id is read (`cadence.get_loop` with id `x` gave the loop error, not "not found"), so a real id gives the same answer. `thought.stop_refinement` (`holdspeak/mcp/families/thought.py:301-302`) uses the same `_run` and the same runtime; it was not called, so its state is unknown, not proved.

Why tests are green: a unit test calls `dispatch` with no running event loop, so `asyncio.run` works. The hub calls it inside the loop.

Also: `recipe.chat` is retired and always raises (`holdspeak/mcp/tools.py:1023-1029`) but stays in the catalogue (`tools.py:267`). `people.relationship.list` answers `people_store_unavailable` on a fresh HOME (expected: no People keystore).

Smoke result: 36 no-argument read tools were called; 35 answered without error. 187 tools need arguments and were not called. 23 no-argument write tools were skipped, then 7 of them were called by hand (`monday_brief.generate`, `desk.needs_you`, `heartbeat.run_now`, `cadence.run_now`, `channel.destinations`, `provider.github_connection` answered; `reaction.process` failed as above).

### 4.4 Untested (no test, UAT or script names the tool as a string)

25 tools:
- Core (`holdspeak/mcp/tools.py`): `workbench.add_item`, `meeting.stop_capture`, `meeting.export`, `meeting.proposals`, `proposal.confirm`, `proposal.dismiss`, `dictation.list`, `dictation.get`, `settings.hub`, `decision_record.create_from_meeting`, `decision_record.create_from_desk`.
- `thought.resume`.
- `concierge.detect`, `concierge.propose`, `concierge.probe`, `concierge.apply`, `concierge.download` (the whole family; `holdspeak/mcp/families/concierge.py` has 0 test importers).
- `provider.jira_connections`, `provider.jira_connection`, `provider.jira_discover`, `provider.jira_search`, `provider.jira_validate_scope`, `provider.confluence_connections`, `provider.confluence_discover`, `provider.confluence_validate_space`.

Limit: a test that builds the name from parts is missed.

## 5. Dead code candidates

### 5.1 Modules with no product importer

| Lines | Module | Notes |
|---|---|---|
| 162 | `holdspeak/db/models/actions.py` | No importer. Classes duplicated in `holdspeak/db/models/__init__.py` |
| 203 | `holdspeak/db/models/activity.py` | same |
| 126 | `holdspeak/db/models/infra.py` | same |
| 236 | `holdspeak/db/models/knowledge.py` | same (1 test importer) |
| 103 | `holdspeak/db/models/meeting.py` | same |
| 232 | `holdspeak/db/models/workbench.py` | same |
| 506 | `holdspeak/product_copy.py` | Only `scripts/phase93_copy_census.py:16` and 2 tests import it |
| 347 | `holdspeak/connector_fixtures.py` | 1 test importer |
| 213 | `holdspeak/realtime_frames.py` | 1 test importer; `web/src/runtime/frames.ts:3` calls it the canon it mirrors |
| 189 | `holdspeak/confluence_templates.py` | 1 test importer |
| 165 | `holdspeak/plugins/builtin/followup_ticket_actuator.py` | No registration found outside its own file; 1 test importer |
| 114 | `holdspeak/workrooms.py` | 1 test importer |
| 85 | `holdspeak/services/thread_tool_protocol.py` | No importer at all |
| 78 | `holdspeak/kernel/voice_resolve.py` | No importer at all |
| 24 | `holdspeak/web/routes/meetings/_shared.py` | No importer at all |
| 21 | `holdspeak/meeting_session/deferred_admission.py` | 2 test importers |

Total: 2,804 lines. The six `db/models` files (1,062 lines) were checked class by class for 8 classes; each exists once in `__init__.py`. The others are candidates: a string-based or plugin-style load would not show in the import graph.

### 5.2 Code that exists but does not run

- `CalendarIngestConductor.start()` / `_loop` (`holdspeak/calendar_ingest_conductor.py:219-227`): thread retired by HS-175-02 (`:1087-1093`).
- `recipe.chat` MCP tool: retired, kept for a stable count (`holdspeak/mcp/tools.py:1023-1029`).
- `HOLDSPEAK_MCP_STANDALONE`: the variable is ignored (`holdspeak/mcp/server.py:36-40`); 3 mentions remain.
- `holdspeak/mcp/refinement_runtime.py` (95 lines): never started in the hub.

### 5.3 Features behind flags that default to off

| Feature | Flag | Size |
|---|---|---|
| Cadence engine loop + Telegram | `cadence.enabled`, `cadence_telegram.enabled` (`holdspeak/config/integrations.py:205,233`) | `holdspeak/cadence/` package, `holdspeak/cadence_telegram.py`, `holdspeak/runtime/cadence.py` (191), `holdspeak/services/cadence_service.py` (306), 13 routes, 11 tools |
| Rails observer | `rails_observer.enabled` (`holdspeak/config/integrations.py:261`) | `holdspeak/rails_observer.py` |
| Wake word | `wake_word.enabled` (`holdspeak/config/device.py:70`) | `holdspeak/wake_word.py`, `holdspeak/runtime/wake_glue.py` (516) |
| Meeting intent router (MIR) | `intent_router_enabled` (`holdspeak/config/meeting.py:93`) | `holdspeak/plugins/` router, queue, 17 built-in plugins |
| Segment probe | `intent_segment_probe_enabled` (`holdspeak/config/meeting.py:110`) | `holdspeak/plugins/segment_probe.py` |
| Diarization | `diarization_enabled` (`holdspeak/config/meeting.py:146`) | `holdspeak/speaker_intel.py` |
| Voice macros | `macros.enabled` (`holdspeak/config/ui.py:119`) | `holdspeak/plugins/voice_macro_connector.py` |
| Desktop presence / mascot | `presence.enabled` (`holdspeak/config/device.py:34`) | `holdspeak/desktop_presence*.py` (4 files) |
| LLM target detect for dictation | `target_detect_llm_enabled` (`holdspeak/config/meeting.py:377`) | part of the dictation pipeline |
| Tool-call gate | off until `holdspeak gate install` (setup status `tool-call-gate`) | `holdspeak/coder_gate.py`, `holdspeak/commands/gate.py` (159), 12 gate routes |

I did not read the owner's real config, so "never on" means "off by default", not "off on his desk".

### 5.4 Parked directories and stray files

| Path | Lines |
|---|---|
| `web/src/features/project-room/_parked` | 11,919 |
| `web/src/desk/chair/_parked` | 5,501 |
| `.githooks/_parked` | 645 |
| `web/src/pages/cores/dictation/_parked` | 430 |
| `docs/internal/philo/phase-6/body/parked` | 113 |
| `scripts/_parked` | 49 |

Tracked at the repository root with no visible purpose: `screen-7268.log`, `screen-74701.log`. Side trees not inventoried here: `apple/` (484 files), `uat/` (290), `aipi-lite/` (127), `dogfood/` (99), `agent/` (15), `designer-handoff/` (11), `architecture/` (7), `extensions/` (4), `gallery/` (4).

## 6. Configuration and engines

Read from the live throwaway hub (`/api/setup/status`, `/api/inference/assignments`, `/api/connections`, `/api/runtime/status`, `/api/front-door/recommendation`) and from the config defaults.

| Core job | What it needs | With nothing configured |
|---|---|---|
| Dictation (hold, speak, release) | Whisper model (`model.name = "base"`, `holdspeak/config/model.py:14`), microphone, OS permission for hotkey and typing | Works. `base` downloads from Hugging Face on first boot (about 146 MB in the throwaway HOME) and loads in ~15 s. With no network the warm-up fails: `Failed to load Whisper model 'base' via mlx-whisper (preload failed)` |
| Meeting recording + transcript | Same Whisper; system-audio device for the remote side (`system-audio-capture` check) | Works for the microphone. Remote audio needs BlackHole or similar |
| Meeting summary / intelligence | An assignment for "Meetings", or the legacy local model at `~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf` (`holdspeak/config/meeting.py:33-36`) | Not available. Log: `intel.llm_capability enabled=False`. Setup status: `Meeting summary: unavailable (no assignment)`. The drainer runs but has nothing it can execute. Auto-enqueue default is `intelligence_auto = "room_linked"` (`holdspeak/config/meeting.py:44`) |
| Dictation rewrite / intent pipeline | A dictation runtime (`holdspeak[dictation-mlx]` or llama.cpp) | Plain transcription only. Setup status `llm-runtime warn`: `No dictation runtime backend is available` |
| Morning brief (`monday_brief.generate`) | Nothing for the deterministic brief; People keystore for person sections | Answers at once: `headline: "No changes"`, `is_empty: true`, `person_sections_state: "unavailable"` |
| Project updates, reviews, steward | A project; for evidence, watches on GitHub (`gh` login), Jira/Confluence (`acli` login); a model for drafted text | `/api/connections`: github `never_checked`, jira `never_checked` ("Add account"), confluence `never_checked`, calendar `not_configured`, models `not_configured` (0 of 7 assigned). `provider.github_connection` answers `authentication_required` / `gh auth login`. Draft behaviour with no model was not exercised |
| Ask, thoughts, recipes, workbenches | An assignment for "Thoughts & notes" / "Agents & tools" | All 7 rows `no_assignment`; row `global` says `repair: "Choose default"`. Over MCP these are also broken by finding 1 |
| Memory search | Nothing (local index rebuilt at reconcile: log `Memory index rebuild: decisions=0, artifacts=0, notes=0`) | Works, empty |
| Calendar, door | Calendar sources in config (`holdspeak/config/integrations.py:37`) | `/api/door`: `calendar_configured: false`, `people_store_state: "unconfigured"`, all counts 0 |
| Heartbeat notifications | Watches | Sweep runs, `watches=0`, notify `held_no_edge` |
| Sending (channels) | A saved destination, plus `gh`/`acli`/email key | `channel.destinations` → `[]` |

First-run state on the fresh hub: `overall: "needs_attention"`, `first_run: true`, `arrival_required: true`. The primary action is `runs-on-destinations`: "Choose another Runs on destination, or repair the named key, node, endpoint, or manifest." The cause is the missing default GGUF file. `/api/front-door/recommendation` returned `packs: []` with `has_llama_cpp: false`, `has_mlx: false`, `has_cloud_credential: false`: on this fresh HOME the front door had no engine to recommend.

Defaults worth knowing: `control_mode = "yolo"` (`holdspeak/config/core.py:291`), `allow_actuators = True` with `allowed_actuators = ["*"]` and `webhook_allowed_hosts = ["*"]` (`holdspeak/config/meeting.py:119-126`), `intel_provider = "local"` (`:33`).

## 7. Not covered

- No pytest run. "Broken" in 4.3 rests on live calls; everything else on static reads.
- 187 MCP tools that need arguments were not called.
- 18 of 19 CLI subcommands were not run. `holdspeak mesh serve`, `holdspeak node` and `holdspeak-mcp` were not booted.
- Per-event threads (meeting, steward run, thread turn, recording ticker) were not triggered.
- A real meeting, a real summary and a real project update were not run; no engine was configured, by design of the fresh-HOME boot.
- The owner's real config and database were not read, so "off by default" may be "on" on his desk.
- Route-caller matching is lexical (limits in section 2). The 122 "tests only" and 19 orphan routes are leads; each needs one look before removal.
- `holdspeak/db/` (repositories, 255 tables) was not inventoried table by table.
- The Swift app, firmware and UAT trees were counted, not read.

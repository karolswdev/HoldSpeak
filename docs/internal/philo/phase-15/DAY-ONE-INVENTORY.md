# Day One inventory: PHILO Phase 15 "The First Day"

Read-only inventory of `main` at `b88fc3f7b` (2026-10-07). No tests run, no tree change. Paths are relative to the repo root. Sources: the tree, `pm/STATUS.md` (STATUS), `docs/internal/CONDUCTOR.md`, `docs/internal/HANDOVER-MUADDIB-XXXIII.md`.

## How to read the state labels

- **WORKS**: a glass (browser) test on main covers the step, and the merged PR's record in STATUS says it ran green. This inventory did not re-run any test. Glass tests are not in FAST; they run as scoped browser tests on a PR and nightly in FULL.
- **UNVERIFIED**: no glass test, or only unit/vitest coverage, or the covering test is skipped or retired.
- **KNOWN BROKEN**: STATUS, the handover or the code names a defect on main.
- **NEEDS REAL METAL**: the step depends on an LLM, a real agent, a real mic, a real calendar, or real egress (gh, acli, email). The tests use doubles here.
- **Atlas cases** (`docs/internal/philo/graph/atlas*.json`) are walked by hand with `scripts/graph_walk.py`. Only seven `atlas.json` cases run in a test (`tests/e2e/test_graph_walk_smoke.py:49-84`). An atlas name below does not mean green.
- **Red on main right now**: A5b (`philo-14/a5b-needs-paths`, commit `e2c7f6b43`) is not on main. That leaves 3 vitests + 9 glass tests red since #935: the Needs-you Project button opens the drawer (`test_philo14_a2_drawer_glass.py`), and a proposal row opens the Room with its selection (`test_philo14_a2b_paths_glass.py` x2) (STATUS:17, "In flight: A5b").

---

## 1. Install and first launch

### 1.1 Install
- **Face**: a terminal. README.md:173-180: `git clone`, `uv venv && source .venv/bin/activate`, `uv pip install -e .`, `holdspeak`. Prerequisites: Python 3.10+, uv, Node 22.12+ and a C++ compiler (README.md:171). There is no PyPI or brew install.
- **Gesture**: CLI only (1440 and 393 do not apply).
- **What `holdspeak` does**: the entry point is `holdspeak.cli_entry:main` (pyproject.toml:247). Bare `holdspeak` runs `_run_web_mode(no_open=False)` (holdspeak/main.py:599-601). It binds 127.0.0.1:8765, or a free port if 8765 is taken (holdspeak/web_server.py:51-68). It prints a token URL and opens the browser (holdspeak/web_runtime.py:542-563).
- **Tests**: `tests/unit/test_phase200_first_value.py`. The clean-venv install test is marked `slow` (CLAUDE.md, FULL only).
- **State**: **UNVERIFIED** on a clean Mac. The llama-cpp-python source build is the heaviest step; README.md:212 admits "Setup is heavier than a menu-bar app".

### 1.2 `holdspeak doctor`
- **Face**: a terminal.
- **What runs**: `holdspeak/doctor.py:374-406`, 10 checks against a running hub: hub-health, runtime-status, runtime-preflight, websocket, desk-bootstrap, auth, mcp-server, inference, database, observer. The longer list, `holdspeak/commands/doctor.py:1065-1110` (mic, hotkey, ffmpeg, connectors, **Coding agents** at :1134-1174), is used only by `/api/setup/status`. The CLI does not wire it: `main.py:40-41` calls `run_doctor()`, which ignores `--strict` and `--connectors`.
- **Tests**: `tests/unit/test_doctor_command.py`, `test_doctor_config_honesty.py`, `test_doctor_observer.py`, `test_setup_status_doctor_drift.py`. No glass test.
- **State**: **KNOWN BROKEN (doc/code drift).** CONDUCTOR.md:7 says "`holdspeak doctor` checks the same". The CLI does not show the Coding agents check, the mic or the hotkey.

### 1.3 The first-value gate (FirstRun)
- **Face**: `/`. `arrival_required` (holdspeak/web/routes/setup_status.py:309) makes ChairHome render `<main data-testid="chair-first-value"><FirstRun/>` (web/src/desk/chair/ChairHome.tsx:455-462). Root testid: `firstrun` (FirstRun.tsx:415).
- **Cards and testids**:
  - `firstrun-local-ai`: "Set up local AI · <bytes>" (FirstRun.tsx:160-163) → `POST /api/setup/local-ai`.
  - `firstrun-you`: name and aliases → `/api/settings`.
  - `firstrun-first-words`: WAITS FOR SPEECH → SPEECH READY → HEARD; "Dictate one sentence", Stop, "Keep as note" → `POST /api/notes` (FirstRun.tsx:274-361; useFirstTake.ts:218).
  - `firstrun-calendar`: `/api/onboarding/calendar{,/macos/access,/check,/use}`.
  - `firstrun-connections`: "Use it" → `/api/onboarding/connections/use`.
  - `firstrun-agents`: Install hooks → `/api/onboarding/agents/use` (optional).
  - `firstrun-found` / `firstrun-proposal`: found engines.
  - `firstrun-ready`: "Ready, <name>"; Record / Dictate / Ask about this week (Ready.tsx:109-134).
- **Gesture**: one scrolling page at both widths. "Continue later" sits at the foot (FirstRun.tsx:453-457). Handoff: `POST /api/desk/seed`, then `PUT /api/setup/onboarding`.
- **Tests**: `test_firstrun_one_screen_glass.py`, `test_firstrun_heard_glass.py`, `test_hs202_02_first_use_glass.py`, `tests/integration/test_setup_first_value_journey.py`. Atlas: `case.j1.*` (8 cases, anchored on `chair-first-value` only). Smoke-fenced: `case.j1.first_words_continue_later.idle`.
- **State**: **WORKS** (glass; the speech model is a double). **NEEDS REAL METAL**: the physical mic and real model inference (STATUS:50). The Agents card's Install button has no testid, and no glass test presses it.

### 1.4 Engines: what gets assigned by default
- **Set up local AI** downloads three things: Whisper `base` (holdspeak/config/model.py:14-16; MLX on Apple Silicon, holdspeak/transcribe.py:116-163), the embedder `nomic-embed-text-v1.5.Q8_0.gguf` (holdspeak/memory/local_model.py:59-70), and the starter `unsloth/Qwen3.5-4B-GGUF` Q4_K_M, 2.74 GB, 8k context (holdspeak/services/inference_setup_catalog.py:34-58). It then turns meaning search on (local_ai_setup_service.py:504-509).
- **Default assignment**: `InferenceDefaultService` makes a responding engine on THIS machine the `global` default (inference_default_service.py:1-34). It scans loopback only (11434/1234/8080/8000). **A LAN or cloud engine is never auto-assigned**: it becomes a proposal that needs "Use it" (:8-9).
- **Summaries on the default**: the meeting queue inherits global (`meeting-intel-queue@2`, holdspeak/services/inference_service_route_policy.py:200-218). Every other SERVICE policy needs an exact `capability:<id>` assignment (:97-105). Memory extract/consolidate/page inherit a LOCAL wider head (holdspeak/memory/engine.py:164-202).
- **State**: **KNOWN BROKEN, false blocker.** The "No engine for summaries" row checks `has_override` (an exact capability head) (holdspeak/services/needs_you_membership.py:598-601; web/src/desk/chair/meetingPathBlocker.ts:15-20,88). The header comment still cites the rev-1 policy. So after "Set up local AI" the Desk still says "No engine for summaries", although the queue would run on the global default. STATUS:17 records the effect: "the fresh-HOME brief always carries a 'No engine for summaries' item". The 4B starter's meeting analysis is untested on real hardware (STATUS:52).

### 1.5 Engines: his LAN model and keys
- **Face**: Settings > Models = the Concierge (`/models`, web/src/desk/applications.ts:338-352). Testids: `concierge-add-engine` ("Add an engine", ConciergeCore.tsx:583-587), `-add-engine-row` (field "Server address"), `-add-check`, `-add-model`, `-add-submit` ("Use this for summaries", :574), `-apply` ("Use these").
- **LAN `http://192.168.1.43:8080`, key `local`**: Check posts `{base_url}` only (web/src/features/concierge/api.ts:358). The server uses `OPENAI_API_KEY` from the env as the key when no profile exists (holdspeak/web/routes/setup.py:225-238). Define sends `requires_key:false, secret:null` (endpointDraft.ts:84; api.ts:393). **The Concierge has no key field.** The only key input is ModelLibraryCore's "Provider key", which is reachable only through the PARKED FrontDoorView (SettingsCore.tsx:54-55). Otherwise the key comes from the env var `HOLDSPEAK_PROFILE_<slot>_KEY` (holdspeak/intel/providers.py:523-531).
- **Anthropic key**: the provider family is accepted, but there is no execution adapter. Its readiness is always `anthropic_runtime_missing` and the row reads broken (holdspeak/services/model_library_service.py:534-537,566-568,876-878). The usable routes are OpenRouter presets or `openai_compatible` (inference_setup_catalog.py:113-237).
- **OpenAI key**: works as an `openai_compatible` endpoint. `OPENAI_API_KEY` is the Check's fallback key. The old config fields that read it are legacy (config/model.py:65-69).
- **What a model unlocks** (holdspeak/inference_capabilities.py:1060-1125): summaries (`meeting.deferred_analysis`), Cadence drafts (the Conductor's YOLO answers), memory facts, beliefs and pages, Ask AI, Thought interview, Thread chat, live analysis and auto-title, `agent.*`, and calendar snapshot extract.
- **Tests**: `test_hs170_concierge_glass.py`, `test_hs201_09_connect_engine_glass.py`, `test_hs143_assignments_glass.py`, `test_hs143_model_library_glass.py`. Atlas: `case.j3.*`. STATUS:17 says j3 assigned_ready/profile_delete block on `arrival-run-intel`, and j3.speech_missing is setup debt.
- **State**: **KNOWN BROKEN for his server if it enforces the key.** There is no way to type `local` on a reachable face. Whether 192.168.1.43 refuses keyless calls: **NEEDS REAL METAL**. "Never run against a real Ollama/LM Studio/llama.cpp server" (STATUS:53).

### 1.6 Meaning search row
- **Face**: the Concierge, THE SET. `concierge-meaning-search`, `meaning-search-verb`, `meaning-search-state` (OFF / DOWNLOADING / INDEXING / ON), `meaning-search-error` (web/src/features/concierge/MeaningSearchRow.tsx:155-198). API: `/api/memory/meaning-search{,/turn-on,/turn-off}`. The embedder is local, so the LAN server (no embeddings) is not needed.
- **Tests**: `test_meaning_search_row_glass.py`. The real-model case skips unless `HOLDSPEAK_MEMORY_EMBED_MODEL` is set (:207). Also `tests/integration/test_meaning_search_real_hub.py`.
- **State**: **WORKS** (glass, OFF/DOWNLOADING/refusal). The real indexing case is **NEEDS REAL METAL**. New items take up to 120 s to become searchable (STATUS:62).

---

## 2. The Morning

### 2.1 Arrival on the Chair screen
- **Face**: `/` → `ChairDesk` `chair-desk` with `data-layout="screen"` (ChairDesk.tsx:197-203), and the screen `desk-screen` (web/src/desk/screen/Screen.tsx:108).
  - Icons (no testid; `data-object-id`/`data-kind`, DeskIcon.tsx:130-131): `project:<id>` drawers, `drawer:people`, `drawer:conductor`, `drawer:needs`, `drawer:parked`, loose objects (screen/compose.ts:133-214).
- **1440**: free layout; TALK `desk-screen-talk` at the foot-left (Screen.tsx:171-176). The four Chair windows (`chair:needs|brief|week|capture`) **start closed on a fresh desk** (chairWindows.ts:71-79). Open: Window ▸ Chair ▸ name, or the icon.
- **393**: grid; no TALK, no drag (Screen.tsx:120,171). Go menu, first rows: Needs you / Brief / The week (DeskMenuBar.tsx:43-65). One window fills the screen. Capture opens only from the Dock's Speak (ChairDesk.tsx:121-127).
- **Tests**: `test_philo14_a1_fresh_arrival_glass.py:76`, `test_philo13_11_chair_glass.py`, `test_philo13_17_phone_desk_glass.py`, `test_philo13_13_dock_glass.py`.
- **State**: **WORKS** (#939, #951, #959). Open: the 393 fresh-arrival path uses Enter, not Go; the long desk scrolls uncapped; ~40 membership GETs on a 20-Project desk (STATUS:17, #939).

### 2.2 Needs you
- **Face**: the Needs drawer `needs-drawer` (web/src/desk/needs/NeedsDrawer.tsx:300-312); `arrival-headline`, `needs-list`, `needs-row`, `needs-next`, `needs-receipt`. All verbs are `needs-row-verb[data-verb=…]` (:91-240). Dock badge = count (Dock.tsx:325-327,502-505).
- **Rows** (needs/needsFace.ts): agent asks TO APPROVE/ASKS (:182-195), HELD CALL (:201-221), PRs, decisions to review (:271-274), proposals TO DECIDE/TO CONFIRM (:276-291), commitments (:299-300), engine blockers (:335-340), failed summaries (:350-355), ARMED/NEXT (:448-485), connect calendar. Hub: `GET /api/desk/needs-you` (holdspeak/web/routes/projects.py:619-637; Room part cached 900 s, :612).
- **Gesture**: 1440 opens the drawer icon or the window; 393 uses Go ▸ Needs you.
- **Tests**: `test_philo13_03_needs_you_glass.py`, `test_needs_you_means_you_glass.py`, `test_conductor_r1_gate_row_glass.py`, `test_hs172_arrival_glass.py`. Atlas: `case.j2.*`, `case.beyond.projections_counts.*`.
- **State**: **KNOWN BROKEN (partial)**:
  - The A5b paths are red on main (above).
  - The engine blocker is false (1.4).
  - At 393 the seventh row sits under the Dock; scroll reach is unverified (STATUS:17, #959).
  - J2 `engines_both_missing` depends on the host (STATUS:17, #939).
  - j2.read_pending/read_unknown need an unimplemented `route_failure` rig.

### 2.3 The Brief (Monday brief)
- **Face**: the `chair:brief` window. Testids: `arrival-brief`, `-generate`, `-row`, `-handled`, `-receipt` (ChairHome.tsx:686-710,1206-1330). Pull-out: `pullouts/views/BriefView.tsx` (standing pages :166,322; "Add to 1:1 agenda" :263-285).
- **Routes**: `GET /api/brief/latest`, `POST /api/brief/generate`, shelf (holdspeak/web/routes/monday_brief.py:112-153). One brief per local day; deterministic, no model (services/monday_brief_service.py:347-417). It copies Needs-you blockers in as WAITING (:637-639).
- **Auto-generate**: only the cadence loop does it, and that loop is OFF by default (`CadenceConfig.enabled = False`, holdspeak/config/integrations.py:223). **On day one the owner presses Generate.**
- **Tests**: `test_philo11_05a_brief_decision_send_glass.py`, `test_hs175_rhythm_brief_glass.py`. Atlas: `case.j10.*` (17). Smoke-fenced: generated_empty, same_day_idempotent, same_day_same_id.
- **State**: **KNOWN BROKEN (empty state).** A fresh-HOME brief always carries "No engine for summaries", so five empty / ALL HANDLED cases fail (j10 reload_persisted, j10 route retained_after_reload, p11 brief_last_ack/defer, philo404 all_handled; STATUS:17, #951). Generate itself: **WORKS**.

### 2.4 The week
- **Face**: the `chair:week` window. Testids: `arrival-week-strip`, `arrival-week-dot`, `arrival-this-week`, `arrival-meetings`, `arrival-thoughts` (ChairHome.tsx:1342-1385,2722-2738). Data: `GET /api/door` → `week` (`DoorService._week_strip`, services/door_service.py:542-586; `has_calendar:false` with no calendar).
- **Tests**: `test_hs175_arrival_glass.py`; atlas `p13.dock.needs_you_week`.
- **State**: **WORKS** with a seeded calendar. A real calendar is **NEEDS REAL METAL** (real EventKit prompt/read unverified, STATUS:51,53).

---

## 3. A meeting

### 3.1 Schedule and one-tap record
- **Face**: Dock Record orb (`RecordOrb.tsx:58-74`, aria "Record a meeting"/"Stop recording", no testid). The Capture bar `arrival-capture-bar` holds `arrival-record-meeting` and `arrival-schedule` (ChairHome.tsx:2929-2966). Routes: `POST /api/meeting/start|stop` (holdspeak/web/routes/meetings/live.py:92,114).
- **Schedule**: `POST /api/scheduled-recordings` (holdspeak/web/routes/scheduled_recordings.py:56-146). Needs you shows ARMED/NEXT with Cancel/Retry. Calendar auto-record is OFF by default and arms 5 min ahead (holdspeak/config/meeting.py:51-53).
- **Gesture**: 1440 uses the Dock orb or Capture (opens from Speak). 393 uses the Dock orb.
- **Tests**: `test_hs144_door_glass.py::test_upcoming_rail_schedule_create_round_trip_and_form_cancel`, `test_philo13_16_capture_glass.py`. `test_hs147_one_tap_glass.py` is RETIRED (skips at :159; its testids exist only in the parked `DoorBoardLane.tsx`). Atlas: `case.j4.record_start.*`, `record_only.*`.
- **State**: **UNVERIFIED for live recording**: j4 record_start/record_only need a `browser_audio_device` rig, and j4.meeting_stop has `meeting_active` false (STATUS:17). Mic, BlackHole and permissions are **NEEDS REAL METAL**. Schedule/Cancel: **WORKS** (glass).

### 3.2 Import a WAV
- **Face**: Meetings window (`/history`) → Import (pages/cores/history/ImportSection.tsx:44; no testid), or drop a file on the desk (GlassDropLayer.tsx:82). Route: `POST /api/meetings/import` → 202 (holdspeak/web/routes/meeting_import.py:54,150). Job: services/meeting_service.py:182-338 ("Transcribing — window N of M"; `import_failed`). **Import does not auto-run the summary** (holdspeak/meeting_import.py:398-433).
- **Tests**: `test_hs202_first_use_smoke.py` (import :474), `test_phase200_daily_loop.py`. Atlas: `case.j4.meetings_import.imported` (smoke-fenced).
- **State**: **KNOWN BROKEN**: "J4 meetings import times out (import_failed, transcription stays active)" (STATUS:27; handover :44). WAV imports on an isolated HOME stop at the 300 s limit unless `HF_HOME` points at the real Whisper cache (STATUS:17).

### 3.3 Transcription and summary
- **Face**: `arrival-run-intel` (ChairHome.tsx:2511) or `detail-run-intelligence-btn` (NeedsYouTable.tsx:112) → `POST /api/meetings/{id}/intelligence/run` (web/routes/meetings/intel.py:90). Result: `meeting-summary-text`. Plugins: the "balanced" profile (`requirements_extractor`, `action_owner_enforcer`, `decision_capture`) plus `project_detector` (holdspeak/plugins/router.py:19-40,145). A plugin with no assignment is skipped `no_assignment` (holdspeak/db/intel.py:370-377).
- **Tests**: `test_hs201_summary_face_glass.py`, `test_hs201_summary_trust_glass.py`, `test_hs201_summary_producer_chain.py`, `test_hs202_first_use_smoke.py`. Atlas: `case.j6.*`.
- **State**: **KNOWN BROKEN**: the meeting window shows its summary twice. The first-use smoke fails in strict mode (STATUS:27). `meeting-summary-text` renders in MeetingSummarySlab.tsx:57 and in ChairHome.tsx:2319; the test reads it at test_hs202_first_use_smoke.py:536,547. The KNOWN set also lists thought-door, save-confirmation, import-refresh, record-refresh and notes-query (:40-45). Atlas: `arrival-run-intel` never appears in j3/j9 setups; the first real-LAN closure s2 walk drew no summary in 300 s, cause unknown (STATUS:17). The 4B and LAN summaries are **NEEDS REAL METAL**.

### 3.4 The aftercare card (MEETING READY)
- **Face**: `AftercareNote` (web/src/components/AmbientLayer.tsx:164-263), no testid: `aside[aria-label="Meeting aftercare"]`. Verbs: Open proposals, Dismiss. Slot: `arrival-aftercare-slot`. Capture opens and grows for the card (ChairDesk.tsx:158-178; #954).
- **Tests**: `test_philo14_a1c_aftercare_capture_glass.py`. Atlas: 7 aftercare cases re-anchored and walked (#954); `case.philo603.toast.*`.
- **State**: **WORKS** (#954). Open: `philo603.toast.floor_list` (393) and `floor_spatial_fallback` block on setup. At 393 the card takes the front after a trigger (j6.summary_text, closure s2). The slot lookup in AmbientLayer.tsx is unfenced (STATUS:17, #954).

### 3.5 Decisions and action items
- **Face**: proposals from `decision_capture` and `action_owner_enforcer` (services/proposal_bridge_service.py:344-412). Confirm: `needs-row-verb[data-verb=confirm]`, `arrival-proposal-confirm` (ChairHome.tsx:2012-2037), `proposal-confirm-btn` (Meetings record), `proposal-confirm` (Room, ProjectRoomCore.tsx:791) → `POST /api/proposals/{id}/confirm` (web/routes/proposals.py:99).
- **Tests**: `test_hs172_meeting_glass.py:256`, `test_hs200_meeting_outcomes_glass.py`, `test_phase200_daily_loop.py` (confirm on a HISTORICAL FIXTURE), `test_philo13_08_decide_glass.py`.
- **State**: **WORKS** for Confirm on fixtures. The proposal row → Room-with-selection path is red on main until A5b (`test_philo14_a2b_paths_glass.py`). Extraction quality on the 4B or LAN model: **NEEDS REAL METAL**.

---

## 4. People and Projects

### 4.1 Add a person
- **Face**: the People window (`desk.open-people`, verbRegistry.ts:390-402; pages/cores/PeopleCore.tsx). "New relationship" focuses `#people-new-relationship` (:302); Enter or Add (:352-354) → `POST /api/people/relationships` (holdspeak/web/routes/people.py:104). The input and Add have no testid. 1:1 prep: `people-prep-lens` (:502).
- **Gesture**: 1440 uses the `drawer:people` icon. On the screen it opens `/`, not People (screen/open.ts:24-74). 393 uses the palette or menu verb.
- **Tests**: `test_hs172_people_glass.py`, `test_hs200_people_preparation_glass.py`, `test_philo13_09_prep_glass.py`. Atlas: `p13.people.prep*`.
- **State**: **WORKS** (glass). Person memory pages do not exist (STATUS:55).

### 4.2 Make a Project (the Door → drawer → Room)
- **Face**: `desk.new-project` → Door (`surface-project-setup`, DoorCore.tsx). Testids: `door-outcome-input`, `door-row-*`, `door-connect-*` (opens Settings integrations), `door-create` → `POST /api/projects/door` (web/routes/project_door.py:47), then the Room. The Project's face is a DRAWER (web/src/desk/drawer/DrawerWindow.tsx; `drawer-facts`, `drawer-hand`, `drawer-park-receipt`); the Room is one press away.
- **Tests**: `test_hs169_door_glass.py`, `test_hs169_door_legs_glass.py`, `test_philo14_a2_drawer_glass.py`, `test_philo14_a2b_paths_glass.py`, `test_hs169_room_glass.py`.
- **State**: **WORKS** for create/drawer. Needs-you → drawer is red until A5b. The drawer LIST view has no drag (DrawerWindow.tsx:229-238).

### 4.3 Connectors
- **Face**: Settings > Connections (pages/cores/connections/ConnectionsPane.tsx).
  - GitHub (`gh`): `connections-github` :178.
  - Jira (`acli`, site + email per connection): `connections-jira` :314 → `POST /api/providers/jira/connections`.
  - Confluence: :375-423.
  - Calendar: `connections-calendar` :465 (EventKit, or ICS https/webcal, services/onboarding_service.py:214-245).
  - First run: `firstrun-calendar`, `firstrun-connections`.
- **Tests**: `test_hs168_connections_glass.py`, `test_philo9_b1_connections_glass.py`, `test_hs166_jira_glass.py`, `test_hs161_github_glass.py`, `test_hs146_calendar_snapshot_glass.py`, `test_hs174_door_confluence_glass.py`. Tests refuse the real gh/acli (`HOLDSPEAK_TEST_NO_REAL_CLI=1`, CONDUCTOR.md:100).
- **State**: **NEEDS REAL METAL**: gh/acli auth and EventKit are unverified on his desk (STATUS:51). **KNOWN BROKEN (gaps)**: a sign-in saves no Send destination; there is no System Settings verb when Calendar access is denied; a GitHub Enterprise egress host reads github.com (STATUS:51,53).

---

## 5. The Conductor

### 5.1 Install hooks
- **Face**: the first-run Agents card (firstrun/AgentsCard.tsx:196-205), or the Conductor drawer window (`/conductor`, Dock ⌘3; conductor/ConductorWindow.tsx:133-146: "Copy install", "Install hooks"; no testid on either) → `POST /api/onboarding/agents/use` (web/routes/onboarding.py:119; op `agent_hooks.install`). CLI: `holdspeak agent-hook install`.
- **Tests**: `tests/unit/test_onboarding_agents.py`, `test_conductor_r3_codex.py`; `test_philo14_c4_conductor_glass.py` (the drawer, not the press). No glass test presses Install.
- **State**: **UNVERIFIED** on glass; **NEEDS REAL METAL** (Codex trust hash via `codex app-server`; "K1/K3 live hook delivery and credential validity not observed on a real desk", STATUS:29).

### 5.2 Hand to agent
- **Routes**: `POST /api/agent/hand` (web/routes/agent_hand.py:81), preview :116.
- **Gestures**:
  - Needs-you rows carry no Hand verb, by ruling (needs/NeedsDrawer.tsx:13-15).
  - Chair arrival rows: `hand-row-verb` (ChairHome.tsx:1699-1703).
  - Drawer: `drawer-hand`, or drag an icon onto the Conductor drawer or an agent icon (1440 only).
  - YOLO: ConfirmLine `hand-confirm`. Secure/Normal: HandSheet `hand-sheet` / `hand-launch` (hand/begin.ts:26-36).
  - 393: no drag; the verb opens the confirm line.
- **Tests**: `test_philo14_c3_drop_to_hand_glass.py` (6), `tests/unit/test_agent_hand*.py`.
- **State**: **WORKS** (glass with doubles). Open (STATUS:17, #946):
  - Door/Room row verbs and ⌘K open the sheet even in YOLO (HandRowVerb.tsx:16; verbRegistry.ts:522).
  - The new agent icon can sit behind the open drawer.
  - There is no issue object on the screen.
  - `/agent` needs an explicit project_id when no sources are stored (STATUS:29).
  - A real launch is **NEEDS REAL METAL**.

### 5.3 The lane: answer, approve/deny
- **Face**: the lane window (web/src/desk/lane/LaneWindow.tsx). Track `lane-track` (BRIEF·WORK·COMMIT·PR·HELD·ASKS·MERGE), answer `lane-ask` → `/api/coders/{key}/steer` with `wait_id` (409 `wait_not_current`). Held call: `lane-approve` / `lane-deny` → `POST /api/gate/proposals/{id}/decide`. Also `lane-stop` (two presses), `lane-raw`. From Needs you: `needs-row-verb[data-verb=answer|approve|deny]`.
- **Tests**: `test_philo14_c2_lane_glass.py`, `test_philo14_c2_lane_actions_glass.py` (8), `test_conductor_r1_gate_row_glass.py`, `tests/unit/test_philo14_c0_launch_lane.py`.
- **State**: **WORKS** (glass with doubles). Open:
  - BRIEF shows a word count; Files changed shows names only.
  - The draft chip reads NOT SET without a drafting model (LaneWindow.tsx:647-675), so the YOLO responder answers nothing routine and every question goes to Needs you.
  - A Normal answer needs ARM first (laneStore.ts:210-213).
  - The real Claude/Codex loop ran once in R1 (#916), on an isolated HOME but with non-isolated credentials (handover :31).

### 5.4 The PR, the merge receipt, the weekly update row
- **Face**: PR card `lane-pr`, `lane-open-pr` (GITHUB.COM egress). Merge receipt `room-merge-receipt` in the Room footer (ProjectRoomCore.tsx:2368-2372; agentFlights.ts:232-249). The Heartbeat follows PRs and closes the origin with PR evidence (K4). The update row reads `Merged: <title> (PR #n)` (services/project_update_service.py:503-524); `report_merged_prs` is ON (heartbeat_service.py:176,560-572).
- **Tests**: vitest `agentFlights.f2.test.tsx:81-84`; unit `test_conductor_k4_follow_through.py`, `test_conductor_r4_hand_close.py`. **No glass test reads `room-merge-receipt` or `Merged:`.**
- **State**: **UNVERIFIED / NEEDS REAL METAL**:
  - No atlas case for launch → PR → merge: the rig lacks an agent double, a clone step and a gh double (STATUS:27; CONDUCTOR.md:108).
  - The atlas has no Conductor case at all (STATUS:17, #947).
  - Merges were proven with a fake gh (STATUS:29).
  - Not on any face: the Room's PR link on merge, and a `report_merged_prs` control (handover :42).

---

## 6. The weekly update and Send

- **Face**: Room → `updates-verb` → UpdatePosture: `update-verb-draft-deterministic`, `update-verb-draft-model`, `update-editor`, `update-verb-publish` (features/project-room/update/UpdatePosture.tsx). Routes: `/api/projects/{id}/updates/draft`, `/api/updates/{id}/publish|delivered` (web/routes/project_updates.py:95-223). Send well: `send-well`, `destination-row`, `send-check`, `send-preview-body`, `send-sent` (web/src/desk/surface/send/SendWell.tsx). Routes: `/api/channels/preview|sends` (web/routes/channels.py:117-141).
- **Destinations** (pages/cores/connections/Destinations.tsx:52-57): Folder (built-in `holdspeak-folder` → `Documents/HoldSpeak/Sent`, services/channel_contract.py:393), GitHub comment, Jira comment, Confluence blog post, Email (Resend or SendGrid; **the default provider is SendGrid**, services/channel_service.py:257,399), Slack webhook.
- **Gesture**: 1440 uses the Room's Updates, or "Send to ▸" on a window (windowSend.tsx). 393: the same verbs in the stacked Room. The palette `p13.palette.draft_update` exists.
- **Tests**: `test_hs162_update_glass.py`, `test_hs173_update_glass.py`, `test_builtin_send_folder_glass.py`, `test_philo10_04_send_face_glass.py`, `test_philo13_15_send_to_glass.py`, `test_philo11_05a_brief_decision_send_glass.py`. Atlas: `p10.*`, `p11.*`, `p9.update.*`.
- **State**: Folder send **WORKS** (glass). gh, Jira, Confluence, email and Slack sends are **NEEDS REAL METAL**. **KNOWN**: `p11.meeting_summary.chair.sent` sends 200 but no sent row matches (unchecked, STATUS:17). Six older Send rigs park the built-in folder (STATUS:51). The model-drafted update is **NEEDS REAL METAL**.

---

## 7. End of day

### 7.1 Parked
- **Face**: the `drawer:parked` icon on the screen **opens the Meetings window (`/history`)**, not a parked drawer (screen/open.ts:44-47; compose.ts:193-198). Parked items show where they live: `meetings-parked` (HistoryCore.tsx:693), `wb-parked`, `drawer-park-receipt`. Routes: `DELETE /api/meetings/{id}` + restore (meetings/crud.py:170-184), Workbench park/restore, `/api/projects/{id}/restore`.
- **Tests**: `test_philo13_02_park_glass.py`. Atlas: `p13.meeting.park_restore`, `p13.workbench.park_restore`.
- **State**: park/restore per kind **WORKS**. The Parked icon as one place for everything: **UNVERIFIED**. It shows only meetings.

### 7.2 Memory
- **What is remembered**: MemoryWorker starts with the hub and sweeps every 120 s (memory_conductor.py:39). The keyword index runs with no model. Vectors, facts, beliefs and pages each need their own assigned engine (inference_capabilities.py:1105-1125; memory_conductor.py:74-89). Sources: MEMORY-DESIGN.md:296-312.
- **Where it shows next morning**:
  - Desk memory `/project-memory` (RecallFace, ProjectRoomCore.tsx:2297; `recall-card`).
  - Standing pages in the Room and BriefView (`standing-pages`).
  - ⌘K → `/api/memory/search`.
  - **Nothing memory-related is on the Chair screen.**
- **Overnight**: the Heartbeat holds sweeps in quiet hours 22–08 (heartbeat_service.py:38-41,412,423). The Brief is not regenerated (the cadence loop is off).
- **Tests**: `test_memory_faces_glass.py`, `test_hs526_desk_memory_glass.py`, `test_palette_memory_glass.py`, `test_phase200_daily_loop.py` (day-2 recall across a hub restart).
- **State**: keyword recall **WORKS** (glass). Facts, beliefs and pages are **NEEDS REAL METAL**: never run with the real LAN model (STATUS:55-57). The Desk memory face does not show the four new kinds (STATUS:58).

---

## Gaps a first day would hit (ranked by owner cost)

1. **His LAN model cannot take its key on any reachable face.** The Concierge sends `requires_key:false, secret:null`, and Check uses only `OPENAI_API_KEY`. Start: `web/src/features/concierge/endpointDraft.ts:84`, `web/src/features/concierge/api.ts:358,393`, `holdspeak/web/routes/setup.py:225-238`. The parked key field is in `ModelLibraryCore.tsx:387-397`. Whether .43 refuses keyless calls: unknown.
2. **False "No engine for summaries" after Set up local AI.** The blocker demands an exact capability head; the queue inherits global since `meeting-intel-queue@2`. It shows in Needs you, the Brief and the meeting path, and fails five empty-brief atlas cases. Start: `holdspeak/services/needs_you_membership.py:598-601`, `web/src/desk/chair/meetingPathBlocker.ts:88`, `holdspeak/services/monday_brief_service.py:637-639`.
3. **WAV import times out** (`import_failed`, transcription stays active) (STATUS:27). Start: `holdspeak/services/meeting_service.py:275-338`, `holdspeak/web/routes/meeting_import.py:23-30`.
4. **The meeting summary renders twice**; the first-use smoke is red (STATUS:27). Start: `web/src/desk/chair/ChairHome.tsx:2306,2319`, `web/src/meetings/MeetingSummarySlab.tsx:57`.
5. **Anthropic keys do nothing**: no execution adapter (`anthropic_runtime_missing`). Start: `holdspeak/services/model_library_service.py:534-537,876-878`.
6. **Needs-you paths red on main** (Project button → drawer, proposal → Room with selection) until A5b merges. Start: branch `philo-14/a5b-needs-paths` `e2c7f6b43`; `web/src/desk/needs/NeedsDrawer.tsx:91-240`.
7. **`holdspeak doctor` does not run the full check list**: no Coding agents, mic, hotkey or connectors, although CONDUCTOR.md:7 says it does. Start: `holdspeak/main.py:40-41`, `holdspeak/doctor.py:374-406`, `holdspeak/commands/doctor.py:1065-1110`.
8. **No YOLO auto-answers without a Cadence-drafts model**: the draft chip reads NOT SET, and the global default does not feed capability-only services. Start: `web/src/desk/lane/LaneWindow.tsx:647-675`, `holdspeak/services/inference_service_route_policy.py:97-105`, `holdspeak/services/agent_responder.py`.
9. **The launch → PR → merge loop is unproven on glass and atlas**: no merge-receipt or `Merged:` glass test, no Conductor atlas case, R1 was the only real walk. Start: `web/src/features/project-room/ProjectRoomCore.tsx:2368-2372`, `holdspeak/services/project_update_service.py:503-524`, `scripts/graph_walk.py`.
10. **The Brief does not generate itself** (cadence loop off), and the Heartbeat holds 22–08, so the first morning starts with Generate. Start: `holdspeak/config/integrations.py:223`, `holdspeak/runtime/cadence.py:102-130`.
11. **Live recording has no browser-audio rig**; j4 record_start/record_only and meeting_stop are blocked (STATUS:17). Start: `holdspeak/web/routes/meetings/live.py:92-118`, `web/src/desk/store/recordingSlice.ts:61-128`.
12. **Calendar denied leaves no way forward**, and a connector sign-in saves no Send destination (STATUS:51). Start: `holdspeak/web/routes/onboarding.py:79-107`, `web/src/desk/firstrun/CalendarCard.tsx:41`.
13. **Email defaults to SendGrid**; Resend must be picked by hand. Start: `holdspeak/services/channel_service.py:257,399`, `web/src/pages/cores/connections/Destinations.tsx:52-57`.
14. **The Parked icon opens Meetings only.** Start: `web/src/desk/screen/open.ts:44-47`.
15. **393: the seventh Needs-you row sits under the Dock** (scroll reach unverified). Start: `tests/e2e/test_philo14_a1_fresh_arrival_glass.py:76`, `web/src/desk/needs/NeedsDrawer.tsx:312`.
16. **Memory is invisible on the Chair**; facts, beliefs and pages are unrun on the LAN model; the memory face hides the four new kinds (STATUS:55-58). Start: `holdspeak/memory_conductor.py:74-89,358-381`, `web/src/features/project-room/ProjectRoomCore.tsx:2297`.
17. **Install hooks has no glass coverage and no testid** on either button. Start: `web/src/desk/firstrun/AgentsCard.tsx:196-205`, `web/src/desk/conductor/ConductorWindow.tsx:133-146`.
18. **People drawer icon opens `/`, not People.** Start: `web/src/desk/screen/open.ts:24-74`.

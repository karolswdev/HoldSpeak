# Betterment: the feature inventory

Status: draft for the owner and the orchestrator, 2026-10-17. Read from code
and docs only: no hub, no browser, no tests. It is the map for the
betterment plan. Each feature named here gets a job-first design
(`README.md` in this folder) and then a recipe.

The reader: a Senior Software Architect who leads three people. He calls
HoldSpeak "the most advanced Agentic OS in the world". He also says the
features confuse him and that he keeps hitting walls. This inventory lists
what he meets, what each part is for, and where it breaks.

## How to read the citations

Short names in the tables point to these sources (all under `docs/internal/`
unless the path says otherwise):

| Short name | Source |
|---|---|
| Recon | `philo/phase-17/RECON-2026-10-13.md` ("gimmick not an OS"), with its root cause (R1 to R7) |
| WB-Recon | `betterment/workbench/RECON.md` and `DESIGN.md` |
| Eng | `betterment/engines/DESIGN.md` and `MODEL.md` |
| MCP | `betterment/mcp/DESIGN.md` and `MODEL.md` |
| PD | `HANDOVER-PRODUCTIVE-DESK-2026-10-13.md` (#1197) |
| DJ | `HANDOVER-DAILY-JOURNEYS-2026-10-13.md` (#1198) |
| MD | `HANDOVER-MODEL-DISCOVERY-DOWNLOAD-2026-10-13.md` (#1199) |
| SA / SR | `SURFACE-AUDIT-2026-10-14/README.md` / `SURFACE-REPAIR-2026-10-14.md` (#1200) |
| SEND | `SEND-REFINEMENT-2026-10-14.md` (#1201) |
| DU | `DEEP-USABILITY-2026-10-14/README.md` (#1202) |
| ST / SAU / SP | `SETTINGS-TRIALS-` / `SETTINGS-AUDIT-` / `SETTINGS-PRIMITIVES-2026-10-14/` (#1203 to #1205) |
| AW | `ACCOUNT-WORKBENCH-2026-10-15/` (#1209) |
| FT | `FOLLOW-THROUGH-2026-10-15/` (#1210) |
| DD | `DECISION-DELIGHT-2026-10-15/NEXT-SURFACES.md` (#1211) |
| AD | `ATTENTION-DISMISS-2026-10-15/` (#1214) |
| CW / CE | `COHESIVE-WORKFLOWS-2026-10-15/` / `COHESIVE-DESK-ENTRY-2026-10-16/` |
| FX | `FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/` (#1220 to #1236) |
| BR | `BRIEF-REFERENCE-OPEN-2026-10-16/PLAN-AUDIT-FLAGSHIPS.md` |
| MS | `MEETING-STOP-NATIVE-2026-10-16/RECOVERY.md` (#1233) |
| T3 | `TONIGHT-THREE-2026-10-17/` (#1240, #1241) |
| DLT | `DAILY-DELIGHT-2026-10-17/RELEASE.md` (#1247) |
| STATUS | `pm/STATUS.md` |

"Face LOC" is the rough line count of the web face (non-test `.ts`, `.tsx`
and `.css`, parked folders left out). "Last touched" is the latest git commit
on those face files. "Status" in a problem cell is what the records say:
fixed, open or unknown. All MCP counts come from the family files
(`holdspeak/mcp/families/`) and `holdspeak/mcp/tools.py`: there are 257 tools
in total.

## 1. The features

### Capture

| # | Feature | Where it lives | Its job for the architect | Main files | MCP | Services | Face LOC | Last touched | Known problems | Overlaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Speak** (voice typing; wings Speak, Journal, Blocks, Learned) | Dock, Go, ⌃1 (`web/src/desk/applications.ts:84-104`) | Hold a key, talk, and the text lands in the app he is in, and gets better each time he corrects it. | `web/src/pages/cores/DictationCore.tsx`, `pages/cores/dictation/`, `holdspeak/dictation_runner.py` | dictation (2) | dictation_service; routes `web/routes/dictation/` (pipeline 1583 lines) | ~5,000 | 10-14 | Chip words on the face: `HOLD NONE ANYWHERE`, `LANDS IN · DRY RUN`, `LISTENER FAILED` (Recon R3). Asks for speech setup when speech is set (Recon R6). A popup of 19 identical journal warnings that "cannot go away", now fixed (AD README:3-6). Physical audio and dictation quality not seen in any record (FX COVERAGE.md:65-73). | Capture ▸ Talk; Settings ▸ Voice; Voice commands |
| 2 | **The hotkey and the menu-bar glyph** (desktop presence, HUD) | macOS menu bar; Right Option | Dictate without opening the desk; see that HoldSpeak listens. | `holdspeak/hotkey.py`, `holdspeak/desktop_presence_cocoa.py`, `holdspeak/desktop_permissions.py` | none | started by `web_runtime.py:540-554` | Python ~900 | 10-09 | The presence label keeps the last activity after a disconnect, open (CE README:79-81). The hotkey listener is from 03-25 and has no record of a recent walk. | Speak |
| 3 | **Voice commands** | Search only (`applications.ts:404-420`, no Go row) | Say a phrase, run a saved action. | `pages/cores/CommandsCore.tsx` | none named | `/api/commands` (system routes) | ~360 | 10-16 | Closed a failed draft, fixed (SA README:45, SR). Recon puts it on the cut list from Go ▸ Tools. | Speak ▸ Blocks |
| 4 | **Meetings** (the archive, a meeting's Outcomes, import) | Dock, Go, ⌃2 (`applications.ts:115-137`); CLI `holdspeak import`, `history`, `intel` | Turn a meeting into a summary, decisions and who owes what, and confirm them. | `pages/cores/HistoryCore.tsx`, `pages/cores/history/`, `web/src/meetings/`, `desk/pullouts/MeetingWindow.tsx` | meeting (10), proposal (2) | meeting_service, meeting_intel_service, proposal_bridge_service, meeting_aftercare_service | ~6,000 | 10-17 | The keep list: correct summary in 14 s (Recon §4). Two review loops and the meeting opened over the list: fixed into one Outcomes and list ▸ detail (PD). Outcomes were lost when the bridge failed, fixed (T3 PLAN.md:45-78). Chips like `PROPOSAL · LINKED · UNREVIEWED` (Recon R3). The 14 meeting plugins are promised in the README; their outputs are not named on the face (unknown). | Decisions; Follow-through; Needs you; People prep |
| 5 | **Record a meeting** (live capture) | Meetings ▸ Record wing; Desk ▸ New Meeting; Capture | Record mic and system audio, and stop cleanly. | `pages/cores/LiveCore.tsx`, `desk/components/RecordOrb.tsx`, `holdspeak/meeting*` | meeting_start_capture / stop | meeting_service | ~1,000 | 10-11 (stop fix 10-16, backend) | Stop hung the whole hub on a CoreAudio lock; now Stop runs off the event loop. Why CoreAudio held the lock is unknown (MS:3-7). | Capture; Scheduled recording |
| 6 | **Scheduled recording, the clock and the calendar snapshot** | Capture ▸ Schedule; Settings ▸ Meetings (auto-record); Search ▸ Calendar snapshot | Record the meetings on his calendar without remembering to. | `desk/components/ScheduleCreateWindow.tsx`, `pages/cores/CalendarSnapshotReviewCore.tsx`, `desk/store/scheduledRecordingSlice.ts` | scheduled_recording (5) | scheduled_recording_service, calendar_snapshot_service (844 lines) | ~900 | 10-16 | Schedule creation erased newer edits, fixed (DU). EventKit, sign-in and the firing of a schedule are not verified (SAU README:108-114, 194). The populated snapshot face is not assessed (CW README:121). Calendar snapshot is on the Recon cut list. | The week; Today |
| 7 | **Capture** (Talk, Write a thought, Record meeting, Schedule) | Dock "Capture" (`desk/components/window/Dock.tsx:504`); Window ▸ Desk | One small window for "get this down now". | `desk/chair/ChairHome.tsx` (3,168 lines, shared with Brief and The week), `desk/chair/chairWindows.ts:36-41` | none | none of its own | part of ~4,800 | 10-16 | Recon keeps it: "the right phone grammar" (Recon §4). | Speak; New menu; Record |

### People and commitments

| # | Feature | Where it lives | Its job | Main files | MCP | Services | Face LOC | Last touched | Known problems | Overlaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 8 | **People** (roster, the 1:1 card, Prep with You owe / They owe you) | Dock, Go, the People drawer (`applications.ts:421-439`) | Before a 1:1 with one of his three reports, see what is open between them. | `pages/cores/PeopleCore.tsx`, `desk/people/prepData.ts`, `desk/pullouts/PeoplePullout.tsx`, `desk/screen/nextOneOnOne.ts` | people (18) | people_service (1,711, encrypted), person_overlay, room_people_service | ~2,400 | 10-16 | A confirmed meeting commitment did not reach the person's prep (Recon R2); fixed, and "They owe you" now opens (PD; FX DELIVERY-CDE). `/api/people/relationships` returns 503, cause unknown, open (STATUS:807-812). The real desk had 0 people five days after the fresh start (Recon). | Follow-through; Monday brief; People in the Room |
| 9 | **Follow-through** (who owes what, Done, Snooze, Undo) | Today ▸ Follow-through wing (`desk/pullouts/IntelligencePullout.tsx:18-21`) | Keep the promises from meetings from slipping. | `desk/pullouts/views/FollowThroughView.tsx` | follow_through (3) | follow_through_service (901) | ~370 | 10-16 | The owner: "confusing and ugly" (FT DESIGN.md:3-4). People text was kept in plain browser storage, P1, fixed (FT AUDIT). Snooze left a task on the board, fixed. Mine / They owe split is not built, open (FT README:137-138). | People prep; Needs you; Meeting Outcomes; Today |

### Projects, updates and decisions

| # | Feature | Where it lives | Its job | Main files | MCP | Services | Face LOC | Last touched | Known problems | Overlaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | **Project Room** (Room and History wings; health, sources, People in the Room, Ask this project, recall) | Go ▸ Projects; the project's desk icon | One place per project: what needs me, what I watch, what changed, what we decided. | `web/src/features/project-room/ProjectRoomCore.tsx`, `project-room/recall/`, `project-room/review/`, `RoomPeopleSection.tsx` | project (50) | project_service (5,321), project_delta_service, room_health_service, recall_service | ~17,900 (whole feature) | 10-16 | The biggest face in the product. The Room review fails on the phone, cause unknown, open (DLT:23). The lead verb ignored a pending Review, fixed (FX DELIVERY-CDE). The real desk had 0 projects (Recon). | Ask AI; Memory; Decisions; Delivery board |
| 11 | **New Project** (the one-screen door) | Desk ▸ New Project; New on the phone | Make a project from a name and its sources. | `features/project-room/door/DoorCore.tsx`, `door/useDoorController.ts` | project_setup_* (part of project) | project_door_service, project_setup_service (1,602) | ~1,900 | 10-16 | The setup interview is parked (`project-room/_parked/setup`). No recent record names a defect. | Accounts (sources) |
| 12 | **Draft update** (the weekly status from a project's records) | Room ▸ Update posture; The week ▸ Draft update (`desk/verbRegistry.ts:1041`); Object ▸ Draft update | Write the Friday status for his manager or team without starting from a blank page. | `features/project-room/update/`, `prepare/PreparePosture.tsx` | project_draft_update, project_publish_update, … | project_update_service (3,178), memory_grounding | inside the Room | 10-16 | One press, 91 s, nothing; the face still said "No updates yet" (Recon R1). No later record says this is fixed: **unknown**. | Automations (the Friday update is also a Workbench template, WB-Recon §3.6); Send |
| 13 | **The steward and reviewer nudges** | Room ▸ Steward posture | A helper per project that drafts the update and proposes a nudge on a PR that waits. | `features/project-room/steward/StewardPosture.tsx` | project_*steward* (5), steward (1), nudge (2) | project_steward_service (2,529), steward_contract | inside the Room | 10-16 | No record of a live run with real sources (FX COVERAGE.md:55-63 lists agent execution and external sign-in as unknown). | Automations; Draft update |
| 14 | **Watches and sources** (Jira, GitHub, Confluence, meetings per project) | Room ▸ sources; Accounts | Bring the project's outside state into the Room. | `features/project-room/` (sources), `pages/cores/connections/` | watch (5), provider (13), connection (2) | watch_service (1,788), watch_sources, jira_provider (1,807), github_provider, confluence_provider | inside the Room | 10-16 | Provider health and sign-in are not verified (AW README:157-162). The project MCP family imports two web routers (`holdspeak/mcp/families/project.py`), which is a layering smell. | Accounts; Automations ("watches" is also an old name for Automations, POSITIONING names table) |
| 15 | **Decisions** (records, New decision, Today ▸ Decisions, supersede) | Desk ▸ New Decision; Today ▸ Decisions; a meeting's Decided | Keep what was decided, why, and what it replaced. | `desk/pullouts/views/DecisionsView.tsx`, `desk/pullouts/DecisionPullout.tsx`, `desk/decide.ts` | decision_record (5), decision (1) | decision_record_service, decision_lifecycle_service | ~930 | 10-17 | The owner rejected New decision (FX README:16-24); rebuilt in #1243 and #1247, his acceptance is open (STATUS:42). A proposed decision read "Decided", fixed (SA README:45). A second mic in the Decisions search, likely open (DD:7-15; `DecisionsView.tsx:355`). | Meeting Outcomes; Room "what we decided"; Memory recall |

### The daily surface

| # | Feature | Where it lives | Its job | Main files | MCP | Services | Face LOC | Last touched | Known problems | Overlaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 16 | **Today** (the Day timeline) | Dock first (`applications.ts:74-83`), Go | Open the laptop and see the day: meetings, what is due, what is next. | `desk/pullouts/IntelligencePullout.tsx`, `desk/pullouts/views/TodayView.tsx` | door (2) | door_service, front_door_service (1,120) | ~2,100 | 10-16 | Today was empty until a meeting existed (Recon §7, job 1). Old work came before Next, fixed (FX DELIVERY-B). The window is still named "Intelligence" in code and in the Desk menu verb "Open Intelligence" (`verbRegistry.ts:367`). | The week; Brief; Needs you |
| 17 | **Brief** (today's brief; the Monday brief) | Today ▸ Brief; **also** the Brief window in Window ▸ Desk (`desk/chair/chairWindows.ts:39`) and phone Go | Read in one minute what changed and what waits. | `desk/pullouts/views/BriefView.tsx`, `desk/chair/ChairHome.tsx` | monday_brief (4), cadence_brief | monday_brief_service (2,455), preparation_brief_service, brief_carry | ~3,900 | 10-16 | Two Briefs (Recon R2). Brief links to a snoozed task did not open, fixed (FX DELIVERY-B). "Question did not complete / not set up" text (Recon R3). | Today; Rhythm's weekly brief |
| 18 | **Needs you** (the list, the bell, the count) | Window ▸ Desk; phone Go; the bell | One list of what waits on him. | `desk/needs/NeedsDrawer.tsx`, `desk/needs/needsFace.ts`, `desk/needsYou.ts` | desk_needs_you | needs_you_aggregate (1,077), needs_you_membership (1,545), attention_ranking | ~3,600 | 10-16 | Four tellers with four numbers (Recon R2); merged into one attention list (PD). Rows repeated themselves, fixed (SA, #1217). Workbench results never reach it (WB-Recon :65). The ambient feed reads only the 4 newest items, open (AD README:31-33). | Follow-through; Brief; Today ▸ To decide |
| 19 | **The week** | Window ▸ Desk; phone Go | See the week: 1:1s to prep, updates to draft, sends to make. | `desk/chair/ChairDesk.tsx`, `desk/surface/objects/Timeline.tsx`, verbs at `verbRegistry.ts:1025-1041` | none of its own | calendar, people, project reads | ~350 + ChairHome | 10-16 | The face moved 166 px on load; caused by the lazy Send well, fixed (MD:107-123). Closed rows hid failure reasons, fixed (SR). | Today |
| 20 | **Notifications** (Qlippy popups, the shade, toasts, desktop notices) | The desk layer; macOS notices | Tell him when something needs him now, once. | `web/src/components/AmbientLayer.tsx`, `desk/components/SystemShade.tsx`, `holdspeak/desktop_notify.py` | heartbeat_notify_test | desktop_notify | ~600 | 10-15 | A toast rendered in three windows at once (Recon R4). A popup that would not go away, fixed (AD). Opening a queued notice does not land, open (THREAD-ASK-REFINEMENT README:87-88). | Needs you |

### Asking, thinking and memory

| # | Feature | Where it lives | Its job | Main files | MCP | Services | Face LOC | Last touched | Known problems | Overlaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 21 | **Ask AI** | Go, ⌘I, Object ▸ Ask AI (`applications.ts:105-114`) | Ask "what do I owe Mira this week?" and get a cited answer. | `desk/components/AskPanel.tsx`, `desk/ask.ts`, `desk/grounding.ts` | ask (4) | ask_service (852), memory_grounding | ~2,300 | 10-17 | 122 s, then `THE HUB REFUSED IT` with no reason (Recon R1); the cause of the delay is not established (PD:86-89). The owner rejected the face (FX README:16-24); rebuilt in #1243 and #1247, acceptance open. "GROUNDED ON 0", fixed (#1218). | Threads; Ask this project; Object ▸ Ask; Develop this thought |
| 22 | **Threads** (modes, `@` sources, slash commands, held tool calls, the Call, Interview) | Desk ▸ New Thread; Object ▸ Continue in thread | A saved conversation with his work that can use tools. | `desk/pullouts/ThreadPullout.tsx` (1,757), `desk/threads.ts`, `desk/components/ThreadComposer.tsx` | thread (1), interview (4) | thread_service (2,820), thread_tools, thread_modes | ~5,200 | 10-17 | The owner rejected the face; rebuilt, acceptance open (FX README; STATUS:42). `/todo` is not idempotent (FX DELIVERY-CDE:25). No production tool sends the Thread elicitation questions (VISUAL-REFINEMENT README:110-111). | Ask AI; Notes; Conductor sessions |
| 23 | **Notes and thoughts** (New Note, Write a thought, Develop this thought) | Desk ▸ New Note **and** Desk ▸ Write a thought (`verbRegistry.ts:167`, `:186`); Capture | Get an idea down, then turn it into a task, a project item or a question. | `desk/pullouts/NotePullout.tsx`, `desk/pullouts/editors/ThoughtNoteEditor.tsx`, `desk/newThought.ts`, `desk/pullouts/ThoughtContextPicker.tsx` | thought (18) | refinement_thought_service (1,938), refinement_context_service, refinement_coordinator, primitive_service | ~2,000 | 10-16 | "A thought is a dead end" (Recon R5). Note → Task, Project, Ask added (PD, DJ). Extracting tasks on Finish is deferred, open (DJ:127-129). The Object menu greyed 7 of 11 verbs on a note (Recon R1); state now unknown. Two menu entries for one record, though POSITIONING says "Note, not Thought". | Threads; Knowledge; Capture |
| 24 | **Knowledge collections** | Desk ▸ New Knowledge | Keep reference material that Ask and Threads can use. | `desk/pullouts/KbPullout.tsx`, `desk/pullouts/editors/KbEditor.tsx` | kb (3) | primitive_service | ~230 | 10-16 | The body saved with a 200 and was lost on reload, fixed (DU README:13-23). | Directory drawers; Notes |
| 25 | **Memory** (search by meaning, recall, standing pages) | Search ▸ Memory only (`applications.ts:337-354`; no Go row) | Ask "what did we decide on X" and get the current answer with its sources. | `pages/cores/ProjectMemoryCore.tsx`, `desk/standingPages.tsx`, `desk/deskMemory.ts` | memory (3) | memory_service, memory_faces, recall_service, meaning_search_service | ~200 (+ pages) | 10-05 | Rows lack owner and source (SA README:47). A memory hit printed raw JSON in Search (Recon R3). A memory-index database lock, fixed; the startup writer is unidentified (STATUS:59-64, 800-802). The README sells memory as a pillar; its face is the oldest in the product. | Room recall; Search; Ask |
| 26 | **Search** (⌘K: objects, verbs, settings, launchers) | ⌘K everywhere | Find any record or run any verb. | `desk/components/DeskToolShelf.tsx` (1,081), `desk/components/paletteHit.tsx` | none | all reads | ~1,300 | 10-17 | Enter on a found thought wrote a file, because a verb row was pre-selected (Recon R5). Phone had no touch close, fixed (#1217). Search is the only door to 10 tools (see §3). | Go; Memory |

### Agents

| # | Feature | Where it lives | Its job | Main files | MCP | Services | Face LOC | Last touched | Known problems | Overlaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 27 | **Conductor** (coding agents, sessions, the terminal pane, launches, answer by voice) | Dock, Go, ⌃3 (`applications.ts:142-155`) | See which Claude Code or Codex session needs him and answer it. | `desk/conductor/ConductorWindow.tsx`, `desk/lane/LaneWindow.tsx`, `desk/components/SessionPullout.tsx`, `desk/pullouts/CoderPullout.tsx` | coder (3), agent (1) | coder_service, conductor_launch, launch_lane, agent_responder (969), launch_rebrief | ~5,700 | 10-16 | The owner rejected the Conductor → Codex session screen (SA BRIEF.md:5); rebuilt in #1200. Opens on "No coder ready · Install hooks" (Recon R7). Live terminal streaming and key delivery to an agent were never seen (SURFACE-REFINEMENT README:111-114; FX COVERAGE.md:59). With no pane, Back repeats (STATUS:865). | Hand to agent; Delivery board; Threads |
| 28 | **Hand to agent** | Object ▸ Hand to agent; drag onto an agent | Give a task, issue or note to a coding agent with its context. | `desk/hand/`, `desk/components/HandSheet.tsx`, `desk/agentHand.ts` | agent_hand | agent_hand_service (751), agent_hand_preview, agent_brief | ~1,300 | 10-13 | No record of a walk from hand to a finished agent result. | Conductor; Automations |
| 29 | **Agents** (saved personas; "New Agent") | Desk ▸ New Agent, which makes a *recipe* (`verbRegistry.ts:225-227`) | Save a role with its own instructions to reuse. | `desk/pullouts/RecipePullout.tsx`, `desk/pullouts/editors/RecipeEditor.tsx` | recipe (4) | recipe_service, recipe_catalog | ~220 | 10-15 | "Agent", "recipe", "persona" and "workbench" are used for one thing (WB-Recon §3.2). The old Agents app is parked but keeps its manifest and route `/companion` (`applications.ts:156-175`). | Thread modes; Automations; Conductor's agents |
| 30 | **The desk's tools for agents** (the MCP server, Reach, control modes) | `holdspeak-mcp`; Settings (MCP and delegation, `web/routes/mcp_http.py`) | Let his own Claude Code or Codex read and act on his desk. | `holdspeak/mcp/server.py`, `holdspeak/mcp/tools.py`, `holdspeak/mcp/families/` | all 257 | authority_service, gate_service, tool_authority | none (no face of its own) | 10-17 (design) | Automation runs get no tools; the one-shot `claude -p` path has no MCP (MCP §2). Three families have no web caller: `reaction.*`, `event.list`, `practice_recipe.*` (§3). | Conductor; Automations |
| 31 | **Delivery board and Mission Control** (PRs, CI, dossiers, delivery terminals, repo and roadmap windows) | Search only; it left the Dock (Recon §3). Launchers in `desk/components/window/launcherRegistry.ts:13-17` | See open PRs, CI, and delivery work across repos. | `desk/components/DeliveryBoard.tsx`, `desk/components/MissionControlConveyor.tsx`, `desk/components/RepoWindow.tsx`, `desk/components/RoadmapWindow.tsx` | none | delivery_service, mission_control_service (from 08-07), delivery routes (~1,600 lines) | ~4,600 | 10-16 | Opens on "Companion repo · owner/repo · ✕ NO LIVE SOURCE" (Recon R7). Terminals opened no window (Recon R1). A successful dossier was never seen (DU open list). | Conductor; Room sources |

### Automation

| # | Feature | Where it lives | Its job | Main files | MCP | Services | Face LOC | Last touched | Known problems | Overlaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 32 | **Workbench** (to become **Automations**; runs, schedules, Resourceful) | Desk ▸ New Workbench (7th of 9); Search ▸ Workbenches (`applications.ts:286-302`) | Have HoldSpeak do one piece of work again and again: the Friday update, follow-ups after a meeting, Monday 1:1 prep. | `desk/components/WorkbenchWindow.tsx`, `desk/components/WorkbenchAutomations.tsx`, `desk/components/workbench/WorkbenchRunsWing.tsx`, `pages/cores/WorkbenchesHomeCore.tsx` | workbench (10) | workbench_service, workbench_runner, resourceful_service, schedule_delegation | ~4,200 | 10-16 | The owner: "Who the fuck would know what a workbench is?" About 45 presses and 12 to 15 minutes to make one; two steps do not work (WB-Recon §2). Failures say "Error: failed" (`holdspeak/services/workbench_runner.py:347`). The run record says `0/0 NO MODEL FAILED` after good results. Changing mode turns the schedule off. Results reach no other face. | Workflows; Rhythm; Steward; Draft update; Brief |
| 33 | **Workflows, sequences and reactions** | Desk ▸ New Workflow; no face for reactions or prepared recipes | Run fixed steps with a receipt per step; react to an event. | `desk/pullouts/WorkflowPullout.tsx`, `desk/pullouts/ChainPullout.tsx`, `desk/pullouts/editors/WorkflowEditor.tsx` | workflow (2), sequence (2), reaction (5), event (1), practice_recipe (3) | sequence_workflow_service, reaction_service, recipe_catalog | ~270 | 10-14 | Sequence Edit rendered nothing and is parked (SR:87-91). A prompt-only workflow had no prompt editor (DU). The reaction and prepared-recipe tools have no web caller (§3). | Automations (the same job under a second name) |
| 34 | **Rhythm** (the Heartbeat, the sweep, cadence loops, the weekly brief) | Search ▸ Rhythm (`applications.ts:221-238`) **and** Settings ▸ Rhythm (`pages/cores/settingsPrefs.tsx:54`) | Keep Needs you current and send the weekly brief on a schedule. | `pages/cores/CadenceCore.tsx` | cadence (11), heartbeat (4) | cadence_service, heartbeat_service (1,249) | ~740 | 10-16 | Showed WRITTEN before the write was done, fixed (SA README:45). Two faces for one setting. | Automations schedules; Brief |

### Engines and setup

| # | Feature | Where it lives | Its job | Main files | MCP | Services | Face LOC | Last touched | Known problems | Overlaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 35 | **Engines** (today also "Runs on", "Concierge", `/models`) | Settings ▸ Engines; HoldSpeak menu (`applications.ts:456-467`, parked aliases) | Say which engine does which work: his LAN model, OpenRouter, Claude Code, Codex. | `web/src/features/runson/RunsOnCore.tsx`, `features/concierge/ConciergeCore.tsx`, `pages/cores/AssignmentEditor.tsx` | concierge (5), model_library (7), inference_assignment (5), inference (1) | about 20 `inference_*` modules (~20,000 lines), concierge_service (2,471), model_library_service, lan_engine_discovery | ~7,000 | 10-16 | Agent CLIs are not engines; OpenRouter takes the first of hundreds of models; Anthropic shows NOT SUPPORTED YET; only groups can be wired (Eng §2). Runs on came back as a ghost window, fixed by moving it into Settings (Recon R4, PD). The desk asked for an engine that was set (Recon R6). Settings ▸ Engines moved 54 px now and then, unknown (FT README:155-161). | Settings; First run; every AI face's engine line |
| 36 | **Settings** (Voice, Meetings, Rhythm, Sounds, People, System, Wallpaper, Guide) | HoldSpeak menu, ⌃4 (`applications.ts:176-204`); wings Settings, Engines, Accounts, Guide (`SettingsCore.tsx:252-255`) | Set a thing once and trust it. | `pages/cores/SettingsCore.tsx`, `settingsPrefs.tsx`, `settingsModels.tsx`, `settingsPeople.tsx` | settings (3) | settings_service (1,077) | ~4,300 | 10-16 | Sections did not open; Try it needed two presses; Answers said "Broken / inference succeeded", fixed (ST). An Auto export save erased the Work calendar name, fixed (SAU). The owner rejected the visual pass and called Voice "vanilla" (SAU README:92-97; SP BRIEF). | Engines; Accounts; Rhythm; Wallpapers |
| 37 | **Accounts** (connections, Send destinations, Jira, GitHub, Confluence, email, Slack) | Settings ▸ Accounts; HoldSpeak menu | Connect the tools his work lives in, once. | `pages/cores/connections/`, `pages/cores/connections/Destinations.tsx` | connection (2), provider (13), channel destinations | connections_service, credential_service, channel_key_file | ~1,600 | 10-16 | Status escaped its badge; Add Jira stood alone (AW DESIGN:3-5); Recheck dropped its ref, fixed (CW). Native sign-in and provider health not verified (AW README:157-162). | Watches; Send; First run |
| 38 | **First run and Setup** (the first-run cards, readiness checks, `holdspeak doctor`) | First open; HoldSpeak menu ▸ Setup (`applications.ts:248-268`); CLI `doctor` | Get from install to a working desk in minutes. | `desk/firstrun/FirstRun.tsx`, `desk/firstrun/SpeechSetup.tsx`, `pages/cores/SetupCore.tsx` | none named | onboarding_service, setup_service, local_ai_setup_service | ~3,850 | 10-15 | Led with a 3 GB bundle, fixed (SA README:46). A wrong SHA-256 in the model catalog blocked a download, fixed; the owner must retry it (MD:9-17, 99-101). | Engines; Accounts; Settings |

### The desk shell

| # | Feature | Where it lives | Its job | Main files | MCP | Services | Face LOC | Last touched | Known problems | Overlaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 39 | **Windows** (drag, zoom, ⌃W, ⌘\`, snap, cascade, Overview) | Everywhere; Window menu | Many pieces of work open at once, each in one place. | `desk/compositor/`, `desk/components/DeskWindow.tsx`, `desk/components/window/Expose.tsx`, `desk/components/window/windowRegistry.ts` | desk_window (6) | desk_window_service (797) | ~5,300 | 10-16 | The keep list: the window kernel works (Recon §4). Windows piled at (24,72) over the icons; sizes did not fit content (Recon R4). | Dock; Overview |
| 40 | **Menus** (Desk, Object, Go, Window, the HoldSpeak menu, the New list) | The menu bar (`desk/components/DeskMenuBar.tsx:43-48`) | One way to open things and act on the front object. | `desk/components/DeskMenuBar.tsx`, `desk/verbRegistry.ts` (1,051), `desk/objectMenu.ts`, `desk/components/DeskMenu.tsx` | desk_verb | none | ~3,600 | 10-17 | Object menu greyed 7 of 11 verbs on a note (Recon R1). The New list has 9 kinds; Workbench is 7th (WB-Recon). "Hide the menus" is still a Desk verb (`verbRegistry.ts:310-315`). Go ▸ Tools is empty (§3). | Search; Dock |
| 41 | **Dock** | The foot of the screen (`desk/components/window/Dock.tsx`) | The daily apps, one press away. | `desk/components/window/Dock.tsx`, `dockState.ts`, `desk/components/dock.css` | none | none | ~1,600 | 10-16 | Missed, Delivery, Terminals and the SENT badge are cut, as the Recon asked. Now: Today, Speak, Meetings, Conductor, People (`applications.ts`); phone: Today, Capture, Meetings, People (`Dock.tsx:503-506`). The owner asked for a shorter Dock (FX FOLLOWUP-DENSITY.md:14). | Go |
| 42 | **The desk screen, icons and drawers** (directories, zones, Get Info, seed notes, Settle in) | The desk itself | His own things on the desk, filed where he put them. | `desk/screen/Screen.tsx`, `desk/drawer/DrawerWindow.tsx`, `desk/components/ZoneWindow.tsx`, `desk/surface/objects/IconGrid.tsx` | desk (8), zone (3) | primitive_service, parked_service, desk_service | ~3,500 | 10-16 | Eight seed notes outnumber his own 8 to 1; icons appear on their own (Recon R7). Directories were missing from the screen and are restored (DESK-DRAWERS-LIVE README:10-17). A scene that fails mid-mount is not disposed, open (STATUS:841-844). Phone: one tap did nothing (Recon §5). | Knowledge; Projects; Search |
| 43 | **Wallpapers** (Change places, atmospheres: Jupiter, Mars, Saturn, Night Train) | Search ▸ Change places, ⌘⇧P (`applications.ts:58-73`) **and** Settings ▸ Wallpaper (`settingsWallpaper.tsx`) | A desk that is pleasant to sit at. | `pages/cores/ChangePlacesCore.tsx`, `pages/cores/settingsWallpaper.tsx`, `desk/gl/` | none | none | ~200 + scenes | 10-16 | Recon R7: "demo chrome", cut Places as an app. Four wallpapers shipped this week; the owner rejected two versions (ORBITAL-PLACES; NIGHT-TRAIN-FIDELITY). POSITIONING: the name is Wallpaper, not Places. | Settings |
| 44 | **Builder tools** (Activity, Processes, Components, Context) | Search only (`applications.ts:269-336`, `:387-403`) | Look under the hood: what the kernel runs, the briefing every agent gets, the component catalog. | `pages/cores/ActivityCore.tsx`, `ProcessCore.tsx`, `ComponentsCore.tsx`, `ConstitutionalContextCore.tsx` | kernel_receipt, pipeline_events | activity_* (from 08-07), invocation_service | ~2,150 | 10-16 | All on the Recon cut list "until each has a job". The Components window returned HTTP 503, cause unknown (T3 RELEASE.md:117-119). | none for the architect |

### Delivery and send

| # | Feature | Where it lives | Its job | Main files | MCP | Services | Face LOC | Last touched | Known problems | Overlaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 45 | **Send to** (destinations, preview, receipts; actuators) | Object ▸ Send to; the Send well on a meeting, note, decision or update | Put the result where his team reads it: Jira, GitHub, Confluence, Slack, email, a folder. | `web/src/features/channels/SendWell.tsx`, `desk/surface/send/SendWell.tsx`, `desk/windowSend.tsx`, `meetings/MeetingSendWell.tsx` | channel (9) | channel_service, channel_cli, channel_email, channel_slack, actuator_service | ~2,800 | 10-17 | The owner found Send ugly (SEND:3); it was hidden below the editor, fixed. A thought could send only to the HoldSpeak folder (Recon R5). A real email or Slack send was never seen (SEND:162-164). An uncertain send now survives reload (T3). | Draft update; Accounts |

45 rows.

## 2. Clusters

| Cluster | Features (# in §1) | Count | The architect's job |
|---|---|---|---|
| A. Capture | Speak (1), hotkey and menu-bar glyph (2), Voice commands (3), Meetings (4), Record (5), Scheduled recording and calendar (6), Capture (7) | 7 | Get what was said and decided into the machine. |
| B. People and commitments | People (8), Follow-through (9) | 2 | Lead three people: what is open between us, who owes what. |
| C. Projects, updates and decisions | Project Room (10), New Project (11), Draft update (12), Steward (13), Watches and sources (14), Decisions (15) | 6 | Know the state of each project, tell others, keep what was decided. |
| D. The daily surface | Today (16), Brief (17), Needs you (18), The week (19), Notifications (20) | 5 | Start the day and know what needs him. |
| E. Asking, thinking and memory | Ask AI (21), Threads (22), Notes and thoughts (23), Knowledge (24), Memory (25), Search (26) | 6 | Ask his work a question; think a thing through; find it again. |
| F. Agents | Conductor (27), Hand to agent (28), Agents (29), the desk's tools for agents (30), Delivery board (31) | 5 | Run and answer his coding agents. |
| G. Automation | Workbench / Automations (32), Workflows and reactions (33), Rhythm (34) | 3 | Have repeated work done for him. |
| H. Engines and setup | Engines (35), Settings (36), Accounts (37), First run and Setup (38) | 4 | Set it up once and trust it. |
| I. The desk shell | Windows (39), Menus (40), Dock (41), Desk screen and drawers (42), Wallpapers (43), Builder tools (44) | 6 | Move around without thinking about it. |
| J. Delivery and send | Send to (45) | 1 | Get the result out to his team. |

## 3. Duplicates and dead ends

### One job, two or more names

- **Three automation concepts and two more half-concepts.** Workbench (32),
  Workflow and Sequence (33), Reactions and Watches (33, 14), Resourceful
  (inside 32), and Rhythm's cadence loops (34) all mean "do this work for me
  later or again". The New list offers Workbench and Workflow side by side
  (`verbRegistry.ts:236`, `:247`). WB-Recon §3.6 adds that Meeting Prep,
  Weekly status, Triage and Morning Brief templates repeat jobs that exist
  elsewhere.
- **Note and Thought.** Desk ▸ New Note and Desk ▸ Write a thought make one
  kind of record (`verbRegistry.ts:167`, `:186`). POSITIONING's names table
  says "Note, not Thought". The MCP family is still `thought.*` (18 tools).
- **Ask in five places.** Ask AI (21), Ask this project in the Room (10),
  Object ▸ Ask AI, Develop this thought (23), and a Thread (22). Each has
  its own grounding words. Recon §3 asks for Thought = Note = Thread.
- **Two Briefs.** Today ▸ Brief and the Brief window (`chairWindows.ts:39`),
  plus the Monday brief and Rhythm's weekly brief. Recon R2 asked to cut the
  Brief window; it is still in Window ▸ Desk and phone Go
  (`DeskMenuBar.tsx:59-64`).
- **"What needs me".** Needs you (18), Follow-through (9), Today ▸ To
  decide, The week, the Room's "what needs me now", People ▸ They owe you.
  PD merged the counts into one list, but six faces still answer the
  question.
- **Decisions in four places.** Meeting Outcomes "Decided", Today ▸
  Decisions, the Room's "what did we decide", and Memory recall.
- **Rhythm twice.** A Rhythm window (`applications.ts:221-238`) and
  Settings ▸ Rhythm (`settingsPrefs.tsx:54`).
- **Wallpaper twice.** Change places (`applications.ts:58-73`) and Settings
  ▸ Wallpaper (`settingsWallpaper.tsx`).
- **Engines under four names.** Engines, Runs on, Concierge and `/models`
  (Eng §2). Three manifest rows still point at it, two of them parked
  (`applications.ts:357-369`, `:456-467`).
- **"Agent" means four things.** A saved persona (New Agent makes a recipe,
  `verbRegistry.ts:225-227`), a coding session in the Conductor, the
  Workbench "Agent" word, and an MCP client.
- **Today is still "Intelligence" in code and in one verb label** ("Open
  Intelligence", `verbRegistry.ts:367`).

### Doors with nothing behind them, or no door

- **Go ▸ Tools is empty.** `deskGo` draws Tools only when an application has
  `go.section: "tools"` (`DeskMenuBar.tsx:141-143`); no row in
  `applications.ts` has it. So Rhythm, Context, Workbenches, Activity,
  Memory, Processes, Commands and Change places, plus Delivery and
  Terminals, are reached only through Search. The `deskGo` comment still
  says Go lists Memory (`DeskMenuBar.tsx:109-112`); it does not.
- **Automations cannot be found.** No icon, no Dock entry, nothing in Go
  (WB-Recon :14-31).
- **MCP tools with no face:** `reaction.*` and `event.list` (the face uses
  `/api/workbenches/{id}/automations` instead, `web/src/desk/api.ts:1218`),
  and `practice_recipe.*` (no web caller of `/api/automations/practice-recipes`,
  `holdspeak/web/routes/automations.py:126-139`). Agents can use them; he
  cannot see them.
- **Verbs that did nothing in the Recon** (R1): Ask AI (a refusal with no
  reason), Draft update (91 s, nothing), Terminals (no window), "Choose an
  engine" on a thought, the Object menu on a note. Terminals left the Dock.
  For Draft update and the note's Object menu, no later record says they
  work: unknown.
- **Run Workbench with no engine** looks live and is dead; "Use it" adds an
  engine but does not assign it (WB-Recon :55-56).
- **Thread elicitation questions** have a face and no production sender
  (VISUAL-REFINEMENT README:110-111).

### Parked items that are still visible or still mapped

- The old **Agents** app: parked, but its manifest row, hub id and route
  `/companion` stay alive (`applications.ts:156-175`).
- **Engines** and **Accounts** compatibility rows sit in the HoldSpeak menu
  as `mark: 2` and `mark: 3` while parked (`applications.ts:465`, `:476`).
- **Settle in** ("Hide the menus") is still a Desk verb
  (`verbRegistry.ts:310-315`), which the Recon cut list named.
- **Seed notes** still sit on a fresh desk (Recon R7); no record says they
  moved.
- **Builder tools** (Activity, Processes, Components, Context, Calendar
  snapshot) stay in Search with no job for the architect (Recon §3).
- **`apple/`** (the iPad and iPhone Swift package) is dormant: last commit
  2026-08-22, referenced only by its own CI workflow. Standing ruling: hold
  it until the web desk is finished.

## 4. Promised but missing

What `README.md` and `docs/internal/POSITIONING.md` promise, against what the
records show:

| Promise | Where promised | What is true |
|---|---|---|
| "Ask your model about any meeting, note, or project, with sources" | README:28, :67-81 | Ask refused with no reason after 122 s (Recon R1). The cause of the delay is not established (PD:86-89). The face was rejected and rebuilt; acceptance is open. |
| "Draft update writes the weekly status from those records" | README:101 | One press, 91 s, nothing (Recon R1). No record of a fix: unknown. |
| "The steward drafts the update and proposes a reviewer nudge" | README:102 | No record of a live run with real sources (FX COVERAGE.md:55-63). |
| "The Monday brief adds what each person owes you" | README:103 | People prep now has both directions (#1221); Follow-through's Mine / They owe is not built (FT README:137-138). People reads return 503 (STATUS:807-812). |
| "Watch live … Answer by voice … SEND to type it into that pane" | README:121-129 ("Watch live" :126) | Live terminal streaming and key delivery were never observed (SURFACE-REFINEMENT README:111-114). |
| "Send … to GitHub, Jira, Slack, or email" | README:28, :107-119 | A real email or Slack send was never observed (SEND:162-164). Sign-in for Jira and GitHub is not verified (AW). |
| "Extend … Workflow: a sequence of steps" | README:141 | Sequence Edit is parked (SR:87-91). Workflow and Workbench are two concepts for one job. |
| "Model … assigned per job" | README:144 | The face assigns groups only; single jobs need MCP. Claude Code, Codex and Anthropic cannot be engines (Eng §2). |
| "256 tools … acts with your owner authority" and an agentic OS | README:11, :28, :148 | The tools serve the Conductor's sessions, but an automation run gets none (MCP §2). |
| "Thread … The Thread has hands … Allow once" | README:77 | Held calls exist; no record of a walk with a real tool hold this week. Unknown. |
| "Memory: standing pages … every sentence cites its sources" | README:83-92 (:90) | The Memory face is from 10-05, its rows lack owner and source (SA README:47), and it is reachable only by Search. |
| "14 built-in plugins … ADR draft, architecture diagram, stakeholder update" | README:62 | The summary, decisions and owed items show. Whether the other plugin outputs reach a face is unknown. |
| "Meeting aftercare shows what changed since the last meeting" | README:64; POSITIONING pillar 3 | Not named in any recent record: unknown. |
| "It learns how you work … replay" | POSITIONING pillar 2 | Replay exists in the Journal (`pages/cores/dictation/Journal.tsx`). Not walked this week: unknown. |
| "A stranger knows what to do first within ten seconds" | POSITIONING:86-87 | Recon: five answers to "what needs me", 31 words not understood on first read, eight seed notes. |
| "A new capability joins one of the four applications or becomes a search tool" | POSITIONING:124-126 | The desk has 26 manifest rows; ten tools hide in Search with no Go row. |
| "Builder tools (Workbench, Commands, Cadence, Activity) are search-reachable, not a tier" | POSITIONING:109-110 | True, and it is the reason Automations cannot be found: the owner's most wanted job sits in a tool tier. |

## 5. A first ranking

Each feature gets two scores from 1 to 5. **Value** is what it is worth to
the architect's week. **Broken** is how far today's face is from doing the
job, from the records above. Rank = value × broken.

### The top 10 features

| Rank | Feature (# in §1) | Value | Broken | Score | One line of reasoning |
|---|---|---|---|---|---|
| 1 | Workbench → Automations (32) | 5 | 5 | 25 | His own named wall. It cannot be found, its name means nothing, and it reports wrong facts. Design and recipe are already drafted. |
| 2 | Ask AI (21) | 5 | 4 | 20 | The question an architect asks every day. It refused with no reason; the rebuilt face waits for his word, and the delay cause is unknown. |
| 3 | Draft update (12) | 5 | 4 | 20 | The Friday status is the core weekly output for a manager. It ended in silence and no fix is recorded. |
| 4 | Engines (35) | 4 | 5 | 20 | Every AI feature stands on it. The engines he pays for (Claude Code, Codex, OpenRouter models) are not choosable. Design drafted. |
| 5 | The desk's tools for agents (30) | 4 | 4 | 16 | 257 tools, and the work that would use them every day gets none. It turns Automations from a prompt into an agent. Design drafted. |
| 6 | Follow-through (9) | 4 | 4 | 16 | "Confusing and ugly" in his words; the Mine / They owe split is missing; six faces answer "what is owed". |
| 7 | Notes and thoughts (23) | 4 | 4 | 16 | The capture he will do most; it still has two names and the extraction on Finish is deferred. |
| 8 | Threads (22) | 4 | 4 | 16 | Rejected and rebuilt; a second Ask with its own grounding words; `/todo` is not idempotent. |
| 9 | Conductor (27) | 4 | 4 | 16 | Agent work is half of "Agentic OS". He rejected the session screen; live terminal and answer delivery were never seen. |
| 10 | People (8) | 5 | 3 | 15 | His three reports. The prep shape works; a 503 on relationships is open and the desk held zero people. |

Next in line, at 15: Brief (17, two Briefs), Record a meeting (5, the
CoreAudio stop cause unknown), and Needs you (18, still six answers to one
question).

### The clusters

| Rank | Cluster | Value | Broken | Score | One line of reasoning |
|---|---|---|---|---|---|
| 1 | G. Automation | 5 | 5 | 25 | The owner's own wall. Five half-concepts for one job, none findable. |
| 2 | E. Asking, thinking and memory | 5 | 4 | 20 | Ask in five places, Note under two names, memory hidden in Search. This is where "Agentic OS" lives or dies. |
| 3 | C. Projects, updates and decisions | 5 | 4 | 20 | Draft update is silent and the steward is unproven. The Room is the largest face (~18,000 lines) and the least walked with real sources. |
| 4 | H. Engines and setup | 4 | 4 | 16 | Engines blocks the CLIs he pays for. Settings was rejected visually, and its many fixes this week show how fragile it is. |
| 5 | F. Agents | 4 | 4 | 16 | The Conductor was rejected and the live loop is unproven. "Agent" has four meanings, and the MCP tools are not given to the runs. |
| 6 | D. The daily surface | 5 | 3 | 15 | The first thing he opens each day. The counts are merged, but Today, Brief, Needs you and The week still split one answer across four faces. |
| 7 | B. People and commitments | 5 | 3 | 15 | The shape is right; the reads are unreliable (503) and Follow-through confuses him. |
| 8 | J. Delivery and send | 4 | 3 | 12 | The face is fixed and survives reload. No real outside send has ever been watched. |
| 9 | A. Capture | 5 | 2 | 10 | The strongest part: the meeting pipeline is the product (Recon keep list). Left: Speak's chip words and the stop hang's root cause. |
| 10 | I. The desk shell | 3 | 3 | 9 | The window kernel works. Left: the empty Go ▸ Tools, ten Search-only tools, seed clutter and demo wallpapers, which make it read as a gimmick. |

The order of betterment designs that follows from this: Automations,
Engines and the MCP rule (all three drafted), then Ask with Threads and
Notes as one design (cluster E), then Draft update with the steward (C),
then Follow-through with People (B), then the daily surface (D).

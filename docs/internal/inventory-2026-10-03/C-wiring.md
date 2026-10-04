# INVENTORY C — the cross-cutting systems, and which processes use them

Date: 2026-10-03. Tree: `origin/main` @ `6ccfa4e0d` (detached worktree, read-only; no tracked file changed).
Paths are relative to the repo root. "PROVED" = run on a real hub booted with a throwaway HOME and DB
(the `tests/e2e/glass_infra.py` `_boot` recipe, real HTTP routes, `save_meeting` as the meeting producer).
Everything else is read from code and carries file:line.

---

## 1. The memory system

### 1.1 What "memory" is — there are five things with that name

| # | Name | What it is | Where |
|---|---|---|---|
| M1 | **Long memory / `memory.search`** | NOT a store. A read-only search over 11 existing tables. Nothing "writes to memory"; a row is in memory only if its table is one of the 11 kinds. | `holdspeak/db/memory.py:21-33` (kinds), `:435` (`search`), `:389` (`recent`) |
| M2 | **Desk memory (the recall face)** | One read that draws decision records as CURRENT / SUPERSEDED / DISPUTED, open commitments as OWED, plus meetings, brief items and "also". Built on M1 plus direct SQL. | `holdspeak/services/recall_service.py:116-`, route `holdspeak/web/routes/memory.py:33`, face `web/src/features/project-room/recall/RecallFace.tsx` |
| M3 | **Workbench agent memory** | A JSONL file per workbench, last 100 entries; fed back into the next run's prompt as `[MEMORY]`. Separate from M1; M1 cannot see it. | `holdspeak/workbench_memory.py:21-95` |
| M4 | **"The Desk remembers" (`deskMemory.ts`)** | Browser-side drafts and window places. UI state only; not knowledge. | `web/src/desk/deskMemory.ts:1-80` |
| M5 | **Dictation project context (`.hs/memory.md`)** | A hand-kept file per repo, read into dictation/agent context. Separate from M1. | `holdspeak/agent_context/models.py:60-86` |

There are no embeddings. Search is lexical only (SQLite FTS5 + `LIKE`), then a one-hop walk over real relationships.

### 1.2 What M1 holds (kinds, key formats, how each is indexed)

Key format is always `<kind>:<id>` (threads: `thread:<id>#<message id>`).

| Kind | Table | Indexed how | Ref |
|---|---|---|---|
| `meeting` | `segments` (transcript text only) | FTS `segments_fts`; parked meetings excluded | `db/memory.py:700-747` |
| `decision` | `decisions` (meeting-extracted decisions) | FTS `decisions_memory_fts`; only rows with `deleted=0 AND source_state='linked'` | `db/memory.py:316-322`, `:631-664` |
| `decision_record` | `decision_records` | `LIKE` scan | `db/memory.py:37-69` |
| `desk_decision` | `desk_decisions` (the Decide window / `POST /api/decisions`) | `LIKE` scan | `db/memory.py:70-80` |
| `artifact` | `artifacts` | FTS `artifacts_memory_fts` | `db/memory.py:666-698` |
| `note` | `notes` (promoted-to-context notes excluded on purpose) | FTS `notes_memory_fts` | `db/memory.py:749-785` |
| `thread` | `thread_message_parts` (not sensitive, not draft, not deleted) | FTS `thread_messages_fts` | `db/memory.py:787-850` |
| `action` | `action_items` | `LIKE` scan | `db/memory.py:81-91` |
| `project_item` | `project_items` (milestones, risks) | `LIKE` scan | `db/memory.py:92-102` |
| `workbench_item` | `workbench_items` | `LIKE` scan | `db/memory.py:103-113` |
| `cadence` | `cadence_loops` | `LIKE` scan | `db/memory.py:114-124` |

**Tables that hold what the product learned and are NOT in memory** (schema: `holdspeak/db/schema.py`):
`intel_snapshots` / `topics` (the meeting SUMMARY and topics, `:128-147`), `monday_briefs` + items (`:2479-2502`; the recall face reads them by its own SQL, `memory.search` does not),
`project_updates` + `project_update_deliveries` (`:4162-4211`), `channel_sends` (`:4235`), `project_briefs` (Prep, `:4522`),
`calendar_events` (`:3717`), `dictation_journal` (`:856`), `decision_commitments` (`:239`; reached only as a relation of a hit),
`follow_through_proposals` (`:4382`), `ask_results` (`:2274`), `speakers` (`:193`), and the whole People store (encrypted sidecar; by design).

### 1.3 Who WRITES (producers of rows that memory can see)

| Kind | Producers |
|---|---|
| meeting / segments | `holdspeak/db/meetings.py:426`, `:502` (`save_meeting`) |
| action | `db/meetings.py:584` (meeting intel), `services/follow_through_service.py:289`, `services/door_service.py:73`, `services/proposal_bridge_service.py:737`, `kernel/meeting_plugin_projection.py:295` |
| decision | `db/decisions.py:308`, `services/proposal_bridge_service.py:678` |
| decision_record | `services/decision_record_service.py:68`, `services/proposal_bridge_service.py:698`, `services/sync_service.py:725` |
| desk_decision | `db/primitives.py:262` (via `POST /api/decisions`, `web/routes/primitives/decisions.py:65`; MCP `desk.create kind=decisions`) |
| note | `db/primitives.py:131` (`POST /api/notes`, MCP `desk.create kind=notes`), `services/refinement_thought_service.py:1323` (a Thought's working note), `rails_observer.py:183` |
| artifact | `db/plugins.py:744`, `workbench_conductor.py:420`, `kernel/workbench_projection.py:37`, `kernel/rails_journal_projection.py:18,51`, `kernel/recipe_projection.py:18` |
| thread | `db/threads.py:204`, `:380` |
| project_item | `db/projects.py:628`, `services/project_service.py:4170`, `:4320` |
| workbench_item | `db/workbenches.py:225` |
| cadence | `db/cadence.py:57` |
| M3 workbench JSONL | `kernel/workbench_projection.py:39-42` (one observation per finished run) |

### 1.4 Who READS

| Consumer | What it reads | Ref |
|---|---|---|
| `GET /api/memory/search` | M1 search | `web/routes/memory.py:19`, `services/memory_service.py:18-48` |
| MCP `memory.search` (outside agents) | same service | `mcp/families/memory.py:13-50` |
| Chat model tool palette | `memory.search` is one of the tools a chat turn may call | `services/thread_tools.py:144`, `:348` |
| `GET /api/memory/recall` (Desk memory face) | M2 | `web/routes/memory.py:33-57`, `services/recall_service.py:497-499` |
| Project Room search box | `/api/memory/search` with `project_id` | `web/src/features/project-room/api.ts:128-131`, `useProjectRoomController.ts:288` |
| Grounding, global relevance pass (model prompts) | `memory.search(query)` when the call has NO explicit ref | `holdspeak/grounding.py:245-262` |
| Grounding, project relevance pass | `memory.search(query, project_id=…)` when a `project:` ref is attached | `holdspeak/grounding.py:510-530` |
| …called with `include_memory=True` by | Ask (`services/ask_service.py:522`, `:580`), desk chat / threads (`services/thread_service.py:392-400`), recipes (`services/recipe_service.py:118`, `:209`), coder (`services/coder_service.py:157`), sequences (`services/sequence_workflow_service.py:55`), workbench runs (`workbench_conductor.py:204-212`) |
| Meeting artifact search | `memory.search(kinds=("artifact",))` | `services/meeting_service.py:566-574` |
| Index rebuild | CLI + schema reconcile | `main.py:530`, `db/reconcile.py:989-1003` |
| M3 | workbench runner prompt | `services/workbench_runner.py:243-244` |

Services with **zero** reads of memory or grounding (grep count 0): `meeting_intel_service`, `project_update_service`, `preparation_brief_service`,
`project_steward_service`, `dictation_service`, `refinement_thought_service`, `follow_through_service`, `meeting_aftercare_service`,
`delivery_service`, `channel_service`, `calendar_snapshot_service`, `heartbeat_service`, `concierge_service`. The Brief
(`monday_brief_service`) reads its own tables by SQL (`:797-1336`), not memory.

### 1.5 The matrix

WRITE = what this process learns lands somewhere `memory.search` / Desk memory can find it.
READ = this process consults memory (or grounding with memory) when it does its work.

| # | Process | WRITE to memory | READ memory |
|---|---|---|---|
| 1 | Meeting ends / summary made | **PARTIAL.** Transcript words: YES (`db/memory.py:700`). Summary and topics: NO — `intel_snapshots`/`topics` are in no kind. **PROVED:** a word only in the summary returns `[]` from `/api/memory/search` and `remembered: 0` from recall. | **NO.** `meeting_intel_service.py` has no memory or grounding call; a summary is made with no knowledge of earlier meetings or decisions. |
| 2 | Decisions (Decide in the meeting, decision window) | **BROKEN in a Project.** Global search finds it (`desk_decision`). The Decide button files it into the project as `decision:<id>` (`web/src/desk/decide.ts:88`), memory's project filter looks for `desk_decision:<id>` (`db/memory.py:78-79`, `:1326`). **PROVED** (repro R1). Also: the Desk memory face shows it only under "also", never as a CURRENT card (cards are `decision_records` only, `recall_service.py:54`). | **NO.** Creating a decision does not look up earlier or conflicting decisions (`db/primitives.py:262`, route `web/routes/primitives/decisions.py:65-101`). |
| 3 | Action items / follow-through | **PARTIAL.** `memory.search` finds them (kind `action`; **PROVED**). The Desk memory face does not: `action` is not in `_ALSO_KINDS` and OWED is built only from `decision_commitments` (`recall_service.py:54`). **PROVED:** recall for the action item's word → `remembered: 0`. | **NO.** `follow_through_service.py`: 0 reads. |
| 4 | 1:1 notes and Prep | **NO (by design).** People notes live in the encrypted People store (`services/people_service.py:205-217`); memory never indexes it. Prep briefs (`project_briefs`) are also not a kind. | **NO.** `preparation_brief_service.py`: 0 memory reads (it reads decision records directly, `:332-343`). The person brief reads linked meetings by its own path (`people_service.py:379-453`). Not proved on the hub (see "not covered"). |
| 5 | The Brief | **PARTIAL.** Not a memory kind; `memory.search` and MCP cannot find a brief. The Desk memory face can (own SQL, `recall_service.py:504-`; **PROVED** `briefs: 3`). | **PARTIAL.** Reads canonical tables by SQL (`monday_brief_service.py:797`, `:1088-1143`, `:1190`, `:1305`), never notes, threads or artifacts. |
| 6 | Weekly / project updates (drafting) | **NO.** `project_updates` and its deliveries are in no kind; a published update cannot be found by search. | **NO.** Drafts from project observations/proposals only (`project_update_service.py:1569-1581`); 0 memory reads. |
| 7 | Dictation / Speak | **NO.** `dictation_journal` is in no kind. | **NO** for M1. It reads M5 (`.hs/memory.md`) and the project KB — a different memory. |
| 8 | Thought / notes | **YES.** Notes: FTS trigger (**PROVED**). A Thought keeps a working note in `notes` (`refinement_thought_service.py:1323`) — read from code, not proved (`POST /api/thoughts` answers `inbox_unavailable` on a bare hub). | **NO.** `refinement_thought_service.py` / `refinement_application_service.py`: 0 memory reads; developing a thought uses only the context the owner attached. |
| 9 | Ask / desk chat | **YES.** Thread messages are indexed (`db/memory.py:787`); read from code. | **PARTIAL (BROKEN inside a Project).** Global pass works (**PROVED**: Ask grounding returns the decision). With a `project:` ref the same question returns zero blocks, and with no query the decision comes back as an unknown ref (repro R1). |
| 10 | The Steward / agents | **PARTIAL.** Workbench runs write artifacts (YES) and M3 JSONL (not searchable). Steward runs (`steward_runs`/`steward_steps`) are in no kind. | **PARTIAL.** Workbench runs read M1 + M3 (`workbench_conductor.py:204-212`, `workbench_runner.py:243`). The Project Steward reads none (`project_steward_service.py`: 0). |
| 11 | The palette search (⌘K) | n/a | **NO.** It matches titles already in the browser store; content search is "deferred, named, not built" (`web/src/desk/components/DeskToolShelf.tsx:8-10`, `:261-270`). |
| 12 | Send / delivery receipts | **NO.** `channel_sends`, `project_update_deliveries`, `delivery_command_receipts` are in no kind. "What did I send, to whom" has no memory answer. | **NO.** |
| 13 | Calendar | **NO.** `calendar_events` is in no kind. | **NO.** (The Brief reads the table directly, `monday_brief_service.py:1190`.) |
| 14 | People relationships | **NO (by design, custody).** | **NO** by relevance. A person reaches a chat turn only as an explicit ref, marked sensitive (`thread_service.py:354-381`). |
| 15 | MCP tools (an outside agent) | **YES.** `desk.create kind=notes` → note → found by search (**PROVED**, and it announced on the bus). | **YES.** `memory.search` returns the same hits as the route (**PROVED**). Same Project-scope defect as row 2. |

**Count (30 cells; row 11 has one):** WRITE — YES 3, PARTIAL 4, NO 6, BROKEN 1. READ — YES 1, PARTIAL 3 (one of them broken inside a Project), NO 11.

In plain words: memory is a search box over some tables. Three things read it (chat/Ask, workbench runs, an outside agent). Every process that *makes* something — the summary, the Brief, an update, Prep, a decision, the Steward — works without it.

### 1.6 Repros (all on a throwaway hub)

**R1 — a decision made with Decide is lost to its Project.** (the `desk_decision:` / `decision:` smell; confirmed)
1. `save_meeting` a meeting; `POST /api/projects {"name":"Atlas"}`; `POST /api/projects/<pid>/meetings/<mid>`.
2. `POST /api/decisions {"title":"Adopt quorumdb for the ledger", …}` → `decision_7ce0e03d975d`.
3. `PUT /api/projects/<pid>/resources/decision:decision_7ce0e03d975d` (exactly what `web/src/desk/decide.ts:88` sends) → 200.
4. `GET /api/memory/search?query=quorumdb` → `[desk_decision:decision_7ce0e03d975d]` (found).
5. `GET /api/memory/search?query=quorumdb&project_id=<pid>` → `[]` (**lost**). Control: `query=kestrel&project_id=<pid>` → the meeting.
6. `hydrate_refs_detailed(qualified_refs=["project:<pid>"], query="what did we decide about quorumdb")` (what Ask/chat calls) → `blocks: []`.
7. Same with no query → `unknown: ["decision:decision_7ce0e03d975d"]` (`grounding.py:381` reads `db.decisions`, the meeting-decision table, for a `decision:` ref). In a chat turn an unknown ref is a refusal (`thread_service.py:401-406`).
8. Control: `PUT …/resources/desk_decision:<id>` → project-scoped search finds it.
Same wrong prefix elsewhere: the Brief writes `decision:<desk decision id>` AND `decision:<meeting decision id>` (`monday_brief_service.py:1097`, `:1108`); `refs.py:36-49` has no `desk_decision` citizen type at all, while `web/src/desk/floorSendBinding.ts:68` and `documentSends.tsx:34` use `desk_decision:`.

**R2 — the summary is not remembered.** Meeting saved with transcript "…kestrel…" and summary "Team agreed the zephyrine migration plan." → search `kestrel`: meeting hit; search `zephyrine`: `[]`; recall `zephyrine`: `remembered: 0`.

**R3 — Desk memory cannot recall an action item.** Action "Draft the quillfeather rollout checklist" → `/api/memory/search?query=quillfeather`: `action:…` hit; `/api/memory/recall?query=quillfeather`: `remembered: 0`.

**R4 — outside agent round trip works.** MCP `desk.create {kind:"notes", data:{…"thornvale"…}}` → `desk_changed note create` frame → `/api/memory/search?query=thornvale` → the note.

A second ref-name split of the same class (not proved to bite): memory names action items `action:<id>` (`db/memory.py:88-90`), the rest of the product names them `action_item:<id>` (`refs.py:38`, `monday_brief_service.py` brief items). The action project filter survives because it also joins through the meeting.

---

## 2. The other cross-cutting systems

Sections 2.1, 2.2, 2.5 and 2.6 were read from code by sub-agents under this lane; the lines marked PROVED were run by me on the throwaway hub; the rest I spot-checked where noted.

### 2.1 The one "needs you" rule

The seam: `computeNeedsYou`, `web/src/desk/needsYou.ts:233` (Door board asking columns `:142-195` + Room rows, deduplicated `:237-253`, + engine-assignment blockers `:257-260`, + failed meeting summaries `:220-223`, `:261`). One shared snapshot: `useNeedsYou` `:490`, polled every 60 s (`:472`).
There is no full backend twin. `desk.needs_you` (`holdspeak/services/project_service.py:536-560` over `services/needs_you_aggregate.py:372`) returns Room rows only, cached up to 900 s (`web/routes/projects.py:606-607`).
**PROVED:** on a hub with one pending action item and one proposed decision, the Brief headline said "1 thing waiting, 1 decision waiting" while `GET /api/desk/needs-you` said `count: 0`.

| Face / process | Uses the one rule? | Ref |
|---|---|---|
| Menu-bar bell, Dock app badge, Dock per-project badge, Attention drawer, Chair "Needs you" window, failed meeting summary | YES | `desk/components/DeskChrome.tsx:43`, `window/Dock.tsx:180,325,393`, `AttentionDrawer.tsx:74,109`, `chair/ChairHome.tsx:456`, `needsYou.ts:220` |
| System shade project list; ⌘K palette "N OPEN" | NO — the Room-only backend count | `SystemShade.tsx:128,155,533`; `DeskToolShelf.tsx:294-302,416` |
| Desktop notifications (heartbeat) | NO — Room-only | `services/heartbeat_service.py:689-693` |
| MCP `desk.needs_you` (an agent asks "what needs him?") | NO — Room-only | `mcp/tools.py:1091-1097`, `operations.py:1813` |
| The Brief | PARTIAL — backend shares the Room aggregate (`monday_brief_service.py:915-919`); the web brief badge counts untriaged items by its own rule (`desk/intelligenceAttention.ts:30-35,49`) |
| Follow-through overdue | NO — own count | `intelligenceAttention.ts:43,48`, `follow_through_service.py:722-746` |
| Decisions to review | NO — not in the rule | `intelligenceAttention.ts:44,50` |
| Meetings list "TO REVIEW" | NO — own rule that reuses the name `needs_you_count` | `db/meetings.py:821`, `pages/cores/history/CatalogRail.tsx:112-126` |
| 1:1 / People overdue | NO — computed in the browser; two client rules + one server rule | `pages/cores/PeopleCore.tsx:451-455,821-822`, `features/project-room/RoomPeopleSection.tsx:146`, `services/room_people_service.py:147-157` |
| Updates / Send failed | NO | `desk/dockState.ts:113-120`, `components/DeliveryBoard.tsx:388,395` |
| Steward / agents waiting on him; thread tool approvals | NO — "NEEDS YOU" label with a third and fourth meaning; approvals counted nowhere central | `desk/missioncontrol.ts:215`, `pages/cores/ProcessCore.tsx:38`, `desk/threads.ts:944,1080` |
| Calendar | NO | `needs_you_aggregate.py:545-555` (only a `next` field) |

Also seen on the hub: an action item with owner "Dana" but `review_state=pending` is put in the `unassigned` lane (`follow_through_service.py:726-727`) and the Brief prints it as "Unassigned: Draft the … checklist". The label is wrong for the reader: it has an owner; it is un-reviewed.

### 2.2 The live bus (`desk_changed`)

The seam: `RuntimeServices.emit_desk_changed`, `holdspeak/runtime/composition.py:179-197`; frame `{type:"desk_changed", data:{kind,id,op,origin}}`. There is no central hook (no middleware, nothing in `OperationRegistry.invoke`, `operations.py:2145-2200`): a write announces only if its service was built with `on_changed`. The web code says so itself: "Other meeting writes, project rooms, thoughts and sync emit no frame" (`web/src/desk/useDeskChangedRefresh.ts:19-21`).

**PROVED** (a `/ws` listener on the throwaway hub, one write at a time):

| Write | Frame |
|---|---|
| `POST /api/notes`, `PUT /api/notes/{id}` | `desk_changed note create/update` |
| `POST /api/decisions`, `PUT /api/decisions/{id}/status` | `desk_changed decision create/update` |
| MCP `desk.create kind=notes` | `desk_changed note create` |
| `POST /api/projects` | **none** |
| `PUT /api/projects/{id}/resources/{ref}` | **none** |
| `POST /api/projects/{id}/meetings/{mid}` | **none** |
| `PUT /api/meetings/{id}` (rename) | **none** |
| `PATCH /api/all-action-items/{id}` (mark done), `…/edit` | **none** |
| `POST /api/brief/generate` | **none** |
| `POST /api/threads` | **none** |

Read from code (not run):

| Write path | Announces? | Ref |
|---|---|---|
| Notes, KBs, zones, workflows, chains, desk decisions; workbenches, items, skills | YES | `services/primitive_service.py:88-561`, `services/workbench_service.py:109-491` |
| Meeting import end / delete / restore; intel queue running/settled; a Send's final settle | YES | `services/meeting_service.py:337,527,536`, `intel_queue.py:81-89`, `services/channel_service.py:615-619` |
| Meeting decisions accept / reject / supersede; decision records supersede / dispute / carry | NO | `web/routes/decisions.py:79-120`, `web/routes/decision_records.py:69-100` |
| Follow-through complete / commit-decision (also does not dirty the needs-you cache) | NO | `web/routes/follow_through.py:110,122` |
| Proposals confirm / edit / dismiss | NO | `web/routes/proposals.py:77-146` |
| People: relationships, 1:1s, agenda, requests, notes, commitments | NO | `web/routes/people.py:73-361` |
| Projects (18 routes), project updates draft → publish, Steward runs / policy / nudges | NO | `web/routes/projects.py:84-671`, `project_updates.py:95-241`, `steward.py:70-248` |
| Send prepare / discard / destinations (only settle announces) | NO | `web/routes/channels.py:99-159` |
| Thoughts, threads (threads stream their own frames) | NO | `web/routes/primitives/thoughts.py:57-343`, `threads.py:91-489` |
| Calendar link / snapshot; watches; cadence; gate; settings | NO | `web/routes/calendar_events.py:67,91`, `calendar_snapshot.py:44,133` |
| Background: calendar ingest, heartbeat sweep, cadence tick, steward runs | NO | no bus call in `calendar_ingest_conductor.py`, `runtime/heartbeat.py`, `runtime/cadence.py`, `project_steward_service.py` |

Web side. Subscribed: the global refresh (`web/src/main.tsx:22`, `useDeskChangedRefresh.ts:46`), `ChairHome.tsx:594`, `AttentionDrawer.tsx:40`, `Dock.tsx:41,242`, `LiveCore.tsx:88`, `HistoryCore.tsx:337`.
Fetch data and subscribe to nothing: `ProjectRoomCore.tsx`, `PeopleCore.tsx`, the Follow-through / Decisions / Brief pullout views, `CalendarSnapshotReviewCore.tsx`, `CadenceCore.tsx`, `history/MeetingDetail.tsx`, `DeskToolShelf.tsx` (reads once).

### 2.3 The engine router / model assignment

The seam: `RoutedInferenceCoordinator` (`holdspeak/services/inference_adoption_service.py:791`; `admit` `:818`, `execute` `:1418`). It resolves the assignment, freezes a route, and lets the fallback controller pick the attempt. Engines are built only from a frozen revision (`holdspeak/inference_targets.py:702`). Read from code by a sub-agent; the thread_practice and read-subprocess lines spot-checked by me.

| Process | Through the router? | Ref |
|---|---|---|
| Live meeting analysis, bookmark label, auto title; deferred summary / decisions / action items; meeting plugins | YES | `meeting_session/intel_routed_children.py:192-314`, `meeting_session/deferred_bound.py:346-392` |
| Desk chat turn; agent tool turn; recipes, sequences, workflow nodes, workbench items; rails summary; decision promotion, cadence draft, PR review draft | YES | `services/thread_service.py:529,1110`, `tool_turn_service.py:105`, `recipe_service.py:145`, `workbench_runner.py:72`, `inference_owner_draft.py:74-156` |
| Live transcription | YES | `speech_session/transcription.py:259-523` |
| Ask; Thought develop; dictation intent / rewrite | YES only when the routed-assignment migration row exists; otherwise the legacy placement path. **Unknown** whether that row always exists on his desk. | `services/ask_service.py:211,310-369`, `services/refinement_coordinator.py:310`, `speech_session/session.py:298-304` |
| Project update draft; Prep brief | PARTIAL — resolves through the route planner, then runs a direct call: no fallback to the next engine | `services/project_update_service.py:1175,1473`, `services/preparation_brief_service.py:986-1015` |
| **Chat guardrail and chat compaction** | **BYPASS, likely broken** — reads the assignment table itself, first entry only, and looks the revision up with `WHERE model=<profile id>`: the exact pattern the repo fixed and named a bug in HS-200-08. Not run. | `services/thread_practice.py:78-100` vs `services/project_update_service.py:1157-1167` |
| Calendar snapshot (vision) | YES first; on ANY error falls back to the first ready vision profile, ignoring the assignment | `services/calendar_snapshot_service.py:582-605,782-801` |
| Agent-context summarizer (claude / codex CLI) | BYPASS — hard-coded CLI | `agent_summarizer.py:254` |
| Import / CLI transcription | BYPASS for model choice (`config.model.name`) | `web/routes/meeting_import.py:25`, `commands/import_recording.py:71` |
| The Brief, recall, memory, Steward | no model call | — |

### 2.4 Egress badges + receipts

Receipt seam: `run_external_egress` (`holdspeak/kernel/external_egress.py:233`); subprocess writes through `PermissionGate.execute_subprocess` (`connector_runtime.py:141`). Badge seam: `EgressChip` (`web/src/desk/surface/gadgets.tsx:745`). Read from code by a sub-agent.

| Outbound call | Receipt | Badge where it happens | Ref |
|---|---|---|---|
| Model calls through the engine (meetings, workbench, update, Prep, Thought) | YES | YES | `intel/engine.py:356`; `meetings/RouteDisclosure.tsx:76`, `UpdatePosture.tsx:500`, `PreparePosture.tsx:707`, `ThoughtWorkspaceWindow.tsx:451` |
| Ask; desk chat | YES | only AFTER the run (a lamp), nothing before he presses | `AskPanel.tsx:354-358`, `ThreadPullout.tsx:1600-1605` |
| Voice intent proposal | YES | always says cloud "AI", whatever the route | `desk/voice/ProposalStrip.tsx:75` |
| Send: Slack, email, GitHub / Jira / Confluence writes | YES | YES | `channel_slack.py:514`, `channel_email.py:751`, `channel_cli.py:75,161`; `SendWell.tsx:450` |
| Telegram | YES | YES (plus one bare "NOT SET" chip) | `cadence_telegram.py:46`; `CadenceCore.tsx:428,641` |
| Dictation rewrite to a remote endpoint | NO egress receipt (exempt on purpose; inference receipt only) | label only | `external_egress.py:14-16`; `SpeakFace.tsx:685-753` |
| Every `gh` / `acli` READ (auth, watches, providers, activity enrichment) | NO — `run_read_subprocess` checks authority and runs, no receipt | Connections: yes; Activity dry-run: NO | `connector_runtime.py:183-196`, `activity_github.py:134`, `ActivityCore.tsx:169` |
| PR receipts `gh pr list` | NO — raw `subprocess.run`, not even gated | a fixed "GitHub" word | `delivery/pr_receipts.py:49,264` |
| Calendar ICS fetch | NO | YES | `calendar_ingest_conductor.py:175`; `SettingsCore.tsx:2043` |
| Model download; TTS weights download | own row / response only, not in the kernel ledger | YES | `inference_acquisition_service.py:96,668`, `web/routes/tts.py:278-292` |
| Agent summarizer (claude / codex CLI) | NO | no face | `agent_summarizer.py:254` |
| Setup probes, steering relay to nodes | NO | unknown | `setup_runtime.py:26,34`, `coder_steering_relay.py:60` |

### 2.5 Send / delivery

The seam: `ChannelService` (`holdspeak/services/channel_service.py:66-67`; prepare `:400`, send `:452`, settle `:575`). What can be sent is the closed list `DOCUMENT_SOURCES` (`services/document_sources.py:542-552`): project update, Brief, desk decision, meeting decision, decision record, meeting summary / digest / follow-up, artifact. Channels: file, GitHub, Jira, Confluence, email, Slack (`services/channel_contract.py:40-48`). Receipts: table `channel_sends` (`db/schema.py:4235`), read back by the SENDS history in the shared SendWell (`web/src/desk/surface/send/SendWell.tsx:714-789`).
(`holdspeak/delivery/` and `delivery_service.py` are a different thing: the coding-factory runtime, not "send a document".)

| Path | One seam? | Ref |
|---|---|---|
| Update, Brief, the three decision kinds, meeting summary/digest/follow-up, artifact — web SendWell and MCP `channel.*` | YES | `document_sources.py:297-539`, `mcp/families/channel.py:42-47` |
| Old Slack export route and desk Slack proposals | parked; refuse | `web/routes/meetings/aftercare.py:47-55` |
| Meeting export download (web), MCP `meeting.export`, CLI export | BYPASS — no receipt, no "sent" record | `web/routes/meetings/crud.py:236-260`, `mcp/tools.py:1078-1079`, `commands/history.py:142` |
| Action item → GitHub issue (aftercare proposal) | BYPASS — a proposal is recorded; **unknown** what executes it after approval | `services/meeting_aftercare_service.py:99-141` |
| Desk GitHub issue / PR comment / commit status; generic webhook | BYPASS (actuators) | `web/routes/actuator_shared.py:241-296` |
| Telegram brief / loops / nudges | BYPASS (kernel egress only) | `cadence_telegram.py:46-53,215-248` |
| "Mark delivered" on an update | records a delivery, sends nothing | `services/project_update_service.py:1929` |
| 1:1 notes / People | no Send at all | — |
| Notes, Thoughts, Prep briefs | not a document source; copy to clipboard only | `document_sources.py:542-552` |

### 2.6 People custody / encryption

What is protected: People records only, in a separate encrypted sidecar (`holdspeak/people/store.py:19`; AES-256-GCM per record, `people/crypto.py:51-71`; key in the OS keychain, `people/keys.py:53-100`). One API: `PeopleService`, owner principal only (`services/people_service.py:1396-1408`).

| Reader / writer | Through custody? | Ref |
|---|---|---|
| Web `/api/people/*`; MCP `people.*` (+ visibility policy) | YES | `web/routes/people.py:66-397`, `mcp/families/people.py:389,499` |
| Door / follow-through person labels, Room People | YES (read in memory) | `services/door_service.py:369-404`, `services/room_people_service.py:1-25` |
| **The Brief as a Send document** | **BYPASS** — the People overlay (names, who-owes-whom counts, next 1:1) is composed under a hard-coded owner principal and frozen into the outgoing document and into `channel_sends.payload` in plain text; the code comment says there is no "People send gate". Spot-checked. | `services/document_sources.py:200-237`, `services/channel_service.py:419-427` |
| Commitment → workbench item | BYPASS — commitment text copied to a plain-text workbench item, later given to the workbench model | `web/routes/people.py:273-343`, `services/workbench_runner.py:287-289` |
| The People policy (INFERENCE / EXPORT / EGRESS) | defined, called only by the two MCP checks. Spot-checked by grep. | `people/policy.py:46-73` |
| A person attached to a chat turn; PR-review bottleneck names | **unknown, likely dead:** both build `PeopleService(self._db)` with the main database where the encrypted store is expected | `services/thread_service.py:354-357`, `services/project_service.py:1843-1849` |
| Action-item owners, speaker names, calendar attendees, decision owners | plain text by design | `db/schema.py:110-114,193-201,3717-3729` |
| Chat turns to a cloud engine | sensitive parts replaced with `[people content withheld]`; kept verbatim for a LAN engine | `services/thread_service.py:1888-1940` |

---

## 3. Ranked gaps

Ranked by what would bite a Senior Architect with three reports in a real week. Size: S = under a day, M = a few days, L = a week or more.

| # | Gap | Proof | Fix in one line | Size |
|---|---|---|---|---|
| 1 | **A decision made with Decide is lost to its Project.** Project search, Ask inside the Room and MCP with `project_id` do not find it; attached with no question it is an "unknown ref". | R1, PROVED | Pick ONE ref name for a desk decision (`desk_decision:`), write it in `decide.ts:88` and the Brief (`monday_brief_service.py:1097`), register it in `refs.py`, and make memory's project filter accept the old `decision:` rows too. | S |
| 2 | **Nothing that writes for him reads memory.** The meeting summary, the Brief, the update draft, Prep and the Steward each start from their own narrow SQL; none knows last week's decision or the note he wrote. | §1.4 (grep count 0), §1.5 | Give the four drafting services (update, Prep, summary, Steward) the same grounding call Ask already uses (`hydrate_refs_detailed(..., include_memory=True)` scoped to the project). | M |
| 3 | **Marking work done does not move the other windows.** Action-item done, follow-through complete, meeting rename, project and People writes, Brief generate send no bus frame; the Room, People and Follow-through windows subscribe to nothing. | §2.2, PROVED (8 writes, 0 frames) | Announce in one place — emit `desk_changed` from `OperationRegistry.invoke` for every mutating operation — and subscribe the Room, People and pullout views. | M |
| 4 | **The numbers disagree.** The bell counts Door cards + Room rows + blockers; notifications, the palette, the system shade and an outside agent get the Room-only count; the Brief has a third. | §2.1; PROVED (Brief "1 waiting, 1 decision", needs-you `count: 0`) | Move `computeNeedsYou` to the backend (`desk.needs_you` returns the full set) and make every face read that one answer. | M |
| 5 | **The Brief, sent out, carries People data with no refusal.** Names, who-owes-whom counts and the next 1:1 go to email / Slack / GitHub in plain text and stay in `channel_sends.payload`. Custody is the owner's hard boundary. | §2.6, spot-checked | Strip the People overlay from the Brief document source (or put it behind his explicit press per send). | S |
| 6 | **The meeting summary is not remembered.** Only transcript words are searchable; a word that exists only in the summary or topics finds nothing. | R2, PROVED | Add the latest `intel_snapshots.summary` + topics to the meeting row in `_meeting_rows` / `_RECENT_SPECS`. | S |
| 7 | **Desk memory cannot answer "what did I send, and to whom" or "what did the update say".** Sends, published updates, Prep briefs and calendar events are in no memory kind. | §1.2 | Add `project_update` and `send` (and `brief`) as `_ECOSYSTEM_SPECS` kinds — a spec entry each, no new index. | S |
| 8 | **The Desk memory face does not recall action items.** `memory.search` finds them, the face drops the kind; OWED shows only decision commitments. | R3, PROVED | Add `action` to the recall read (OWED section) in `recall_service.py:54`. | S |
| 9 | **⌘K finds titles only.** He cannot type a word he remembers from a meeting and land on it. | `DeskToolShelf.tsx:8-10` | Add a "memory" row group in the palette backed by `/api/memory/search` (the rider the file already names). | S |
| 10 | **1:1s stand outside everything**: no Send, no bus frames, "overdue" computed in the browser by its own rules, never in memory (by design) and Prep reads no memory. With three reports this is his most frequent loop. | §1.5 row 4, §2.1, §2.2, §2.5 | Put People commitments into the one needs-you rule and the bus; keep content custody as it is. | M |
| 11 | **"Unassigned" is printed for an item that has an owner** (it is un-reviewed, not unassigned) — on the board and in the Brief. | PROVED (owner Dana → "Unassigned: …") | Name the lane for what it is ("To review") or lane by owner first (`follow_through_service.py:726-729`). | S |
| 12 | **Meeting export, Telegram and the GitHub/webhook actuators go round the Send seam**: no receipt, no SENDS history. | §2.5 | Route meeting export through `ChannelService` (file channel); leave actuators, list them in SENDS. | M |
| 13 | **Chat guardrail and compaction look their engine up the broken way** (`WHERE model=<profile id>`), so long chats may fail to compact on his "Migrated intel endpoint" profile. | `thread_practice.py:95-100`; read, not run | Resolve through the same `_route_plan_deployment` path the update drafter uses. | S |
| 14 | **Ask and desk chat show where the words go only after they went**; the voice proposal strip always says cloud. | §2.4 | Draw the route chip in the composer before Send (the chip and route read exist). | S |
| 15 | **Update draft and Prep do not fall over to the next engine** when the first is down (the LAN box asleep = no draft). | §2.3 | Run both through `RoutedInferenceCoordinator.execute` like Ask. | M |
| 16 | **`gh` / `acli` reads leave no receipt**; PR receipts skip the gate. A ledger gap, not a week-breaker. | §2.4 | Write one receipt in `run_read_subprocess`; route `pr_receipts.py` through it. | S |

---

## 4. Not covered / not proved

- People / 1:1 on the running hub: not run. People setup creates a key in the OS keychain; I did not touch the owner's keychain. Rows 4 and 14 are from code.
- Anything that needs a model on the hub (a real Ask answer, an update draft, Prep, a summary, chat compaction): not run. Ask's memory read was proved by calling its grounding function (`hydrate_refs_detailed`) against the hub's database, not by a full Ask turn.
- Thought on the hub: `POST /api/thoughts` answers `inbox_unavailable` on a bare hub; the Thought row is from code.
- Dictation, calendar, Steward, Send: from code only. No real outbound call was made.
- Sections 2.1-2.6 are sub-agent reads of the code; I proved the bus table and the needs-you mismatch on the hub and spot-checked the People/Brief send path, the policy grep, `thread_practice.py:78-100` and `run_read_subprocess`. The rest of those tables is not re-verified line by line.
- Unknown, named above: whether the routed-assignment migration row always exists (Ask / Thought / dictation legacy path); what executes an approved aftercare GitHub-issue proposal; whether the two `PeopleService(self._db)` sites ever work.
- The web faces were not opened in a browser; face claims are from source.

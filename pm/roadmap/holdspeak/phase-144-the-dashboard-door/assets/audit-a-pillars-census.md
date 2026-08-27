# Phase 144 Pillars Census -- Audit A

Auditor: read-only code census agent  
Branch: main @ ab79c702 (tree clean)  
Date: 2026-08-27

---

## PILLAR 1 -- TODO / Kanban Feedstock

### 1.1  Action Items (meeting-derived)

| Aspect | Evidence |
|--------|----------|
| **Table** | `action_items` -- `holdspeak/db/schema.py:97-109` |
| **Columns** | id, meeting_id, task, owner, due, status, review_state, reviewed_at, source_timestamp, created_at, completed_at |
| **Status values** | `pending` (default), plus runtime values `open`, `done`, `dismissed` -- no CHECK constraint; follow-through terminal set at `follow_through_service.py:103`: `{"done","dismissed","closed","killed"}` |
| **Review states** | `pending` (default), `accepted` -- used by cadence collector to flag `needs_review` |
| **Due field** | TEXT, nullable -- ISO date string |
| **Owner** | TEXT, nullable -- freeform name string |
| **HTTP routes** | Follow-through board: `GET /api/follow-through/board` -- `holdspeak/web/routes/follow_through.py:33-45`; complete verb: `POST /api/follow-through/complete` -- `follow_through.py:47-57`; commit-decision: `POST /api/follow-through/commit-decision` -- `follow_through.py:59-69` |
| **MCP tools** | `follow_through.board` -- `holdspeak/mcp/tools.py:336`; `follow_through.complete` -- `tools.py:345`; `follow_through.commit_decision` -- `tools.py:355` |
| **Web surfaces** | FollowThroughLane (Chair lane, `web/src/desk/chair/lanes/FollowThroughLane.tsx`); FollowThroughView (Intelligence pullout, `web/src/desk/pullouts/views/FollowThroughView.tsx`) |
| **Kanban fitness** | Has status, owner, due, provenance (meeting_id, source_timestamp). Follow-through service already sorts into four lanes: `now`, `waiting`, `unassigned`, `overdue` (`follow_through_service.py:104,135`). Kanban-ready as-is. |

### 1.2  Decision Commitments (follow-through anchor)

| Aspect | Evidence |
|--------|----------|
| **Table** | `decision_commitments` -- `schema.py:220-231` |
| **Columns** | id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at |
| **Status** | `open` (default) -- CHECK not constrained beyond default |
| **Write path** | Created via `FollowThroughService.commit_decision` -- `follow_through_service.py:238-270` |
| **Kanban fitness** | Thin join table linking a decision to an action_item. The action_item carries the kanban state; this table adds provenance only. |

### 1.3  Cadence Loops (open-loop engine)

| Aspect | Evidence |
|--------|----------|
| **Table** | `cadence_loops` -- `schema.py:1636-1654` |
| **Columns** | id, source_type, source_id, project, title, summary, status, priority, needs_review, owner, created_at, updated_at, due_at, snoozed_until, stale_score, last_nudged_at, nudge_count |
| **Status values** | `open` (default), `snoozed`, `closed`, `killed`, `delegated` -- `schema.py:1643` |
| **Priority values** | `low`, `normal`, `high`, `urgent` -- `schema.py:1644` |
| **Source types collected** | `meeting_action`, `meeting_decision`, `pending_proposal`, `agent_question` -- `holdspeak/cadence/collector.py:44-48,51` |
| **Next actions** | `cadence_next_actions` table -- `schema.py:1669-1681`; columns: id, loop_id, kind, title, body_markdown, confidence, reversible, proposal_id, generated_by, generated_at |
| **HTTP routes** | Cadence surface exposed via surface window `surface-cadence` at `/cadence` deep link -- `routes.tsx:64`; dedicated route file `holdspeak/web/routes/cadence.py` |
| **MCP tools** | `cadence.status`, `cadence.loops`, `cadence.get_loop`, `cadence.brief`, `cadence.closeout`, `cadence.history`, `cadence.audit`, `cadence.snooze`, `cadence.set_status`, `cadence.run_now`, `cadence.apply_closeout` -- `holdspeak/mcp/families/cadence.py:16-142` |
| **Web surface** | Settings/Cadence surface window (`SurfaceWindows.tsx:93`) |
| **Kanban fitness** | Rich: status, priority, owner, due_at, stale_score, snoozed_until. The follow-through board already consumes loops alongside action_items (`follow_through_service.py:137-211`). Cards carry `source="cadence_loop"` lane assignment. Kanban-ready. |

### 1.4  Cadence Nudges

| Aspect | Evidence |
|--------|----------|
| **Table** | `cadence_nudges` -- `schema.py:1683-1698` |
| **Status values** | `pending`, `shown`, `acted`, `dismissed`, `expired` -- `schema.py:1691` |
| **Severity** | `quiet`, `normal`, `persistent`, `escalated` -- `schema.py:1689` |
| **Kanban fitness** | Not independently actionable; these are delivery signals for loops. Not a kanban source. |

### 1.5  Refinement Thoughts (Phase 141 "From Thought to Work")

| Aspect | Evidence |
|--------|----------|
| **Table** | `refinement_thoughts` -- `schema.py:859-883` |
| **Columns** | id, create_request_id, raw_utf8, raw_sha256, raw_source_kind, raw_source_ref, raw_captured_at, working_note_id (FK notes.id), working_revision, lifecycle_revision, attachment_revision, attachment_sha256, aggregate_revision, continuity_revision, resume_order, state, created_at, updated_at, completed_at, tombstoned_at |
| **State values** | `working`, `completed`, `tombstoned` -- `schema.py:876` |
| **Continuity** | Tracked via `refinement_invocations` table -- `schema.py:1999-2032`; states: `reserved`, `in_flight`, `awaiting_projection`, `review_ready`, `failed`, `refused`, `cancelled`, `indeterminate`, `unknown`, `stale`, `superseded` |
| **HTTP routes** | `POST /api/thoughts` (create) -- `holdspeak/web/routes/primitives/thoughts.py:51`; `GET /api/thoughts` (list) -- `thoughts.py:68`; `GET /api/thoughts/{thought_id}` -- `thoughts.py:132`; `GET /api/thoughts/{thought_id}/workbench` -- `thoughts.py:148`; plus adopt, default-context, context, complete, resume, refine, stop, review actions |
| **MCP tools** | `thought.create`, `thought.adopt_note`, `thought.get_default_context`, `thought.replace_default_context`, `thought.list_context`, `thought.refine`, `thought.reconcile`, `thought.stop_refinement`, `thought.attach_context`, `thought.detach_context`, `thought.refresh_context`, `thought.answer_review`, `thought.accept_review`, `thought.reject_review`, `thought.answer_and_continue`, `thought.update_working`, `thought.complete`, `thought.resume` -- `holdspeak/mcp/families/thought.py:63-199` |
| **Web surfaces** | ThoughtEntry (input widget, `web/src/desk/chair/ThoughtEntry.tsx`); FinishThoughtsLane (working thoughts lane, `web/src/desk/chair/FinishThoughtsLane.tsx`); ThoughtWorkspaceWindow (`web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx`); ThoughtDocumentPane; ThoughtContextPicker; ThoughtNoteEditor |
| **Kanban fitness** | State machine is rich (`working`/`completed`/`tombstoned` + continuity substates). The FinishThoughtsLane already surfaces unfinished thoughts with `continuity_state` labels (idle, working, review_ready, stale, named_failure, unavailable_remote). Has `updated_at`, source kind, and aggregate revision. **Missing for kanban**: no explicit `owner`, `due`, or `priority` field. Could appear in a "Finish these" lane but not a standard kanban without extension. |

### 1.6  Workbench Items

| Aspect | Evidence |
|--------|----------|
| **Table** | `workbench_items` -- `schema.py:1480-1499` |
| **Columns** | id, workbench_id, title, body, priority, status, grounding_json, context_json, result, result_egress_json, result_artifact_id, mint_attempted, tokens_consumed, created_at, last_modified, claimed_at, completed_at |
| **Status values** | `pending`, `claimed`, `done`, `failed`, `dismissed` -- `schema.py:1487` (CHECK constraint) |
| **Priority** | INTEGER, default 3 -- `schema.py:1485` |
| **HTTP routes** | Workbench CRUD and items via `holdspeak/web/routes/` and main MCP tools file |
| **MCP tools** | `workbench.list`, `workbench.get`, `workbench.create`, `workbench.update`, `workbench.delete`, `workbench.add_item`, `workbench.update_item`, `workbench.delete_item`, `workbench.run`, `workbench.list_runs` -- `holdspeak/mcp/tools.py:116-224` |
| **Web surface** | Workbenches surface window (`SurfaceWindows.tsx:133`), deep link `/workbenches` |
| **Kanban fitness** | Has status, priority, title, timestamps (created_at, claimed_at, completed_at). Owned by a specific workbench (workbench_id). Could be kanban-surfaced per-workbench but items are agent tasks, not owner TODOs. Missing explicit `due` and `owner`. The `body` field carries the task description. |

### 1.7  Decisions (meeting-derived memory)

| Aspect | Evidence |
|--------|----------|
| **Table** | `decisions` -- `schema.py:380-401` |
| **Lifecycle** | `recorded`, `accepted`, `superseded`, `rejected` -- `schema.py:395` (CHECK constraint) |
| **HTTP routes** | `holdspeak/web/routes/decisions.py`; follow-through board (decisions feed the "waiting" lane) |
| **MCP tools** | `decision_record.list`, `decision_record.get`, `decision_record.create_from_meeting`, `decision_record.create_from_desk`, `decision_record.search` (these are the Phase 127 durable records); also `decision.supersede` via tools.py |
| **Web surface** | DecisionsView in IntelligencePullout (`web/src/desk/pullouts/views/DecisionsView.tsx`) |
| **Kanban fitness** | Lifecycle is a decision pipeline, not a task pipeline. Relevant to a dashboard as "recent decisions" or "decisions needing review", not as kanban cards. |

### 1.8  Decision Records (Phase 127 durable)

| Aspect | Evidence |
|--------|----------|
| **Table** | `decision_records` -- `schema.py:1100-1113` |
| **Lifecycle** | `active` (default), no CHECK constraint visible beyond column definition |
| **Related tables** | `decision_record_sources` (schema.py:1115), `decision_record_work` (schema.py:1125), `decision_record_revisions` (schema.py:1135) |
| **Kanban fitness** | Governing document, not a task. Relevant as a dashboard section (recent decisions) but not kanban. |

### 1.9  People Commitments (encrypted sidecar)

| Aspect | Evidence |
|--------|----------|
| **Storage** | Encrypted sidecar store, NOT in schema.py -- `holdspeak/services/people_service.py:1-6`, `holdspeak/kernel/people_store.py` |
| **Projection** | `PeopleCommitmentProjection` protocol -- `follow_through_service.py:89-101`; produces `FollowThroughCard` objects with `source="people_commitment"` |
| **Status** | Managed inside encrypted store; `_OPEN_COMMITMENT = "open"` -- `people_service.py:28` |
| **MCP tools** | `people.readiness`, `people.relationship.list`, `people.relationship.get`, `people.grounding.get`, `people.relationship.create`, `people.one_on_one.create`, `people.agenda.add`, `people.note.create`, `people.request.create`, `people.request.accept`, `people.commitment.transition` -- `holdspeak/mcp/families/people.py` |
| **Web surface** | Follow-through board (people cards overlay) -- `follow_through_service.py:217-231`; People surface window (`SurfaceWindows.tsx:227`) |
| **Kanban fitness** | Already projected into follow-through lanes. Cards have id, text, owner, due, status, lane, target_ref. Kanban-ready via the existing projection. |

### 1.10  Watches and Reactions (connector event system)

| Aspect | Evidence |
|--------|----------|
| **Tables** | `connector_watches` -- `schema.py:2214-2226`; `connector_reactions` -- `schema.py:2251-2264`; `service_events` -- `schema.py:2230-2248`; `reaction_event_projections` -- `schema.py:2269-2277` |
| **Watch states** | `enabled` flag (0/1), `last_success_at`, `last_error` |
| **Reaction flow** | Event matches pattern -> projects into a workbench_item + optional auto-run |
| **MCP tools** | `watch.list`, `watch.create`, `watch.set_enabled`, `watch.refresh`, `watch.preview`, `event.list`, `reaction.list`, `reaction.create`, `reaction.set_enabled`, `reaction.process` -- `holdspeak/mcp/families/reactions.py:19-56` |
| **Kanban fitness** | Watches are infrastructure, not tasks. Their projected workbench_items are the actionable artifacts. Not a direct kanban source. |

### 1.11  Delivery/Work Attempts

| Aspect | Evidence |
|--------|----------|
| **Table** | `work_attempts` -- `schema.py:1785-1804` |
| **State values** | `starting`, `working`, `waiting`, `idle`, `ended`, `abandoned`, `unknown` -- `schema.py:1799` |
| **Web surface** | MissionControlConveyor (`web/src/desk/components/MissionControlConveyor.tsx`); delivery terminal, delivery dossier |
| **Kanban fitness** | Coder/agent work tracking. Not owner TODO items. Could appear as "what agents are doing" but is infrastructure. |

### 1.12  Monday Brief Items

| Aspect | Evidence |
|--------|----------|
| **Table** | `monday_brief_items` -- `schema.py:2190-2199` |
| **Sections** | `changed`, `broke`, `waiting`, `decisions` -- `monday_brief_service.py:14` |
| **Shelf** | `monday_brief_item_shelf` -- `schema.py:2204-2210`; states: `acknowledged`, `deferred` -- `monday_brief_service.py:29` |
| **MCP tools** | `monday_brief.get`, `monday_brief.generate` -- `holdspeak/mcp/tools.py:365-371` |
| **Web surface** | BriefLane (Chair lane, `web/src/desk/chair/lanes/BriefLane.tsx`); BriefView (`web/src/desk/pullouts/views/BriefView.tsx`) |
| **Kanban fitness** | Informational digest items, not tasks. The "waiting" section items could be read as kanban, but they are projections of action_items/commitments that already exist as primary objects. Not a kanban source. |

### PILLAR 1 GAPS TABLE

| Gap | Description | Impact on kanban |
|-----|-------------|------------------|
| **No unified task table** | Tasks exist as action_items, cadence_loops, workbench_items, people commitments (encrypted), and thoughts -- five separate stores with different schemas. | A kanban must query N sources or compose through FollowThroughService (which does 3 of 5 today). |
| **Thoughts lack owner/due/priority** | `refinement_thoughts` has state+continuity but no owner, due_at, or priority field -- `schema.py:859-883`. | Cannot slot into standard kanban lanes without extension or convention (e.g., tag-based priority). |
| **Workbench items lack due/owner** | `workbench_items` has status+priority but no `due` or human `owner` -- `schema.py:1480-1499`. | Agent-work items are workbench-scoped; no cross-workbench kanban without a new query. |
| **No kanban-specific metadata** | No table carries a "kanban lane" or "board position" column. Lane assignment is computed at read time by FollowThroughService. | A dashboard kanban that is more than follow-through must compute lanes or add metadata. |
| **People commitments are opaque** | People data lives in an encrypted sidecar; the only read path is `PeopleCommitmentProjection.list_cards()`. | The follow-through board already handles this; a dashboard kanban can reuse it. |
| **No cross-object "tag" or "label"** | Action items have no general tagging; thoughts have tags (via note); cadence has project. | Filtering a kanban by category requires per-source logic. |

---

## PILLAR 2 -- Upcoming Meetings

### 2.1  Scheduled Recordings

| Aspect | Evidence |
|--------|----------|
| **Table** | `scheduled_recordings` -- `schema.py:3354-3375` |
| **Columns** | id, title, cron_expr, tz, one_shot, duration_minutes, enabled, revision, created_at, last_fired_at, next_fire_at, armed_at, deadline_at, state, last_outcome, last_receipt_id, delegation_receipt_id |
| **State values** | `idle`, `arming`, `recording`, `stopped`, `cancelled`, `refused`, `missed` -- `schema.py:3369` (CHECK constraint) |
| **Conductor** | `holdspeak/scheduled_recording_conductor.py` -- lifecycle: enabled schedule -> cron tick -> arm -> countdown -> fire (start recording) -> auto-stop. Functions: `_tick` (line 338), `_arm` (line 368), `_countdown_then_fire` (line 400), `_fire` (line 473), `_auto_stop` (line 546) |
| **Cron** | `holdspeak/cron.py` -- `cron_is_due()` (line 34), `next_cron_fire()` (line 61); standard 5-field minute/hour/dom/month/dow |
| **next_fire_at** | REAL (epoch seconds), nullable -- computed by `next_cron_fire()` and stored; the dashboard-visible "next upcoming" field |
| **HTTP routes** | `GET /api/scheduled-recordings` (list), `POST /api/scheduled-recordings` (create), `GET /api/scheduled-recordings/{id}`, `PATCH /api/scheduled-recordings/{id}`, `DELETE /api/scheduled-recordings/{id}`, `POST /api/scheduled-recordings/{id}/cancel` -- `holdspeak/web/routes/scheduled_recordings.py:58-148` |
| **MCP tools** | `scheduled_recording.list`, `scheduled_recording.create`, `scheduled_recording.update`, `scheduled_recording.delete`, `scheduled_recording.cancel_armed` -- `holdspeak/mcp/tools.py:375-413` |
| **Web surface** | MeetingsLane (Chair lane) shows enabled scheduled recordings with SCHEDULED badge and next-fire time -- `web/src/desk/chair/lanes/MeetingsLane.tsx:101-111,126-162`. Sorted after live meetings, before archived. |

### 2.2  Calendar/ICS/OWA Connector

| Aspect | Evidence |
|--------|----------|
| **ICS/iCalendar imports** | **NONE FOUND.** Grep for `ics`, `icalendar`, `calendar.*import`, `owa`, `outlook` across `holdspeak/**/*.py` returned zero import/library references. |
| **Calendar activity connector** | `holdspeak/connector_packs/calendar_activity.py:1-80` -- reads `activity_records` for known calendar/video-call domains (Teams, Google Meet, Zoom, Webex) from browser history and creates `activity_meeting_candidates` rows. This is a browser-history heuristic, NOT a calendar API integration. |
| **activity_meeting_candidates table** | `schema.py:690-712` -- columns: id, source_connector_id, source_activity_record_id, dedupe_key, title, starts_at, ends_at, meeting_url, started_meeting_id, confidence, status, created_at, updated_at |
| **Recognized domains** | `holdspeak/activity_candidates.py:19-21` -- `outlook.live.com`, `outlook.office.com`, `outlook.office365.com` plus Teams/Zoom/Google Meet domains |
| **Phase 135 ruling** | Memory says "black-box OWA/Playwright, ICS first" was RULED, but NO implementation was built. |

### 2.3  What "Upcoming" Data the Hub Knows Today

| Data source | What it provides | Gap |
|-------------|------------------|-----|
| **scheduled_recordings** (enabled, next_fire_at) | Exact next fire time for owner-configured cron-driven recordings | Not a "meeting" -- it is a recording schedule. No title/attendees/agenda unless the owner typed one. |
| **activity_meeting_candidates** | Browser-history-derived meeting URLs with starts_at/ends_at | Heuristic, stale, no agenda/attendees. Confidence field present but low-fidelity. |
| **meetings** (in-progress) | A live recording has `capture_status='active'`, no `ended_at` | Present-tense, not upcoming. |
| **No ICS/CalDAV/OWA/Google Calendar** | Zero lines of calendar-protocol code exist in the codebase. | The hub cannot know an owner's future meeting calendar today. This is the single largest gap for a "Dashboard Door" that wants to show upcoming meetings. |

### PILLAR 2 GAPS TABLE

| Gap | Description | Impact on dashboard |
|-----|-------------|---------------------|
| **No calendar integration** | Zero ICS/CalDAV/OWA/Google Calendar protocol code. Phase 135 ruled the approach but nothing was built. | An "upcoming meetings" section can only show scheduled_recordings.next_fire_at and (weakly) activity_meeting_candidates. |
| **activity_meeting_candidates are stale heuristics** | Derived from browser history visits, not live calendar state. No refresh cadence. | Cannot be trusted as "upcoming" without user confirmation. |
| **scheduled_recordings have no agenda/attendees** | Just title + cron + duration. | A recording schedule is not a meeting invitation; it lacks the social context a meeting card needs. |
| **No meeting-title suggestion** | A scheduled recording gets a user-typed title or empty string. | Dashboard cannot auto-label "Daily standup" etc. without calendar integration. |

---

## PILLAR 3 -- Existing Dashboard-ish Surfaces

### 3.1  The Chair (the "/" mount)

| Aspect | Evidence |
|--------|----------|
| **Entry** | `web/src/routes.tsx:20-21` -- path `/`, component `Desk` (lazy import of `DeskApp`) |
| **DeskApp** | `web/src/desk/DeskApp.tsx` -- renders ChairHome when no editing/pullout is active |
| **ChairHome** | `web/src/desk/chair/ChairHome.tsx:38-63` -- composes: hero slot (ThoughtEntry or null when foreground work), activeWork slot (FinishThoughtsLane), four lanes from LANE_COMPONENTS registry |
| **Lane order** | `brief` -> `follow-through` -> `meetings` -> `agents` -- `web/src/desk/chair/laneContract.ts:26-31` (counsel ruling B.Q2: urgency gradient) |
| **Data routes** | BriefLane reads `GET /api/brief/latest`; FollowThroughLane reads `GET /api/follow-through/board`; MeetingsLane reads store (meetings + scheduled recordings); AgentsLane reads `GET /api/coders/status` + `GET /api/recipes` |

### 3.2  Monday Brief (generation + surface)

| Aspect | Evidence |
|--------|----------|
| **Generation** | `holdspeak/services/monday_brief_service.py:56-120` -- MondayBriefService.generate() computes a window (17:00 close, Mon->Fri or weekend->Fri), collects changed/broke/waiting/decisions from pipeline_events + follow_through + decisions |
| **Persistence** | `monday_briefs` + `monday_brief_items` + `monday_brief_item_shelf` tables -- `schema.py:2180-2210` |
| **HTTP routes** | `GET /api/brief/latest`, `POST /api/brief/generate`, `GET /api/brief/shelf`, `POST /api/brief/items/{item_id}/shelf` -- `holdspeak/web/routes/monday_brief.py:22-51` |
| **MCP tools** | `monday_brief.get`, `monday_brief.generate` -- `tools.py:365-371` |
| **MCP resource** | `holdspeak://briefs/latest` -- `holdspeak/mcp/resources.py:188,463-465` |
| **Web surfaces** | BriefLane (Chair lane, `web/src/desk/chair/lanes/BriefLane.tsx`); BriefView in IntelligencePullout (`web/src/desk/pullouts/views/BriefView.tsx`) |

### 3.3  Intelligence Pullout (Phase 128)

| Aspect | Evidence |
|--------|----------|
| **Entry** | `web/src/desk/pullouts/IntelligencePullout.tsx:1-80` |
| **Three views** | `brief` (BriefView), `follow-through` (FollowThroughView), `receipts` (DecisionsView) -- `IntelligencePullout.tsx:12-16` |
| **View persistence** | localStorage key `hs.desk.intelligence-view` -- `IntelligencePullout.tsx:10` |
| **Navigation** | `intelligenceNavigation.ts` -- allows programmatic view switching and overdueOnly filter |
| **Data routes** | BriefView: `GET /api/brief/latest` + shelf; FollowThroughView: `GET /api/follow-through/board`; DecisionsView: decision records API |

### 3.4  Belt / MissionControl (delivery conveyor)

| Aspect | Evidence |
|--------|----------|
| **Implementation** | `web/src/desk/missioncontrol.ts:7-9` -- "the belt renders view shapes. Statuses are typed and honest" |
| **Data** | Belt frames from the WebSocket bus (scope `"belt"`) -- `missioncontrol.ts:191-198` |
| **Web surface** | MissionControlConveyor (`web/src/desk/components/MissionControlConveyor.tsx`) |
| **Content** | Agent sessions, delivery work attempts, PR status -- infrastructure monitoring, not owner TODOs |

### 3.5  Surface Windows Registry

All surfaces registered in `web/src/desk/components/SurfaceWindows.tsx:37-240`:

| Surface ID | Label/Purpose |
|------------|---------------|
| `surface-dictation` | Dictation |
| `surface-meetings` | Meetings review |
| `surface-live` | Live recording |
| `surface-settings` | Settings |
| `surface-cadence` | Cadence engine |
| `surface-setup` | Setup |
| `surface-constitutional-context` | Constitutional context |
| `surface-workbenches` | Workbenches |
| `surface-companion` | Agents / personas |
| `surface-components` | Design components |
| `surface-activity` | Activity intelligence |
| `surface-project-memory` | Project memory |
| `surface-processes` | Processes |
| `surface-commands` | Commands |
| `surface-people` | People |

### 3.6  FinishThoughtsLane (activeWork slot)

| Aspect | Evidence |
|--------|----------|
| **Entry** | `web/src/desk/chair/FinishThoughtsLane.tsx:45-60` |
| **Data** | Calls `unfinishedThoughts()` from `web/src/desk/thoughts.ts` (paginated via cursor) |
| **Content** | Lists thoughts in `working` state with continuity labels: idle, reserved, in_flight, awaiting_projection, review_ready, stale, named_failure, unavailable_remote -- `FinishThoughtsLane.tsx:5-15` |
| **Position** | Sits in the Chair's `activeWork` slot, ABOVE the four lanes -- `ChairHome.tsx:59` |

### PILLAR 3 GAPS TABLE

| Gap | Description | Impact on dashboard |
|-----|-------------|---------------------|
| **No single "dashboard" surface** | The Chair at `/` is the closest thing: four lanes + thoughts + hero. But it is a composition of independent lanes, not a unified dashboard. | Phase 144 would either extend the Chair or create a parallel surface. |
| **No TODO count/badge** | The Chair lanes show items but no global badge like "3 overdue, 2 waiting". The Intelligence attention system (`intelligenceAttention.ts`) tracks untriaged brief items but not follow-through counts. | A dashboard needs a headline count widget. |
| **No upcoming-meetings lane** | MeetingsLane shows past meetings + scheduled recordings. There is no "upcoming" section because there is no calendar source (Pillar 2 gap). | Dashboard cannot show "next meeting in 45 min" without calendar integration. |
| **Brief and Follow-Through are separate lanes** | They share a surface (Intelligence pullout) but are separate Chair lanes. A dashboard might want to merge their signals. | Composition decision, not a technical gap. |

---

## What a Door Could Compose Today Without New Backend

The Chair at `/` (`ChairHome.tsx:56-62`) already provides the composition frame: hero, activeWork, and four ordered lanes. A "Dashboard Door" could recompose existing backend data without new tables or routes:

1. **TODO Kanban**: The `GET /api/follow-through/board` endpoint (`follow_through_service.py:122`) already returns four lanes (`now`, `waiting`, `unassigned`, `overdue`) merging action_items + cadence_loops + people_commitment projections. This is the closest existing kanban read model. The `POST /api/follow-through/complete` verb handles status transitions. A dashboard kanban rendering these four lanes is achievable with zero new backend -- it is what the FollowThroughLane and FollowThroughView already do, just in a different visual shape.

2. **Upcoming Meetings**: Today the only "upcoming" data is `scheduled_recordings` with `enabled=1` and `next_fire_at` -- already surfaced in MeetingsLane (`MeetingsLane.tsx:101-162`). `activity_meeting_candidates` with future `starts_at` could supplement this but are unreliable heuristics. Showing scheduled recordings sorted by next_fire_at is achievable; showing real calendar meetings requires new backend (ICS/CalDAV integration).

3. **Scheduled Recordings**: Fully served by existing `GET /api/scheduled-recordings` + conductor state. The MeetingsLane already renders them with SCHEDULED badge and next-fire label.

4. **Thoughts in Progress**: The FinishThoughtsLane (`FinishThoughtsLane.tsx`) already surfaces unfinished thoughts with continuity state. Reusable as a dashboard "active work" section.

5. **Monday Brief Headline**: `GET /api/brief/latest` returns the brief with headline, sections, and shelf state. The BriefLane already renders a condensed view.

**What requires new backend**:
- Real calendar integration (ICS import, CalDAV, OWA Playwright scraper) for true "upcoming meetings"
- A unified task count/status endpoint that merges action_items + cadence_loops + thoughts + people commitments into a single summary (the follow-through board is close but excludes thoughts and workbench items)
- Any kanban persistence (lane overrides, manual ordering) beyond the computed lanes

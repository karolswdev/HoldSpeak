# Projects, updates and decisions: the code map

Read from main `68e49a296` on 2026-10-17. No code changed. This is the
"what it is in data" input for `DESIGN.md` and `RECIPE.md`. Line numbers
drift; check them before you build.

## 1. A project in data

| Thing | Table | Notes | Source |
|---|---|---|---|
| Project | `projects` | name, description, keywords, team members, purpose, outcome text, owner, lifecycle, posture, target date, review cadence, revision, `room_read_at` | `holdspeak/db/schema.py:552-581` |
| Meeting link | `meeting_projects` | source, confidence (auto-detect uses `detection_threshold`, default 0.4) | `schema.py:584-591` |
| Filed thing | `project_resources` | `resource_ref` (note, meeting, decision record, …), relationship | `schema.py:1639-1653` |
| Plan item | `project_items` | milestone, risk, dependency, signal, workstream. No decision kind | `schema.py:1669-1688` |
| Outside state | `project_sources`, `project_observations`, `project_evidence_links` | watches write observations | `schema.py:4201-4255` |
| Review | `project_proposals`, `project_reviews` | the steward's and the delta's proposals | `schema.py:4257-4305` |
| Update | `project_updates`, `project_update_deliveries` | one row per draft revision; `generator` is `model:<assignment>` or `deterministic` | `schema.py:4307-4360` |
| Steward | `steward_policies`, `steward_runs`, `steward_steps`, `steward_commands` | | `schema.py:4417-4512` |
| Ask, brief | `project_ask_tasks`, `project_briefs` | | `schema.py:4638`, `:4678` |

One read builds the Room: `ProjectService.room()` returns 16 sections, each
built in isolation so one failure does not blank the face
(`holdspeak/services/project_service.py:710-821`).

Size: `web/src/features/project-room` is 15,310 lines of `.ts/.tsx` without
tests and `_parked` (`ProjectRoomCore.tsx` alone 3,114; `model.ts` 1,206);
`_parked` holds 5,862 more. The services: `project_service.py` 5,321,
`project_update_service.py` 3,178, `project_steward_service.py` 2,529.

## 2. The Room

- **Postures** (one at a time): Review, Update, Steward, Prepare, then the
  Room itself (`web/src/features/project-room/ProjectRoomCore.tsx:2870-2915`).
  With no project, the window shows Recall (`:2867`).
- **Wings**: Room and History (`:2957`, `:2982`).
- **Main column**: head (`:347`), Open here / Needs you (`:894`, `:959`),
  Unfinished (`:2187`), Plan (`:1250`), Health (`:467`).
- **Folds**: Sources (`:1339`), Pages, Decisions and owed (`:1854`), Since you
  looked (`:1779`), Files (`:1633`), People (`RoomPeopleSection.tsx`), Briefs
  (`:2221`), Writes (`:1724`). Plus the Send well (`:2681`) and the Ask well
  (`:2302`).
- The health word is a lookup of `AT RISK`, `ON TRACK`, `NEW`
  (`ProjectRoomCore.tsx:345`). The walk showed "On track" with a blocked
  release, so the rule does not read risks from meetings or notes.
- The window is registered as `surface-project-memory`, app
  `open-project-memory`: in code the Room is still "project memory".

| Verb | Route | State |
|---|---|---|
| Draft update (head) | `POST /api/projects/{id}/updates/draft` (`update/api.ts:34`) | live; failure hidden (§3) |
| Review N | `/api/projects/{id}/delta`, `/reviews…` (`review/api.ts:12-56`) | live |
| Watch sources (opens the steward) | `/api/projects/{id}/steward/runs`, `/policy` (`steward/api.ts:16-82`; button `ProjectRoomCore.tsx:1444-1447`) | live, wrong label |
| Prepare | `/api/projects/{id}/briefs/prepare` (`prepare/api.ts:36`) | live |
| Confirm / Dismiss proposal | `/api/proposals/{id}/confirm|dismiss` (`api.ts:152`, `:161`) | live |
| Watch pause / resume / retire | `/api/watches/{id}/…` (`api.ts:107-121`) | live |
| Nudge send / dismiss | `/api/nudges/{id}/send|dismiss` (`api.ts:229`, `:238`) | live |
| Decision accept / supersede | `/api/decisions/{id}/{action}` (`api.ts:75`) | dead: no face caller |
| `promoteDecision`, `fetchProject` | `api.ts:86-87`, `:33` | dead: no callers |
| Review "Draft update (P3)" | `review/ReviewPosture.tsx:358-360` | dead: a hidden placeholder |

## 3. Draft update, traced

1. The head button calls `updateCtrl.draft("model" | "deterministic")`
   (`ProjectRoomCore.tsx:438-447`). It picks "model" when the engine state is
   "set", and `useEngine` counts `no_compatible_assignment` as "set"
   (`web/src/desk/hooks/useEngine.ts:51`).
2. `draft()` posts and, on success, switches to the editor. On failure it
   stores the reason and calls `fail("DRAFT NOT MADE", …)`, but leaves the
   posture off (`update/useUpdateController.ts:205-249`). The Update posture,
   the only face that draws that error, mounts only when the posture is not
   off (`ProjectRoomCore.tsx:2880`). **Result: the failure is never shown.**
3. The route is an `async def` that calls the operation directly, with
   `strict_model_failure: True` (`holdspeak/web/routes/project_updates.py:95-106`).
   No thread: the model call runs on the server's event loop. **Result: the
   whole hub stops answering while the model works** (walk: `/health` took
   74 s). Briefs do it right with `asyncio.to_thread`
   (`project_briefs.py:90`).
4. The service reads the Room at one revision, linked meetings' summaries and
   open owned actions, `room.decisions`, open proposals, up to 500
   observations, and, for a model draft, memory pages "what changed this
   week" and "what is open" (`project_update_service.py:1936-2083`).
5. One model call with a JSON schema and a 120 s deadline
   (`project_update_service.py:1802-1934`, `:1880-1900`; capability
   `project.update_draft`, not marked structured,
   `holdspeak/inference_capabilities.py:1119`). If the text does not parse
   against the source refs, the result is unusable (`:1920-1924`).
6. In strict mode a failure raises `project_update_model_failed` with reason
   `no_engine`, `did_not_answer` or `not_usable`, and **nothing is saved**
   (`:2102-2114`). The face sends no `command_id`, so no command row records
   the failure either (`update/api.ts:36`; `:2260-2266`).
7. The records draft ("deterministic") maps fields to sections in about
   0.1 s. Its `Source Coverage` line is a constant: "All sources consulted
   successfully." (`project_update_service.py:336`). It puts every linked
   meeting's summary in Progress, including 1:1s.

Other doors to "Draft update":

| Door | Code | Same path? |
|---|---|---|
| Object menu, palette "Draft update for …" | `web/src/desk/verbRegistry.ts:469-482`, `:1039-1045` | No: opens the update list; drafts nothing |
| Update list "Draft update" | `update/UpdatePosture.tsx:515-551` | Same call; the error is shown here |
| MCP `project.draft_update` | `holdspeak/mcp/families/project.py:1676-1677` | Same operation without strict mode: a failed model draft silently becomes a records draft (`project_update_service.py:2115-2122`) |
| Steward effect `draft_update` | `project_steward_service.py:1515-1556` | Always the records draft (`:1533`), though the steward face promises more (`steward/model.ts:246-249`) |
| Watch action `project.update.draft` | `holdspeak/watch_validation.py:57-65` | Accepted as a rule action; nothing ever runs it (§5) |
| A "Friday update" automation | none | Does not exist. The TODO Agent starter has an item "Draft the weekly status update" (`holdspeak/workbench_templates.py:37`), answered by one generic model call that never touches `project_updates` |

## 4. The steward

- Six phases: Observe, Compare, Propose, Act, Verify, Record
  (`project_steward_service.py:1-17`, `:35`). Act walks seven effect kinds:
  refresh sources, create proposals, apply proposal effects, draft update,
  create a Needs-you item, GitHub comment, prepare send (`:39-47`), each only
  if the frozen policy allows it (`:1027-1080`).
- It makes **no model call** and runs **no agent**. Its only CLI calls are
  `gh` reads, and `gh pr comment` for a nudge when he presses Send
  (`:891-985`, `:1973-2098`).
- Triggers: Room "Run once" (background, the face polls,
  `steward_contract.py:209-212`; `steward/useStewardController.ts:61-82`); a
  watch rule with action `project.steward.run_once`, drained by the heartbeat
  as SCHEDULER (`workbench_conductor.py:620-636`;
  `project_steward_service.py:159-205`); MCP `project.steward.trigger`
  (`steward_contract.py:539-593`).
- Results show only in the Steward posture, the Room's nudge cards
  (`ProjectRoomCore.tsx:627-695`) and `room.steward`.
- Overlap: the steward and Workbench Reactions both read `connector_watches`
  (`workbench_conductor.py:585`, `:609-618`). Cadence loops get project
  projections separately (`project_steward_service.py:2371`). So "watch my
  sources and do something" has three engines: Reactions, the steward and
  cadence.

## 5. Watches and sources

- A watch is a `connector_watches` row with a baseline snapshot, a project
  id, a provider connection and a 60-minute default cadence
  (`schema.py:2617-2650`); rules, evaluations and effects in
  `watch_rules`, `watch_evaluations`, `watch_effects` (`:4138-4199`).
- Evaluation fetches a snapshot (GitHub, Jira, Meeting, Confluence classes,
  `holdspeak/watch_sources.py:72-715`), diffs it, writes
  `project_observations` for the project, then records effects
  (`holdspeak/services/watch_service.py:741-1010`, `:1371-1460`).
- **Only one action is ever drained**: `project.steward.run_once`
  (`project_steward_service.py:178` is the only caller of
  `list_pending_effects`). `project.observe` (every template, for example
  `holdspeak/github_templates.py:75`), `project.update.draft`,
  `project.propose`, `door.add_item`, `workbench.*` and `cadence.upsert_loop`
  make effect rows that stay pending forever (`holdspeak/watch_validation.py:57-65`).
  The observations themselves are still written, so the Room gets the data.
- Accounts: `watch_provider_connections` keeps no secrets
  (`schema.py:4118-4136`). Jira and Confluence go through `acli`, one row per
  site and email (`jira_provider.py:459-524`); GitHub through `gh`
  (`github_provider.py:7-14`, `:79`). The Accounts face is
  `web/src/pages/cores/connections/ConnectionsPane.tsx`.
- The door (`door/DoorCore.tsx:472-479`, `:301-373`) asks for a name and per
  provider toggles. `ProjectDoorService.create` marks each source
  "selected, test passed" **without running a test**
  (`holdspeak/services/project_door_service.py:274-277`), writes the project,
  watches, rules and sources in one transaction (`:287`;
  `project_service.py:3046-3065`), and links **no meetings, notes or people**.
- Layering smell: `holdspeak/mcp/families/project.py:1205`, `:1207` imports
  `holdspeak.web.routes.providers`, and `:1229-1241` imports serializers from
  `holdspeak.web.routes.steward`.
- Parked: the setup interview face, `project-room/_parked/setup/` ("retired by
  Phase 169"); its back end still runs: `project_setup_service.py` (1,602
  lines), 12 routes, 10 `project.setup.*` MCP tools.

## 6. Decisions: four stores

| Store | What writes it | Source |
|---|---|---|
| `decisions` | the meeting projection (lifecycle recorded, accepted, superseded, rejected) | `schema.py:399-418` |
| `desk_decisions` | Desk ▸ New Decision, and the meeting's Decide well | `schema.py:1114-1130`; `web/src/desk/decide.ts:65-95` |
| `decision_records` (+ sources, work, revisions) | Confirm in a meeting's Outcomes | `schema.py:1141-1189` |
| `decision_commitments` | links a decision to an action | `schema.py:239-248` |

Who reads what:

- Meeting Outcomes "Decided" joins proposals to records
  (`web/src/pages/cores/history/MeetingDetail.tsx:106-146`).
- The Room's "Decisions and owed" reads `decision_records` only through the
  meeting sources of linked meetings (`project_service.py:2270-2333`), so a
  desk decision filed to the project never shows there.
- The Room drawer reads the `decisions` table through
  `/api/decisions?project_id` (`useProjectRoomController.ts:167`): a second,
  different read.
- Today ▸ Decisions reads `/api/decisions?scope=all`
  (`desk/pullouts/views/DecisionsView.tsx:177`, `:293`), which merges stores.
- The desk "Decisions" drawer is a zone; nothing files decisions into it. The
  walk showed it empty with one confirmed and one desk decision on the desk.
- `GET /api/decisions` is declared twice; the first mount wins and the
  primitives handler is dead (`holdspeak/web/routes/decisions.py:39`,
  `holdspeak/web/routes/primitives/decisions.py:58`; mounts
  `holdspeak/web_server.py:1526` vs later).
- MCP already has `decision_record.create_from_desk` (`holdspeak/mcp/tools.py:1267-1282`),
  so a desk decision can become a record.
- The delta raises "Accepted decision is due for periodic review" for a
  decision confirmed minutes earlier
  (`holdspeak/services/project_delta_service.py:212`, `:238`, `:479`).

## 7. MCP

68 project-cluster tools in `holdspeak/mcp/families/project.py` (core 17,
items and resources 7, delivery and steward 6, setup 10, providers 13,
watches 7, suggested sources 3, connections 2) plus nudges 3, decisions 6,
follow-through 3 and door 2 (`holdspeak/mcp/tools.py:374-383`,
`:1267-1309`; `families/door.py`). Everything an agent needs to write an
update already exists as a read: `project.get_room`, `project.get_delta`,
`meeting.get`, `decision_record.list`, `people.relationship.get`,
`provider.jira_search`, `memory.page`. Missing for the design: an
"update.write" that saves an agent's text as a project update with its
sources, and a tool to add a source by URL.

## 8. Constraints for the build

- Keep every table and every MCP tool. Retire faces, not data.
- `project_updates` stays the one store of updates. An automation result for
  a project update is a `project_updates` row, not a second copy.
- Strict mode on the face is right (no silent fallback); the fix is to show
  the failure and to never block.
- One LAN slot: background memory and a draft compete for the same engine.
  The draft must not wait behind background work without saying so.
- Egress rules stay: publish prepares a send; he presses Send.

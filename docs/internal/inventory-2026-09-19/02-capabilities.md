# HoldSpeak — Capability Inventory (the machine side and the seam)

Repo `/Users/karol/dev/tools/HoldSpeak`, branch `main`. Read-only. Every count
below is measured from the tree, not read off a document.

## 0. The shape in one table

| Surface | Count | Source |
|---|---|---|
| HTTP routes served | **693** | `docs/api-surface.json` (generator `scripts/gen_api_surface.py`) |
| …called by `web/src` | **525** | consumers field |
| …called by `apple/` (iOS) | **89** | consumers field |
| …called by **nothing in the repo** | **159** (136 excluding the 19 page routes + 4 FastAPI docs routes) | consumers field |
| MCP tools registered | **225** in 20 families + a top-level catalogue | `holdspeak/mcp/tools.py`, `holdspeak/mcp/families/__init__.py:33-53` |
| CLI top-level commands | **19** | `holdspeak/main.py:81-443` |
| Services | **112** modules | `holdspeak/services/` |
| DB tables | **220** | `holdspeak/db/schema.py` |
| Background conductors started at hub boot | **4** + the heartbeat | `holdspeak/web_server.py:1260-1326` |

**FACE? is derived, not guessed.** The `consumers` field in
`docs/api-surface.json` is produced by `scripts/gen_api_surface.py`, which
extracts real call sites from `web/src` and `apple/`. Where the derivation
looked suspicious I re-grepped by hand; two corrections are flagged inline
(`/api/model-profiles`, the parked Interview/Setup face).

---

## 1. Capability inventory by domain

Legend for **FACE?**: **yes** = a live `web/src` screen calls it · **partial** =
some verbs of the capability are on a screen, others are not · **parked** = the
face exists but lives under a `_parked/` directory and is not routed ·
**no** = headless; MCP and/or HTTP and/or CLI only.

### 1.1 Meetings and capture

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Start/stop a recording | Records a meeting from the mic and writes a meeting row | `holdspeak/services/meeting_service.py:33` | `POST /api/meeting/start`, `POST /api/meeting/stop`, `POST /api/stop` | `meeting.start_capture`, `meeting.stop_capture` | `holdspeak meeting` | **yes** — LiveCore |
| Bookmark a moment mid-meeting | Drops a marker you can jump to later | `meetings/live.py` | `POST /api/bookmark` | — | — | **yes** |
| Meeting CRUD + facets | List, open, rename, delete, filter your meetings | `meeting_service.py:33` | `GET/PUT/DELETE /api/meetings[/{id}]`, `GET /api/meetings/facets` | `meeting.list`, `meeting.get`, `meeting.delete` | `holdspeak history` | **yes** |
| Import an external recording | Brings an audio file or transcript in as a meeting | `holdspeak/meeting_import.py` | `POST /api/meetings/import` | — | `holdspeak import` | **yes** |
| Recover an interrupted capture | Rebuilds a meeting whose capture died mid-flight | `meeting_service.py:33` | `POST /api/meetings/{id}/capture/recover` | — | — | **no** — server only |
| Export a meeting | Markdown/JSON export of a meeting | `holdspeak/meeting_exports.py` | `GET /api/meetings/{id}/export` | `meeting.export` | — | **yes** |
| Export to Slack | Posts the meeting summary into Slack | `holdspeak/slack_export.py` | `POST /api/meetings/{id}/export/slack` | — | — | **yes** |
| Speaker identification | Names who spoke; edit a speaker label | `holdspeak/speaker_intel.py` | `GET/PATCH /api/speakers[/{id}]` | — | — | **yes** |
| Sync-conflict resolution | Reconciles a meeting edited on two devices | `meeting_service.py:33` | `GET/POST /api/meetings/{id}/sync-conflicts[…]` | — | — | **yes** |
| Meeting candidates from activity | Suggests "this looked like a meeting, record it?" | `services/activity_meeting_candidate_service.py` | `GET/POST/DELETE /api/activity/meeting-candidates`, `/{id}/start` | — | — | **partial** — preview + status PUT server-only |
| Intent timeline / artifacts | Shows what the meeting produced, as a timeline | `holdspeak/intent_timeline.py` | `GET /api/meetings/{id}/intent-timeline`, `/artifacts` | — | — | **yes** |
| Plugin-run inspection | Shows which meeting plugins ran and what they emitted | `holdspeak/meeting_plugins.py` | `GET /api/meetings/{id}/plugin-runs` | — | — | **no** — server only |

### 1.2 Meeting intelligence

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Run intelligence on a meeting | Turns a transcript into a summary, decisions and actions | `services/meeting_intel_service.py:15` | `POST /api/meetings/{id}/intelligence/run`, `POST /api/intel/process`, `POST /api/intel/retry/{id}` | `meeting.run_intelligence` | `holdspeak intel` | **yes** — but the button *enqueues*, it does not compute (`meeting_intel_service.py:55`) |
| The intel job queue | Holds the work a finished meeting created, and drains it | `holdspeak/intel_queue.py:698`, drainer `holdspeak/intel_queue_conductor.py` | `GET /api/intel/jobs`, `GET /api/intel/summary` | — | `holdspeak intel` | **yes** (read) — the drainer itself is a conductor |
| Intel recovery | Retry or skip a meeting whose intelligence failed | `meeting_intel_service.py:15` | `GET/POST /api/meetings/{id}/intel-recovery[…]` | — | — | **yes** |
| Aftercare (follow-up draft, file an issue) | Drafts the follow-up email / files the ticket after a meeting | `services/meeting_aftercare_service.py:23` | `GET /api/meetings/{id}/aftercare`, `/followup-draft`, `/aftercare/file-issue` | — | — | **partial** — `followup-draft` server-only, `file-issue` iOS-only |
| Meeting proposals + decisions on them | Shows what the meeting proposed; you confirm or dismiss | `services/proposal_bridge_service.py:91` | `GET /api/meetings/{id}/proposals`, `POST …/{pid}/decision`, `/api/proposals/{id}/confirm|dismiss|edit` | `meeting.proposals`, `proposal.confirm`, `proposal.dismiss` | — | **yes** |
| Outcome review / accept-reviewed | Batch-accepts the meeting outcomes you agree with | `web/routes/proposals.py` | `GET /api/meetings/{id}/outcome-review`, `POST …/proposals/accept-reviewed` | — | — | **yes** |
| Action items | The to-dos a meeting produced; edit, review, transition | `meetings/action_items.py` | `PATCH /api/action-items/{id}[/edit|/review]`, `/api/all-action-items…` | — | — | **partial** — `/edit` and `/review` on both families are **server-only** (4 routes) |

### 1.3 Decisions and follow-through

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Decision records (canonical) | The durable record of what was decided and why | `services/decision_record_service.py:38` | `GET /api/decision-records[…]`, `/review`, `/search`, `/source/…`, `/work/…`, `POST …/carry` | `decision_record.*` (5), `decision.supersede` | — | **yes** |
| Dispute / supersede a record | Marks a decision contested or replaced | `decision_record_service.py:38` | `POST /api/decision-records/{id}/dispute`, `/supersede` | `decision.supersede` | — | **no** — both routes server-only (MCP has supersede) |
| Decision lifecycle (accept/reject/promote) | Accept or reject a proposed decision and promote it to an artifact | `services/decision_lifecycle_service.py:12` | `GET/POST /api/decisions/{id}[/accept|/reject|/supersede|/moment|/promote/{type}]` | — | — | **yes** |
| Decision primitives (desk objects) | Decisions as first-class desk objects you can CRUD | `web/routes/primitives/decisions.py` | `GET/POST/PUT/DELETE /api/decisions[…]` | `desk.*` generic | — | **yes** |
| Follow-through board | One board of everything you owe and are owed | `services/follow_through_service.py:20` | `GET /api/follow-through/board`, `POST /commit-decision`, `/complete` | `follow_through.*` (3) | — | **yes** |
| Monday brief | The week-opening brief assembled from your desk | `services/monday_brief_service.py:90` | `POST /api/brief/generate`, `GET /api/brief/latest`, `/shelf`, `POST /api/brief/items/{id}/shelf` | `monday_brief.generate`, `monday_brief.get` | — | **yes** |
| Needs-you aggregate | The ranked "these five things need you" list | `services/needs_you_aggregate.py:166` | `GET /api/desk/needs-you` | `desk.needs_you` | — | **yes** |

### 1.4 Projects / Rooms

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Project CRUD, archive, restore | Create and manage a Project Room | `services/project_service.py:337` | `GET/POST/PATCH/DELETE /api/projects[/{id}]`, `POST …/restore` | `project.create/get/list/update/archive/restore` | — | **partial** — `restore` server-only |
| The Door (one-screen create) | The fast path that makes a Room from one screen | `services/project_door_service.py`, `door_service.py:19` | `POST /api/projects/door`, `/door/count`, `GET /api/door` | `door.get`, `door.add_item` | — | **yes** |
| The Interview / guided setup | The multi-question wizard that builds a Room from your answers | `services/project_setup_service.py:169`, `interview_service.py:58` | 12 routes `/api/project-setups[…]` | `project.setup.*` (10), `interview.*` (4) | — | **parked** — the only caller is `web/src/features/project-room/_parked/setup/api.ts` |
| The Room view | The Room's own screen with its resources and reads | `project_service.py:337` | `GET /api/projects/{id}/room`, `POST …/room/read` | `project.get_room` | — | **yes** |
| Project items / backlog | Work items on a Project, with transitions | `project_service.py:337` | `GET/POST/PATCH /api/projects/{id}/items[…]`, `/transition` | — | — | **no** — all 4 routes server-only |
| Project resources (link/unlink) | Attaches a repo, ticket, doc to a Project | `project_service.py:337` | `GET/PUT/DELETE /api/projects/{id}/resources[…]` | `project.link`, `project.unlink` | — | **partial** — list is on a face, PUT/DELETE server-only |
| Meeting↔Project linking | Says which meetings belong to this Project | `project_service.py:337` | `GET/POST/DELETE /api/projects/{id}/meetings[…]`, `GET /api/meetings/{id}/projects` | — | — | **partial** — list only; link/unlink server-only |
| Suggested sources | Proposes connectors/repos worth watching for this Project | `services/project_doc_suggestions.py`, `project_service.py:337` | `GET /api/projects/{id}/suggested-sources`, `/add`, `/dismiss` | `project.suggested_sources`, `project.add_suggested_source`, `project.dismiss_suggested_source` | — | **yes** |
| Project delta + review | "What changed since you last looked", and a review over it | `services/project_delta_service.py:216` | `GET /api/projects/{id}/delta`, `POST /reviews`, `…/accept`, `…/proposals/{id}/decide` | `project.get_delta`, `project.open_review`, `project.accept_review`, `project.decide_proposal` | — | **partial** — `GET …/reviews/{id}` server-only |
| Project updates (draft → publish) | Drafts a status update from observations and publishes it | `services/project_update_service.py:178` | `GET/POST /api/projects/{id}/updates[…]`, `PUT/POST /api/updates/{id}[/publish|/regenerate]`, `GET …/markdown` | `project.draft_update`, `project.update_draft`, `project.publish_update`, `project.list_updates` | — | **yes** |
| **Claim review on an update** | Accept or reject an individual claim inside an update | `services/project_update_service.py:2026` | **none** | **none** | **none** | **DEAD** — `review_claim` is defined and called by nothing |
| Preparation brief | Prepares you for a meeting/1:1 from the Project's material | `services/preparation_brief_service.py:147` | `GET /api/briefs/{id}`, `POST /keep`, `/discard`; `GET/POST /api/projects/{id}/briefs[…]` | — | — | **partial** — 5 of 8 routes server-only |
| Since-last-meeting | "Here is what happened since we last met" | `project_service.py:337` | `GET /api/projects/{id}/since-last-meeting` | — | — | **yes** |
| Project summary / briefings / action items | Rolled-up views of a Project | `project_service.py:337` | `GET /api/projects/{id}/summary`, `/briefings`, `/action-items` | — | — | **no** — all three server-only |

### 1.5 Watches, steward, automations

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Create a connector watch | "Tell me when this repo/ticket/space changes" | `services/watch_service.py:266` | `POST /api/automations/watches`, `GET /api/projects/{id}/watches` | `watch.create`, `watch.list`, `project.watch.set_rules` | — | **yes** |
| Evaluate a watch (manual) | Checks a watch right now | `watch_service.py:266` | `POST /api/watches/{id}/evaluate` | `project.watch.evaluate` | — | **no** — route server-only; MCP-reachable |
| Pause / resume / retire a watch | Turns a watch off without losing it | `watch_service.py:266` | `POST /api/watches/{id}/pause|/resume|/retire` | `project.watch.pause/resume/retire` | — | **yes** |
| Watch rules / baseline / test | Edits the match rules, resets the baseline, dry-runs it | `holdspeak/watch_condition_matcher.py`, `watch_validation.py` | `PUT /api/watches/{id}/rules`, `POST /baseline`, `/test`; `GET /api/watches` | `project.watch.set_rules`, `project.watch.test`, `project.watch.inspect` | — | **no** — all four server-only; MCP-reachable |
| Reactions (event → action) | "When X happens, do Y" | `services/reaction_service.py:197` | `GET/POST /api/automations/reactions`, `POST /process`, `PUT /{id}/enabled` | `reaction.*` (5) | — | **partial** — create/list on a face; process + enable server-only |
| Steward policy per Project | Decides what the steward may do unattended on this Project | `services/project_steward_service.py:67` | `GET/PUT /api/projects/{id}/steward/policy` | `project.configure_steward` | — | **yes** |
| Run the steward (manual) | Sweeps a Project now and produces a run record | `project_steward_service.py:67` | `POST /api/projects/{id}/steward/runs`, `GET /api/steward/runs/{id}`, `POST /stop` | `project.run_steward`, `project.get_steward_run`, `project.stop_steward` | — | **yes** |
| Steward trigger (scheduled path) | The seam the unattended sweep would call | `project_steward_service.py:67` | `POST /api/steward/trigger` | `project.steward.trigger` | — | **yes**, but returns a **soft refusal** `{"success": false, "code": "scheduler_not_wired"}` with `isError: false` |
| Steward nudges | "Chase this person about this" suggestions | `services/activity_nudge_service.py` | `GET /api/projects/{id}/nudges`, `POST /api/nudges/{id}/send|/dismiss` | `steward.nudges`, `nudge.send`, `nudge.dismiss` | — | **yes** |
| Workbench automations | Per-workbench triggers with history and a test run | `holdspeak/workbench_conductor.py` | 7 routes under `/api/workbenches/{id}/automations`, `/resourceful` | — | — | **yes** |
| Practice recipes | Named repeatable practices the product can run | `services/practice_recipe_*` / `holdspeak/mcp/families/practice_recipe.py` | `GET /api/automations/practice-recipes[/{id}[/plan]]` | `practice_recipe.list/get/compile` | — | **partial** — list on a face; get + plan server-only |
| Scheduled recording | Records a meeting on a cron or from a calendar event | `services/scheduled_recording_service.py:143` | 6 routes `/api/scheduled-recordings[…]` | `scheduled_recording.*` (5) | — | **yes** |

### 1.6 Calendar and people

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Calendar sources + snapshot | Reads your calendars and previews what it found | `services/calendar_snapshot_service.py`, `holdspeak/calendar_ingest.py` | `GET /api/calendar/sources`, `POST /api/calendar/snapshot[/confirm]` | — | — | **yes** |
| Calendar events + linking | Shows events; links one to a meeting or a person | `holdspeak/calendar_ingest.py` | `GET /api/calendar/events`, `POST/DELETE /api/calendar/events/{id}/link` | `people.calendar_link`, `people.calendar_unlink` | — | **yes** |
| People relationships | The people you work with, as records | `services/people_service.py:16` | 26 routes under `/api/people` — **all 26 web-consumed** | `people.*` (17) | — | **yes** |
| 1:1 sessions + agenda + brief | Runs a 1:1 loop with an agenda and a prepared brief | `people_service.py:16` | `GET/POST /api/people/relationships/{id}/one-on-ones`, `/agenda`, `/brief` | `people.one_on_one_create`, `people.one_on_one_brief`, `people.agenda_add` | — | **yes** |
| Commitments | What a person owes you and you owe them | `people_service.py:16` | `/api/people/commitments/{id}/satisfy|/transition|/execution|/workbench` | `people.commitment_transition` | — | **yes** |
| Person resolution + aliases | Decides who "Karol" means, and links your own aliases | `services/person_overlay.py`, `people_service.py:16` | `POST /api/people/resolve`, `…/owner-aliases` | `people.resolve`, `people.owner_alias_link/unlink` | — | **yes** |
| People readiness | Says whether the People ledger is usable yet | `people_service.py:16` | `GET /api/people/readiness` | `people.readiness` | — | **yes** |

### 1.7 Dictation and voice

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Push-to-talk dictation → typed text | Speak, and the text lands in the focused app | `holdspeak/dictation_runner.py`, `desktop_typing.py` | `POST /api/dictation/transcribe`, `/preview/type`, `/preview/discard`, `/wake/type` | — | `holdspeak dictation` | **yes** (+ a global hotkey, `holdspeak/hotkey.py`) |
| Streaming dictation | Live partials over a socket | `holdspeak/speech_session/` | `WS /ws/dictation/stream` | — | — | **yes** |
| Mic ownership / floor | Stops two things fighting over the microphone | `holdspeak/services/dictation_service.py:17` | `GET/POST /api/dictation/floor[/claim|/release]`, `POST /api/dictation/mic/open|close` | — | — | **yes** |
| Dictation journal | Everything you dictated, editable and replayable | `holdspeak/dictation_telemetry.py` | `GET/DELETE/PUT /api/dictation/journal[…]`, `/correct`, `/replay` | — | — | **yes** |
| Corrections | Teaches it a word it keeps getting wrong | `holdspeak/dictation_learning.py` | `GET/POST/DELETE /api/dictation/corrections[…]` | — | — | **yes** (the owner has disowned this loop as a use case) |
| Blocks (dictation macros) | Named blocks of dictation behaviour you can compose | `holdspeak/dictation_selection.py` | 6 routes `/api/dictation/blocks[…]` | — | `holdspeak dictation blocks` | **yes** |
| Intent routing (control/override/profile) | Decides whether what you said was text or a command | `holdspeak/services/…` + `web/routes/dictation/intents.py` | `GET /api/intents/control`, `POST /preview`, `PUT /override`, `PUT /profile` | — | — | **partial** — `control`, `preview`, `profile` on LiveCore; `PUT /override` has **no caller** |
| Project KB for dictation | Vocabulary the dictation engine should know about | `web/routes/dictation/kb.py` | `GET/PUT/DELETE /api/dictation/project-kb`, `POST /starter` | `kb.*` (3) | — | **yes** |
| Agent context / hooks | Feeds what you are doing into the dictation context | `holdspeak/agent_context/` | `GET /api/dictation/agent-context`, `/agent-hooks`, `/project-context` | — | `holdspeak agent-hook` | **partial** — `clear` + `summarize` server-only |
| Project doc suggestions | Proposes an edit to your project doc from what you said | `holdspeak/project_doc_suggestions.py` | `GET /api/dictation/project-doc-suggestion`, `POST /apply`, `/dismiss` | — | — | **partial** — apply + dismiss server-only (the read is on a face; you cannot act on it) |
| Remote dictation | Dictate from the phone into the desk | `web/routes/dictation/pipeline.py` | `POST /api/dictation/remote` | — | — | **yes** |
| Learning digest + readiness | "Here is what dictation learned / is it ready" | `dictation_learning.py` | `GET /api/dictation/learning-digest`, `/readiness` | — | — | **yes** |
| Wake word | Hands-free trigger | `holdspeak/wake_word.py` | `POST /api/dictation/wake/type` | — | — | **yes** |
| Text-to-speech | Reads something back to you | `web/routes/tts.py` | `POST /api/tts`, `/download`, `GET /status` | — | — | **yes** |

### 1.8 Desk primitives (thoughts, notes, workbenches, recipes, chains, workflows)

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Thoughts + refinement loop | A thought you refine with the model, with reviews you answer | `web/routes/primitives/thoughts.py` | 20 routes — **all 20 web-consumed** | `thought.*` (18) | — | **yes** |
| Notes | Plain desk notes | `web/routes/primitives/notes.py` | 5 routes | — | — | **yes** |
| Workbenches | A working surface with items, memory and runs | `services/workbench_runner.py:23` | 22 routes | `workbench.*` (10) | — | **partial** — run-cancel server-only |
| Skills library | Reusable skills a workbench can call | `holdspeak/skills_library/` | `GET/POST/PUT/DELETE /api/skills[…]` | — | — | **yes** |
| Workbench templates | Start a workbench from a template | `holdspeak/workbench_templates.py` | `GET /api/workbench-templates`, `POST …/instantiate` | — | — | **yes** |
| Recipes (agent personas) | A named persona you can run or chat with | `web/routes/primitives/recipes.py` | 9 routes | `recipe.list/get/run/chat` | — | **partial** — `POST …/chat` and run-cancel server-only (MCP has chat) |
| Chains | A sequence of primitive runs | `web/routes/primitives/chains.py` | 7 routes | `sequence.run`, `sequence.cancel` | — | **partial** — run-cancel server-only |
| Workflows | Another sequence-of-steps runner | `web/routes/primitives/workflows.py` | 7 routes | `workflow.run`, `workflow.cancel` | — | **partial** — run-cancel server-only |
| Ask | One-shot question against a model with grounding | `services/ask_service.py:35` | `POST /api/ask`, `/keep`, `/{id}/cancel`, `POST /api/grounding/resolve`, `GET /api/models` | `ask.run/keep/cancel/resolve_grounding` | — | **partial** — cancel server-only |
| Ask tasks (long-running) | A background ask you can resume or discard | `project_service.py:337` | `GET /api/ask-tasks`, `POST /{id}/discard|/resume|/stopped`, `POST /api/projects/{id}/ask-tasks` | — | — | **yes** |
| Invocations ledger | Every model call, with its receipt | `services/invocation_service.py` | `GET /api/invocations[/{id}]`, `POST /{id}/cancel` | `pipeline.events` | — | **partial** — cancel server-only |
| Directories | Groups of primitives | `web/routes/primitives/directories.py` | 8 routes | `zone.file/unfile/list_members` | — | **partial** — `GET …/members` server-only |
| Knowledge bases | Named collections of resources | `web/routes/primitives/kbs.py` | 8 routes | `kb.*` (3) | — | **partial** — `GET …/members` server-only |
| Memory recall + search | Finds what you said/decided before | `services/memory_service.py:13`, `recall_service.py:118` | `GET /api/memory/recall`, `/search` | `memory.search` | `holdspeak memory rebuild-index` | **yes** |
| Threads (desk chat) | The chat thread on the desk, with branch/compact/keep | `services/thread_service.py:86` | 18 routes | **`thread.set_status` only (1 of ~18 verbs)** | — | **yes** |
| Thread → interview promotion | Turns a chat into interview facts you promote | `web/routes/threads.py:55-64` | `POST /api/threads/{id}/interview`, `GET …/interview/promotions` | — | — | **partial** — the read is server-only and no face emits `promote`/`revoke_promotion` |
| Desk snapshot / projections / seed | The desk's stored objects, its presentation, a demo seed | `services/desk_service.py:13` | `GET /api/desk/projections`, `PUT …/presentation`, `POST /api/desk/seed`, `/reset` | `desk.snapshot`, `desk.list/get/create/update/delete`, `desk.verb` | `holdspeak seed` | **yes** |
| **`desk.verb` dispatch** | Drive a desk verb from outside the browser | `holdspeak/mcp/tools.py:1016` | — | `desk.verb` | — | **effectively DEAD** — 5 dispatchable lambdas, none of which is an id in `web/src/desk/verbRegistry.ts`; everything else returns `{"status": "ui_only"}` |

### 1.9 Connectors and providers

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Connections list + recheck | "Are my GitHub/Jira/Confluence connections alive?" | `services/connections_service.py:90` | `GET /api/connections`, `POST /{provider}/recheck` | `connection.list`, `connection.recheck` | — | **yes** |
| Provider catalogue | Which providers exist at all | `web/routes/providers.py` | `GET /api/providers` | `provider.list` | — | **yes** |
| GitHub provider (discover/validate/connection) | Finds your repos and checks one is reachable | `services/github_provider.py` | 4 routes | `provider.github.*` (3) | — | **parked** — only `_parked/setup/api.ts` calls them; MCP-reachable |
| Jira provider (multi-account) | Finds your Jira sites/projects, searches, validates scope | `services/jira_provider.py` | 6 routes | `provider.jira.*` (6) | — | **partial** — `connections` GET/POST on a face; discover/search/validate/recheck server-only |
| Confluence provider | Finds your spaces and validates one | `services/confluence_provider.py` | 4 routes | `provider.confluence.*` (3) | — | **no** — all four server-only; MCP-reachable |
| Repository working tree | Browse, read, stage, commit inside a linked repo | `web/routes/repositories.py` | 10 routes | **none** | — | **partial** — `web/src/desk/repository.ts` calls list+create; the 8 tree/file/stage/commit/checkout routes have **no caller anywhere** |
| Activity enrichment (GitHub/Jira pipelines) | Annotates your activity ledger from connectors | `services/activity_enrichment_service.py` | 14 routes | **none** | — | **partial** — 4 on ActivityCore, **10 server-only, no MCP twin** |
| Activity ledger + domains + rules | Tracks what you worked on and maps it to projects | `services/activity_ledger_service.py:11`, `activity_rules_service.py` | 13 routes | **none** | — | **yes** (12 of 13) |
| Activity nudges | "You've been in this repo an hour, want a Project?" | `services/activity_nudge_service.py` | 4 routes | `nudge.send`, `nudge.dismiss` | — | **partial** — `dismiss` is iOS-only, `select/clear` server-only |
| Browser-extension event intake | The extension posts what you are browsing | `holdspeak/activity_extension.py` | `POST /api/activity/extension/events` | — | — | **no** — the caller is `extensions/`, outside the generator's scan |

### 1.10 Inference, models, setup

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Inference assignments | Says which model does which job | `services/inference_assignment_service.py:90` | 5 routes `/api/inference/assignments[…]` | `inference_assignment.*` (5) | — | **yes** |
| Model library | The models you own, hosted or local | `services/model_library_service.py:65` | 7 routes `/api/inference/model-library[…]` | `model_library.*` (7) | — | **partial** — `connect-paired-device` server-only |
| Concierge (detect → propose → download → apply) | Walks you from "no models" to "a working engine" | `services/concierge_service.py` | 5 routes `/api/concierge/*` | `concierge.*` (5) | — | **yes** |
| Inference targets / profiles | Raw endpoint records with secrets | `web/routes/primitives/profiles.py`, `services/profile_service.py` | 11 routes | — | — | **partial** — probe + secret PUT/DELETE + `POST /api/profiles` server-only |
| **Model profiles** (a *second* profile concept) | A named model config with bindings, probes and revisions | `services/model_profile_service.py:205` | 8 routes `/api/model-profiles[…]` | **none** | — | **DEAD face** — zero hits for `model-profiles` anywhere in `web/src` or `apple/` (the generator's two "web" marks are substring false positives). The service **is** read by `inference_route_plan_service.py:142` and `inference_adoption_service.py:2302`, so the concept is live in the engine and unreachable by hand |
| Capabilities catalogue | The abstract jobs a model can be assigned to | `services/inference_capability_service.py` | `GET /api/inference/capabilities[/{id}]` | — | — | **partial** — the per-id route is server-only |
| Model acquisition jobs | Downloads a model and reports progress | `services/inference_acquisition_service.py` | `GET /api/inference/acquisitions/{id}`, `POST /cancel` | `inference.cancel_model_acquisition` | — | **no** — both server-only; MCP has cancel only |
| First-value / onboarding walk | The guided first run | `holdspeak/setup_runtime.py`, `setup_status.py` | `POST /api/setup/first-value/*`, `PUT /api/setup/onboarding`, `GET /api/setup/status` | — | — | **yes** |
| Runtime options + test | Pick and prove a local runtime | `setup_runtime.py` | `GET /api/setup/runtime-options`, `POST /runtime-test`, `POST /discover-models`, `GET /hub-default-summary` | — | — | **yes** |
| Front door (topology + recommendation + apply) | "Here is how your setup looks and what to do next" | `services/front_door_service.py` | 4 routes `/api/front-door/*` | — | — | **yes** |

### 1.11 Cadence, heartbeat, attention

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Cadence loops | Open loops with people, chased on a cadence | `services/cadence_service.py:20` | 13 routes `/api/cadence/*` | `cadence.*` (11) | `holdspeak cadence {status,loops,run-now,brief,closeout,audit}` | **partial** — `POST /api/cadence/closeout/apply` server-only |
| Heartbeat | The unattended sweep that evaluates watches and notifies | `services/heartbeat_service.py:98` | `GET/PUT /api/settings/heartbeat`, `POST /run-now` | `heartbeat.status/set/run_now/notify_test` | — | **yes** — Settings |
| Desktop notification | The OS notification the heartbeat sends | `holdspeak/desktop_notify.py` | — | `heartbeat.notify_test` | — | **no** direct face; configured via heartbeat settings |

### 1.12 Authority, gate, kernel, remoteness

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Control mode + policy | The master "how much may it do on its own" dial | `services/authority_service.py:14` | `PUT /api/authority/control-mode`, `GET /api/authority/policy`, `POST /evaluate` | **none** | `holdspeak control-mode` | **yes** |
| Grants | Scoped permissions you hand out | `authority_service.py:14` | `GET/POST /api/authority/grants`, `DELETE /{id}`, `GET /{id}/uses` | **none** | — | **partial** — delete + uses server-only; **no MCP tool touches authority at all** |
| Coder gate (Claude Code PreToolUse) | Holds an agent's tool calls for your decision | `services/gate_service.py:14` | 12 routes `/api/gate/*`, `/api/principals/*`, `/api/sessions/{key}/receipt` | **none** | `holdspeak gate {hook,install,arm,disarm,allow,revoke,status}` | **partial** — 3 routes server-only |
| Kernel broker (submit/read/decide/events) | The ledger every privileged effect passes through | `holdspeak/kernel/` | 7 routes `/api/kernel/*` | **none** | — | **partial** — `submit`, `read`, `events` on the desk; the 4 executor/decide routes server-only |
| Actuators (GitHub/Slack/webhook propose→decide) | Lets it act outside, with your confirmation | `services/actuator_service.py` | 7 routes `/api/desk/actuators/*` | **none** | — | **yes** |
| Remote MCP (Reach) | Drives HoldSpeak from another machine over MCP | `holdspeak/web/routes/mcp_http.py` | `POST /api/mcp`, `GET/PUT /api/settings/remote`, credentials CRUD | (the transport for all 225) | — | **partial** — the settings face exists; `POST /api/mcp` has no in-repo caller |
| Secrets | Stores and rotates API keys | `services/credential_service.py` | `PUT/DELETE /api/settings/secrets/{id}`, `POST /rotate` | **none** (deliberate refusal) | — | **yes** |
| Mesh / device pairing | Pairs a phone or second device | `holdspeak/mesh.py`, `services/mesh_service.py` | 5 `/api/mesh/*`, `GET/POST /api/sync/*` | — | `holdspeak mesh serve`, `holdspeak device-psk` | **partial** — relay claim/complete/fail are iOS-only |

### 1.13 Delivery / coding agents

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Coder sessions (list/select/pin/kill) | Sees and manages the coding agents you spawned | `services/coder_service.py:14` | 6 `/api/coders/*` | `coder.list/get/audit` | — | **yes** |
| Coder steering (arm/steer/peek/keys) | Sends keystrokes and instructions into a live agent pane | `holdspeak/coder_steering.py`, `coder_steering_relay.py` | 16 routes | **none** — classified as a **defect to repair (HS-200-28)**, not a refusal | — | **yes** |
| Coder factory (spawn/rename) | Starts a new coding agent | `holdspeak/coder_factory.py` | 2 routes | — | — | **yes** |
| Delivery snapshot / sources / attempts | Tracks what's shipping | `services/delivery_service.py:13` | 6 routes | — | — | **yes** |
| Delivery PRs | Fetch, diff, draft a review, propose, send to an agent | `holdspeak/delivery/` | 9 routes | — | — | **partial** — `launches/{id}/input` server-only |
| Delivery nodes + terminal | Links a second machine and runs commands on it | `holdspeak/commands/node_serve.py` | 10 routes | — | `holdspeak node serve|token|pair` | **partial** — 7 routes are the *node's own* client calls, not a face |
| Delivery dossiers / evidence | The evidence bundle behind a story or phase | `holdspeak/delivery/` | 3 routes | — | — | **partial** — story dossier is iOS-only |
| Mission control | The rails view over agent sessions and receipts | `services/mission_control_service.py` | 10 routes | — | — | **partial** — `rails/remote-events` server-only |
| Roadmaps (Delivery Workbench read) | Reads the `pm/roadmap` tree | `web/routes/roadmaps.py` | 4 routes | — | — | **yes** |
| Plugin jobs | The background job queue for meeting plugins | `services/plugin_job_service.py:12` | 5 routes | `plugin_job.*` (4) | — | **partial** — cancel + retry-now server-only (MCP has both) |

### 1.14 Settings and system

| Capability | What it does for the user | Owner | HTTP | MCP | CLI | FACE? |
|---|---|---|---|---|---|---|
| Settings read/write | Everything configurable | `services/settings_service.py:214` | `GET/PUT /api/settings`, `GET /api/settings/hub` | `settings.get`, `settings.update`, `settings.hub` | — | **yes** |
| Constitutional context | The owner's standing instructions given to every model call | `holdspeak/constitutional_context.py` | `GET/PUT /api/constitutional-context`, `/history` | — | — | **yes** |
| Doctor | "Is my install healthy?" | `holdspeak/doctor.py` | — | — | `holdspeak doctor` | **no** — CLI only |
| Backup / restore | Snapshots the database | `holdspeak/commands/backup.py` | — | — | `holdspeak backup`, `holdspeak restore` | **no** — CLI only |
| Runtime status / identity / device health | "Is the hub alive, which process owns the DB" | `holdspeak/runtime_identity.py`, `runtime_lock.py` | `GET /api/runtime/status`, `/api/system/identity`, `/api/devices/health`, `/health` | — | — | **yes** |
| Agent capabilities | What the agent surface can do | `holdspeak/agent_capabilities.py` | `GET /api/agents/capabilities` | — | — | **yes** |
| Live bus | Pushes status frames to the open desk | `holdspeak/realtime_frames.py` | `WS /ws`, `WS /api/devices/audio` | — | — | **yes** |
| Events query | "What has happened on my desk" | `services/event_query_service.py` | `GET /api/automations/events`, `/api/kernel/events` | `event.list` | — | **yes** |

---

## 2. Counts and reconciliation with the 2026-09-13 audit

### 2.1 Totals

| Measure | Count |
|---|---|
| Capabilities inventoried above | **~118** |
| …with a live web face (`yes`) | **62** |
| …`partial` (some verbs faceless) | **38** |
| …`no` face — reachable only by MCP, CLI, another machine, or raw HTTP | **15** |
| …**parked** (face exists, not routed) | **2** (the Interview/Setup wizard; the GitHub provider discovery it drives) |
| …**dead** — no face, no MCP, no CLI, no scheduler, no client | **3** |
| MCP-only capabilities (no face at all, MCP is the only hand) | Watch rules/baseline/test, watch manual evaluation, Confluence provider, GitHub provider discovery, project setup/interview, acquisition cancel — **6** |
| CLI-only capabilities | doctor, backup, restore, memory index rebuild, device-psk, mesh serve, node serve, agent-hook install — **8** |
| Routes with no in-repo caller | **136** (excluding 19 page + 4 docs routes) |

**The three genuinely dead capabilities:**

| Capability | Evidence |
|---|---|
| **Claim review on a project update** | `project_update_service.py:2026` `review_claim` — the only occurrence of the name in the whole tree is its own definition. No route, no MCP tool, no CLI. Every claim is permanently `unreviewed`. Unchanged since the audit (§10.6). |
| **Model profiles CRUD** | `/api/model-profiles` × 8 routes; zero hits for `model-profiles` in `web/src` or `apple/`; no MCP tool. The *service* is live (read by the route planner), the *hand* does not exist. |
| **Repository working-tree operations** | 8 of 10 `/api/repositories/{id}/…` routes (tree, file read/write, stage, commit, checkout, branches, status) — `web/src/desk/repository.ts` calls only the list and create routes. No MCP twin. |

Near-dead, worth naming separately: **`desk.verb`** is alive as a tool and dead as
a capability — its five dispatchable verbs have an **empty intersection** with
`web/src/desk/verbRegistry.ts` (`holdspeak/mcp/tools.py:1016`), so no UI verb is
drivable from outside the tab. HS-200-46 re-measured the drift as **22 missing
catalog verbs and zero phantoms**, correcting the audit's 20/13.

### 2.2 What the audit found · what is fixed · what still stands

| # | Audit finding (2026-09-13) | Status today | Evidence |
|---|---|---|---|
| §3.1 / P0 | Nothing drains the intel queue | **FIXED** (HS-200-42) | `holdspeak/intel_queue_conductor.py`, started at `holdspeak/web_server.py:1319-1322`, stopped at `:1343`, ownership-gated; `meeting_intel_service.py:95-100` wakes it |
| §3.2 / P0 | Nothing ever arms a watch | **FIXED** (HS-200-43) | `next_evaluation_at` now written outside `evaluate_due` at `project_service.py:2572`, `watch_service.py:118` (`arm_watch`) and `:1564`; ungated reconcile backfill |
| §3.3 / P1 | Manual evaluation records no effects | **FIXED** (HS-200-43) | effects minted under the scheduled idempotency key from both paths |
| §10.1 / P0 | MCP sidecar is a second unlocked writer on the live DB | **FIXED** (HS-200-45) | one composition root `holdspeak/runtime/composition.py`; the stdio sidecar is now a **client of the hub through `/api/mcp`** and never opens the database; WAL + `busy_timeout` on. *(`.mcp.json` still has no `env` block — now harmless, because the sidecar no longer opens the file.)* |
| §10.4 / P1 | UX-canon guard sees 5% of its violations | **FIXED** (HS-200-44) | whole-file matching; the real number is **175 in scope / 203 repo-wide**, not 187 |
| §10.7 / P2 | Two schedulers on one row, only one checks quiet hours | **FIXED** (HS-200-43) | the workbench conductor's watch block deleted; the heartbeat is the single scheduler; quiet hours hold the whole sweep |
| §5 | 13 false documentation sentences | **FIXED as a mechanism** (HS-200-46) | `tests/unit/doc_claims/registry.py` — executable predicates, `known_false` ratchet at 7→5 |
| §10.6 / P1 | `review_claim` unreachable | **STILL OPEN** | single definition, no caller |
| §10.8 / P2 | `promote` / `revoke_promotion` reachable from no shipped caller | **STILL OPEN (half)** | the routes exist (`web/routes/threads.py:55-64`) but nothing in `web/src` emits either verb |
| §10.9 / P2 | `project.steward.trigger` soft-refuses with `isError: false` | **STILL OPEN** | `POST /api/steward/trigger` still returns `{"success": false, "code": "scheduler_not_wired"}` |
| §10.10 / P3 | `jsonschema` imported at module scope, declared only in extras | **STILL OPEN** | `pyproject.toml:82` (test extra), `:141` — not in `[project.dependencies]` |
| §9.1 | `bind_host` is decorative | **STILL OPEN** | `web/routes/mcp_http.py:262-263` — stored into a dict, applied by nothing; no CIDR check anywhere |
| §9.2 | Reach enable flag is in-memory, dies on restart | **STILL OPEN** | `request.app.state._remote_settings`, `mcp_http.py:204, 254-258` — a plain dict, no config field, no boot initializer |
| §9.3 | `DESK` palette resolves to all tools, identical to `ALL` | **STILL OPEN** | `holdspeak/mcp/palettes.py` — `_lazy_desk_tools()` and `_lazy_all_tools()` both `from holdspeak.mcp.tools import TOOLS` |
| §8 | `desk.verb` is a catalog of refusals | **STILL OPEN** | `tools.py:1016-1017` |
| §7 | No server-side screen state; no layout in `desk_snapshot` | **STILL OPEN, by policy** | `holdspeak/db/primitives.py:1073`; HS-200-45's status line says "the X11 wire face wants its own phase" |
| §2 flow 3 | Interview face parked | **STILL PARKED** | the only caller of the 12 `/api/project-setups` routes is `web/src/features/project-room/_parked/setup/api.ts` |

### 2.3 What the audit did **not** find, and has since been measured

Chartered 2026-09-18 out of a second clock measurement
(`pm/roadmap/holdspeak/phase-200-the-working-practice/current-phase-status.md:3`),
**all seven still `backlog`**:

| Story | Defect |
|---|---|
| HS-200-47 | `cron_is_due` reads a naive `datetime.now()` (`holdspeak/cron.py:45`) and no row stores a zone — a workbench schedule silently follows the hub's clock across DST. `ScheduledRecordingService` one module away does it correctly (`scheduled_recording_service.py:177, 235-240, 289`). |
| HS-200-48 | The schedule delegation resolves `recipe_id` against `recipes` (the agent-persona table) and raises `delegation_stale_work` without one (`schedule_delegation.py:17-19`) — a **practice recipe cannot be minted as scheduled work at all**. |
| HS-200-49 | `workbenches` has no `project_id`, so a scheduled run has no Project and no source scope. |
| HS-200-50 | A due occurrence drives free-text `workbench_items` through the inference waist at `capability_id="workbench.item"`; nothing dispatches to the services a recipe declares. |
| HS-200-51 | A run produces a `result` string, not a kept brief / current decision / editable update. |
| HS-200-52 | `ReactionService.create_watch` mints `state=''` (`reaction_service.py:229`), which `arm_watch` refuses (`watch_service.py:115`) and `list_due_watches` excludes (`db/automations.py:457-458`). **Neither the automations route nor the MCP verb can create a watch the scheduler will ever select** — the only armable connector mint is inside `ProjectService.create_from_setup`, i.e. behind the **parked** Interview. This is HS-200-43's fix leaking: the watch is armable in principle and unarmable from every shipped surface but one. |
| HS-200-53 | No occurrence has ever fired on the real clock. `kernel_schedule_ticks` empty on the owner's desk. |

**And a correction to the audit's own model of Cadence:** the product's tick calls
Cadence *"attention only, never schedule"* (`holdspeak/workbench_conductor.py:630`).
Stories 21, 33, 34, 35 were amended because they had named Cadence as a scheduler seam.

---

## 3. Background machinery — what runs on its own

Two separate start surfaces: **runtime threads** (`holdspeak/web_runtime.py:529-535`,
via `runtime/ownership.py:124` `_start_scheduled_work`) and **app-lifespan
conductors** (`holdspeak/web_server.py:1264-1325`).

### 3.1 The loops

| Loop | Defined / started | Trigger | Interval (configured where) | Writes | Default | How the user knows it ran |
|---|---|---|---|---|---|---|
| **Heartbeat sweep** | `runtime/heartbeat.py:78` / started `runtime/ownership.py:145` | boot + timer | thread ticks **60 s** (hardcoded `runtime/heartbeat.py:86`); sweep due every `sweep_every_minutes`, **default 15** (`heartbeat_service.py:38`), stored in `cadence_policies`, edited at `PUT /api/settings/heartbeat` | watch `last/next_evaluation_at`, watch events, `heartbeat.notify` + `calendar.refresh` receipts, desktop notification | **ON**, **no kill switch** | desktop notification when `notify != off` (default `edge`) + last/next sweep on the Rhythm screen |
| **Connector watch evaluation** | `watch_service.py:1003` `evaluate_due` / called only from `runtime/heartbeat.py:139` | rides the heartbeat | per-watch `evaluation_cadence_minutes`, default **60** (`watch_service.py:1094`); **max 10 watches per sweep** (`WATCH_SWEEP_MAX`, `:86`); breaker 3 failures / 900 s (`:62-63`) | `connector_watches`, watch events, pending effects | ON per watch | events on the Automations surface; **excess watches are silently deferred** |
| **Deferred plugin job queue** | `runtime/plugin_queue.py:120` / `web_runtime.py:529-534` | boot + tight poll | **0.6 s** hardcoded (`runtime/plugin_queue.py:125`) | `plugin_run_jobs`, plugin outputs, `runtime_queue` frame | **ON, no setting at all**, and **not ownership-gated** | queue HUD frame only |
| **Intel queue drainer** (HS-200-42) | `intel_queue.py:776` / `web_server.py:1322` | boot + timer + `wake()` on enqueue | **15 s** (`intel_queue_conductor.py:50`), floor 5 s; retries from `meeting.intel_retry_*` | `intel_jobs`, intelligence rows; broadcasts `aftercare_ready`, `runtime_queue` | ON when this process owns the DB (`intel_queue_conductor.py:72`) | `aftercare_ready` frame + drainer badge on `web/src/desk/chair/ChairHome.tsx:441` |
| **Workbench conductor (a 4-in-1 tick)** | `workbench_conductor.py:524` / `web_server.py:1274` | boot + timer | **60 s** hardcoded (`workbench_conductor.py:530`) | workbench cron runs, **plus** reactions (`:576-581`), resourceful idle (`:593`), steward `run_due` (`:622`), cadence projections (`:632`) | **ON unconditionally, not ownership-gated** | run rows + a log line; the three sub-ticks log only |
| ↳ legacy watch refresh (Reactions) | `reaction_service.py:355` / `workbench_conductor.py:578` | timer | `refresh_interval_minutes` in the watch query JSON, default **35** (`reaction_service.py:31`) | watch snapshots, automation events | ON per legacy watch (`state == ''`) | **log only** |
| ↳ reaction projection | `reaction_service.py:523` / `:581` | timer | 60 s | workbench items | ON | rows appear |
| ↳ resourceful idle tick | `services/resourceful_service.py:264` / `:593` | timer | 60 s | idle-policy ledger events | ON per policy row | **log only** |
| ↳ project steward `run_due` | `project_steward_service.py:141` / `:622` | timer + pending `project.steward.run_once` effects | 60 s tick; per-project `cooldown_seconds` | steward runs, deltas, effects | **OFF** — `unattended_enabled` written `0` by default (`web/routes/steward.py:326`) | steward run rows / StewardPosture in the Room |
| **Scheduled recording conductor** | `scheduled_recording_conductor.py:155` / `web_server.py:1298` | boot + timer | **60 s** (`:100`); 10 s arming countdown (`:35`); 1 h missed-catchup (`:38`); per-schedule cron | `scheduled_recordings.next_fire_at`; **starts and stops real meetings** | ON; per-row `enabled` | a meeting actually starts + a countdown broadcast |
| **Calendar refresh** | `calendar_ingest_conductor.py:237` `refresh()` | boot (sync) + heartbeat | effectively the heartbeat's 15 min (`runtime/heartbeat.py:132-136`) | `calendar_events`, linked recordings, `calendar.refresh` receipt | ON per `calendar.sources[].enabled` | calendar rows on the Desk |
| Duration ticker | `web_server.py:1406` / `:1216` | boot | 1.0 s | nothing durable | ON | live timer |
| Kernel liveness | `web_server.py:1418` / `:1236` | boot | 1.0 s | kernel operation state | ON | Process window |
| Coder frames | `web_server.py:1431` / `:1217` | boot | 2.0 s | WS frames | ON | coder surface |
| Rails observer | `web_server.py:1473` / `:1218` | boot | 5.0 s | rails journal projection | ON if rails configured | MissionControl journal |
| Refinement coordinator | `services/refinement_coordinator.py:89` / `web_server.py:1221` | boot | lease renew | `refinement_hosts` leases; resubmits recovered refinements | ON | refinement resumes; log only |

### 3.2 Off by default

| Loop | Started | Interval | The switch |
|---|---|---|---|
| **Cadence engine tick** | `runtime/ownership.py:137-142`, only if `_cadence_enabled()` (`runtime/cadence.py:19`) | `cadence.tick_interval_seconds`, default **300**, floor 30 | **`cadence.enabled = False`** (`config/integrations.py:202`) — **and there is no settings route for it**; `settings_service.py` maps only `cadence_telegram.*`. It is a hand edit of `~/.config/holdspeak/config.json`, and it must additionally pass `operation_policy.resolve_policy` |
| ↳ **Monday brief auto-regeneration** | `runtime/cadence.py:94`, only from the cadence tick | once/day after quiet hours | Same. **It is named and receipted as `"heartbeat"` (`runtime/cadence.py:120,138`) but the heartbeat never calls it.** With cadence off, the Monday brief **never regenerates on its own** — only `POST /api/brief/generate` from `CadenceCore.tsx:245` |
| ↳ needs-you cache invalidation | `runtime/cadence.py:155` | per tick | same — dead unless cadence is on |
| ↳ Telegram daily push | `runtime/cadence.py:64` | once/day | cadence on **and** `cadence_telegram.enabled` + `allowed_chat_ids` |
| Wake-word listener | `web_runtime.py:563`, live-toggled `:377` | continuous | `wake_word.enabled = False` (`config/device.py:70`) |
| Global hotkey | `web_runtime.py:543-548` | key press | ON; `hotkey.key`. Degrades silently to `global_hotkey_available: false` on a permission failure |
| Desktop presence | `web_runtime.py:385` | timer | `presence.enabled` false (`web_runtime.py:381`) |
| Recording ticker | `runtime/meeting_glue.py:346` — per meeting, not boot | 1.0 s (`device_recording_tick.py:65`) | ON during a meeting with devices |

### 3.3 Boot one-shots that run without a click

`web_server.py:1204` gate held-invalidation · `:1210` inference recovery · `:1219`
projection reap · `:1228` ask-task recovery · `:1239` skill seeding · `:1258`
steward `recover_on_startup` · `scheduled_recording_conductor.py:157`
boot reconcile · `runtime/transcriber_state.py:211` transcriber warm.

### 3.4 Wired but never started

| Thing | Evidence |
|---|---|
| `CalendarIngestConductor.start()` / `_loop` | **no production caller** — only `tests/unit/test_calendar_ingest_conductor.py` and `test_event_linked_arm.py:499`. `web_server.py:1309` constructs the object and does one synchronous boot refresh. `CALENDAR_REFRESH_SECONDS = 900` (`config/integrations.py:14`) is **dead configuration** feeding a thread that never runs |
| `holdspeak/cron.py` | not a scheduler at all — a cron-expression parser imported by the two conductors |
| `holdspeak/activity_nudges.py` | `compute_nudges` has one caller (`activity_nudge_service.py:17`), reached only from the HTTP route. **A nudge exists only while someone is looking at the page** |
| `IntelQueueWorker` standalone `start_intel_queue_worker` | now has a caller (`intel_queue_conductor.py:138`) — this was the audit's P0, fixed |

### 3.5 The ownership asymmetry

`_start_scheduled_work` (`runtime/ownership.py:124`) gates the heartbeat and
cadence on `owns_database`, and the intel drainer gates itself
(`intel_queue_conductor.py:72`). The **workbench conductor**, the
**scheduled-recording conductor** and the **plugin-job queue** have **no
ownership gate**. Under `HOLDSPEAK_ALLOW_UNOWNED_DB=1` the hub prints
"starting with scheduled work OFF" (`runtime/ownership.py:58`) while three loops
keep writing — including the one that **starts real recordings**.

### 3.6 "What is running on my behalf?" — there is no such place

No HTTP route and no screen lists the background machinery with last-run and
next-run. `grep "conductor" holdspeak/web/routes/` returns a steward comment and
an import. Seven partial surfaces exist instead:

| Surface | Covers | Misses |
|---|---|---|
| Rhythm / `CadenceCore.tsx` (`GET/PUT /api/settings/heartbeat`) | **only** the heartbeat (last/next sweep, interval, quiet hours, notify) + cadence loops + Monday brief | every conductor |
| Drainer badge `ChairHome.tsx:441` | intel queue depth + `absent`/`running` | no next-run |
| Process window `ProcessCore.tsx` | live kernel operations | schedules, idle conductors |
| Automations | per-watch enable + event history | no scheduler view; `next_evaluation_at` not surfaced |
| Scheduled recordings | that one conductor's `next_fire_at` | everything else |
| Steward posture | one project's policy + last run | per-project only |
| `GET /api/runtime/status` | hotkey, transcription, DB owner lock | no conductor list |

Three loops — the plugin queue, the workbench tick's reaction/resourceful
sub-ticks, and the cadence projections — are visible **only in log lines**.

---

## 4. Configuration surface

There is **no declarative settings registry**. The schema is a tree of Python
dataclasses rooted at `Config` (`holdspeak/config/core.py:264`), serialized whole
to `~/.config/holdspeak/config.json` (`core.py:34-35`). Everything else —
heartbeat, steward, watches, inference assignments, activity privacy, remote MCP
— is a **separate store** the settings service does not own.

### 4.1 config.json — 112 leaf keys

| Namespace | Keys | Owner |
|---|---:|---|
| `meeting.*` | **47** | `config/meeting.py:16` |
| `dictation.*` | **27** (incl. `dictation.runtime.*` ×14) | `config/meeting.py:445`, `config/model.py:53` |
| `cadence.*` | 7 | `config/integrations.py:196` |
| `model.*` | 6 | `config/model.py:12` |
| `wake_word.*` | 5 | `config/device.py:59` |
| `cadence_telegram.*` | 4 | `config/integrations.py:223` |
| `rails_observer.*` | 4 | `config/integrations.py:250` |
| top-level (`config_version`, `machine_id`, `control_mode`) | 3 | `core.py:266-277` |
| `hotkey.*`, `presence.*` | 2 each | `config/ui.py:13`, `config/device.py:24` |
| `ui.*`, `device.*`, `mesh.*`, `thoughts.*`, `calendar.*` | 1 each | — |
| **Total** | **112** | |

Plus five **virtual** wire keys never persisted (`_revision`, `_placement`,
`_calendar_subscription`, `_calendar_sources`, `_secrets` —
`settings_service.py:43-63, 175`) and **8 write-only secrets**
(`SECRET_PATHS`, `settings_service.py:22`) that `settings.update` refuses
(`strip_secret_mutations`, `:180`) and only `/api/settings/secrets/{id}` can write.

### 4.2 The other stores

| Store | Keys | Where |
|---|---|---|
| Project row | 17 columns incl. `detection_threshold` (0.4), `posture`, `review_cadence_json`, `modules_json` | `db/schema.py:538-567` |
| Steward policy (per project) | 9 columns; **`unattended_enabled` defaults `0`** | `db/schema.py:4133-4149` |
| …plus `evaluation_cadence_minutes`, **not a policy column** — it fans out to every watch of the project | | `web/routes/steward.py:295-309` |
| Watches / watch rules | 10 + 6 columns | `db/schema.py:2462-2484`, `:3944-3957` |
| Heartbeat | 5 keys in `cadence_policies.config_json` | `heartbeat_service.py:152-236` |
| Inference assignments | `global` + 6 groups (`thoughts_notes`, `writing_dictation`, `speech_recognition`, `meetings`, `agents_tools`, `background`), each a chain of ≤4 profiles | `inference_assignment_service.py:52-60`; `db/schema.py:2778-2791` |
| Activity privacy / domain / project rules | 2 + per-row | `db/schema.py:645-663` |
| Remote MCP | `enabled`, `bind_host`, `port` — **process memory, not persisted** | `web/routes/mcp_http.py:198, 248` |
| Coder gate | `~/.holdspeak/gate.json` (`gate_schema: 1`) + per-repo spawn settings | `coder_gate.py:46, 637` |

### 4.3 Environment variables — 24 `HOLDSPEAK_*`

Notable: `HOLDSPEAK_WEB_HOST`/`_PORT` (`web_runtime.py:67, 91`),
`HOLDSPEAK_ALLOW_UNOWNED_DB` (`runtime_lock.py:60, 271`),
`HOLDSPEAK_MCP_STANDALONE` (`runtime/composition.py:48, 227`),
`HOLDSPEAK_MCP_PEOPLE_ACCESS` (`mcp/families/people.py:26`),
`HOLDSPEAK_TOKEN` / `HOLDSPEAK_AGENT_CREDENTIAL` / `HOLDSPEAK_HUB_URL`
(`coder_gate.py`), `HOLDSPEAK_USER_PACKS_DIR` / `_USER_PLUGIN_PACKS_DIR`
(pack trust boundaries), `HOLDSPEAK_FAULT` (`faults.py:32`).
`HOLDSPEAK_ERROR` (`errors.py:18`) is **not an env var** — it is a constant with
a misleading name.

### 4.4 Files on disk

`~/.config/holdspeak/config.json` (the settings file) ·
`~/.config/holdspeak/blocks.yaml` ·
`~/.local/share/holdspeak/holdspeak.db` + logs + `meeting-captures/` ·
`~/.holdspeak/` holds **eight further config surfaces**: `gate.json`,
`gate-spawn-settings/`, `agent_credentials/`, `connector_packs/`,
`plugin_packs/`, `workbenches/`, `pricing.json`, `profile-custody/profile-keys.json`,
`delivery_workbench.json` · per-project `<repo>/.holdspeak/project.yaml` and
`blocks.yaml` (the project file **fully replaces** the global one,
`plugins/dictation/blocks.py:185`).

**Two config roots.** `~/.config/holdspeak/` is the settings file;
`~/.holdspeak/` is nine unrelated stores. Nothing names the split.

### 4.5 Day one — what a user actually has to touch

| # | Setting | Why |
|---|---|---|
| 1 | **Inference assignments** — `global`, then `meetings` and `writing_dictation` | nothing generates anything without a routable model |
| 2 | **Model library** — download or connect one engine | assignments are unfillable without a ready engine |
| 3 | `meeting.mic_device` + `system_audio_device` | otherwise capture records silence |
| 4 | `hotkey.key` | default `alt_r` collides on many keyboards; the whole dictation path is unreachable if it does not fire |
| 5 | `model.language` | default `auto`; pinning it is the biggest transcription-quality win |
| 6 | `calendar.sources[]` | gates `intelligence_auto: "room_linked"`, `auto_record`, 1:1 briefs, most of Rhythm |
| 7 | Provider connections (GitHub/Jira/Confluence) | prerequisite for Projects, watches, steward. **Not in config.json at all** |
| 8 | `cadence.enabled` (**a hand edit of the JSON file — no route, no screen**) + heartbeat quiet hours | the whole nudge/rhythm half is off |
| 9 | per-project `steward_policies.unattended_enabled` | the steward observes and never acts until this is flipped, per project |

A user who stops after 3 has a working recorder. Items 8 and 9 are the two the
product will not tell them about.

### 4.6 Legacy and duplicated

| Thing | A | B | Which wins |
|---|---|---|---|
| **Model assignment** | 4 separate config pointers: `meeting.intel_profile_id`, `dictation.runtime.profile_id`, `thoughts.inference_target_id`, `rails_observer.profile_id` | the `inference_assignments` table (`global` + 6 groups) | **B**, but only once a per-family migration row exists — until then both are live (`settings_service.py:224-250, 262-290`). MCP's own tool description calls A "retired routing controls" (`mcp/families/settings.py:32`) |
| **Meeting provider** | `meeting.intel_provider` (`local\|cloud\|auto`) | the adopted destination / placement authority | the destination can override the dial; `_placement.provider_honored` is false when it did (`settings_service.py:63, 89`) |
| **Cloud endpoint** | `meeting.intel_cloud_*` and `dictation.runtime.openai_compatible_*` | the profiles table | A is declared dead (`LEGACY_ENDPOINT_FIELDS`, `config/core.py:120-127`), stripped on read and write — yet still serialized into the file a user can open |
| **Calendar** | `_calendar_subscription` (single legacy source) | `calendar.sources[]` | B; A kept alive only for `SettingsCore.tsx` and e2e seeds (`settings_service.py:57-59`) |
| **Quiet hours** | `cadence.quiet_hours_start/_end` in config.json | heartbeat `quiet_hours.{start,end}` in the DB | **two stores, same defaults 22/8** (`config/integrations.py:209-210` vs `heartbeat_service.py:210`) |
| **`settings.hub`** | web handler `web/routes/system/settings.py:145` | MCP handler `mcp/tools.py:807` | **two independent re-implementations of one aggregate, already drifting** — the web one carries the intel-run receipt and remote-host rhythm; the MCP one does not |

**Legacy profile ids.** `legacy-intel` and `legacy-dictation`
(`config/core.py:130-131`) are synthetic rows minted once by
`migrate_legacy_endpoints` (`:189-247`) and shown in the model library as real
profiles named "Migrated intel endpoint" / "Migrated dictation endpoint".

**Stored but unwritable.** `_DEFAULTED_MODEL` and `_DEFAULTED_MEETING`
(`settings_service.py:420-429`) are silently dropped from any patch — the file
shows ~9 values a user cannot change. One of them, `web_auto_open`, is stripped
but **does not exist on `MeetingConfig` at all**.

**Dead keys** (stored, read by nothing): `meeting.intel_summary_model`
(only the normalizer touches it, `settings_service.py:444`),
`meeting.mir_enabled` (pinned true, zero web references),
`meeting.intent_segment_probe_enabled` (one read, no UI),
`model.local_model_preload_authority`, `dictation.runtime.eviction_idle_seconds`.
Already-deleted-and-stripped: `ui.theme`, `ui.history_lines`,
`ui.show_audio_meter`, `meeting.intel_queue_poll_seconds`, `meeting.mir_profile`,
`meeting.plugin_profile` (`settings_service.py:475-502`).

### 4.7 Reachability

| Bucket | Count |
|---|---:|
| config keys reachable from a web screen (`PREF_MODULES`, `web/src/pages/cores/settingsPrefs.tsx:40-59`) | **109 of 112** |
| not on any screen (`thoughts.inference_target_id`, `config_version`, `machine_id`) | 3 |
| hidden behind per-module "RAW" diagnostics folds rather than the primary face | **~33** |
| MCP-only | **~0** — `settings.update` takes an arbitrary partial patch (`mcp/families/settings.py:41-47`), so MCP is a **superset** of the web surface |
| web-only, not MCP | the 8 secrets |
| writable by neither | ~9 pinned + 6 legacy endpoint fields |

## 5. Model / engine path

**There are two complete, parallel model-selection stacks in the tree, plus a
third for speech, and which one runs is decided by rows in a migration-marker
table that has no screen.**

| Stack | What it is | Governs |
|---|---|---|
| **A — routed** ("Phase 143") | capability registry → assignment ledger → route plan → fallback controller → runner | desk chat, meeting intel, agent turns, and post-migration dictation LLM legs |
| **B — legacy config placement** | `Config.meeting.*` / `Config.dictation.runtime.*` → `profiles` pointer → `resolve_meeting_placement` / `effective_dictation_llm` | pre-migration dictation; **and the meeting "host" badge**, which is all it still does |
| **C — speech plan** | `Config.model.*` → `whisper_deployment_identity` → frozen `DeploymentRevision` → `Transcriber` | Whisper, when the routed branch is not taken |

The switch between A and B is
`inference_assignment_migrations` (`db/schema.py:2801`), read at
`speech_session/session.py:645-662`, `plan.py:512`, `ask_service.py:368`,
`refinement_coordinator.py:294`, `settings_service.py:255`. **It is invisible to
the user.**

### 5.1 Transcription (audio → text)

No remote transcription exists; every path is local Whisper (MLX or
faster-whisper — there is no Parakeet anywhere).

1. Session reads **two** migration markers — `speech_routing` and
   `provider_routing` (`speech_session/session.py:645-652`).
2. `new_speech_route = speech_routing AND provider_routing AND principal is not
   DEVICE_SERVICE_IDENTITY` (`session.py:658-662`). **Any one missing and the whole
   session falls back to legacy. Device-service capture is permanently legacy.**
3. Routed → `_routed_session_validation_plan` (`session.py:668-681`); the bundle is
   sole authority. Legacy → `DictationSessionPlanResolver().resolve` (`:684-690`)
   → `whisper_deployment_identity(config.model)` (`plan.py:260-274`).
4. Routed assignment resolution walks invocation → subject → capability → group →
   global (`inference_route_plan_service.py:381-397`).
5. `speech.transcribe` revisions return an **inert handle** — they load nothing
   (`inference_targets.py:737-741`).
6. **The function that actually picks the model:**
   `TranscriberState._ensure_transcriber_loaded` (`runtime/transcriber_state.py:81-121`),
   then `_resolve_backend` (`transcribe.py:116-146`: `auto` → mlx on darwin-arm64 if
   importable, else faster-whisper, else raise).
7. **Escape hatch:** if the caller omits `model_name=`, step 6 falls back to ambient
   `Config.model.name` **even under a frozen route** (`transcriber_state.py:94-96`).
   Routed callers pass it (`:198`, `runtime/meeting_glue.py:217`); `main.py:687` and
   `commands/import_recording.py:74` do not.

### 5.2 Dictation (push-to-talk → typed text)

Two selections per utterance: the Whisper leg (as §5.1) and the LLM leg.

1. Same marker gate (`session.py:645-662`).
2. Routed → `freeze_assigned_provider_routes()` re-checks
   `family='thoughts-writing-route-assignments'`; **if absent it silently returns**
   (`session.py:297-321`). Aliases `intent-router`→`speech.intent_classify`,
   `rewrite`→`speech.rewrite`.
3. The resolver **blanks `pipeline_terms["runtime_profile_id"]`** (`plan.py:512-518`)
   and replaces the legs with `f"routed:{name}"` sentinels (`:554-558`).
4. Legacy → `_provider_legs` (`plan.py:609-644`): blank pointer →
   `dictation_local_deployment_identity` → `_local_dictation_engine(backend)`
   (`auto` probes `mlx_lm`, else `llama_cpp`); non-blank →
   `resolve_placement(db, invocation=profile_id)` (`inference_targets.py:567-604`).
5. Construction: `_try_build_runtime` (`plugins/dictation/assembly.py:197-345`).
6. **Any adopted profile forces `backend = "openai_compatible"` regardless of
   `cfg.runtime.backend`** (`assembly.py:341`) — a user's `backend = "mlx"` is
   silently discarded.

### 5.3 Meeting intelligence (transcript → summary/decisions/actions)

Fully routed for execution. Legacy is still live **for reporting only**, and
that is the sharpest defect found.

1. `meeting_run_intelligence` enqueues a job (`meeting_intel_service.py:46-83`).
2. **The reported host** comes from `resolve_meeting_placement(Config.load().meeting)` —
   the *legacy* stack (`meeting_intel_service.py:82-90`), precedence mesh profile >
   openAICompatible profile > `intel_provider` intent (`intel/providers.py:666-727`).
3. The drainer claims the job (`intel_queue.py:674-676`), freezes plugin members
   (`db/intel.py:314-405`), probes each plugin capability for a freezable assignment
   — **no assignment ⇒ silently skipped with a receipt, not a failure** (`:406-434`).
   The three core capabilities (`meeting.deferred_analysis`, `bookmark_label`,
   `auto_title`) are strict: a missing assignment is terminal.
4. Binding freezes every route as a **SERVICE** principal
   (`meeting_deferred_queue_binding.py:133-140`).
5. **SERVICE principals are default-deny**: `assignment_sources` restricted to
   `("capability",)` (`inference_service_route_policy.py:41`, enforced at
   `inference_route_plan_service.py:392-394`). **A group or global assignment that
   works for your desk chat is invisible to the meeting queue.**
6. Entries → deployment revisions (`:1309-1375`), leg election
   (`inference_fallback_controller.py:175-410`), engine built by
   `_engine_for_revision` (`inference_targets.py:719-783`).

**The lie:** steps 2 and 6 read from **different stacks**. `run_intelligence`
stamps `set_intel_job_model_host` from `Config.meeting.intel_profile_id` /
`intel_provider` and returns it to the UI as `"host"`. Execution ignores it. A
user with a LAN assignment and default config **sees `"local"` while the run
egresses to `192.168.1.43`**. The comment at `meeting_intel_service.py:76-77`
claims "Article III at the point of decision" — it is not the point of decision.

### 5.4 Desk chat / agent turns

1. Capability is hardcoded `"chat.turn"` (`thread_service.py:499-500`).
2. The per-thread picker reads `thread.profile_override` (`:508`) and, if set,
   writes an **invocation-scoped assignment** right before admit (`:1826-1845` →
   `inference_adoption_service.py:2078-2094` → `set_assignment`).
3. Admit (`:527-537`), route resolution (invocation scope wins,
   `inference_route_plan_service.py:381`), badge read back off the frozen plan
   (`:539-547`), cloud-boundary redaction gated on the frozen boundary (`:1849-1875`).
4. Multi-pass tool turns **re-apply the override per pass** with a fresh invocation
   id (`:1100-1119`). Agent tool turns go through `agent_turn_service.py:124-180`.

### 5.5 The LAN endpoint 192.168.1.43:8080

**Not configured or discovered anywhere in the Python hub** — zero hits outside
`apple/` and `pm/`. On the hub it is only ever a `profiles` row the user created
(`profile_service.py:58`, `model_library_define_endpoint`, or Concierge).
Classification is **by IP, not identity**: `egress_boundary`
(`intel/providers.py:390-425`) returns `private_network` for RFC1918; Concierge's
`_is_lan_host` (`concierge_service.py:285-300`) adds `.local`/`.ts.net`/`.internal`.
Discovery runs only over **already-known** endpoints (`concierge_service.py:371-384`);
`front_door_service.py:9` states "No network-wide scan." And **LAN endpoints skip
the key requirement entirely** (`concierge_service.py:387`), so a LAN box is
`STATE_READY` unconditionally.

### 5.6 Every mechanism that can decide which model runs — 29 of them

| # | Mechanism | Owner | Web screen? |
|---|---|---|---|
| 1 | Capability registry (48 capabilities, 9 groups, 7 retry policies) | `inference_capabilities.py:1031-1101` | indirectly (group labels) |
| 2 | Assignment ledger, 5 scopes | `inference_assignment_service.py:382`, scopes `:1420-1490` | **yes** — `CapabilityAssignmentsCore.tsx`, `AssignmentEditor.tsx` |
| 3 | Next-run / invocation override | `inference_adoption_service.py:2078` | only the thread model picker |
| 4 | Service route policy (SERVICE default-deny) | `inference_service_route_policy.py:41` | **no** |
| 5 | Route plan (frozen, hashed) | `inference_route_plan_service.py:209/242/405` | read-only in receipts |
| 6 | Fallback controller | `inference_fallback_controller.py:175` | receipts only |
| 7 | Model profiles **v2** | `services/model_profile_service.py` | the *data* via `ModelLibraryCore.tsx`; **the dedicated `/api/model-profiles` CRUD family has no caller** |
| 8 | Legacy `profiles` table **v1** | `services/profile_service.py:58-95` | yes — `/profiles`, aliased into Concierge |
| 9 | Model Library (composes 7 + 8 + catalog) | `services/model_library_service.py` | yes |
| 10 | Concierge | `concierge_service.py:355-470`, `:1081-1160` | yes |
| 11 | Front Door / packs | `front_door_service.py:715-790, 974` | yes |
| 12 | Starter bundle | `inference_assignment_service.py:732` | via 11 |
| 13 | Signed preset catalog | `inference_setup_catalog.py:33+` | yes |
| 14 | Acquisition (downloads) | `inference_acquisition_service.py:411, 505` | yes |
| 15 | **Migration markers** | `db/schema.py:2801` | **no — invisible, and they decide which stack runs** |
| 16-19 | `Config.meeting.intel_provider`, `intel_profile_id`, `intel_realtime_model`, `intel_cloud_*` | `config/meeting.py:33, 73, 36, 65-69` | **no** (settings API + MCP only) |
| 20-22 | `Config.dictation.runtime.backend` / `profile_id` / model paths | `config/model.py:56, 69, 59-60` | partly |
| 23 | `Config.model.name/.backend/.language` (Whisper) | `config/model.py:14-16` | partly |
| 24 | `local_model_preload_authority` | `config/model.py:44` | no |
| 25 | Thought placement pointer | `inference_targets.py:607-619` | partly |
| 26 | `resolve_placement` 4-tier ladder | `inference_targets.py:567-604` | no |
| 27 | Profile key custody | `profile_key_service.py:19` | yes (key-set state) |
| 28 | Meeting plugin router | `plugins/router.py:110` | no |
| 29 | Runner engine factory | `inference_targets.py:702/719` | no |

**Naming traps** — these sound like model selection and are not:
`holdspeak/target_profile.py` detects the *destination app* you are dictating
into (`:61`); `holdspeak/dictation_selection.py` is a 5-minute pin of an
ActivityRecord id (`:38`); `services/profile_service.py` "profiles" are
*endpoints*; `DictationPipelineConfig.target_profile_override`
(`config/meeting.py:379`) overrides the *app* profile, not a model;
`inference_capability_service.py` is a 67-line read-only projection.

### 5.7 Overlaps — where two mechanisms decide the same thing

| # | Overlap | Winner (precedence code) |
|---|---|---|
| O1 | The 5 assignment scopes | first match walking the ordered key list, `inference_route_plan_service.py:379-386`; invocation beats everything |
| O2 | Routed assignments vs legacy dictation config + pointer | the migration marker; `plan.py:512-518` blanks `runtime_profile_id`, `:554-558` replaces the legs |
| O3 | Routed `speech.transcribe` vs `Config.model.*` | `session.py:658-662` — needs **both** markers **and** a non-device principal |
| **O4** | `meetings` group assignment vs `intel_profile_id`/`intel_provider` | **assignment wins execution** (`meeting_deferred_queue_binding.py:133`); **config wins the displayed host** (`meeting_intel_service.py:82-90`). Never reconciled — a live lie in the UI |
| O5 | `intel_profile_id` vs `intel_provider` | adopted destination beats intent, `intel/providers.py:678-706`; a dangling pointer degrades and surfaces `PLACEMENT_PROVIDER_OVERRIDDEN` |
| **O6** | `cfg.runtime.backend` vs an adopted `profile_id` | the profile wins unconditionally — `assembly.py:341` silently discards the user's backend |
| O7 | v1 `profiles` vs v2 `model_profile_revisions` | per entry by `profile_schema_version`, `inference_route_plan_service.py:1317` — **two schemas, two editors, one route** |
| **O8** | Concierge apply · Front Door packs · AssignmentEditor · MCP `inference_assignment_set` · `apply_starter_bundle` | all five funnel to `set_assignment`; **last writer wins** via optimistic `expected_revision` (`:403-412`). No ownership marker, so the Concierge silently stomps a hand-edited group |
| **O9** | OWNER inheritance vs SERVICE default-deny | principal kind (`inference_service_route_policy.py:41`) — **a group assignment that works for desk chat is invisible to the meeting queue** |
| O10 | `resolve_placement` 4-tier vs assignment 5-scope | **nothing reconciles them.** Two differently-shaped ladders; `plan.py:638` uses the first, everything routed the second |
| O11 | Frozen entry vs `reserve_next_attempt` context-skip | the controller may skip ahead on `context_support.maximum_tokens` (`inference_fallback_controller.py:274-289`) — **entry 1 is a preference, not the answer** |
| O12 | `_ensure_transcriber_loaded(model_name=)` vs ambient config | argument wins if passed; two CLI callers do not pass it |
| O13 | Strict core capabilities vs skip-with-receipt plugins | core three terminal; `meeting.plugin.*` **silently excluded** (`db/intel.py:406-434`) — half a summary, no error |
| O14 | `requires_key` + key presence vs assignment selection | a keyless cloud profile still freezes and **fails at dispatch** (`concierge_service.py:387-390`) |
| O15 | `paired_device` assignable in the editor vs unbuildable at runtime | refused by name at `inference_targets.py:780-782` — **you can assign a model that can never run** |
| O16 | `engine_display_name` vs `resolveEngine` vs `run_egress` | **three separate namers** (`concierge_service.py:110`, `web/src/pages/cores/dictation/SpeakFace.tsx:201-262`, `intel/providers.py:455-477`) for "what is running" |

### 5.8 How many concepts to answer "which model runs my meeting summary?"

**Sixteen.** Capabilities · capability groups · the 5-scope ladder · SERVICE
default-deny · profiles v1 vs v2 · bindings and deployment revisions · readiness
observations · retry policy and fallback dispositions · the context-ceiling skip ·
egress boundary and `allowed_boundaries` · profile key custody · migration markers ·
the legacy `intel_*` trio · the plugin chain router · skip-with-receipt · and which
of six surfaces last wrote the assignment.

And after all sixteen, the number the product shows you
(`meeting_intel_service.py:90`) is computed from the stack that **does not run**.

---

## 6. Complexity verdict — the top 10

Ranked by how much of the user's day the excess concept costs. Nothing is
proposed for deletion; the owner's standing rule is **park, never delete**.

### 1. Two model-selection stacks, arbitrated by an invisible table

**The excess:** 29 mechanisms, 16 concepts, 3 stacks, and a migration-marker table
with no face that decides which stack even runs (`db/schema.py:2801`,
`session.py:658-662`). The user needs one sentence: *this capability runs on this
model*.

**Collapse:** finish the migration and make the marker a **boot-time fact, not a
per-session branch** — one `routing_generation` value the hub logs at startup and
`GET /api/runtime/status` returns. Park Stack B whole (`intel/providers.py`
placement, `Config.meeting.intel_*`, `Config.dictation.runtime.profile_id`) behind
a single `legacy_routing` flag that defaults off and is settable only from the
config file. Retire `resolve_placement`'s 4-tier ladder (O10) in favour of the
5-scope one.

### 2. The meeting host badge is computed from the stack that does not run

**The excess:** two answers to "where did my summary run", and the one on screen is
the wrong one (`meeting_intel_service.py:82-90` vs
`meeting_deferred_queue_binding.py:133`). This is not complexity, it is a
truthfulness defect wearing complexity's clothes — and it is exactly the class of
thing the egress badge exists to prevent.

**Collapse:** delete the legacy read at the call site and stamp `model_host` from
the **frozen route plan**, the same object the receipt already carries. One
function, one source. Everything else here can wait; this cannot.

### 3. SERVICE default-deny makes the assignment editor lie by omission

**The excess:** the user sets a `meetings` **group** assignment in the editor, and
the meeting queue cannot see it (`inference_service_route_policy.py:41`,
`inference_route_plan_service.py:392-394`). The editor shows a green row for an
assignment that does nothing. Combined with skip-with-receipt (O13), the result is
a half-written summary with no error.

**Collapse:** either let SERVICE principals inherit the group scope for capabilities
whose boundary the policy already permits, or — cheaper and honest — have the
assignment editor **render the effective set per principal kind**, so a group row the
meeting queue cannot use is drawn as an unfilled slot with the reason on it.

### 4. Nowhere to see what is running on your behalf

**The excess:** 15 loops, 4 of them with no ownership gate, 3 visible only in log
lines, and **seven partial surfaces** none of which is a roster (§3.6). A user
cannot answer the single most basic question about an unattended product.

**Collapse:** one route — `GET /api/runtime/schedule` — returning a row per loop
(`name`, `enabled`, `interval`, `last_run_at`, `next_run_at`, `owner_gated`,
`last_outcome`), fed by a tiny registry the conductors register into at start. One
screen renders it. This is the highest value-per-line item in this whole document:
it makes the other nine visible.

### 5. Five ways to write a group assignment, no ownership marker

**The excess:** Concierge, Front Door packs, the Assignment editor, MCP
`inference_assignment_set`, and `apply_starter_bundle` all funnel to `set_assignment`
with last-writer-wins (O8). Re-running the Concierge **silently stomps a hand-edited
group** and nothing records that it did.

**Collapse:** stamp `set_by` on the assignment revision (already versioned at
`inference_assignment_service.py:403-412`) and have every bulk writer — Concierge,
packs, starter bundle — **skip a row whose `set_by` is `owner`**, disclosing what it
skipped. Zero new concepts; one column.

### 6. Two config roots and nine unrelated stores under `~/.holdspeak/`

**The excess:** settings live in `~/.config/holdspeak/config.json`; gate config, spawn
settings, agent credentials, connector packs, plugin packs, workbench memory, pricing,
profile keys and the delivery map live in `~/.holdspeak/`. Nothing names the split,
and `~/.holdspeak/` is the one users find first.

**Collapse:** move the nine under `~/.config/holdspeak/` (or `~/.local/share/`, by
XDG kind) with a symlink shim from the old root for one release. If that is too much
churn, at minimum add `holdspeak doctor --paths` printing the full map — the CLI
already owns the "where does my stuff live" question.

### 7. The dictation correction loop is a whole subsystem the owner has disowned

**The excess:** corrections CRUD, the learning digest, `dictation_learning.py`, the
journal replay path, and a third correction kind added by Phase 176 — against the
owner's own words, *"I honestly don't give too much of a shit about those
corrections"* (recorded as the 2026-09-08 data point).

**Collapse:** park the correction surfaces behind the Speak face's RAW fold, keep the
journal (it is the receipt and it is used), and stop charting work against the loop.
No code is deleted; it stops occupying the primary face and the roadmap.

### 8. Five overlapping "run a thing" primitives

**The excess:** recipes (9 routes), chains (7), workflows (7), workbenches (22),
practice recipes (3) — plus reactions and automations. They differ in provenance, not
in what the user wants: *run these steps, on a schedule or on a trigger*. And
HS-200-48 has now found that a practice recipe **cannot even be named as scheduled
work**, because the delegation resolves `recipe_id` against the *agent-persona* table
(`schedule_delegation.py:17-19`).

**Collapse:** pick **workbench** as the surviving noun (it has the schedule column,
the memory, the runs and the most face) and express the other four as workbench
templates. Park the chains and workflows routes; keep recipes as personas only, which
is what the table actually is. Fixing HS-200-48 by namespacing is treating the
symptom of five nouns where one belongs.

### 9. `desk.verb` is a catalog of refusals nobody can use

**The excess:** a documented tool whose five dispatchable verbs have an **empty
intersection** with the UI's own verb registry (`mcp/tools.py:1016`), 22 registry
verbs missing from the catalog, and `window.close`/`minimize`/`cycle`/`snap-*`
advertised and doing nothing. `desk_snapshot`'s MCP description advertises "layout"
and returns none (`resources.py:158`).

**Collapse:** two small honesty fixes, both prerequisites for anything the X11 vision
would need. (a) A **parity test** binding the three verb lists so the catalog cannot
drift again. (b) `desk_snapshot` either returns layout or **stops advertising it** —
and `desk.verb` returns a real refusal (`isError: true`) instead of a stub that reads
as success. Same for `project.steward.trigger`'s `scheduler_not_wired`
(audit §10.9, still open).

### 10. Three faceless capability families and a parked wizard

**The excess:** `/api/model-profiles` (8 routes, zero callers), the repository
working tree (8 of 10 routes, zero callers), `review_claim` (defined, never called),
and the **entire Interview/Setup wizard** — 12 routes, 10 MCP tools, 8 tables from
Phase 159 — whose only caller is `web/src/features/project-room/_parked/setup/api.ts`.
The parked wizard matters beyond itself: HS-200-52 found that
`ProjectService.create_from_setup` is **the only path in the product that mints an
armable watch**, so parking the face parked the only working watch-creation route.

**Collapse:** (a) Unpark or formally retire the Interview — but **first** move the
arming logic out of `create_from_setup` into `watch_service.arm_watch` so the Door and
the MCP verb mint armable watches too (this is HS-200-52 and it is `backlog`).
(b) Park `/api/model-profiles` CRUD behind the Model Library, which already renders
the same data. (c) Either give `review_claim` a route or delete the claim-review
concept from the update schema — a permanently `unreviewed` field is worse than no
field. (d) Park the 8 repository write routes; `web/src/desk/repository.ts` uses two.

---

### The one-line verdict

The machine side is real, large and mostly honest: 693 routes, 225 MCP tools, 118
capabilities, and only **3 genuinely dead**. The audit's two missing callers are
**fixed**. What remains is not missing function calls — it is **duplication**: two
model stacks, two config roots, five run-primitives, five assignment writers, two
`settings.hub` implementations, and fifteen background loops with no roster. The
user's cost is not that the product cannot do things; it is that **for most
questions there are two answers and the one on screen is not always the one that
ran.**

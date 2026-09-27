# Phase 9 - The Room on the Contract

**Last updated:** 2026-09-27 (round two: Codex Astra r1 DO-NOT-RATIFY paid (`checks/charter-astra-r1.md`); Codex Astra r2 owed; the owner's ratification owed. Round two added Q0 (the job ends at publication in the Room), the admission table for every in-scope identity, the source-addition and agent-authority probes (F16–F19, reproduced), the new-tool contracts, the HTTP exceptions inventory, the steward lifecycle beat, the red-first matrix and the pinned closing contract. Earlier: DRAFTED by the Fedaykin docs lane (Opus 5.5) for Muad'Dib on the owner's rulings D1–D3 of 2026-09-27, grounded on main `b37dc2fb`. Nothing is built.)

**Status:** DRAFT — round two: Codex Astra r1 DO-NOT-RATIFY paid; Codex Astra r2 owed; the owner's ratification owed.

## Goal

The owner works in a project room. He makes a project, puts a milestone and a risk in it, sees what needs him, lets the steward run and draft his update, and publishes that update in the Room — from the Room's face or from an MCP client that knows only the catalogue. The Room, its sources (the connectors) and the steward reach one declared operation each, bound to the hub's services, as Phase 7 did for notes, zones and decisions. The Room's face shows what the hub holds. Plus one bounded story of desk debts from the Phase 8 ledger. Delivery of the update to a person is not in the job unless Q0 (b) is ruled.

## Authority

The owner, 2026-09-27, by AskUserQuestion (his picks, verbatim):

- **D1, the job:** "Work in a project room" — Projects on the contract: the Room, its connectors and the steward on the one declared contract, as Phase 7 did for notes/zones/decisions. The closing test: a cold-context client runs a real project job from the MCP catalogue alone, and the Room's face shows it at 1440 and 393.
- **D2:** "Yes, one bounded story" of desk debts from the Phase 8 ledger: the desk-wide `::selection` you can see (`web/src/styles/global.css:68`, 1.13:1 today), and the list face repair (10 px count line → 12 px, the "SHOWNS" plural, the Zone column cut at 393, raw sort-header buttons → library Button, the row menu's Delete cut 15 px at 393). Canvas first for the list face (UX-CANON §A.2).
- **D3, the closing client:** Codex (cold context; the Phase 7 story 04 driver `scripts/philo7_file_and_find.py` and its launch setup are the precedent).

The ledger this phase pays: the BACKLOG row "Projects on the contract" (`pm/roadmap/holdspeak/BACKLOG.md:1300-1304`), Phase 8's THE LEDGER rows 1, 2 and 6 (`../phase-8-the-honest-floor/final-summary.md` "THE LEDGER"), and Phase 7's ledger row 8, "find it cold" (`../phase-7-the-desk-on-the-contract/final-summary.md` THE LEDGER; BACKLOG "PHILO-7-04 follow-ups" row 3).

Muad'Dib's rulings on round two (2026-09-27, paying Codex Astra r1): the job ends at "draft and publish the update in the Room" (Q0, recommended); source addition is closed by a durable, truthful outcome, never by "svc fixed"; Q1 becomes an explicit operation/argument/effect/admission table; Q2 is restated as owner execution with named refusals versus bounded project delegation; Q3's alternatives propagate into scope, stories, discovery and the closing assertions; each repair story ships its own fences; a steward lifecycle beat precedes story 02; F14 is a prerequisite repair in story 01.

Carried, unchanged: the Seven Tenets (`docs/internal/CONSTITUTION.md:18-60`); Article XI (`docs/internal/CONSTITUTION.md:167-193`); UX-CANON §A.1 every verb the library Button, §A.2 the canvas before build, §A.11 a verb that does nothing is a lie (`docs/internal/UX-CANON.md:17-58`); the method and laws of handovers XXVIII–XXX (`docs/internal/project-rooms/HANDOVER-MUADDIB-XXVIII.md:11-20`, `HANDOVER-MUADDIB-XXIX.md:33-42`, `HANDOVER-MUADDIB-XXX.md:18-24`); Phase 5's settled positions and compatibility rules (`../phase-5-the-one-service-layer/current-phase-status.md:109-146`); Phase 7's "Settled between the brains" (`../phase-7-the-desk-on-the-contract/current-phase-status.md` §"Settled between the brains"); the owner's ruling that MCP flows through the services (2026-09-23, verbatim in the Phase 7 Authority).

## The roots

- **Tenet 2 (not even pre-alpha):** the Room is where his second job lives, and today he cannot reach it from the places that point to it (F1), and no suggested source can become a watched source (F16, F17).
- **Tenet 3 (help and accelerate):** the face must say what the hub did. Today the steward face shows effect counts the run did not take (F3), the Room says ON TRACK with a milestone seven days late that it does not show (F2), the Room read says the updates and the steward are "not_yet_built" after both ran (F6), and a Jira suggestion answers "accepted" with nothing added (F17).
- **Tenet 1 (no over-engineering):** one explicit descriptor row per operation, as in Phase 7. No discovery framework, no universal CRUD, no new authority policy beyond what Q1 and Q2 rule. The setup interview and the provider discovery tools keep working as they are; their migration is deferred.
- **Tenet 5 (component framework):** the Room composes the library species it has; the items section (Q3) and the list face repair are drawn on the canvas from the library first.
- **Tenet 7 (a Senior Architect with reports):** a project has milestones, risks and a steward; he writes where it stands. The job and the closing test are his.
- **Article XI:** today no project write is admitted through the kernel and none leaves a kernel receipt (F8); an agent with a PROJECT credential can turn on unattended steward runs and archive a project with no grant (F19). Q1 and Q2 ask him to rule both.

## Status of this charter

DRAFT, round two, 2026-09-27, written by the Fedaykin docs lane (Opus 5.5) for Muad'Dib. Codex Astra r1 (`checks/charter-astra-r1.md`): DO-NOT-RATIFY, nine findings, six conditions, four MISSED; paid in this revision ("Round two: Codex Astra r1, paid"). Owed: Codex Astra r2; the owner's ratification and his answers to Q0–Q3. Nothing is built. The stories stay `backlog` until the owner ratifies.

## The grounding (main `b37dc2fb`)

The full record, with every shot, log and probe: `docs/internal/philo/phase-9/grounding/README.md` (round two's probes: its "Round two" section and `round-two/r2-probes.json`). Product code is unchanged between `b37dc2fb` and this revision.

- **The census.** `scripts/residual_census.py --check` under an isolated HOME: `RESIDUAL FENCE GREEN: 284 identities match` = 223 MCP + 61 HTTP; public tools 229 (reproduced by Codex Astra, r1 F6). The project identities: **61 MCP + 6 HTTP** — `project.*` 42; the connectors in the same module, `provider.*` 13 and `connection.*` 2; `desk.needs_you`, `steward.nudges`, `nudge.send`, `nudge.dismiss` 4 (in `holdspeak/mcp/tools.py`); HTTP `projects.py` 4, plus `ProjectService` built in `automations.py` and `people.py` 2. The census counts constructors and declared exposure; it is not a capability inventory — see "HTTP capability exceptions".
- **The job, walked** over `/api/mcp` from `tools/list` and on the face at 1440x900 and 393x852, on a real hub with an isolated HOME.
- **FINDINGs, ranked by owner cost** (lines and shots in the grounding README):
  - **F1** The Room cannot be opened from the eight places that point to it: the key `project-room` is registered nowhere and its fallback `/projects` is no route (`web/src/desk/chair/ChairHome.tsx:851`, `web/src/pages/cores/history/MeetingReview.tsx:273`, six more; `web/src/App.tsx:68`). Walked: a meeting's project button opens nothing, at both widths.
  - **F16** A GitHub suggestion cannot be added: the route's `{ref}` is one path segment (`holdspeak/web/routes/projects.py:608`); `POST …/suggested-sources/example%2Fpayments/add` answers 404 (round two, P1; Codex Astra r1 F2).
  - **F17** A Jira suggestion is marked accepted and nothing is added: `POST …/suggested-sources/PAY-123/add` answers 200 `accepted_no_watch`, the suggestion becomes `accepted`, zero resources and zero watches exist after (P1). The route accepts first and swallows the failure (`projects.py:628`, `:633-639`); `qualified_ref` refuses `jira:` and `github:` refs (`holdspeak/db/relationships.py:25`); and a successful `add_resource` writes no watch at all (`holdspeak/services/project_service.py:3169-3284`), though the tool says it creates a Watch source (`holdspeak/mcp/families/project.py:833`).
  - **F19** A PROJECT credential with no delegation turned on unattended steward runs (`project.configure_steward(unattended_enabled=True)`) and archived a project; zero kernel rows (P3; Codex Astra r1 F4).
  - **F2** A milestone he adds does not show in the Room (no items section), and the Room says ON TRACK seven days after its date (overdue counts commitments only, `project_service.py:1457-1461`).
  - **F3** The steward face shows "Observe 1 source · Propose 1 · Act 1 effect" for a run with `proposal_count: 0` and `actions_taken: 0`: it counts each phase's checkpoint step (`web/src/features/project-room/steward/StewardPosture.tsx:155-164`). The run did not do nothing: COMPARE opens a review (`holdspeak/services/project_steward_service.py:860-869`); ACT performed no action because, with no policy, no effect kind is eligible, and no word says so.
  - **F4** No MCP verb adds anything to a project: items and resources are HTTP only (`projects.py:294-325`, `:411-515`); the face creates through the Door (which arms and baselines watches), MCP through `project.create` (a bare project).
  - **F5** `project.suggested_sources`, `add_suggested_source` and `dismiss_suggested_source` fail on every call (`svc` unbound, `project.py:2044`, `:2053`, `:2058`, `:2072`). Repairing that alone would reach F17.
  - **F18** Archive is not a label edit: it pauses the project's watches and turns unattended steward runs off in the same transaction (`project_service.py:3023-3035`); reproduced (P2: `unattended_enabled` 1 → 0, zero kernel rows).
  - **F6** The Room read says updates and steward are `absent · not_yet_built` after both ran (`project_service.py:510-511`).
  - **F7** The Room's RECEIPTS are its own reads ("READ MEETINGS" ×n) (`project_service.py:1933`).
  - **F8** No project write is admitted through the kernel or leaves a kernel receipt. Two lower-level admissions already exist and must be kept, not duplicated: `ensure_meeting_watch` writes a `watch.create` kernel operation (`holdspeak/services/watch_service.py:1642-1649`, reached from `project.link`, `project_service.py:3507-3508`), and a model draft's call is admitted as `inference.invoke`.
  - **F9** `steward.nudges`, `nudge.send` (a GitHub comment) and `nudge.dismiss` build the steward service with `unittest.mock.MagicMock` collaborators in product code (`holdspeak/mcp/tools.py:1177-1191`). Code-read.
  - **F10** At 393 the Ask well covers the Steward verb and the SOURCES heading on first view (`elementFromPoint` hits `room-ask-well`); at 1440 the verb is hit.
  - **F11** The update list heads a published update "DRAFTS 1", its row reads "PUBLISHEDRev 11m agoDeterministic draft", and its emblem is a fixed "E" (`web/src/features/project-room/update/UpdatePosture.tsx:257`, `:268-270`).
  - **F12** The project tool descriptions name mechanisms, not his jobs, and say nothing about where an id comes from.
  - **F13** MCP `desk.needs_you` ignores the muted projects that HTTP applies (`projects.py:546-573` vs `tools.py:1077-1090`). Code-read.
  - **F14** A base install cannot import the MCP catalogue: `holdspeak/operations.py:38` imports `jsonschema`, declared only in the `test` and `dev` extras (`pyproject.toml:85`, `:139`). Prerequisite repair in story 01.
  - **F15 (corrected)** The Room's normal SUGGESTED row has wired Add and Dismiss (`web/src/features/project-room/ProjectRoomCore.tsx:976-1000`); the Button with no action (`:1050`) is on a watch source row whose `src.suggested` is set. Code-read, not rendered.
- **Publication is local.** `publish_update` changes the update's lifecycle, the project revision and the ledgers; it has no recipient and sends nothing (`holdspeak/services/project_update_service.py:1901`); the face offers Copy separately (`UpdatePosture.tsx:580`). Hence Q0.
- **The D2 debts reproduce on main**: `::selection` 1.13:1 at both widths; 51 (1440) and 33 (393) visible text nodes under 12 px in the list, the census and status lines 10 px; "27 SHOWNS OF 27"; at 393 the Kind, Zone and Attention columns are wholly off the right edge; 4 raw sort-header `<button>`s (`web/src/desk/components/DeskSortableTable.tsx:96`); the row menu's Delete cut 15 px at 393, in view at 1440.

## Scope

The job (as Q0 (a), Q1 (a), Q2 (a), Q3 (a) would rule it): **make a project; add a milestone and a risk; see what needs him; let the steward run and draft the update; publish the update in the Room.** "Section Q3 propagation" below states what changes under each other answer.

- **In:**
  1. **Story 01 — the Room's operations on the contract, with discovery words.** Prerequisite: F14 (`jsonschema` in the base dependencies; a clean-install import fence). Descriptors in `holdspeak/operations.py`, bound at hub composition to the hub's `ProjectService`, `ProjectDeltaService` and `ProjectUpdateService`, for the 18 MCP identities of the enumeration (Room lifecycle 9, review 4, updates 4, `desk.needs_you` 1) and the 3 HTTP constructors; the Door's create (`POST /api/projects/door`) as a declared operation beside `project.create`, each classified by its own effect (admission table); the seven new public tools (see "The new public tools"). **Story 01 owns every backend edit in `ProjectService`** for this phase: F6 (the Room read reports updates and the steward), F13 (one needs-you count), and the backend halves of story 03's repairs — health counting a past-due milestone and the milestone in NEEDS YOU (F2, as Q3 rules) and RECEIPTS from the Room's writes (F7). Discovery words (F12): the descriptions name his jobs and where each id comes from; **no description may say or imply that publishing sends or delivers the update** (Q0).
  2. **Story 02 — the steward and the connectors under Article XI.** Precondition: the steward lifecycle beat (below), checked by Codex Astra before build. Descriptors for the 20 MCP identities (steward 5, nudges 3, watches 7, suggested sources 3, connections 2) and the 3 HTTP constructors; the nudges on the hub's service (F9); **source addition with a durable, truthful outcome** (F5, F16, F17): accepting a suggestion leaves a resource AND a watch on the Room, read back; or it is refused with a named reason and the suggestion stays pending — never "accepted" with nothing added; GitHub `owner/repo` references reach the route. Kernel admission, one terminal receipt and refusal receipts for each row the admission table admits, on both transports; agent writes as Q2 rules (F8, F18, F19).
  3. **Story 03 — the Room's face tells the truth (face files; backend from story 01).** F1 (one registered key; every caller moved to it), F2 (the items section as Q3 rules; canvas first), F3 (counts from effect steps; the review COMPARE opened; "no effect allowed" said), F7, F10, F11, F15 (the watch-source branch reproduced, then wired or withheld).
  4. **Story 04 — the desk debts (D2; canvas first for the list face).** The selection token; the list face as the owner ratifies it.
  5. **Story 05 — the atlas: assembly, rerun and equivalence.** Stories 01–04 each ship the active fences and atlas cases for their own repairs; story 05 assembles them into the phase atlas file, reruns every Phase 7, 8 and 9 case at both widths, and runs the api/op/browser equivalence. It authors no new face case.
  6. **Story 06 — the closing use from a cold-context Codex session**, pinned below ("The closing contract").
- **Out (with their homes):**
  - **Delivery of the update to a recipient** (email, chat, a page): BACKLOG "PHILO-9 charter follow-ups", unless Q0 (b).
  - **Migration deferred, still callable:** the setup interview (`project.setup.*`, 10) and the provider discovery tools (`provider.*`, 13) stay hand-wired MCP tools; they remain callable with today's behaviour and authority (the setup tools check OWNER, `holdspeak/services/project_setup_service.py:214` and nine more). Reason: they are not on the job's path (the Door replaced the interview's face, `holdspeak/web/routes/project_door.py:4`; the Door's source rows own provider discovery). Not verifying them on an isolated rig (no accounts) is a limit, not the reason. BACKLOG "PHILO-9 charter follow-ups".
  - The saved asks (`projects.py:92-196`), the Room people read (`projects.py:672`), the briefings and the Prepare posture: the Room's other postures.
  - DESK palette = ALL (BACKLOG "PHILO-7-02 canvas follow-ups"): stays under Q2 (a); under Q2 (b) story 02 repairs it first.
  - The six non-desk kernel two-step terminal writes; the tombstoned Thought's note 500; the Floor rename field clip, the 4.7 s to the field, the rename re-send and the late refusal's lost reason; the rename duplicate; the Follow-through doubled hairline; the guarded right-click rig note; the Workbench footer linger; the 11/10 px rules outside Settings and outside the list; the privacy note: all stay in their BACKLOG homes.
  - The ToolSearch confound (Phase 7 ledger row 9): report only; the closing client is Codex (D3).

### The enumerated identities

Of `docs/internal/philo/phase-5/residual-set.json` at main `b37dc2fb`:

| Story | Transport | Identities | Count |
|---|---|---|---|
| 01 | mcp | `project.list`, `project.get`, `project.get_room`, `project.create`, `project.update`, `project.archive`, `project.restore`, `project.link`, `project.unlink`, `project.open_review`, `project.get_delta`, `project.decide_proposal`, `project.accept_review`, `project.list_updates`, `project.draft_update`, `project.update_draft`, `project.publish_update`, `desk.needs_you` | 18 |
| 01 | http | `projects.py::build_projects_router._build_needs_you` `HeartbeatService`; `automations.py::build_automations_router._project_service` `ProjectService`; `people.py::build_people_router.projects` `ProjectService` | 3 |
| 02 | mcp | `project.configure_steward`, `project.run_steward`, `project.stop_steward`, `project.get_steward_run`, `project.steward.trigger`, `steward.nudges`, `nudge.send`, `nudge.dismiss`, `project.watch.inspect`, `project.watch.test`, `project.watch.evaluate`, `project.watch.set_rules`, `project.watch.pause`, `project.watch.resume`, `project.watch.retire`, `project.suggested_sources`, `project.add_suggested_source`, `project.dismiss_suggested_source`, `connection.list`, `connection.recheck` | 20 |
| 02 | http | `projects.py::build_projects_router.api_suggested_sources`, `.api_add_suggested_source`, `.api_dismiss_suggested_source` `SuggestedSourceService` | 3 |

**38 MCP + 6 HTTP.** Residual 284 → **240** (all 44 paid) to **246** (the 38 MCP only; an HTTP construction that stays for the route tests MOVES and is not paid). New public tools raise the public tool count (229 → 236 with the seven below); reported apart.

### The new public tools (ratified here, not in a first commit)

New MCP exposure for capabilities the hub already has over HTTP. Names under `project.*`, so `PROJECT_PALETTE` (every tool of `holdspeak/mcp/families/project.py`, `:2098`) and therefore `SWEEP` hold them; `DESK`/`ALL` hold every tool. The receipt read reuses Phase 7's `kernel.receipt`; `kernel.receipt` is added to `PROJECT` and `SWEEP` (palettes only gain tools, `holdspeak/mcp/palettes.py:1-5`).

| Tool | Arguments (JSON Schema, `additionalProperties: false`) | Result | Named refusals | Service (existing) | Authority (Q1 (a), Q2 (a)) |
|---|---|---|---|---|---|
| `project.item.list` | `project_id` (req); `item_type` ∈ {milestone, risk, dependency, workstream, signal}; `limit` ≤ 200; `offset` | `{items, total}` as `GET /api/projects/{id}/items` | `project_not_found`, `invalid_arguments` | `ProjectService.list_items` (`project_service.py:4243`) | read: palette |
| `project.item.create` | `project_id`, `item_type`, `title` (req); `summary`, `severity`, `owner_ref`, `due_at` (ISO date), `lifecycle`; `details` per type (risk: `likelihood`, `impact` req, `mitigation`; dependency: `direction`, `counterpart_ref` req; signal: `metric` req; `project_service.py:215-240`); `expected_revision`; `command_id` | `{item}` + envelope | `invalid_item_type`, `details_invalid`, `stale_revision`, `project_not_found` | `create_item` (`:3628`) | exempt: palette |
| `project.item.update` | `project_id`, `item_id`, `patch` (req); `expected_revision`; `command_id` | `{item}` | as create; a milestone cannot reach `reached` here (`:4112-4116`) | `update_item` (`:3947`) | exempt: palette |
| `project.item.transition` | `project_id`, `item_id`, `verb` (the target lifecycle, req); `expected_revision`; `command_id` | `{item}` | `invalid_lifecycle`, `stale_revision`, `project_item_not_found` | `transition_item` (`:4106`) | exempt: palette |
| `project.resource.list` | `project_id` (req) | `{resources}` | `project_not_found` | `list_resources` (`:374`) | read: palette |
| `project.resource.add` | `project_id`, `resource_ref` (req); `relationship` ∈ {member, source, output, related}; `expected_revision`; `command_id` | `{resource}` | `unknown_resource_kind`, `unknown_relationship`, `stale_revision` | `add_resource` (`:3169`) | admitted (filing) |
| `project.resource.remove` | `project_id`, `resource_ref` (req) | `{removed}` | as add | `remove_resource` (`:3286`) | admitted (unfiling) |

### The admission table (Q1 (a), every in-scope identity)

"Admitted" = one kernel operation before it acts and one terminal receipt, on both transports, with refusal receipts (Phase 7 R2). "Exempt" = a plain edit or a read (Article XI.5). A row with an existing lower-level admission keeps it and is not admitted twice: the existing operation becomes a child of the row's operation, or the row is admitted by that operation alone (the steward beat and story 01 decide which, per row, and record it). Under Q2 (a) an AGENT calling an admitted row is refused `delegation_required` with a refusal receipt; exempt rows and reads keep today's palette behaviour.

| Operation | Arguments that change the effect | Effect (read from the code) | Admission |
|---|---|---|---|
| `project.list`, `get`, `get_room`, `get_delta`, `list_updates`, `get_steward_run`, `steward.nudges`, `watch.inspect`, `suggested_sources`, `connection.list`, `desk.needs_you`, `item.list`, `resource.list` | — | reads | none |
| `project.create` (bare) | — | a project row, revision, change, event; no watch (`project_service.py:2342-2433`) | exempt |
| Door create (`POST /api/projects/door`) | `sources` | a project, and for each source an armed watch that reads GitHub/Jira on a schedule, then a baseline read (`holdspeak/services/project_door_service.py:300-315`) | admitted when any source is given (egress); exempt without sources |
| `project.update` | `patch` | fields; `lifecycle: archived` is refused (`project_service.py:2747-2757`) | exempt |
| `project.archive` | — | archived, AND the project's watches paused AND unattended steward runs turned off, one transaction (`:3023-3035`; F18) | admitted (changes authority, stops scheduled egress) |
| `project.restore` | — | lifecycle active; does not resume watches or unattended runs (`:3060-3168`) | exempt |
| `project.link` | `meeting_id` | files a meeting in the Room; ensures a meeting watch, already a `watch.create` kernel operation (`:3507-3508`, `watch_service.py:1642-1649`) | admitted (filing); the `watch.create` operation is its child, not a second top-level admission |
| `project.unlink` | `meeting_id` | unfiles the meeting | admitted (unfiling) |
| `project.open_review` | — | freezes a local review window | exempt |
| `project.decide_proposal` | `verb` | `accept`/`edit_accept` write the proposal into the Room; `defer`/`dismiss` change only its state | admitted for `accept`, `edit_accept` (decides); exempt for `defer`, `dismiss` |
| `project.accept_review` | — | accepts the window, bumps the revision, supersedes undecided proposals | admitted (decides) |
| `project.draft_update` | `generator` | a draft; `model` calls a model, already admitted as `inference.invoke` | exempt (the model call keeps its own admission) |
| `project.update_draft` | `body_md` | the draft's text | exempt |
| `project.publish_update` | — | the update becomes read-only and published in the Room; revision and ledgers (`project_update_service.py:1901`); sends nothing | admitted (may be irreversible: a published update is read-only) |
| `project.configure_steward` (write) | any policy field | `enabled`, `unattended_enabled` (a delegation), `eligible_effect_kinds`, bounds | admitted (changes authority) |
| `project.run_steward` | — | a run: OBSERVE, COMPARE (opens a review), PROPOSE, ACT (each eligible effect: `refresh_sources`, `create_proposals`, `apply_proposal_effects`, `draft_update`, `create_door_item`, `github_comment`) | admitted; each executed effect a child operation (XI.2); `github_comment` crosses egress |
| `project.stop_steward` | `run_id` | a durable stop on a run | admitted (controls a process) |
| `project.steward.trigger` | — | evaluates due watches and runs due steward work now | admitted (controls a process); its runs are children |
| `nudge.send` | `step_id`, `text` | a GitHub comment | admitted (egress) |
| `nudge.dismiss` | `step_id` | the nudge's state only | exempt |
| `project.watch.test` | — | fetches the source (egress) and persists `test_state`/`test_result_json` (`watch_service.py:499`, `:595-600`) | admitted (egress) |
| `project.watch.evaluate` | — | snapshot, diff, transitions; records effects the steward can act on | admitted (egress) |
| `project.watch.set_rules` | `rules`, cadence | what the watch does and how often | admitted (changes what may act) |
| `project.watch.pause`, `resume`, `retire` | — | stops or starts scheduled source reads | admitted (controls a process) |
| `project.add_suggested_source` | `reference` | a resource and a watch on the Room, or a named refusal with the suggestion pending (story 02) | admitted (filing; arms egress) |
| `project.dismiss_suggested_source` | `reference` | the suggestion never shows again | exempt |
| `connection.recheck` | `provider_id`, `ref` | probes the provider (egress) and stores the check time | admitted (egress) |
| `project.item.create`, `update`, `transition` | — | the owner's own records in the Room | exempt |
| `project.resource.add`, `remove` | `relationship` | files or unfiles a thing in the Room | admitted (filing) |

### Q3 propagation

| | Q3 (a) items shown, entry over owner-authenticated MCP (recommended) | Q3 (b) as (a) plus an in-world Add control | Q3 (c) no items on the face |
|---|---|---|---|
| Story 01 | the item tools; health and NEEDS YOU count a past-due milestone | as (a) | the item tools stay (F4); no health or NEEDS YOU change |
| Story 03 | the items section (canvas); no Add control | the items section and one Add control (canvas shows both) | no items section; F2 is recorded as a known gap on the BACKLOG |
| Discovery words | "add a milestone / risk to a project" → `project.item.create` | as (a) | as (a) (the tools exist) |
| Story 06 job | add a milestone and a risk over MCP; the face shows both and the overdue milestone in NEEDS YOU | as (a); the face leg adds nothing (the closing client is MCP) | link a meeting and add a resource; the attention item is the review the steward's COMPARE opened, IF it shows in NEEDS YOU on the rig before the run — else (c) cannot meet exit 8 and the owner is told |
| BACKLOG | "add item on the face" home | none | "items on the face" home |

Under Q3 (a) the only item-entry path this phase proves is owner-authenticated MCP (and the existing HTTP route). No voice or agent path is promised.

### The steward lifecycle beat (a precondition of story 02)

The steward runs asynchronously: the route and the tool insert a run and return its id, then a daemon thread executes the phases (`holdspeak/web/routes/steward.py:94`; `project.py:1554-1633`). Phase 7's synchronous completion does not carry over. Before story 02 builds, a short design beat (like Phase 7's `design/grant-lifecycle-beat.md`), checked by Codex Astra, fixes:

1. **The pending handle:** the call returns `run_id` and the run's `operation_id` at once; the operation is non-terminal while the run works.
2. **Parentage:** each executed effect is a child operation of the run's operation; a scheduler-started run (`steward.trigger`, `run_due`, unattended) names its principal and authority basis (the owner's recorded policy).
3. **The terminal receipt:** exactly one per run — completed, failed, stopped or indeterminate — written in the same step that ends the run.
4. **Stop:** `project.stop_steward` is admitted; the stopped run ends with its own terminal receipt.
5. **Recovery:** after a hub restart with a run in flight, the run ends terminal (indeterminate or failed) with its receipt; no run or operation stays non-terminal. Fenced with a real restart (the Phase 7 F13 pattern).

### HTTP capability exceptions (Room routes that stay HTTP-only this phase, and why)

| Route | Line | Does | Why HTTP-only | Authority this phase |
|---|---|---|---|---|
| `POST /api/updates/{id}/regenerate` | `holdspeak/web/routes/project_updates.py:134` | regenerates a draft; `generator=model` calls a model | a face verb (Regenerate); the job drafts through `project.draft_update` | the model call's `inference.invoke`; otherwise exempt (a draft) |
| `GET /api/updates/{id}/markdown` | `project_updates.py:195` | the update as Markdown | presentation/export read | none |
| `POST /api/projects/door/count` | `holdspeak/web/routes/project_door.py:38` | counts for the Door's source rows | the Door's own read | none |
| `POST /api/projects/{id}/room/read` | `projects.py:55` | the Room's "read" marker | presentation state | none |
| `GET …/briefings`, `/meetings`, `/summary`, `/action-items`, `/artifacts`, `/since-last-meeting`, `/people`; `GET /api/meetings/{id}/projects`; `GET /api/desk/relationships/{ref}` | `projects.py:37,285,373,382,391,400,672,364,327` | reads the Room's face or other postures use | covered by `get_room`, or another posture | none |
| `POST/GET …/ask-tasks` | `projects.py:92-196` | the saved asks | the Ask posture (Out) | unchanged |
| `GET /api/projects/{id}/reviews/{review_id}` | `holdspeak/web/routes/project_reviews.py:63` | one review | `get_delta` covers the open one | none |
| `GET /api/projects/{id}/steward/runs` | `holdspeak/web/routes/steward.py:151` | the run history | the face's history list; `get_steward_run` covers one run | none |
| `GET /api/watches`, `GET /api/projects/{id}/watches` | `holdspeak/web/routes/watches.py:40,56` | watch lists | `get_room` sources cover the Room's | none |
| `PATCH /api/watches/{id}`, `POST /api/watches/{id}/baseline` | `watches.py:89,141` | update a watch spec; baseline read (egress) | the Door and the face's own edits | admitted on the route per the table's watch rows (Article XI applies on every transport) |

## Exit criteria (evidence required)

The red-first law for this phase (Codex Astra r1 F8): **behavioural red** at each state and width a defect affects, through the real hub on an isolated HOME with real producers; **preservation green** at the states and widths it does not affect; **deliberate mutations** for structural invariants. A missing symbol, an unknown tool or an import error is never counted as a red. New public exposure has no red; its proof is equivalence of durable outcome and refusals with the existing HTTP route. The grounding is diagnostic, not a fence: each story writes the executable failing assertion. Existing atlas words change in the same commit as the product change. Receipts are fenced as rendered after each transition.

| Seam | 1440 | 393 | Kind |
|---|---|---|---|
| F1 the Room from a meeting's project button (and one caller per face) | red | red | behavioural |
| F2 a past-due milestone shown, health turned (Q3 (a)/(b)) | red | red | behavioural |
| F3 steward counts equal the run; the review shown; "no effect allowed" | red | red | behavioural |
| F7 RECEIPTS are writes | red | red | behavioural |
| F10 the Steward verb hit at its centre | preservation green | red | behavioural |
| F11 the update list words | red | red | behavioural |
| D2 selection ≥ 3:1 | red | red | behavioural (measured) |
| D2 list text ≥ 12 px, "SHOWN" | red | red | behavioural |
| D2 every kept column in view | preservation green | red | behavioural |
| D2 row menu in view near the bottom | preservation green | red | behavioural |
| D2 sort headers are the library Button | red | red | structural (a mutation re-adding a raw `<button>` turns it red) |
| F5/F16/F17 source addition: resource + watch, or named refusal with the suggestion pending | red (API) | — | behavioural |
| F6, F13 the Room read; one needs-you count | red (API) | — | behavioural |
| F8/F18/F19 admission and agent refusals | red (API) | — | behavioural, authenticated principal; mutations |
| F9 no `unittest.mock` in `holdspeak/` | — | — | structural (AST fence; mutation) |
| F14 a base install imports `holdspeak.mcp.tools` | red | — | behavioural (a clean venv) |
| the residual set; one `project-room` registration | — | — | structural (census on a copy of main; a caller census; mutations) |

- [ ] 1. **The residual set shrank by the enumerated identities** (38 MCP; the 6 HTTP only where the construction left), by `(transport, entry point, discriminator)`; the fence fails on a new residual identity on a copy of main. Evidence: `scripts/residual_census.py --check`; `residual-set.json` `paid`.
- [ ] 2. **The job is discoverable and executable over MCP alone.** A fence reads only the real `tools/list` answer and maps "make a project", "add a milestone / risk to a project" (Q3 (a)/(b)), "what needs me", "let the steward run", "draft my update" and "publish my update in the Room" to a tool and an argument path; no description says or implies send or deliver for publication. Every in-scope operation reaches the same declared operation and live service by route, MCP and the rig's `op` step. The seven new tools match the table above (schema, palette, refusals), and their durable outcomes and refusals equal the HTTP route's. Evidence: the discovery fence; the equivalence run.
- [ ] 3. **Every Room read says what exists, and source addition is truthful.** `get_room` reports a published update and a completed steward run; one needs-you count with a muted project; no `unittest.mock` in product code; accepting a GitHub (`owner/repo`) and a Jira suggestion leaves a resource and a watch, read back — or is refused with a named reason and the suggestion stays pending (red on main: 404; 200 `accepted_no_watch` with nothing added, P1). Evidence: API fences through the real hub.
- [ ] 4. **Article XI as Q1 rules and Q2 as ruled.** Each admitted row of the admission table is one kernel operation with one terminal receipt on both transports; each refusal class leaves its receipt; exempt rows and reads leave none; no duplicate admission where a lower-level admission exists; the steward beat's five points fenced, including a real restart; under Q2 (a) an agent's admitted write is refused `delegation_required` with a receipt (red on main: P3 succeeded with zero rows). Under Q1 (c) this exit is NOT MET, recorded as constitutional debt. Evidence: admission fences with an authenticated principal and their mutations.
- [ ] 5. **The Room's face shows the job**, per the matrix rows F1, F2, F3, F7, F10, F11, and the owner-ratified items canvas under Q3 (a)/(b). Evidence: glass fences and shots.
- [ ] 6. **The D2 debts are paid as the owner ratified the list canvas**, per the matrix D2 rows; the web baseline has zero branch-new. Evidence: glass fences; the canvas ratification.
- [ ] 7. **The assembled atlas passes**: every Phase 9 case (shipped by stories 01–04) green at both widths on the phase head, with the red-first record each story kept; the Phase 7 and Phase 8 cases still pass; the api/op/browser equivalence holds. Evidence: story 05's rerun.
- [ ] 8. **The closing use** meets "The closing contract" below: each fixed expectation read back from the hub and shown on the Room's face at 1440 and 393; "find it cold"; zero repository reads; the owner reviews the shots. Never recorded as a sitting.

## The closing contract (story 06; fixed before the run)

- **Launch:** `scripts/philo7_file_and_find.py` (or a sibling) with `--client codex --legs owner` (the driver's defaults are `claude` and `owner,agent`, `scripts/philo7_file_and_find.py:1538-1542`). An OWNER-token run proves OWNER behaviour only; agent refusals are proved by story 02's fences.
- **Isolation:** two sessions, each with its own fresh scratch directory, `HOME` and `CODEX_HOME` (only `auth.json`), distinct session ids, no resumed transcript; `--ignore-user-config --ignore-rules --disable apps --disable plugins`; no preamble; the isolated hub the only MCP server. The complete initial context of each session is retained; the client's event log is reconciled with the hub's recorded exchanges; zero repository reads (a repository resource read is a read); the zero-read fence fails on the Phase 5 logs; redaction at capture and its leak fence.
- **The fixture (written to the story's fixture file before the run; Q3 (a) shown):**
  - Project: "Payments ledger cutover".
  - Milestone: "Cutover rehearsal", `due_at` = the run date minus 3 days, lifecycle `planned`.
  - Risk: "Old ledger freeze slips", `likelihood` "medium", `impact` "high", `mitigation` "Freeze the schema by Friday".
  - Expected attention: NEEDS YOU lists "Cutover rehearsal" as overdue (the words the ratified canvas fixes) and health is not ON TRACK.
  - Steward: the owner leg sets the policy `eligible_effect_kinds: ["draft_update"]` (admitted), runs the steward; expected: the run completes; COMPARE's review exists; ACT drafts one update (`_effect_draft_update`, `project_steward_service.py:1339`); the face's counts equal the run.
  - Publication: the client publishes that draft; readback: lifecycle `published`, read-only, and the body names "Cutover rehearsal" and "Old ledger freeze slips".
  - Find it cold: the second session gets only "Payments ledger cutover" in the owner's words, finds the project and reads its published update.
  - Each expectation is confirmed reachable on the rig before the run; one that is not goes back to its story, never softened in the fixture.
- **Checks are on content:** each readback compares the fixture's values (titles, dates, lifecycle, counts, receipt ids), not a success flag.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-9-01 | The Room's operations on the contract (and discovery) | backlog | [story-01-the-rooms-operations-on-the-contract](./story-01-the-rooms-operations-on-the-contract.md) | — |
| PHILO-9-02 | The steward and the connectors under Article XI | backlog | [story-02-the-steward-and-the-connectors-under-article-xi](./story-02-the-steward-and-the-connectors-under-article-xi.md) | — |
| PHILO-9-03 | The Room's face tells the truth (canvas first) | backlog | [story-03-the-rooms-face-tells-the-truth](./story-03-the-rooms-face-tells-the-truth.md) | — |
| PHILO-9-04 | The desk debts: the selection and the list face (canvas first) | backlog | [story-04-the-desk-debts](./story-04-the-desk-debts.md) | — |
| PHILO-9-05 | The atlas: assembly, rerun and equivalence | backlog | [story-05-the-atlas-cases-for-the-room](./story-05-the-atlas-cases-for-the-room.md) | — |
| PHILO-9-06 | Work in a project room without the repo (Codex) | backlog | [story-06-work-in-a-project-room-without-the-repo](./story-06-work-in-a-project-room-without-the-repo.md) | — |

The stories stay `backlog` until the owner ratifies the charter.

## Lanes (proposed)

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The contract | 01 → (beat) → 02 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Codex Astra | ../wt-philo-9-01, ../wt-philo-9-02 | feat/philo-9-01-room-contract, feat/philo-9-02-steward-connectors |
| The Room's face | 03 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Codex Astra | ../wt-philo-9-03 | feat/philo-9-03-room-face |
| The desk debts | 04 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Codex Astra | ../wt-philo-9-04 | feat/philo-9-04-desk-debts |
| The atlas and the closing use | 05 → 06 | Astra (Luna) | Muad'Dib | ../wt-philo-9-05, ../wt-philo-9-06 | feat/philo-9-05-atlas, feat/philo-9-06-room-without-the-repo |

Ownership: story 01 owns `holdspeak/services/project_service.py`, `holdspeak/operations.py`, `holdspeak/mcp/families/project.py`, `holdspeak/mcp/tools.py` and the generated files; story 02 takes them after 01 merges. Story 03 owns the Room's face files only (`web/src/features/project-room/`, the `project-room` callers) and consumes story 01's backend (health, NEEDS YOU, RECEIPTS, the Room read); a backend change story 03 finds is handed to story 01's lane by patch, not co-edited. Story 04 owns `web/src/styles/global.css` and the list files. 03 and 04 run beside 01/02; 05 starts after 01–04 merge; 06 last. A lane runs its scoped fences and rig cases only; the full suite is CI's job on the PR.

## Where we are

2026-09-27: DRAFTED from the owner's rulings D1–D3, the BACKLOG row "Projects on the contract", the Phase 8 ledger and the grounding on main `b37dc2fb` (`docs/internal/philo/phase-9/grounding/README.md`).

2026-09-27, round two: Codex Astra r1 DO-NOT-RATIFY (`checks/charter-astra-r1.md`), paid on Muad'Dib's rulings. The three probes reproduced on a fresh isolated HOME (grounding "Round two"): P1 GitHub 404 / Jira `accepted_no_watch` with nothing added (F16, F17; `qualified_ref` refuses both kinds, and a successful add writes no watch); P2 archive turns unattended runs off (F18); P3 a PROJECT credential without a grant turns unattended runs on and archives (F19); zero kernel rows in each. F3 and F15 corrected. Owed: Codex Astra r2; the owner's ratification and Q0–Q3; the steward lifecycle beat before story 02; the items canvas (Q3 (a)/(b)) and the list canvas before their face builds. Nothing is built.

**Estimate (PROVISIONAL; not grounded per story):** effort **10–15 engineering days** — 01 2.5–3.5 (18 descriptors, 7 new tools, the Door declared, F14, the backend of F2/F6/F7/F13, the discovery words); the steward beat 0.5; 02 3.5–4.5 (20 descriptors, the admission table, the async lifecycle, source addition end to end, the nudges without doubles); 03 1.5–2.5 (face repairs, the items canvas); 04 1–1.5; 05 0.5–1 (assembly and rerun only); 06 about 1. Calibration: Phase 7's 11–15 d estimate closed in about two elapsed days; Phase 8's 2.5–4 d in about a day and a half, most of it check rounds. **Elapsed forecast: about 4–6 days**, gated by the beat, two canvases, the Codex rounds and the owner's word. Re-stated after story 01 lands.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope creep into the setup interview, provider discovery or the Room's other postures | high | the enumeration and the exceptions inventory are the whole scope | a story edits `project_setup_service.py`, a `provider.*` branch or the Prepare/Ask postures |
| A universal CRUD or discovery framework instead of explicit rows | medium | one descriptor row per operation (Phase 7 settled); the seven new tools as tabled | a generic "project entity" layer, or descriptors generated from the route table |
| Admission that changes authority by accident, or admits twice | medium | the admission table is the rule; lower-level admissions become children; boundary fences with an authenticated principal | a write refused that was allowed on main without a ruling; two top-level operations for one act |
| "Accepted" without a source again | medium | exit 3 reads the resource and the watch after every accept, and the pending suggestion after every refusal | an accept path that returns 200 with no watch |
| The job passes on empty outcomes | medium | the closing fixture fixes the attention item, the steward's draft and the publication content before the run | a readback that checks a success flag, not the fixture's values |
| The Room's key repaired in one caller, not all eight | medium | one registration and a caller census (handover XXX law 9) | a `project-room` caller left with a non-route fallback |
| The closing client uses the repository | low | the isolation contract; the zero-read fence red on the Phase 5 logs | a repository read in a retained log |
| Retained sessions carry account data | medium | redact at capture; leak fence (handover XXX law 12) | an address or token in a tracked file |

## Decisions for the owner

- **Q0 — "Where does the job end?"** **Recommended: (a).**
  - (a) At "draft and publish the update in the Room". Publishing makes it the Room's record (read-only); it does not send it to anyone; I copy it where I need it. Delivery goes on the BACKLOG. *(Publish sends nothing today, `project_update_service.py:1901`; the face offers Copy.)*
  - (b) Real delivery: the update reaches a recipient (a channel and an address I name). Larger: a new egress path, its admission and its canvas.
- **Q1 — "Which project writes go through the kernel with a receipt?"** **Recommended: (a).**
  - (a) The rows marked "admitted" in the admission table: writes that decide, file, change authority, control a process, cross egress or cannot be undone — including Archive (it turns off unattended runs and pauses watches) and a watch test (it reads the source and keeps the result). Plain edits and reads go without. No act is admitted twice.
  - (b) Every project write.
  - (c) None in this phase. This is migration only, carrying constitutional debt: it cannot meet the Article XI exit (exit 4 stays NOT MET), and the steward keeps acting with no kernel receipt.
- **Q2 — "What may an agent do in my projects?"** Today an agent with a PROJECT credential can turn on unattended steward runs and archive a project with no grant (F19). **Recommended: (a).**
  - (a) The owner executes consequential project writes; an agent calling an admitted row is refused by name (`delegation_required`) with a receipt. Reads and exempt edits keep today's behaviour. This changes behaviour, and your answer ratifies the change.
  - (b) Bounded project delegation: extend the Phase 7 grant to the admitted project rows, with an agent leg in the closing use; DESK palette = ALL repaired first.
- **Q3 — "Where do I see the things in my project?"** Today a milestone or a risk is stored but the Room never shows it (F2). **Recommended: (a).** Each answer's effect on the stories: "Q3 propagation".
  - (a) The Room shows its items in one section and counts a late milestone in health and NEEDS YOU; items are added through owner-authenticated MCP (and the existing HTTP route); canvas first.
  - (b) As (a), plus a small in-world Add control; the canvas shows both.
  - (c) No items on the face; the job's "thing" is a linked meeting or a resource.

## Round two: Codex Astra r1, paid

| r1 | Finding | Paid |
|---|---|---|
| F1 | Publish does not deliver | Q0 (recommended: local publication); "send" removed from the job, the discovery phrases and story 06; discovery fence forbids send/deliver words for publication; delivery on the BACKLOG |
| F2 | Source addition deeper than F5; F15 wrong | P1 reproduced (F16, F17, plus: `qualified_ref` refuses both kinds; a successful add writes no watch); exit 3 is a durable truthful outcome; F15 corrected |
| F3 | Q1 blanket "plain edit" | the admission table for every in-scope identity; archive (F18, reproduced), `watch.test` (persists), bare vs Door create classified by effect; lower-level admissions kept, no duplicates; Q1 (c) described as constitutional debt that cannot meet exit 4 |
| F4 | Q2 (a) preserved agent authority change | P3 reproduced (F19); Q2 restated: owner execution + named refusals (ratifies the behaviour change) vs bounded delegation |
| F5 | Q3 does not propagate; job outcome thin; F3 too broad | "Q3 propagation" table; (a) names owner-authenticated MCP as the item-entry path; the closing fixture names the attention item and the steward's draft; F3 restated (COMPARE opens a review; ACT none) |
| F6 | Census right; not a capability inventory | kept; "migration deferred, still callable" for setup/provider tools; "HTTP capability exceptions" inventory |
| F7 | Tenet 1 cost placement | stories 01–04 ship their own fences and cases; story 05 assembles, reruns and runs equivalence; the seven new tools tabled; the steward lifecycle beat; backend ownership assigned to story 01 |
| F8 | Blanket red-first false | the state/width matrix; missing-symbol / unknown-tool reds excluded; new exposure proved by equivalence |
| F9 | Closing launch not pinned | "The closing contract": `--client codex --legs owner`, fresh homes and sessions, no resume, name-only find-it-cold, full context, event/hub reconciliation, fixture before the run, content checks |
| MISSED 4 | F14 unassigned | a prerequisite repair in story 01 with a clean-install fence |

## Decisions made (this phase)

- 2026-09-27 — the owner: D1 "Work in a project room"; D2 "Yes, one bounded story"; D3 Codex closes it (AskUserQuestion).
- 2026-09-27 — DRAFTED: six stories; 38 MCP + 6 HTTP identities; the grounding on main `b37dc2fb` — Fedaykin docs lane for Muad'Dib.
- 2026-09-27 — round two on Muad'Dib's rulings, paying Codex Astra r1: Q0 added; the admission table; Q2 restated; Q3 propagated; the new-tool contracts, the exceptions inventory, the steward beat, the red-first matrix, the closing contract; F14 into story 01 — Fedaykin docs lane for Muad'Dib.

## Decisions deferred

- Q0–Q3: the owner, at ratification.
- Per admitted row with a lower-level admission (link's `watch.create`, a model draft's `inference.invoke`): child operation or sole admission — story 01 / the steward beat, recorded and checked.
- The items section's words and seat, and the list face: their canvases, ratified by the owner before each face build.
- The phase atlas file (`atlas-phase9.json` or an existing file): story 01's first case fixes it against the atlas schema.

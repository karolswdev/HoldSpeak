# PHILO Phase 9 grounding — the census and the project job, walked on real metal

Written 2026-09-27 by the Fedaykin docs lane (Opus 5.5) for Muad'Dib, for the Phase 9 charter
(`pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md`).
Nothing here is built. Every finding below was seen on a real hub or is marked "code-read".

## How it was run

- **Commit:** main `b37dc2fb` (the worktree HEAD; `git rev-parse HEAD origin/main` equal).
- **Hub:** the rig's real hub (`scripts/graph_walk.py serve --scheduler`: a real `MeetingWebServer`, the database
  owner lock, the intelligence drainer, the heartbeat conductor), on an isolated HOME made by `mktemp -d`
  (`probes/iso.sh.txt`). The database path the hub printed was under that HOME. The owner's HOME and database were
  not touched.
- **MCP leg:** `probes/mcp_walk.py.txt` through `POST /api/mcp` with the owner token: `initialize`, `tools/list`,
  then the job. Every request and answer: `mcp/mcp-walk.jsonl`; the catalogue: `mcp/tools-list.json`; the project
  descriptions: `mcp/tools-project-descriptions.json`; one line per step: `mcp/summary.json`.
- **Face leg:** Playwright Chromium at 1440x900 and 393x852 (`probes/face_*.py.txt`, `probes/open_room_probe.py.txt`).
  Shots and logs under `face/`. Each log keeps the visible buttons, the text, and every non-GET request the page sent.
- **D2 leg:** `probes/d2_probe.py.txt`, `probes/menu_probe.py.txt`; shots and numbers under `d2/`.
- **Kernel read-back:** read-only `sqlite3` on the isolated database after the walk.

## The census (counting rules of Phase 5 and Phase 7)

`uv run --extra test python scripts/residual_census.py --check` under an isolated HOME at `b37dc2fb`:
`RESIDUAL FENCE GREEN: 284 identities match`. The ledger (`docs/internal/philo/phase-5/residual-set.json`
`measurements`): 284 = **223 MCP + 61 HTTP**; public tools **229** (`tools/list` returned 229).

The counting rule, verbatim from the ledger: "mcp: every assembled tool dispatched by hand, desk.* split by kind and
desk.verb by verb and kind, minus the identities an operation descriptor exposes; http: every syntactic
*Service(...) construction in holdspeak/web/routes, keyed by module::function".

The project identities, by name. "Writes" is what the callable does to durable state. "Authority today" is what
checks the caller: the palette (a credential's allow-list, `holdspeak/mcp/palettes.py:40-54`) and any check inside
the service. **No project write is admitted through the kernel** (see F8).

### MCP `project.*` — 42 (all in `holdspeak/mcp/families/project.py`, `dispatch` at `:1152`)

| # | Identity | Real callable (line) | Writes | Authority today | Class |
|---|---|---|---|---|---|
| 1 | `project.list` | `ProjectService.list_projects` (`:1170`) | no | palette | read |
| 2 | `project.get` | `ProjectService.get_project` (`:1177`) | no | palette | read |
| 3 | `project.get_room` | `ProjectService.room` (`:1181`) | no | palette | read (the Room) |
| 4 | `project.create` | `ProjectService.create_project` (`:1188`) | yes | palette | Room lifecycle |
| 5 | `project.update` | `ProjectService.update_project` (`:1198`) | yes | palette | Room lifecycle |
| 6 | `project.archive` | `ProjectService.archive_project` (`:1212`) | yes: also pauses the project's watches and turns unattended steward runs off in the same transaction (`project_service.py:3023-3035`; probe P2) | palette | Room lifecycle |
| 7 | `project.restore` | `ProjectService.restore_project` (`:1225`) | yes | palette | Room lifecycle |
| 8 | `project.link` | `ProjectService.associate_meeting` (`:1241`) | yes (files a meeting in the Room) | palette | Room lifecycle |
| 9 | `project.unlink` | `ProjectService.disassociate_meeting` (`:1254`) | yes | palette | Room lifecycle |
| 10 | `project.open_review` | `ProjectDeltaService.open_review` (`:1270`) | yes (opens a review window) | palette | review |
| 11 | `project.get_delta` | `ProjectDeltaService._find_open_review` + route glue (`:1276-1313`) | no | palette | review read |
| 12 | `project.decide_proposal` | `ProjectDeltaService.decide_proposal` + copied route glue (`:1315-1344`) | yes (decides) | palette | review |
| 13 | `project.accept_review` | `ProjectDeltaService.accept_review` (`:1346`) | yes (decides) | palette | review |
| 14 | `project.list_updates` | `ProjectUpdateService.list_updates` (`:1360`) | no | palette | update read |
| 15 | `project.draft_update` | `ProjectUpdateService.draft_update_command` (`:1370`) | yes; `generator=model` calls a model | palette | update |
| 16 | `project.update_draft` | `ProjectUpdateService.save_update` (`:1382`) | yes | palette | update |
| 17 | `project.publish_update` | `ProjectUpdateService.publish_update` (`:1400`) | yes | palette | update |
| 18 | `project.configure_steward` | the steward-policy DB layer, direct (`:1419-1552`) | read, or write when a field is given (incl. `unattended_enabled`, a delegation) | palette | steward verb |
| 19 | `project.run_steward` | `ProjectStewardService.insert_run` + a daemon thread `execute_phases` (`:1554-1633`) | yes; its effects may include `github_comment` (egress) | palette + the steward policy | steward verb |
| 20 | `project.stop_steward` | `ProjectStewardService.stop` (`:1635`) | yes | palette | steward verb |
| 21 | `project.get_steward_run` | steward-run DB layer (`:1646`) | no | palette | steward read |
| 22 | `project.steward.trigger` | `evaluate_due` + `run_due` via the conductor seam (`:1660-1701`) | yes | palette | steward verb |
| 23 | `project.setup.start` | `ProjectSetupService.start_setup` (`:1706`) | yes | OWNER (`project_setup_service.py:214`) | setup interview (parked face) |
| 24 | `project.setup.resume` | `ProjectSetupService.get_setup` (`:1711`) — takes no principal | no | palette only | setup interview |
| 25 | `project.setup.answer` | `ProjectSetupService.answer` (`:1717`) | yes | OWNER (`:287`) | setup interview |
| 26 | `project.setup.suggest` | `ProjectSetupService.suggest` (`:1727`) | yes | OWNER (`:340`) | setup interview |
| 27 | `project.setup.finalize` | `ProjectSetupService.finalize` (`:1734`) | yes (makes a project and watches) | OWNER (`:662`) | setup interview |
| 28 | `project.setup.clarify_jira_scope` | `ProjectSetupService.clarify_jira_scope` (`:1744`) | yes | OWNER (`:1183`) | setup interview |
| 29 | `project.setup.select_proposal` | generic `getattr` (`:1155-1166`) | yes | OWNER (`:472`, and `:1158`) | setup interview |
| 30 | `project.setup.deselect_proposal` | generic `getattr` (`:1155-1166`) | yes | OWNER (`:492`) | setup interview |
| 31 | `project.setup.test_proposal` | generic `getattr` (`:1155-1166`) | yes (a real source read) | OWNER (`:555`) | setup interview |
| 32 | `project.setup.clarify_repo_scope` | generic `getattr` (`:1155-1166`) | yes | OWNER (`:1020`) | setup interview |
| 33 | `project.watch.inspect` | `WatchService.get_watch` (`:1975`) | no | palette | connector read |
| 34 | `project.watch.test` | `WatchService.test_watch` (`:1982`) | yes: fetches the source and persists `test_state` / `test_result_json` (`watch_service.py:595-600`; round two, Codex Astra r1 F3) | OWNER (`watch_service.py:488`) | connector |
| 35 | `project.watch.evaluate` | `WatchService.evaluate_once` (`:1989`) | yes | OWNER (`:952`) | connector |
| 36 | `project.watch.set_rules` | `WatchService.set_rules` + direct cadence write (`:1997-2016`) | yes | OWNER (`:1391`) | connector |
| 37 | `project.watch.pause` | `WatchService.pause_watch` (`:2018`) | yes | OWNER (`:425`) | connector |
| 38 | `project.watch.resume` | `WatchService.resume_watch` (`:2025`) | yes | OWNER (`:438`) | connector |
| 39 | `project.watch.retire` | `WatchService.retire_watch` (`:2032`) | yes | OWNER (`:459`) | connector |
| 40 | `project.suggested_sources` | `SuggestedSourceService.list_suggestions` (`:2041`) | no | — (fails on every call, F5) | connector read |
| 41 | `project.add_suggested_source` | `accept_suggestion` + `ProjectService.add_resource` (`:2047`) | yes | — (fails, F5) | connector |
| 42 | `project.dismiss_suggested_source` | `dismiss_suggestion` (`:2066`) | yes | — (fails, F5) | connector |

### MCP connectors in the same module — 15

`provider.list`, `provider.github_connection`, `provider.github_discover`, `provider.github_validate_repo`,
`provider.jira_connections`, `provider.jira_add_connection` (writes), `provider.jira_connection`,
`provider.jira_discover`, `provider.jira_search`, `provider.jira_validate_scope`, `provider.confluence_connections`,
`provider.confluence_discover`, `provider.confluence_validate_space` (`project.py:1757-1969`: account and discovery
calls to GitHub, Jira and Confluence, egress); `connection.list`, `connection.recheck` (`project.py:2078-2088`,
`ConnectionsService`: the readiness of each connector). Authority: palette; `PROJECT_PALETTE` holds every tool of the
module (`project.py:2098`).

### MCP adjacent (in `holdspeak/mcp/tools.py`) — 4

| Identity | Real callable (line) | Writes | Class |
|---|---|---|---|
| `desk.needs_you` | `build_aggregate` over `ProjectService.list_projects`/`room` (`tools.py:1077-1090`) | no | aggregate read (the Phase 7 charter parked it here) |
| `steward.nudges` | `ProjectStewardService(db, MagicMock(), MagicMock()).list_nudges` (`tools.py:1177-1181`) | no | steward read (F9) |
| `nudge.send` | `ProjectStewardService(db, MagicMock(), MagicMock()).send_nudge` (`tools.py:1182-1186`) | yes; a GitHub comment (egress) | steward verb (F9) |
| `nudge.dismiss` | the same, `dismiss_nudge` (`tools.py:1187-1191`) | yes | steward verb (F9) |

### HTTP — 6

| Identity (`module::function`) | Service built | Note |
|---|---|---|
| `holdspeak/web/routes/projects.py::build_projects_router._build_needs_you` | `HeartbeatService` | reads the mute list (`projects.py:546-549`) |
| `holdspeak/web/routes/projects.py::build_projects_router.api_suggested_sources` | `SuggestedSourceService` | `projects.py:600` |
| `holdspeak/web/routes/projects.py::build_projects_router.api_add_suggested_source` | `SuggestedSourceService` | `projects.py:615`, plus raw SQL at `:620` |
| `holdspeak/web/routes/projects.py::build_projects_router.api_dismiss_suggested_source` | `SuggestedSourceService` | `projects.py:653`, plus raw SQL at `:657` |
| `holdspeak/web/routes/automations.py::build_automations_router._project_service` | `ProjectService` (2 constructions) | a second `ProjectService` outside the hub's |
| `holdspeak/web/routes/people.py::build_people_router.projects` | `ProjectService` | as above |

**Total: 61 MCP + 6 HTTP** project identities of the 284. The HTTP-only project operations that the census does not
count (it counts constructors, not traversal) include the items (`projects.py:411-515`), the resources
(`projects.py:294-325`), the room read marker (`projects.py:55`), the saved asks (`projects.py:92-196`) and the Door's
create-with-sources (`holdspeak/web/routes/project_door.py:4`).

## The job

One plausible Senior-Architect job, picked from what the Room offers: make a project, add a thing to it, see what
needs him, ask the steward, draft and publish the update in the Room (publication is local; it sends nothing — round two, Q0). Walked both ways.

- **Over MCP** (`mcp/summary.json`): `project.create` ok; `project.get_room` ok; **add a thing: the catalogue has no
  verb** (F4); `project.add_suggested_source` / `suggested_sources` / `dismiss_suggested_source` fail (F5);
  `desk.needs_you` ok (count 0); `project.open_review` ok; `project.configure_steward` → `{"policy": null}`;
  `project.run_steward` ok, the run completes; `project.draft_update` and `project.publish_update` ok;
  `connection.list` and `provider.list` ok; `project.get_room` after the job says updates and steward are
  "not_yet_built" (F6).
- **On the face** (`face/*`): New Project from ⌘K, the Door, Create Project: the Room opens (`12-after-create-*`).
  Draft update → Draft → Publish works (`14`–`16`). Steward → Run once: the run completes and the face overstates it
  (F3). A milestone added over HTTP does not show (F2). The Room cannot be opened from a linked meeting (F1).

## FINDINGs, ranked by owner cost

**F1 — He cannot open a Room from where the product sends him.** The surface key `project-room` is registered
nowhere (no `action: "project-room"` or alias in `web/src/desk/applications.ts`; `registerSurface` only registers
those rows, `web/src/desk/components/SurfaceWindows.tsx:99-110`). So `openSurfaceOr("project-room", "/projects", …)`
falls back to `/projects`, which is not a route (`web/src/routes.tsx:41-75`), and `App.tsx:68` sends it to `/`. Eight
callers: `web/src/desk/chair/ChairHome.tsx:851,864,1815,1953`, `web/src/desk/components/SystemShade.tsx:458,594`,
`web/src/features/project-room/recall/RecallFace.tsx:84`, `web/src/pages/cores/history/MeetingReview.tsx:273`.
Walked at 1440 and 393: a meeting linked to "Payments migration" (`project.link`), Meetings → REVIEW → the
`PAYMENTS MIGRATION` button (`aria-label="Open the Project: Payments migration"`): no Room opens, the window set is
unchanged and the Meetings window goes back to OUTCOMES (`face/31c-review-tab-*.png` → `face/32-after-open-project-*.png`,
`face/open-room-*.json`). The only path that works is ⌘K "Open <project>" (`open-project-memory` with the scope
`project:<id>`, `web/src/desk/components/DeskToolShelf.tsx:341`). The Chair, the shade and the recall callers were not
clicked (they need a connector snapshot or a decision in a Room); they share the same dead key.

**F2 — A thing he adds to a project does not show in the Room, and the Room says he is on track.** A milestone
"Cutover rehearsal", due 2026-09-20 (seven days past), made with `POST /api/projects/{id}/items`: the hub's Room read
has it in `items.focus`, but the face has no items section (the Room's sections: `ProjectRoomCore.tsx:774`, `:793`,
`:963`, `:1136`, `:1242`, `:1556`, `:1588`; `web/src/features/project-room/api.ts` has no item call). The health chip
stays `ON TRACK`: the overdue input counts follow-through commitments only (`holdspeak/services/project_service.py:1457-1461`,
`:1482`), and NEEDS YOU comes only from connector watch snapshots and the review (`project_service.py:702-760`).
Shots: `face/04-room-1440.png`, `face/04-room-393.png`. (A risk without `details.likelihood` is refused 400,
"details.likelihood is required for risk"; the milestone was the item the lane could add with a title and a date.)

**F3 — The steward face overstates what the run did.** After Run once on a new project the face reads
"Observe 1 source · Propose 1 · Act 1 effect" (`face/26-steward-ran-1440.png`, `-393.png`). The hub's run: every
phase completed, `proposal_count: 0`, `actions_taken: 0`, `effect_receipts: []`, and all six effect kinds skipped with
`not_in_eligible_effect_kinds` (`GET /api/projects/{id}/steward/runs`, read back in the lane). The face counts each
phase's checkpoint step (`effect_kind: "phase:observe"` etc.) as a source, a proposal and an effect
(`web/src/features/project-room/steward/StewardPosture.tsx:155-164`). With no policy (`project.configure_steward` →
`{"policy": null}`) no effect kind is eligible, so ACT performs no action, and no word says so. The run is not
"nothing": COMPARE opens a review (`holdspeak/services/project_steward_service.py:860-869`, `self._delta.open_review`),
so a run leaves an open review window even when ACT takes no action (corrected in round two, Codex Astra r1 F5).

**F4 — No MCP verb adds anything to a project.** The catalogue's only "add" verb is `project.add_suggested_source`
(`mcp/summary.json`, "find a verb to add a thing"). Items (`list`, `create`, `update`, `transition`:
`holdspeak/web/routes/projects.py:411-515`) and resources (`list`, `add`, `remove`: `projects.py:294-325`) exist only
over HTTP. The face makes a project through the Door (`POST /api/projects/door`, `project_door.py:4`, with sources and
watches); MCP makes a bare project (`project.create`) — two create paths.

**F5 — The three suggested-source MCP tools fail on every call.** Each answers
`{"error": "cannot access local variable 'svc' where it is not associated with a value"}` (`mcp/mcp-walk.jsonl`):
`svc` is bound only in other branches of `dispatch`, and these branches read `svc._db`
(`holdspeak/mcp/families/project.py:2044`, `:2053`, `:2058`, `:2072`).

**F6 — The Room read says the updates and the steward do not exist.** After a published update and a completed
steward run, `project.get_room` (and `GET /api/projects/{id}/room`) answers `"updates": {"state": "absent", "reason":
"not_yet_built"}` and the same for `steward` (`holdspeak/services/project_service.py:250`, `:510-511`;
`mcp/room-after-job.json`). A client without the repository reads that as "none".

**F7 — The Room's receipts are its own reads.** RECEIPTS shows ten rows of "READ MEETINGS", "READ", "READ PROJECT",
"MARK ROOM READ" (`face/20-room-reopened-1440.png`); the create, the publish and the steward run are not among them
(`project_service.py:1933`, the last ten pipeline receipts, reads included).

**F8 — No project write is admitted through the kernel, and no write leaves a kernel receipt.** After 3 creates,
3 publishes, 3 steward runs, 1 review opened and 1 meeting link, `kernel_operations` held only `dictation.session`,
`heartbeat.*`, `inference.invoke`, `watch.create` and `zone.file` rows (read-only `sqlite3` on the isolated database).
Authority: any principal whose palette holds the tool; OWNER checks only in the setup service and the watch writes (the
census above). Article XI.1 names model calls and egress as consequential (`docs/internal/CONSTITUTION.md:169-175`); the
steward's `github_comment` and `nudge.send` cross egress, and `draft_update` with `generator=model` calls a model. This
is the owner's question (the charter's Q1).

**F9 — Three MCP tools build the steward service with test doubles in product code.** `steward.nudges`,
`nudge.send` (a GitHub comment) and `nudge.dismiss` construct `ProjectStewardService(db, MagicMock(), MagicMock())`
(`holdspeak/mcp/tools.py:1177-1191`, `from unittest.mock import MagicMock`). Code-read; `nudge.send` was not run (no
GitHub account on the isolated HOME).

**F10 — At 393 the Ask well covers the Steward verb on first view.** `document.elementFromPoint` at the centre of the
Steward button hits `room-ask-well`, not the button (`face/face-job-393.json`, `obscured_steward`); the SOURCES heading
is under the well too (`face/13-room-393.png`). Playwright's click scrolled first and reached it, so it is reachable by
scrolling. At 1440 the button is hit (`face/face-job-1440.json`).

**F11 — The update list says DRAFTS for a published update, and its words run together.** The list head is
`countLabel("DRAFTS", …)` for every lifecycle (`web/src/features/project-room/update/UpdatePosture.tsx:257`); the row
reads "PUBLISHEDRev 11m agoDeterministic draft" with no space between the parts at 393, and the lead emblem is a fixed
"E" (`:268-270`) (`face/21-update-posture-with-published-393.png`).

**F12 — The tool descriptions name mechanisms, not his jobs.** For example "Get the coherent room projection for one
project (identity, items, …)", "Open a deterministic review window for a project", and every id is "Project
identifier." with no word on where it comes from (`mcp/tools-project-descriptions.json`). The same class Phase 7
repaired for the desk (`pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md`
"Discovery without repository access").

**F13 — MCP `desk.needs_you` ignores the owner's muted projects; HTTP applies them.** `projects.py:546-573` drops
muted Rooms from the count; `tools.py:1077-1090` does not read the mute list. Code-read; not observed (needs-you items
need a connector snapshot).

**F14 — A base install cannot import the MCP catalogue.** `holdspeak/operations.py:38` imports `jsonschema`; the
package declares it only in the optional `test` and `dev` extras (`pyproject.toml:85`, `:139`), not in the base
dependencies. In this lane a fresh `uv run` venv (base
dependencies, 79 packages) failed `from holdspeak.mcp.tools import TOOLS` with `ModuleNotFoundError: No module named
'jsonschema'` (at `operations.py:38`). Route modules import `operations` at load (`holdspeak/web/routes/monday_brief.py:14`,
`meeting_import.py:17`, `primitives/kbs.py:17`), so the hub likely cannot start on a base install; **not booted** —
unknown. Not a Room defect; round two makes it a prerequisite repair in story 01 (Codex Astra r1 MISSED 4).

**F15 (corrected in round two) — the handlerless "Add" is not the suggested-source row.** The Room's normal SUGGESTED
row has wired Add and Dismiss (`ProjectRoomCore.tsx:976-1000`, `ctrl.handleAddSuggestion` / `handleDismissSuggestion`).
The Button with no action at `ProjectRoomCore.tsx:1050` sits on a different branch: a *watch source* row whose
`src.suggested` is set. Code-read; that branch was not rendered. The real source-addition wall is F16 and F17 (Codex
Astra r1 F2).

## The D2 debts, measured on main `b37dc2fb`

| Debt | 1440 | 393 | Source |
|---|---|---|---|
| `::selection` on the list's zone name field (selected, focused) | `rgba(168,110,74,.12)` over `rgb(21,23,29)` paints `rgb(39,33,34)`: **1.13:1** | the same, **1.13:1** | `web/src/styles/global.css:68-71`; `d2/d2-*.json`, `d2/selection-field-*.png` |
| Text under 12 px in the list | 51 visible text nodes; census line and status 10 px | 33 nodes; 10 px | `web/src/desk/components/list-view.css:61`, `:76`; `d2/d2-*.json` |
| The plural | "27 SHOWNS OF 27" | the same | `web/src/desk/components/DeskListView.tsx:331` |
| The Zone column | fits | **Kind, Zone and Attention are wholly off the right edge** (cells end at 685, 764, 842 px on a 393 px viewport): only NAME shows | `d2/list-393.png`, `d2/d2-393.json` |
| Sort headers | 4 raw `<button class="desk-sortable-table-sort">` | the same | `web/src/desk/components/DeskSortableTable.tsx:96` (UX-CANON §A.1) |
| Row menu Delete near the bottom edge | fits (bottom 875, viewport 900) | **cut 15 px** (top 839, bottom 867, viewport 852) | `d2/row-menu-393.json`, `d2/row-menu-393.png`; the menu opens `anchor="below"` (`DeskListView.tsx:376-385`) |

The Zone column is worse than the Phase 8 record ("`1 ITEM` shows as `1 ITE`", BACKLOG "PHILO-8-01 follow-ups"): on
this main and this seed the whole column is off screen at 393.

## Unknown

- What `POST /api/inference/assignments/editor` does when the update posture opens (it fired on every open,
  `face/face-job-*.json` `writes`). Not read.
- The provider discovery tools and the Door's create-with-sources were not walked: the isolated HOME has no GitHub,
  Jira or Confluence account.
- Whether the hub boots on a base install (F14).
- The Chair, shade and recall callers of `project-room` were not clicked (F1).

## Round two (2026-09-27): Codex Astra r1's probes, reproduced

Codex Astra checked the charter at `3066dccb` (`pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/checks/charter-astra-r1.md`,
DO-NOT-RATIFY). The lane reproduced its three probes on a fresh isolated HOME with the rig's real hub
(`probes/r2_probes.py.txt`; the record `round-two/r2-probes.json`; product code unchanged since `b37dc2fb`).

**P1 — source addition.** Two suggestions minted through the real scanner and persistence
(`SuggestedSourceService.scan_transcript` + `create_suggestions`, the calls `holdspeak/intel_queue.py:383-385` makes) from
"We should watch example/payments and PAY-123 before the cutover." `GET …/suggested-sources` lists both. Then the routes
the face calls, the reference URL-encoded as `web/src/features/project-room/api.ts:178` does:

| Reference | Request | Answer | Suggestion after | Resource / watch after |
|---|---|---|---|---|
| `example/payments` (GitHub) | `POST …/suggested-sources/example%2Fpayments/add` | **404** `{"detail":"Not Found"}` | `pending` | none |
| `PAY-123` (Jira) | `POST …/suggested-sources/PAY-123/add` | **200** `resource.state: "accepted_no_watch"`; the body's suggestion still says `"status": "pending"` | **`accepted`** | **none**: zero `project_resources`, zero `connector_watches` |

**F16 — A GitHub source cannot be added from a suggestion.** The route's `{ref}` is one path segment
(`holdspeak/web/routes/projects.py:608`); an `owner/repo` reference, encoded or not, never reaches it (404).

**F17 — A Jira suggestion is "accepted" and nothing is added, and the answer says otherwise.** The route accepts the
suggestion first (`projects.py:628`), then calls `add_resource`, whose failure is swallowed into
`accepted_no_watch` (`projects.py:633-639`); the MCP twin does the same (`holdspeak/mcp/families/project.py:2055-2063`).
The cause, reproduced in the lane: `qualified_ref("jira:PAY-123")` and `qualified_ref("github:example/payments")` both
raise `ValueError: unknown resource kind` (`holdspeak/db/relationships.py:25`, reached from `project_service.py:3177`).
And even when `add_resource` succeeds it writes a `project_resources` row only, no watch (`project_service.py:3169-3284`),
while the tool says "create a Watch source on the Room" (`project.py:833`). The accepted suggestion no longer offers
itself again. So no path turns a suggestion into a watched source.

**P2 — archive as the owner (F18).** `project.configure_steward(enabled=True, unattended_enabled=True)`, then
`project.archive` over MCP: the policy went from `unattended_enabled 1` to `0` (`enabled` stayed 1); zero
`kernel_operations` rows before and after (`round-two/r2-probes.json` `p2`). The archive also pauses the project's
watches in the same transaction (`project_service.py:3023-3035`). **F18: archive changes the steward's authority
(unattended runs), not only a label.**

**P3 — a PROJECT credential without a delegation (F19).** Remote Access enabled, a credential issued through Settings
(`POST /api/settings/remote/credentials`, palette `PROJECT`, identity `probe-agent`); no delegation row exists. As that
agent: `project.configure_steward(unattended_enabled=True)` succeeded (the policy row reads `unattended_enabled 1`);
`project.archive` succeeded (`is_archived 1`); zero `kernel_operations` rows (`round-two/r2-probes.json` `p3`).
**F19: an agent can turn on unattended steward runs and archive a project with no grant and no receipt**
(Article XI.4: "Only the owner approves, rejects, or delegates").

**The census, rechecked by Codex Astra:** 284 = 223 MCP + 61 HTTP; 229 public tools; 61 project-adjacent MCP; the 38
proposed MCP identities and six HTTP tuples exist; 284 → 240–246 correct (r1 F6).


## Round three (2026-09-27): Codex Astra r2's probe and the lane's code reads

Codex Astra checked the charter at `f72db808` (`pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/checks/charter-astra-r2.md`,
DO-NOT-RATIFY, converging).

**Astra's fixture probe (Codex Astra's run, not the lane's; recorded as Astra reported it).** On an isolated real hub
Astra created the charter's milestone ("Cutover rehearsal") and risk ("Old ledger freeze slips") through the production
HTTP routes, set the steward policy `eligible_effect_kinds: ["draft_update"]`, and ran the steward over MCP: one
`draft_update` effect completed; the draft named both titles; publication persisted across a readback; a later edit was
refused `published_update`. Ids: run `pstrun_aee671c2319c4d00ad51d15dae12024a`, review
`prev_34d7867155cf42509b0f2b2fe1eca11f`, update `pupd_1d86640c7ab64a5ba6f3c9e82b6179c8`. Astra's records
(`probe.json`, `readback.json`) sit in a temporary directory outside the repository and are not retained here; the lane
did not re-run this probe.

**F20 — the steward records a blank review id.** In that run `compare.review_id` was `""` although the review existed:
`_phase_compare` reads `review.get("id")` (`holdspeak/services/project_steward_service.py:869`); `open_review` returns
`review_id` (`holdspeak/services/project_delta_service.py:1848`). Code-read confirmed in the lane.

**F21 — "list" and "count" probe providers.** The Door's count fetches GitHub/Jira snapshots
(`holdspeak/services/project_door_service.py:146`, through `holdspeak/services/watch_sources.py:75`, `gh pr list`);
`connection.list` calls `_github_entry`, which calls `connection_status` and so probes GitHub authentication and persists
its state (`holdspeak/services/connections_service.py:113-121`, `:154-177`; `holdspeak/services/github_provider.py:183`).
`connection.recheck` for `calendar` and `models` returns local readiness (`connections_service.py:123-141`). Code-read.

**Q3 (c)'s attention item.** An open review alone is not in NEEDS YOU; only pending proposals are
(`holdspeak/services/project_service.py:814-826`). Astra's review had zero proposals and zero attention items. A pending
proposal needs an observation the closed rules turn into one (`holdspeak/services/project_delta_service.py:224-248`:
`followthrough.overdue`, `followthrough.stale`, `decision.review_due`, `watch.transition`).

**F22 — "1 proposals waiting".** `project_service.py:822` writes `f"{pending} proposals waiting"`. Code-read.

# Phase 9 - The Room on the Contract

**Last updated:** 2026-09-27 (DRAFTED by the Fedaykin docs lane (Opus 5.5) for Muad'Dib, on the owner's rulings D1–D3 of 2026-09-27; grounded on main `b37dc2fb`: the census, the project job walked on a real hub at 1440 and 393, the D2 debts measured. The Codex Astra check is owed; the owner's ratification and his answers to Q1–Q3 are owed. Nothing is built.)

**Status:** DRAFT.

## Goal

The owner works in a project room. He makes a project, puts a thing in it, sees what needs him, asks the steward to run, and sends his update, from the Room's face or from an MCP client that knows only the catalogue. The Room, its sources (the connectors) and the steward reach one declared operation each, bound to the hub's services, as Phase 7 did for notes, zones and decisions. The Room's face shows what the hub holds. Plus one bounded story of desk debts from the Phase 8 ledger.

## Authority

The owner, 2026-09-27, by AskUserQuestion (his picks, verbatim):

- **D1, the job:** "Work in a project room" — Projects on the contract: the Room, its connectors and the steward on the one declared contract, as Phase 7 did for notes/zones/decisions. The closing test: a cold-context client runs a real project job from the MCP catalogue alone, and the Room's face shows it at 1440 and 393.
- **D2:** "Yes, one bounded story" of desk debts from the Phase 8 ledger: the desk-wide `::selection` you can see (`web/src/styles/global.css:68`, 1.13:1 today), and the list face repair (10 px count line → 12 px, the "SHOWNS" plural, the Zone column cut at 393, raw sort-header buttons → library Button, the row menu's Delete cut 15 px at 393). Canvas first for the list face (UX-CANON §A.2).
- **D3, the closing client:** Codex (cold context; the Phase 7 story 04 driver `scripts/philo7_file_and_find.py` and its launch setup are the precedent).

The ledger this phase pays: the BACKLOG row "Projects on the contract" (`pm/roadmap/holdspeak/BACKLOG.md:1300-1304`), Phase 8's THE LEDGER rows 1, 2 and 6 (`../phase-8-the-honest-floor/final-summary.md` "THE LEDGER"), and Phase 7's ledger row 8, "find it cold" (`../phase-7-the-desk-on-the-contract/final-summary.md` THE LEDGER; BACKLOG "PHILO-7-04 follow-ups" row 3).

Carried, unchanged: the Seven Tenets (`docs/internal/CONSTITUTION.md:18-60`); Article XI (`docs/internal/CONSTITUTION.md:167-193`); UX-CANON §A.1 every verb the library Button, §A.2 the canvas before build, §A.11 a verb that does nothing is a lie (`docs/internal/UX-CANON.md:17-58`); the method and laws of handovers XXVIII–XXX (`docs/internal/project-rooms/HANDOVER-MUADDIB-XXVIII.md:11-20`, `HANDOVER-MUADDIB-XXIX.md:33-42`, `HANDOVER-MUADDIB-XXX.md:18-24`); Phase 5's settled positions and compatibility rules (`../phase-5-the-one-service-layer/current-phase-status.md:109-146`); Phase 7's "Settled between the brains" (`../phase-7-the-desk-on-the-contract/current-phase-status.md` §"Settled between the brains"); the owner's ruling that MCP flows through the services (2026-09-23, verbatim in the Phase 7 Authority).

## The roots

- **Tenet 2 (not even pre-alpha):** the Room is where his second job lives, and today he cannot reach it from the places that point to it. The Chair's rows, the shade, a meeting's project button and the recall face all call a surface key that is registered nowhere (grounding F1, walked at both widths).
- **Tenet 3 (help and accelerate):** the face must say what the hub did. Today the steward face says "Act 1 effect" for a run that did nothing (F3), the Room says ON TRACK with a milestone seven days late that it does not show (F2), and the Room read says the updates and the steward are "not_yet_built" after both ran (F6).
- **Tenet 1 (no over-engineering):** a finite, explicit descriptor table per operation, as in Phase 7. No discovery framework, no universal CRUD, no new authority policy by default. The setup interview and the provider discovery tools are parked, not rebuilt.
- **Tenet 5 (component framework):** the Room composes the library species it has; the new items section (Q3) and the list face repair are drawn on the canvas from the library first.
- **Tenet 7 (a Senior Architect with reports):** a project has milestones, risks and a steward; he tells his boss where it stands. The job and the closing test are his.
- **Article XI:** today no project write is admitted through the kernel, and none leaves a kernel receipt (F8). The steward can post a GitHub comment (egress) and a draft can call a model; Article XI.1 names both as consequential. Q1 asks him which project writes are admitted.

## Status of this charter

DRAFT, 2026-09-27, written by the Fedaykin docs lane (Opus 5.5) for Muad'Dib. Owed: the Codex Astra check (the method's other brain, `docs/internal/TWO-BRAINS.md`); the owner's ratification and his answers to "Decisions for the owner" (Q1–Q3). Nothing is built. The stories stay `backlog` until the owner ratifies.

## The grounding (main `b37dc2fb`)

The full record, with every shot, log and probe: `docs/internal/philo/phase-9/grounding/README.md`. In short:

- **The census.** `scripts/residual_census.py --check` under an isolated HOME: `RESIDUAL FENCE GREEN: 284 identities match` = 223 MCP + 61 HTTP; public tools 229. The project identities: **61 MCP + 6 HTTP** — `project.*` 42; the connectors in the same module, `provider.*` 13 and `connection.*` 2; `desk.needs_you`, `steward.nudges`, `nudge.send`, `nudge.dismiss` 4 (in `holdspeak/mcp/tools.py`); HTTP `projects.py` 4, plus `ProjectService` built in `automations.py` and `people.py` 2. Each identity is listed by name with its real callable, whether it writes, and its authority today in the grounding README.
- **The job, walked.** Make a project, add a thing, see what needs him, ask the steward, draft and publish the update: over `/api/mcp` from `tools/list`, and on the Room's face at 1440x900 and 393x852, on a real hub with an isolated HOME.
- **FINDINGs, ranked by owner cost** (each with its lines and shots in the grounding README):
  - **F1** The Room cannot be opened from the eight places that point to it: the key `project-room` is registered nowhere and its fallback `/projects` is no route (`web/src/desk/chair/ChairHome.tsx:851`, `web/src/pages/cores/history/MeetingReview.tsx:273`, six more; `web/src/App.tsx:68`). Walked: a meeting's project button opens nothing, at both widths.
  - **F2** A milestone he adds does not show in the Room (no items section, `web/src/features/project-room/ProjectRoomCore.tsx`), and the Room says ON TRACK seven days after its date (overdue counts commitments only, `holdspeak/services/project_service.py:1457-1461`).
  - **F3** The steward face says "Observe 1 source · Propose 1 · Act 1 effect" for a run with 0 proposals and 0 actions, every effect kind skipped (`web/src/features/project-room/steward/StewardPosture.tsx:155-164`); with no policy a new project's steward can do nothing, and nothing says so.
  - **F4** No MCP verb adds anything to a project: items and resources are HTTP only (`holdspeak/web/routes/projects.py:294-325`, `:411-515`); the face creates through the Door, MCP through `project.create` (two create paths).
  - **F5** `project.suggested_sources`, `add_suggested_source` and `dismiss_suggested_source` fail on every call (`svc` unbound, `holdspeak/mcp/families/project.py:2044`, `:2053`, `:2058`, `:2072`).
  - **F6** The Room read says updates and steward are `absent · not_yet_built` after both ran (`holdspeak/services/project_service.py:510-511`).
  - **F7** The Room's RECEIPTS are its own reads ("READ MEETINGS" ×n); the create, publish and steward run are not there (`project_service.py:1933`).
  - **F8** No project write is admitted through the kernel or leaves a kernel receipt (read back from the isolated database after 3 creates, 3 publishes, 3 steward runs, a review and a link).
  - **F9** `steward.nudges`, `nudge.send` (a GitHub comment) and `nudge.dismiss` build the steward service with `unittest.mock.MagicMock` collaborators in product code (`holdspeak/mcp/tools.py:1177-1191`). Code-read.
  - **F10** At 393 the Ask well covers the Steward verb and the SOURCES heading on first view (`elementFromPoint` hits `room-ask-well`).
  - **F11** The update list heads a published update "DRAFTS 1", its row reads "PUBLISHEDRev 11m agoDeterministic draft", and its emblem is a fixed "E" (`web/src/features/project-room/update/UpdatePosture.tsx:257`, `:268-270`).
  - **F12** The project tool descriptions name mechanisms, not his jobs, and say nothing about where an id comes from (`docs/internal/philo/phase-9/grounding/mcp/tools-project-descriptions.json`).
  - **F13** MCP `desk.needs_you` ignores the muted projects that HTTP applies (`holdspeak/web/routes/projects.py:546-573` vs `holdspeak/mcp/tools.py:1077-1090`). Code-read.
  - **F14** A base install cannot import the MCP catalogue: `holdspeak/operations.py:38` imports `jsonschema`, declared only in the `test` and `dev` extras (`pyproject.toml:85`, `:139`). Out of this phase (BACKLOG).
  - **F15** A suggested source row's "Add" Button has no action (`ProjectRoomCore.tsx:1050`). Code-read, not seen.
- **The D2 debts reproduce on main** (grounding "The D2 debts"): `::selection` 1.13:1 at both widths; 51 (1440) and 33 (393) visible text nodes under 12 px in the list, the census and status lines 10 px; "27 SHOWNS OF 27"; at 393 the Kind, Zone and Attention columns are wholly off the right edge (worse than the Phase 8 record); 4 raw sort-header `<button>`s (`web/src/desk/components/DeskSortableTable.tsx:96`); the row menu's Delete cut 15 px at 393 (top 839, bottom 867, viewport 852), in view at 1440.

## Scope

- **In:**
  1. **The Room's operations on the contract, with discovery words (story 01).** Explicit descriptors in `holdspeak/operations.py`, bound at hub composition to the hub's `ProjectService`, `ProjectDeltaService` and `ProjectUpdateService`, for: the Room lifecycle (`project.list`, `get`, `get_room`, `create`, `update`, `archive`, `restore`, `link`, `unlink`: 9 MCP identities), the review (`open_review`, `get_delta`, `decide_proposal`, `accept_review`: 4), the updates (`list_updates`, `draft_update`, `update_draft`, `publish_update`: 4) and `desk.needs_you` (1): **18 MCP identities**, plus the HTTP constructors `projects.py::_build_needs_you` and the two `ProjectService` constructions outside the hub (`automations.py`, `people.py`): **3 HTTP**. New exposure over MCP for what today is HTTP only: the items (`item.list`, `item.create`, `item.update`, `item.transition`) and the resources (`resource.list`, `resource.add`, `resource.remove`) — F4; one create path (the Door's create and `project.create` reach one operation, or the difference is named in the descriptor). Repairs: F6 (the Room read tells the truth about updates and the steward), F13 (one needs-you count on both transports), F12 (descriptions name his jobs; argument descriptions name where each id comes from). A discovery fence that reads only the real `tools/list` answer.
  2. **The steward and the connectors on the contract, under Article XI as Q1 rules (story 02).** Descriptors for the steward (`configure_steward`, `run_steward`, `stop_steward`, `get_steward_run`, `steward.trigger`: 5), the nudges (`steward.nudges`, `nudge.send`, `nudge.dismiss`: 3, built on the hub's service, no `MagicMock` — F9), the Room's sources (`project.watch.*`: 7; the suggested sources: 3, repaired — F5; `connection.list`, `connection.recheck`: 2): **20 MCP identities**, plus the three `SuggestedSourceService` constructors in `projects.py`: **3 HTTP** (the raw SQL at `projects.py:620` and `:657` goes with them). Kernel admission and one terminal receipt for each write Q1 admits, on both transports, with refusal receipts as Phase 7 ruled (R2); agent writes as Q2 rules. F8.
  3. **The Room's face tells the truth (story 03; canvas first for any new section).** F1: every caller opens the Room (one key, registered once; no fallback to a route that does not exist). F2: the Room shows the project's items as Q3 rules, and health counts a past-due milestone. F3: the steward face counts effects, not checkpoints, and says when no effect kind is allowed. F7: RECEIPTS are the writes, not the Room's own reads. F10: the Steward verb is not covered at 393. F11: the update list's words. F15: verified, then repaired or withheld. Each repair uses an idiom that exists; the items section (if Q3 keeps it) is drawn on the canvas and ratified by the owner before build.
  4. **The desk debts, D2 (story 04; canvas first for the list face).** The desk-wide `::selection` token with a visible contrast (a measured number at both widths). The list face repair as the owner ratifies it on the canvas: no product text under 12 px, the "SHOWN" plural, every column readable at 393, the sort headers as the library Button, the row menu fully in the viewport at 393.
  5. **The atlas cases and their `.op` siblings (story 05)** for the repaired faces and the job, at 1440 and 393.
  6. **The closing use from a cold-context Codex session (story 06):** the job from the catalogue alone; "find it cold" (a second session finds a project it did not make); the Room's face at 1440 and 393; rehearsed, owner-reviewed shots.
- **Out (with their homes):**
  - The setup interview (`project.setup.*`, 10 MCP identities): its face is parked (`web/src/features/project-room/_parked/setup/`); the Door replaced it (`holdspeak/web/routes/project_door.py:4`). Parked, not deleted (the owner's ruling "never delete — park instead"). BACKLOG "PHILO-9 charter follow-ups".
  - The provider discovery tools (`provider.*`, 13): account and discovery calls to GitHub, Jira and Confluence (egress; they need his accounts, which an isolated rig does not have). The Door's source rows keep using them over HTTP. BACKLOG "PHILO-9 charter follow-ups"; the next connector slice.
  - An "add a thing" verb on the Room's face, if Q3 (b) is ruled: BACKLOG "PHILO-9 charter follow-ups".
  - F14, the base install and `jsonschema`: BACKLOG "PHILO-9 charter follow-ups" (packaging; small).
  - The saved asks (`projects.py:92-196`), the Room people read (`projects.py:672`), the briefings and the Prepare posture: the Room's other postures, not in the job.
  - DESK palette = ALL (BACKLOG "PHILO-7-02 canvas follow-ups"): stays there under Q2 (a); under Q2 (b) story 02 repairs it first.
  - The six non-desk kernel two-step terminal writes (BACKLOG "PHILO-7-02 lifecycle beat follow-ups"); the tombstoned Thought's note 500 (BACKLOG "PHILO-7-02 round two follow-ups"); the Floor rename field clip, the 4.7 s to the field, the rename re-send and the late refusal's lost reason (BACKLOG "PHILO-8-01 follow-ups" rows 2–5); the rename duplicate (BACKLOG "PHILO-8-02 follow-ups" row 3); the Follow-through doubled hairline (BACKLOG "PHILO-8-04 follow-ups"); the guarded right-click rig note (BACKLOG "PHILO-8-03 follow-ups" row 3); the Workbench footer linger; the 11/10 px rules outside Settings and outside the list; the privacy note: all stay in their homes.
  - The ToolSearch confound (Phase 7 ledger row 9): a Claude-client effect; the closing client is Codex (D3). Report only.
  - Any change to the kernel beyond the admission Q1 rules; any face outside the Room, the list and the selection token.

### The enumerated identities (proposed; story 01 and 02 fix them in their first commit)

Of `docs/internal/philo/phase-5/residual-set.json` at main `b37dc2fb`:

| Story | Transport | Identities | Count |
|---|---|---|---|
| 01 | mcp | `project.list`, `project.get`, `project.get_room`, `project.create`, `project.update`, `project.archive`, `project.restore`, `project.link`, `project.unlink`, `project.open_review`, `project.get_delta`, `project.decide_proposal`, `project.accept_review`, `project.list_updates`, `project.draft_update`, `project.update_draft`, `project.publish_update`, `desk.needs_you` | 18 |
| 01 | http | `projects.py::build_projects_router._build_needs_you` `HeartbeatService`; `automations.py::build_automations_router._project_service` `ProjectService`; `people.py::build_people_router.projects` `ProjectService` | 3 |
| 02 | mcp | `project.configure_steward`, `project.run_steward`, `project.stop_steward`, `project.get_steward_run`, `project.steward.trigger`, `steward.nudges`, `nudge.send`, `nudge.dismiss`, `project.watch.inspect`, `project.watch.test`, `project.watch.evaluate`, `project.watch.set_rules`, `project.watch.pause`, `project.watch.resume`, `project.watch.retire`, `project.suggested_sources`, `project.add_suggested_source`, `project.dismiss_suggested_source`, `connection.list`, `connection.recheck` | 20 |
| 02 | http | `projects.py::build_projects_router.api_suggested_sources`, `.api_add_suggested_source`, `.api_dismiss_suggested_source` `SuggestedSourceService` | 3 |

**38 MCP + 6 HTTP.** The honest range at close, as Phase 7 stated it: a syntactic census cannot tell a fallback from a hub construction, so an HTTP identity whose construction stays for the route tests MOVES and is not paid. Residual 284 → **240** (all 44 paid) to **246** (the 38 MCP only). New public tools (items, resources, and any receipt read) raise the public tool count (229 today); a different measurement, reported apart. The census counts constructors and declared exposure, not traversal: the HTTP-only item and resource routes are not identities, and their exposure is real work no count shows.

## Exit criteria (evidence required)

Every behavioural fence is red on main before the repair — through the real hub on an isolated HOME, never a test double that lies about the field a check reads — and green after. "At both widths" means 1440x900 and 393x852. The grounding (`docs/internal/philo/phase-9/grounding/`) is the red record on main `b37dc2fb` for each item it measured.

- [ ] 1. **The residual set shrank by the enumerated identities** (38 MCP; the 6 HTTP only where the construction left), recorded by `(transport, entry point, discriminator)`; the fence fails on a new residual identity (red on a copy of main). Evidence: `scripts/residual_census.py --check` at the phase head and on the copy; `docs/internal/philo/phase-5/residual-set.json` `paid`.
- [ ] 2. **The job is discoverable and executable over MCP alone.** A fence reads only the real `tools/list` answer and maps each job phrase ("make a project", "add a milestone / risk to a project", "what needs me", "run the steward", "draft my update", "send my update") to its tool and argument path (red on main: no item tool, F4). Every in-scope operation is reachable by route, by MCP and by the rig's `op` step and reaches the same declared operation and the same live service in one hub. Evidence: the discovery fence; the three-transport run.
- [ ] 3. **Every Room read says what exists.** `project.get_room` (and the route) reports the published update and the steward run (red on main, F6); the three suggested-source tools answer (red on main, F5); `desk.needs_you` gives one count on both transports with a muted project (red on main, F13); no `MagicMock` in product code (an AST fence over `holdspeak/`, red on main, F9). Evidence: fences through the real hub.
- [ ] 4. **Article XI as Q1 rules.** Each admitted project write is one kernel operation with one terminal receipt on both transports; each refusal class leaves its receipt (Phase 7 R2); reads and plain edits leave none; agent writes behave as Q2 rules. Red on main: zero project rows in `kernel_operations` (F8). Evidence: the admission fences with an authenticated principal (handover XXIX law 5) and their mutations.
- [ ] 5. **The Room's face shows the job, at both widths.** Every caller of the Room opens it (red on main: the meeting's project button, F1); a past-due milestone shows and turns health (as Q3 rules; red on main, F2); the steward face's counts equal the hub's run (red on main, F3); RECEIPTS show the writes (F7); the Steward verb is hit at its centre at 393 (F10); the update list's head and row words are right (F11). Evidence: glass fences through the real hub; shots; the owner-ratified canvas for any new section.
- [ ] 6. **The D2 debts are paid as the owner ratified the list canvas.** `::selection` on the field reaches at least 3:1 against the field at both widths (measured; 1.13:1 on main); the list has no product text under 12 px, no "SHOWNS", every column readable at 393, the sort headers are the library Button, the row menu is in the viewport at 393 (red on main: the grounding's numbers). Evidence: glass fences; the canvas ratification; the web baseline with zero branch-new.
- [ ] 7. **The atlas has a case for each repaired face at both widths**, with an `.op` sibling where the outcome is durable; each new face case fails on main; the Phase 7 and Phase 8 atlas cases still pass. Evidence: the rig runs, red on main and green on the phase head.
- [ ] 8. **The closing use.** Astra drives a cold-context Codex session (the R3 claim, worded exactly: an empty scratch directory, a scratch `HOME`/`CODEX_HOME` with only the auth file, `--ignore-user-config --ignore-rules`, no preamble, the isolated hub the only MCP server; zero repository reads in the retained log; discovery from the catalogue alone) through the job in his words: make a project, add a milestone and a risk, ask what needs him, run the steward, draft and send the update; a second cold session finds that project without its id ("find it cold"). The Room's face at 1440 and 393 shows each result, read back from the hub. Rehearsed, owner-reviewed shots; never recorded as a sitting. The zero-read fence fails on the Phase 5 logs. Evidence: `evidence-story-06.md`, the retained sessions (redacted at capture, handover XXX law 12).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-9-01 | The Room's operations on the contract (and discovery) | backlog | [story-01-the-rooms-operations-on-the-contract](./story-01-the-rooms-operations-on-the-contract.md) | — |
| PHILO-9-02 | The steward and the connectors under Article XI | backlog | [story-02-the-steward-and-the-connectors-under-article-xi](./story-02-the-steward-and-the-connectors-under-article-xi.md) | — |
| PHILO-9-03 | The Room's face tells the truth (canvas first) | backlog | [story-03-the-rooms-face-tells-the-truth](./story-03-the-rooms-face-tells-the-truth.md) | — |
| PHILO-9-04 | The desk debts: the selection and the list face (canvas first) | backlog | [story-04-the-desk-debts](./story-04-the-desk-debts.md) | — |
| PHILO-9-05 | The atlas cases for the Room | backlog | [story-05-the-atlas-cases-for-the-room](./story-05-the-atlas-cases-for-the-room.md) | — |
| PHILO-9-06 | Work in a project room without the repo (Codex) | backlog | [story-06-work-in-a-project-room-without-the-repo](./story-06-work-in-a-project-room-without-the-repo.md) | — |

The stories stay `backlog` until the owner ratifies the charter.

## Lanes (proposed)

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The contract | 01 → 02 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Codex Astra | ../wt-philo-9-01, ../wt-philo-9-02 | feat/philo-9-01-room-contract, feat/philo-9-02-steward-connectors |
| The Room's face | 03 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Codex Astra | ../wt-philo-9-03 | feat/philo-9-03-room-face |
| The desk debts | 04 | Muad'Dib's lane (Fedaykin, Opus 5.5) | Codex Astra | ../wt-philo-9-04 | feat/philo-9-04-desk-debts |
| The atlas and the closing use | 05 → 06 | Astra (Luna) | Muad'Dib | ../wt-philo-9-05, ../wt-philo-9-06 | feat/philo-9-05-atlas, feat/philo-9-06-room-without-the-repo |

01 and 02 are sequential: `holdspeak/operations.py`, `holdspeak/mcp/tools.py`, `holdspeak/mcp/families/project.py` and the generated files have one shipping owner per commit. 03 and 04 run in parallel with 01/02 (face files only); 03's F6-dependent reads wait for 01's Room read. 05 starts after 01–04 merge; 06 last. A lane runs its scoped fences and rig cases only; the full suite is CI's job on the PR.

## Where we are

2026-09-27: DRAFTED from the owner's rulings D1–D3, the BACKLOG row "Projects on the contract", the Phase 8 ledger and the grounding on main `b37dc2fb` (`docs/internal/philo/phase-9/grounding/README.md`): the census (61 MCP + 6 HTTP project identities of 284), the job walked on a real hub on an isolated HOME both ways at 1440 and 393 (F1–F15), and the D2 debts measured (all reproduce; the 393 Zone column is worse than recorded). Owed: the Codex Astra check; the owner's ratification and Q1–Q3; the story 03 canvas (if Q3 keeps the items section) and the story 04 list canvas, each before its face build. Nothing is built.

**Estimate (PROVISIONAL; not grounded per story):** effort **9–13 engineering days** — 01 2–3 (18 descriptors, 7 new item/resource operations, one create path, the discovery words); 02 3–4 (20 descriptors, the admission and receipts Q1 rules, the nudge service without doubles, the suggested-source repair); 03 2–3 (six face repairs, the items canvas if Q3 keeps it); 04 1–1.5 (a token, the list canvas, the list repair); 05 about 1; 06 about 1. The slice is about 1.2 times Phase 7's identities (38 vs 33 MCP) plus new exposure and a face story. Calibration: Phase 7's 11–15 d estimate closed in about two elapsed days; Phase 8's 2.5–4 d closed in about a day and a half, most of it check rounds (Phase 8 story 02 took seven Codex rounds, handover XXX). **Elapsed forecast: about 3–5 days, gated by two canvases, the Codex check rounds and the owner's word.** The range is re-stated after story 01 lands.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope creep into the setup interview, the provider discovery tools or the Room's other postures | high | the enumerated identities are the whole contract scope; the rest is Out with homes | a story edits `project_setup_service.py`, a `provider.*` branch or the Prepare/Ask postures |
| A universal CRUD or discovery framework instead of explicit rows | medium | one descriptor row per operation, naming its callable, schema, result, refusals, exposure and completion (Phase 7 settled) | a generic "project entity" layer, or descriptors generated from the route table |
| Admission that changes authority by accident | medium | Q1 names the admitted writes; existing authority is preserved unless ruled (Phase 7 settled: owner-only is a policy change); boundary fences run with an authenticated principal | a write refused that was allowed on main, without a ruling |
| The face lies again on a path the fences do not cover | medium | each F-number has a glass fence red on main; the steward counts are read from the hub's run in the same fence | a fence green while its hub read-back disagrees with the face |
| The Room's key is repaired in one caller, not all eight | medium | close the class (handover XXX law 9): one registration and a census of every `openSurfaceOr` caller | a caller of `project-room` left with a fallback that is not a route |
| The closing client uses the repository | low | the R3 setup and the zero-read fence, red on the Phase 5 logs; a repository resource read is a read (Phase 7 story 04 C1) | a read of the repository in the retained log |
| Retained sessions carry account data | medium | redact at capture and fence the leak (handover XXX law 12) | an address or token in a tracked file |

## Decisions for the owner

- **Q1 — "Which project writes should go through the kernel with a receipt?"** Article XI.1 names acts that decide, change authority, call a model or cross egress. **Recommended: (a).**
  - (a) The writes that decide, file, act or leave the machine: deciding a review proposal and accepting a review; sending the update; linking or unlinking a meeting; adding or removing a source and changing a watch's rules (they set up reads of GitHub or Jira); running the steward and each effect it takes (a GitHub comment leaves the machine); sending a nudge; changing the steward's policy (unattended runs are a delegation); a model draft. Plain edits (make a project, rename, archive, restore, items, a draft's text) and reads go without. *(The Phase 7 D3 line — "writes that FILE or DECIDE" — carried to the Room.)*
  - (b) Every project write.
  - (c) None in this phase; the debt stays on the BACKLOG. *(Smallest; the steward keeps acting with no kernel receipt.)*
- **Q2 — "May an agent do project work for me?"** **Recommended: (a).**
  - (a) Not in this phase: the closing use runs as the owner; agent credentials keep today's behaviour; the delegation grant stays for the desk (BACKLOG). *(Tenet 1; the Phase 7 grant took a design beat and a canvas.)*
  - (b) Yes: extend the desk grant (Phase 7 R1) to the project writes Q1 admits, with an agent leg in the closing use; DESK palette = ALL is repaired first.
- **Q3 — "Where do I see the things in my project?"** Today a milestone or a risk is stored but the Room never shows it (F2). **Recommended: (a).**
  - (a) The Room shows its items (milestones, risks, dependencies, workstreams, signals) in one section, and health counts a late milestone; I add items by voice or through an agent; the canvas first. *(D1's closing test needs the face to show what the client added; an "add" form is BACKLOG.)*
  - (b) As (a), and the Room also gets an "add" verb for items; the canvas shows both. *(Larger: a form on the face.)*
  - (c) No items on the face; the job's "thing" is a linked meeting or a source only. *(Smallest; the job loses its milestone.)*

## Decisions made (this phase)

- 2026-09-27 — the owner: D1 "Work in a project room"; D2 "Yes, one bounded story"; D3 Codex closes it (AskUserQuestion).
- 2026-09-27 — DRAFTED: six stories; 38 MCP + 6 HTTP identities; the setup interview and the provider discovery tools Out (parked); the grounding on main `b37dc2fb` — Fedaykin docs lane for Muad'Dib.

## Decisions deferred

- Q1–Q3: the owner, at ratification.
- The canonical operation names (`item.create` or `project.item.create`, and the others): story 01's first commit, checked by Codex Astra. Existing public names stay compatible.
- The items section's words and seat, and the list face: their canvases, ratified by the owner before each face build.
- Where the new atlas cases live (`atlas-phase9.json` or an existing file): story 05, against the atlas schema.

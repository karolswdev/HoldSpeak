# Projects, updates and decisions: recipe

Build order for `DESIGN.md`. One slice = one PR in the fast cycle
(`CLAUDE.md`). File and line references come from `MODEL.md` and `RECON.md`
(main `68e49a296`, 2026-10-17); check them against main before you start.

Rules for every slice:

- Tests never touch the owner's real HOME, DB or Keychain.
- Faces obey `docs/internal/UX-CANON.md`: the library Button, no modals, no
  counters of zero, no prose blocks, the 12 px floor, 44 px targets at 393.
- Nothing is deleted. A retired face moves to `_parked/` or behind RAW. Every
  table and MCP tool stays.
- `project_updates` stays the one store of updates; the decision record stays
  the one store the face shows for decisions.
- Egress stays his press: Publish and Nudge prepare; Send sends.

Dependencies on other recipes: P7 needs Automations A2 and A6
(`../workbench/RECIPE.md`). P8 needs Engines E1 and MCP M1 and M2
(`../engines/RECIPE.md`, `../mcp/RECIPE.md`). Everything before P7 stands
alone. P0 and P1 are the urgent ones: they fix the Friday press.

---

## P0. Draft update never freezes the desk and never goes quiet

- **Goal:** pressing Draft update leaves every other window working, and a
  failure says why in the Room.
- **Files:** `holdspeak/web/routes/project_updates.py`,
  `web/src/features/project-room/ProjectRoomCore.tsx` (the head, around
  `:438-447`), `web/src/features/project-room/update/useUpdateController.ts`,
  `web/src/desk/hooks/useEngine.ts`, tests.
- **Changes:**
  - Run the draft operation off the event loop (`asyncio.to_thread`, as
    `project_briefs.py:90` does) in `api_draft_update` (`:95-106`), and in
    every other route in that file that can call a model.
  - In the Room head, draw the draft run state under the button: "Working ·
    LAN Qwen · 23 s" while it runs, and on failure one line in words from the
    409 reason (`no_engine`, `did_not_answer`, `not_usable`) with **Try
    again** and **Use a draft from your records** (which posts
    `generator: deterministic`). Today this state exists in
    `useUpdateController` but only the Update posture draws it.
  - Send a `command_id` with each draft so a failed draft leaves a record.
  - `useEngine`: `no_compatible_assignment` is not "set" (`:51`). With no
    usable engine, the press makes the records draft and says so.
- **Done when:** with a stub engine that sleeps 60 s, `GET /health` answers in
  under 1 s during the draft. With a stub that returns unparseable text, the
  Room shows "The answer could not be read" and both verbs within 1 s of the
  409, at 1440 and 393.
- **Tests:** T1 `tests/integration/test_desk_project_room.py` (health
  answers during a slow draft; the 409 body); T2
  `web/src/features/project-room/__tests__/room.app.test.tsx` (failure line
  rendered from a recorded 409 answer, both verbs drive to their outcome).
- **Not in this slice:** the background engine pass, any layout change.

## P1. Write update: a true draft in under a second, the engine's after

- **Goal:** one press shows a readable draft at once; the engine's version
  replaces it when ready, with Undo.
- **Files:** `holdspeak/services/project_update_service.py`,
  `holdspeak/web/routes/project_updates.py`,
  `web/src/features/project-room/update/` (controller, posture, api),
  `web/src/features/project-room/ProjectRoomCore.tsx`, tests.
- **Changes:**
  - The press first saves the records draft (synchronous, fast) and opens it
    in the Update state, rendered (no markdown marks, no `[UNVERIFIED]`).
    The button label becomes **Write update**.
  - Then it starts the engine pass as a background job (a job row plus a poll
    route, the same pattern as steward runs, `steward_contract.py:209-212`).
    The Update state shows "*Engine* is improving this draft · 14 s" with
    Stop.
  - On success the engine text replaces the draft as a new revision, with
    "Written by *engine* · 41 s" and Undo. If the user edited meanwhile, show
    "A better draft is ready · Use it" instead; never overwrite his words.
  - On failure, one line in words with Try again; the records draft stays.
  - Fix the records draft: `Risks & Blockers` reads meeting risks, risk
    items and notes filed as sources; `source_coverage` lists what was read
    and what was not (replace the constant at `:336`).
  - The edit is a plain in-place text edit of the rendered update; the
    B/I/U/H1 toolbar leaves the Update state.
- **Done when:** on the RECON seed, Write update shows text naming the HSM
  blocker within 1 s; with the LAN engine, its draft replaces it with Undo;
  with an engine stub that fails, the records draft stays with the reason.
  At 1440 and 393.
- **Tests:** T1 `tests/unit/test_project_update_drafter.py` (risks from
  notes and meetings; true coverage), T1 integration for the job and poll;
  T2 `room.app.test.tsx` (draft, replace, Undo, "a better draft is ready"
  after an edit), from recorded hub answers.
- **Not in this slice:** For ▾, Looked at, the automation.

## P2. Leave 1:1s out of updates

- **Goal:** a project update never contains a 1:1 or a People note unless he
  adds it by hand. (Decision 2.)
- **Files:** `holdspeak/services/project_update_service.py` (week sources,
  `:2559-2718`), the meeting kind helper used by People prep, tests.
- **Changes:** classify a linked meeting as a 1:1 when it has exactly two
  speakers and one of them is one of his People, or its title starts "1:1".
  Exclude its summary and its actions from the update text; list it in the
  coverage line as "left out: 1:1 with Mira". Exclude People notes the same
  way. Owed items from a 1:1 that are filed to the project by hand stay.
- **Done when:** on the RECON seed, the draft has no Mira workload text, and
  the coverage line names the 1:1 as left out.
- **Tests:** T1 `tests/unit/test_project_update_drafter.py`.
- **Not in this slice:** any face change.

## P3. The Now wing: where it stands in ten seconds

- **Goal:** the project window answers state, needs you, waiting on, and this
  week on one screen at 1440.
- **Files:** `web/src/features/project-room/ProjectRoomCore.tsx` (head,
  Needs you, folds), a new `web/src/features/project-room/now/` for the three
  blocks, `holdspeak/services/room_health_service.py` (state and reason),
  `holdspeak/services/project_service.py` (`room()` sections), tests.
- **Changes:**
  - Head: the state with its reason ("At risk: tokenization waits on the HSM
    ceremony") from this week's meeting risks, risk items, overdue owed items
    and failing CI. Second line: next date, last update, this week's meetings.
  - Needs you: proposals to Confirm and his own owed items only.
  - Waiting on: other people's owed items grouped by person, one line each.
    No "Hand to coder" on these rows.
  - This week: the three memory pages as Decided, Risks, Changed, each line
    with its source chip; Decided lines open the decision.
  - Remove from the Now wing (move to `_parked/` where they are components):
    the five folds, Files, Briefs, Unfinished, the footer `READ · NEXT CHECK`
    and Refresh. Wings read **Now** and **History**.
  - Phone: the one-column order in `DESIGN.md`.
- **Done when:** on the RECON seed, at 1440 without scrolling: "At risk" with
  the HSM reason, Needs you holds the guild agenda item, Waiting on shows
  Theo 2, Jun 2, Mira 1, and This week shows the confirmed decision and the
  runbook risk. At 393 the head and Write update are on the first screen.
- **Tests:** T1 `tests/integration/test_desk_project_room.py` (state and
  reason from the seed); T2 `room.app.test.tsx`; T3 the desk sweep covers the
  window at both widths.
- **Not in this slice:** Nudge, Ask routing, Sources line.

## P4. Projects and Decisions in Go; withhold dead verbs

- **Goal:** he reaches any project and the Decisions window in one press, and
  the palette lists only verbs that work.
- **Files:** `web/src/desk/applications.ts`, the Go menu and phone launcher
  sources, `web/src/desk/verbRegistry.ts` (`:469-482`, `:1039-1045`, the
  "Select a Project" rows), tests.
- **Changes:** add **Projects** (a list window: name, state and reason, next
  date, NEW update) and **Decisions** (the existing `DecisionsView` as its
  own window) to Go and the phone launcher. Withhold palette verb rows whose
  subject is missing. The Object menu and palette "Draft update for X" press
  Write update in that project instead of opening the list. Rename the
  palette's `Project · AGENT` persona out of the way of projects (it is a
  saved persona; cluster F decides its fate; until then list it after
  projects).
- **Done when:** Go shows Projects and Decisions at 1440; the phone launcher
  shows them; ⌘K "draft update" lists only "Write update for Payments
  migration", and Enter writes one.
- **Tests:** T2 `web/src/desk/__tests__/menus.app.test.tsx`,
  `palette.app.test.tsx`; T3 the sweep (every app in `applications.ts`).
- **Not in this slice:** the Decisions data model (P9).

## P5. Sources in one go

- **Goal:** a new project gets its meetings, notes, people and outside
  sources from one paste and one Add all.
- **Files:** `web/src/features/project-room/door/DoorCore.tsx`,
  `door/useDoorController.ts`, `door/api.ts`,
  `holdspeak/services/project_door_service.py`, a small URL parser module,
  the meeting search used by Search, tests.
- **Changes:**
  - One paste field that parses GitHub repository, Jira URL or key, and
    Confluence space URLs into source rows; each row validates through the
    existing provider validate tools and shows its sign-in state in words.
  - Stop marking unchecked sources as "test passed"
    (`project_door_service.py:274-277`); run the check, or say "not checked".
  - Found: meetings and notes that match the name and its words, with Add all
    and a remove cross per row; People from their speakers.
  - Sign in unfolds the one command with Copy and Recheck in place, the same
    component as the Accounts row.
  - In the project window, the Sources line unfolds the same rows plus each
    source's state in words; new matching meetings appear as Needs you rows
    ("mentions payments · Add").
  - Meeting ▸ More ▸ Add to Project lists the projects directly (one step,
    not a scroll to a second button).
- **Done when:** on the RECON seed, typing "Payments migration" lists the
  three meetings and two notes; Add all and Create project open a window whose
  This week is already filled, in at most 6 presses. A pasted
  `github.com/acme/payments` shows "not signed in on this Mac" in the rig.
- **Tests:** T1 `tests/unit/test_project_door_service.py` (URL parsing, no
  fake "passed"), T1 integration for Found; T2 a door app test from recorded
  answers.
- **Not in this slice:** watch rule editing (stays behind RAW).

## P6. Nudge and Ask, in their homes

- **Goal:** Waiting on rows nudge through Send, and Ask opens the one Ask
  window.
- **Files:** `web/src/features/project-room/now/`, the Room's Ask well
  (`ProjectRoomCore.tsx:2302`), the nudge routes (`api.ts:229`, `:238`),
  `holdspeak/services/project_steward_service.py` (the nudge text builder),
  tests.
- **Changes:** Nudge on a Waiting on row prepares a reviewer nudge for the
  item's place (a PR comment through the existing nudge path; Jira, Slack or
  email through the Send well when the item has that destination) and opens
  the Send well; the row shows "Nudge ready". Without a place to send, no
  Nudge. The Ask field opens the Ask window with About = this project; the
  Room's own answer well and Unfinished list are parked.
- **Done when:** on a seeded PR item, Nudge shows a prepared comment in the
  Send well and nothing is sent until Send. Typing a question and Enter opens
  the Ask window scoped to the project.
- **Tests:** T2 `room.app.test.tsx`, `send.app.test.tsx`; T1 for the nudge
  text.
- **Not in this slice:** the automation starter for nudges (P7).

## P7. The update is an automation; the steward folds in

- **Goal:** the Friday update runs by itself, and the steward's jobs live in
  Automations and Needs you. (Decision 1.)
- **Needs:** Automations A2 (one instruction + sources, one result per run)
  and A6 (Put it in).
- **Files:** `holdspeak/services/workbench_service.py` and the runner (a
  project-update result kind that writes a `project_updates` row),
  `holdspeak/services/project_update_service.py`,
  `web/src/features/project-room/ProjectRoomCore.tsx` (Update line, Steward
  posture behind RAW), `holdspeak/workbench_templates.py` (starters),
  tests.
- **Changes:**
  - The first Write update in a project creates its update automation (When:
    only when pressed; Do: the update text with For; About: this project;
    With: the engine for Drafts and updates; Put it in: this project's
    updates) and runs it as P1's engine pass.
  - The Update line shows When and With and NEW; "Every Friday at 15:00" turns
    the schedule on in one press; Open shows the newest update.
  - Starters: **Friday update** (asks which project) and **Nudge on waiting
    reviews** (When: a PR in a project's repository waits 2 days; Put it in:
    Needs you).
  - Steward proposals become Needs you rows; the Steward posture and policy
    move behind RAW; past steward runs show in History as plain events.
- **Done when:** a scheduled Friday update writes a `project_updates` row and
  shows NEW in the project and in Today; the Steward face is not reachable
  without RAW.
- **Tests:** T1 `tests/integration/test_desk_workbenches.py` (a project
  update result row), `tests/integration/test_desk_project_room.py`; T2
  `room.app.test.tsx`.
- **Not in this slice:** tools for the engine.

## P8. The agent writes the update

- **Goal:** with Claude Code (or any tool engine), the update is written by an
  agent that reads the project itself and cites what it used.
- **Needs:** Engines E1, MCP M1 (one-shot runs with the desk's tools) and M2
  (Looked at).
- **Files:** the automation runner's tool path, `holdspeak/services/project_update_service.py`
  (plain-text engine contract), `holdspeak/mcp/families/project.py`
  (`project.update_draft` takes sources and engine), the Update state
  (Looked at), tests.
- **Changes:**
  - A tool-capable engine gets the CONDUCTOR set and the Do text from
    `DESIGN.md`; it saves its text through `project.update_draft` with the
    sources it read.
  - An engine without tools gets the records draft and the three pages as its
    material and returns plain text. Drop the JSON-schema response contract
    for the update; keep claim support as a check on the cited refs, shown as
    Looked at, not as `[UNVERIFIED]` marks.
  - Looked at lists every tool read of the run, each a link.
- **Done when:** with Claude Code and no About beyond the project, Run now
  writes an update that names this week's meetings and decisions, leaves out
  the 1:1, and Looked at lists real links. No run sends anything.
- **Tests:** T1 with a recorded agent transcript at the CLI seam; T2 for
  Looked at.
- **Not in this slice:** Gmail or other connectors (MCP decision 2).

## P9. One decision record

- **Goal:** every decision is one record with one home, and every other place
  links to it. (Decision 3.)
- **Files:** `web/src/desk/decide.ts`, `web/src/desk/pullouts/DecisionPullout.tsx`,
  `web/src/desk/pullouts/views/DecisionsView.tsx`,
  `holdspeak/services/decision_record_service.py`,
  `holdspeak/services/project_service.py` (`:2270-2333`), the desk zone for
  Decisions, a one-time copy of desk decisions into records, tests.
- **Changes:**
  - New Decision and the meeting's Decide well create a decision record
    (with the existing `create_from_desk` path), with About and Why; never a
    loose desk object.
  - The project reads decisions by project: linked meetings or filed to it.
  - The desk icon named Decisions opens the Decisions window.
  - Today ▸ Decisions becomes a link to the Decisions window; Today's Needs
    you shows "Confirm" rows for proposed decisions.
  - A one-time, idempotent copy of existing desk decisions into records; the
    `desk_decisions` table stays.
  - "Due for periodic review" only from the record's review date
    (`project_delta_service.py:238`, `:479`).
  - Remove the shadowed `GET /api/decisions` handler from the face's path
    (`holdspeak/web/routes/primitives/decisions.py:58`) by parking it.
- **Done when:** a decision made with New Decision from a project shows in
  the project's This week, in Decisions, and behind the desk icon; the
  steward no longer flags it minutes later.
- **Tests:** T1 `tests/unit/test_decision_records_routes.py`,
  `tests/integration/test_desk_project_room.py`; T2 a decisions app test.
- **Not in this slice:** supersede chains on the face beyond what exists.

## P10. Watches tell the truth underneath

- **Goal:** rules offer only actions that run, and the MCP layer stops
  importing web routes.
- **Files:** `holdspeak/watch_validation.py`, the rule editor behind RAW,
  `holdspeak/mcp/families/project.py` (`:1205-1241`), a small shared module
  for the provider list and steward serializers, tests.
- **Changes:** stop offering rule actions that nothing drains
  (`project.update.draft`, `project.propose`, `door.add_item`, `workbench.*`,
  `cadence.upsert_loop`); keep `project.observe` as the default and stop
  writing a pending effect row for it (the observation is the effect). Leave
  existing rows in place. Move `_NATIVE_PROVIDERS`,
  `collect_provider_manifests` and the steward serializers out of the web
  routes into a service module both import.
- **Done when:** a new watch writes observations and no pending effect rows;
  `holdspeak/mcp` imports nothing from `holdspeak/web/routes`.
- **Tests:** T1 `tests/unit` watch validation and an import-boundary test.
- **Not in this slice:** any face.

# Today, Needs you and People: recipe

Build order for `DESIGN.md`. One slice = one PR in the fast cycle
(`CLAUDE.md`). File and line references come from `MODEL.md` and `RECON.md`
(2026-10-17, head `217001b2e`); check them against main before you start.

Rules for every slice:

- Tests never touch the owner's real HOME, DB or Keychain. Test doubles
  replay recorded real hub answers (`scripts/record_needs_you_fixture.py`,
  `web/src/test/recordedHub.ts`), never typed ones.
- Faces obey `docs/internal/UX-CANON.md`: the library Button, no modals,
  no counters of zero, one true line for an empty state.
- Nothing is deleted. A retired face moves to a `_parked/` folder. Stored
  data stays: action items, decision commitments, cadence loops, People
  records, brief rows, shelf state, notified ids.
- People stays encrypted. Agents read People; only the owner writes it.
- The seed of the recon (three meetings, Mira, Theo, Jun) is the fixture
  for every "done when". Record it once in D0 as
  `tests/fixtures/daily_week/` through the product's own producers.

Dependencies: D9 needs Automations A2 to A6 (`../workbench/RECIPE.md`) and
MCP M1 (`../mcp/RECIPE.md`). D8's quiet "finished" notice for agents pairs
with the agents cluster's fleet slice (`../herdr/STUDY.md` idea 4); D8 ships
the rule and the results half without it.

---

## D0. Every row knows its person, its direction and its date (backend)

- **Goal:** Mira's promise shows in Mira's prep, and "by Wednesday" means a
  date, without any press.
- **Files:** `holdspeak/intel/parsing.py` (around `:214`, the `due` read),
  the action-item write path, `holdspeak/services/people_service.py`
  (`resolve_relationship_by_owner` `:1245`, `resolve_owner_candidates`
  `:1394`, `open_meeting_actions` `:687-749`),
  `holdspeak/services/needs_you_membership.py` (`_is_self` `:526`,
  `_waiting_on` `:531`, `_person_identity` `:536`),
  `holdspeak/services/follow_through_service.py` (`_lane` `:863-892`),
  tests, the new fixture.
- **Changes:**
  - Resolve a said due ("Wednesday", "Friday next week", "this week",
    "Nov 5") to an ISO date against the meeting's start date when the
    item is stored. Keep the said words as `due_said`. Unresolvable words
    stay as words with no date.
  - Owner resolution: an owner string that matches exactly one person by
    alias, full name, or first name resolves to that person. Two matches
    stay unresolved and say so (`ambiguous`). No alias press needed for
    the unique case.
  - Every Needs-you row gets `direction` (`mine`, `theirs`, `decide`,
    `setup`) and `person_id`. For a *mine* row, `person_id` is the other
    attendee of a two-person meeting, or a person named once in the text;
    else empty.
  - People's 1:1 brief adds *mine* rows for this person to `I owe` (from
    the same rows), next to the typed `leader_owes` commitments.
  - Lanes use the resolved date, so "Monday" in two days is due soon.
- **Done when:** on the fixture, Mira's brief lists "Draft the rollback
  runbook · due Tue 20 Oct" with no alias set; Theo's brief lists "Review
  design doc on settlement retries" under I owe; `GET /api/desk/needs-you`
  rows carry `direction` and `person_id`; "Friday next week" from a
  Thursday meeting resolves to the Friday of the following week.
- **Tests:** T1 (`tests/unit/test_desk_needs_you.py`; a new
  `tests/integration/test_desk_people.py`; the parsing unit tests).
- **Not in this slice:** any face change.

## D1. One number, true labels

- **Goal:** the bell, the Dock, the desk icons and Today show the same
  number, and no row says a wrong thing.
- **Files:** `holdspeak/services/needs_you_membership.py` (the count,
  `:1381`), the project icon badge source (trace it: it showed 12 vs 11),
  `web/src/desk/pullouts/views/FollowThroughView.tsx` (`:121` the label,
  `:127` the 10-character cut), `holdspeak/services/monday_brief_service.py`
  (a failure row that later succeeded), the setup row in
  `web/src/desk/needs/NeedsDrawer.tsx`.
- **Changes:**
  - The count rule: *mine* due today or late + *decide* + blocked agents +
    setup that blocks his own work. *Theirs* never counts. One function;
    every badge reads it; a project badge is the same rule filtered to the
    project.
  - An action item links "Open meeting", not "Open decision".
  - Due shows once, as a date, never cut.
  - The brief drops a "did not start" row when the same job later
    succeeded.
  - The setup row has one verb (`Choose engine`), not `SET` plus another.
- **Done when:** on the fixture after nine keeps, the bell, the Dock and
  the project icon all show 4 (or the project's share), at 1440 and 393;
  the brief has no stale failure row; Follow-through rows read "Open
  meeting" and full dates.
- **Tests:** T1 for the count and the brief; T2 (`bell.app.test.tsx`,
  `dock.app.test.tsx`); T3 the desk sweep.
- **Not in this slice:** new filters, Today layout.

## D2. Needs you: the filters and one verb per row

- **Goal:** "what does Theo owe me" is two presses from anywhere.
- **Files:** `web/src/desk/needs/NeedsDrawer.tsx` (`FILTERS` `:470-478`,
  the row verbs `:137-324`), `web/src/desk/needs/needsFace.ts`,
  `holdspeak/web/routes/projects.py:619` (filter params), the vitest.
- **Changes:**
  - Chips: **Mine**, **They owe me**, **To decide**, **This week**, a
    person picker, a project picker. Chips combine. A chip shows its count
    and is absent at zero. The time-class chips leave; ranking keeps their
    order. Muted moves to More.
  - The `Work · N` group header goes; the list is ranked with no groups.
  - One primary verb by direction: Done, Nudge, Decide, or the setup verb.
    **Nudge** opens the Send well with a short drafted message to that
    person (the egress rule: he presses Send). More holds Open, Later, Add
    to project, Drop.
  - The route accepts `direction`, `person`, `project`, `week` and the
    MCP tool `desk.needs_you` gets the same arguments (`holdspeak/mcp/tools.py:413`).
- **Done when:** on the fixture, `They owe me` + `Theo` shows exactly
  Theo's two rows; `Mine` shows two rows with Done; at 393 the chips
  scroll in one row and no verb is cut.
- **Tests:** T1 (`tests/unit/test_desk_needs_you.py` for the filters); T2
  (`needs-you.app.test.tsx`); T3 sweep.
- **Not in this slice:** meeting groups (D3), Today (D4).

## D3. Promises from a meeting (owner decision 1)

- **Goal:** after a meeting, its promises are tracked with zero presses
  (or one), and a wrong one goes with one.
- **Files:** the proposal bridge (`holdspeak/services/proposal_bridge_service.py`
  and `needs_you_aggregate.py` around `:545-560`), `NeedsDrawer.tsx`, the
  meeting Outcomes face only where it shares the verbs, tests.
- **Changes:**
  - With decision 1 = yes: a finished summary keeps its promises that have
    an owner (the same write that Confirm does today), marked NEW and
    grouped under the meeting at the top of Needs you until seen. Each has
    **Drop** with Undo. Decisions stay *decide* with **Decide**.
  - With decision 1 = no: the group shows **Keep all N** and per-row Keep
    and Drop.
  - A promise with no owner stays pending and asks "Whose?" with the
    meeting's speakers as one-press choices.
  - Proposals never count in the bell until kept (D1's rule).
- **Done when:** on the fixture, the three summaries end with nine tracked
  rows and two decisions to decide, with no Confirm press; Drop on "Do it"
  removes it and Undo brings it back.
- **Tests:** T1 (the bridge); T2 (`needs-you.app.test.tsx`,
  `meetings.app.test.tsx` where verbs are shared).
- **Not in this slice:** extraction quality (the meetings cluster).

## D4. Today is one page

- **Goal:** he opens Today and sees the number, the first meeting and his
  first thing without a press.
- **Files:** `web/src/desk/pullouts/IntelligencePullout.tsx`,
  `web/src/desk/pullouts/views/TodayView.tsx`,
  `web/src/desk/pullouts/views/BriefView.tsx` (becomes the Since-yesterday
  fold), `web/src/desk/verbRegistry.ts:367-377` ("Open Intelligence" →
  "Open Today"), the brief route (generate on read when missing), a new
  `web/src/desk/__tests__/today.app.test.tsx`.
- **Changes:**
  - No wings. Order: header (date, Record now), Needs you top 5 with All,
    the day rail, Since yesterday (Since Friday on Monday) folded to a
    count line, This week folded to counts per day.
  - Since yesterday is generated when Today opens and no brief exists for
    the period; no Generate or Refresh on the face.
  - Follow-through moves to `_parked/`; the Decisions wing becomes a link
    to the Decisions app in Since yesterday.
  - Empty desk: one line, "Your meetings and calendar fill this.", with
    Connect calendar and Record now.
- **Done when:** on the fixture at 1440 and 393, Today shows "4" in Needs
  you, the next 1:1 with Prep, and Since yesterday with "3 meetings · 2
  decisions · 9 promises", with no press; the empty desk shows its one
  line.
- **Tests:** T2 (`today.app.test.tsx`); T1 (`tests/unit/test_desk_brief.py`
  for generate-on-read); T3 sweep (the wing list changes).
- **Not in this slice:** the Prepared block (D9), retiring the windows (D5).

## D5. Retire the Brief and The week windows

- **Goal:** one place for the start of the day; the menus stop offering
  three.
- **Files:** `web/src/desk/chair/chairWindows.ts:36-41`,
  `web/src/desk/components/DeskMenuBar.tsx:59-64` (phone Go),
  `web/src/desk/verbRegistry.ts:865-878` (chair window verbs),
  `web/src/desk/chair/ChairHome.tsx` (park the Brief and Week sections and
  the dead `NeedsYouSection`), the hub window service (close parked ids on
  load).
- **Changes:** Window ▸ Desk and the phone's Go list **Today**, **Needs
  you**, **Capture**. A desk that has `chair:brief` or `chair:week` open
  closes it on load and opens Today in its place, once.
- **Done when:** at 1440 and 393 no menu offers Brief or The week; a desk
  restored with `chair:week` open shows Today instead, with no error.
- **Tests:** T1 (`tests/integration/test_desk_chair.py` for the window
  ids); T2 (`chair.app.test.tsx`, `menus.app.test.tsx`); T3 sweep.
- **Not in this slice:** Capture.

## D6. People from his work

- **Goal:** his three reports exist after three presses and no typing.
- **Files:** `holdspeak/services/people_service.py` (a suggestion read
  and an add-from-suggestion write), `holdspeak/web/routes/people.py`,
  `web/src/pages/cores/PeopleCore.tsx` (`:345`, `:372-383`, `:497-505`),
  `holdspeak/mcp/families/people.py`, tests.
- **Changes:**
  - `GET /api/people/suggestions`: names from meeting speakers and owners
    that match no person (with counts and the meeting), "1:1 with X"
    calendar series and series with one other attendee, and, when Jira is
    connected, assignees on his projects. Reads only.
  - **Add** creates the person (full name from the calendar or Jira when
    known; kind Report for a 1:1 series, else Peer), links the spoken name
    as an alias and the series. **Not a person** hides the name for good.
  - No `Set up People` step: the first add creates the store. The empty
    line: "People you meet appear here."
  - A failed People read draws "People could not be read · Try again" in
    place, in People, Today and Needs you. Log the readiness value and the
    caller on each 503 so the cause of the open 503 can be found.
  - MCP: `people.suggestions` (read). Adding stays owner-only.
- **Done when:** on the fixture with no people, People lists Mira, Theo
  and Jun under From your meetings; three Add presses make them, and Mira's
  prep shows her promise with no other step; "Do it" never appears as a
  name; at 393 each suggestion row fits with both verbs.
- **Tests:** T1 (`tests/integration/test_desk_people.py`); T2
  (`people.app.test.tsx`); T3 sweep.
- **Not in this slice:** Jira assignees if no Jira read exists yet (then
  it is the next PR).

## D7. The 1:1 prep

- **Goal:** one press from Today gives a prep he can walk into the room
  with.
- **Files:** `web/src/pages/cores/PeopleCore.tsx` (PrepPane `:779-1040`),
  `web/src/desk/people/prepData.ts`, `people_service.py` (the brief
  `:448-543`: last meeting, points), tests.
- **Changes:** columns titled **{Name} owes me** and **I owe {Name}**, both
  from the one list (D0); **Nudge** on her rows; **To raise** with the voice
  mic and *suggested* points (from D9 when present) with Add; **Last time**
  (the last meeting with her, its points and decisions, Open). Context,
  History and Info become folds under the prep. `Pick from calendar` goes
  (series come from D6).
- **Done when:** from Today's NEXT card, Prep opens Mira's prep with her
  promise, Last time, and the next 1:1 time, at 1440 and 393.
- **Tests:** T2 (`people.app.test.tsx`); T1 for the brief fields.
- **Not in this slice:** the suggestions engine (D9).

## D8. Notices only for what needs him (owner decision 2)

- **Goal:** every notice in a week is about something of his that is due.
- **Files:** `holdspeak/services/heartbeat_service.py` (`:915-1050`),
  `holdspeak/desktop_notify.py` (`:60-156`, `:271`), the web presence
  (which window is in front), Settings ▸ Rhythm, tests.
- **Changes:**
  - Notify on: a *mine* row turning due or late; a *decide* row whose
    meeting starts within 30 minutes; a blocked agent (as today); 10
    minutes before a 1:1 ("Prep ready"). Never on *theirs*, unseen
    promises, or count changes.
  - At the end of quiet hours, one morning notice replaces the backlog
    and opens Today.
  - No notice for the window in front (the desk reports its front window
    to the hub).
  - Decision 2 = yes: a finished automation result raises a quiet notice
    and a NEW line in Today until opened (the seen bit). Agents join when
    the agents cluster ships its fleet slice.
- **Done when:** a sweep on the fixture fires for Email Dana (mine, due
  today) and not for Theo's rows; the morning notice reads "4 need you ·
  first: 1:1 with Mira 20:15"; with Needs you in front, no notice fires.
- **Tests:** T1 (heartbeat unit tests; `HOLDSPEAK_DESKTOP_NOTIFY=0` keeps
  posts off and records the decision).
- **Not in this slice:** sounds.

## D9. Morning prep (after Automations A2–A6 and MCP M1; owner decision 3)

- **Goal:** the day is prepared before he arrives.
- **Files:** the Automations starters list, `Put it in: Today` as a
  destination, `TodayView.tsx` (the Prepared block), tests.
- **Changes:**
  - A starter **Morning prep** with the sentence in `DESIGN.md`. With
    decision 3 = yes, it is created on and set to weekdays 07:30 once a
    tool-capable engine exists.
  - Its result renders as Today's Prepared block: one card per meeting
    today (each side's open items, points to raise as *suggested*), mine
    due today, and drafted nudges as Prepared sends. Looked at lists what
    it read.
  - **Prepare now** in Today's header menu runs it once.
- **Done when:** on the fixture with a stub tool-capable engine replaying
  a recorded run, Today shows the Prepared block with a card for the 1:1
  with Mira; Add on a suggested point puts it on her agenda; the engine's
  name shows on the block.
- **Tests:** T1 (the run makes one result with Put it in Today); T2
  (`today.app.test.tsx`).
- **Not in this slice:** other starters.

## D10. MCP parity

- **Goal:** an agent can ask what he sees.
- **Files:** `holdspeak/mcp/tools.py` (`desk.needs_you`), a `today.get`
  read, `holdspeak/mcp/families/people.py`.
- **Changes:** `desk.needs_you` with `direction`, `person`, `project`,
  `week` (from D2); `today.get` returns the Today page as data (Needs-you
  top, the day, Since yesterday, Prepared); `people.suggestions` (from D6).
  Writes keep their classes: Done and Drop are WORK; Decide and People
  writes stop for his press from an agent.
- **Done when:** `desk.needs_you(direction="theirs", person="Theo")` returns
  Theo's two rows; `today.get` matches the face on the fixture.
- **Tests:** T1 (`tests/mcp/`).
- **Not in this slice:** none.

# The daily surface and People: the code map

Read from the code of the owner's desk head (`217001b2e`, worktree
`wt-daily-delight-delivery-20261017`). Line numbers are from that head;
check them against main before a slice starts. Paths are relative to the
repository root.

## 1. What each face is in data

### Today (the window `intelligence:desk`)

- One pullout with four wings: `Day`, `Brief`, `Follow-through`,
  `Decisions` (`web/src/desk/pullouts/IntelligencePullout.tsx:16-22`). The
  last wing used is kept in localStorage `hs.desk.intelligence-view`
  (`:14`).
- **Day** (`web/src/desk/pullouts/views/TodayView.tsx`) makes four reads
  at once (`:165-170`): `GET /api/door` (`holdspeak/web/routes/door.py:19`
  → `DoorService.get`, `holdspeak/services/door_service.py:136-170`:
  `board{overdue,now,waiting,unassigned,active}`, `upcoming`, `counts`,
  `calendar_configured`, `week`), `GET /api/meetings?limit=40`,
  `GET /api/desk/needs-you`, and People readiness plus
  `/api/people/relationships?counts=1` (`:111-124`).
- Day draws: head (weekday, "N meetings ahead", `Record now`), the time
  rail with the NEXT card (`Open prep`, `Record`, arm), later meetings,
  "to finish" rows, then a side with `OWED` (only People-typed
  commitments, `:445-453`) and `TO DECIDE`, which shows **one** proposal:
  the first decision, else the first proposal (`:217-218`).
- "Intelligence" is still the code name: the verb `desk.open-intelligence`
  "Open Intelligence" (`web/src/desk/verbRegistry.ts:367-377`), the object
  kind `intelligence` (`web/src/desk/api.ts:158`), the editors registry
  (`web/src/desk/pullouts/editors/registry.ts:27`), aria labels.
- `holdspeak/services/front_door_service.py` is the engine-setup
  recommender, not Today.

### Brief

- Routes under `/api/brief` (`holdspeak/web/routes/monday_brief.py:87`):
  `GET /latest` (`:98`), `POST /generate` (`:116`), shelf (`:126`, `:130`),
  `GET /{id}` (`:146`).
- Producer: `MondayBriefService.generate`
  (`holdspeak/services/monday_brief_service.py:631`). Sections
  `this_week, changed, broke, waiting, decisions` (`:21`, assembled
  `:814-830`). `waiting` copies the Needs-you list
  (`_collect_needs_you`, `:1201-1267`). A brief exists only after a
  Generate press or a cadence run.
- Two faces render it: Today ▸ Brief (`web/src/desk/pullouts/views/BriefView.tsx`)
  and the Chair window `chair:brief` (`web/src/desk/chair/ChairHome.tsx:1252-1384`,
  registered `web/src/desk/chair/chairWindows.ts:38`). They use different
  verb words (`Acknowledge` vs `Ack`) and different extras (Today has
  Speak, People and Add to 1:1 agenda; the window has the Send well).
- The phone's Go "Brief" opens Today ▸ Brief, not the window
  (`web/src/desk/components/DeskMenuBar.tsx:59-64`).
- `cadence.brief` (`holdspeak/mcp/families/cadence.py:52`) is a third,
  separate "morning brief" from the cadence service.

### Needs you

- `GET /api/desk/needs-you[?fresh=1]` (`holdspeak/web/routes/projects.py:619`)
  → `needs_you_membership.compose` on each request (`:635-636`); a
  900-second cache covers only the Room part.
- Sources (`holdspeak/services/needs_you_membership.py:10-25`): the Door
  board's asking columns, which include meeting action items, decision
  loops and People commitments (`:80-124`); Room rows (CI, reviews, Jira,
  milestones, Room commitments, review bottlenecks); unfiled meeting
  proposals; engine blockers and failed summaries; decisions to review
  (`:145`); coder agents waiting in the last 30 minutes (`:218`); held
  tool calls (`:328`); armed recordings.
- Not in it: automation results (zero matches), finished agents.
- "Mine" today: `SELF_OWNER_NAMES = {"me", "you", "manager"}` plus the mic
  label and configured owner names (`:520`, `_is_self` `:526-528`). The
  face shows `YOURS`. "Theirs" is `WAITING ON <OWNER>` (`_waiting_on`,
  `:531-533`), counted out of the number.
- Ranking: overdue > due today > not run > no due date > waiting
  (`holdspeak/services/attention_ranking.py:44-46`, `:94-121`).
- Count = members + unread source groups + arming (`needs_you_membership.py:1381`).
  The browser polls about once a minute (`web/src/desk/needsYou.ts:917-934`).
  The bell, Dock and Screen read it; the project icon badge did not match
  it in the walk (12 vs 11, 5 vs 4), cause not traced (**unknown**).
- Filters are time classes: `All, Overdue, Due today, Not run, No due
  date, Waiting, Muted` (`web/src/desk/needs/NeedsDrawer.tsx:470-478`), an
  empty filter is hidden.
- ChairHome still builds a `NeedsYouSection` that is never drawn
  (`ChairHome.tsx:1079`, `:1182`, `:1197`); `chair:needs` renders
  `NeedsDrawer` (`chairWindows.ts:45`).

### The week

- Chair window `chair:week` (`chairWindows.ts:39`), body in
  `ChairHome.tsx:1385-1470`: the week strip (`door.week`,
  `door_service.py:163`, `:564`), calendar meetings, armed recordings,
  recorded meetings with `RAN`/`REFUSED` chips, thoughts, and this week's
  decisions and Door cards (`:2224-2250`).
- The "Prep 1:1 with X", "Draft update for P" verbs
  (`verbRegistry.ts:1019-1046`) exist only as palette rows.

### Notifications

- Desktop notice: `desktop_notify.notify` (`holdspeak/desktop_notify.py:271`).
  Raised by the heartbeat sweep over the Needs-you list
  (`holdspeak/services/heartbeat_service.py:915-1050`, body "N need you
  [across P projects]", `:1031-1034`) and by the coder edge when a session
  starts waiting (`:887-908`).
- Edge rule: fires on new item ids or escalations, not on count changes
  (`desktop_notify.py:60-156`); notified ids are stored
  (`heartbeat_service.py:263`). Waiting and muted rows never fire (`:945`).
  Quiet hours 22:00–08:00 hold notices and deliver once afterwards.
- Switches: `notify: off | edge | every_sweep` (`:41`, `:935`),
  `quiet_hours`, `muted_projects`, env `HOLDSPEAK_DESKTOP_NOTIFY=0`.
- In-desk: the Qlippy ambient layer (`web/src/components/AmbientLayer.tsx:312-500`),
  only when the mascot is on; the shade is parked
  (`web/src/desk/components/SystemShade.tsx:2`). No toast emitter found.
- No rule "never for the window in front" exists. Done does not notify by
  design (`docs/internal/CONDUCTOR.md:56`).

### People

- One encrypted SQLite file, one key in the keystore
  (`holdspeak/people/store.py:19`). Kinds: relationship, one_on_one,
  agenda_item, request, commitment, grounding_note
  (`holdspeak/services/people_service.py:52-54`).
- Commitments carry a direction: `leader_owes` ("You owe", from an
  accepted request) and `report_owes` ("They owe you", `/owed`)
  (`:58-67`, `:234-306`).
- The 1:1 brief (`:448-543`) adds `open_meeting_actions`: accepted action
  items whose owner string resolves to **exactly** this person
  (`:687-749`) through `owner_aliases` (`:1175-1224`). A display name is
  not an alias, so "Mira" in a meeting never reaches "Mira Okafor" until
  he adds the alias (walk §4).
- My own meeting items (owner "Me") never reach a person's `YOU OWE`:
  nothing stores "about whom".
- Creation: one path, `create_relationship` (`:138-151`), from the face
  form (`web/src/pages/cores/PeopleCore.tsx:345`, `:497-505`) or MCP
  `people.relationship.create` (`holdspeak/mcp/families/people.py:365-372`).
  Nothing proposes a person from meetings, calendar or Jira.
  `LinkSuggestions` links a calendar series to a person who exists
  (`PeopleCore.tsx:1143-1144`).
- **The 503.** Every read calls `_require_ready_owner`
  (`people_service.py:1598-1609`), which raises `people_store_unavailable`
  for any readiness other than `ready` (unconfigured, locked,
  key_unavailable, corrupt, unavailable), and the route maps it to 503
  (`holdspeak/web/routes/people.py:16-41`). The store re-reads the key
  file on each get. In the walk the store was ready and no 503 came. The
  recorded 503s were intermittent in rig quick checks (`pm/STATUS.md:807-812`).
  Which reader hits a not-ready store, and why readiness flips, is
  **unknown**. Today guards its own read (`TodayView.tsx:113-114`).
- Agents may read People through MCP; writes are owner-only (owner ruling
  2026-10-06).

### Follow-through

- `FollowThroughService` (`holdspeak/services/follow_through_service.py`)
  reads `action_items` joined to `decision_commitments` and `meetings`
  (`:777-795`), plus `cadence_loops` (`:245-275`); People adds only
  `leader_owes` commitments as cards with owner `"you"`
  (`people_service.py:1512-1539`); "They owe you" commitments are left out
  (`:1520`).
- Lanes (`_lane`, `follow_through_service.py:863-892`): pending review or
  no owner → `unassigned`; no due → `waiting`; past due → `overdue`;
  due in 2 days → `now`; else `waiting`. Because `due` is the string the
  meeting said ("Wednesday"), nothing in the walk ever became `now` or
  `overdue`.
- Owner is free text. The face truncates the due to 10 characters
  (`web/src/desk/pullouts/views/FollowThroughView.tsx:127`, "Friday nex")
  and labels a confirmed action item "Open decision" because the confirm
  links it to a decision (`:121`).
- Verbs: done, dismiss, snooze, delegate, reopen (Undo, 8 s), due
  (`follow_through_service.py:405-430`).

## 2. Dead, duplicate and wrong verbs

| Verb | Where | Problem |
|---|---|---|
| `SET` and `Choose an engine` | one Needs-you setup row (`e06-bell-1440.png`) | two verbs for one step |
| `Confirm` / `Not now` on a proposal | Today TO DECIDE (`TodayView.tsx:468-472`), Needs you (`NeedsDrawer.tsx:223-235`), the Chair (`ChairHome.tsx:2092`) | three homes |
| `Done` on a follow-through item | Needs you (`:193`, `:344`), the Chair (`:1625`, `:1993`), Follow-through, People prep (`PeopleCore.tsx:850`) | four homes |
| `Generate` / `Refresh` brief | Today ▸ Brief and the Brief window | two homes; needed at all only because no brief is ready |
| `Ack` / `Acknowledge`, `Defer` | the Brief window and Today ▸ Brief | one verb, two words |
| `Connect calendar` | Today (`TodayView.tsx:404`), Needs you (`NeedsDrawer.tsx:317`, `:650`) | three buttons |
| `Pick from calendar` | People prep | jumps to another tab and a fold instead of picking |
| `Open decision` on an action item | Follow-through | wrong label (`FollowThroughView.tsx:121`) |
| `Open Intelligence` | Desk menu | old name for Today |
| the shade | `openSystemShade` (`openObject.ts:132-134`) | nothing listens; still reachable from `gate:` refs |

## 3. Overlaps

- One answer, "what waits on me", in six faces: the bell/Needs you, Today
  TO DECIDE, Today ▸ Follow-through, the Brief's `waiting`, the Brief
  window's headline, The week's Door cards. The Door board is fetched
  three times (`TodayView`, `NeedsDrawer.tsx:512`, `ChairHome.tsx:499`,
  `:1040`, `:1058`).
- Two owed models: People's typed commitments (Today `OWED`) and meeting
  action items resolved by alias (People prep "They owe you"). Today's
  `OWED` counts only the first.
- Calendar upcoming is drawn in Today, The week and the Brief.

## 4. MCP

- `desk.needs_you` (`holdspeak/mcp/tools.py:413`, handler `:1152-1163`),
  no filter arguments.
- `door.get`, `door.add_item` (`holdspeak/mcp/families/door.py:20`, `:31`).
- `monday_brief.get/generate/shelf/shelf_read` (`tools.py:1316-1327`),
  resource `holdspeak://briefs/latest` (`holdspeak/mcp/resources.py:533`).
- `follow_through.board/complete/commit_decision`, `people.*` (18),
  `heartbeat.*` (`holdspeak/mcp/families/heartbeat.py:15-71`).
- Missing for this design: a filtered Needs-you read, a Today read, a
  person-suggestion read.

## 5. Constraints for the design

- Keep the stored data: action items, decision commitments, cadence loops,
  People records (encrypted), brief rows, shelf state, notified ids. Rename
  and regroup only what he sees.
- People stays encrypted and local. Agents read People; only the owner
  writes it (2026-10-06). An automation can *suggest* an agenda item; it
  cannot add one.
- The Needs-you count excludes waiting rows today. Keep that: "they owe me"
  never makes a number.
- The hub owns windows (`desk_window_service.py`). Retiring the Brief and
  The week windows needs their ids to close cleanly on desks that have
  them open.

# The daily surface and People: what it is today (recon, 2026-10-17)

This is the "What it is today" input for `DESIGN.md` section 2. It covers
Today, Brief, Needs you, The week, Notifications, People and
Follow-through (INVENTORY rows 16 to 20, 8 and 9). I walked the jobs as a
first-time user at 1440x900 and 393x852. I fixed nothing. The shots are in
`shots/` (72 files; 7 duplicates from failed tab presses are parked in
`shots/_parked-duplicates/`). The rig is in the footnote.[^rig]

Two desks:

- **The empty desk** (`e*` shots): a fresh HOME, no engine, no people, no
  meetings. This is his desk on the first morning after the fresh start.
- **The working desk** (`f*` and `m*` shots): three meetings of this week
  with real transcripts (a platform sync, a 1:1 with Theo, an architecture
  review), two notes, one project, two people seeded (Theo Park, Jun Sato),
  a third added through the face (Mira Okafor), and a calendar for the
  evening (1:1 with Mira 20:15, Payments platform sync 21:00, 1:1 with Jun
  22:00). The summaries ran for real on the LAN engine (qwen3.8-27b): all
  three in about 2.5 minutes.

The walk ran at 19:30 on a Saturday. The "8 AM" of the job is simulated by
a calendar that starts 45 minutes later. Quiet hours (22:00 to 08:00) were
not crossed.

## The jobs I walked

1. **The morning.** Open HoldSpeak. In 10 seconds, know what needs me today
   and do the first thing in one press.
2. **What is owed.** See what I owe and what my people owe me, apart.
3. **Before a 1:1.** Prep for Mira: what I owe her, what she owes me, what
   to raise.
4. **A person comes to exist.** Get my three reports into People.
5. **After the meetings.** Turn this week's meeting promises into things
   HoldSpeak tracks.
6. **Being told.** Get a notice only when something needs me.

## 1. The empty desk (first morning)

- The first face is **Get ready**: `Speech`, `Set up speech · 144 MB`,
  `First words · WAITS FOR SPEECH`, `Chat engines`, `Optional setup`
  (`00-first-open-*.png`). Nothing about the day.
- After `Continue later`, the desk shows six drawers, the People and
  Conductor icons, a seed note `Weekly update`, and the bell with **1**
  (`e01-desk-*.png`). The bell is the only thing that speaks.
- **Today** (dock, first item): `Saturday`, `Record now`, a time rail with
  `No calendar yet` and `Connect calendar` (`e02-today-*.png`). Four wings
  across the top: `DAY · BRIEF · FOLLOW-THROUGH · DECISIONS`.
- **Today ▸ Brief**: `No brief generated.` and a plain `Generate` button
  (`e03-today-brief-1440.png`). **Today ▸ Follow-through**: `No
  follow-through yet` (`e04-today-followthrough-1440.png`).
- **The bell (1)** opens **Needs you**: `1 needs you`, `NO CALENDAR`,
  `Connect calendar`, a fold `1 of 1 available`, a chip `ALL`, a group
  `Work · 1`, one row `SET · No engine for summaries · Meeting summaries ·
  SETUP · Choose an engine` (`e06-bell-1440.png`). Two verbs say "set up"
  on one row (`SET` and `Choose an engine`). The setup row is filed under
  "Work".
- **Window ▸ Desk** holds four more windows: `Needs you`, `Brief`, `The
  week`, `Capture` (`e07-window-desk-submenu-1440.png`). The phone's Go
  lists them as apps: `Needs you`, `Brief`, `The week`, `Capture`, then
  `Meetings`, `Ask AI`, `People`, `Conductor` (`e01-desk-393.png`).
- **The Brief window**: `BRIEF`, `Generate`, `No brief yet`
  (`e08-brief-window-*.png`). **The week**: `NO CALENDAR · Connect`, in a
  short window at the bottom right (`e09-week-window-*.png`).
- **People**: one button, `Set up People`, and the line `Encrypted,
  local-only relationship context` (`e10-people-empty-1440.png`). After the
  press: a `Name` field, `Direct report · Peer · Extended`, `Add`, `Add a
  person to start` (`e11-people-after-setup-*.png`).

On the empty desk the morning answer is: one setup row and three empty
faces. Nothing tells him that his meetings, his calendar or his people
would fill this.

## 2. The working desk: the morning

The summaries ran, and the desk now holds what the three meetings said.

| Face | What it shows at 19:32 | Shot |
|---|---|---|
| Bell | **11** | `m01-desk-morning-1440.png` |
| Project icon "Payments ledger cutover" | **12** | `m01-desk-morning-1440.png` |
| Today ▸ Day | `3 MEETINGS AHEAD`; NEXT `1:1 with Mira · IN 43 MIN` with steps `1 Prep · 2 Record · 3 Summary · 4 Send follow-up` and `Record when it starts`; side plate `TO DECIDE`: **one** item, `Adopt idempotent retries with a dedupe key`, `Open decision · Confirm · Not now` | `m02-today-day-*.png` |
| Today ▸ Brief | `No brief generated.` until `Generate` (about 15 s); then `OCT 16-17`, `SINCE FRIDAY`, 7 "changed" rows (`MEETING RECORDED`, `PROJECT ADDED`, `3 people added`, three `SUMMARY REQUESTED`), one `SUMMARY DID NOT START · Check the summary route, then try again` (the summary had since succeeded), then 11 `PROPOSED` rows | `m03-*`, `m04-today-brief-generated-*.png` |
| Today ▸ Follow-through | `To review · 7`, each with the owner as typed (`Jun`, `Theo`, `Me`, `Mira`), the due date as said (`Thursday`, `this week`, `Friday nex`), `Open meeting · Done · Details` | `m05-today-followthrough-1440.png` |
| Today ▸ Decisions | `Current only`, `No decisions yet.` | `m06-today-decisions-1440.png` |
| Needs you | `11 need you`, `NEXT · 20:15 · 1:1 with Mira`, chips `ALL · NO DUE DATE`, one group `Work · 11`; every row is `ACTION` or `DECISION` with `Confirm · More` | `m10-needs-you-*.png`, `m11-needs-you-full-1440.png` |
| Brief window | `BRIEF · 11 THINGS WAITING`, three rows with `Ack · Defer`, `16 more`, then a Send well with `HoldSpeak folder` and a full preview of the brief | `m12-brief-window-*.png` |
| The week | Day strip `MON … SAT`, `3 MEETINGS THIS WEEK`, the three evening events, then the recorded meetings, each with `RAN · 192.168.1.43 · LAN` **and** `REFUSED` | `m13-week-window-*.png` |

The same eleven things appear in five places: the bell, Needs you, the
Brief (as `PROPOSED`), Follow-through (seven of them, as `To review`), and
the Brief window (`11 THINGS WAITING`). Today ▸ Day shows one of them. The
project icon says 12.

The extraction was good but not clean: `Do it` (from "Do it." in the 1:1)
and `Talk about the staff path in our next one-on-one` arrived as
**decisions** (`m10-needs-you-1440.png`).

## 3. After the meetings: keep what was promised

To turn nine of the eleven proposals into tracked items I pressed
`Confirm` nine times in Needs you, about 2.5 s each (`m14-*`, `m15-*`).
`Do it` and the staff-path row were left; `More` offers `Open · Add to
Project · Defer · Decline` (`m18-needs-more-menu-1440.png`).

After the nine presses:

- Needs you: `4 need you`. My own two show `YOURS` and `Done`. A new chip
  `WAITING` appears (`m15-needs-after-confirms-1440.png`). Under `WAITING`:
  five rows, `WAITING ON JUN`, `WAITING ON MIRA`, `WAITING ON THEO`
  (`m16-needs-waiting-filter-1440.png`). This is the closest thing to "they
  owe me" in the product, and it is a time filter, not an owner filter.
- Today ▸ Day: `TO DECIDE` now shows the staff-path row. Nothing of mine
  due Monday shows (`m07-today-day-after-confirm-1440.png`).
- Today ▸ Follow-through: all seven moved from `To review` to `Later · 7`,
  including mine due Monday. Every action now reads `Open decision`
  instead of `Open meeting`. The due date shows twice (a chip and a line)
  and `Friday next week` is cut to `Friday nex`
  (`m08-today-followthrough-after-*.png`).
- Today ▸ Decisions: `DECISIONS 2` (the freeze and the retries).
- The project badge went to 5 while the bell said 4.

## 4. Before the 1:1 with Mira

| Step | Presses | What I saw | Shot |
|---|---|---|---|
| Open People | 1 | `3 people`, each `No 1:1 planned · Plan` | `m20-people-list-1440.png` |
| Open Mira | 1 | `PREP · CONTEXT · HISTORY · INFO`; `NEXT 1:1 · NOT PLANNED`, `No 1:1 planned · Pick from calendar`; `YOU OWE · Add`; `THEY OWE YOU · Add`. Empty, although Needs you says `WAITING ON MIRA` and the calendar has `1:1 with Mira` at 20:15 | `m21-people-mira-before-1440.png`, `m23-people-mira-after-1440.png` |
| `Pick from calendar` | 1 | Jumps to the `CONTEXT` tab, unfolds `Links`: `Projects`, `Calendar series · Link calendar event`, `Names in meeting notes · Add` | `m25-mira-pick-calendar-1440.png` |
| `Link calendar event`, pick `1:1 with Mira` | 2 | `Linked 10/17/2026 · Unlink` | `m29-mira-link-calendar-1440.png`, `m31-mira-alias-added-1440.png` |
| Type `Mira` in `Names in meeting notes`, Add | 2 + typing | My typed alias did not save in two tries; I linked the three first names through the hub's own route[^alias] | `m31-*` |
| Back to People | 1 | Now `NEXT 1:1 · TODAY 08:15 PM · IN 38 MIN · Mira Okafor · Open prep` and `1:1 Today 20:15` on her row | `m33-people-list-linked-*.png` |
| `Open prep` | 1 | `THEY OWE YOU 1 · Draft the rollback runbook · from Payments platform sync · BY Tuesday · Done`. `YOU OWE` empty. No "last time", no "to raise" | `m35-mira-prep-aliased-*.png` |

Theo, after the same alias link: `THEY OWE YOU 2` (`Profile the
reconciliation job…`, `Write up alert rule changes`), but `YOU OWE` is
empty, although in his 1:1 I said "I'll review your design doc by Monday"
(`m36-theo-prep-aliased-1440.png`). That item is mine and it is about Theo,
and nothing records "about Theo".

Today's NEXT card has `Open prep`, which opens the same prep in its own
window in one press (`m40-today-day-final-1440.png`,
`m41-today-prep-press-1440.png`). Today's `OWED` plate never appeared: it
counts only commitments typed in People, not the meeting items that People
now shows.

**Result:** a correct prep for Mira took about **9 presses, typing, and a
trip through a tab called CONTEXT and a fold called Links**, and it only
works once he knows that "Names in meeting notes" is what joins a meeting's
"Mira" to the person "Mira Okafor".

## 5. A person comes to exist

- On the empty desk: `Set up People` (1 press), then name, kind, `Add` (3
  presses and typing) per person (`e10-*`, `e11-*`).
- On the working desk: `Add person`, type `Mira Okafor`, `Direct report`,
  `Add`: 4 presses and typing, about 4 s of machine time
  (`f11-people-add-form-1440.png`, `f12-people-mira-added-1440.png`).
- Nothing proposes a person. Three meetings named Mira, Theo and Jun as
  speakers and as owners; the calendar has "1:1 with Mira"; Needs you
  already writes `WAITING ON MIRA`. People still starts from an empty
  form. The People icons on the desk appear only once a person exists.

## 6. Being told

- The rig blocks real desktop notices (`HOLDSPEAK_DESKTOP_NOTIFY=0`). A
  sweep run by hand recorded what it would have posted: `count 4`,
  `newItems 4`, `fired false`, `outcome not_posted_in_rig`.[^notify] The
  four include the two extraction mistakes (`Do it` and the staff-path
  "decision"), so the first notice of his day would have counted them.
- Heartbeat defaults: sweep every 15 minutes, `notify: edge`, quiet hours
  22:00 to 08:00. Held notices are delivered once quiet hours end, so an
  8:00 open meets the night's backlog as one notice.
- I saw no Qlippy popup and no toast in the walk. The shade is parked.
- Nothing notifies when an automation or an agent finishes.

## 7. Side findings (other clusters own them)

- **Engines.** Giving the summaries an engine took four tries:
  `Choose an engine` → the found LAN row (no effect) → `Find on LAN` → `Use
  it` (adds, does not assign) → `Default engine` → press the LAN row
  (`PATCHED 19:30 · DEFAULT ENGINE → QWEN3.8 27B`). The summary route
  still answered `selection_hash_required` once, and the Brief kept a
  `SUMMARY DID NOT START` row after the summary succeeded
  (`f01-*` to `f07-*`). Engines (`../engines/`) owns this.
- **The meeting summary of "Payments platform sync"** opens with
  "Following the architecture review that adopted idempotent retries…",
  a meeting that happened a day *later* (`m13-week-window-1440.png` text).
  Asking (`../asking/`) or Capture should check what context the summary
  gets.
- **Only one of three meetings** has a desk icon (`1:1 with Theo`).

## Friction log

"Presses" counts presses and typed fields. "Wait" is measured machine time.
"Est." is my estimate for a first-time user who reads the screen.

| # | Job step | Presses | Wait / est. | What he expects | Where he stops |
|---|---|---|---|---|---|
| 1 | Open the desk, first morning | 1 (`Continue later`) | 3 s / 15 s | The day | `Get ready` is about speech setup, not the day |
| 2 | Know what needs me (empty) | 1 (bell) | 2 s / 10 s | "Nothing yet; connect your calendar" | One setup row under "Work" with two set-up verbs |
| 3 | Know what needs me (working) | 1–4 (bell, Today, wings) | 3 s / 60 s | One number and the top three | 11 on the bell, 12 on the project, 1 in Today, 11 PROPOSED in the Brief, 7 in Follow-through |
| 4 | Read what changed | 2 (Today ▸ Brief, Generate) | 15 s / 45 s | The brief is ready when he arrives | It is not made until he presses Generate; one stale failure row |
| 5 | Keep the meeting promises | 9 (`Confirm` × 9) | 2.5 s each / 60 s | One "keep these" per meeting | One press per item; two wrong "decisions" need `More ▸ Decline` |
| 6 | See mine vs theirs | 2 (bell, `WAITING`) | 2 s / 30 s | Two lists: mine, they owe me | "Waiting" is a time filter; Follow-through has no split; the Today OWED plate never shows meeting items |
| 7 | See this week's due dates | – | – / stuck | Dates | `Thursday`, `this week`, `Friday nex`; everything sits in `Later` |
| 8 | Prep for Mira | ~9 + typing | 3 s per step / 2–3 min | Open prep and see both directions | `NOT PLANNED` and empty columns until he links the calendar series and "Names in meeting notes" under Context ▸ Links |
| 9 | Prep for Theo: what I owe him | – | – / stuck | "Review Theo's design doc" under You owe | My own items carry no "about whom" |
| 10 | Add three reports | 4 + typing each | 4 s each / 1 min | They come from the meetings he already had | An empty form; nothing suggested |
| 11 | Be told | 0 | – | One notice when something of his is due | The notice would count unconfirmed extraction noise |

[^rig]: Isolated hubs started with `scripts/graph_walk.py serve` from the
    code of the owner's desk worktree (`wt-daily-delight-delivery-20261017`,
    `217001b2e`, the head his desk runs; bundle `f5317bcd54bf056e`), with
    `_isolated_hub_env` (scratch `HOME` from `mktemp -d`, every isolation
    switch from `CLAUDE.md`). Port 8831: the empty desk. Port 8833 (with
    `--scheduler`): the working desk. A first working hub on 8832 was
    discarded because a pre-seeded engine config made a profile with no
    model record (`f02-engine-assigned-1440.png`, `f03-lan-used-1440.png`
    are from it). Seed through the product's own producers before boot
    (`db.meetings.save_meeting`, `PrimitiveService.create_note`,
    `PeopleService.create_relationship`, `db.projects.create_project`),
    the calendar through `POST /api/calendar/snapshot/confirm`. Summaries
    through `POST /api/meetings/{id}/intelligence/run` on the real LAN
    engine `qwen3.8-27b` at `192.168.1.43:8080`; nothing faked. Chromium
    headless via Playwright, 1440x900 and 393x852 (mobile, touch, scale 2).
    Both hubs stopped and both scratch HOMEs removed afterwards.
[^alias]: `POST /api/people/relationships/{id}/owner-aliases` with
    `{"alias": "Mira"}` (and Theo, Jun): the route the face's `Add` calls
    (`holdspeak/web/routes/people.py:244`). My typed press did not save;
    whether a real keyboard saves it I did not verify.
[^notify]: `POST /api/settings/heartbeat/run-now` on the rig; the
    `notify` block of the answer.

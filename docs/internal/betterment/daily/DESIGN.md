# Today, Needs you and People: betterment design

Status: draft for the owner. Clusters D (the daily surface) and B (People
and commitments): INVENTORY rows 16 to 20, 8 and 9. Inputs: `RECON.md` (the
live walk, 72 shots, 2026-10-17) and `MODEL.md` (the code map). It applies
the product model of `../PLAN.md` §2: one Needs you list, its other faces
become filters, Today is the start of the day, and the Brief window goes
into Today. Companions: `../workbench/DESIGN.md` (Automations),
`../engines/DESIGN.md`, `../mcp/DESIGN.md`, `../herdr/STUDY.md`.

## 1. The job

He leads three people (Mira, Theo, Jun) and runs a few projects. At 8 AM he
opens HoldSpeak. In ten seconds he wants to know three things: what is on
today, what is his to do, and who owes him what. Then he wants to act on the
first thing with one press: open the prep for his first 1:1, mark a thing
done, nudge someone. Before each 1:1 he wants one page: what I owe them,
what they owe me, what to raise. He does not want to type his people in: they
are in his meetings and his calendar already. He wants a notice only when
something is his and is due, never for noise. The owner on Follow-through:
"confusing and ugly". On the product: "the most advanced Agentic OS in the
world". So the morning should already be prepared when he arrives.

## 2. What it is today

The full walk is in `RECON.md`. In short:

| Job step | Today | Shot |
|---|---|---|
| Open the desk, first morning | `Get ready` (speech setup). After `Continue later`: drawers, a seed note, a bell with **1**: "No engine for summaries", filed under "Work", with two set-up verbs | `00-first-open-1440.png`, `e06-bell-1440.png` |
| What needs me (working desk) | Bell **11**, project icon **12**, Today ▸ Day shows **1** "to decide", Brief lists **11** `PROPOSED`, Follow-through **7** `To review`, the Brief window "**11** things waiting". Five faces, four numbers | `m01-*`, `m02-*`, `m04-*`, `m05-*`, `m12-*` |
| What changed | No brief until he presses `Generate` (15 s). One stale "Summary did not start" row after the summary ran | `m03-*`, `m04-*` |
| Keep the meeting promises | `Confirm` nine times, one row at a time. Two extraction mistakes ("Do it", a "decision" to talk about the staff path) wait in the same list | `m14-*`, `m15-*` |
| Mine vs theirs | No split in Follow-through. Needs you has a time filter `WAITING` that lists "WAITING ON MIRA". Today's `OWED` plate counts only typed People items and never appeared | `m16-*`, `m08-*` |
| Due dates | "Thursday", "this week", "Friday nex". Everything sits in `Later`, including mine due Monday | `m08-today-followthrough-after-1440.png` |
| Prep for Mira | `NOT PLANNED` and empty columns, although the calendar has "1:1 with Mira" and she owes the rollback runbook. About 9 presses through `CONTEXT ▸ Links ▸ Calendar series` and `Names in meeting notes` fix it | `m21-*`, `m25-*`, `m35-*` |
| What I owe Theo | "Review Theo's design doc" (said in his 1:1) never shows in his `YOU OWE` | `m36-theo-prep-aliased-1440.png` |
| Add my three reports | `Set up People`, then an empty form, 4 presses and typing per person. Nothing is suggested | `e10-*`, `e11-*`, `f11-*`, `f12-*` |
| Be told | The first sweep would notify "4 need you", and two of the four are extraction noise | RECON §6 |

What worked: the meeting summaries were good, the extraction found every
real promise with the right owner, Today's NEXT card with `Open prep` is
the right idea, and People's prep has the right two columns.

## 3. Why it fails

1. **One question has six homes.** "What waits on me" is answered by Needs
   you, Today ▸ To decide, Today ▸ Follow-through, the Brief, the Brief
   window and The week. Each draws its own subset with its own number and
   its own verbs (`MODEL.md` §2, §3). He cannot trust any one of them, so he
   opens all of them. (`m01`, `m02`, `m04`, `m05`, `m12`.)
2. **A row does not know who it belongs to.** The owner is the string the
   meeting said ("Mira", "Me"); the due date is the word the meeting said
   ("Thursday"). So the product cannot sort mine from theirs, cannot put
   Mira's promise in Mira's prep, cannot put my promise to Theo in Theo's
   prep, and cannot tell that Monday is in two days (`MODEL.md` §1 People
   and Follow-through; `m08`, `m21`, `m36`).
3. **People start from a form, not from his work.** Nothing turns a
   speaker, an owner or a "1:1 with Mira" calendar series into a person.
   The join he needs ("Names in meeting notes") hides under Context ▸
   Links. So People is empty or disconnected, and every face that depends
   on it is empty too (`e10`, `m25`).
4. **The morning is not prepared.** The brief exists only after a press.
   The 1:1 prep is computed when opened, with nothing to raise. Meeting
   promises wait for one Confirm each. An engine with the desk's tools
   could do all of this before 8 AM, and nothing asks it to (`m03`, `m14`).
5. **Notices count noise.** The notice rule counts every new row, including
   unconfirmed extraction and setup rows, and nothing tells a finished
   agent or a new result apart from a thing that needs him (RECON §6).

## 4. The design

### The concept

**Needs you is one list of everything that waits on him or on his people.
Each row knows its person, its direction (mine, theirs, to decide) and its
real date. Every other face is a filter of that list. Today is the top of
the list plus the day, prepared before he arrives.**

### The words

| He sees | It replaces |
|---|---|
| **Today** | Intelligence, Day wing, Brief window, The week window, Monday brief (as a window) |
| **Needs you** | Follow-through, To decide, Waiting, To review, the Brief's "waiting", "N things waiting" |
| **Mine** · **They owe me** · **To decide** · **This week** | lanes Overdue / Due soon / Later / To review / Unassigned; filters No due date / Not run / Waiting |
| **Since yesterday** (Since Friday on Monday) | Brief, Generate, Refresh, Acknowledge / Ack |
| **Keep** · **Drop** (a promise from a meeting) | Confirm, Decline, Not now, PROPOSED |
| **Decide** (a decision from a meeting) | Confirm (on a decision), Open decision |
| **Done**, **Nudge**, **Later** | Done, Snooze, Defer, Details ▸ Tomorrow |
| **Prep** (for a 1:1) | Open prep, Prep, Plan, Pick from calendar |
| **I owe {name}** · **{name} owes me** · **To raise** · **Last time** | YOU OWE, THEY OWE YOU, TO RAISE, LAST TIME |
| **From your meetings** (suggested people) · **Add** · **Not a person** | Set up People, Add person form as the only door |
| **Prepared** (the morning automation's result in Today) | — |

Kept names: Person, People, Project, Decision, Meeting, Automation, Engine.

### The rows: what a Needs-you row is

Every row carries, in data and on the face:

- **direction**: *mine* (owner is him: "Me", his name, his mic label),
  *theirs* (owner is a person), *decide* (a decision or an approval), or
  *setup* (an engine or a connection is missing);
- **person**: the Person the row is about. For *theirs*, the owner. For
  *mine*, the person it is for: the other person in a two-person meeting,
  or a person named in the text ("Theo's design doc"). Empty is allowed;
- **due**: a real date, resolved when the item is made from what the
  meeting said and the meeting's own date ("by Wednesday" in a meeting on
  Thu 15 Oct → Wed 21 Oct). The said words stay as the source line;
- **project** and **source** (the meeting, note or decision it came from);
- **one primary verb** for its direction: mine → **Done**; theirs →
  **Nudge** (prepares a message; he presses Send); decide → **Decide**;
  setup → the one verb that fixes it (**Choose engine**, **Connect
  calendar**). Everything else is under **More** (Open, Later, Add to
  project, Drop).

### Today (desktop, 1440)

One page, no wings. The top answers the three questions; the day is below.

```
┌ Today ── Monday 19 October ─────────────────────────────── [ Record now ] ┐
│                                                                           │
│  PREPARED 07:30 · Claude Code                                       NEW  │
│  ┌──────────────────────────────────┐ ┌────────────────────────────────┐ │
│  │ 09:30  1:1 with Mira       [Prep]│ │ NEEDS YOU · 4            [All] │ │
│  │  Mira owes: rollback runbook,    │ │ ● Email Dana the cutover date   │ │
│  │  due Tue                         │ │   Mine · today · Ledger  [Done]│ │
│  │  To raise: staff path for Theo?  │ │ ● Review Theo's design doc      │ │
│  │ 11:00  Payments platform sync    │ │   Mine · for Theo · today[Done]│ │
│  │  2 open, 1 decision due  [Open]  │ │ ◆ Read-only or archive the old │ │
│  │ 14:00  1:1 with Jun        [Prep]│ │   ledger? · to decide  [Decide]│ │
│  └──────────────────────────────────┘ │ ○ Theo: load test numbers       │ │
│                                       │   They owe me · Wed     [Nudge]│ │
│  THE DAY                              └────────────────────────────────┘ │
│  08:00 ─●─ now                                                            │
│  09:30  ■ 1:1 with Mira          NEXT · in 90 min   [Prep] [Record]       │
│  11:00  ■ Payments platform sync                                          │
│  14:00  ■ 1:1 with Jun                                                    │
│                                                                           │
│  ▸ Since Friday  3 meetings · 2 decisions kept · 7 promises · 1 failed   │
│  ▸ This week     Mon 3 · Tue 2 · Wed 4 · Thu 1 · Fri 2                    │
└───────────────────────────────────────────────────────────────────────────┘
```

- **Needs you** (right, top): the first five rows of the one list, ranked
  (overdue, due today, to decide before a meeting it belongs to, then the
  rest). "They owe me" rows show only when overdue or due today. `All`
  opens the Needs-you window. When nothing waits: one line, "Nothing needs
  you. Next: 1:1 with Mira at 09:30."
- **Prepared** (left, top): the newest result of the *Morning prep*
  automation (below). One card per meeting today, with what each side
  owes and what to raise. `Prep` opens the person's prep. Absent when the
  automation is off or has not run; never an empty frame.
- **The day**: the time rail as today (it works), with `Prep` on 1:1s and
  `Record` on every meeting.
- **Since yesterday** (Since Friday on Monday): the brief, folded to one
  line of counts. Unfolded, it lists what changed, grouped by meeting and
  project. It is generated when Today opens if none exists for the period,
  and by the morning automation; there is no Generate button. A failure
  row disappears once the thing it reports has succeeded.
- **This week**: one folded line with a count per day; unfolded, the
  week's meetings and due rows. It replaces The week window.
- **NEW results**: a finished automation or agent adds one line under
  Prepared ("Friday team update has a new result", "Codex finished
  PLAT-212") until he opens it (the seen bit, `../herdr/STUDY.md` idea 4).

Empty desk: Today shows the day rail and one line under Needs you: "Your
meetings and calendar fill this. [Connect calendar] [Record now]". The
engine setup row appears only once a meeting is waiting for a summary.

### Today (phone, 393)

The same order, one column: Prepared (one card per meeting, swipe), Needs
you (top 3, `All`), the day, Since yesterday, This week. `Record now` stays
in the title strip.

```
┌ Today · Mon 19 Oct      [●] ┐
│ PREPARED 07:30          NEW │
│ ┌─────────────────────────┐ │
│ │ 09:30 1:1 with Mira     │ │
│ │ Mira owes: runbook (Tue)│ │
│ │ To raise: 1      [Prep] │ │
│ └─────────────────────────┘ │
│ NEEDS YOU · 4         [All] │
│ ● Email Dana · today [Done] │
│ ● Theo's doc · today [Done] │
│ ◆ Old ledger?      [Decide] │
│ THE DAY                     │
│ 09:30 1:1 with Mira  [Prep] │
│ 11:00 Payments sync         │
│ ▸ Since Friday · 3 meetings │
│ ▸ This week                 │
└─────────────────────────────┘
```

### The Needs-you window (desktop)

```
┌ Needs you ────────────────────────────────────────────────── 4 ┐
│ [Mine 2] [They owe me 5] [To decide 2] [This week] [Mira ▾] [Ledger ▾] │
│                                                                 │
│ FROM PAYMENTS PLATFORM SYNC · Thu 15 Oct                        │
│   ● Email Dana the cutover date    Mine · Mon 19   [Keep] [Drop]│
│   ○ Draft the rollback runbook     Mira · Tue 20   [Keep] [Drop]│
│   ○ Profile reconciliation job     Theo · Wed 21   [Keep] [Drop]│
│   ◆ Freeze old-ledger writes Nov 5 decision        [Decide]     │
│                                     [ Keep all 3 ]              │
│ ─────────────────────────────────────────────────────────────── │
│ ● Review Theo's design doc   Mine · for Theo · Mon 19   [Done]  │
│ ◆ Read-only or archive the old ledger?  to decide      [Decide] │
│ ○ Write up alert rule changes   Theo · Fri 23          [Nudge]  │
└─────────────────────────────────────────────────────────────────┘
```

- **Filters** are chips over the one list: **Mine**, **They owe me**, **To
  decide**, **This week**, a **person** picker and a **project** picker.
  Chips combine (Mine + Theo = what I owe Theo). A chip shows its count
  and is absent at zero. No chip selected = everything, ranked.
- **From a meeting**: new promises arrive grouped under their meeting,
  already kept (decision 1). `Drop` removes a wrong one in one press with
  Undo. **Keep all** confirms the group when he wants to review first
  (decision 1, alternative). Decisions are never kept silently: they stay
  **Decide** until he presses it (a decision is authority).
- **The number** is one number everywhere (bell, Dock, desk icon, Today):
  Mine due today or overdue + To decide + blocked agents + setup that
  blocks his own work. "They owe me" never counts. A project icon shows
  the same rule filtered to that project, or nothing.
- **Grouping**: none by default (ranked). The "Work · 11" group header goes.
- Phone: the chips scroll in one row; rows are full width with the verb at
  the right; `More` holds the rest.

### People

**A person comes from his work.** The People window opens on his people
and, under them, **From your meetings**:

```
┌ People ─────────────────────────────────────────────── [ Add ] ┐
│ NEXT 1:1  Today 09:30 · Mira Okafor                    [ Prep ] │
│                                                                 │
│ MO Mira Okafor   Report · 1:1 Mon 09:30 · owes 1               │
│ TP Theo Park     Report · owes 2 · I owe 1                     │
│ JS Jun Sato      Report · 1:1 Mon 14:00 · owes 2               │
│                                                                 │
│ FROM YOUR MEETINGS                                              │
│ Priya      named in Architecture review · 1 promise   [Add] [Not a person] │
│ Dana       named in Payments platform sync            [Add] [Not a person] │
└─────────────────────────────────────────────────────────────────┘
```

- **Suggestions** come from three places, with no engine needed: meeting
  speakers and owners that match no person; recurring calendar series
  named "1:1 with X" or with one other attendee; and, when Jira is
  connected, assignees on his projects' issues. Each row says where the
  name came from.
- **Add** makes the person in one press: the full name if the calendar or
  Jira has it, kind *Report* for a 1:1 series, else *Peer* (one press on
  the kind chip changes it); it links the spoken name as an alias and the
  1:1 series. Past and future rows with that name join the person at once.
- **Not a person** hides the name for good ("Do it" will never be a
  person).
- **Names resolve on their own** when there is one match: "Mira" in a
  meeting joins "Mira Okafor" if she is the only Mira. Two Miras → the row
  shows both and asks once. Names in meeting notes stays under Info for
  the odd case; he never needs it for the normal case.
- **The empty desk**: no `Set up People` press. The first Add creates the
  encrypted store. With no people and no suggestions: one line, "People
  you meet appear here."
- **The 503**: a People read that fails shows one line in place,
  "People could not be read · Try again", and never breaks Today or Needs
  you. The cause stays under investigation (`MODEL.md` §1, unknown).

### The 1:1 prep

```
┌ Mira Okafor · Report ───────────────────────── [ Record ] ┐
│ NEXT 1:1  Mon 19 Oct 09:30 · in 90 min                    │
│ ┌ MIRA OWES ME ───────────────┐ ┌ I OWE MIRA ───────────┐ │
│ │ Rollback runbook · Tue 20   │ │ (nothing)             │ │
│ │ from Payments sync  [Nudge] │ │                       │ │
│ └─────────────────────────────┘ └───────────────────────┘ │
│ TO RAISE                                    [ + ] [mic]  │
│ · Reconciliation still 40 min per batch (Payments sync)  │
│ · Owner for read-only vs archive?        suggested [Add] │
│ LAST TIME  1:1 on 8 Oct · 3 points · 1 decision    [Open]│
│ ▸ Notes · Projects · History                             │
└───────────────────────────────────────────────────────────┘
```

- Two columns named with her name, both fed by the one list (`person =
  Mira`): what she owes me (theirs) and what I owe her (mine, *for Mira*).
- **To raise** is the agenda. The morning automation suggests points
  (marked *suggested*, with **Add**); only his press adds them (People
  writes stay owner-only).
- **Last time** is the last meeting with her, its points and decisions.
- Notes, Projects and History fold below; Context, History and Info are
  no longer tabs he must visit to make prep work.
- Phone: one column in the same order.

### The morning, prepared: the *Morning prep* automation

An automation in the Automations model (`../workbench/DESIGN.md`), shipped
as a starter and shown in Automations like any other:

> **When** weekdays at 7:30 · **Do** "Prepare my day: for each meeting
> today, what each side owes and what to raise; list what is mine and due
> today or late; draft a nudge for each thing that is late from someone
> else" · **About** today's calendar, Needs you, People, this week's
> meetings and notes · **With** his tool-capable engine · **Put it in**
> Today.

- It runs with **the desk's tools** (`../mcp/DESIGN.md`): it reads the
  calendar, `desk.needs_you`, `people.one_on_one.brief`, memory and
  decisions. It writes only what the MCP rule allows without asking: the
  result, and *suggested* "to raise" points on the result (not on the
  person). Nudges are **Prepared**: drafts that wait for his Send.
- Its result renders in Today's **Prepared** block. **Looked at** lists
  the meetings, people and decisions it read.
- With an engine without tools, it runs on the sources in About and says
  so on its With line. With no engine, Today simply has no Prepared block.
- The same job runs **on demand** with `Prepare now` in Today's header
  menu, for a day that started without it.

### Notifications

One rule: **a notice is for something that needs him now, once.**

| Notifies | Does not notify |
|---|---|
| A *mine* row becomes due today or late (once, at 08:00 or when it turns due) | *They owe me* rows, at any time |
| A *to decide* row whose meeting starts within 30 minutes | Promises from a meeting before he has seen them |
| An agent is blocked and asks him (as today) | Setup rows, unless they block a meeting starting soon |
| 10 minutes before a 1:1: "1:1 with Mira at 09:30 · Prep ready" (with Prep) | Anything for the window he is looking at |
| A finished agent or automation: **quiet** (no sound), unless he is looking at it (decision 2) | Count changes on their own |

- **The morning notice**: at the end of quiet hours, one notice replaces
  the night's backlog: "4 need you · first: 1:1 with Mira 09:30". Pressing
  it opens Today.
- **The seen bit**: a finished agent or result stays NEW in Today until he
  opens it, then it leaves (herdr).
- **Never for the front window**: if the window that the notice is about
  is in front, there is no notice.
- Settings keep their place (Settings ▸ Rhythm): notify on/off, quiet
  hours, and "quiet notices for finished work" on/off.

### What each press does

| Verb | Where | One press does |
|---|---|---|
| **Prep** | Today day row, Prepared card, People NEXT 1:1 | Opens the person's prep window, scrolled to the next 1:1 |
| **Record** | Today day row, prep | Arms recording for that meeting (as today's `Record when it starts`) |
| **Done** | a *mine* row | Marks it done; Undo for 8 s |
| **Nudge** | a *theirs* row | Prepares a short message to that person in the Send well (destination: his saved one for that person, else a note); he presses Send |
| **Decide** | a *to decide* row | Opens the decision in place with **Accept**, **Change**, **Not now**; Accept writes the Decision |
| **Keep all** | a meeting group (decision 1 alternative) | Keeps every promise in the group |
| **Drop** | a promise | Removes it; Undo for 8 s; teaches nothing |
| **Later** | More | Hides the row until tomorrow 08:00 |
| **Add** | From your meetings | Creates the person, links the name and the 1:1 series |
| **Not a person** | From your meetings | Hides that name from suggestions |
| **Add** (to raise) | prep | Adds a suggested point to the 1:1 agenda |
| **Prepare now** | Today header menu | Runs Morning prep once, now |
| **All** | Today's Needs you | Opens the Needs-you window with no filter |
| A filter chip | Needs-you window | Narrows the list; a second press clears it |

### What is removed or parked (nothing is deleted)

- **Today's wings** (Day, Brief, Follow-through, Decisions) leave; Today is
  one page. `Decisions` moves to the Decisions app (its one home in
  `../PLAN.md` §2); Today's Since-yesterday lines link to it.
- **The Brief window** (`chair:brief`) and **The week window**
  (`chair:week`) are parked. Window ▸ Desk and the phone's Go list
  **Today**, **Needs you**, **Capture**.
- **Follow-through** (`FollowThroughView`) is parked; its verbs live on
  Needs-you rows. The `follow_through.*` MCP tools stay.
- **Generate / Refresh / Acknowledge / Ack / Defer** on the brief leave the
  face. The shelf data stays.
- **The time-class filters** (Overdue, Due today, Not run, No due date,
  Waiting, Muted) leave the chip row; ranking keeps their order, and Muted
  moves to More ▸ Muted projects.
- **`Set up People`** leaves; **Pick from calendar** becomes automatic
  (suggested series) with Link under Info for the odd case.
- **"Intelligence"** leaves every label.
- The dead `NeedsYouSection` in ChairHome is parked.

## 5. Decisions for the owner

1. **Promises from a meeting are kept on arrival.** When a summary
   finishes, its promises with an owner land in Needs you as kept rows,
   grouped under the meeting, each with Drop (and Undo). Decisions still
   wait for **Decide**. Recommended: yes. Ledger, not gate: the meeting is
   the record, and nine Confirm presses buy nothing. The alternative keeps
   them pending with one **Keep all** per meeting.
2. **Finished work notifies quietly.** A finished agent or automation
   raises a notice with no sound, unless he is looking at it, and stays
   NEW in Today until he opens it. It never enters the Needs-you count.
   Recommended: yes (the herdr study's decision 2, applied to results as
   well).
3. **Morning prep is on by default.** Once a tool-capable engine exists,
   the *Morning prep* automation runs on weekdays at 7:30 and fills
   Today's Prepared block. He can turn it off in Automations. Recommended:
   yes, with the engine shown on its With line so he knows what runs.

## 6. How we know it worked

On his desk, on a Monday at 8 AM, with his real week:

- He opens HoldSpeak and, **within 10 seconds and with zero presses**, can
  say the number that needs him, his first meeting, and the first thing
  that is his. The bell, the Dock and Today show **the same number**.
- He opens the prep for his first 1:1 in **1 press**, and it shows what
  each side owes, with the right person on every row, and at least one
  point to raise.
- After a meeting, its promises are tracked with **0 presses** (decision
  1) or **1 press** (Keep all), and a wrong one goes with 1 press.
- His three reports exist in People after **at most 3 presses in total**
  (one Add each, from the suggestions), with no typing.
- "What does Theo owe me" takes **2 presses** (Needs you ▸ They owe me ▸
  Theo) from anywhere.
- In one working week, every notice he gets is about something that was
  his and was due, or a quiet "finished" he chose to keep.

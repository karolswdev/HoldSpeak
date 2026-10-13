# Design: attention (R2 one attention source and one review; R5 a thought is a dead end)

Phase 17, 2026-10-13. One of four designs from the recon
(`RECON-2026-10-13.md`). This one owns: Needs you, the bell, Missed, the icon
badge, the Brief count; the meeting review and Outcomes; a commitment reaching
People prep; thought → task, person, project, ask; the ⌘K default.

Every claim below is grounded in main @ b50b13a0b. Paths are relative to the
repo root. Line numbers are from that head.

## 1. The problem

- "What needs me" is told in five places: the bell `5`, the dock "Missed"
  drawer with `NEEDS ATTENTION · 8` (four identical "Dictation needs review"),
  the Needs-you window, a "Needs you" desk icon with its own `5`, and the
  Brief caption `5 THINGS WAITING` (shots 012, 013, 030, 077).
- One meeting has two review loops. REVIEW: Confirm ×6, "Accept reviewed",
  then "Accept 4?". OUTCOMES: the same five rows still `TO CONFIRM`, Confirm ×5
  again (shots 030, 032, 035).
- "Write the rollback runbook" (owner Mira) is in six faces and not in Mira's
  1:1 prep, the one place he would look (shot 036). He typed it by hand (041).
- A finished thought can become nothing: no task, no person, no project, no
  ask (shot 018). ⌘K pre-selects `Send … to HoldSpeak folder`; Enter on a search
  result writes a file (shot 020).

## 2. The cause in the code

### 2.1 Four tellers already share one number; the fifth is a foreign read model

There are not five sources. There are two read models and one stored snapshot:

| Teller | Reads | Number |
|---|---|---|
| Bell (`AttentionBell`, `web/src/desk/components/DeskChrome.tsx:41-58`) | `useNeedsYou().count` (`web/src/desk/needsYou.ts:917`) over `GET /api/desk/needs-you` | `members + unread + arming` (`needsYou.ts:796`; hub twin `holdspeak/services/needs_you_membership.py:1381`) |
| "Needs you" desk icon (`web/src/desk/screen/compose.ts:191-199`) | the same snapshot (`Screen.tsx:56,81`) | the same; drawn as `lamp: { tone: "ask", count }` (`compose.ts:197`) |
| Needs-you window (`chair:needs`, `web/src/desk/chair/chairWindows.ts:37,45` → `web/src/desk/needs/NeedsDrawer.tsx:483-698`) | the same, plus `GET /api/door` for the calendar | head `needsHead(count, …)` (`needs/needsFace.ts:715-718`); the same number |
| Chair Brief window (`chair:brief`, `chairWindows.ts:38` → `web/src/desk/chair/ChairHome.tsx:1237-1345`) | `/api/brief/latest` for rows; `needs.count` for the caption | `5 THINGS WAITING` is `countToken(waiting, …)` with `waiting={needs.count}` (`ChairHome.tsx:1302, 2381`). It is the bell's number wearing a brief's hat |
| Dock "Missed" (`announceLauncher({id:"attention", label:"Missed"})`, `web/src/desk/components/AttentionDrawer.tsx:107-121`) → `SystemShade` (`web/src/desk/components/SystemShade.tsx:243`) | `GET /api/desk/projections` (`holdspeak/db/projections.py`), `GET /api/gate/proposals?state=held`, its own 5 s poll of needs-you, `/api/brief/latest`, dictation corrections | `NEEDS ATTENTION · 8` = `counts.needs_attention + gate.held.length` (`SystemShade.tsx:219, 291`); only 4 rows drawn (`:220-222`). `FINISHED · 4` is capped at 4 (`:223-225`) |

The one-number rule is already law and fenced on the hub
(`tests/unit/test_one_needs_you_number.py`, `tests/unit/test_needs_you_means_you.py`,
owner rulings 2026-10-04; bounce B11/B12 of Phase 15 paid in #980). The bell,
the icon, the window and the Brief caption agree. The foreign teller is
Missed: it reads the **projections** read model, which is a different universe.
`ProjectionRepository._collect` (`holdspeak/db/projections.py:235-252`) lists
actuator proposals, invocations, the dictation journal, steering audit, failed
captures, sync conflicts, artifacts, intel and plugin jobs, cadence loops and
pipeline receipts. None of that is in the needs-you rule, and the needs-you
members (Door cards, Room rows, decisions to review, coder rows) are not in it.

Four identical rows: `_dictation` (`projections.py:431-456`) makes one
projection per `dictation_journal` row with non-empty `warnings`, titled by the
constant `"Dictation needs review"` (`:444`); newest first; the shade takes
four. No excerpt, no grouping; only Acknowledge/Dismiss clears them.

The dark material: `.desk-next .desk-shade` uses `--desk-panel-fill` =
`--bg` = `#0e0f13` (`web/src/desk/components/attention.css:363-381`,
`web/src/styles/tokens.css:85, 287`). The light slate remap in
`window-interior.css:20-34` applies only to window shells; the shade is a bare
fixed `div`, so it keeps the old dark root tokens.

Two Briefs are two components: the Chair slot in `ChairHome.tsx` (rows =
`untriagedBrief`, the shelf, `BRIEF_CAP` 3) and Today ▸ Brief =
`web/src/desk/pullouts/views/BriefView.tsx:183-…` (THIS WEEK, lookback,
PEOPLE, Standing pages). Phone Go lists the Chair windows first through
`PHONE_GO_CHAIR` (`web/src/desk/components/DeskMenuBar.tsx:56-61`).

### 2.2 One status, four doors, and a bulk verb that holds rows silently

REVIEW (`web/src/pages/cores/history/MeetingReview.tsx`, mounted at
`MeetingDetail.tsx:364-374`) and OUTCOMES (`meetingOutcomes`,
`MeetingDetail.tsx:68-214`) read the same row, `follow_through_proposals.state`
(`holdspeak/db/schema.py:4533-4594`, `state IN ('proposed','confirmed','dismissed')`),
and write through the same endpoints (`POST /api/proposals/{id}/confirm|dismiss|defer`,
`holdspeak/web/routes/proposals.py:100-168` → `ProposalBridgeService`
`confirm_proposal` `:758-1021`, `dismiss_proposal` `:1023`, `defer_proposal` `:1087`).
They are not two tables. The rows that still say TO CONFIRM after REVIEW are
rows that are really still `proposed`, for three reasons:

1. **"Accept reviewed" holds rows and says so only in the count.**
   `_held_reason` (`proposal_bridge_service.py:1133-1144`) skips an action whose
   `owner` or `due` is unknown, or whose support is not SUPPORTED/LINKED. That is
   the "6 to review" against "Accept 4?" gap (shot 032). OUTCOMES then reads
   `state === "proposed"` and draws `TO CONFIRM` (`MeetingDetail.tsx:116-120, 133-135`).
2. **Defer is not a state.** It sets `deferred_until` on a `proposed` row
   (`holdspeak/db/proposals.py:197-215`). Needs you and Follow-through hide it
   (`follow_through_service.py:183-184, 668-683`); OUTCOMES never reads
   `deferred_until` (the type at `useMeetingData.tsx:28-50` does not declare it).
3. **Follow-through verbs never close the proposal.** `FollowThroughService.complete`
   (`holdspeak/services/follow_through_service.py:373-560`) updates `action_items`,
   `cadence_loops`, `decision_commitments` and never `follow_through_proposals`.

Four doors on the same verb: REVIEW, OUTCOMES (`useMeetingData.tsx:302-317`, which
also bypasses `_held_reason` and confirms with a null owner), Today ▸ Day's TO
DECIDE well (`web/src/desk/pullouts/views/TodayView.tsx:455-470`), and the
Needs-you row. A fifth face, Follow-through's "To review" lane, acts on the
`action_items` row underneath (`follow_through_service.py:781-782`).

OUTCOMES also does a dead read: `asRows(aftercare, ["action_items","actions","items"])`
(`useMeetingData.tsx:336`); `compute_meeting_aftercare` returns none of those
keys (`holdspeak/meeting_aftercare.py:346-357`), so it always falls back to
`intel.action_items` (`MeetingDetail.tsx:121-123, 183-187`).

### 2.3 Why Mira's prep does not show the commitment

The only path from a meeting action to a Person is `_brief_owned_actions`
(`holdspeak/services/people_service.py:686-721`), read by `one_on_one_brief`
(`:498-503`) and shown as THEY OWE YOU in `web/src/pages/cores/PeopleCore.tsx:925-937`.
Its query is:

```sql
WHERE m.parked = 0 AND ai.status = 'pending' AND TRIM(COALESCE(ai.owner,'')) <> ''
```

then `row["owner"].casefold() in alias_keys`. Two defects:

- `confirm_proposal` writes `status = 'open'` (`proposal_bridge_service.py:937, 953`).
  So the item is in her prep while unreviewed and **leaves it the moment he confirms it**.
  The same filter is at `:1007`.
- The match is an exact owner **alias** only (`link_owner_alias`). The display
  name "Mira" does not match unless it was added as an alias. The resolver that
  knows display names, `resolve_owner_candidates` (`people_service.py:1357-1437`:
  `linked | ambiguous | not_linked`, never a guess), is called only by the Room's
  people projection (`room_people_service.py:225-260`).

Nothing in `confirm_proposal` or `follow_through_service.py` resolves an owner to
a Person, and nothing stores a relationship id. That is right under the custody
law (`follow_through_service.py:113-118`: no People content in plaintext); the
join must stay a read-time join. It is just the wrong join.

### 2.4 The thought has no machinery

- Desk ▸ Write a thought: `verbRegistry.ts:185` → `openNewThought()`
  (`web/src/desk/newThought.ts:81-117`): `POST /api/notes`, then
  `POST /api/thoughts/adopt`, then `openPullout("note:<id>")`. The window is
  `ThoughtWorkspaceWindow` (`web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx`,
  820×640 at `:634`), body `WorkspaceReady` (`:106-589`).
- Foot verbs (`:565-587`): Change (opens `ThoughtReadsWell`, the "Find a note…"
  context picker), Copy, Send (`NoteSendWells`, `:551-563`), Finish → `completeThought`
  → `POST /api/thoughts/{id}/complete` → `RefinementThoughtService.complete_with_receipt`
  (`holdspeak/services/refinement_thought_service.py:1189`): `state='completed'`
  and a receipt. **Nothing downstream is created.**
- `thought_refine` returns one question or one synthesis
  (`refinement_coordinator.py:610-628`); it extracts nothing. Nothing runs
  intelligence on a thought.
- The meeting extractor takes plain text: `MeetingIntel.analyze(transcript: str, …) -> IntelResult`
  (`holdspeak/intel/engine.py:938`), output `action_items: list[ActionItem{task, owner, due}]`
  and `decisions` (`holdspeak/intel/models.py:56-105`). It is called only from
  meeting paths. The proposal chain cannot be reused as is:
  `follow_through_proposals.meeting_id TEXT NOT NULL` (`schema.py:4535`) and
  `confirm_proposal` requires the meeting (`proposal_bridge_service.py:785-790`).
- A task with no meeting already exists on the hub: `DoorService.add_item(principal, task, *, owner, due, source_type="meeting", source_ref="")`
  (`holdspeak/services/door_service.py:56-70`) inserts `action_items` with
  `meeting_id NULL`, `status 'open'`, `review_state 'accepted'`. It is MCP-only
  (`door.add_item`, `holdspeak/mcp/families/door.py:31-59`, `source_type` enum
  `meeting|thread`); `holdspeak/web/routes/door.py` has only `GET` (`:21`).
- Filing a note in a project exists: `project.resource.add` →
  `PUT /api/projects/{pid}/resources/{ref}` (`holdspeak/operations.py:2090-2113`);
  `web/src/desk/decide.ts:91` already uses it for a decision.
  `web/src/desk/AddToProject.tsx` is meetings-only (`{meetingId}` props, `:24-35`).
- The Object menu offers a note Ask AI, Edit, Rename, Duplicate, Delete, Hand
  (`web/src/lib/primitives.ts:488-496`; rows at `verbRegistry.ts:424-622`). It has
  no Make task, no Add to project. Why those rows read dead on his note is the
  verbs cluster (`DESIGN-verbs.md`).

### 2.5 ⌘K pre-selects a verb

`DeskToolShelf` (`web/src/desk/components/DeskToolShelf.tsx`): `SECTIONS`
puts VERBS before OBJECTS (`:50-59`). Rows sort by score, then section index,
then insertion (`:734-739`). The `week.send` row is labelled
`Send ${title} to ${name}` from the front window's send choices (`:551-568`,
`verbRegistry.ts:982-989`); the thought's title is its first words, so "ledger"
word-matches it at 60, the same as the note row, and the tie goes to VERBS.
`sel` resets to 0 (`:416-420, 455-458`); `selected = runnable[0]` (`:852-855`);
Enter always runs the selected hit (`:892-898`). Running the Send row only
`pick()`s the destination in the thought's SEND well (it does not write the
file); it still reads as "Enter = send".

## 3. The target behavior

### 3.1 What needs me (Job 1)

1440: press the bell (count `5`). The Needs-you window opens: `5 need you`,
rows ranked as today, each with its one verb (`Confirm`, `Review`, `Open`).
Press Today: DAY, BRIEF, FOLLOW-THROUGH, DECISIONS; the brief is in Today. Two
presses, two windows. No Missed, no icon count, no second Brief, no
`THINGS WAITING`.

393: Go ▸ Needs you (first row) or the bell; Go ▸ Today for the brief. Two
taps.

Cost: Job 1 from 6 presses / 3 windows to 2 / 2 at 1440, and 4 / 2 to 2 / 2 at
393. Answers to "what needs me": one.

### 3.2 One review of a meeting (Job 3)

1440: the meeting opens on OUTCOMES. Summary; Decided · 1; Who owes what · 5.
Each row carries the owner and the due as words (`Mira · by Friday`) and one
verb, `Confirm`, with `Not now` and `Dismiss` behind `More ▸` on the row. A row
whose owner or due is unknown shows the gap as its own ask under the row
(`Who? [Tomas ▾]  When? [____]`), not as a chip, and `Confirm` on it commits
what was typed. The foot has `Confirm all 4` when four rows have no gap; the
two with gaps stay above it with their asks open. Press `Confirm all 4`, pick
Tomas's due, `Confirm`: 3 presses for 5 rows. The REVIEW wing is gone; the
transcript span of a row is under `More ▸ Show in transcript`. ARTIFACTS
stays.

393: the same face; `Confirm` is the footer's primary verb for the first open
row; `More` holds the rest (the phone footer rule is the windows cluster's).

Cost: Job 3 from 14 presses to about 9; review loops from 2 to 1.

### 3.3 The commitment reaches Mira (Job 4)

He confirms "Write the rollback runbook · Mira · by Friday" once, anywhere.
He opens People ▸ Mira ▸ PREP. THEY OWE YOU lists `Write the rollback runbook ·
from Ledger standup · by Friday · Done`. Zero presses beyond opening her card.
The same row is in Follow-through and The week; it is one `action_items` row.

Cost: Job 4 "follow a commitment" from 7 presses (type it by hand) to 0.

### 3.4 A thought becomes something (Job 2)

1440: Desk ▸ Write a thought, type, `Finish` (3 presses). The foot now reads
`Ask · Task · Project · Send · Finish`. Press `Task`: a well unfolds under the
foot with the first line as the task text, `Who [Me ▾]` (a cycle over Me and
his People), `When [____]`, `Add`. Press `Add`: the foot receipt says
`TASK · MIRA · ADDED 14:12`; the row is on Follow-through and in Mira's prep.
Press `Project`: a cycle over his projects, `Add`; receipt `IN LEDGER MIGRATION`.
Press `Ask`: Ask AI opens grounded on this note with an empty question (the
verbs cluster owns what Ask AI does next).

Later (slice 6): `Finish` runs the meeting's extraction on the text and the
thought window shows `Who owes what · 2` with the same rows and the same
`Confirm` as a meeting. "Ask Tomas to own the reconcile step" becomes
`Own the reconcile step · Tomas · TO CONFIRM` without a press.

393: the same; `Finish` primary, the four others under `More`.

Cost: Job 2 "turn it into something" from impossible to 2 presses (`Task`,
`Add`), 0 after slice 6.

### 3.5 ⌘K

Type "ledger": the first, pre-selected row is the OBJECT (the note). Verb rows
list after objects and are never pre-selected; Enter opens the object. The
Send verb row stays reachable by arrow.

## 4. The design

### 4.1 One attention source

**Keep (it is already right):** `GET /api/desk/needs-you` is the list; the
bell is its count; the Needs-you window is its face; the ranking, the
coverage rows, `Nothing needs you` only when coverage is complete
(HS-200-15 rulings), the Confirm on a TO CONFIRM row.

**Remove (park):**

| What | Where it is | Where it goes |
|---|---|---|
| The dock "Missed" launcher | `AttentionDrawer.tsx:107-121` `announceLauncher({id:"attention"…})`; `Dock.tsx:87` `ACTIONABLE_LAUNCHERS` | `web/src/desk/_parked/attention/AttentionDrawer.tsx`; the `attention` id leaves `ACTIONABLE_LAUNCHERS` |
| The dark shade | `SystemShade.tsx`, `attention.css:363-381` | `web/src/desk/_parked/attention/SystemShade.tsx` and `.css`; the mount at `DeskApp.tsx:278` goes |
| The icon count | `compose.ts:197` `lamp: { tone:"ask", count }` | the lamp stays (`{ tone: "ask" }`), the `count` field is dropped (OWNER CALL 1) |
| The Chair Brief window | `chairWindows.ts:38` `chair:brief`; the `brief` slot of `ChairHome.tsx:1237-1345`, `BriefSection` `:2360-…`, `briefEgress.tsx` | `web/src/desk/chair/_parked/BriefWindow.tsx`; `chair:brief` leaves `CHAIR_WINDOWS` and `PHONE_GO_CHAIR`; the Go row becomes the existing verb `desk.intelligence-brief` (`verbRegistry.ts:389-396`, opens Today ▸ Brief) |
| `N THINGS WAITING` | `ChairHome.tsx:1302, 2381` | cut with the window. The stored brief's own headline (`monday_brief_service.py:687-699`, `len(members)` at generation time) is a snapshot and must not pretend to be live: Today ▸ Brief shows it as `GENERATED 06:00` text only; the live count is the bell's (words cluster for the sentence) |
| `useIntelligenceAttention` chips on the parked window | `web/src/desk/intelligenceAttention.ts`, consumer `AttentionDrawer.tsx:80` | parked with the drawer |

**What Missed had that the list does not, and where each goes:**

| Missed row | Verdict |
|---|---|
| Dictation needs review (warned journal rows) | Not attention. The Speak Journal wing owns warnings; the projection stays in the read model for ⌘K ▸ Processes (words cluster parks Processes behind ⌘K). No row in Needs you. |
| Failed intel or plugin job | Already a Needs-you member (R3 "failed summaries", `needs_you_membership.py`). No change. |
| Gate holds (conductor) | Already members (R5 coder rows, gate holds). No change. |
| Cadence loop needs you (`projections.py:623-662`) | Joins `compose` as a member kind `loop` with verb `Open` (slice 3). This is the only projection kind that needs his hand and is not in the rule. |
| Artifacts draft / needs_review (a drafted update) | The Room's own face shows its draft (verbs cluster, Draft update). Not a desk-wide member. |
| FINISHED receipts (sweeps, jobs) | Not attention. ⌘K ▸ Activity. |
| LEARNED corrections | Speak ▸ Learned wing already owns them. |
| BRIEF row | Today ▸ Brief. |

**Data and API:** none. `compose` gains one producer (cadence loops), additive.
The projections read model and `/api/desk/projections` stay as they are, read
by Processes and Activity only.

**Words:** the bell has no label; its count is the number. The window head:
`5 need you` / `Nothing needs you` / `Can't see everything` (for "Coverage
incomplete"). The foot: one time, `CHECKED 13:52` (today it prints both
`Checked just now` in the strip and `RANKED 13:52` in the foot; both are the
hub cache's `computedAt`, `NeedsDrawer.tsx:454-462, 609-610`). Row verbs:
`Confirm`, `Review`, `Open`, `Answer`.

**OWNER CALL 1 — the Needs-you icon's count.** Recon says cut the badge. Bounce
B12 (2026-10-08) asked for the one number on the icon too, and #980 put it
there. Recommendation: the icon keeps its ask-tone lamp and loses the number;
the bell is the one count. A lamp says "something waits", a count says how
many; one count on the desk is the OS rule. Other option: keep the count on
both (it is the same number, so it is not a lie), and cut only Missed and the
Brief caption.

### 4.2 One review: OUTCOMES owns Confirm

**Component changes (web):**

- `MeetingDetail.tsx`: the wings become `outcomes | artifacts`
  (`web/src/desk/objectWindows.ts:18` and `MeetingRecord.tsx:48`). REVIEW is parked:
  `web/src/pages/cores/history/_parked/MeetingReview.tsx` and `reviewModel.ts`
  (the `heldReason` rule at `reviewModel.ts:275-280` moves into the Outcomes
  row model; nothing else from it is needed).
- `useMeetingData.tsx`: drop the three reads that feed the commitments
  (`/follow-through-proposals` `:204-210`, the dead `aftercare` rows `:336`, the
  `intel.action_items` fallback) and read `GET /api/meetings/{id}/outcome-review`
  (`ProposalBridgeService.meeting_review`, `proposal_bridge_service.py:1210-1328`),
  which already carries every proposal with `state`, `deferred_until`, `support`,
  `owner`, `due`, spans and coverage. One projection, one face.
- `meetingOutcomes` (`MeetingDetail.tsx:68-154`): a row's state is read from
  one function, `rowState(p)`:
  - `proposed` and no gap → `TO CONFIRM` with `Confirm`;
  - `proposed` and gap (`!owner || !due`, the `_held_reason` rule) → the row
    unfolds its ask (owner cycle over Me + People, due field); `Confirm` sends
    `POST /api/proposals/{id}/confirm` with `{owner, due}` (the body
    `confirm_proposal` already accepts, `:758`);
  - `proposed` and `deferred_until` in the future → `NOT NOW · UNTIL THU`,
    verb `Confirm` still on the row;
  - `confirmed` → `Mira · by Friday`, with `Done` (Follow-through's `complete`,
    `POST /api/follow-through/complete`, by the row's `action_item_id`);
  - `dismissed` → not shown.
- The foot: `Confirm all N` (N = rows with no gap), calling the existing
  `POST /api/meetings/{id}/proposals/accept-reviewed` (`proposals.py:78-86`),
  which already applies the hold rule. The held rows are visible above it with
  their asks open, so the number is never a surprise.
- `More ▸` on a row (the library row's hover verbs, `SurfaceLedgerRow`):
  `Not now` (defer), `Dismiss`, `Show in transcript` (the span, from the same
  projection), `Edit` (text, through `/edit`).
- Today ▸ Day's TO DECIDE well (`TodayView.tsx:455-470`) and the Needs-you row
  keep `Confirm`: it is the same status and the same endpoint; a door is not a
  second review. Their `Not now` stays. They never show the gap ask; a row with
  a gap reads `Confirm` there too, and its press opens the meeting on that row
  (`openRef`) instead of confirming blind. This removes the blind confirm at
  `useMeetingData.tsx:302-317`.

**Hub changes (additive):**

- `FollowThroughService.complete` (`follow_through_service.py:373-560`): in
  the same transaction as the `action_items` update (around `:439-452`), look up
  the proposal by `action_item_id` (or `commitment_id`) and set `state='confirmed'`
  on `done`, `state='dismissed'` on `dismiss`. Then a Done in Follow-through
  no longer leaves a `TO CONFIRM` in the meeting. The CHECK constraint already
  allows both states; no schema change.
- `confirm_proposal` server-side gap rule: when `kind == "action"` and the final
  owner or due is empty, the single-row Confirm still goes through (he chose it);
  only the bulk verb holds. No change to `_held_reason`.

**Words:** `Who owes what`, `Decided`; row meta `Mira · by Friday`,
`TO CONFIRM`, `NOT NOW · UNTIL THU`, `DONE`; verbs `Confirm`, `Confirm all 4`,
`Not now`, `Dismiss`, `Done`. No `PROPOSAL`, `LINKED`, `UNREVIEWED`, `SUPPORTED`,
`DUE · UNKNOWN`, `OWNER · TOMAS` (the full vocabulary is the words cluster's;
these are the attention rows' words).

**OWNER CALL 2 — the transcript span.** REVIEW showed `MTG 10-13 · 13:53` and
a MORE unfold with the sentence the row came from. Recommendation: keep it,
under `More ▸ Show in transcript`, one press, because "where did this come
from" is the question that makes Confirm safe. Other option: cut it from the
window; `Open transcript` in the foot stays.

### 4.3 A confirmed commitment reaches the person's prep

The fix is a read-time join, which keeps the custody law (no relationship id
in plaintext, `follow_through_service.py:113-118`; `people.resolve` returns
only an id).

**Hub (`people_service.py`):**

- `_brief_owned_actions` (`:686-721`):
  - `LEFT JOIN meetings` (a task from a thought has `meeting_id NULL`; see 4.4)
    with `COALESCE(m.parked, 0) = 0`;
  - `ai.status NOT IN ('done','dismissed')` instead of `= 'pending'`;
  - `ai.review_state = 'accepted'` (confirmed only: prep shows what is agreed;
    the unconfirmed ones are in Needs you, one place);
  - match by `resolve_owner_candidates(owner)["link"] == "linked"` and
    `relationship.id == this relationship`, instead of the alias set. One
    resolver, no guess; an `ambiguous` owner is nobody's (and is the gap ask in
    4.2 next time).
  - The same two filters at `:1007` (`open_action_items`, the LAST TIME section).
- `compose_person_overlay._cards_by_aliases` (`holdspeak/services/person_overlay.py:127`)
  and `door_service._build_owner_person_index` (`door_service.py:411-441`) call
  the same resolver, so the Brief's PEOPLE section, the Door and the prep agree.
- The brief payload row gains `action_item_id` (already `id`), `source`
  (`meeting_title` or `"thought"`), and `due` as today.

**Web (`PeopleCore.tsx:925-937`):** the THEY OWE YOU row from
`brief.open_meeting_actions` reads `Write the rollback runbook · from Ledger
standup · by Friday` with `Done` (→ `POST /api/follow-through/complete`
`{card_id, verb:"done"}`). The typed `report_owes` records stay as they are;
`Add` stays for what no meeting captured.

**Data and API:** none. No migration.

**Words:** `THEY OWE YOU`, `YOU OWE`, `from Ledger standup`, `by Friday`, `Done`.

**Seam:** owner strings on the user's side ("Karol will send the data retention
doc") map to YOU OWE only if `_is_me` (`needs_you_membership.py:520-582`) is
shared with the prep; the reserved aliases (`people_service.py:51`) forbid "me"
as an alias. That is a later slice, named here and not designed.

### 4.4 A thought becomes a task, a project item, an ask, and (later) outcomes

**Web (`ThoughtWorkspaceWindow.tsx`):**

- The foot verbs (`:565-587`) become `Ask · Task · Project · Send · Finish`.
  `Copy` moves to the Object menu (it is there as a note verb through the
  verbs cluster's pass); `Change` is cut (recon R5; the context picker stays
  reachable from Ask AI, which is where grounding is chosen).
- `Task` unfolds a `TaskWell` under the foot (UX-CANON A.4, a well, not a
  modal): `StringGadget` text prefilled with the first line, `CycleGadget`
  `Who` over `Me` + `GET /api/people/relationships` display names,
  `StringGadget` `When`, `Add`. `Add` → `POST /api/door/items` (new, below).
  Receipt in the foot: `TASK · MIRA · ADDED 14:12`, the well closes.
- `Project` unfolds a `CycleGadget` over `GET /api/projects` and `Add` →
  `PUT /api/projects/{pid}/resources/note:{id}` with `relationship: "related"`
  (the `project.resource.add` edge `decide.ts:91` already uses). Receipt
  `IN LEDGER MIGRATION`. `AddToProject.tsx` stays meetings-only; the thought
  uses the resource edge, which is the right object for a note.
- `Ask` → the path the Object menu's Ask AI already takes
  (`verbRegistry.ts:480-486`): `useDesk.getState().setSelected(["note:<id>"])`
  then `useDesk.getState().openAsk()`. The Ask AI window opens with this note
  as its context and an empty question. The seam: Ask AI's face, the default
  question and the refusal reason are `DESIGN-verbs.md` (R1).
- One new vitest-tier app test file: `web/src/desk/__tests__/thought.app.test.tsx`
  (there is none for the thought window today).

**Hub (additive):**

- `POST /api/door/items {task, owner?, due?, source_type, source_ref}` in
  `holdspeak/web/routes/door.py`, a thin route over the existing operation
  `DoorService.add_item` (`door_service.py:56`). The `source_type` enum in
  `holdspeak/mcp/families/door.py:49` gains `"thought"`. `action_items` already
  has `source_type` and `source_ref` columns (the INSERT at
  `proposal_bridge_service.py:947-960` writes them). No schema change.
- Because `add_item` writes `review_state 'accepted'`, the task lands on
  Follow-through in its lane by due, and in the owner's prep through 4.3 (the
  `LEFT JOIN meetings` is what lets it in).

**Slice 6, thought outcomes (the meeting's machinery on a thought):**

- On `complete_with_receipt` (`refinement_thought_service.py:1189`), when an
  engine is assigned, queue `MeetingIntel.analyze(working_note.body_markdown)`
  (`intel/engine.py:938`) through the intel queue (the same worker the meeting
  uses, so progress and failure reasons are the verbs cluster's one run face).
  For each `ActionItem`: `DoorService.add_item(task, owner, due, source_type="thought", source_ref="note:<id>")`,
  but with `review_state 'pending'` (one new keyword, `reviewed: bool = True`,
  default unchanged). Decisions: the existing `decision_record_create_from_desk`
  path, lifecycle proposed.
- The thought window gets a `Who owes what · N` section under the text, the
  same `OutcomeRow` species as the meeting, rows `TO CONFIRM` with `Confirm`.
  Confirm here = `POST /api/follow-through/complete {card_id, verb:"accept"}`, a
  new verb in `complete` (`follow_through_service.py:373`) that sets
  `review_state='accepted', status='open'`. The Follow-through "To review" lane
  already lists `review_state='pending'` rows (`:781-782`), so the row is in
  Needs you's universe without a new producer.
- This deliberately does **not** reuse `follow_through_proposals`:
  `meeting_id TEXT NOT NULL` would need a table rebuild (SQLite cannot drop
  NOT NULL in place), and `confirm_proposal` is meeting-bound at `:785-790`.
  `action_items` with `review_state` is the proposal for a thought. The meeting
  keeps its proposals; both faces draw the same row species.

**OWNER CALL 3 — when the extraction runs.** Recommendation: on `Finish`,
automatically, the way a meeting runs its summary (the keep list: "everything
else should be built the way this is"), with the run shown in the foot
(`FINDING TASKS · 6 S`) and nothing if the text has no owed item. Other option:
a `Find tasks` verb he presses; cheaper to trust, one more press per thought.

**Words:** `Task`, `Project`, `Ask`, `Send`, `Finish`; `Who`, `When`, `Add`;
`Who owes what`; receipts `TASK · MIRA · ADDED 14:12`, `IN LEDGER MIGRATION`.
No `READS · NOTHING`, `KEPT · IN INBOX`, `ONE QUESTION`, `NO ENGINE YET`,
`EVERYDAY CONTEXT` (words cluster and verbs cluster own those cuts; this design
only names the verbs that replace the foot).

### 4.5 ⌘K: the object first, a verb never pre-selected

`DeskToolShelf.tsx`:

- `SECTIONS` order becomes `PROJECTS, PEOPLE, OBJECTS, MEETINGS, VERBS, PROGRAMS, SETTINGS, MEMORY`
  (`:50-59`). The sort stays score-first; on a tie the object now wins.
- A row carries `preselect: false` when its section is VERBS and the verb acts
  on the front window (the `week.send` rows, `:551-568`, and `sendChoices`
  rows). The initial `sel` (`:416-420, 455-458`) is the index of the first row
  with `preselect !== false`; arrows reach every row; Enter still runs the
  selected hit (`:892-898`).
- The MEMORY section's raw JSON comes from spec bodies concatenating JSON
  columns in `holdspeak/db/memory.py:121, 146, 326-329`; "Search never prints
  JSON" is the words cluster's (R3). Named here only because it sits on the
  same list.

## 5. The slices

Each is one PR on the fast cycle (`scripts/quick_check.sh`, merge, the
watcher runs the suite). Ordered by what he feels first.

### Slice 1: the commitment reaches the person's prep (half a day)

- Files: `holdspeak/services/people_service.py` (`_brief_owned_actions`,
  `open_action_items`), `holdspeak/services/person_overlay.py`,
  `holdspeak/services/door_service.py` (`_build_owner_person_index`),
  `web/src/pages/cores/PeopleCore.tsx` (the THEY OWE YOU row: source, due, Done).
- Tests: T1 `tests/unit/test_people_brief.py` gains: confirm a meeting action
  owned "Mira" (display name, no alias) → her brief lists it; dismiss it → it
  leaves; an ambiguous first name lists it for nobody. T2
  `web/src/desk/__tests__/people.app.test.tsx`: the row reads
  `from Ledger standup · by Friday` with `Done`, from a recorded brief answer.
- Risk: low. A read-time change; the custody law untouched. The one behavior
  change: unconfirmed items leave prep (they are in Needs you).
- Live: import the Ledger standup, Confirm "Write the rollback runbook", open
  Mira ▸ PREP. It is there.

### Slice 2: one review, OUTCOMES owns Confirm (one day)

- Files: `web/src/pages/cores/history/MeetingDetail.tsx`, `useMeetingData.tsx`,
  `MeetingRecord.tsx`, `web/src/desk/objectWindows.ts`, `TodayView.tsx` (gap
  rows open the meeting), `web/src/desk/needs/NeedsDrawer.tsx` (same),
  `holdspeak/services/follow_through_service.py` (`complete` closes the
  proposal). Parked: `MeetingReview.tsx`, `reviewModel.ts` →
  `web/src/pages/cores/history/_parked/`.
- Tests: T1 `tests/unit/test_phase200_meeting_outcomes.py` gains: Done in
  Follow-through → proposal `confirmed`; Defer → `deferred_until` read on the
  outcome-review projection. T2 `web/src/desk/__tests__/meetings.app.test.tsx`:
  from a recorded `/outcome-review` answer, a gap row unfolds its ask;
  `Confirm all 4` with six rows; a deferred row reads `NOT NOW`. T3 the sweep
  (the meeting window at 1440 and 393, REVIEW gone from the manifest).
- Risk: medium. The row model is rewritten; the recorded fixture must be
  re-recorded (`scripts/record_needs_you_fixture.py` pattern) from a real hub.
- Live: import a transcript, open the meeting: one review; `Confirm all`
  leaves the two gap rows with their asks; confirm one with Tomas's due.

### Slice 3: one attention source (one day)

- Files: `web/src/desk/components/AttentionDrawer.tsx`, `SystemShade.tsx`,
  `attention.css` → `web/src/desk/_parked/attention/`; `DeskApp.tsx:278`;
  `Dock.tsx:87`; `web/src/desk/screen/compose.ts:197`; `chairWindows.ts:38`;
  `DeskMenuBar.tsx:56-61`; `ChairHome.tsx` (the brief slot and `BriefSection`
  → `web/src/desk/chair/_parked/BriefWindow.tsx`); `intelligenceAttention.ts`
  parked; `holdspeak/services/needs_you_membership.py` (`compose` gains cadence
  loops).
- Tests: T1 `tests/unit/test_one_needs_you_number.py` gains a cadence loop
  that needs him; `tests/unit/test_desk_chair.py` loses `chair:brief`. T2
  `bell.app.test.tsx`, `needs-you.app.test.tsx`, `dock.app.test.tsx` (no Missed
  tile; no badge on the icon), `chair.app.test.tsx`. T3 the sweep: `chair:brief`
  leaves the manifest; the dock at 1440 and 393.
- Risk: medium. Many small deletions; the `attention` window id may be
  referenced by `MissionControlConveyor.tsx:646` (it opens the parked frame;
  that press goes with it, verbs cluster's Conductor face). The 393 Go list
  changes (windows cluster owns the phone grammar; this slice only swaps one
  row for the existing `desk.intelligence-brief` verb).
- Live: the dock has no Missed; the bell count is the Needs-you head; Today ▸
  Brief is the brief; the desk icon glows without a number.

### Slice 4: the thought's three verbs (one day)

- Files: `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx`, new
  `TaskWell.tsx` and `ProjectWell.tsx` beside it,
  `holdspeak/web/routes/door.py` (`POST /api/door/items`),
  `holdspeak/mcp/families/door.py` (`thought` in the enum). `door.add_item` has
  no entry in `holdspeak/operations.py` today; the route calls
  `DoorService.add_item` directly, as the MCP family does.
- Tests: T1 `tests/unit/test_web_routes_thoughts.py` or a new
  `tests/unit/test_desk_thought.py`: `POST /api/door/items` with
  `source_type: thought` lands on the Follow-through board and, with owner Mira,
  in her prep (slice 1's join). T2 new `web/src/desk/__tests__/thought.app.test.tsx`:
  `Task` unfolds, `Add` posts, the receipt renders; `Project` posts the
  resource edge. T3 the sweep (the thought window's foot at 393 is a known
  wrap; the fence stays).
- Risk: low. Additive route; the well is the library's species.
- Live: write "Ask Tomas to own the reconcile step", Finish, `Task`, Who
  Tomas, `Add`; open Follow-through and Tomas's prep.

### Slice 5: ⌘K the object first (half a day)

- Files: `web/src/desk/components/DeskToolShelf.tsx`; `verbRegistry.ts:982-989`
  (`preselect: false` on `week.send`).
- Tests: T2 `web/src/desk/__tests__/palette.app.test.tsx`: query "ledger" with
  a thought in front → the note row is selected; Enter opens it; the Send row is
  present and reachable by arrow.
- Risk: low.
- Live: ⌘K, "ledger", Enter: the note opens.

### Slice 6: thought outcomes (two days; after OWNER CALL 3)

- Files: `holdspeak/services/refinement_thought_service.py` (`complete_with_receipt`
  queues the run), the intel queue entry for a note text, `door_service.py`
  (`reviewed=` keyword), `follow_through_service.py` (`accept` verb),
  `ThoughtWorkspaceWindow.tsx` (the `Who owes what` section, the run in the foot).
- Tests: T1 a new `tests/unit/test_thought_outcomes.py` with a stub engine
  (`tests/unit/brief_rule_stub.py` pattern): Finish → two `action_items`
  `review_state pending`, `source_ref note:<id>`; `accept` → `open`, in Mira's
  prep. T2 `thought.app.test.tsx` from a recorded answer.
- Risk: medium. A new run on the engine per finished thought; the run face is
  the verbs cluster's; if that is not merged first, the thought shows only the
  rows and a `FINDING TASKS` word in the foot.
- Live: Finish the Tomas thought; `Who owes what · 1` appears; Confirm; it is
  in his prep.

First slice to build: **slice 1**. It is the smallest change and the one that
turns the meeting pipeline into his week.

## 6. What not to do

- **No new `attention_items` table or an "attention service" that unifies
  projections and needs-you.** The rule already exists and is fenced; the fix is
  to stop reading the other read model on the desk. A union would carry the
  dictation noise into the one list.
- **No relationship id on `action_items`, `decision_commitments` or
  proposals.** The custody law forbids People content in plaintext; the resolver
  is a read-time join by design (HS-200-14). One resolver, four readers.
- **No rebuild of `follow_through_proposals` to allow a null meeting.** A
  thought's proposal is an `action_items` row with `review_state pending`; the
  table that exists is enough.
- **No third review face "Decide" that merges Outcomes and Review.** Outcomes
  is the face he praised (keep list); it gains the one thing Review had that it
  lacked (the gap ask, the span) and Review is parked.
- **No proposal-level "Confirm everywhere" sync layer (web sockets, event
  bus).** The `desk_changed` frame and the `revision` re-read already exist
  (`MeetingRecord.tsx:125-146`); the faces disagreed because of status, not
  because of staleness.
- **No people picker modal, no task form window.** A well under the foot, the
  library's gadgets, a receipt in the foot (A.4, A.5).
- **No new ranking of the palette by object type.** One flag (`preselect`) and
  one section order change; the scoring stays.
- **No auto-attribution of an ambiguous owner.** `ambiguous` is nobody's until
  he says (D1 of HS-200-14), and the gap ask on the row is where he says it.

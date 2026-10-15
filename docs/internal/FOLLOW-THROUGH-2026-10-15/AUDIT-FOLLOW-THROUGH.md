# Follow-through source audit — 2026-10-15

**DRAFT · UNCHECKED — awaiting Muad'Dib. HOLD FOR BUILD.**

Base: `420a0eb28df9b1cdae2ce3fde8e78790f221d7cd`, worktree
`/Users/karol/dev/tools/wt-follow-through-20261015`. Source inspection only.
No product edits, tests, browser, installs, or owner state access. Root owns
the isolated live walk, canvas, settled design, and release. Anchors will
drift after implementation; verify the declaration before editing.

Tuesday question: can the architect see what he owes and is owed, act once,
and understand the result? The source exposes real actions, but it cannot
currently represent the complete two-way job. There are also concrete
writer and feedback gaps. Actual fit, legibility, and pointer reach need
root's live walk at 1440 and 393.

## Current flow and authorities

| Step | Actual producer or route | Current behavior |
| --- | --- | --- |
| Open the app | `web/src/desk/applications.ts:75`; `web/src/desk/intelligenceNavigation.ts:26` | Today opens the Intelligence window. Navigation selects Follow-through and can supply `followThroughId` or `overdueOnly`. `web/src/desk/openObject.ts:173` recognizes action/follow-through refs. |
| Host the board | `web/src/desk/pullouts/IntelligencePullout.tsx:125` | Four view tabs, Follow-through body, empty `SurfaceFooter`. Saved tab is restored. A tab click clears the drill filter (`:106`). |
| Read | `web/src/desk/pullouts/views/FollowThroughView.tsx:181`; `holdspeak/web/routes/follow_through.py:96` | GET `/api/follow-through/board`; optional server filters are project, owner, lane. HTTP enrichment can add People display names (`:28`), but the face requests the unfiltered board. |
| Meeting actions | `holdspeak/db/meetings.py:641`; `holdspeak/services/follow_through_service.py:178` | Persisted action items are primary cards. A pending review or missing owner goes to `unassigned`; otherwise due date selects the lane (`:820`). |
| Note tasks | `web/src/desk/thought-workspace/TaskWell.tsx:39`; `holdspeak/web/routes/door.py:28`; `holdspeak/services/door_service.py:79` | Add posts an accepted open action, owner defaults to `Me`, source is `note:<id>`. This transaction inserts no cadence loop. |
| Thread tasks | `holdspeak/services/thread_service.py:821` | `/todo` executes `door.add_item` through the existing thread tool executor with thread provenance. |
| Decision commitments and other loops | `holdspeak/services/follow_through_service.py:294`; `holdspeak/cadence/collector.py:127` | Commit creates an action plus a decision commitment. Collector also projects a decision loop. Board includes non-action loops independently (`holdspeak/services/follow_through_service.py:218`). Collector can also produce agent-question and proposal loops (`holdspeak/cadence/collector.py:51`, `:178`). |
| People | `holdspeak/services/people_service.py:1512` | Encrypted commitments hydrate as transient `people:<commitment>` cards, owner `you`, lane `now`, relationship `target_ref`. Only leader-owed commitments enter this projection. |
| Source/open | `web/src/desk/pullouts/views/FollowThroughView.tsx:103`, `:246`; `web/src/desk/surface/citations.tsx:45` | Verified note/thread refs open their primitive; decisions retain decision identity; meetings route through the Meetings surface. People opens its relationship. A card with no verified source currently offers an opener that reports an error after the press. |
| Done / Dismiss | `web/src/desk/pullouts/views/FollowThroughView.tsx:214`, `:372`; `holdspeak/services/follow_through_service.py:449` | POST `/complete`; action, action-linked loops, and decision commitments update in one transaction. Service emits a completion/dismissal ledger receipt. People transitions through its encrypted authority (`:393`; `holdspeak/services/people_service.py:1541`). |
| Snooze / Assign | `web/src/desk/pullouts/views/FollowThroughView.tsx:374`; `holdspeak/services/follow_through_service.py:495`, `:505` | Snooze posts an `until` day; Assign posts free-text `to`. People offers neither, matching its unsupported verbs. Assign changes ownership and emits a receipt; snooze changes existing loops only. |
| Reopen / dates / review | `web/src/desk/pullouts/views/FollowThroughView.tsx:259`; `holdspeak/services/follow_through_service.py:535`, `:558`; `holdspeak/web/routes/meetings/action_items.py:42` | Face exposes Reopen only through the eight-second Done Undo. Service also supports a date write. Meeting review has a separate existing PATCH route. Neither date nor review acceptance is exposed by this face. |
| Refresh | `web/src/desk/pullouts/views/FollowThroughView.tsx:173`, `:193`, `:237` | Initial read, re-read after a write, and desk-change subscription. Read ordering prevents an older successful response replacing a newer one. |

## Five prioritized findings

### 1. P1 — Done persists decrypted People text in plaintext browser storage

The Done button sends `card.text` for every source (`web/src/desk/pullouts/views/FollowThroughView.tsx:372`).
On success, `complete` stores that text as `label` in `window.localStorage`
(`:227`–`:230`). For a People card this is the encrypted commitment's body
(`holdspeak/services/people_service.py:1519`–`:1537`). The service explicitly keeps People cards
out of plaintext observation and caches (`holdspeak/services/follow_through_service.py:21`,
`:249`). The cleanup timer is cancelled when the view unmounts
(`web/src/desk/pullouts/views/FollowThroughView.tsx:204`–`:211`); an expired key is removed on a later
read (`:121`), so the write need not expire after eight seconds in storage.

This is a current code path, not a live disclosure measurement. Keep the
existing encrypted custody when refining receipts; no new privacy system
is needed. **Tenet 7; Constitution III and VI.**

### 2. P1 — Some displayed obligations have the wrong writer and duplicate a real action

Board cards for non-action loops use `loop.id` (`holdspeak/services/follow_through_service.py:230`).
The view gives every non-People card the same four action-item writes
(`web/src/desk/pullouts/views/FollowThroughView.tsx:370`–`:380`). `/complete` looks up only `action_items.id`
after the People branch and raises `Action item not found` for an ordinary
loop ID (`holdspeak/services/follow_through_service.py:393`–`:410`). An existing correct authority
is already declared by `DoorService._follow_through_card`: loop/decision
cards use cadence verbs (`holdspeak/services/door_service.py:240`, `:280`), whose writer is
`CadenceService.set_status` (`holdspeak/services/cadence_service.py:110`).

This is reachable through real producers. `commit_decision` creates an
action and decision commitment (`holdspeak/services/follow_through_service.py:320`, `:350`);
`LoopCollector._collect_meeting_decisions` produces a second loop for that
commitment (`holdspeak/cadence/collector.py:127`–`:174`). Board deduplication covers only
`meeting_action` loops (`holdspeak/services/follow_through_service.py:169`, `:220`), so the
decision loop and action can both show the same obligation. Completing the
action updates loops by the action ID (`:455`), while this loop's source ID
is the decision ID. Its closure waits for recollection. **Tenets 3 and 5;
UX-CANON A.11.**

### 3. P1 — Action outcomes can be unchanged or hidden

Snooze writes only an UPDATE to already-existing cadence loops
(`holdspeak/services/follow_through_service.py:495`–`:504`) and returns success without checking
whether any loop changed (`:588`). A task created by the real note/door
producer has no such loop yet (`holdspeak/services/door_service.py:82`–`:98`), while the board
already includes its action. The normal collector calls the repository with
`include_completed=False` (`holdspeak/cadence/collector.py:94`), which selects
only `status = 'pending'` (`holdspeak/db/meetings.py:1194`). Note tasks and
committed decisions are written as `open`, so collection itself does not
create their action-linked loop. Snooze can succeed and leave those rows on
the board. The current snooze test seeds its loop in
advance (`tests/unit/test_write_through_verbs.py:24`, `:74`), so it does not
cover this case.

The face also ignores the response and renders success feedback only for
Done (`web/src/desk/pullouts/views/FollowThroughView.tsx:223`–`:237`); Dismiss, Snooze, and Assign have no
explicit outcome. After the last Done empties the board, an Undo rejection
sets `error` (`:239`), but the empty-board return omits it (`:281`–`:283`);
the error render is below that return (`:298`). An attempt can fail while
the owner sees only the Done receipt and empty state. **Tenet 3;
Constitution VI; UX-CANON A.10.**

### 4. P2 — The lane contract does not answer “mine / owed to me / needs review”

`_lane` checks only whether an owner exists, then uses the due date
(`holdspeak/services/follow_through_service.py:829`–`:849`). A report's work due today goes to
Now; the owner's own work without a due date goes to Waiting. The face adds
no ownership filter and displays an unmapped owner as initials with the
name in a tooltip (`web/src/desk/pullouts/views/FollowThroughView.tsx:337`–`:345`). People mapping is
optional (`holdspeak/web/routes/follow_through.py:41`–`:71`).

People already stores the reverse commitment direction, but deliberately
excludes it from this board (`holdspeak/services/people_service.py:58`, `:1519`–`:1521`;
`tests/unit/test_people_service.py:222`, especially `:244`). This is a scope
gap for the requested Tuesday job, **not a regression in the current People
contract**. The settled design must choose an honest use of the existing
People lists/relationship opener or a deliberate projection change.

To review also combines pending-review items with already-accepted unowned
items (`holdspeak/services/follow_through_service.py:829`). Its card schema does not retain
`review_state` (`:86`), and the face offers neither review acceptance nor
the already-supported date writer. Ownership classification already exists
in `holdspeak/services/needs_you_membership.py:515`, `:546`, `:1319`; reuse its
owner-name rules if this job is put on Follow-through. **Tenets 3 and 7.**

### 5. P2 — The row hides the task and source while repeated chrome leads

Every lane is rendered, in fixed Now → Waiting → To review → Overdue order
(`web/src/desk/pullouts/views/FollowThroughView.tsx:53`, `:299`), including a No items body for an empty
lane (`:408`). A populated lane says its count twice, on Section and Ledger
(`:305`, `:309`); the library already permits a Ledger without another head
(`web/src/desk/surface/Surface.tsx:788`, `:808`).

Rows omit `wrap` (`web/src/desk/pullouts/views/FollowThroughView.tsx:329`), inheriting a one-line
ellipsis for the task (`web/src/desk/surface/surface.css:1473`). Opening the
row does not add a full task-text view. Unmapped owner initials, a relative
date, and a source glyph occupy the remaining cells (`web/src/desk/pullouts/views/FollowThroughView.tsx:335`).
The source verb's word is only in title/ARIA (`:353`–`:365`). Notes have a
valid source but `available=false` (`holdspeak/services/follow_through_service.py:667`);
threads have `available=true` with no segment text (`:650`). Expanded rows
then show SOURCE MOMENT UNAVAILABLE / Source moment unavailable
(`web/src/desk/pullouts/views/FollowThroughView.tsx:383`–`:401`) even though these are openable non-meeting
sources. People receives the same irrelevant unavailable-moment line.

A focused drill sets `openCardId` only (`:200`); it does not pass the library's
`selected` prop, which owns scroll and focus (`web/src/desk/surface/Surface.tsx:886`–`:892`). A
long-board drill can therefore open a row without bringing it into view.
These are source facts; actual truncation, row visibility, count prominence,
hit overlap, and spacing are **unverified geometry**. CSS also carries an
accent rail on Overdue (`web/src/desk/pullouts/intelligence.css:635`) and a nowrap mapped-person
chip (`:666`). Root should judge the live face and use the existing kit
before adding any component. **Tenets 2, 3, 5, and 6; UX-CANON C and D.**

## Existing focused tests and proposed small budget

Names below were read in source. Nothing was collected or run in this audit;
no green result is claimed.

| Existing file | What it already covers / gap |
| --- | --- |
| `tests/unit/test_follow_through_service.py:95` | Board lanes, project/owner filters, action/decision provenance, pending review, overdue, snoozed-loop exclusion (`:382`). No action Snooze without a pre-existing loop or decision-loop write round trip. |
| `tests/unit/test_write_through_verbs.py:58` | Done, Dismiss, Snooze, Delegate, Reopen write-through; fixture always creates an action loop. |
| `tests/unit/test_decision_loop_collection.py:56` | Real accepted/committed decision → collector; verifies loop idempotence, not the combined board/writer result. |
| `tests/unit/test_people_service.py:137`, `:222` | Transient encrypted projection, supported transitions, deliberate exclusion of report-owed commitments. |
| `web/src/desk/pullouts/views/FollowThroughView.test.tsx:86` | Optional person chips, initials, note/decision/meeting source dispatch (`:144`), Done id survives remount and Undo addresses that id (`:173`), recorded lane counts (`:207`). Other actions and empty-board refusal not covered. |
| `web/src/desk/pullouts/IntelligenceTruth.test.tsx:105` | Visible overdue drill, clear filter, filtered empty state, honest whole-board emptiness. |
| `web/src/desk/__tests__/needsYou.app.test.tsx:108` | Follow-through drill opens the requested row's verbs. It does not assert selection, scrolling, full task visibility, or successful review acceptance. |
| `tests/integration/test_face_wire_fences.py:379` | Existing real-hub recorder/fence for the honest Follow-through board. Use recorded producer answers for new face cases. |

Suggested implementation budget: **six new test functions, in existing files**.
Two backend cases in `test_follow_through_service.py`: (1) real
commit-decision → collector → one obligation with a working authority;
(2) real `DoorService.add_item` → Snooze without a linked loop → durable hidden
state or an honest refusal. Four rendered cases in `FollowThroughView.test.tsx`:
People Done retains encrypted custody; last-row Done → failed Undo shows the
failure; recorded non-Done writes show the returned outcome; mixed recorded
source/owner rows retain full identity and use the correct source/action
authority. Extend the existing drill case only if the settled design uses
the library selection behavior. Update existing word fences with the chosen
copy, retaining their state assertions.

Root's isolated live walk and the existing generic desk sweep own 1440/393
geometry. No new framework or phase-named browser suite is needed. Any
eventual pytest/vitest/graph walk must use the repo test lock and an isolated
HOME. Do not run `tests/e2e/test_metal.py`.

## Excluded from findings and remaining unknowns

Current source already has worded action buttons, the To review lane name,
verified note/decision/meeting source dispatch, card-specific Done Undo,
desk-change refresh with read ordering, and an honest clearable overdue
filter. These prior fixes are not re-reported. The old 390×300 first-open
size is also excluded: `web/src/desk/pullouts/size.ts:16` now seeds 880×700,
with saved geometry taking precedence.

No claim about actual owner rows, encrypted sidecar readiness, live route
results, screenshots, accessibility tree, pointer ownership, exact geometry,
or test outcomes. Those remain root's walk and implementation verification.

**HOLD FOR BUILD — audit complete; no product changes authorized by this report.**

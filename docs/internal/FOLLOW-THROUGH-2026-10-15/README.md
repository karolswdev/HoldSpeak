# Follow-through and attention refinement

Base `420a0eb28`; isolated worktree `wt-follow-through-20261015`. The owner
called Follow-through confusing and asked for continued substantive surface
refinement. This pass covers Follow-through, Brief selection, the Decisions
reader and the decision window with existing Workbench components and writers.

Final quick check GREEN; PR and normal local deployment recorded at release.
Owner judges it live.

## Direction and changes

[Settled direction](DESIGN.md), [library canvas](canvas/index.html),
[Follow-through audit](AUDIT-FOLLOW-THROUGH.md) and
[neighbor audit](AUDIT-NEIGHBORS.md). Root rendered/read the existing production
screens and the library direction at 1440/393 before build. The canvas uses
declared samples; it proves direction, not service behavior. Early canvas
runs stopped on a Material prop/font allow path and then exposed phone row
specificity; both were corrected. The final direction is in `canvas-approved/`.

Follow-through has one heading per populated date/review group: Overdue,
To review, Due soon, Later. Task text wraps, full owner names remain visible,
and date/source facts are explicit. Done, Details and source actions are
named; Manage groups Owner/Assign, Due date/Save date, Tomorrow, Dismiss and
Cancel. Dirty drafts survive refresh, lane moves and exact rejected-value
Retry. People receives only its existing supported controls, and its Done
receipt stays in memory. Cadence Close/Stop/Tomorrow uses actual loop writers
without manufacturing action Undo. [Focused face proof](BUILD-FOLLOW.md).

The service creates a missing source-keyed Snooze loop in the existing
transaction. A new confirmed task now leaves the active board before any
collector pass. Canonical action identity suppresses duplicate action/decision
mirrors, including filtered or completed actions. Snooze survives stale loop
owner fields on owner-filtered reads. Standalone loops remain independent.
[Focused backend proof](BUILD-BACKEND.md).

Brief's latest person or item owns its selected row and footer actions.
Late agenda/shelf failures name the original request subject alongside the
current selection; Retry retains the original target. Decision status uses
the library choice popup: inspecting writes nothing, explicit choice uses
the existing PUT, refusal keeps the saved state and offers Retry. Decision
bodies use named inset Material, with context/evidence/history folds and
worded source/chain actions. Failed next-record reads show that destination's
error and Try again/Results, rather than the prior record as a result.
[Neighbor proof](BUILD-NEIGHBORS.md).

## Review and focused checks

[Independent final source review](REVIEW.md) found two P2 issues and rechecked
the fixes once: a record's top-level decision id was used as a meeting id;
a late Brief failure did not identify the original Retry subject. Existing
canonical source mapping and named receipts fix them. Root also reproduced
an offscreen date failure after scrolling to Manage. Each newly rejected write
now scrolls its named notice into view once; quiet reads do not scroll.

Root read final scoped run tails: **44 backend tests**, **46 Follow tests in
five files**, **60 neighbor tests in six files**, all passed. Regression names,
red runs, final commands and limitations are in the three build reports.
Follow logs a non-failing jsdom canvas warning, which is not browser evidence.
TypeScript first found a fixture `never[]` cast; the explicit board type fixes
it. Final TypeScript passed. Architecture/atlas/doc claims first found three
stale presentation anchors; current atlas anchors now name the actual picker,
Context and agenda callback. The same **651 checks passed** after correction.
No sealed graph pass was edited.

## Root production walks

All runtime artifacts below are under `.tmp/follow-through/`, not tracked
screenshots. Each hub uses a fresh isolated HOME/DB, with no owner state,
model execution, native capture, clipboard or external send.

Before: six Follow states at each width on bundle `cfa38b02306c2789`, using
real Note and Door task producers. Root observed repeated headings, initials,
clipping, glyph/dead source controls, accepted Snooze leaving a new task on
board, and last-item Undo refusal with no visible error. Neighbor baselines
captured six states per width: status refusal hidden, Ewa footer retained after
item selection, and old record retained on failed Next. The initial desktop
neighbor rig stopped on a wrong object URL; the corrected run is retained as
`neighbors-before-retry-1440/`. Its initial footer observer read Settings;
root used the actual Today screenshot, then corrected the observer.

After: `after-final-1440/` and `after-final-393/` captured **14 states each**,
with no page errors, on bundle `ac30d81663f205b6` (`index-C79zwcIV.js`). Real
assignment saved Grace Hopper. A controlled date refusal kept the newer
2026-10-21 draft; Retry saved the rejected 2026-10-19 value, and Save date
then stored the newer value. The named failure was visible and owned its
central hit point at both widths. Open note reached the actual source and
returned. Tomorrow hid the new action and the isolated DB row showed one
canonical `meeting_action` loop with the same action id, snoozed until the
next day. Last Done, controlled Undo refusal and exact real Retry restored
the task. Three declared repository-seeded manual loops exercised actual
Close/Stop/Tomorrow routes and board transitions. The seed is not collector
or model evidence. Root read board, Manage, date refusal, Snooze, empty-board
Undo and cadence shots.

The first after rig stopped on an over-scoped row locator; the second reached
Snooze but tried a source_id absent from the cadence HTTP projection. Those
outputs remain separate. The final rig reads the canonical source identity
from its explicitly isolated DB and validates lifecycle through real routes.

Neighbor after: `neighbors-after-final-1440/` and `neighbors-after-final-393/`
captured **11 states each**, with no page errors. Real desk decision status
inspection sent no write, the explicit Accepted choice was deliberately refused
once, and exact Retry updated the real stored status. Recorded Brief/People
samples replay at HTTP boundaries: person → item makes Platform review own the
footer, and a held Ewa agenda read refused after that change. The footer showed
the current item and the named Ewa failure; Retry used Ewa's original route and
one agenda payload. Governing record samples are declared replays; Next first
hit the real missing-record 404, showed its own failure without the old body,
then Try again read the exact replayed successor. Results returned to the list.
No agenda store, record producer, provider send or model claim comes from those
replays. A replayed record absent from the real DB naturally refuses the Send
preview; this is not evidence of a send dispatch. Root read the actual papers,
selection/failure footers and requested-record recovery at both widths.

Two earlier neighbor after rigs stopped on harness expectations: a controlled
503 renders the existing standard HTTP reason rather than the injected body;
then an immediate Retry observer ran before its agenda request completed. Both
outputs remain separate. The final observer awaits that exact response.

The official graph case `case.follow_through.snooze.new_task` passed at 1440
and 393 using real Note and Door producers, no collector/model/replay. The
first click dispatched POST complete (200), and the board GET proved all four
active lanes empty. Root read initial feedback and settled terminal outcome
separately: **1.071 / 1.081 seconds**, within 30 seconds. Before showed the
exact new action; after showed the dated result and empty board. Pointer and
native browser touch respectively were recorded. Fresh HOME/DB paths, dirty
base revision and no boundary substitutions were checked; no page errors.
Outputs: `graph-snooze-1440/20261015T195902Z-case.follow_through.snooze.new_task-astra-1440/`
and `graph-snooze-393/20261015T200005Z-case.follow_through.snooze.new_task-astra-393/`.
The current graph join check passes, with its 14 existing subtype notes.

## Limits and continued work

These groups classify dates/review state; they do not implement Mine/They owe
ownership. Isolated UI replays do not prove encrypted People store readiness,
provider health, microphone hardware, clipboard or sending. Normal hub release,
public availability, owner acceptance, full main tape and postmerge review are
separate facts. The bounded source review is not labelled Muad'Dib's check.


## Wider release check

First quick: 365 web passed, 1334 affected Python passed / one failed,
107 desktop/phone sweeps passed (2 existing xfails), and 17 canon passed.
The failure was the existing parking test's explicit expectation of a duplicate
decision loop card. Its before/restored expectations now assert canonical
actions and absence of mirrors; parked-all-hidden and physical action-loop
restoration checks are unchanged. Root read the exact diff and the latest
**45/45 backend/parking scope**. Backend product code did not change in this
round. Logs: `quick-release/`, `backend-parking-{collect,green}.log`.
Second quick: 365 web and 1335 affected Python passed; 106 sweeps passed,
one failed (2 existing xfails); canon 17 passed. The failure observed a 54 px
movement in Settings → Engines during its stillness fence. Settings product
code is unchanged by this pass; the first full sweep passed this case. The
exact case collected once and passed alone in 12.76s (`sweep-models-repro.log`).
No product/test code, waiver or threshold was changed for this movement. A
fresh complete quick run confirms the release; the intermittent motion remains
an explicit limitation rather than an inferred repair.
Final complete quick (`quick-confirm/`, `quick-confirm.log`) is GREEN:
**365 web / 1335 affected Python / 107 desk sweeps (2 existing xfails) /
17 canon**. Root read all tails and the exit code. The frontend build id
remains `ac30d81663f205b6`; the actual product walked above is unchanged.
Architecture generation and graph join checks pass. No full/main tape or
postmerge review is inferred from this result.

[Next surfaces](NEXT-SURFACES.md) ranks four inherited issues found during
this pass: the shared divider can overpaint an active window; Decision mounts
a duplicate Send preview by default; text Save dismisses the editor before
its result; and the mounted Send preview lacks a version after status change.
The audit distinguishes observed appearance from source-only behavior and
preserves the existing send/Retry safeguards. These are not marked repaired.


An additional isolated phone shot in `long-owner-393/long-owner.png` shows the
whole long task and Alexandra Montgomery. The task wraps across two lines;
its measured scrollWidth does not exceed its clientWidth. Root read the shot.

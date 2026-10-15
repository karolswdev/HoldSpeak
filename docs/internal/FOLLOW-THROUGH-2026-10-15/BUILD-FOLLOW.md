# Follow-through build — 2026-10-15

**Built and frozen · HOLD FOR SHIP.** Root owns independent review, build,
isolated live walk, screenshots, quick check, and release.

Worktree `/Users/karol/dev/tools/wt-follow-through-20261015`, base
`420a0eb28`. Implemented the settled `DESIGN.md` Follow-through direction
against root's library canvas. Tenets 2/3/5/6/7: readable work, one action,
visible outcome, existing components and canonical authorities.

## Delivered

- Only populated Overdue → To review → Due soon → Later groups, one library
  heading/count per group. Wrapped task, full mapped/recorded owner, explicit
  date facts plus stored calendar date. Positive age labels say Assigned or
  Added. Source buttons say their actual destination and require a verified
  ref. Missing source is a fact. Valid note/thread/People sources no longer
  claim that a meeting moment is unavailable.
- Visible Done/Details on action and People rows. Inset Manage with named
  Owner and Due date fields, Assign and Save date through existing writers,
  Tomorrow, Dismiss, Cancel. Due date is a library text StringGadget with
  numeric input mode and `YYYY-MM-DD` placeholder, without a native picker.
  People receives no unsupported assignment/date/snooze controls.
- `decision`/`cadence_loop` cards use the existing cadence Close/Stop/Tomorrow
  HTTP routes. They receive no action-item Done or Undo.
- A synchronous global write ref prevents conflicting writes before React
  paints disabled controls. Initial reading blocks; refresh keeps the
  accepted board and edited values visible. Exact write failures and Retry
  render outside empty/filter branches, with the task and failed verb.
  Read refusal has its own Retry read. Successful writes show a result.
- Drafts survive lane moves and quiet refresh. A saved field clears its
  dirty flag only if the field still matches that submitted value; newer
  edits remain. Retry resubmits the rejected request, preserving newer input.
  Only the newest started board read may land.
- Ordinary Done keeps its existing eight-second persisted receipt/Undo.
  People Done/Undo exists in memory only; legacy persisted People receipts
  are discarded on read. No private body or opaque People receipt is saved.
- Addressed navigation opens and selects the actual target after the board
  arrives. The existing row selection behavior scrolls/focuses it; ordinary
  refresh does not repeat scrolling. Tomorrow uses the local calendar day,
  including during a negative-offset evening.

Product anchors: `web/src/desk/pullouts/views/FollowThroughView.tsx:56`
(groups), `:69` (receipt privacy), `:151` (read/draft custody), `:206`
(write guard and exact Retry state), `:252` (cadence routes), `:274`
(states and face). Local material/layout is in
`web/src/desk/pullouts/intelligence.css:599`; StateChip is bounded to
`width: fit-content` at `:652`.

## Exact scope and proof

Owned product files: FollowThroughView.tsx and only the Follow-through CSS
slice of intelligence.css. Tests changed: FollowThroughView.test.tsx,
IntelligenceTruth.test.tsx, IntelligenceWalk.test.tsx. IntelligencePullout's
test remained unchanged but was included in every run. Root additionally
authorized the existing `needsYou.app.test.tsx` presentation fence: Done is
scoped to the actual row, Details must be open, Assign replaces Delegate,
and only the requested card is expanded. Its owner/obligation assertions
remain intact. Shared library/host navigation/backend/neighbor faces were
not edited by this lane.

All commands used `.tmp/follow-through/locked.py`, which invokes the repo
test lock with a fresh isolated HOME and the declared machine-state switches.
No browser, build, installation, staging, commit, or owner-state action.

Initial collection: `.tmp/follow-through/follow-collect-red.log`, exact four
files, exit 0. Before implementation, `.tmp/follow-through/follow-red.log`:

```text
Test Files  1 failed | 3 passed (4)
     Tests  3 failed | 25 passed (28)
```

The three new face cases failed on the old face: readable identity/groups,
legacy People receipt custody, and the new last-row Done/Undo path.
Root's before walk separately observed the hidden Undo refusal and no-op
Snooze; this lane does not claim to have independently walked those defects.

Final collection: `.tmp/follow-through/follow-collect.log`, exit 0, 46 named
tests in exactly these five files:

```text
src/desk/pullouts/views/FollowThroughView.test.tsx
src/desk/pullouts/IntelligenceTruth.test.tsx
src/desk/pullouts/IntelligenceWalk.test.tsx
src/desk/pullouts/IntelligencePullout.test.tsx
src/desk/__tests__/needsYou.app.test.tsx
```

Final run: `.tmp/follow-through/follow-green.log`, exit 0:

```text
Test Files  5 passed (5)
     Tests  46 passed (46)
  Duration  7.65s
```

Root's TypeScript check then found TS2352 in the lane-move test fixture:
its initially empty lanes inferred `never[]`. Fixed the fixture with an
explicit `Record<keyof typeof EMPTY_BOARD, (typeof card)[]>` annotation and
removed the cast. Product files stayed frozen. Re-collected the same 46
names in `.tmp/follow-through/follow-collect-typefix.log` (exit 0), then
re-ran the exact five files in `.tmp/follow-through/follow-green-typefix.log`:

```text
Test Files  5 passed (5)
     Tests  46 passed (46)
  Duration  7.80s
```

Root owns the subsequent TypeScript/build result; this lane did not run it.

Root's production walk then found that a rejected date's board-top notice
could sit above the current Manage viewport. Added one ref/effect around the
existing write ActionNotice: each new rejection scrolls that notice nearest
once. The notice keeps the failed verb, task and exact reason; field edits
and quiet board refreshes do not repeat the scroll. No duplicate alert,
library, host, or CSS change. The existing date-refusal case now asserts
that exact notice is scrolled once, task/verb are visible, quiet reads do
not scroll again, newer input remains, and Retry sends the rejected value.

Proof: `.tmp/follow-through/follow-red-notice.log` failed exactly that new
scroll assertion (`1 failed | 45 passed`); collection in
`follow-collect-notice.log` remained 46 tests in the same five files. Final
run `.tmp/follow-through/follow-green-notice.log`, exit 0:

```text
Test Files  5 passed (5)
     Tests  46 passed (46)
  Duration  8.26s
```

Product and tests are frozen again. Root owns the production re-walk.

The final inventory includes these new rendered behavior cases:

```text
draws each populated group once, with wrapped tasks, full owners and verified source words
keeps People Done and Undo in memory, and discards a legacy persisted private receipt
shows a last-row Undo refusal on an empty board and Retry repeats that exact write
Assign uses the existing writer once, keeps the board visible, and preserves a newer owner draft across a lane move
a refused date keeps the draft and Retry sends the rejected date without replacing newer input
Tomorrow sends the next local day during a Denver evening, and Dismiss is a separate receipted write
People exposes only its existing Done, Dismiss and source authorities
an addressed task scrolls and expands after its read, while refresh neither re-scrolls nor accepts an old answer
Close loop uses its actual cadence writer and never offers an action Undo
Stop uses its actual cadence writer and never offers an action Undo
Tomorrow uses its actual cadence writer and never offers an action Undo
```

`git diff --check` was clean for the six changed product/test paths.

## Evidence boundaries

New normal-task cases replay the actual board from root's isolated Note +
Door producer walk, embedded with provenance in the test file. People uses
the existing real-hub recorded People card. Cadence uses root's actual HTTP
board recorded in `.tmp/follow-through/loop-wire/board.json`, explicitly
seeded through `CadenceRepository.upsert_loop(OpenLoop(source_type=manual))`;
it is not collector/model evidence. Controlled refusal/pending responses
prove face dispatch and rendered state transitions, not real service writes.

The successful run logs a non-failing jsdom `HTMLCanvasElement.getContext`
warning from DeskIcon. This lane does not claim a clean browser console or
live geometry from that run. Actual 1440/393 fit, pointer reach, real API
write results, encrypted-store readiness, microphone behavior, and release
build remain root's verification. No unsupported Mine/They owe buckets or
new capability was added.

**HOLD FOR SHIP.**

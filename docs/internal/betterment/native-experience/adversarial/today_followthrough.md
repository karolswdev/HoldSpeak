# today_followthrough

JOB: See what needs attention today and keep commitments moving  
BASELINE: main555728021 (PR1430; anchors may drift)  
REVIEWER TASK: review_today_followthrough  
EVIDENCE CLASS: source, assertions, captures; no execution

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts at Today, the bell, or Needs you: read one ranked attention
answer, inspect its source, take the lawful next act, see its outcome, and
return after refresh, failed read, close/reopen, or a later day. The audit's
broad duplication gap is not an observed bug. Today imports `useNeedFaces` and `NeedRow`, while `TodayNeeds`
explicitly uses the same snapshot, rank, and verbs as the full Needs window
(`web/src/desk/needs/NeedsDrawer.tsx:951-1042`,
`web/src/desk/needs/TodayNeeds.tsx:1-5,31-35,79-87`). The hub answer is also
the shared membership for the bell, Chair, Dock, brief, notifications, and
MCP (`web/src/desk/needsYou.ts:771-777`). Today is contextual; Needs is the
full ledger; retain both.

FINDINGS:

1. **P0 — The stated gap would invite a duplicate runtime.** The audit does
   not name the existing projection or its identity boundary. `NeedsYouRoomItem`
   already carries `actionItemId`, `proposalActionItemId`, `commitmentId`,
   `proposalId`, and `meetingId` (`web/src/desk/needsYou.ts:45-67`), and the
   same `NeedRow` posts the same `card_id` from Today and Needs. Owner cost:
   a worker could build a second “Today task” store and make counts or Done
   diverge, failing Tenets 2, 3, and 5. Correction: replace this gap with a
   typed contract table: source id, open ref, lawful verb, receipt, and
   refresh/return route for actions, proposals, Decisions, and People.

2. **P1 — Outcome and recovery are not bounded end to end.** The backend
   atomically updates an action, cadence loops, linked commitments, and
   proposal state and writes ledger refs/correlation facts
   (`holdspeak/services/follow_through_service.py:416-533,665-685`). The UI tests prove
   POST and Drop/Undo calls, not visible terminal receipt, stale response,
   close/reopen return, or duplicate prevention
   (`web/src/desk/__tests__/today.app.test.tsx:153-160`,
   `web/src/desk/__tests__/needs-you.app.test.tsx:192-203,287-297`). Owner
   cost: “Done” can look like disappearance, while retry or reopening could
   lose the original card identity. This fails Tenets 3, 6, and
   7. Correction: specify one receipt/return contract and prove it across
   Today, Needs, and People prep; preserve the original id through proposal →
   action → commitment transitions.

3. **P1 — Nudge is a real egress variant, not just attention.** Nudge first
   persists a note, resolves a saved destination, then hands off to the Send
   well (`web/src/desk/needs/NeedsDrawer.tsx:656-700`); assertions stop before
   channel send (`web/src/desk/__tests__/needs-you.app.test.tsx:206-217`).
   Owner cost: an implementation can claim follow-through while losing draft,
   destination, failure, or return truth. This fails Tenets 1, 3, and 6 and
   Constitution Articles III and V. Correction: bound Nudge to
   `send_prepare`/`send_commit` with egress, retry, and no-duplicate receipt;
   keep it separate from the local Done transition.

## Convergence

Converge `meeting_aftercare` on meeting/proposal/action provenance and the
first Needs/Today consumer; `people_prep` on the same action identity while
keeping encrypted `people:<id>` commitments source-owned; `decisions` on
`decision:<id>` and its commit-to-action boundary; `calendar_record`
on meeting/event source context; `send_prepare` and `send_commit` on Nudge
egress; and `mcp_tools` on `desk.needs_you`/`follow_through.*`. No universal
workflow_id is needed; share existing ids, openers, outcome/receipt, and row
grammar. Do not merge Today and Needs into
one face (timeline context versus full ledger), or merge People/Decisions into
a universal workflow registry; those boundaries protect authority and data
custody.

## User experience

The available captures show the intended fast path: Today and Needs both say
14; Today shows five ranked rows and `All`, while Needs shows the full ledger
(`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/today-1440.png`,
`needs-1440.png`). At 393, Today keeps three rows and `All`, and Needs keeps
the row grammar (`today-393.png`, `needs-393.png`). This likely pleases
Tuesday speed. Captures are not baseline proof or
owner acceptance; recovery, focus return, latency, accessibility, and craft
after an act remain unknown.

CONDITIONS: Correct the false duplication gap; document id/receipt/return and
proposal lineage; cover Nudge through send outcome. Keep shared projection.

MISSED:

1. High: Done/Later/Drop from Today, then close/reopen and find the same id and receipt.
2. High: proposal confirmation becoming one action without duplicate rows or receipts.
3. High: Nudge destination failure, send uncertainty, retry, and return to the commitment.
4. Medium: Needs read failure or People lock with Retry and no false empty state.

TUESDAY: Yes for finding and starting the work; not yet proven for truthful return after a write, failure, or egress.

## Acceptance challenges

1. Open a counted action in Today, press Done, then open Needs; assert one
   canonical `action_item:<id>`, one terminal receipt, and no duplicate after refresh.
2. Open a meeting proposal, confirm it, close/reopen Today, and assert the
   same obligation has one action/commitment lineage and one lawful next verb.
3. On a “They owe me” row, press Nudge, edit the prepared note, choose a
   supported destination, force a failed/unknown send, retry once, and return
   without a duplicate note or silent egress.
4. Make the Needs read fail, press Retry, then reopen the window; assert the
   previous answer is never presented as clear and the recovered row retains
   its source/open ref.

UNKNOWN: No tests were executed; no live Desk/API/provider/native action or
owner state was used. Source and captures do not prove persistence across
restart, performance, accessibility, or owner delight.

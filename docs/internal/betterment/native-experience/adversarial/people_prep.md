# people_prep

JOB: Prepare for a 1:1 with one report  
BASELINE: main555728021  
REVIEWER TASK: review_people_prep  
EVIDENCE CLASS: source, assertions, optional captures; no execution or owner walk

VERDICT: DO-NOT-RATIFY

## Totality

The job starts from Today, a calendar event, or People; resolves the report and
series; gives the architect prior decisions, open work, context, and agenda;
lets him edit what to raise; enters the 1:1; then records or stops it, returns
to the person, and carries actions into aftercare. The service aggregates
encrypted People records with plaintext meetings (`holdspeak/services/people_service.py:469-573`),
but the audit treats “prep capabilities are named” as the whole workflow.
Failure, stale refresh, concurrent windows, and return are not bounded.

FINDINGS:

1. P0 — The audit’s evidence set cannot support its implementation brief. The
   inventory names only the first 100 lines of `PeopleCore`/`PeoplePullout` and
   one backend test (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:2370-2399`),
   while prep is in `PeopleCore.tsx:941-1229`, the route is
   `holdspeak/web/routes/people.py:210-263`, and UI assertions cover linking,
   agenda, opens, and retry (`web/src/pages/cores/__tests__/peoplePrepB4.test.tsx:104-220`).
   Owner cost: a worker could redesign live behavior. This fails Tenets 2, 3,
   and 5. Correction: expand active paths/assertions, excluding parked code.

2. P0 — The job stops at a “Record meeting” press. That control passes an exact
   calendar id to `startRecording` (`PeopleCore.tsx:1108-1115`), but no audit
   criterion covers failed/stopped capture, review, or return to People and
   Today/Needs. Agenda, commitment, and action writes are separate calls
   (`PeopleCore.tsx:993-1019`). Owner cost: prep can look complete while Tuesday
   has no continuation. This fails Tenets 3 and 7. Correction: define the
   boundary using existing recorder, aftercare, and follow-through; do not invent
   a launcher.

3. P1 — The audit names cross-window identity and freshness but does not inspect
   their safeguards or bounds. A person window is `pullout:people:<id>`
   (`PeoplePullout.tsx:16-28`) and `openPerson` carries `people:<id>[:lens]`
   (`openObject.ts:22-34`). `PrepPane` does have live-effect cleanup
   (`PeopleCore.tsx:941-964`) and newer drafts survive a pending write
   (`PeopleCore.tsx:989-1019`); source review did not observe a wrong-person
   state. What remains unspecified is parent refresh/revision ownership and
   supported multi-window behavior. Owner cost: unbounded conflict work.
   This fails Tenets 3 and 5. Correction: document response identity, conflict
   wording, focus return, and whether same-person windows deduplicate. Test only
   supported relationship IDs/instances.

4. P1 — “Nudge” is an omitted side path: pressing it persists a `/api/notes`
   record before the visible send well (`PeopleCore.tsx:911-938`), whose shared
   contract is `documentSends.tsx:87-96`. The audit must say whether this is a
   draft, how discard/retry works, and where egress is disclosed. Owner cost:
   abandoned nudges become surprise notes or duplicate sends. This fails Tenets
   1 and 3. Correction: reuse `send_prepare`’s outcome contract.

## Convergence

Converge `people_prep` with `meeting_aftercare`, `meeting_archive`,
`today_followthrough`, `decisions`, `projects_room`, `project_update`,
`calendar_record`, and `send_prepare` only for contracts: stable refs
(`people:<id>`, `meeting:<id>`, `project:<id>`), source openers, and outcomes
(`PeopleCore.tsx:1151-1163`, `web/src/desk/needs/NeedsDrawer.tsx:129-131`).
First consumers are People, Aftercare, and Today/Needs. `_parked/FollowThroughView.tsx`
is not active. Keep private People data separate from shared pages; one giant
“work” face would destroy focus.

## User experience

The optional captures show a promising native direction: [/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/person-1440.png](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/person-1440.png)
(1440) gives NEXT 1:1, TO RAISE, two owe plates, and quiet folds; [/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/person-393.png](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/person-393.png)
(393) keeps the grammar without a modal. These are external captures, not
baseline proof or owner acceptance. The narrow capture is a peer/engineer fixture,
not proof of a report-specific agenda. Large Add controls and unused space also
need a craft pass: honest transitions alone will not establish delight. The
audit omits empty, missing-calendar, locked-store, stale, and return states.

CONDITIONS: Add omitted active source/tests; document the end-to-end state
machine and stable identities; specify stale/conflict/return behavior.

MISSED:

1. Capture stop/failure and reviewed aftercare return (highest cost).
2. Two person windows, fast refresh, and concurrent agenda edits.
3. Calendar/provider unavailable, People locked, and no linked event.
4. Nudge draft persistence, discard, retry, and egress.

TUESDAY: Not yet—the owner can reach a compact prep face quickly, but the audit does not prove he can trust the job through the meeting and back to work.

## Acceptance challenges

1. From a calendar/Today event with an alias but no linked series, open the
   person; show a suggestion, make no POST until “Link this 1:1”, then show the
   event by stable id. A rejected link leaves the suggestion and named retry.
2. With an agenda, one report action, and one owner action, add an agenda point,
   mark one done, open its meeting source, close/reopen the person, and verify
   saved state and focus return.
3. For supported relationship IDs/instances, refresh while a write is pending.
   Verify each response stays bound to its identity, same-person windows follow
   the documented deduplication rule, and the draft remains with named retry.
4. Press Record meeting for the exact event, exercise capture failure/stop, and
   return to People; the receipt names the result and the reviewed action appears
   once in active Today/Needs follow-through.
5. Press Nudge once, edit or discard its prepared note, retry a failed send, and
   verify no duplicate note or silent egress.

UNKNOWN: No tests were executed; no provider, native recorder, Desk API, owner
state, accessibility, performance, or live acceptance was observed. Captures are
external references; endpoint health and owner-desk population remain unknown.

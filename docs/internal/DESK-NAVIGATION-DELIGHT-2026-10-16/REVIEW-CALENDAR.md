DRAFT — bounded finished-source counsel, Sol xhigh, 2026-10-16.
UNCHECKED — awaiting Muad'Dib. This is not Muad'Dib's formal review and is
not a fast-cycle merge gate. Read-only review against base `11984`; only this
report was written. No tests, browser, product edits or agents were run.

VERDICT: RATIFY

FINDINGS:
None requiring a change in the bounded Calendar source. The repair serves
Tenets 3 and 5, and its receipt/error treatment serves Constitution VI.

1. Identity is assigned once, used as the row key and as the edit/remove
   target, and stripped from the wire. Text edits and a preceding removal do
   not replace the surviving row's identity. Evidence:
   `web/src/pages/cores/CalendarSnapshotReviewCore.tsx:129`, `:157`, `:240`,
   `:250`, `:306`; the real-library node/focus assertions are in
   `web/src/pages/cores/__tests__/CalendarSnapshotReviewCore.test.tsx:204`
   and `:228`.
2. Confirm sets the synchronous guard before submission. Anchor, event edits
   and removal consult that guard; the review remains mounted inside the
   pending fieldset, including the inherited mic Buttons. Confirm uses the
   library loading state outside that fieldset. Evidence:
   `web/src/pages/cores/CalendarSnapshotReviewCore.tsx:145`, `:242`, `:252`,
   `:263`, `:273`, `:389`; the deferred-request test checks one admission,
   retained nodes, all rendered Buttons disabled, and a refused pending edit
   at `web/src/pages/cores/__tests__/CalendarSnapshotReviewCore.test.tsx:253`.
3. A refusal or rejected request restores the submitted review, with its
   draft intact. Unchanged Retry serializes the same trimmed anchor and
   event objects; a new edit clears the failure and returns the verb to
   Confirm. Evidence: `web/src/pages/cores/CalendarSnapshotReviewCore.tsx:155`,
   `:178`, `:185`, `:246`, `:274`, `:396`; exact body equality and revised-draft
   assertions are in the named test at `:298` and `:336`.
4. Success takes count/source solely from the accepted response, with no
   invented fallback; refusal stays visible in the review. Layout uses the
   existing ledger/gadgets, a full-row title/location, named day/start/end,
   library Remove confirmation, and the named `surface` container to stack
   the phone schedule. Evidence:
   `web/src/pages/cores/CalendarSnapshotReviewCore.tsx:171`, `:219`, `:285`,
   `:311`, `:320`; `web/src/pages/cores/calendar-snapshot-review.css:16`,
   `:21`, `:44`.
5. The existing collect log lists 17 cases, and the existing run log records
   17/17 passing in 2.35 s. These are read evidence, not a fresh execution:
   `.tmp/navigation/calendar-test-collect.log:1`;
   `.tmp/navigation/calendar-test-run.log:23`, `:25`.

CONDITIONS:
None for this source verdict.

MISSED:
No additional bounded implementation miss identified. The test named
“cancel (closing window) writes nothing” asserts only that mounting makes no
API call; it does not close a real window. The removal test proves surviving
node/focus identity with `fireEvent`, not pointer focus transfer or real
keyboard traversal. Evidence: the named test at `:165` and `:228`.

TUESDAY:
The source supports reading and correcting the events without losing field
identity, then retrying a refused save; the actual phone and writer outcome
remain root's live verification.

UNKNOWN:
Real 1440/393 fit, pointer ownership, browser focus/keyboard behavior, footer
portal placement and the isolated ICS/config write were not exercised here.
The test replaces SurfaceFooter and SurfaceSection and mocks the API
(`web/src/pages/cores/__tests__/CalendarSnapshotReviewCore.test.tsx:15`,
`:21`, `:36`), so it cannot prove those outcomes. Earlier calendar images
under `.tmp/navigation/after-{1440,393}/` are declared synthetic extraction
scope, not OCR/model proof, and are not evidence of this rebuilt layout.
The guard proves one in-flight request for this mounted review; this review
makes no server exactly-once, real voice, provider or OCR claim.

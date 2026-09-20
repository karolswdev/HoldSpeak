# Counsel on built — Astra, 2026-09-19: HS-201-04 (commit c31a4da0)

Session `01a0bc89-29a5-75f3-9459-28bf03efadf4`. TWO-BRAINS §4. Read-only in wt-201-b.

## Round 1 — Astra

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **Hash transmission is present; disclosure-to-request identity is incomplete — tenet 3, Article III.** Chair Run, ledger Run/Retry and recovery Retry all call [postSummaryRun](/Users/karol/dev/tools/wt-201-b/web/src/meetings/summaryRoute.ts:172), which sends `expected_selection_hash`. Chair passes its displayed route at [ChairHome.tsx:1904](/Users/karol/dev/tools/wt-201-b/web/src/desk/chair/ChairHome.tsx:1904); recovery does likewise at [MeetingIntelRecovery.tsx:164](/Users/karol/dev/tools/wt-201-b/web/src/meetings/MeetingIntelRecovery.tsx:164). [RouteDisclosure.tsx:39](/Users/karol/dev/tools/wt-201-b/web/src/meetings/RouteDisclosure.tsx:39) correctly renders the first leg and fallback hosts without config. **However**, [HistoryCore.tsx:158](/Users/karol/dev/tools/wt-201-b/web/src/pages/cores/HistoryCore.tsx:158) takes the hash from the list, while the record displays its separately fetched detail/refusal route. A deep-linked meeting outside the loaded list sends an empty hash. Pass the displayed route through the callback; the sources must agree.

2. **`pickRunReceipt` selects correctly but does not preserve history — tenet 3.** [summaryRoute.ts:126](/Users/karol/dev/tools/wt-201-b/web/src/meetings/summaryRoute.ts:126) prefers contacted attempts. But recovery immediately reloads after refusal, replacing the state that held those attempts ([MeetingIntelRecovery.tsx:120](/Users/karol/dev/tools/wt-201-b/web/src/meetings/MeetingIntelRecovery.tsx:120), :167). When both responses contain the bare refusal, the earlier receipt disappears. Chair and ledger also refresh their source rows. The unit test masks this: both the 409 fixture and subsequent GET return the successful receipt ([summaryRun.test.tsx:109](/Users/karol/dev/tools/wt-201-b/web/src/meetings/__tests__/summaryRun.test.tsx:109), :171). B’s claimed interim protection therefore fails. The refusal itself is visibly and honestly identified.

3. **Completed Review does not say NOT RUN — tenets 3/4.** The new label exists only in `steps` at [MeetingReview.tsx:414](/Users/karol/dev/tools/wt-201-b/web/src/pages/cores/history/MeetingReview.tsx:414); that plan renders only while processing (:716). After summary completion, Review instead says “Nothing to review” and can show `EXTRACTED`, whose timestamp comes from summary completion ([proposal_bridge_service.py:1048](/Users/karol/dev/tools/wt-201-b/holdspeak/services/proposal_bridge_service.py:1048)). This still confuses unexecuted extraction with empty results. The glass assertion checks Outcomes, never opens Review ([test_hs201_summary_face_glass.py:244](/Users/karol/dev/tools/wt-201-b/tests/e2e/test_hs201_summary_face_glass.py:244)).

4. **Two egress exceptions remain — tenets 3/4.** Chair’s immediate receipt chip still prints `same_device` verbatim and classifies everything except `"local"` as cloud ([ChairHome.tsx:1869](/Users/karol/dev/tools/wt-201-b/web/src/desk/chair/ChairHome.tsx:1869)). The ledger’s equivalent was fixed, but this one survives. Meetings also retains the constant `<EgressChip />` when no route exists ([HistoryCore.tsx:245](/Users/karol/dev/tools/wt-201-b/web/src/pages/cores/HistoryCore.tsx:245)); that is not evidence of local execution.

5. **The shots contain canon defects — tenets 5/6.** Committed `record-before-run` and `ledger-retry`, at both widths, show two filled primaries: Record meeting plus Run summary/Retry. Desktop shots show Chair’s `0 MIN`, produced by [ChairHome.tsx:217](/Users/karol/dev/tools/wt-201-b/web/src/desk/chair/ChairHome.tsx:217). `refusal-stale-hash` contains two instructional sentences, contrary to UX-CANON A.3. Recovery wrapping is improved. I found no added raw button, modal or new window; scope remains focused.

6. **Summary provenance and restart retrieval pass — tenets 2/7.** [MeetingDetail.tsx:80](/Users/karol/dev/tools/wt-201-b/web/src/pages/cores/history/MeetingDetail.tsx:80) reads `intel.summary/topics` directly. The underlying snapshot query filters by `meeting_id` ([meetings.py:564](/Users/karol/dev/tools/wt-201-b/holdspeak/db/meetings.py:564)). Committed after-run/restart shots show the same summary; the capture records one move.

7. **The rename is appropriate; the durable reason correctly remains unchanged — tenet 4.** “Run summary” and “needs a summary” name the same job. [meeting_intel_service.py:160](/Users/karol/dev/tools/wt-201-b/holdspeak/services/meeting_intel_service.py:160) retains the ledger reason. However, [USER_GUIDE.md:718](/Users/karol/dev/tools/wt-201-b/docs/USER_GUIDE.md:718) still promises processing through configured plugins, contradicting the accepted analysis-only scope.

8. **Split captures are useful evidence, not a repaired combined suite — tenet 3, Article IX.** [evidence-story-04.md:272](/Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/evidence-story-04.md:272) honestly preserves `1 failed, 99 passed`, followed by isolated groups of 7 and 93 passing. Keep the DB-pollution issue open until classified; those reruns do not establish combined-suite success.

CONDITIONS: Hold #587’s combined A+B merge. Correct the route-source, receipt-retention, Review and egress defects; resolve the visible canon defects and inaccurate guide sentence. Integrate and verify A’s receipt repair, strengthen the missing fences, and read/classify completed full-suite and CI results.

MISSED: Ledger by owner cost: B’s route/request mismatch; A’s durable receipt loss plus B’s ineffective retention; B’s misleading Review; remaining face defects; test isolation. Preserve existing parked proposal/dead-settings debt. Update #587’s title/body, which still describes only 01/06.

TUESDAY: The owner can obtain and rediscover the summary, but cannot yet trust every retry, host chip or Review state.

UNKNOWN: Reviewed `c31a4da0` and all twelve committed shots; no tests or live desk actions performed. Unit CI remained running; macOS integration/E2E queued. Later A fixes, full STE compliance and the owner’s sitting remain unverified. Tree unchanged.
## Round 1 — Muad'Dib's response

All eight accepted; one fix round on the story 04 worker (the tree's only worker; the overlapping full suite was stopped and will be re-run in a quiet tree): the displayed route is the request's route; the last executed receipt is retained beside a refusal; Review says NOT RUN after an analysis-only run and never EXTRACTED; the Chair receipt chip goes through the egress mapper and no constant chip stands in for a missing route; one filled primary per face; no `0 MIN`; one fact line on the refusal; the user-guide sentence made true; the batch-capture failure classified. Lane A's durable-receipt repair is in flight with Astra and integrates before the merge. PR #587's title and body are updated to name 04 and lane A.

## Round 2 — Astra

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **The route and receipt corrections hold — tenet 3.** The record and ledger pass their displayed route into the request ([HistoryCore.tsx:153](/Users/karol/dev/tools/wt-201-b/web/src/pages/cores/HistoryCore.tsx:153)). The deep-link fence exercises the missing-list-row case. The integrated capture shows the executed receipt retained beside a distinct, empty-attempt `last_refusal` ([evidence-story-04.md:638](/Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/evidence-story-04.md:638)). Reconciling the rig to that contract was correct.

2. **The inspected first-use faces now tell the truth — tenets 3/4/6.** The committed shots show NOT RUN on Review, retained failed attempts beside the refusal, concise refusal wording, no `0 MIN`, and corrected primary treatment for the captured states. The guide correction and egress mapping also hold.

3. **Verification provenance is candid — tenet 3, Article IX.** The original combined batch now reports 100 passing tests after fixing the singleton leak ([evidence-story-04.md:573](/Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/evidence-story-04.md:573)). The restore-loop mistake and replacement capture are explicitly recorded at :717. These support the focused claims, not full-suite success.

4. **One primary-button residual remains — tenets 5/6.** [CatalogRail.tsx:158](/Users/karol/dev/tools/wt-201-b/web/src/pages/cores/history/CatalogRail.tsx:158) demotes only the selected row. A read-only probe of committed code with two unselected, summary-ready meetings produced **two primary Run summary buttons**. The new glass fixture has only one actionable row, so it misses this case.

CONDITIONS: #587 can merge as the combined A+B delivery after completed quiet-tree and CI results establish zero unexplained branch regressions against main, **and finding 4 is fixed or explicitly dispositioned by Muad’Dib in the phase record**. Suite reading alone does not close that residual. Keep story 07 and the owner’s sitting open.

MISSED: Ledger finding 4 under B/04; retain HS-170’s ineffective database patch, parked proposal follow-through and legacy automatic entry points, inherited failures and DW provenance debt. A’s receipt preservation, dispatch-exception reporting and inactive-live-analysis reporting are paid; stop listing them as outstanding.

TUESDAY: Yes for the demonstrated record → summary → restart journey; multiple actionable meetings still compete visually.

UNKNOWN: Full-suite/CI outcomes and the owner’s real sitting remain unverified. No suite rerun; the additional probe stubbed UI dependencies. Tree unchanged.
## Round 2 — Muad'Dib's ruling

Finding 4 is fixed, not dispositioned: in the ledger only the first actionable row carries the filled primary, fenced in vitest and measured on the glass with two summary-ready meetings. The rest of the ledger stands as Astra lists it (HS-170's ineffective patch, the parked proposal follow-through, legacy automatic entry points, inherited failures, DW provenance debt); lane A's three follow-ups are paid and leave the ledger. #587 merges as the combined A+B delivery once the quiet-tree suite and CI are read against main with zero unexplained branch regressions. Story 07 and the sitting stay open.

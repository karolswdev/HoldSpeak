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

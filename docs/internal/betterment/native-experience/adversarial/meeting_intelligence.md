# meeting_intelligence

Job: Run meeting intelligence and read a useful result.  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430).  
Reviewer task name: `review_meeting_intelligence`.  
Evidence class: source/assertions plus static 1440/393 captures; no tests, Desk walk, provider call, or owner acceptance.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The family is correctly bounded to asking for a saved meeting summary and typed output. It must not absorb capture/import or the later consent-bearing aftercare job. The audit is not yet a complete implementation brief: its only inspected UI source (`web/src/desk/pullouts/MeetingWindow.tsx:65-75`) chooses live versus saved content, while trigger, route disclosure, result, retry and return are in `web/src/pages/cores/history/MeetingRecord.tsx:198-231,242-258,363-369`, `web/src/pages/cores/history/MeetingDetail.tsx:645-751`, and `web/src/pages/cores/history/useSummaryRun.ts:57-131`. Schema-valid output is not proof that a decision is correct (`docs/MEETING_INTELLIGENCE.md:91-96`).

FINDINGS:

1. **P0 — the state/job contract is incomplete.** The inventory says queued/running/failed/finished and result quality are unknown (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:2023-2026`), but the audit does not name the auto/manual Run/Retry/Skip matrix, duplicate refusal, route drift, no transcript/route, absent drainer, partial publication, or reopen return. This fails Tenet 3 (help and accelerate); the owner cost is a stranded path or a second screen. Correction: make `intel_status`, `intel_job`, `planned_route.selection_hash`, `run_receipt`, `last_refusal`, and `aftercare_ready` the lifecycle, with one action and honest outcome per state.

2. **P1 — “read a useful result” has no falsifiable quality/provenance bar.** `web/src/meetings/MeetingSummarySlab.tsx:54-81` renders non-empty summary/topics; `web/src/pages/cores/history/MeetingDetail.tsx:714-785` renders outcomes and looked-at records; assertions mainly prove request bodies/tokens (`web/src/meetings/__tests__/summaryRun.test.tsx:242-327,425-448`). This fails Tenet 3 (clear useful results) and Tenet 7 (the architect’s decisions); the owner cost is mistaking a saved response for an actionable decision. Correction: require a useful summary and typed decisions/actions where the source supports them, truthful absence otherwise, source links where available, explicit partial/unknown output, and a review hand-off; never claim semantic correctness.

3. **P1 — background/restart behavior is named but not joined to the face.** The backend has durable queue/conductor and `drainer` truth (`holdspeak/services/meeting_intel_service.py:220-287`, `323-371`), and the window refreshes on desk/aftercare/focus signals (`web/src/pages/cores/history/MeetingRecord.tsx:172-196`), but the audit omits close/minimize, hub stop, backoff, drainer absent, and reopened window/Chair behavior. This fails Tenet 5 (modular component framework); the owner cost is stale status and lost return-to-work. Correction: separate retained operation from mounted UI and prove adoption after close, restart, and late completion.

4. **P2 — pleasure/craft is unassessed.** Historical outcomes captures (`docs/internal/betterment/capture/shots/41-meeting-outcomes-1440.png`, `docs/internal/betterment/capture/shots/41-meeting-outcomes-393.png`) show summary → decisions/actions → footer receipt, but are not current-shell or owner evidence. This fails Tenet 6; the owner cost is a slow, crowded first use. Correction: keep `Button`, `SurfaceWell`, `SurfaceFooter`, and one meeting window; add current 1440/393 acceptance for open → verify route → run → read summary → open one source-linked outcome.

## Convergence

Converge on the durable meeting contract (`meeting_id`, `intel_status`, `intel_job`, `planned_route`, `run_receipt`) and existing runtime notifications. First consumers are `meeting_record` (trigger/window), `meeting_import` (same saved-record entry), `meeting_aftercare` and `decisions` (typed outputs), and `meeting_archive` (reopen after restart); these relationships are explicit in the inventory group (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:1687-1694`). Keep capture/import native and aftercare consent separate. Do not merge them into a generic intelligence screen: their source, native boundary, and approval jobs differ. `meeting_archive` should reuse the same result identity, not invent another persistence authority.

## User experience

The likely happy path is efficient because the saved record stays in one window and the result precedes outcomes (`web/src/pages/cores/history/MeetingRecord.tsx:329-395`); the static capture supports that composition. Source-only assertions cannot certify readability, performance, accessibility, or delight. Optimize repeat use: clear route chip, one Run action, durable status after leaving, and direct return to the same result—not a wizard or queue dashboard.

CONDITIONS: Add the state/return matrix, define the useful-result/provenance bar, name the shared contract and first consumers above, and add 3–5 current 1440/393 falsifiable acceptance scenarios. No new runtime or approval framework.

MISSED:

1. Highest cost: close/restart while queued or running, then reopen and find the same result.
2. Route changes or drainer absence after the press, including refusal without provider contact.
3. Partial plugin publication where summary survives but decisions/actions remain incomplete.
4. Repeat run after transcript or model-route change without overwriting the prior receipt.

TUESDAY: Yes for a saved meeting if the one-window Run → result → source-linked outcome path remains visible; the audit is not yet specific enough to preserve that speed through recovery.

## Acceptance challenges

1. With a saved transcript and ready route, one Run press sends the displayed hash, shows QUEUED/RUNNING, then shows the persisted summary and receipt in the same window.
2. Close the window while queued; after a hub restart, reopen the meeting and observe the same job/result, with no duplicate run.
3. Change the route after disclosure; the press is refused before provider contact, shows the fresh route, and preserves the prior executed receipt.
4. Make one plugin fail after summary publication; the record shows summary plus an explicit incomplete state, Retry/Skip, and later returns to the same meeting.

UNKNOWN: No tests were executed; no live Desk, provider, native boundary, model quality, cold-restart, performance, or owner acceptance was observed.

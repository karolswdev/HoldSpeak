# meeting_archive

Job: Find the same meeting and result again after restart. Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd`. Reviewer task name: `review_meeting_archive`. Evidence class: source and assertions; no execution, live Desk/API, provider/native actions, or owner acceptance.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts with saved meeting data or a persisted Meetings window after restart. The owner must find it by title, date, filter, or transcript text, open its identity, distinguish transcript from queued/failed/partial/ready summary, read the linked result, and return to work. Parked records and interrupted intelligence are in scope; capture/import own intake, intelligence and aftercare own results. `docs/USE_CASES.md:22-32` and `docs/MEETING_ARCHITECTURE.md:150-160` establish this boundary; audit only states a broad collection gap.

FINDINGS:

1. **P0 — the finite archive page is not closed.** The face sends `limit=100` and never sends an offset or consumes `next_cursor` (`web/src/pages/cores/HistoryCore.tsx:125-141`), although the service emits that cursor (`holdspeak/services/meeting_service.py:702-760`) and the DB slices rows (`holdspeak/db/meetings.py:963-973`). This is source risk, not a live claim. Owner cost: an older meeting may be absent and require a guessed token. Tenets 2 and 3 fail if implicit. Correction: specify continuation/direct search, stable ordering, and return behavior outside page one; do not invent a generic Explorer.

2. **P0 — “same result” has no restart state contract.** A meeting can retain its transcript while summary work is queued, failed, or ready (`docs/MEETING_ARCHITECTURE.md:150-154`). `MeetingRecord` adopts a durable run receipt (`web/src/pages/cores/history/MeetingRecord.tsx:198-231`), and an assertion covers queued-to-ran adoption (`web/src/pages/cores/history/__tests__/meetingWindowR1.philo17.test.tsx:96-108`), but the audit does not define which summary/artifact/aftercare identity is “the result” or how partial/failed output reads after restart. Owner cost: missing work can look like “nothing happened.” Tenets 3 and 6 fail. Correction: bind meeting/run ids, artifacts, source links, and `intel_status` to one reopen contract with retry/return outcomes.

3. **P1 — selection, scroll, and return are only partly durable.** `selectedMeeting` is local state (`web/src/pages/cores/HistoryCore.tsx:62,112-164`), while `meeting:<id>` scope is workspace-persisted (`web/src/desk/__tests__/surface-windows.test.tsx:62-87`); Back is asserted only across an in-memory rerender (`web/src/pages/cores/history/__tests__/openActionsFacet.test.tsx:96-112`). Migration keeps only the newest meeting from old pullouts (`web/src/desk/store/compositorSlice.ts:77-109`). Owner cost: restart or stale filtering can restore a record but lose archive context. Tenets 5 and 7 fail. Correction: state persistence/reset for scope, filter, selected id, and scroll; validate stale ids using existing compositor ownership.

4. **P1 — the evidence ledger understates proof.** It names only `tests/unit/test_meeting_service.py` and leaves cold restart/long-list navigation unknown (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:2084-2119`). Assertions cover workspace rehydration, Back, stale reads, and receipts (`web/src/desk/__tests__/surface-windows.test.tsx:62-87`; `web/src/pages/cores/history/__tests__/meetingWindowR1.philo17.test.tsx:66-94`). Owner cost: workers may duplicate seams or treat test existence as archive coverage. Tenets 2 and 3 fail. Correction: inventory these as support, then add named cold-restart, >100-row, parked, and result-state scenarios; do not imply execution.

## Convergence

Converge with `meeting_record`, `meeting_import`, `meeting_intelligence`, `meeting_aftercare`, `decisions`, and `today_followthrough` (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:1687-1694`). Share meeting id, list/detail adapter, `intel_status`/receipt, canonical scope, refresh, and SurfaceFooter feedback. HistoryCore and MeetingRecord are first consumers; intelligence supplies result state, aftercare/decisions consume the same source identity. `windows`, `navigation_commands`, `objects_pullouts`, and `feedback` are framework consumers (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:3121-3202,3497-3518`). Keep intake, execution, and consent separate. Do not merge into `explorer_repo`: transcript search and meeting status are domain-specific (`docs/internal/betterment/native-experience/APPLICATION-MODEL.md:54-71`).

## User experience

Source suggests a good path: one Meetings window offers Record/Import, mic-enabled Search, compact rows, and row-to-record transition (`web/src/pages/cores/HistoryCore.tsx:323-375,462-499`); the record keeps Back and a footer receipt (`web/src/pages/cores/history/MeetingRecord.tsx:329-395`). Persisted scope should make an open record quick after restart. The bounded rail (`web/src/desk/surface/surface.css:340-359`) may become a long-list hunt; no capture was inspected. Source cannot certify 1440/393 craft, accessibility, latency, or delight.

CONDITIONS: Make page/ordering, result-state, persistence/return, and evidence boundaries explicit; name consumers and add four challenges. No owner gate/runtime.

MISSED:

1. Older-than-first-page meeting and unique transcript search.
2. Restart during queued, failed, or partial intelligence, with source-linked result identity.
3. Park/restore after restart without losing transcript or artifacts.
4. Same-time meetings, stale filters, and selection/scroll restoration.
5. Return from Meeting ready/Today and Back without stealing another window’s focus.

TUESDAY: Likely yes for a recent visible meeting or an already-open persisted record; not yet for an older result or a restart during unfinished intelligence.

## Acceptance challenges

1. Seed 101 meetings with a unique transcript token on the oldest. After a cold restart, search that token, open exactly that `meeting:<id>`, read its transcript and saved summary, then Back to the same archive context.
2. Leave a summary queued, close/restart, and reopen the persisted meeting. Assert the same run/job receipt says QUEUED, then the terminal ready or failed state appears without a duplicate run or false empty result.
3. Park a meeting with transcript, summary, and one artifact; restart; use PARKED and Restore; assert its id and related result remain and the record returns to Meetings.
4. Create two meetings with equal start times, refresh while changing a filter, and open one. Assert deterministic order, no stale row/detail cross-wiring, and the selected id—not title text—survives the return.

UNKNOWN: No tests, live Desk/API/database/provider/native walk, cold restart, visual capture, performance, accessibility, or owner acceptance. Existing test files are inspected assertions, not execution proof.

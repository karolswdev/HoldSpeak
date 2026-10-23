# calendar_record — adversarial review

workflow id: `calendar_record`  
job: Review calendar evidence and schedule a meeting recording  
baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd`  
reviewer task: `review_calendar_record`  
evidence class: source inspected and assertions inspected; no execution, provider/native walk, or owner observation.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job can start from an existing calendar feed/event or from a screenshot intake. In the latter, correct visible events and confirm a durable calendar projection; in either path, choose one occurrence, arm recording, survive refresh or
restart, start and stop the meeting, then find the saved meeting and useful
result again. The audit is too broad as one undifferentiated screen story. Keep
the snapshot review and scheduled/live capture as two bounded jobs, joined by
one event resource contract. The current guards are useful: source pruning and
linked-schedule R1/R2/R3 reconciliation exist (`holdspeak/calendar_ingest_conductor.py:298-346,573-735`), and cancellation is receipted
(`tests/unit/test_scheduled_recording_cancel.py:62-95`). They do not close the
snapshot handoff.

FINDINGS:

1. **P0 — mutable snapshot identity breaks convergence.** The review POST drops
the synthetic row id (`web/src/pages/cores/CalendarSnapshotReviewCore.tsx:128-157`),
then the snapshot UID hashes title, time, and location
(`holdspeak/services/calendar_snapshot_service.py:288-303`). Projection ids hash
that UID and the start (`holdspeak/calendar_ingest.py:412-416`); reconciliation
only follows a surviving UID (`holdspeak/calendar_ingest_conductor.py:651-735`).
On re-import into the same snapshot source, changing a title changes UID and can make the prior event look removed, cancelling an arm. That cancellation is receipted (`holdspeak/calendar_ingest_conductor.py:728-734`); whether the owner sees it promptly is unverified, and no live cancellation was observed. This fails Tenets 3
and 7; the cost is an unexpected cancelled recording after a cosmetic source edit. Persist a stable snapshot source
event/occurrence identity and derive the mutable ICS fields from it. Use the
existing source reconciliation, not a second registry. The stable-UID case is
already guarded by `tests/unit/test_event_linked_reconcile.py:216-246`.

2. **P1 — time and recurrence are inferred, not owned.** The face stores only
weekday and wall-clock strings (`CalendarSnapshotReviewCore.tsx:22-28,314-359`).
Confirmation stamps the host's local timezone (`holdspeak/services/calendar_snapshot_service.py:253-284`), emits UTC ICS, and the linked schedule separately chooses hub local time (`holdspeak/services/scheduled_recording_service.py:279-301`). A remote O365 calendar, a DST boundary, or a different hub can record the wrong instant. A screenshot supplies visible occurrences, not proof of an unseen recurring series. Bound snapshot intake to those occurrences; preserve recurrence/exception identity only when an actual calendar source provides it. The existing snapshot assertion explicitly locks host-local behavior (`tests/unit/test_calendar_snapshot_service.py:268-282`), while DST coverage is for manual cron (`tests/unit/test_times_dst_denver.py:23-54`). Store/display the applicable source zone and occurrence identity, convert once with `ZoneInfo`, and name ambiguous/missing wall-time refusals. Also validate numeric hours/minutes: the regex accepts `25:90` (`holdspeak/services/calendar_snapshot_service.py:77,174-177`) before unguarded datetime construction (`:262-274`). This fails Tenets 3 and 6.

3. **P1 — the fast path ends at “SAVED,” not at a recording result.** The done
state exposes only count/source label (`CalendarSnapshotReviewCore.tsx:210-232`).
The schedule form is a separate manual title/cron flow
(`web/src/desk/components/ScheduleCreateWindow.tsx:57-81,161-214`), while the
actual event arm lives in `ComingUp` (`web/src/pages/cores/history/ComingUp.tsx:116-173`).
The user must rediscover the event, and `record()` reports success regardless of
the void-returning start call (`ComingUp.tsx:116-119`). Backend failure receipts
and `did_not_record` exist (`holdspeak/services/scheduled_recording_service.py:172-206`),
but the review-to-meeting return is absent. This fails Tenets 3 and 7. After
confirm, hand off to the existing ComingUp/store contract, carry the stable event
id, and show armed, recording, refused, saved, and retry outcomes linked to the
same Meeting.

## Convergence

First consumers should be `meeting_record` (the live session and stop),
`meeting_archive` (same meeting after restart), and `meeting_intelligence` (a
useful result). Share event identity, `OP_OUTCOME`, persistence, and the existing
ComingUp/scheduled-recording store. Keep snapshot evidence review separate from
live capture: their permissions, recovery, and egress differ; merging them into
a wizard would increase cognitive load.

## User experience

The editable ledger, no-modal review, draft retention in the schedule form, and
named cancellation/failure states are good craft. Source inference says the
Tuesday owner still faces a context break: confirmation gives no next action,
timezone confidence, occurrence identity, or route to the resulting meeting.
No capture was inspected; beauty, accessibility, performance, and delight are
unknown.

CONDITIONS: Preserve the existing guards while adding stable identity and
explicit timezone and source-supported recurrence validation; connect confirmation to the existing
event-arm path; persist and surface the recording/meeting result through restart.

MISSED:

1. Highest cost: edited snapshot event cancels or loses an existing arm.
2. Wrong-zone/DST and recurring-series occurrence behavior.
3. Refused fire, retry-now, stop failure, and return to the same saved Meeting.

TUESDAY: Not yet—the owner can confirm evidence, but cannot follow one clear path to an armed recording and verified result.

## Acceptance challenges

1. Confirm one screenshot event, rename it, refresh, and verify one stable event and one still-armed schedule with the new title.
2. Import an event whose calendar zone differs from the hub and crosses DST; verify the displayed zone and fire instant match the source wall time.
3. For an existing calendar feed that actually supplies a recurring series, cancel one occurrence, refresh, and verify its cancellation and sibling identities. A screenshot-only intake must remain a declared set of visible occurrences, with no invented series.
4. Let a scheduled fire refuse for no microphone, use Record now, stop the successful meeting, restart, and verify the same calendar-linked Meeting and result are findable.

UNKNOWN: No tests ran; EventKit/sign-in, populated snapshot extraction, schedule firing, native audio, restart behavior, shots, and owner acceptance were not observed. Existing tests and source establish seams only; omission is not an observed product failure.

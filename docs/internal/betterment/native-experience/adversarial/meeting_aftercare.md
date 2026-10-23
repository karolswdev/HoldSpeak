# meeting_aftercare

Job: Review meeting outcomes and follow through on actions  
Baseline: `55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `/root/review_meeting_aftercare`  
Evidence class: source inspected; existing captures inspected (not owner acceptance); tests exist but were not run; no root execution or owner observation.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The brief names the read-only digest, prior-meeting comparison, provenance, triage, and proposal boundary. It is incomplete as an implementation brief: it does not state the active MeetingRecord/Needs recovery path or bind the wire shape to the commitment consumer.

FINDINGS:

1. **P1 — The consumer can discard the canonical aftercare action projection.** The API returns `open_items.by_owner[].items` with task, due, review state, and provenance (`docs/MEETING_AFTERCARE.md:54-61`; `holdspeak/meeting_aftercare.py:504-515`), while `useMeetingData` extracts only `action_items`, `actions`, or `items` (`web/src/pages/cores/history/useMeetingData.tsx:537-543`). `MeetingDetail` falls back to meeting-intelligence actions (`web/src/pages/cores/history/MeetingDetail.tsx:163-173`). Cost: a user can review a stale or differently identified commitment, bypassing aftercare owner/due/provenance state. This fails Tenets 3 and 6. Correction: define one typed projection, preserve durable action IDs and provenance, feed it to MeetingRecord, Needs, and refresh/confirm transitions, and add exact-wire-shape and stale-response cases. This is a source contradiction, not an observed production incident.

2. **P1 — durable return is not audited beyond the transient signal.** `AftercareNote` intentionally returns `null` instead of covering current work (`web/src/components/AmbientLayer.tsx:182-236`); the bell's meeting-specific READY route lasts six seconds before opening Needs (`web/src/desk/components/DeskChrome.tsx:43-73`). This does not prove outcomes disappear: Needs already groups durable arrival work by meeting (`web/src/desk/needs/NeedsDrawer.tsx:1120-1145,1219-1225`) and saved meetings remain reopenable. Cost: the audit has not proved that missed-event/restart users reach the same review through these existing doors. This fails Tenets 3 and 7. Correction: trace and verify the durable Needs/Meetings route, including an unread result with no pending actions. Extend that route only if a real gap remains; do not add another attention card, popup, or persistence registry merely because the transient host is empty.

3. **P2 — The egress boundary is not stated against the active surface.** The backend creates a GitHub issue proposal only for an accepted action (`holdspeak/services/meeting_aftercare_service.py:137-148`), with approval and policy checks separate (`holdspeak/services/meeting_aftercare_service.py:106-135`; `holdspeak/web/routes/meetings/aftercare.py:56-59`). Active MeetingDetail exposes prepared follow-up only when requested and a summary exists (`web/src/pages/cores/history/MeetingDetail.tsx:753-765`); no active caller for `file-issue` was found. Cost: completion, approval, destination, receipt, and unknown outcome are ambiguous. This fails Tenets 3 and 6 and Constitution Articles III and V. Correction: bound aftercare to read/triage/confirm, or name file-issue as separate send-commit flow with destination, approval, egress badge, and receipt states; otherwise mark it out of scope.

## Convergence

Converge `meeting_intelligence` (summary readiness and `aftercare_ready`) with incomplete-summary states; `decisions` with shared decision ID, provenance, review, and receipt; `today_followthrough` with durable action ID, owner, due, review/status, and Done/Later/Drop receipts; `meeting_archive` with restart/findability; and `source_context` with exact transcript links. `send_prepare`, `send_commit`, and `feedback` own destination, approval, egress, and indeterminate receipts. Do not merge aftercare into DecisionsView or Today/Needs: historical diff, durable lifecycle, and attention queue are different jobs. Share contract, state, and row grammar, not a new registry or wizard.

## User experience

The intended happy path is one meeting window: summary → Since last → decisions/commitments → exact source → confirm or Done → refreshed state; prepared follow-up is a separate approved egress. Existing captures (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/meeting-1440.png`, `meeting-393.png`) show compact summary, source-linked “Who owes what,” and prepared follow-up, but they are not owner acceptance. The `NO OWNER · NO DATE` state and transient bell identify assignment/recovery cases to verify, not proof that the durable work is lost. A Tuesday user must not re-enter context or infer whether “prepared” means sent.

CONDITIONS: Correct the canonical action projection and durable entry/return contract; explicitly bound external actions; then capture the acceptance challenges below. Keep all unknown execution, accessibility, performance, and owner-delight claims unknown until observed.

MISSED:

- High: no cross-window identity/recovery assertion for a missed `aftercare_ready` event.
- High: no assertion that current action rows retain review state and exact provenance through refresh.
- Medium: no active-surface proof for file-issue/send outcome and receipt.

TUESDAY: Not yet; the useful meeting view exists, but the mismatched action shape risks review fidelity, and return after a missed signal remains unproved.

## Acceptance challenges

1. A fresh meeting with one sourced decision and one sourced action opens from a cold desk; one meeting-scoped entry reaches MeetingRecord, source opens the exact segment, Confirm/Done updates Decisions, Needs, and the record without duplicates.
2. The owner misses the event, restarts, and returns after six seconds; the same meeting remains findable, with pending/accepted/unknown states intact and no generic-only fallback.
3. Adjacent meetings with the same people compare by the documented calendar/project/people rule; reworded actions are new, closed actions remain closed, and every link lands on the correct meeting.
4. Queued or failed summaries do not masquerade as an empty digest; Retry/Skip/Review remains honest and no send or issue proposal occurs before accepted data and approval.

UNKNOWN: No tests, live walk, provider operation, native build, or owner acceptance was performed; source-only review cannot certify rendered behavior, accessibility, performance, or delight.

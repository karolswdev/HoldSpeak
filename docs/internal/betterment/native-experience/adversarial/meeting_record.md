# meeting_record

Job: Record a live meeting and stop cleanly. Baseline: main55572802181d6a8045f6d27e3c722aaf5694dbbd (PR1430). Reviewer task: `review_meeting_record`. Evidence class: static source review, representative existing assertions, and two existing desk captures; no tests, builds, live Desk/API calls, provider/native actions, or owner acceptance.

VERDICT: DO-NOT-RATIFY

## Totality

The real job starts from Live, the Record orb, calendar context, or an open meeting; claims one recording identity; acquires mic/system/device streams; shows honest readiness and live feedback; accepts transcript/bookmarks; stops with bounded cleanup; seals audio and the Meeting; reports summary queued, unavailable, failed, or pending; returns to the saved Meeting; and finds that id after restart. The inventory keeps import, intelligence, and archive separate, but its gaps are too general to guide those handoffs. `docs/USE_CASES.md:22-32` is the boundary, not only the button press.

FINDINGS:

1. **P0 — capture stopped and result saved are not the same outcome.** `holdspeak/runtime/meeting_stop.py:112-154` catches persistence errors, emits a runtime error, and returns `status: stopped` plus `save_error`; the error is not wholly silent. The HTTP route broadcasts that payload but answers only `success: true` and an optional cleanup warning (`holdspeak/web/routes/meetings/live.py:80-88`). The store then clears capture state (`web/src/desk/store/recordingSlice.ts:135-170`). Owner cost: an HTTP consumer cannot distinguish a stopped capture from a fully saved result, and partial persistence/recovery is unbounded in the audit. This fails Tenets 3 and 7. Correction: retain the stopped truth and separately expose persisted/partial/failed status, meeting id, and recovery. Do not simply return an HTTP error that makes the existing store falsely say “STILL RECORDING.” Preserve the save failure in the final receipt.

2. **P1 — Hardware degradation is not an application fact.** The recorder falls back to mic-only when system capture cannot start (`holdspeak/meeting_recorder.py:385-418`); Live’s `audioOnly` fact is speech-model readiness, not stream availability (`web/src/pages/cores/LiveCore.tsx:282-285`). A child cleanup warning is optional (`holdspeak/web/routes/meetings/live.py:83-87`) and the direct Live stop path does not consume it (`web/src/pages/cores/LiveCore.tsx:286-325`). C10 tests prove bounded stop and journal recovery, not owner feedback. This fails Tenets 3 and 7. Correction: define mic, system, and child-cleanup states; show one receipt and recovery action while keeping record-only usable.

3. **P1 — Window identity is named but not carried through edits and stale events.** `LiveCore` accepts `meetingId` (`web/src/pages/cores/LiveCore.tsx:75-82`) but metadata saves call unscoped `/api/meeting` (`web/src/pages/cores/LiveCore.tsx:328-348`); the route resolves global `ctx.get_state()` (`holdspeak/web/routes/meetings/live.py:133-146`). The audit says focus ownership but not target binding, stale fencing, or two-window behavior. This fails Tenets 5, 6, and 7. Correction: bind stop/edit/return to meeting and window identity, or refuse stale doors; test no late update or focus steal.

4. **P1 — The audit stops before the result handoff.** Stop queues summary work after durable save (`holdspeak/runtime/meeting_stop.py:91-108`), and the face offers a saved-Meeting return (`web/src/pages/cores/LiveCore.tsx:672-683`), but the brief does not define the contract between `meeting_record`, `meeting_intelligence`, and `meeting_archive`. Owner cost: next action and result readiness remain guesswork. This fails Tenets 3 and 7. Correction: specify one meeting id, queue/running/finished/failed states, return target, and restart lookup; do not add a result surface.

## Convergence

Share `meeting_id`, capture status, `OP_OUTCOME`, runtime frames, receipts, and the Meeting window with `meeting_intelligence` (summary queue/result), `meeting_archive` (restart lookup), `meeting_import` (identity only), `calendar_record` (calendar outcome), `feedback` (pending/refused/partial), and `windows` (focus/restore). Keep file custody, long-running intelligence, and scheduling separate: one wizard would slow record/stop and blur authority. `speech_dictation` and `voice_commands` may share the mic floor, not the Meeting lifecycle.

## User experience

The existing [1440 Live capture](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-live-1440.png) and [393 Live capture](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-live-393.png) show a promising fast path: one Start verb, four visible steps, no modal, and a readable 393 layout. Source inference shows the shared Button and saved return. These are idle states only; they do not prove active recording, stop feedback, hardware truth, accessibility, performance, or delight. Corrections preserve the quiet face and add facts at existing receipt/Meeting seams.

CONDITIONS: Make the four contracts above explicit in the audit, name active source/tests for each, and add the acceptance challenges below. No new owner gate is implied.

MISSED:

1. Save failure versus recoverable journal, with exactly-once retry.
2. Mic-only/system-audio loss and child-cleanup feedback.
3. Summary queue state, saved identity, restart lookup, and return-to-task.
4. Two windows, stale frames, and meeting-target ownership.

TUESDAY: The idle entry is quick and familiar, but not yet—the owner cannot trust what Stop saved or what audio/result state comes next.

## Acceptance challenges

1. At 1440 and 393, start from Live and the Record orb, capture one segment, stop, and assert one meeting id, honest saved/partial receipt, return link, and no duplicate after restart.
2. Inject the hanging child seam; Stop meets its deadline, preserves accepted audio as recoverable, names degradation, and the next Record works.
3. Make `session.save()` fail. The face must say capture stopped but save failed/partial, retain recovery facts for the same id, and not falsely show STILL RECORDING; a supported retry cannot create a second Meeting.
4. Make system capture unavailable while mic capture works. The Meeting says mic-only before/after Stop; speech-not-set-up remains separate.
5. Open two Meeting windows, edit/stop one, and deliver a late frame. Only the bound meeting changes; the other keeps state and focus.

UNKNOWN: No tests were executed. No live Desk/API/provider/native walk, physical CoreAudio result, WebKit/assistive-technology behavior, performance measure, or owner acceptance was observed; captures are idle visual evidence only.

## Bounded repair — Stop and save facts, 2026-10-23

The Stop HTTP response now retains the runtime's capture, Meeting identity,
save and cleanup facts. Confirmed stopped capture remains a successful Stop
even when saving fails; clients must not retry Stop against an already-stopped
recording or claim that the Meeting was saved. Explicit still-recording
responses retain recording and the existing refusal. Missing legacy save
facts remain unknown.

The recording store and LiveCore use the same small outcome parser. A
DB-saved partial result retains the existing Meeting door and its warning.
Capture recovery is limited to the existing recoverable-checkpoint case with
retained JSON and a verified durable row; it does not repair a failed JSON
export or unrelated aftercare. Other persistence failures retain their actual
identity and refusal rather than offering a fake recovery success.

The actual MeetingWindow transition retains the global receipt after
LiveCore unmounts; clean Stop clears only its own matching verb/subject.
The native Stop test retains its loop-responsiveness assertions while
expecting the additional response facts, and generated API-consumer docs
now include the existing capture-recovery route's web callers.

Focused proof: 40 component/store/parser cases, two native Stop response
cases and nine route/integration
cases passed under the test lock with isolated HOME. Required quick passed the build, 4,187 related web cases, 40 affected
Python/browser cases, 110 sweep, 27 canon and 1,126 repository guards.
Root inspected the 393 Live and 1440 stopped-record captures. These are fixture observations, not
physical audio/device, complete persistence-recovery, or owner UX acceptance.
The broader identity/edit/summary handoff and capture-recovery findings in
this audit remain open.

[PR1437](https://github.com/karolswdev/HoldSpeak/pull/1437) records this bounded delivery.

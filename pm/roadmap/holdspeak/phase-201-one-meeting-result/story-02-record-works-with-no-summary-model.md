# HS-201-02 - Record works with no summary model

- **Project:** holdspeak
- **Phase:** 201
- **Status:** done
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** Astra (lane A)

## Problem

Recording is refused when the SUMMARY model is missing, because admission unconditionally requests live-analysis, bookmark-label and auto-title routes (`meeting_session/intel_admission.py:149`, `:292`), and Stop unconditionally hands off deferred analysis and auto-title (`meeting_session/session.py:686`, `intel_admission.py:467`). The refusal writes `record_only`, logs ERROR, and the desk shows a timer: 52 s of the walker's microphone were captured with no possible transcript (audits/face-walk-opus.md defects 3, 4; audits/runtime-astra.md fact 6). When it does surface, the face says "transcript is empty" while the truth is `no_assignment` (`services/meeting_intel_service.py:41` vs `intel_admission.py:211`).

## Scope

- **In:** with only `speech.transcribe` assigned, a meeting records AND transcribes; live-intel routes and the Stop handoff are requested only when intelligence is requested; a refusal that does happen is shown at record time as a token on the Record verb and names its real reason (`no_assignment`, in plain words); the speech-parent fencing stays.
- **Out:** the summary run itself (03, 05); the live recording room (parked, walk defect 5).

## Acceptance criteria

- [x] **A-proven:** Isolated HOME, speech assigned, no text model: Record then Stop yields a SAVED, non-empty transcript with final transcription and parent closure intact; no `admission refused` line in the hub log.
- [x] **A-proven:** With a text engine available, nothing is dispatched to it before the summary gesture (Stop queues no deferred analysis and no auto-title; fence on the queue and the binder, `intel_admission.py:467`, `meeting_deferred_queue_binding.py:69`), including for an untitled meeting.
- [x] **A-proven:** The dictation regression (`tests/unit/test_transcriber_init_race.py`) is classified a/b/c in this story's evidence because it shares the transcription seam; a (b) is fixed here.
- [x] **A-proven:** With no speech engine, the Record response and saved record carry the immediate `transcription_status_detail` refusal and its real reason.
- **Transferred to HS-201-01 (see status):** The Record verb renders that refusal token at the moment of refusal; shot at 1440.
- [x] **A-proven:** The wrong-cause message ("transcript is empty" for `no_assignment`) can no longer be produced; a fence test proves it fails pre-fix.
- [x] **A-proven:** The speech-only budget expectation in `test_meeting_transcription_children_join_the_existing_meeting_session` and the unassigned Stop expectation in `test_stop_aftercare_upserts_one_legacy_deferred_row_for_bundle_and_record_only` were updated to this posture. Other admission fences are unchanged and green.

## Test plan

- **Unit:** `tests/unit/` admission tests for the conditional routes and the reason threading; fence proven red without the fix.
- **Integration:** the e2e record-to-transcript run in an isolated HOME.
- **Manual / device:** the refusal token shot at 1440.

## Notes / open questions

Lane A (Astra to Luna). Serves exit criterion 2. The Record-verb refusal token is a FACE edit: lane A defines the read-model field, lane B (story 01) renders it. Do-not-touch for lane A: `web/src/desk/chair/*`.

## Lane delivery boundary

The owner assigned A the backend and B the token on the face. A completion
means the backend criteria above; the transferred face criterion stays owed by
HS-201-01. Evidence: `evidence-story-02.md`. The hard-coded speech-only Web
Record and parked Stop auto-enqueue are explicit amendments in the phase
status and peer check, not a claim that the old live-intelligence settings work.

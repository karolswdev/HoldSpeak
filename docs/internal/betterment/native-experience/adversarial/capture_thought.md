# capture_thought

Job: Get a thought down now and keep the saved note. Baseline: main55572802181d6a8045f6d27e3c722aaf5694dbbd (PR1430). Reviewer task: `review_capture_thought`. Evidence class: static source review, representative existing assertions, and optional desk captures; no tests, live Desk/API calls, provider/native actions, or owner acceptance.

VERDICT: DO-NOT-RATIFY

## Totality

The real job starts at Capture’s New note or Talk, accepts typed or spoken words, creates or reuses one Thought-backed Note, opens the workspace, keeps words through failure, lets the architect finish and close it, and makes the body findable after reopen. It includes setup/unavailable speech, an empty press, rapid repeat, interrupted write, conflict/offline retry, and return to the prior Desk task. `Record` is `meeting_record`; replay/learning is `speech_learning`. The inventory does not state these boundaries or the durable “saved” event.

FINDINGS:

1. **P0 — the audit names an inactive note seam.** Its only UI source is `NotePullout`, but `web/src/desk/components/Pullout.tsx:148-169,183-185` routes notes to `NoteWindowRouter` and `ThoughtWorkspaceWindow`; `NotePullout` is legacy code, not Capture evidence. The active handoff is `web/src/desk/chair/ChairHome.tsx:146-221`, `web/src/desk/newThought.ts:75-118`, and `web/src/desk/thought-workspace/ThoughtDocumentPane.tsx:55-90`. Owner cost: a worker can build on the wrong seam. This fails Tenets 2, 3, and 5. Correction: replace the source/tests with the active router, workspace, key handoff, writer, and `chair.app.test.tsx`; mark legacy code non-evidence.

2. **P0 — first words can be discarded on the only failure that matters.** Capture unmounts its field on the first character and starts `openNewThought(next)` (`web/src/desk/chair/ChairHome.tsx:198-220`). If creation fails, `open()` calls `stopThoughtKeys()` before reporting retry (`web/src/desk/newThought.ts:80-96`), dropping the retained seed (`web/src/desk/thoughtKeys.ts:55-64`). The refusal test covers an unseeded press, not seeded text (`web/src/desk/__tests__/thoughtDoorAndReceipt.test.tsx:138-155`). Owner cost: “capture now” loses the thought while offering Retry. This fails Tenets 3 and 7. Correction: persist the seed in the existing draft/receipt channel and replay it once against one creation identity; retain visible text until create succeeds.

3. **P1 — persistence and return are not one tested job.** The writer has durable-draft, save-failure, and conflict mechanics (`web/src/desk/pullouts/editors/useThoughtNoteWriter.ts:154-209,293-305`), and `Done` closes only after its guard (`web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:620-624`). The audit does not define the “saved” revision, prove reopen, or require return to Capture/previous work without stealing focus. This fails Tenets 3 and 7. Correction: specify durable id/revision, retry/conflict, close, and focus-return state.

## Convergence

Converge with `notes_editor` on the Thought workspace, writer, durable draft, revision/conflict, and `DeskEditor` insertion; first consumers are Capture’s New note/Talk handoff and the note window. Converge with `speech_dictation` on Talk setup/mic refusal, but keep Capture’s saved-note target distinct from Speak’s focused-app delivery. Converge with `native_input` on caret/IME/undo and `feedback` on write receipts. Do not merge one speech page: `meeting_record` owns long-lived audio and `speech_learning` owns journal correction/replay; shared vocabulary does not mean shared authority.

## User experience

The optional captures show a promising first surface: [Capture 1440](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/capture-1440.png) and [Capture 393](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/capture-393.png) show the same readable grammar, with Talk, New note, and Record at the top and no modal. This is a good Tuesday entry point. They show only idle Capture, not expanded New note, setup, failure, or saved result; the [note 1440](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/note-1440.png) and [note 393](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/note-393.png) shots show an ordinary populated note, not this journey. Evidence suggests discoverability, not persistence, accessibility, or audio quality.

CONDITIONS: Rebase the audit on active sources, retain seeded text across create/open failures, and specify durable revision plus close/focus return. No new owner gate is implied.

MISSED:

1. Seeded create refusal and retry without text loss (highest cost).
2. Active router/workspace versus legacy `NotePullout` evidence.
3. Offline/conflict, reopen after close, and return to prior work.
4. Talk setup/unavailable speech and rapid repeat without duplicate or merged notes.

TUESDAY: Not yet—the entry point is clear, but the audit cannot promise that a first thought survives the handoff and can be found again.

## Acceptance challenges

1. At 393 and 1440, press New note, press Escape without typing, then type a first character. Assert no empty POST, one Note/Thought identity, the complete phrase in the active workspace, Finish/Done, close, reopen, and the same body/title.
2. With speech ready, press Capture Talk and release one phrase; with speech unavailable, press it and use the in-place setup. Assert the ready path creates the same note contract, the setup path names its state, and no focused external app receives the phrase.
3. Refuse the seeded `/api/notes` create after the first character. Assert the text remains visible or retained with Retry, retrying creates one note, and no second press duplicates or concatenates it.
4. While the note is dirty, force offline then a revision conflict. Assert the exact draft remains, Retry/Reload is real, Done does not close before an authoritative save, and reopening after close restores the saved revision with the prior Desk task usable.

UNKNOWN: No test was executed. No live Desk/API/provider/native walk, physical microphone result, performance, IME/assistive-technology behavior, or owner acceptance was observed. Optional captures are external visual references only.

## Repair — failed-create words, 2026-10-23

The repair keeps the text of one New Note attempt outside the keyboard
interception lifetime. A refused create or pre-create flush releases keyboard
authority and retains the captured words for the existing Retry. Retry restores
that attempt once; another refusal retains them again. A create response with
no Note identity is a visible refusal instead of silent loss.

This extends the existing `thoughtKeys` handoff and `newThought` door. It does
not add another editor or draft store. The focused cases cover seed plus typing
while creation is pending, repeated failure, malformed response, timeout and
pointer handoff. The production route remains ThoughtWorkspaceWindow.

Focused proof: 34 cases across `thoughtDoorAndReceipt.test.tsx`,
`thoughtKeys.test.ts` and `chair.app.test.tsx` passed. Delayed successful
creation uses the same snapshot without rearming keyboard capture. These
component observations do not establish durability across reload or another
global failure receipt replacing this attempt's Retry. Required quick passed: build, 4,169 related web tests, five real-browser
key/window cases, 110 desk sweep, 27 canon and 1,126 repository guards.
Root inspected every-key captures at 1440 and 393. The repair PR records
delivery.
This does not settle the other Capture, editor, voice-targeting or appearance
findings in this audit.

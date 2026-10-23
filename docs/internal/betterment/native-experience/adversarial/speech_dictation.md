# speech_dictation

Job: Speak and see text land in the focused application.  Baseline: main55572802181d6a8045f6d27e3c722aaf5694dbbd (PR1430).  Reviewer task: `review_speech_dictation`.  Evidence class: source and representative assertions inspected; no tests, live Desk calls, provider actions, hardware walk, capture, or owner acceptance.

VERDICT: DO-NOT-RATIFY

## Totality

The real job is: focus an editor, hold Talk (or the physical hotkey), capture one utterance, transcribe and optionally rewrite it once, deliver it to the intended target, see an honest receipt, correct or retain the result, and return to the editor without losing caret, selection, draft, or microphone ownership. The audit is right that this is partial, but its evidence stops at `DictationCore` and `micSession`; it does not inspect the active `SpeakFace`/deck or the NoteEditor consumer named by its own gap (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:1808-1847`). That makes the proposed implementation boundary too vague to build safely.

FINDINGS:

1. **P0 — the Speak path lacks an explicit gesture-time focus target.** `useSpeakDeck` sends an async `/api/dictation/remote` call with `target_mode: focused` and no captured focus identity (`web/src/pages/cores/dictation/useSpeakDeck.ts:283-311`). Spoken text is already pipelined there; typed text may still need processing. The route calls the focused delivery hook later (`holdspeak/web/routes/dictation/pipeline.py:746-769`; `holdspeak/runtime/dictation_delivery.py:102-115`), and the desktop adapter binds focus at that invocation (`holdspeak/desktop_typing.py:79-105`). Source inspection therefore exposes a wrong-app risk if focus changes before binding, not an observed failure or proof about every hotkey path. This fails Tenet 7 (trust and control) and Tenet 3 (accelerate without recovery work). Correction: define one target binding at Talk release, fence late results against that generation, and return a named stale-target refusal with a retry/keep path.

2. **P0 — the audit generalizes a legacy append path into the active note contract.** `NoteEditor`'s MicButton appends (`web/src/desk/pullouts/editors/NoteEditor.tsx:171-183`), but ordinary note opens route through `NoteWindowRouter` into `ThoughtWorkspaceWindow` (`web/src/desk/components/Pullout.tsx:148-184`). Its active document pane already calls `DeskEditor.insertAtCursor` for voice and captured opening text (`web/src/desk/thought-workspace/ThoughtDocumentPane.tsx:55-89`). Owner cost: implementing a new adapter at the wrong seam or replacing working caret behavior. This fails Tenets 2/3/5. Correction: distinguish active workspace, retained inline-editor entry points, and legacy pullouts; preserve CodeMirror insertion/undo. Specify when voice binds the editor and selection, and prove late results, composition, unmount, and two supported editors instead of declaring caret insertion universally absent.

3. **P1 — the named tests prove pipeline mechanics, not the advertised job.** `test_dictation_pipeline.py` asserts stage order, fallback text, and warnings (`tests/unit/test_dictation_pipeline.py:72-154`); `test_dictation_cold_start_cap.py` proves runtime disablement and a second no-raise run (`tests/integration/test_dictation_cold_start_cap.py:55-135`). Neither proves microphone-to-transcript delivery, target identity, late-result fencing, or return to work. This fails Tenet 3. Correction: name focused-delivery, editor-selection, interruption, retry/idempotency, and return-to-task assertions in the audit.

## Convergence

Converge with `native_input` and `notes_editor` on the caret/selection insertion adapter, latest-writer fence, editor focus return, and undo contract; first consumers are the active `ThoughtDocumentPane`/`DeskEditor` and shared mic gadgets; inventory retained inline-editor paths separately. Converge with `speech_learning` on one run/journal identity, raw-versus-landed text, correction facts, and receipt, but keep replay/learning as a separate job. Converge with `voice_commands` and `meeting_record` only on the existing microphone floor and named refusal (`web/src/lib/micSession.ts:1-18,203-220`); command dispatch and long-lived meeting lifecycle must remain separate. `capture_thought` may share durable draft/receipt vocabulary, not its saved-note identity. Do not merge these into one speech page or runtime: a command effect, editor insertion, note capture, and meeting recording have different authority and recovery semantics.

## User experience

The active face is compact: Talk, an utterance well, “Types into,” result, and in-flow receipts (`web/src/pages/cores/dictation/SpeakFace.tsx:372-425`; `web/src/pages/cores/dictation/useSpeakDeck.ts:347-365`). That is a good Tuesday shape, and the tests preserve one pipeline and teach from the raw transcript (`web/src/pages/cores/dictation/__tests__/speakFaceTeach.test.tsx:380-465`). It cannot yet please a senior architect because “the app in front” names no app and is unsafe across an async boundary. No capture is present, so visual craft, 393/1440 density, accessibility, and microphone quality remain unknown.

CONDITIONS: Correct the active-editor evidence and add the target-generation and caret/selection timing contracts, their recovery semantics, and focused tests covering the complete job before this audit can guide implementation. No new owner gate is implied.

MISSED: (1) wrong-app delivery after focus changes; (2) selection/IME/undo insertion; (3) pending delivery or timeout with exactly-once retry; (4) open-mic/meeting interruption and return; (5) engine setup handoff preserving the utterance.

TUESDAY: Not yet: the face is compact, but an architect cannot know that a late result will land in the intended app or caret.

## Acceptance challenges

1. With editor A focused, release Talk, switch to editor B while transcription is pending, and resolve the response: A receives the text (or a named stale-target refusal); B never receives it, and the receipt identifies the outcome.
2. In the active Thought document, select text mid-document, speak, and resolve: the captured range is replaced once, IME composition is not corrupted, `⌘Z` restores the prior text, and focus returns to the editor.
3. Start open mic, start a meeting, and verify a named floor refusal; stop the meeting, speak again, and verify capture resumes without a second mic authority.
4. Force a timeout or pending delivery after transcription: the transcript remains editable/retained, retrying the same delivery id produces one terminal effect and one journal row, and setup-to-Engines return preserves the utterance.

UNKNOWN: No test was executed. Hardware microphone behavior, real focused-app delivery, end-to-end transcript quality, WebKit/assistive technology behavior, performance, and owner delight were not observed; the optional desk-sweep captures were not used as evidence.

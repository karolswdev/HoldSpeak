# voice_commands

Job: Say a phrase and run one configured Desk action.  Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430).  Reviewer task: `review_voice_commands`.  Evidence class: source, representative assertions, and viewed 1440/393 captures; no tests, live Desk calls, provider/native actions, or owner acceptance.

VERDICT: DO-NOT-RATIFY

## Totality

The real job is: open Speak, configure one exact phrase, say it once, match it without typing prose, run the allowed Desk operation once, show its result or named refusal, and return to prior work. It includes disabled/no-match dictation, setup failure, recording-floor conflict, repeated speech, disconnect, action failure, and retry without a second effect. The inventory is right to keep this partial, but its evidence stops at the registry and manifest (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:1884-1912`), not the active command path.

FINDINGS:

1. **P0 — the audit cannot guide the implementation it names.** The durable record lists only `verbRegistry.ts`, `applications.ts`, and `verbRegistry.test.ts` (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:1890-1902`). Active behavior is configured in `holdspeak/config/ui.py:34-40,122-168`, dispatched through `holdspeak/dictation_runner.py:61-75`, fenced/emitted by `holdspeak/web/routes/system/voice_stream.py:339-407`, and rendered by `web/src/pages/cores/dictation/SpeakFace.tsx:99-141,526-538`. Owner cost: a worker could build against a parked seam and miss the result/recovery contract. This fails Tenets 2, 3, 5, and 7. Correction: make these paths and `tests/integration/test_desk_speak.py:298-430`, `tests/unit/test_voice_command_dispatch.py:32-124`, and `web/src/pages/cores/__tests__/speakRoom.test.tsx:274-303` the evidence set; mark registry-only assertions as supporting evidence.

2. **P0 — two voice systems are conflated, so “same scoped target/availability” is not yet a bounded job.** Configured macros are whole-utterance exact-keyword matches and auto-fire because saved configuration is consent (`holdspeak/config/ui.py:122-130`; `holdspeak/dictation_runner.py:64-70`). Contextual proposals are a separate client grammar with confidence, selection, and explicit Confirm/Cancel (`web/src/desk/voice/grammar.ts:1-23`; `web/src/desk/components/MicButton.tsx:250-293`). Bound `voice_commands` to macros or specify a deliberate bridge; otherwise a worker may add a second command bus. This fails Tenets 1, 3, and 5. Correction: preserve the closed five-value `desk_verb` enum and the existing configured local action kinds (`open_url`, `launch_app`, `shell`, `type_text`, `holdspeak/config/ui.py:34-55`); cover their distinct previews, effects, and refusals. Document shared registry metadata (label, availability, outcome) versus why selection-aware proposals remain separate.

3. **P1 — preview and return are omitted from the acceptance contract.** The command board labels Desk-verb action as `Preview` (`web/src/pages/cores/CommandsCore.tsx:247-253`), and the API deliberately returns preview without firing it (`holdspeak/web/routes/system/voice.py:339-364`). Actual Speak firing opens the returned note/Today/Ask or reports a missing result (`web/src/pages/cores/dictation/SpeakFace.tsx:108-140`), but the named inventory test does not cover that UI contract. Owner cost: Tuesday setup can look verified while the first real phrase has no proved landing or return. This fails Tenets 3 and 7. Correction: distinguish “preview configuration” from “fire phrase,” assert one result receipt and focus/work return, and cover `new note`, `ask`, `open today`, and a missing/failed operation.

## Convergence

Converge with `speech_dictation` on one microphone session, no-match dictation, named refusal, and disconnect recovery; with `meeting_record` on the audio-floor ownership and `record`/`stop` operation boundary; with `navigation_commands` and `feedback` on registry labels, availability, and receipts; with `windows` on opening the returned app without stealing unrelated focus. First consumers are Speak and the existing Commands board. Keep `native_input`/`notes_editor`’s selection-aware proposal flow separate from exact configured macros, and keep `capture_thought`’s saved-note identity separate from `new_note`’s command result. Do not merge all voice into one runtime: the existing close-and-guard boundary is valuable.

## User experience

The viewed command-board captures show a clear five-row setup with visible phrase, outcome, Preview/Edit/Delete, and a 393 layout that remains usable (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-dictation@commands-1440-Voice_commands.png`; `/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-dictation@commands-393-Voice_commands.png`). That is a good Tuesday starting point for an architect. It does not show speech, fired state, refusal, or return; source suggests honest receipts, but cannot certify beauty, accessibility, latency, or owner delight.

CONDITIONS: Expand active source/test evidence; choose and bound macro-versus-proposal convergence; specify exact-once fire, result/receipt, interruption, retry, and return semantics.

MISSED:

1. Recording-floor conflict and stop recovery.
2. Browser disconnect or transcription failure without a late action.
3. `new note`/Ask/Today result identity and focus return.
4. Configured local action kinds beyond the five default Desk verbs, duplicate keywords, repeated speech, and disabled/no-match behavior.

TUESDAY: The setup is easy to discover, but the audit cannot yet promise that one spoken phrase lands once and returns the architect to work.

## Acceptance challenges

1. With default macros enabled, say “start recording”: one meeting starts, the final frame contains the operation result, no prose is delivered, and the next “stop recording” reaches that same meeting; then a second Stop names the refusal.
2. Say “new note” and “open today” from an open unrelated window. Assert the returned identity/window opens once, the receipt names it, and the prior window remains recoverable; a missing create result is a named refusal.
3. Disable commands and say a configured phrase: it remains ordinary dictation. Say an unconfigured phrase: no command fires. Repeat a phrase with punctuation: at most one effect.
4. Disconnect or lose the microphone floor during transcription. Assert no late command fires; after the meeting stops, a fresh utterance can run, with a named retry/refusal rather than duplicated work.

5. Configure a supported local action in an isolated fixture: its preview names the exact saved payload, the preview endpoint follows its documented effect policy, and real speech produces an honest outcome/refusal for that action kind. Default Desk verbs are not the entire configured-macro product.

UNKNOWN: No tests were executed. Physical speech recognition, hotkey and native paths, browser/assistive-technology behavior, performance, provider failures beyond source assertions, and owner acceptance were not observed; captures are visual references only.

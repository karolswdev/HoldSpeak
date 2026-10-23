# native_input

Job: Edit text with keyboard, IME, voice and undo semantics intact. Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430). Reviewer task: `review_native_input`. Evidence class: source inspection, representative assertions, and optional 1440/393 captures; no tests, live Desk/API calls, provider/native actions, or owner acceptance.

VERDICT: DO-NOT-RATIFY

## Totality

The real job is to enter or revise text, keep the intended window/control and caret or selection, survive IME composition and asynchronous voice completion, see a named failure or retained draft, undo the insertion or applied change, and return to the same work. It includes typed editing, field-fill voice, selection-aware editor voice, late results after rerender/unmount, and save refusal.

The inventory is too broad about “shared inputs” and too narrow about active consumers. Ordinary note opens route through `NoteWindowRouter` to the Thought workspace; the legacy form editor is explicitly no longer reached (`web/src/desk/components/Pullout.tsx:148-184`). The active pane already inserts at CodeMirror’s selection (`web/src/desk/thought-workspace/ThoughtDocumentPane.tsx:55-90`), while the retained inline `NoteEditor` appends voice to `f.body` (`web/src/desk/pullouts/editors/NoteEditor.tsx:171-183`). The audit must distinguish those paths before prescribing one missing adapter.

FINDINGS:

1. **P0 — active and legacy editor contracts are conflated.** `DeskEditor` already has selection-aware `insertAtCursor` and CodeMirror history (`web/src/desk/components/DeskEditor.tsx:15-20,209-220,244-290`), and the active Thought pane uses it. Treating caret insertion as absent risks replacing a working seam; treating the legacy append path as universal loses a selection. Owner cost is a worker implementing the wrong target. This fails Tenets 3, 5, and 7. Correction: split active Thought insertion, retained inline-editor behavior, and field-fill semantics; name each first consumer and target-binding rule.

2. **P0 — field semantics and recovery are unspecified across the named surfaces.** `StringGadget` voice replaces the controlled value (`web/src/desk/surface/gadgets.tsx:321-347`), `PadGadget` appends with a space (`web/src/desk/surface/gadgets.tsx:413-467`), Ask uses a separate mic that appends to its Pad (`web/src/desk/components/AskPanel.tsx:937-1000`), and retained `ThreadComposer` does the same (`web/src/desk/components/ThreadComposer.tsx:990-993,1131-1160`). Settings fields have a queued write/retry contract, not a freeform document (`web/src/pages/cores/SettingsCore.tsx:1304-1315`). A universal caret adapter would be wrong for replacement fields, secrets, search, and command drafts. This fails Tenets 1, 3, and 5. Correction: define `replace`, `append`, and selection/caret policies; retain Settings retry and Ask/Thread snapshot boundaries.

3. **P1 — guards exist, but the advertised cross-consumer proof does not.** The keymap and composers respect composing events (`web/src/desk/keymap.ts:133-160`; `web/src/desk/components/AskPanel.tsx:997-1000`), MicButton fences capture generations and late stops (`web/src/desk/components/MicButton.tsx:202-220,414-456`), and Pad tests cover a late writer (`web/src/desk/surface/gadgets.test.tsx:397-420`). DeskEditor tests cover selection and focus, not voice-to-selection or undo (`web/src/desk/components/DeskEditor.test.tsx:21-79`). This is an evidence gap, not proof of a universal defect. Correction: require focused assertions for IME composition, mid-selection voice replacement, late completion after window change/unmount, native undo, retained failure, and focus return.

## Convergence

Converge with `notes_editor` on CodeMirror selection/history and the Thought writer; with `speech_dictation` on MicButton generation, target binding, refusal, and focus return; with `capture_thought` on `thoughtKeys` and note identity; with `ask_whole_desk` and `threads` on durable draft, autocomplete, and snapshot. Keep Settings’ field/revision contract separate: document, form, and conversation lifecycles differ. Reuse `DeskEditor`, `StringGadget`/`PadGadget`, `MicButton`, `durableDraft`, and existing receipts.

## User experience

The optional note captures show a readable saved-note face at 1440 and 393, while Settings 393 shows a compact stacked form with mic affordance ([note-1440.png](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/note-1440.png), [note-393.png](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/note-393.png), [surface-settings-393.png](/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-settings-393.png)). They show idle/read states, not caret, IME, voice, undo, refusal, or return. Simple typing looks promising; interrupted voice editing is unproven.

CONDITIONS: Re-scope by active consumer and insertion policy; record the existing caret/IME/focus/undo guards; add the cross-consumer acceptance assertions above. No new owner gate is implied.

MISSED:

1. Wrong-field or wrong-window landing after a late voice result (highest cost).
2. Active Thought workspace versus legacy NoteEditor routing.
3. Undo/history behavior after programmatic voice or AI replacement.
4. Ask/Thread autocomplete and durable draft recovery while capture is pending.

TUESDAY: Not yet—the shell is familiar, but the audit cannot promise that voice or recovery preserves the architect’s actual caret and draft.

## Acceptance challenges

1. In the active Thought workspace, select text mid-document, compose with IME, then resolve one voice result. The selected range is replaced once, composition is intact, `⌘Z` restores the prior text, and focus remains in the editor.
2. In Ask, type a prefix, move the caret, capture speech, then edit a follow-up while capture settles. The declared field policy is followed, no duplicate text appears, submit snapshots the intended prompt, and the later draft remains.
3. Start voice in one editor, switch windows or unmount it before completion, and resolve the result. Only the bound target changes, or a named stale/retained outcome is shown; another field never changes.
4. In Settings, edit a named text field, speak, force a refused save, and retry. The field’s replacement semantics and native undo remain usable, the changed value stays visible, and focus returns to the originating control.

UNKNOWN: No tests were executed. No live IME, hardware microphone, voice-quality, assistive-technology, WebKit, performance, cross-window, provider/native, or owner-acceptance evidence was established in this review; the captures are idle visual references only, and baseline anchors may drift.

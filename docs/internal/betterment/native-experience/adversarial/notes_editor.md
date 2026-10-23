# notes_editor — Write, edit and develop a note without losing text

Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_notes_editor`  
Evidence class: source inspection, representative assertions, and prior desk captures; no execution.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The real job starts in Capture (`New note` or `Talk`), Desk `New Note`/`Ctrl-T`, or an existing note. `openNewThought` retains keys typed before the window exists, reuses an empty Thought, and opens one note pullout (`web/src/desk/newThought.ts:46-119`; `web/src/desk/chair/ChairHome.tsx:146-220`). The active router calls `openNoteThought` and renders `ThoughtWorkspaceWindow`, not the ordinary `NotePullout` or its form editor (`web/src/desk/components/Pullout.tsx:148-169`; `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:599-665`). CodeMirror owns typing, IME, selection and undo; the microphone inserts at the current caret; the writer retains drafts, fences conflicts, and flushes before Done/close (`web/src/desk/thought-workspace/ThoughtDocumentPane.tsx:44-90`; `web/src/desk/components/DeskEditor.tsx:209-219,244-340`; `web/src/desk/pullouts/editors/useThoughtNoteWriter.ts:154-208,293-305`). Ask-about-selection, Add to note, refinement, finish/resume, reload and return are part of this note identity.

The audit does not trace this active path. `NoteEditor` appends voice to `f.body` (`web/src/desk/pullouts/editors/NoteEditor.tsx:171-183`), but note `openEditor` redirects to the sticky (`web/src/desk/store/deskSlice.ts:109-120`); `NoteEditor` and compact `ThoughtNoteEditor` are retained/legacy consumers, not proof that the active window lacks caret insertion.

FINDINGS:

1. **P1 — Active/retained boundary is missing.** Evidence: `web/src/desk/components/Pullout.tsx:148-169`; `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:599-665`. The audit names only `NoteEditor` and `ThoughtNoteEditor` and calls their append behavior the family gap, omitting the active router, workspace, capture handoff, and `thoughtKeys`. Cost: implementers may “fix” dead code or add a second editor path, failing Tenet 3 (accelerate) and Tenet 6 (Workbench-native coherence). Correction: make the active route primary, mark retained paths, and state which note identities reach each consumer.
2. **P1 — The caret finding is too broad, not wholly false.** Evidence: `web/src/desk/thought-workspace/ThoughtDocumentPane.tsx:55-90`; `web/src/desk/components/DeskEditor.tsx:209-219`; `web/src/desk/pullouts/editors/NoteEditor.tsx:171-183`. The active path already has `insertAtCursor` and a field-owned `MicButton`; the retained generic editor still appends. Cost: a blanket shared-runtime rewrite risks IME/undo regressions and violates Tenet 5 (component framework). Correction: specify one small insertion contract (target identity, captured range, late result, undo) and name `ThoughtDocumentPane` as first consumer; decide whether retained `NoteEditor` remains reachable before changing it.
3. **P2 — Whole-job recovery and return are under-described.** Existing assertions cover conflict/reload and failed-save retry (`web/src/desk/thought-workspace/ThoughtWorkspaceWindow.test.tsx:351-383`) and the note app covers open/Done/Add-to-note (`web/src/desk/pullouts/__tests__/note.app.test.tsx:85-103,126-148`), but the audit does not connect these to capture, close/reopen, completed Thought resume, or an external append while dirty. Cost: Tuesday confidence and craft remain unproved (Tenet 7). Correction: add falsifiable transitions below and preserve the current writer/close guards.

## Convergence

Converge with `native_input` on `DeskEditor` selection/IME/undo and with `speech_dictation` on MicButton authority, target capture and late-result handling. Converge with `capture_thought` on `openNewThought`, `thoughtKeys`, empty-Thought reuse and one note identity; keep Capture as the fast entry face. Converge with `ask_whole_desk` and `source_context` on selected-passage handoff and Add-to-note through the existing writer; keep Ask request identity separate. `voice_commands` covers configured macros; selection-aware MicButton proposals are a distinct path, not body insertion. Do not merge capture, note editing, and command speech: their triggers, recovery and authority differ.

## User experience

Prior captures under `/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/` show a credible path: `note-1440.png` and `note-393.png` show one quiet note window, a visible mic, and a short footer; `capture-1440.png` and `capture-393.png` show three discoverable Capture verbs. Likely pleasing at 393 where the note owns the work area. Captures show appearance only, not caret placement, voice delivery, IME, interruption, or save recovery; no owner-delight claim follows.

CONDITIONS:

1. Rewrite the audit around the active router and label legacy consumers.
2. Narrow the caret gap to a contract and reachable consumers, retaining existing CodeMirror and guards.
3. Include the scenarios below with focused assertions or live evidence in the implementation brief.

MISSED:

1. **High:** active editor IME + voice-at-caret + undo sequence.
2. **High:** dirty note versus Ask Add-to-note, conflict/reload, close/reopen and focus return.
3. **Medium:** Capture first-character creation, duplicate presses, empty reuse, and completed-Thought resume.

TUESDAY: The route is promising and visually compact, but the audit is not yet a safe implementation brief until it tells the worker which editor is real and proves the no-loss return path.

## Acceptance challenges

1. From Capture, press New note, type immediately, and press it again: exactly one note opens, all words remain, and the title follows the saved note.
2. In an active note, place the caret between two words, speak text, compose one IME phrase, and undo: each insertion lands at the owned caret and undo removes only the latest edit.
3. Edit, refuse/offline the save, close or press Done, then reopen and Retry: the draft remains, no close claims success early, and a later authoritative save clears the retained copy.
4. With a clean note, Add to note from Ask reloads the append; with a dirty note, it does not overwrite local words and exposes the existing changed-elsewhere recovery before return.

UNKNOWN: No tests were run, no new live walk or owner acceptance occurred, and no hardware IME/microphone, assistive-technology, timing, or native-provider behavior was observed. The captures are prior artifacts, not this review’s execution.

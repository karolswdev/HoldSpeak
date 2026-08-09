# HS-129-07 — The speakable desk

- **Project:** holdspeak
- **Phase:** 129
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-129-11
- **Owner:** unassigned

## The thesis (the bar)

Article IV.1: every text input can be spoken into. Audit C's census found
the voice-first product has unspeakable fields in eight rooms. Closing the
census also retires the bare-input dialect: the fields adopt `StringGadget`
(web/src/desk/surface/gadgets.tsx:215-265) or carry a `MicButton` in the
established adjacent position.

### What changes

Wire speak-to-fill (and shared control skin where the field is bare):

1. WorkflowEditor — all four inputs (Name/Tone/keyword/prompt),
   editors/WorkflowEditor.tsx:48-97.
2. NoteEditor — title + tags (title bare at :134-138, tags at :156-160);
   the body mic stays.
3. KbEditor — body (`DeskEditor`) gains its mic; name keeps its own;
   name input adopts StringGadget (:129-163).
4. ReceiptsView search (views/ReceiptsView.tsx:154-163) — StringGadget +
   mic.
5. RepoWindow commit message (:200) — mic; checkbox/select/input adopt the
   shared control skin (audit C §2, D §5).
6. SessionPullout compose + rename (:464, :623) — mics.
7. DeskComposer textarea + input (:34, :42) — mics.

Compliant rooms (Ask, ProjectMemory, PersonaChat, Workbench inlet, Live,
CapabilitySection, Coder reply, DeliveryTerminal) are untouched.

## Acceptance criteria

1. A census test enumerates rendered text inputs/textareas across the
   audited tree and asserts each has an associated mic affordance
   (allowlist: non-text controls only).
2. Each wired mic actually appends/fills its field's value (unit-level
   `onText` assertions).
3. No bare `<input>`/`<textarea>` remains in the seven touched rooms —
   shared gadget or skinned variant only.

## Test plan

- Web: the mic census test + per-editor onText tests; existing editor
  suites green; typecheck.
- Walk: one shot per touched room showing the mic seated in the field row
  at 1440; ReceiptsView also at 393.

# HS-176-05 — The desk answering the hand

- **Project:** holdspeak
- **Phase:** 176
- **Status:** done
- **Depends on:** HS-176-02, HS-176-03, HS-176-04
- **Unblocks:** HS-176-06
- **Owner:** unassigned

## Problem

The arc says "the desk answering the hand": the dictation pipeline
should respond to the owner's hand as a loop, not a one-shot. Today
the pipeline runs once per utterance: speak → land. The correction
(story 02) adds teach → apply, and the journal (story 03) adds the
visible stream. This story integrates them: the full loop from speak →
see it land → judge it → teach it → see the teaching applied, visible
in one session on the Speak window. The desk does not just type; it
learns.

## Scope

- In:
  - The Speak face shows the full loop in one session: the owner
    speaks, the text lands (the utterance well on SpeakFace.tsx; the
    170 UtteranceWell component is an orphan parked by story 04), he
    judges (`OK` / `Wrong`), he teaches (the teach row from story 02),
    `Review` re-pointed at the Journal wing,
    he speaks again and the correction fires (the correction chip on
    the new row), the journal shows both utterances with the
    correction applied on the second.
  - The learning digest updates live: after the correction fires, the
    digest section shows the updated reach count without refresh.
  - The correction chip links back to the correction: tapping it
    shows which correction fired and why (the similarity score, the
    key → value).
  - No restart required: the correction is applied within the same
    hub session (the CorrectionStore is warm; the pipeline reads from
    it on every run).
- Out:
  - Multi-step correction chaining (one correction per utterance is
    sufficient for this phase).
  - Correction undo (the correction is removable via the Speak face
    or DELETE API; this story does not add a one-tap undo).
  - Model-generated correction suggestions.

## Acceptance criteria

- [ ] The full loop works in one Speak session: speak → land → judge →
      teach → speak again → correction fires → journal shows the chain
      (Article IX.1).
- [ ] The learning digest updates live after the correction fires
      (no page refresh; the WebSocket bus pushes the update).
- [ ] The correction chip on the utterance row links back to the
      correction detail (key, value, similarity score).
- [ ] No hub restart is required between teaching and applying the
      correction.
- [ ] Zero egress (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k desk_answering`
  - The pipeline reads from CorrectionStore on every run (no
    restart required to pick up a new correction).
  - The learning digest updates after a correction fires.
- Integration: the rig boots a hub, teaches a correction via POST,
  runs a matching utterance, asserts the correction fired and the
  learning digest updated.
- Manual: the owner performs the full loop on the Speak face in one
  session; the correction fires; the journal shows the chain.

## Notes / open questions

- The WebSocket bus frame for learning digest updates: propose reusing
  the `dictation.journal.entry` frame (story 03) with a
  `learning_digest` field appended, or a separate
  `dictation.learning.update` frame. Decided at build time.

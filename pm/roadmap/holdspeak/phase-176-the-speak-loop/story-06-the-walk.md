# HS-176-06 — The walk

- **Project:** holdspeak
- **Phase:** 176
- **Status:** backlog
- **Depends on:** HS-176-05
- **Unblocks:** HS-176-07
- **Owner:** unassigned

## Problem

The owner's attended walk on his desk is the exit gate (Article IX.4).
The Speak Loop introduces new behavior (corrections, the journal
stream, MicButton everywhere, the full loop) that must be proven on
his real desk with a real mic. The walk is the proof that dictation is
a daily tool.

## Scope

- In:
  - The owner's attended walk on his desk, both widths (1440 + 393).
  - The walk covers:
    1. He dictates a sentence; it lands correctly.
    2. He dictates a sentence with a word the pipeline gets wrong; he
       taps the utterance and teaches a correction.
    3. He dictates a matching sentence; the correction fires; the
       corrected text lands.
    4. The journal shows all three utterances as a stream; the
       correction chip is on the third row.
    5. The learning digest reads > 0 corrections, > 0 reach.
    6. He opens a surface outside Speak (e.g. a Note editor); the
       text input has MicButton; he dictates into it.
    7. He returns to the Speak window; the journal shows the Note
       utterance with source "browser."
  - The stopwatch per face (Article IX.2).
  - His verdict (Article IX.4).
- Out:
  - Automated rig legs (those are in stories 02-05).
  - Linux walk.

## Acceptance criteria

- [ ] The owner walks all seven beats on his real desk (Article IX.1,
      IX.4).
- [ ] A correction is taught and applied on a matching sentence.
- [ ] The journal shows all utterances as a live stream with source
      and correction chips.
- [ ] The learning digest reads > 0 (Article VI.1).
- [ ] MicButton works on a non-Speak surface.
- [ ] Both widths (1440 + 393) are walked.
- [ ] His word.

## Test plan

- Unit: n/a (walk story).
- Integration: n/a.
- Manual: the seven-beat walk on his desk; screenshots at both widths;
  the stopwatch per face; his verdict recorded verbatim.

## Notes / open questions

- The walk depends on a working mic on the owner's machine. The walk
  runner must be run from his desk (not CI).

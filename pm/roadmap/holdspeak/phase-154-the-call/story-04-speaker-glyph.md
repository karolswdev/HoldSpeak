# HS-154-04 - The speaker glyph and auto-speak (S6 chunks, barge-in)

- **Project:** holdspeak
- **Phase:** 154
- **Status:** backlog
- **Depends on:** HS-154-01, HS-154-03
- **Unblocks:** HS-154-05
- **Owner:** unassigned

## Problem

The voice must feel live: speech starts before the turn ends (counsel
S6), every assistant turn is replayable, and the owner interrupting
always wins (settled design D4).

## Scope

- **In:** a speaker glyph on every assistant message (replay via the
  D1 seam; active state while speaking; click stops). In call mode,
  auto-speak feeds sentence boundaries from the streaming deltas into
  `enqueueSentence` as they arrive (S6) — not on `turn_done`. Barge-in:
  a detected utterance start (02) or any click on the chip/glyph stops
  TTS immediately and the loop returns to LISTENING. Sensitive-part
  text is spoken locally exactly as rendered — the browser voice is
  local and the server path is the hub; no new egress.
- **Out:** per-voice settings beyond the existing voice pick.

## Acceptance criteria

- [ ] vitest: streaming deltas produce sentence-boundary enqueues before turn_done; barge-in calls `stop()` and no further enqueues fire for that turn; the glyph replays a finished turn and shows the speaking state.
- [ ] Auto-speak only in call mode; glyph replay works with the call OFF.
- [ ] Glass 1440 + 393: the glyph on assistant rows, speaking state visible, zero overflow.

## Test plan

- **Unit:** vitest `speakerGlyph.test.tsx` + `autoSpeak.test.ts`.
- **Integration:** glass leg `speak`.
- **Manual / device:** story 05 (the audible leg is attended).

## Notes / open questions

- Sentence boundary = delta text split on `.!?` with a length floor; do not over-engineer.

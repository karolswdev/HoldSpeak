# HS-154-04 - The speaker glyph and auto-speak (S6 chunks, barge-in)

- **Project:** holdspeak
- **Phase:** 154
- **Status:** done
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

## What shipped

- **autoSpeak.ts** (`web/src/desk/autoSpeak.ts`): the streaming auto-speak
  module. Accumulates text deltas, splits at sentence boundaries (`.!?`
  plus a 20-char length floor), feeds each completed sentence to
  `enqueueSentence` BEFORE `turn_done`. Tail flushed at `turn_done`.
  Call-mode gate (no-op when OFF). Barge-in: `bargeIn()` stops TTS and
  blocks further enqueues for the barged turn. Tracks auto-spoken turn
  IDs (prevents double-speak). Tracks active speaker ID for glyph
  highlighting.

- **SpeakerGlyph.tsx** (`web/src/desk/components/SpeakerGlyph.tsx`): a
  button on every finished assistant message row. Click replays the
  message text via `speak()`. Active/speaking visual state when this
  message is being spoken (highlight + stop symbol). Click while
  speaking stops. Works with call OFF (replay is always available).
  Desk tokens; focusable; Enter/Space toggles. No modals; no prose.

- **ThreadPullout.tsx** wired: delta bus handler feeds `autoSpeakFeedDelta`
  (text-kind only, not reasoning); turn_done handler calls
  `autoSpeakFlushTurn`; `callMode` effect syncs
  `autoSpeakSetCallActive`.

- **CallChip.tsx** wired: click handler calls `autoSpeakBargeIn()`
  (replaces bare `ttsStop()`); `wireCallLoop` now passes
  `onStateChange` callback that triggers `autoSpeakBargeIn()` when
  the loop transitions to `"transcribing"` (owner started talking).

- **thread-pullout.css**: `.thread-speaker-glyph` / `--active` styles
  matching the desk token vocabulary (20px, 2px radius, border-subtle,
  warning-signal active state).

- **Tests:**
  - `autoSpeak.test.ts` (21 tests): sentence boundary splitting, delta
    enqueue timing, barge-in blocking, call-mode gate, replay, TTS
    state listener.
  - `speakerGlyph.test.tsx` (11 tests): render, click replay, speaking
    state, stop on re-click, keyboard reachable, aria-label.
  - `callChip.test.tsx` updated (11 tests): barge-in assertions.
  - `test_hs154_call_glass.py::test_speaker_glyph_glass`: glyph renders
    on assistant rows at 1440+393, click invokes browser TTS (page-level
    speechSynthesis stub), data-speaking flips true/false, zero overflow.

- **Defects found and fixed:**
  - _Defensive glass leg (bounced):_ the initial glass test had no fake
    engine seeded in the hub fixture, so on the glass hub (no model) the
    assistant never responded, zero glyphs rendered, and every meaningful
    assertion hid behind `if glyph_count > 0:` -- the same pattern
    bounced in 153-04. Fixed: added `_TextEngine` fake engine to the
    shared hub fixture (copied from test_hs153_practice_glass.py),
    wired it via `broker.inference_runner._engine_factory`, added
    `chat.turn`-scoped assignment to `_seed_profile`. The leg now
    asserts without conditionals: `expect(first_glyph).to_be_visible()`,
    `data-speaking == "false"`, click -> `data-speaking == "true"` +
    `_ttsUtterances` non-empty, click again -> stopped.
  - _speechSynthesis stub silently ignored:_ headless Chromium defines
    the native `speechSynthesis` as a non-writable property;
    `window.speechSynthesis = {...}` silently failed. Fixed with
    `Object.defineProperty(window, 'speechSynthesis', {...})`.
  - _replayMessage ordering bug:_ `activeSpeakerId` was set BEFORE
    `speak()`, but `speak()` internally calls `stop()` synchronously,
    which fires the idle listener that clears `activeSpeakerId`. Fixed
    by setting `activeSpeakerId` AFTER `speak()` returns.

## Notes / open questions

- Sentence boundary = delta text split on `.!?` with a length floor; do not over-engineer.

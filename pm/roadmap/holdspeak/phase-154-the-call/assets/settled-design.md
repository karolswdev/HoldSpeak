# Phase 154 settled design — The Call (DC-04)

Ruled by the orchestrator 2026-08-30 from the holistic counsel
design-beat (Phase 152 `assets/counsel-design-beat.md`: RATIFY-W-C;
M9, S6, R4), RFC §6.8, and the orchestrator's TTS feasibility ruling
(HANDOVER §Phase-154 — it SUPERSEDES RFC §6.8's "recommend B
server-side Python kokoro": PyTorch `kokoro` needs Python <3.13, we run
3.13; `kokoro-onnx` works but its `phonemizer`+espeak-ng chain is
GPL-3.0). Builders implement. Charter commit lands on PR #511
(`feat/deskos-platform-revolution`), the superseding merge vehicle.

## The one sentence

The Thread learns to talk and to listen: a voice for every assistant
turn (zero-egress by default), the existing ear wired into a hands-free
loop, and one visible call state on the thread head that the owner can
always stop with a click.

## D1 — the voice (story 01)

- Default TTS = the **browser Web Speech API** (`speechSynthesis`):
  zero deps, zero egress, instant, no licence exposure. One client
  seam `web/src/lib/tts.ts` — `speak(text, opts)`, `stop()`, sentence
  queue — every caller goes through it.
- Optional extra `holdspeak[tts]` = **kokoro-onnx** server-side:
  `POST /api/tts` streams WAV chunks; a visible GPL note (phonemizer +
  espeak-ng are GPL-3.0) in Settings where the extra is enabled; the
  weights download is egress-badged and receipted, reusing the Model
  Library download/receipt pattern (`holdspeak/web/routes/model_library.py:83`).
  When the extra is absent the route answers 404 and the client seam
  stays on the browser voice — no dead UI.
- S6: the sentence-chunk streaming contract — the client seam accepts
  text incrementally (sentence boundaries), so speech starts before the
  turn ends. R4 (recorded): if server TTS first-chunk exceeds 2 s the
  seam falls back to the browser voice for that utterance.

## D2 — the ear (story 02)

- Reuse the EXISTING energy VAD: `web/src/lib/vad.ts` → `micSession.ts`
  → `POST /api/dictation/transcribe` (Silero later — recorded). No new
  audio stack.
- The hands-free loop: while the call is LISTENING, endpoint detection
  closes the utterance, the existing transcribe path yields text, and
  the text is sent as a normal turn through the SAME `start_turn` path
  (admission, palette, guardrails — nothing bypassed). The egress badge
  stays per turn.

## D3 — call mode (story 03) — M9

- Additive `threads.call_mode INTEGER NOT NULL DEFAULT 0`; the generic
  reconcile carries it to existing DBs (prove against the pre-change
  DDL, the 153 pattern).
- Toggle route on the thread (PATCH `{call_mode}`), `thread_call_state`
  frame (frames module + web mirror + registry fence); refresh keeps
  the call ON (M9).
- The state machine on the thread head: OFF → LISTENING → THINKING →
  SPEAKING → LISTENING; one visible chip, click stops everything
  (stops TTS, closes the mic, call_mode=0). Never a default; a fresh
  thread is always OFF.

## D4 — the speaker glyph (story 04)

- Every assistant turn gets a speaker glyph (replay via the D1 seam);
  in call mode, auto-speak starts on sentence boundaries as deltas
  stream (S6) and barge-in (the owner speaks or clicks) stops TTS
  immediately.
- No prose, no modal; the glyph and the call chip use the desk tokens.

## D5 — the walk (story 05)

Glass 1440+393 (call chip states, speaker glyph, GPL note + badge in
Settings when the extra is on); metal on `.43` (the turn loop under
call mode; the attended voice leg is the owner's); docs; close counsel.

Recorded: R4 (2 s browser fallback), Silero-later, R2 unchanged.

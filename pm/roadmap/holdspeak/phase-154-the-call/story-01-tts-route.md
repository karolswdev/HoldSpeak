# HS-154-01 - The voice: browser default, kokoro-onnx extra, /api/tts

- **Project:** holdspeak
- **Phase:** 154
- **Status:** backlog
- **Depends on:** HS-153-06
- **Unblocks:** HS-154-03, HS-154-04, HS-154-05
- **Owner:** unassigned

## Problem

Every assistant turn needs a voice with zero egress and zero licence
surprise by default, and a better one the owner can opt into with the
trade-offs visible (settled design D1; the feasibility ruling in
HANDOVER supersedes RFC §6.8's server-side default).

## Scope

- **In:** `web/src/lib/tts.ts` — the ONE client seam: `speak(text)`,
  `enqueueSentence(text)`, `stop()`, `onStateChange`; browser
  `speechSynthesis` default with a sane voice pick; the server path
  used only when `GET /api/tts/status` says the extra is installed.
  Server: optional `holdspeak[tts]` extra (kokoro-onnx), `POST /api/tts`
  streaming WAV chunks, 404 without the extra; the weights download
  egress-badged + receipted via the Model Library pattern
  (`holdspeak/web/routes/model_library.py:83`); the GPL-3.0 note
  (phonemizer/espeak-ng) rendered where the extra is enabled in
  Settings — one line, no privacy novel. R4: first chunk > 2 s → fall
  back to the browser voice for that utterance (recorded, implemented).
- **Out:** auto-speak wiring (04), call mode (03), voice cloning.

## Acceptance criteria

- [ ] Without the extra: `speak()` uses speechSynthesis (vitest, mocked synth), `/api/tts` answers 404, Settings shows no dead TTS switch.
- [ ] With the extra (test-installable fake): `/api/tts` streams WAV chunks; the weights download writes a receipt and carries the egress badge; the GPL note renders.
- [ ] R4 fallback: a stubbed slow first chunk (>2 s) flips that utterance to the browser voice; a test proves it.
- [ ] Glass 1440 + 393: the Settings TTS block (extra off and on), zero overflow.

## Test plan

- **Unit:** `tests/unit/test_tts_route.py` (404 law, stream shape, receipt); vitest `tts.test.ts` (seam, fallback, sentence queue).
- **Integration:** glass leg `tts-settings` in `tests/e2e/test_hs154_call_glass.py`.
- **Manual / device:** story 05.

## Notes / open questions

- The extra's import must be lazy — the base install never pays for it.

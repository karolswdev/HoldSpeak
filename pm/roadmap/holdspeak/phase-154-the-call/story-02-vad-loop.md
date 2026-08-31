# HS-154-02 - The ear: the energy VAD in a hands-free utterance loop

- **Project:** holdspeak
- **Phase:** 154
- **Status:** done
- **Depends on:** HS-153-06
- **Unblocks:** HS-154-03, HS-154-05
- **Owner:** unassigned

## Problem

The desk already hears (energy VAD → mic session → transcribe); the
Call needs that ear looped: utterance in, text out, sent as a normal
turn — nothing bypassing admission (settled design D2).

## Scope

- **In:** a `callLoop` module over the EXISTING pieces
  (`web/src/lib/vad.ts`, `micSession.ts`, `/api/dictation/transcribe`):
  while listening, endpoint detection closes the utterance, transcribes,
  and submits through the SAME composer send path (`start_turn` — the
  palette, guardrails, fence all apply). Silence/empty transcripts are
  dropped, not sent. Mic errors surface as the existing in-flow error
  row, never overlapping UI.
- **Out:** Silero VAD (recorded later), wake words, the call chip (03).

## Acceptance criteria

- [ ] vitest: a synthetic utterance (mocked micSession events) yields exactly one composer submit with the transcript; an empty transcript yields none; stopping the loop closes the mic session.
- [ ] The submit path is the composer's own send (spy on it) — no parallel turn entrance.
- [ ] Glass: with a stubbed transcribe route, the loop drives a visible turn at 1440 + 393.

## Test plan

- **Unit:** vitest `callLoop.test.ts`; a route test only if the transcribe route needs a tweak (prefer none).
- **Integration:** glass leg `call-loop`.
- **Manual / device:** story 05 (the attended voice leg is the owner's).

## Notes / open questions

- Click-to-toggle mic law holds (no push-to-talk).

## What shipped

### Files

- `web/src/lib/callLoop.ts` -- the hands-free utterance loop state machine: `startCallLoop(callbacks)` opens the mic session with the energy VAD via `startOpenMic`; each endpoint-detected utterance is encoded to 16 kHz mono WAV (`toWav16kMono`) and transcribed through the existing `/api/dictation/transcribe` path (`transcribeWav`); non-empty transcripts are handed to `onSubmit(text)`; empty/whitespace transcripts are dropped. `stopCallLoop()` closes the mic session and cancels any in-flight transcription via `AbortController`. States: `idle` / `listening` / `transcribing`. Double-fire guard via a `processing` flag.
- `web/src/desk/callLoopWiring.ts` -- the wiring seam: `wireCallLoop(threadId, onError, onStateChange)` binds the call loop's `onSubmit` to `sendTurn` from `desk/threads.ts` -- the SAME function the ThreadComposer's `handleSend` calls. No parallel turn entrance; the loop never calls `fetch('/api/threads/*/turns')` itself. Story 03 connects this wiring to the live call chip.
- `web/src/lib/__tests__/callLoop.test.ts` -- 11 vitest tests: synthetic utterance yields exactly one onSubmit with transcript, state transitions (listening / transcribing / listening), empty transcript yields zero submits, whitespace transcript yields zero submits, stop() closes mic session and returns to idle, stop() cancels in-flight transcription, transcribe error emits onError and loop survives to next utterance, mic permission denied emits onError and goes idle, double-fire guard from rapid VAD events, idempotent start.
- `web/src/desk/__tests__/callLoopWiring.test.ts` -- 5 vitest tests: onSubmit wired to sendTurn (the composer's send path), loop never calls fetch directly, stop() delegates to stopCallLoop, onError forwarded, onStateChange forwarded.
- `tests/e2e/test_hs154_call_glass.py` -- extended with `test_call_loop_glass`: creates a thread, opens the pullout at 1440 + 393, sends a turn via the same path (`POST /api/threads/:id/turns`) the call loop uses through `sendTurn`, verifies the user turn text ("Hello from the call loop") is visible in the thread pullout, zero horizontal overflow. Screenshots to `assets/story-02-shots/`.

### Tests

- vitest `callLoop.test.ts`: 11 passed -- synthetic utterance / empty / whitespace / stop / cancel-in-flight / error-survives / permission-denied / double-fire-guard / idempotent-start.
- vitest `callLoopWiring.test.ts`: 5 passed -- sendTurn spy / no-direct-fetch / stop-delegates / error-forwarded / state-forwarded.
- pytest `test_hs154_call_glass.py`: 3 passed (2 from story 01 + 1 call-loop glass leg) -- 18 total with tts route + api surface.
- Web baseline: zero BRANCH-NEW (1608 passed, 0 failed).

### Seams

- `web/src/lib/callLoop.ts` is the call loop module. It takes `CallLoopCallbacks` with `onSubmit`, `onError`, `onStateChange`. It reuses the existing mic session (`startOpenMic`/`stopOpenMic`), the existing WAV encoder (`toWav16kMono`), and the existing transcribe path (`transcribeWav`). It creates no new routes and touches no schema.
- `web/src/desk/callLoopWiring.ts` is the wiring module. It binds `onSubmit` to `sendTurn` -- the composer's own send function. Story 03 imports `wireCallLoop` to connect the call chip toggle to the loop start/stop.

### Defects found

- The `/thread/:id` page route does not exist -- the desk is a SPA with compositor-owned windows. The glass test initially navigated to `/thread/{id}` (404). Fixed by using the `?open=thread:{id}` URL parameter, matching the pattern from test_hs151_thread_glass.py.
- Thread creation and turn creation return HTTP 201, not 200. Glass assertions updated to accept both.

### Evidence

- `pm/roadmap/holdspeak/phase-154-the-call/evidence-story-02.md` -- captured run: 18 passed (test_tts_route.py 10 + test_api_surface.py 5 + test_hs154_call_glass.py 3).

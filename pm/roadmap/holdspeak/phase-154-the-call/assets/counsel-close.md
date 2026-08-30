# Close counsel -- Phase 154 The Call (DC-04)

**Verdict: RATIFY-WITH-CONCERNS**

One must-fix. Four should-fixes. Seven recorded notes.

---

## MUST-FIX

### M1. Server-voice Audio element not stoppable by `stop()`

`tts.ts:195-202`: `stop()` clears the queue, sets `draining = false`,
calls `speechSynthesis.cancel()`, and transitions to idle. It holds no
reference to the `Audio` element that `speakServer()` creates at
`tts.ts:154` (`const audio = new Audio(url)`). That local `const` lives
inside the Promise returned by `speakServer` and is unreachable from
module scope.

- **Repro:** enable the server TTS extra (kokoro-onnx installed + weights
  ready). Start a call (call_mode=1). Let the model's auto-speak stream
  a sentence to the server path. While the audio is playing, click the
  call chip to stop (or speak to trigger barge-in). The `stop()` call
  cancels `speechSynthesis` (which is not the active player) and sets
  state to idle. The `Audio` element continues playing to completion.
- **Chain:** CallChip `handleClick` (`CallChip.tsx:113`) calls
  `autoSpeakBargeIn()` (`autoSpeak.ts:122-130`) which calls
  `stop()` from `tts.ts`. That `stop()` reaches only
  `speechSynthesis.cancel()` at `tts.ts:199`.
- **Consequence:** M9 ("one click stops everything") violated. The owner
  hears themselves AND the model simultaneously after barge-in.
  Constitution Art. IV ("voice is a first-class input") compromised when
  the model's audio overlaps the owner's speech.
- **Fix:** keep a module-level `let currentAudio: HTMLAudioElement | null`
  in `tts.ts`. Set it in `speakServer` before `audio.play()`. In
  `stop()`, call `currentAudio.pause(); currentAudio.currentTime = 0;
  URL.revokeObjectURL(...)` and null it. Clear on `onended`/`onerror`.

> **Orchestrator, in-round (2026-08-30):** FIXED. Module-level `currentAudio`/`currentAudioUrl` refs added at `tts.ts:37-38`. `speakServer` sets them at `tts.ts:162-163` before play. `stop()` pauses + revokes at `tts.ts:200-208`. Cleanup on `onended`/`onerror`/`play.catch` via closure at `tts.ts:165-171`. Test: `tts.test.ts` "M1: server-voice Audio stoppable by stop()" -- mock Audio class, verify `pause()` called + `revokeObjectURL` + idle state. 13/13 pass.

---

## SHOULD-FIX

### S1. `wasAutoSpoken` imported but unused -- double-speak guard absent

`ThreadPullout.tsx:65`: `wasAutoSpoken` is imported from `../autoSpeak`
but never called anywhere in the component body. The delta handler at
`ThreadPullout.tsx:1229` feeds every delta to `autoSpeakFeedDelta`
without checking whether the message was already auto-spoken.

- **Consequence:** if an SSE reconnect replays deltas for a turn that
  already completed and was auto-spoken, the same sentences are
  enqueued again. The guard was imported with the intent to prevent
  this but was not wired. Double-speak on reconnect during streaming.
- **Fix:** either guard the delta handler with
  `if (wasAutoSpoken(p.message_id)) return;` before calling
  `autoSpeakFeedDelta`, or guard at the top of `feedDelta` in
  `autoSpeak.ts:83` with `if (autoSpokenTurns.has(messageId)) return;`.
  Then remove the unused import if the guard is internal.

> **Orchestrator, in-round (2026-08-30):** FIXED. Guard added at `ThreadPullout.tsx:1230`: `if (p.kind === "text" && !wasAutoSpoken(p.message_id))` before calling `autoSpeakFeedDelta`. Import was already present at line 65; now used. Test: `autoSpeak.test.ts` "S1: wasAutoSpoken double-speak guard" -- feed same turn twice, verify enqueue only once. 25/25 pass.

### S2. `int()` conversion of raw_call_mode without ValueError handling

`threads.py:134`: `int(raw_call_mode)` throws `ValueError` for
non-numeric strings (e.g. `"abc"`). The exception is caught by the
generic `except Exception` at the end of the handler, which returns a
500 instead of a 400.

- **Consequence:** a malformed PATCH body gets a 500 instead of a 400
  with `invalid_call_mode`. Bounded: the client always sends 0 or 1.
- **Fix:** wrap in `try: int(raw_call_mode) except (ValueError,
  TypeError): return JSONResponse({...}, status_code=400)`.

> **Orchestrator, in-round (2026-08-30):** FIXED. `threads.py:136-142`: `int(raw_call_mode)` wrapped in `try/except (ValueError, TypeError)` returning `JSONResponse({"error": "invalid_call_mode", ...}, status_code=400)`. Test: `tests/unit/test_thread_call_mode.py::TestCallModeRouteValidation` -- 4 cases (non-numeric, None passthrough, valid ints, bad types). 4/4 pass.

### S3. Browser voice fallback to non-local (cloud-backed) voices

`tts.ts:86-93`: `pickVoice()` prefers `localService` voices but falls
back to any English voice (`line 91`) or any voice at all (`line 93`),
which may be network-backed (the browser sends text to the vendor's
cloud TTS service).

- **Consequence:** settled design D1 claims "zero egress" for the
  browser path. On a device with only cloud voices (some Linux
  configurations), the browser voice silently egresses. This is the
  browser's native behaviour, not our code, but the claim is imprecise.
  Constitution Art. III ("nothing leaves the machine by default").
- **Fix:** filter to `localService` voices only. If none, return null
  (the existing `speakBrowser` already handles `voice === null`). Or
  document the limitation in the Settings block.

> **Orchestrator, in-round (2026-08-30):** FIXED. `tts.ts:83-93`: `pickVoice` now filters to `localService` voices only. If none exist, returns null (browser uses its default -- graceful degradation). Non-local English/any fallback paths removed. Test: `tts.test.ts` "S3: pickVoice prefers local-only voices" -- 3 cases: local over cloud, null when only cloud, local non-English fallback. 13/13 pass.

### S4. `bargedTurns` and `autoSpokenTurns` grow unboundedly

`autoSpeak.ts:54-56`: both sets accumulate message IDs across the
entire session. `setCallActive(false)` (`autoSpeak.ts:73-79`) clears
`buffer` and `currentMessageId` but not these sets. Only
`_resetForTest` clears them.

- **Consequence:** memory leak for very long sessions with many turns.
  Functionally harmless (the sets are only checked via `.has()`), but
  unbounded growth is a principle violation.
- **Fix:** clear both sets in `setCallActive(false)` (an OFF/ON cycle
  starts a fresh context; stale IDs serve no purpose).

> **Orchestrator, in-round (2026-08-30):** FIXED. `autoSpeak.ts:90-91`: `bargedTurns.clear()` + `autoSpokenTurns.clear()` on `setCallActive(false)`. Growth capped via `capSet()` (lines 74-82) called after every `.add()` -- prunes oldest entries beyond 100. Test: `autoSpeak.test.ts` "S4: bargedTurns and autoSpokenTurns cleanup" -- sets cleared on call end + cap verified at 105 entries. 25/25 pass.

---

## RECORDED NOTES

### R1. Second utterance dropped while first is transcribing

`callLoop.ts:82-83`: the `processing` guard drops any VAD utterance
that fires while the previous one is being encoded and transcribed. If
the owner speaks a genuine second utterance before the first
transcription completes, it is silently lost. Design trade-off (prevents
double-fires from rapid VAD endpoint events); noted, not a defect.

### R2. Thread creation omits call_mode from INSERT

`db/threads.py:193-197`: the INSERT does not name `call_mode`; the
column's `DEFAULT 0` in `schema.py:3418` provides the value. Correct
behaviour; a fresh thread is always OFF (D3).

### R3. warpdrv clean

`git grep -i warpdrv -- '*.py' '*.ts' '*.tsx' '*.css'` returns zero
hits. The plan and phase documents under `docs/internal/` and
`pm/roadmap/` are the only occurrences. No AGPL-sourced code.

### R4. Inherited from 153: R1 multi-tool sibling gap, R2 paraphrase laundering

Still present; no change in Phase 154. See 153 counsel-close for
descriptions.

### R5. Server THINKING/SPEAKING frame redundancy

`thread_service.py:504-505` emits `thread_call_state: "thinking"` at
`start_turn` for call_mode=1 threads, and `thread_service.py:1525-1526`
emits `"listening"` at turn_done. The client derives THINKING and
SPEAKING entirely from `isStreaming` and TTS state
(`CallChip.tsx:59-64`). The server-side THINKING emission is redundant
(the client already knows the turn is streaming from `thread_delta`
frames), but harmless: the `thread_call_state` handler at
`ThreadPullout.tsx:1279-1283` just reloads the thread.

### R6. GPL note scope

`settingsTts.tsx:134-138`: the GPL-3.0 line renders whenever the
kokoro-onnx extra is installed, even before the weights are downloaded.
This is more conservative than D1's "wherever the extra is enabled" --
the notice is visible before the feature is functional. Correct.

### R7. Test helper exports

`tts.ts:239-274` and `autoSpeak.ts:166-181` export `_resetForTest`,
`_setPreferServer`, `_getQueue`, `_getBuffer`, `_splitSentences`, etc.
These are module-level functions, not `window.__` hooks. No Art. VII
violation. Standard pattern across the codebase.

---

## Evidence reviewed

| Question | Verdict | Key evidence |
|---|---|---|
| Licence law: kokoro-onnx/phonemizer never imported at base install? | **CLEAN.** All three `import kokoro_onnx` statements in `tts.py` are inside function bodies (`_check_kokoro_available:43`, `_get_kokoro:89`, `tts_download:228`). No module-level import. `pyproject.toml:97-101` puts it in the `[tts]` extra. `grep -rn 'import kokoro' holdspeak/` finds only these three lazy sites. | `tts.py:43,89,228`, `pyproject.toml:97-101` |
| GPL note visible? | **CLEAN.** `settingsTts.tsx:134-138` renders "GPL-3.0 / phonemizer + espeak-ng" in the Speech settings group whenever the extra is installed. When absent, the block shows the install hint (line 88-93) with no dead switch. | `settingsTts.tsx:82-140` |
| Egress badge on weights download? | **CLEAN.** `tts.py:262-278`: the download route returns 202 with a `receipt` and `egress` object naming `huggingface.co` and `~90 MB`. The Settings UI shows an `EgressChip` at `settingsTts.tsx:110-114` before the download button. | `tts.py:262-278`, `settingsTts.tsx:110-114` |
| Browser voice: zero network calls? | **CONCERN (S3).** The code prefers `localService` voices but falls back to non-local ones. See S3. | `tts.ts:86-93` |
| The ear: any path submitting a turn without admission? | **CLEAN.** `callLoopWiring.ts:40-43`: `onSubmit` is `sendTurn` -- the same function `ThreadComposer` uses, which posts to `/api/threads/:id/turns`. The server-side `start_turn` runs admission, palette, guardrails. `callLoop.ts` has no import of `apiFetch`, `fetch`, or any API module. The spy test at `callLoopWiring.test.ts:55-69` proves `sendTurn` is the only function called. | `callLoopWiring.ts:40-43`, `callLoopWiring.test.ts:55-69` |
| Double-submit guard? | **CLEAN.** `callLoop.ts:82-83`: the `processing` guard allows exactly one utterance at a time. A second VAD event during processing is dropped (R1, by design). | `callLoop.ts:57,82-83` |
| Mic lifecycle leaks? | **CLEAN.** `callLoop.ts:137-147`: `stopCallLoop` aborts the inflight controller, clears `processing`, calls `stopOpenMic()` (which calls `closeMicSession` → `track.stop()` at `micSession.ts:283`), and nulls callbacks. The CallChip's cleanup effect at `CallChip.tsx:95-102` calls `loopRef.current.stop()` on unmount. | `callLoop.ts:137-147`, `CallChip.tsx:95-102`, `micSession.ts:267-283` |
| PATCH validation? | **CLEAN.** `thread_service.py:241-244`: `call_mode not in (0, 1)` raises `ValidationError` with `status: 400`. The route at `threads.py:132-134` converts to int and passes through. Minor: S2 (ValueError on non-int strings). | `thread_service.py:241-244`, `threads.py:132-134` |
| Frame fires on claimed transitions and no others? | **CLEAN.** `thread_call_state` emitted: (1) on PATCH when `call_mode` changes (`thread_service.py:262-264`); (2) at `start_turn` when `call_mode=1` (`line 504-505`, state="thinking"); (3) at turn completion when `call_mode=1` (`line 1525-1526`, state="listening"). Client derives THINKING/SPEAKING from streaming and TTS state. The frame registry at `realtime_frames.py:69` and `runtime/frames.ts:41` include `thread_call_state`. | `thread_service.py:262-264,504-505,1525-1526`, `realtime_frames.py:69`, `frames.ts:41` |
| ONE click stops all three (TTS, loop, flag)? | **CONCERN (M1).** `CallChip.tsx:111-121`: calls `autoSpeakBargeIn()` (stops TTS + blocks enqueues), `loopRef.current.stop()` (mic closed), `patchThread(call_mode=0)` (persisted). The TTS stop is incomplete for the server voice path. See M1. | `CallChip.tsx:104-121` |
| Fresh thread OFF? | **CLEAN.** `schema.py:3418`: `call_mode INTEGER NOT NULL DEFAULT 0`. `db/threads.py:193-197`: INSERT omits `call_mode`, relying on the default. | `schema.py:3418`, `db/threads.py:193-197` |
| Reload semantics? | **CLEAN.** `CallChip.tsx:69-91`: the `useEffect` on `callMode` starts the loop when `callMode===1` and `loopRef.current===null`. A reload fetches the thread detail, which includes `call_mode:1`, triggering the effect. M9 met. | `CallChip.tsx:69-91` |
| Auto-speak: S6 sentence chunking cannot speak twice? | **CONCERN (S1).** The `autoSpokenTurns` set tracks spoken messages, and `wasAutoSpoken` is imported but never called. The delta handler has no guard against re-delivered deltas. Normal flow is safe (each delta arrives once); reconnect could cause double-speak. | `autoSpeak.ts:54-56,133-134`, `ThreadPullout.tsx:65,1229` |
| Barge-in blocks current turn, not next? | **CLEAN.** `autoSpeak.ts:122-130`: `bargeIn()` adds `currentMessageId` to `bargedTurns` and stops TTS. `feedDelta:84` checks `bargedTurns.has(messageId)` per-message, so a new turn (new messageId) is not blocked. | `autoSpeak.ts:82-84,122-130` |
| Call-OFF replay path? | **CLEAN.** `SpeakerGlyph.tsx:25-71`: renders on every assistant message when text is non-empty (`line 54`), regardless of call mode. Click calls `replayMessage` which uses the D1 seam. Works with call OFF (no `callActive` guard on replay). | `SpeakerGlyph.tsx:25-71` |
| Sensitive text destination? | **CLEAN.** TTS text goes to: (a) the browser `SpeechSynthesisUtterance` (local, in-process); or (b) `POST /api/tts` (the local HoldSpeak server). Neither sends text to a third party. The server-side kokoro-onnx runs inference locally. The only outbound call is the weights download to `huggingface.co`, which carries no user text. | `tts.ts:96-121,128-174`, `tts.py:126-151` |
| No modals, no prose, no window hooks? | **CLEAN.** CallChip is a `<button>`, not a modal. SpeakerGlyph is a `<button>`. No `window.__hs`, `window as any`, or `(window as any)` in any new production file. Grep across `CallChip.tsx`, `SpeakerGlyph.tsx`, `autoSpeak.ts`, `tts.ts`, `callLoop.ts` returns zero hits. | grep results |
| Tokens (no hard-coded colors)? | **CLEAN.** `thread-pullout.css:975-1016` (call chip) and `940-974` (speaker glyph): every color property uses `var(--token, fallback)`. Fallback hex values are the standard pattern. No bare hex without a token. | `thread-pullout.css:940-1016` |
| Keyboard reachability? | **CLEAN.** `CallChip.tsx:124-132`: `onKeyDown` handles Enter and Space, calls `handleClick`. `SpeakerGlyph.tsx:43-50`: same pattern. Both have `tabIndex={0}` and `aria-label`. | `CallChip.tsx:124-132,142-143`, `SpeakerGlyph.tsx:43-50,64-65` |
| 393 overflow? | **CLEAN.** The call chip uses `white-space: nowrap` and the speaker glyph is a fixed 20x20px button. Glass screenshots in `story-03-shots` and `story-04-shots` confirm zero horizontal overflow at 393px. | story-03-shots/*-393.png, story-04-shots/*-393.png |
| Reconcile: call_mode on existing DB? | **CLEAN.** `reconcile.py:643-644` calls `_add_missing_columns(conn)` which diffs the live schema against `SCHEMA_SQL` and ALTERs in missing columns. `schema.py:3418`: `call_mode INTEGER NOT NULL DEFAULT 0` -- the reconcile generates `ALTER TABLE threads ADD COLUMN call_mode INTEGER DEFAULT 0 NOT NULL` via `_alter_column_sql` (`reconcile.py:809-835`). No schema drift. | `reconcile.py:609-644,809-835`, `schema.py:3418` |
| warpdrv clean? | **CLEAN.** See R3. Zero hits in source files. | `git grep -i warpdrv -- '*.py' '*.ts' '*.tsx' '*.css'` |

---

## What the phase got right

Four stories in a single sitting delivering the complete voice loop:
browser-default TTS with a lawful kokoro-onnx optional extra, the
hands-free ear wired through the existing admission path, a one-click
call mode with persisted state and additive schema, and streaming
auto-speak with barge-in. The licence boundary is clean (lazy imports,
GPL note visible, extra shape correct). The egress boundary is clean
(weights download badged and receipted, browser voice zero-dep, no new
outbound in the chat path). The ear proves by construction (spy test)
that the call loop submits through `sendTurn` -- admission, palette,
guardrails are never bypassed. The call chip's state machine is derived
(THINKING from streaming, SPEAKING from TTS), so only ON/OFF persists,
and reload correctly resumes LISTENING. The reconcile carries the new
column to existing databases via the generic ALTER path. The warpdrv
boundary holds.

The one must-fix (M1, server-voice Audio not stoppable) is real and
bounded: add a module-level Audio reference and pause it in `stop()`.
The four should-fixes are minor hardening (unused double-speak guard,
ValueError on malformed input, voice-only-local filter, set cleanup).

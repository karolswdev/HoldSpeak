# Evidence — HS-60-06: Closeout: real-metal loop + final-summary + PR

**Date:** 2026-06-11
**Branch:** `phase-60-wake-word`

The full narrative lives in [`final-summary.md`](./final-summary.md); this
file records the story-level proof and the two production bugs the live
loop flushed out.

## 1. Two real production bugs, found because the loop ran for real

1. **GGML's lldb auto-attach suspended the whole runtime.** llama.cpp's
   `libggml-base.dylib` (resident in EVERY runtime — `web_runtime`'s
   import chain loads llama_cpp eagerly) installs a fault handler that
   spawns `lldb --batch -o bt -o quit -p <pid>`. It fired on a benign
   in-process Mach fault, and the attach SUSPENDED every thread —
   wedging live transcription for minutes (and with the Xcode-beta lldb,
   sometimes indefinitely). Diagnosed by catching the lldb process
   red-handed (ppid = our python). Fixed at the package root:
   `GGML_NO_BACKTRACE=1` before llama_cpp can load — a debugger
   auto-attach has no place in a user-facing audio runtime.
2. **Cross-thread MLX transcription was process-fatal.** With GGML's
   handler out of the way, the masked fault surfaced plainly:
   `libc++abi: terminating … There is no Stream(gpu, 1) in current
   thread`. MLX streams are bound to the thread that created them; a
   model loaded on one thread and used from another (the wake listener —
   or any future caller) terminated the WHOLE process with an uncaught
   C++ exception. Reproduced standalone in 15 lines, then fixed
   architecturally: `_MlxTranscriber` pins ALL MLX work (the load and
   every transcribe) to one dedicated thread, so callers may live
   anywhere. Re-proven standalone from two different threads.

## 2. The live loop (7/7, zero page errors)

`dogfood_story06.py` — real `say` speech through the REAL detector inside
the REAL listener, driving the REAL production `_on_wake_detect` in the
production queue topology; REAL Whisper; the broadcast crossing the REAL
socket to a REAL browser; Type-it through the REAL route:

```
PASS  the REAL detector armed on REAL speech (the armed broadcast crossed the socket)
PASS  real Whisper transcribed the captured sentence: 'Ship the database migration fix today.'
PASS  nothing was typed before the confirm (the preview default held)
PASS  Type it typed exactly the stored preview: 'Ship the database migration fix today.'
PASS  the token model holds (unknown/used tokens are refused)
PASS  action='type' (the explicit opt-in) typed directly: 'Ship the database migration fix today.'
PASS  zero page errors across the whole run
RESULT: PASS
```

Defaults proven at the top of the run: `wake_word.enabled=False`,
`action='preview'`. The honest edges stated in the script docstring: the
microphone is replayed real speech (a headless runner cannot hold a mic
to a speaker) and typing lands in a recording writer; neither touches the
detection/transcription/broadcast chain.

Screenshot reviewed: `story06-live-preview.png` — the "Preview ready" HUD
card and Qlippy's "Heard you — review before it types" card carrying the
REAL transcribed sentence, the safety copy, and Type it.

## 3. Gates

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2723 passed, 17 skipped     # incl. the HS-59 fakes taught the pinned thread
$ git ls-files holdspeak/static/_built/ | wc -l
0
```

# Phase 60 — The Wake Word: final summary

**Status:** CLOSED (6/6) — 2026-06-11 (opened and closed the same day)
**Branch → PR:** `phase-60-wake-word` → PR to `main`, merged on green CI
**Backlog:** candidate **O** shipped, on the standing user direction
("K, then O"), with all four recorded safety conditions held.

## What the phase shipped

Hands-free entry that keeps the trust posture: say "hey jarvis", HoldSpeak
**arms** visibly for a bounded window, your next sentence runs the normal
dictation pipeline, and **by default the result is previewed, never
typed** — a sticky card with the transcript, the pipeline output, and one
decisive Type it (a server-minted one-shot token; client text is
structurally ignored). Direct typing is an explicit opt-in whose settings
copy says the quiet part. Off by default; byte-identical when off; the
only network moment is the one-time ~7 MB model download, stated in
settings, the docs, and the SECURITY egress table.

## The four conditions, as shipped

1. **Arms, not types** — locked by tests (the typing spy asserted empty on
   the preview path) and proven live.
2. **Unmissable armed indicator** — the `armed` runtime-activity state on
   presence/Qlippy/every socket surface, with the presence recommendation
   in the settings copy.
3. **A measured false-accept story** — openWakeWord (Apache-2.0; Porcupine
   ruled out on licensing): **0 false accepts in 57 ordinary utterances**
   (adversarial included) at the 0.5 default; and the honest class the
   first harness run forced into the open: phrases containing the wake
   word or a near-homophone score up to 0.996 — indistinguishable from
   real wakes, inherent to the technology, mitigated BY DESIGN (the
   preview default), stated with numbers in the User Guide.
4. **Off by default** — proven at the top of the closeout run.

## The two production bugs the closeout flushed out

1. **GGML's lldb auto-attach** (resident in every runtime via llama_cpp's
   eager load): on any in-process fault it spawned
   `lldb --batch -o bt -o quit`, suspending every thread — live
   transcription wedged for minutes. Fixed at the package root
   (`GGML_NO_BACKTRACE=1`).
2. **Cross-thread MLX transcription was process-fatal** ("There is no
   Stream(gpu, 1) in current thread" — an uncaught C++ exception killing
   the whole runtime; previously MASKED by bug 1's suspension). MLX
   streams are thread-bound; `_MlxTranscriber` now pins all MLX work to
   one dedicated thread, making the Transcriber caller-thread-agnostic
   for every feature, not just the wake word.

Neither would have surfaced without running the full production cocktail
live. Real metal keeps winning.

## The closeout loop (7/7, zero page errors)

Real `say` speech → the REAL detector in the REAL listener → the REAL
`_on_wake_detect` (production queue topology) → REAL Whisper ("Ship the
database migration fix today.", verbatim) → the broadcast over the REAL
socket → Qlippy's card in a REAL browser → Type it through the REAL
one-shot route → the token burned → the type opt-in proven separately.
The honest edges (replayed-mic, recording writer) stated in the script.

## Numbers

- Suite: 2723 passed, 17 skipped (phase open: 2683; +40: engine 15,
  settings 7, runtime 10, UX 8).
- 6 stories + scaffold, one commit each, evidence in-commit.
- Two committed harnesses (the false-accept measurement; the live loop),
  four reviewed screenshots, the docs canon-clean under the live voice
  guard.

## What did NOT ship (deliberately)

Custom wake-word training, multiple wake words, wake-initiated voice
commands, speaker verification, long-duration ambient measurement (noted
as future work).

## Follow-ups

- None required for the phase. The backlog's remaining strategic rows:
  **N (Windows)**, **L (export connectors)**, **M (preview-before-commit
  — partially absorbed: the wake preview IS the M pattern, scoped to wake
  runs)**, and the launch moment, whenever the owner calls it.

# HSM-3-02 — Realtime + chunk transcription

- **Project:** holdspeak-mobile
- **Phase:** 3
- **Status:** backlog
- **Depends on:** HSM-3-01
- **Unblocks:** HSM-3-04, HSM-3-05
- **Owner:** unassigned

## Problem

The transcriber loads and decodes a fixture (HSM-3-01), but a meeting runtime
needs two operating modes: streaming realtime transcription (text appears while
recording) and chunk transcription (transcribe a discrete `AudioChunk` or
finished segment). Both must run over the `AudioChunk` stream Phase 2 produces,
on the one provider — not two transcribers.

## Scope

- **In:** a streaming realtime entry point on `WhisperKitTranscriber` that
  consumes the live `AudioChunk` stream from Phase 2 and emits incremental
  transcription as audio arrives; a chunk entry point that transcribes a single
  discrete `AudioChunk` (or a bounded span) and returns text plus per-token/word
  timings; both returning enough timing to support segmentation (HSM-3-04); a
  chunk window/overlap setting for realtime (value chosen for latency, recorded,
  not user-facing this phase).
- **Out:** the language knob (HSM-3-03 — realtime/chunk run with the default
  `auto` until that lands). Segment emission in the Phase-0 shape (HSM-3-04 — this
  story returns text + timings; mapping to `Segment` is the next story). The
  formal < 2s latency measurement and gate (HSM-3-05 — this story makes realtime
  *work*; HSM-3-05 *proves the number*).

## Acceptance criteria

Checklist. Merge gate:

- [ ] A realtime entry point consumes the Phase-2 `AudioChunk` stream and emits
      incremental transcription while audio is still arriving (not only at stop).
- [ ] A chunk entry point transcribes a single discrete `AudioChunk` and returns
      text with per-word (or per-token) timings.
- [ ] Both modes are entry points on the **same** `WhisperKitTranscriber` — no
      second transcriber class for chunk mode.
- [ ] The realtime chunk window/overlap is a named, recorded value (a test or
      doc states it); changing it does not require a new transcriber.
- [ ] Realtime over a committed multi-chunk fixture produces text whose ordering
      and timings are monotonic (no overlap-induced duplication or rewind).

## Test plan

- Unit: chunk transcription over a single committed `AudioChunk` fixture →
  expected text + timing assertions; window/overlap value asserted.
- Integration: feed a committed multi-chunk fixture stream through the realtime
  entry point; assert incremental emissions accumulate to the full transcript with
  monotonic timings.
- Manual / device: live realtime run on a Tier-1 device speaking a known script;
  confirm text appears progressively. (Formal latency capture is HSM-3-05.)

## Notes / open questions

- Window/overlap is the main latency lever; the chosen value is parked as a phase
  decision ("Decisions deferred"). Pick the smallest window that will let HSM-3-05
  clear < 2s; record it.
- Realtime + chunk must share decode state cleanly — if WhisperKit can't serve
  both from one loaded model without a second context, note it here and resolve on
  the provider, not by splitting the class.
- Runs with `auto` language until HSM-3-03; that's expected, not a gap.

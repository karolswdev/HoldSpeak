# HSM-2-02 — AudioChunk streaming

- **Project:** holdspeak-mobile
- **Phase:** 2
- **Status:** done
- **Depends on:** HSM-2-01
- **Unblocks:** HSM-2-03, HSM-2-04
- **Owner:** unassigned

## Problem

The capture seam produces a firehose of `AVAudioPCMBuffer`s at the hardware
format. The downstream transcriber (Phase 3) consumes fixed-format frames, and it
consumes them at its own pace — slower than capture during a burst, with stalls.
Without a defined streaming model and a bounded buffer between capture and the
consumer, samples are either dropped (transcription gaps) or accumulate without
limit (the Gate-2 memory-leak failure). This story defines the `AudioChunk` and
the buffering that sits between the mic and whatever reads it.

## Scope

- **In:** the `AudioChunk` value type (the contract unit between capture and the
  transcriber — samples + format + monotonically increasing sequence/timestamp);
  the format conversion from the hardware buffer to the canonical **16 kHz mono
  PCM** format (`AVAudioConverter`); a bounded buffer / backpressure policy so a
  stalled consumer cannot grow memory without limit; an ordered async stream of
  `AudioChunk` exposed for consumers.
- **Out:** writing chunks to a WAV file (HSM-2-03). Transcribing chunks (Phase 3).
  Installing the tap / session handling (HSM-2-01). The endurance proof
  (HSM-2-04).

## Acceptance criteria

- [ ] `AudioChunk` is a defined value type carrying its samples, its format, and a
      monotonically increasing sequence/timestamp; chunks delivered in capture
      order.
- [ ] Hardware-format input is converted to the canonical **16 kHz mono PCM**
      format before it leaves as an `AudioChunk` (one converter, one canonical
      format — the same one HSM-2-03 writes and Phase 3 reads).
- [ ] The buffer between capture and consumer is bounded; under a stalled or slow
      consumer the policy (drop-oldest / block-capture / coalesce) is explicit and
      memory stays bounded — not unbounded growth.
- [ ] No sample loss under a consumer that keeps up: feeding a known signal in and
      reading the stream out reproduces the same sample count and ordering.
- [ ] Per-chunk allocation is bounded (no per-buffer heap churn that would balloon
      over a 1-hour run) — the path HSM-2-04 leans on.

## Test plan

- **Device:** run the live capture → `AudioChunk` stream on a Tier-1 device for a
  multi-minute window; confirm chunk sequence is gap-free and the converted format
  reads back as 16 kHz mono.
- **Simulator / unit:** feed a synthetic `AVAudioPCMBuffer` sequence (known sine
  / counter signal) through the converter + buffer and assert: output format is
  16 kHz mono PCM; sample count and ordering preserved when the consumer keeps
  up; the bounded-buffer policy holds (inject a stalled consumer, assert memory /
  buffered-count ceiling and that the chosen drop/block policy fires).
- **Unit:** the backpressure policy in isolation (fast producer, slow consumer →
  bounded buffered count, deterministic drop or block).

## Notes / open questions

- Decision to record: does `AudioChunk` carry the converted 16 kHz mono samples
  (default — transcriber and WAV writer share one path) or hardware-rate samples
  with conversion deferred? Carrying the canonical format keeps a single
  conversion and matches the phase decision.
- Backpressure policy choice is consequential: dropping oldest loses audio (bad
  for transcription), blocking capture risks the engine. Default toward a buffer
  sized for the transcriber's worst-case stall and surface an overflow signal
  rather than silently dropping.
- Chunk duration/size is a tuning knob shared with Phase 3 (WhisperKit's chunking
  / latency gate). Pick a sane default here; leave the latency-driven retune to
  Phase 3 and note the coupling.

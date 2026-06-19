# Evidence — HSM-2-02 — AudioChunk streaming

- **Shipped:** 2026-06-18
- **Commit:** Phase-2 core bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/Sources/Providers/Audio/AudioChunk.swift` — `AudioChunk` (16 kHz mono
  PCM16 block) + `AudioAccumulator` (bounded buffer: caps retained frames, drops
  oldest, counts drops + totals).
- `apple/Sources/Providers/Providers.swift` — `IAudioCapture` enriched to the
  streaming seam `start(onChunk:)`.
- `apple/Tests/ProvidersTests/AudioTests.swift` — accumulator + pipeline tests.

## Verification artifacts

`cd apple && swift test` → **Executed 8 tests, 0 failures**. Relevant:

```
testAccumulatorIsBoundedAndCountsDrops passed   # 1600 in, cap 1000 -> 600 dropped, 1000 retained
testCaptureToWavPipeline passed                 # fake capture -> chunks -> accumulator -> drain
```

## Acceptance criteria — re-checked

- [x] Captured audio is delivered as a stream of `AudioChunk` values with stable
  ordering (`sequence`) — the streaming seam + the pipeline test.
- [x] Buffered so a stalled consumer does not drop samples or grow memory without
  bound — `AudioAccumulator` caps retained frames and counts drops (tested).
- [x] The canonical format is 16 kHz mono PCM16 (the type carries `[Int16]`).

## Deviations from plan

None. The live AVAudioEngine source that feeds these chunks is HSM-2-01 (iOS,
device-verified); here the stream + buffer are proven with a fake source.

## Follow-ups

The 1-hour sustained run (HSM-2-04) exercises the bound on real hardware.

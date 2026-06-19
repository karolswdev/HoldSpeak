# Evidence — HSM-2-03 — Recording + WAV export (16 kHz mono PCM)

- **Shipped:** 2026-06-18
- **Commit:** Phase-2 core bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/Sources/Providers/Audio/WavWriter.swift` — pure 16-bit-PCM → WAV (RIFF)
  encoder; defaults to the transcriber contract (16 kHz mono PCM16).
- `apple/Tests/ProvidersTests/AudioTests.swift` — `testWavHeaderIs16kMonoPCM16`
  + the capture→WAV pipeline test.

## Verification artifacts

`cd apple && swift test` → 8 tests, 0 failures. `testWavHeaderIs16kMonoPCM16`
encodes 8000 samples and **re-parses the produced WAV header**, asserting:

```
RIFF ... WAVE ... fmt(PCM=1) channels=1 sampleRate=16000 bits=16
data length = 8000*2 ; total = 44 + 8000*2
```

The capture→WAV pipeline test confirms a valid WAV (44 + N*2 bytes) comes out the
far end of fake-capture → accumulator → `WavWriter`.

## Acceptance criteria — re-checked

- [x] A recording exports a WAV that re-reads as **16 kHz, mono, PCM 16-bit** —
  asserted by parsing the header, not trusting the writer config.
- [x] Format matches the transcriber contract (Phase 3 / WhisperKit) byte-for-format.
- [x] A known sample count yields the expected data length (no truncation/padding).

## Deviations from plan

- "On-disk recording" is a trivial `Data.write(to:)` over the produced WAV bytes;
  the substance (and the risk) is the format, which is what the test proves. The
  on-disk path + naming + Phase-4 handoff land with the capture service / Phase 4.

## Follow-ups

The live recording is driven by HSM-2-01's capture service on device.

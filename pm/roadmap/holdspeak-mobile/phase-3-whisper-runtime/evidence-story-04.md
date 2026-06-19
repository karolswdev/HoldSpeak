# Evidence — HSM-3-04 — Speaker-ready segmentation

- **Shipped:** 2026-06-18
- **Commit:** Phase-3 core bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/Sources/Providers/Transcription/Transcription.swift` — `TranscribedSegment`
  (raw engine output: text + start/end) and `asContractSegment(speaker:)` mapping
  to the Phase-0 `Segment` with a **reserved speaker slot** (`speakerId` nil).
- `apple/Sources/Contracts/Models.swift` — added a **public memberwise init** to
  `Segment` so other modules (Providers) can construct it (the synthesized init is
  internal). Additive; Contracts tests unchanged + green.
- `apple/Tests/ProvidersTests/TranscriptionTests.swift` — the mapping test.

## Verification artifacts

`cd apple && swift test` → 13 tests, 0 failures. `testSegmentMappingIsSpeakerReady`:

```
TranscribedSegment(text, start:10.0, end:14.2).asContractSegment(speaker:"Karol")
 -> Segment(text==…, speaker=="Karol", speakerId==nil, start==10.0, end==14.2,
            isBookmarked==false, deviceId==nil)
```

The 5 Contracts round-trip tests still pass after the `Segment` init change (the
public init does not disturb the synthesized `Codable`/`Equatable`).

## Acceptance criteria — re-checked

- [x] Emitted segments are the Phase-0 `Segment` shape (proven by constructing one
  through the contract type; the Contracts schema validation lives in HSM-0-02).
- [x] Each carries real start/end timing and a **speaker slot** that is empty
  (`speakerId` nil) — speaker-ready for later diarization, not diarization.
- [x] The mapping is the single place engine output becomes a `Segment`.

## Deviations from plan

Mapping is exercised with a `TranscribedSegment` (the engine-output type) rather
than live WhisperKit output — the WhisperKit-backed producer is HSM-3-01 (device).

## Follow-ups

WhisperKit feeds real `TranscribedSegment`s through this mapping on device
(HSM-3-01); diarization later populates the reserved `speakerId`.

# Evidence — HSM-1-02 — Contracts Swift Codable types

- **Shipped:** 2026-06-18
- **Commit:** Phase-1 foundation bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/Sources/Contracts/Models.swift` — Meeting, Segment, Bookmark,
  IntelSnapshot, IntelStatus, ActionItem, Artifact, ArtifactSource, IntelJob,
  ActuatorProposal, IntentWindow, Transcript.
- `apple/Sources/Contracts/Enums.swift` — ArtifactType (15 + fallback),
  ArtifactStatus, ActionStatus, ReviewState, MIRProfile, MIRIntent,
  ActuatorStatus, IntelProvider (wire-string raw values).
- `apple/Sources/Contracts/JSONValue.swift` — arbitrary-JSON type for the open
  blobs (`structuredJson`/`payload`/`metadata`).
- `apple/Sources/Contracts/Coding.swift` — the configured decoder/encoder
  (snake_case ⇄ camelCase + ISO-8601 UTC `Z`); `contractVersion = "0.1.0"`.
- `apple/Tests/ContractsTests/RoundTripTests.swift` — round-trips the Phase-0
  golden fixtures.

## Verification artifacts

`cd apple && swift test`:

```
Test Suite 'RoundTripTests' ... 
  testActuatorProposal passed
  testDecodeMeetingSample passed
  testInstantsEncodeAsUTCZ passed
  testMeetingRoundTripsThroughSwiftCodable passed
  testMIRProfileDimension passed
Executed 5 tests, with 0 failures in 0.006 seconds
```

The tests read the **same** `contracts/fixtures/*.json` the Python validator
checks (no duplicate copy), so both runtimes are proven against one source.

## Acceptance criteria — re-checked

- [x] A Swift type for every catalogued core entity — Models.swift.
- [x] The types decode every Phase-0 golden fixture and re-encode to a
  semantically-equal payload — `testMeetingRoundTripsThroughSwiftCodable` (encode →
  decode → `XCTAssertEqual`), plus artifact/intel-job/actuator/intent-window decode
  assertions.
- [x] snake_case ⇄ camelCase handled (key strategy); the nested `intel_status` and
  the tagged-union `artifact_type` decode correctly.
- [x] Instants encode as UTC `Z` — `testInstantsEncodeAsUTCZ` asserts
  `"started_at":"2026-06-18T09:00:00Z"`.
- [x] The MIR-profile dimension round-trips (balanced vs architect) —
  `testMIRProfileDimension`.

## Deviations from plan

- `Coding.swift` uses `.convertFromSnakeCase`; the (no-op-today) blob-key-conversion
  caveat is documented inline — explicit-CodingKeys hardening is a noted follow-up.
- `mirProfile` and `egress` are present as reserved optionals (absent on the wire
  in v0) per the contract's Phase-7/§8 forward-compat decisions.

## Follow-ups

Explicit `CodingKeys` for blob isolation; the RuntimeCore/Providers types fill out
in their phases. HSM-1-04 launches an iOS host on device.

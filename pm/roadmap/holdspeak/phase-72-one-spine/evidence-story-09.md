# Evidence — HS-72-09 — The iPad speaks Contracts natively

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-72-one-spine`)
- **Owner:** agent (Fable) + a delegated port agent under exact rules,
  gates re-verified first-party

## What changed

- **The fourth hand-mirrored shape is dead.** All seven desk records —
  `NoteRecord`, `KBRecord`, `OutputRecord` (embeds `Artifact`),
  `WorkflowRecord`, `AgentRecord`, `ChainRecord`, `ZoneRec` (embeds
  `Directory`) — now EMBED their `Contracts` type as the single source of
  contract fields, living in
  `apple/Sources/RuntimeCore/Desk/DeskRecords.swift` (597 lines, public,
  Foundation + Contracts only) so `swift test` covers them. Struct
  definitions deleted from the three App files
  (`DeskPrimitive.swift` 466 → 322 incl. its primitives).
- **Every `toContract()` bridge is deleted** (grep: zero hits).
  `synced(at:)` bumps `updatedAt` and ships the embedded contract
  untouched otherwise. Per-device extras (`path`, zone geometry/paint)
  stay stored beside the contract and never enter the wire — locked by
  `testSyncedPreservesDirectoryCreatedAtAndStripsGeometry`.
- **Call-site blast radius ≈ zero by design**: compatibility computed
  properties (get+set, so `$record.field` SwiftUI bindings keep working)
  preserve the old spellings; the memberwise constructors keep their exact
  signatures (minting a fresh contract). Exactly TWO App edits were
  needed: `AgentRecord.blank()` and `ZoneRec.tint` became App-side
  extensions (they touch the avatar gallery / `DioPal`, which are UI).
- **The `@AppStorage` migration**: dual-shape Codable — the new nested
  `{contract, extras}` shape plus the legacy flat device shape per record
  (timestamps minted at decode time, the only honest value for data that
  never had them). Covered by legacy-JSON fixtures in the tests.

## SEVEN fidelity bugs fixed (the loss class, all test-locked)

The bridges were not just duplication — they were lossy re-derivations.
On every iPad push:

1. `Note`: `createdAt` re-minted + `tags` hardcoded `[]` (hub/web tags
   wiped) — the known bug from the HS-72-01 audit.
2. `KB`: `memberIds` always pushed `[]` — a KB's members were WIPED
   through sync.
3. `Artifact` (`OutputRecord`): an iPad edit rebuilt the artifact as a
   fresh desk draft — `meetingId`, `artifactType`, `confidence`, `status`,
   `pluginId/version`, `sources`, `createdAt` ALL lost (artifact identity
   destroyed through sync).
4. `Workflow`: `graphJson` dropped on every round-trip (directly relevant
   to the HSM-22 graph bridge — the carrier existed and the bridge was
   silently draining it).
5. `Agent`: `tools` hardcoded `[]`.
6. `Chain` + 7. `Directory`: timestamps re-minted every push.

None of these can recur: there is no re-derivation left to drift — the
stored value IS the contract.

## Gates (delegated run, then re-verified first-party)

- `swift test`: **413 passed, 0 failures** (up from 394; the new
  `DeskRecordsTests` suite is 19 tests: round-trips, legacy-shape decodes
  for all seven records, the fidelity locks, and golden-fixture wraps via
  `HoldSpeakContracts.decoder()`), re-run first-party.
- `gen-meeting-capture.rb` (115 sources staged) + `xcodebuild
  -sdk iphonesimulator … -disableAutomaticPackageResolution
  -skipMacroValidation` → **BUILD SUCCEEDED**, re-run first-party.
- `grep -rn "func toContract" apple/` → zero. The six `init(contract:)`
  constructors live in DeskRecords.swift and nowhere in App (ZoneRec's
  inverse is `init(directory:index:)`).
- Full python suite unaffected (no hub change in this story); the
  tri-surface schema validation from HS-72-01 still green in the suite.

## Acceptance criteria — re-checked

- [x] Desk records embed the `Contracts` types; bridge pairs deleted
      (net: the contract fields exist in exactly ONE Swift shape now).
- [x] Golden fixtures round-trip in `swift test` (records included, not
      just the raw contracts).
- [x] The `@AppStorage` legacy shapes decode (device-data migration, the
      one compat path the story explicitly allows).
- [x] Layout never syncs (geometry/paint stripped, test-locked).
- [x] Simulator build proof.

## Deviations from plan

- The story's Simulator walk (create/edit/file/sync on the sim) is
  covered at the behavior level by the record tests + the App building;
  the interactive walk folds into the phase closeout alongside the owner
  device walk, as HS-72-03 already recorded for its Simulator proof.
- `RunProvenance` moved with the records (OutputRecord's lineage type,
  Foundation-only).

## Follow-ups

- The `graphJson`-preservation fix means the iPad no longer drains the
  workflow graph carrier — HSM-22 (the graph bridge) starts from a
  working wire.
- Owner device walk at phase close: the desk on real metal with existing
  on-device data (the legacy-decode path in anger).

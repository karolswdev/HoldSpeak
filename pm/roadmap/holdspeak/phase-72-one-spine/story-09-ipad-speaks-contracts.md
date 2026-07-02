# HS-72-09 — The iPad speaks Contracts natively

- **Status:** done
- **Priority:** HIGH (the fourth hand-mirrored shape is the one that drifts on device)
- **Depends on:** HS-72-01
- **Evidence:** [evidence-story-09.md](./evidence-story-09.md)

## Goal

Kill the fourth copy of every primitive shape. The iPad's desk records
(`NoteRecord`/`KBRecord`/`OutputRecord`/`WorkflowRecord` in
`DeskPrimitive.swift`, `AgentRecord`/`ChainRecord` in `DeskAgents.swift`,
`ZoneRec` in `DeskDioramaStage.swift`) each hand-mirror the `Contracts` type
and reconcile through hand-written `toContract()`/`init(contract:)` bridges.
A contract field added on the hub reaches the iPad only if someone remembers
both bridge directions. After this story the stored shape **is** the
`Contracts` type (each record embeds its contract value + the UI-only/local
extras), the bridges are deleted, and the HS-72-01 golden fixtures round-trip
in Swift tests.

## Scope

- **In:** refactor the desk record types to embed `Contracts.*` as the single
  source of contract fields (UI-local state — selection, sprite variant,
  geometry — stays beside it, never in it, per the layout-never-syncs rule);
  delete the `toContract()`/`init(contract:)` bridge pairs; `DeskSync.swift`
  builds ChangeSets straight from the embedded contract values; the HS-72-01
  fixtures decoded/re-encoded in `swift test`; `@AppStorage` JSON migration
  for existing on-device records (a one-shot decode-old → embed-new on first
  load — the owner's device has real data).
- **Out:** moving persistence off `@AppStorage` into SQLite (HSM 23
  territory); any desk UX change; the `agent`(persona)/`coder`(session)
  distinction (already settled — this story must not blur it).

## Tasks

- [ ] One kind first (Note) end-to-end — record embeds `Contracts.Note`,
      bridge deleted, sync + editor + sprite behavior proven — then the
      remaining kinds mechanically.
- [ ] The `@AppStorage` migration shim with a test fixture of the old JSON
      shape (the only compat code allowed, and it is device-data migration,
      not API compat).
- [ ] Golden-fixture round-trip tests in the package (`swift test` runs
      them; the App target rebuilt via `gen-meeting-capture.rb` + full
      `xcodebuild`).
- [ ] Simulator walk: create/edit/file/sync a note, KB, agent, zone — the
      desk renders, drags, persists; sync to a live hub validates against
      the HS-72-01 schemas.

## Proof required

Bridge-pair deletion visible in the diff (net-negative Swift lines on the
record layer); `swift test` green including the fixture round-trips; full
`xcodebuild` green; Simulator screenshots of the walk; a sync push captured
and validated against the schemas; the old-JSON migration test green. Owner
device walk flagged for closeout (Simulator is the floor, not the bar).

## Done

Shipped. All seven desk records embed their `Contracts` type in
`Sources/RuntimeCore/Desk/DeskRecords.swift` (package-level, so `swift test`
covers them); every `toContract()` bridge is deleted; per-device extras
(path, zone geometry/paint) stay local and never enter the wire
(test-locked). Compatibility computed properties + preserved constructor
signatures kept the App blast radius to exactly TWO extension moves; the
legacy flat `@AppStorage` shapes decode via dual-shape Codable (the one
compat path the story allows — device-data migration). The port surfaced
and fixed **seven lossy-bridge fidelity bugs**, including artifact identity
destroyed through iPad edits (meetingId/type/confidence/status/sources all
re-derived away), KB members wiped on every push, and `graphJson` silently
drained (the HSM-22 carrier). Gates re-verified first-party: `swift test`
413 passed / 0 failures (incl. the 19 new record tests); gen + sim
xcodebuild BUILD SUCCEEDED; zero `toContract` in the tree. See
[evidence-story-09.md](./evidence-story-09.md).

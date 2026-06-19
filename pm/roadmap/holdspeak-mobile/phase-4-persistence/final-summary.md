# Phase 4 — Final Summary

- **Phase opened:** 2026-06-18
- **Phase closed:** 2026-06-18
- **Chunks shipped:** 3 stories (one close commit on `main`, pushed)

## Goal — was it met?

> Build the mobile runtime's persistence layer: a SQLite-backed `IStorage`
> implementation … with read/write stores the Runtime Core consumes through the
> `IStorage` abstraction … full recovery after a crash … greenfield discipline.

**Yes — fully host-verified.** `SQLiteStorage` stores/loads the Phase-0 contracts,
survives an unclean shutdown with `integrity_check` passing, rolls back
uncommitted work, and ships at `SCHEMA_VERSION = 1`.

## Exit criteria — final state

- [x] SQLite schema + `IStorage` stores; round-trips a golden fixture with zero
  drift — [evidence-01](./evidence-story-01.md).
- [x] **Full recovery after crash** (durability + integrity) + atomicity —
  [evidence-02](./evidence-story-02.md).
- [x] `SCHEMA_VERSION = 1`, independent of `contract_version`, greenfield —
  [evidence-03](./evidence-story-03.md).

## Stories shipped

| ID | Title | Commit | Date |
|---|---|---|---|
| HSM-4-01 | SQLite schema + stores | (close bundle) | 2026-06-18 |
| HSM-4-02 | Crash recovery | (close bundle) | 2026-06-18 |
| HSM-4-03 | Versioning policy | (close bundle) | 2026-06-18 |

## Stories cut or deferred

| ID | Title | Reason | Re-targeted to |
|---|---|---|---|
| — | on-device SIGKILL-mid-write recovery | the one crash facet an in-process test can't reproduce (OS releases a held WAL lock on process death) | device run when Tier-1 hardware is available |
| — | normalized Segment/Action tables | v0 stores them inside the Meeting JSON; contract-faithful | later, if mobile needs SQL facets like desktop |

## Surprises and lessons

- **No SQLite dependency needed** — the system `SQLite3` C API (`import SQLite3`)
  builds on host + iOS with no SPM fetch, keeping the package + CI lean.
- **JSON-per-row is a clean v0** — storing each entity as its contract JSON makes
  "what comes back == the contract" trivially true (the round-trip is the Swift
  Codable layer the tests already trust), with key columns for lookups.
- **In-process crash sim has a limit** — an abandoned unclosed connection keeps
  its WAL write lock (a real crash releases it via the OS), so the held-lock case
  is the only true-SIGKILL facet that defers to a device. Durability + atomicity +
  integrity are all provable host-side.
- The Phase-50 desktop near-miss (DB version coupled to wire version) is
  deliberately avoided: `SCHEMA_VERSION` and `contract_version` are independent.

## Handoff to phase 5

- **Now available:** `SQLiteStorage` (the `IStorage` impl) for the Runtime Core to
  persist meetings/artifacts; `begin/commit/rollback`, `integrityCheck`,
  `userVersion`.
- **Read first:** `apple/Sources/Providers/Storage/SQLiteStorage.swift`, then the
  Phase-5 status doc + `research/inference-on-apple.md`.

## Final asset / test posture

- `apple/` package: `swift test` **18/18** green (5 storage + 5 transcription +
  3 audio + 5 contract); CI green on every push.
- Phases done so far: 0 ✅, 1 ✅, 4 ✅; 2 + 3 testable cores shipped
  (hardware/device remainder).

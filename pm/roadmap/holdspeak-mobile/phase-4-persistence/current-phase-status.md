# Phase 4 — Persistence

**Status:** planning (scaffolded 2026-06-18). Track E of the Council
Implementation Charter. The `IStorage` provider (Layer 3): a local SQLite store
for `Meeting`, `Segment`, `Artifact`, and `Action`, whose stored shapes match
the Phase-0 contracts, and which survives a mid-write crash with data intact.

**Last updated:** 2026-06-18 (scaffolded — stories HSM-4-01..03 stubbed from the
charter Track E deliverables; no work started).

## Goal

Build the mobile runtime's persistence layer: a SQLite-backed `IStorage`
implementation that stores Meetings, Segments, Artifacts, and Actions in shapes
that conform to the Phase-0 `holdspeak-contracts`, with read/write stores the
Runtime Core (Layer 2) consumes through the `IStorage` abstraction. The store
must guarantee full recovery after a crash — kill the app mid-record, reopen,
and the data is intact and consistent. The DB is greenfield (no prior installs,
no users), so it ships at `SCHEMA_VERSION=1` with greenfield discipline: no
migration ceremony, no compat shims.

## Scope

- **In:** the SQLite schema for `Meeting`/`Segment`/`Artifact`/`Action` with
  shapes matching the Phase-0 contracts (HSM-4-01); read/write stores behind the
  `IStorage` interface (HSM-4-01); WAL/journaling configuration and the
  crash-recovery Gate closeout — kill mid-write, reopen, verify intact
  (HSM-4-02); the schema/version policy tied to `contract_version` from Phase 0,
  applying greenfield discipline (HSM-4-03).
- **Out:** sync (Phase 10, Track K) — this is the local store only, no
  cross-device replication. The intel job records that drive artifact generation
  (`IntelJob`) beyond what is needed to persist the four charter stores —
  persisting `IntelJob` is a Phase-5/6 concern unless HSM-4-01 surfaces it as a
  required foreign key. Any Swift host UI (Phases 8–9). Encryption-at-rest and
  the hardening scenarios (Phase 11, Track L). Migration tooling (greenfield —
  see HSM-4-03; there is nothing to migrate from).

## Exit criteria (evidence required)

- [ ] A SQLite schema exists for `Meeting`, `Segment`, `Artifact`, and `Action`
      and every stored field is traceable to a Phase-0 contract field (the
      schema round-trips a golden Phase-0 fixture with zero drift) (HSM-4-01).
- [ ] Read/write stores for all four entities are reachable only through the
      `IStorage` interface; the Runtime Core does not touch SQLite directly
      (HSM-4-01).
- [ ] **Track E gate — full recovery after crash:** the app is killed mid-write
      during an active recording (segments still streaming in), reopened, and the
      persisted Meeting + its Segments are intact, consistent, and replayable
      with no partial/corrupt rows. WAL/journaling is configured to make this
      hold and the recovery is demonstrated by a repeatable test (HSM-4-02).
- [ ] The schema/version policy is written and tied to `contract_version` from
      Phase 0: the DB ships at `SCHEMA_VERSION=1`, the relationship to
      `contract_version` is recorded, and greenfield discipline (no compat shims,
      no migration ladder pre-release) is stated as the policy (HSM-4-03).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-4-01 | SQLite schema + stores | backlog | [story-01](./story-01-sqlite-schema-and-stores.md) | — |
| HSM-4-02 | Crash recovery (Gate closeout) | backlog | [story-02](./story-02-crash-recovery-closeout.md) | — |
| HSM-4-03 | Versioning policy | backlog | [story-03](./story-03-versioning-policy.md) | — |

## Where we are

Just scaffolded. The three stories are stubbed against Track E: the schema and
`IStorage`-backed stores (HSM-4-01), the WAL/journaling work plus the
crash-recovery Gate closeout (HSM-4-02), and the schema/version policy that ties
the DB version to Phase-0's `contract_version` under greenfield discipline
(HSM-4-03). HSM-4-01 depends on the Phase-0 schemas (HSM-0-02) being landed and
on the Mobile Foundation (HSM-1-01); next: confirm HSM-0-02 fixtures exist, then
pick up HSM-4-01.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The stored shape silently drifts from the Phase-0 contract (a field renamed/dropped on the way into SQLite) | high | Round-trip a golden Phase-0 fixture through write→read in HSM-4-01; the test fails on any field drift | A contract field has no column and no documented reason — stop and reconcile against HSM-0-02 before adding storage-only fields |
| "Recovery after crash" is asserted from a clean shutdown, not a real mid-write kill | high | HSM-4-02 kills the process mid-write with segments in flight (SIGKILL / app-terminate), not a graceful close, and reopens | The recovery test only ever exercises a clean close — it does not prove the Gate; rebuild the test to kill mid-write |
| WAL checkpointing or file-mode (`-wal`/`-shm` companion files) behaves differently under iOS app suspension than on the dev host | medium | Demonstrate the Gate on a real iOS target, not only the simulator/host; note the suspend/background path | Recovery passes on the host but a backgrounded-then-killed app loses the last segments on device — escalate; do not close the Gate on host-only evidence |
| Versioning gets coupled to the DB `SCHEMA_VERSION` by accident, re-importing the Phase-0 risk | low | HSM-4-03 states `contract_version` and `SCHEMA_VERSION` are independent and records why | A contract bump forces a DB schema bump with no storage change (or vice-versa) — stop and decouple per HSM-4-03 |

## Decisions made (this phase)

- 2026-06-18 — Persistence is SQLite (per charter Track E), behind the Layer-3
  `IStorage` abstraction; the Runtime Core never sees SQLite directly — charter
  Track E + Architecture §Layers.
- 2026-06-18 — The mobile DB is greenfield: it ships at `SCHEMA_VERSION=1` with
  no migration ceremony and no compat shims, mirroring the desktop DB's
  greenfield posture — pre-release app, no installed base.

## Decisions deferred

- Whether `IntelJob` (and aftercare/actuator records) get their own tables in
  this phase or land with Phase 5/6 — trigger: HSM-4-01 catalog cross-check —
  default: store only the four charter entities (`Meeting`, `Segment`,
  `Artifact`, `Action`) here; add `IntelJob` only if it is a required foreign key
  for `Artifact`.
- Concrete `contract_version`↔`SCHEMA_VERSION` mapping (lockstep vs independent)
  — trigger: HSM-4-03, after HSM-0-03 fixes the contract version scheme —
  default: independent, with `SCHEMA_VERSION=1` recording which
  `contract_version` it was built against.
- Encryption-at-rest for the SQLite file — trigger: Phase 11 (Track L,
  Hardening) — default: unencrypted local file in app-sandbox storage for V1.

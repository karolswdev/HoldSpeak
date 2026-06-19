# HSM-4-01 — SQLite schema + stores

- **Project:** holdspeak-mobile
- **Phase:** 4
- **Status:** backlog
- **Depends on:** HSM-0-02, HSM-1-01
- **Unblocks:** HSM-4-02, HSM-4-03
- **Owner:** unassigned

## Problem

The Runtime Core needs somewhere to put a recorded meeting and read it back, but
nothing persists yet. The store must hold `Meeting`, `Segment`, `Artifact`, and
`Action` in shapes that match the Phase-0 `holdspeak-contracts` — if the stored
shape drifts from the contract, the mobile runtime stops being interoperable with
desktop, which is the whole point of the program. Persistence must also sit
behind the Layer-3 `IStorage` abstraction so the Runtime Core never depends on
SQLite directly.

## Scope

- **In:** a SQLite schema (`SCHEMA_VERSION=1`) with tables for `Meeting`,
  `Segment`, `Artifact`, and `Action`, every column traced to a Phase-0 contract
  field (from HSM-0-02's schemas); the relationships from the Phase-0 catalog
  drawn as foreign keys (Meeting → Segments; Artifact/Action → their owning
  Meeting; Action → Decision/Artifact provenance where the contract has it);
  read/write stores for all four entities; the `IStorage` interface (or its
  persistence-relevant surface) implemented by the SQLite store so the Runtime
  Core consumes it through the abstraction only.
- **Out:** WAL/journaling configuration and the crash-recovery proof (HSM-4-02 —
  HSM-4-01 lands the schema and stores; durability tuning is the next story). The
  version policy doc (HSM-4-03). Sync (Phase 10). Persisting `IntelJob` /
  aftercare / actuator records unless one is a required foreign key for the four
  charter entities (default: out — see phase Decisions deferred). Any host UI.

## Acceptance criteria

Checklist. Merge gate. Each item must be verifiable by reading code or running a
command:

- [ ] A SQLite schema for `Meeting`, `Segment`, `Artifact`, and `Action` exists,
      created at `SCHEMA_VERSION=1`, with no migration ladder.
- [ ] Every column maps to a Phase-0 contract field (HSM-0-02); the mapping is
      recorded (a column↔contract-field table or inline schema comments), and any
      storage-only column has a stated reason.
- [ ] Entity relationships from the Phase-0 catalog are enforced as foreign keys
      (e.g. a `Segment` cannot exist without its `Meeting`).
- [ ] A golden Phase-0 fixture (one `Meeting` with `Segment`s, `Artifact`s, and
      `Action`s) writes and reads back with zero field drift — the round-tripped
      object equals the fixture.
- [ ] All four read/write stores are reachable through the `IStorage` interface;
      a test (or a grep over the Runtime Core) shows no direct SQLite calls
      outside the storage implementation.
- [ ] Enum-valued columns (statuses, artifact type, action lifecycle state) accept
      exactly the contract's vocabulary and reject values outside it.

## Test plan

- Unit: write→read round-trip per entity, asserting object equality against the
  golden Phase-0 fixture from HSM-0-02; enum-rejection cases; foreign-key
  enforcement (orphan insert fails).
- Integration: a full meeting (Meeting + N Segments + Artifacts + Actions) is
  persisted and re-read through `IStorage` only, with no direct DB access path
  used.
- Manual / device: n/a here — durability under crash is HSM-4-02; on-device file
  placement is exercised there.

## Notes / open questions

- Depends on HSM-0-02 (the per-entity JSON Schemas) being landed — the column set
  is derived from those schemas, not re-invented here. If HSM-0-02 is not ready,
  this story is blocked, not "guessed."
- Depends on HSM-1-01 (Mobile Foundation) for the package/workspace the store
  lives in.
- Greenfield: `SCHEMA_VERSION=1`, no migrations. The version policy and the
  `contract_version` relationship are HSM-4-03's job; record the
  `contract_version` this schema was built against so HSM-4-03 can wire it up.
- Record desktop/contract field names verbatim per HSM-0-01's rule; resolve any
  casing impedance in the serialization contract (HSM-0-03), not in the SQL.
- If the catalog cross-check shows `Action` requires a `Decision` or `Artifact`
  provenance link that pulls in another entity, park the extra entity per the
  phase Decisions-deferred default rather than expanding scope silently.

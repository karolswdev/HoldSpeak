# HS-127-10 — Local-first sync

- **Project:** holdspeak
- **Phase:** 127
- **Status:** done
- **Depends on:** HS-127-09
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

A receipt that exists only on one device is not durable enough for its work.
Sync receipt records, links, revisions, and tombstones through the existing
local-first spine without turning concurrent history into silent overwrites.

### What changes

1. Register receipt records, sources, work links, revisions, and tombstones
   with `SyncService`.
2. Carry immutable revisions and supersession lineage as syncable facts.
3. Define deterministic conflict handling for concurrent receipt edits and
   link changes.
4. Retain deletion tombstones so removed records do not reappear.

## Acceptance criteria

1. Two peers converge on receipt facts, sources, work links, and revisions.
2. Concurrent edits retain both histories or produce a named resolvable state;
   neither silently wins by overwrite.
3. Tombstones propagate and prevent deleted receipt records from resurrection.
4. Sync remains local-first and preserves receipt evidence references.

## Test plan

- Sync: converge a receipt created on one peer onto another.
- Sync: create concurrent edits and assert deterministic, non-destructive output.
- Sync: propagate a tombstone and verify it does not resurrect after replay.

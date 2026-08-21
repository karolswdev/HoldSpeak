# HS-141-01 — Raw before AI

- **Status:** done
- **Depends on:** Phase 140 landing
- **Unblocks:** every Phase 141 product story

## Problem

Today FirstWords is browser-durable until Keep, Notes are mutable without CAS,
and no record can prove an immutable original beside a revisioned working draft.
Refinement cannot safely begin on that foundation.

## Scope

Add the narrow persisted refinement aggregate and transactional creation seam:
immutable raw byte snapshot/hash/source/time, one visible working Note ID and
revision, lifecycle state, attachment revision, and timestamps. Create raw +
working Note atomically with a caller-stable request ID. Add expected-revision
CAS for every working mutation and named conflict/reload behavior. The aggregate
owns Unfinished/completed presentation state. File the working Note into Inbox
through qualified directory membership. Thought-owned Notes must be writable
only through the refinement/CAS service: the canonical ordinary Note mutation
path detects ownership and requires the same expected revision or refuses.
Paired-device sync is part of that closure: an inbound mutation for a
thought-owned Note must route through the aggregate/CAS service with its expected
revision or refuse as a named conflict. Direct repository upsert is forbidden
for these Notes.

Do not add model calls, UI, proposals, generic chat, or external execution.

## Acceptance

- [x] No refinement can start until the server transaction returns the durable
  raw ID/snapshot hash and working Note revision.
- [x] Retried/ambiguous creation returns the same aggregate and Note, never a
  duplicate.
- [x] Raw remains byte-equal and has no refinement mutation API.
- [x] Two writers on one expected revision yield one success and one named
  conflict; no false success.
- [x] Generic Note PUT/upsert cannot bypass CAS for a thought-owned working Note.
- [x] Paired-device sync cannot bypass ownership/CAS through repository upsert;
  stale or revisionless inbound changes refuse without false success.
- [x] Unfinished/completed live on the refinement aggregate, not invented Note
  fields; Inbox membership uses the qualified `note:` ref.
- [x] Delete/tombstone and restart behavior are explicit and tested.
- [x] Design counsel ratifies schema, states, transitions, and concurrency matrix
  before downstream UI work.

## Tests

Focused repository/service/route tests; failure injection at transaction and
response boundaries; two-instance fresh-read/CAS; no real HOME.
Include paired-device retry, stale-revision, and revisionless-sync cases.

# HS-160-08 — Remove and Forget: barrier, purge, disclosure

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-160-03, HS-160-06, HS-160-07, HS-160-09
- **Unblocks:** HS-160-11, HS-160-12, HS-160-13, HS-160-14
- **Owner:** unassigned

## Problem

Deletion is a distributed safety operation, not a row delete. A requested
lineage must become inadmissible immediately, then all eligible local v2 copies
and derivatives must disappear through failures without expanding the owner's
Forget request to unrelated canonical truth.

## Scope

- **In:** Remove and Forget commands; atomic admission barrier; lineage and
  intersecting-operation discovery; whole-operation key shred where material
  shares an operation key; registered derivative purgers; queue/progress/
  retry/tombstone schema; owner disclosure for collateral loss of co-resident
  copied material and for legacy/provider/backup exclusions.
- **Out:** forgetting unrelated canonical sources, claiming provider deletion,
  claiming physical overwrite guarantees, and destructive schema downgrade.

## Acceptance criteria

- [ ] Remove commits intent and barrier atomically; capture, compile, retrieval,
  graph, planning, and new derivative admission reject barred lineage at once.
- [ ] Forget targets requested source/cell lineage and discovers every
  intersecting encrypted operation. Each affected per-operation key is wholly
  shredded, which may make other copied material in that envelope unavailable,
  but does not forget unrelated canonical sources or independent derivatives.
- [ ] Saga is idempotent and resumable; terminal success means zero eligible
  local in-scope v2 payloads, claims, procedure rows, embeddings, graph edges,
  caches, private receipt payload/envelopes, purgeable usage-lineage detail, and
  queued work—not universal physical zero outside HoldSpeak's authority.
- [ ] Owner-ratified content-free immutable terminal attestations/tombstones
  survive Forget with no private prose/value/query/vector/path or resolvable
  usage lineage; Forget success neither deletes nor depends on deleting them.
- [ ] Legacy remnants, provider copies, backups, and unavoidable compliance
  tombstones are separately disclosed under the owner-ratified retention law;
  none remain eligible for compile, retrieval, or model-bearing operations.
- [ ] HS-160-09 purgers preserve source/target endpoint and generation lineage;
  missing or unknown purgers fail the operation closed rather than declaring
  success.
- [ ] Progress and errors contain stable IDs/states/counts only; canary scans
  find no removed content, query, vector, prompt, or private path.

## Test plan

- **Semantics:** one source in several operations, several sources sharing one
  operation key, unrelated independent source, already-removed/missing lineage.
- **Fault:** crash/restart before/after barrier, intent discovery, destroying,
  native key deletion, each purger, queue acknowledgement, and terminal receipt.
- **Concurrency:** simultaneous plan/retrieval/source revision and duplicate
  Remove/Forget; admission barrier always wins.
- **Privacy/disclosure:** canary scan plus exact legacy/provider/backup and
  co-resident-material disclosures.

## Notes / open questions

- CF-0 §12/§15 and INV-009 are normative.
- The composed cross-store zero-eligible campaign is rerun at HS-160-14 close.

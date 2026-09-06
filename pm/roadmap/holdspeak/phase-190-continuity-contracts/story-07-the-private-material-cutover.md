# HS-190-07 — The private-material cutover: resolver and writer census

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-190-04, HS-190-05, HS-190-06
- **Unblocks:** HS-190-08, HS-190-11, HS-190-14
- **Owner:** unassigned

## Problem

An encrypted vault does not protect HoldSpeak while legacy inference tables or
feature-local readers and writers still persist private material in plaintext.
Cutover needs its own bounded PR, inventory proof, and rollback posture.

## Scope

- **In:** v2 private-material lookup/envelope references for every existing
  inference-bearing table in CF-0 scope; `PrivateMaterialService` resolver;
  generated reader/writer census; dual-read/single-v2-write transition; legacy
  disclosure; inventory/parity doctor; stopped-writer rollback and old-binary
  canonical-only fence; storage/WAL/temp/log/backup leakage scan.
- **Out:** new semantic derivatives, deleting legacy owner data automatically,
  reactivating a plaintext writer after cutover, and Remove/Forget orchestration.

## Acceptance criteria

- [ ] Every in-scope private reader/writer has a generated owner/path/status row;
  uncatalogued inference-bearing SQL or file writes fail CI.
- [ ] New writes use v2 encrypted references only. Legacy reads remain explicit,
  readable, disclosed, and redacted through the CF-0 resolver; retiring that
  reader is a separately approved migration. No crypto or resolver error falls
  back to plaintext.
- [ ] Resolver authorizes server-derived principal, operation, purpose,
  destination, scope, and lineage before returning bytes and records only a
  sanitized terminal receipt.
- [ ] Cutover doctor reconciles legacy/v2 counts, keys, envelope lineage, plan
  references, orphan rows, and unreadable material on clean and representative
  upgraded databases.
- [ ] Current-binary flags-off uses the v2 resolver while preserving legacy
  behavior. After writers stop, old binary opens canonical data only in degraded
  posture; model-bearing/adoption/plaintext-write paths are fenced.
- [ ] Canary content does not appear in public DB columns, WAL/temp snapshots,
  logs, metrics, exceptions, receipts, exports, or backup manifests.

## Test plan

- **Migration:** representative legacy corpus, dual-read/single-write, inventory
  mismatch, interrupted backfill/cutover, restart, repeated migration.
- **Census/fence:** known readers/writers plus injected uncatalogued plaintext
  writer; current flags-off and old-binary canonical-only fixtures.
- **Privacy:** resolver authorization matrix, corrupt/locked vault, sentinel scan
  of every named artifact class and sanitized legacy disclosure.

## Notes / open questions

- CF-0 §12.1, §16.1, TXN-005, and the private-table inventory are normative.
- This story changes storage wiring behind disabled CF-0 flags; it enables no
  Continuity plan injection or semantic behavior.

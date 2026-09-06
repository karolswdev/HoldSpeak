# HS-190-13 — The local proof harness: ledger, leakage, fixtures

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-190-03 through HS-190-12
- **Unblocks:** HS-190-14
- **Owner:** unassigned

## Problem

Continuity's most important promises—locality, deletion, deterministic plans,
scope fences, and product honesty—cannot be accepted from prose or scattered
test logs. The owner needs one local, sanitized, retention-bounded proof ledger
that distinguishes structural CF-0 evidence from later quality evidence.

## Scope

- **In:** `ContinuityProofService`; versioned proof event/index schema;
  requirement/story/test/artifact linkage; local retention and explicit export;
  preview/redaction; deterministic evidence bundle manifest; leakage scanner;
  fixture capture orchestration; fault-injection result ingestion; coverage and
  waiver validation; proof-store Remove/Forget behavior.
- **Out:** remote telemetry, uploading by default, owner-content snapshots,
  fabricated quality metrics, and writing story evidence before its PR ships.

## Acceptance criteria

- [ ] Every proof row names requirement, story, producer/test, result, timestamp,
  environment class, artifact digest, retention class, and sanitation status.
- [ ] Ledger and manifest never contain source text, claims, queries, prompts,
  vectors, secrets, absolute private paths, or raw crash payloads.
- [ ] Preview shows exactly what export will contain; export is explicit,
  deterministic, integrity-checkable, and disabled by default.
- [ ] Retention follows the owner ledger; Remove/Forget includes proof artifacts
  that carry barred lineage while retaining only non-identifying compliance
  tombstones authorized by that decision.
- [ ] Harness can ingest every CF-0 structural/fault fixture and reports missing,
  stale, failed, waived, or wrong-environment evidence without converting it to
  pass.
- [ ] Product captures carry required sizes/watermark and are linked to exact
  fixture/service versions; real-quality gate fields remain `not measured`.

## Test plan

- **Schema:** deterministic manifest/digest, lifecycle, waiver expiry,
  requirement coverage, stale artifact, tamper detection.
- **Privacy:** sentinel corpus across ledger, preview, export, logs, paths,
  screenshots metadata, and crash ingestion.
- **Lifecycle:** retention expiry, explicit export/cancel, Remove/Forget, locked
  vault, partial capture, restart and resumable bundle construction.
- **Product:** fixture-size/watermark/service-version verification.

## Notes / open questions

- CF-0 MEAS-001–010 and §§12.2/18 are normative.
- Roadmap `evidence-story-*.md` files remain separate write-once delivery
  records; this runtime proof ledger supplies verifiable inputs to them.

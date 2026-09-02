# HS-160-04 — The source spine: capture registry, outbox, observations

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-160-01, HS-160-02
- **Unblocks:** HS-160-03, HS-160-07, HS-160-08, HS-160-09, HS-160-11
- **Owner:** unassigned

## Problem

HoldSpeak has many truth owners—Notes, Threads, People, Projects, meetings,
Recipes, Workflows, Workbenches, Coder, files, and plugins. Polling them with
feature-local cursors creates missed deletions, duplicated revisions, and
unclear privacy lineage. CF-0 needs one loss-resistant source spine before it
can claim whole-ecosystem integration.

## Scope

- **In:** generated source/adapter registry; stable root-event and observation
  identity; transactional outbox capture where HoldSpeak owns writes; bounded
  scan/backfill contract where it does not; cursor, run, disposition, retry,
  quarantine, and reconciliation records; revision/deletion/privacy/scope/
  staleness fixtures for every registered source class; handoff law preventing
  two simultaneous writers.
- **Out:** inference, accepted claims, storing source prose in the journal,
  production connectors not already authorized by the owner, and UI.

## Acceptance criteria

- [ ] Every in-repo source owner has service/trigger ownership, capture mode,
  stable IDs, revision semantics, deletion signal, privacy class, and adapter
  status in a generated registry.
- [ ] Journal/observation rows store references, hashes, spans, and redacted
  metadata only. An authenticated adapter hydrates a canonical revision from
  its authoritative source service; only copied/admitted excerpts later cross
  the HS-160-06 `PrivateMaterialService` boundary.
- [ ] Cursor advances through the greatest contiguous sequence of
  `published|deleted|ineligible|skipped_terminal` dispositions. `retryable`
  blocks that adapter cursor; only bounded policy may deliberately emit an
  explicit, replayable `skipped_terminal`. Retries are idempotent.
- [ ] Startup and scheduled reconciliation find missing/orphaned outbox,
  observation, and cursor states and emit sanitized repair receipts.
- [ ] Backfill-to-live cutover proves no gap and no double writer per source.
- [ ] Fixtures cover revised, deleted, private, moved-scope, stale, duplicate,
  out-of-order, and unknown-adapter observations for every source class.

## Test plan

- **Registry:** generated census is deterministic and CI fails on an uncatalogued
  source owner/adapter.
- **Integration:** transaction/outbox/reconciliation over representative native
  source services; scan adapters use fixed snapshots and resumable cursors.
- **Fault:** duplicate root event, slow-drip poison event, crash at each cursor
  boundary, stale source before publication, and backfill/live handoff. A
  poison event that remains `retryable` proves the cursor cannot skip it merely
  because it has retried, while unrelated adapters continue.
- **Privacy:** canary prose never appears in journal, dispositions, or receipts.

## Notes / open questions

- CF-0 §10, GEN-001–010, and TXN-007 are normative.
- “All things HoldSpeak” is demonstrated by a generated total registry plus
  explicit status—not by pretending every source is semantically learned in
  CF-0.

# HS-160-01 - The evidence schema: observations, links, proposals, reviews

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-160-02
- **Owner:** unassigned

## Problem

Delta needs durable homes: append-only normalized observations
(§5.5, deterministic identity), evidence links (§5.6), proposals
with the full decision lifecycle (§5.7), and frozen review windows
(§5.8). DB-001..005 govern; the IDs come from project_contracts
(pobs_/pprop_ deterministic, prev_ unique).

## Scope

- **In:** schema v69 (additive): `project_observations` (§5.5 —
  UNIQUE on the deterministic identity so adapter retries no-op;
  append-only, supersedes_observation_id for corrections — DB-003),
  `project_evidence_links` (§5.6), `project_proposals` (§5.7 —
  lifecycle open|accepted|deferred|dismissed|superseded|failed,
  dismissal_basis_hash, deferred_until, review_window_key),
  `project_reviews` (§5.8 — from/through sequences,
  source_manifest_json, opened/accepted revisions). Indexes for
  bounded reads. Repo helpers (named columns; conn-accepting
  variants where the review-accept transaction will need them —
  the 159 M-1 law learned). Snapshot regen per the literal-\s+
  gotcha. Real-DB-copy proof (the 158/159 pattern, CI-skip clean;
  run by the orchestrator with real HOME).
- **Out:** §5.9 project_updates (P3), any service logic (02+).

## Acceptance criteria

- [ ] Legacy + real-DB-copy reconcile clean, idempotent; snapshot diff confined to new lines; named INSERTs; fences green.
- [ ] Observation identity law provable at the schema level: same (adapter, source identity, source version, fact key) → UNIQUE conflict resolves to no-op (DB-002/§5.5).
- [ ] Proposal + review shapes carry every §5.7/§5.8 field; 157/158/159 suites untouched-green.

## Test plan

- **Unit:** `tests/unit/test_delta_schema.py` (fresh/legacy/real-copy, uniqueness laws); test_db snapshot legs; positional-INSERT fence.

## Notes / open questions

- pobs_/pprop_ generators already take the determinism inputs (P0's frozen signatures) — the schema's UNIQUE constraints must agree with THOSE inputs exactly.

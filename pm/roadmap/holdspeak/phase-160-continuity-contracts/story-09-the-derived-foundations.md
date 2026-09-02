# HS-160-09 — The derived foundations: procedures, generations, graph

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-160-02, HS-160-03, HS-160-04, HS-160-06
- **Unblocks:** HS-160-08, HS-160-10, HS-160-13
- **Owner:** unassigned

## Problem

Core Memory must eventually support semantic recall, related-memory graph
traversal, and learned procedures. Those derivatives are dangerous unless
their lineage, version, invalidation, and swap semantics exist before a real
model writes them.

## Scope

- **In:** embedding-generation registry and manifests; model/dimension/metric/
  normalization/route/license fields; build/verify/swap/retire state machine;
  active-generation contract; derivative lineage/invalidation queues; graph node,
  edge, path, provenance, and scope fences; procedure candidate/version/status/
  adapter contracts; sealed `memory.embed`, `memory.rerank`,
  `memory.claim_extract`, and `memory.claim_consolidate` capability contracts.
  `memory.continuity_brief@1` contract/schema and evidence-backed fake
  publication/validation fixtures complete the five-contract set.
  Deterministic fake vectors/candidates live only in isolated test doubles or
  rollback-clean development fixtures; production runtime lands schemas and
  validators only, with generation/projection tables empty.
- **Out:** choosing a model or vector database, production embeddings, semantic
  ranking thresholds, production chunk/vector writer or reader, an active fake
  generation or semantic flag, executing learned procedures, and automatic publication.

## Acceptance criteria

- [ ] Every derivative identifies exact source/claim version, generation,
  policy/privacy version, producer, egress grant, root-event taint/trust,
  created time, and revocation state; graph edges bind both endpoint head tuples.
- [ ] Generation contracts require isolated build, verify-before-atomic-swap,
  and rejection of mixed dimensions/generations. CF-0 exercises this only in an
  isolated fake repository; production contains no declared or active fake
  generation, and rollback-clean fixtures leave no generation row behind.
- [ ] Dimension, finite-value, count/order, normalization, and lineage checks
  reject wrong, NaN/Inf, zero, reordered, stale, or orphaned fake vectors.
- [ ] Source edit/delete, privacy change, Project membership change, correction,
  destination/egress change, taint downgrade, and Forget invalidate affected
  derivatives before retrieval/top-K admission, with authorization joins over
  source and target endpoint heads rather than post-filtering.
- [ ] Procedure, graph, and embedding purgers implement HS-160-06's registered
  interface, preserve resumable lineage progress, and reach zero real derivative
  rows through injected crash/restart.
- [ ] Graph traversal applies authorization at every node and edge; an allowed
  start cannot cross to a barred scope through an intermediate edge.
- [ ] Procedure candidates stay proposals until an owner-authorized adapter and
  explicit acceptance exist; fake candidates cannot execute an action.
- [ ] Every fake derivation invocation uses the existing admitted-operation law,
  encrypted input/output envelopes, hard output caps, and terminal sanitized
  receipts; invalid extras/output, privilege/tool-target text, slow-drip taint,
  or route/egress refusal publishes zero derivative rows.
- [ ] `memory.continuity_brief@1` binds the exact evidence/claim heads, scope,
  policy/privacy/egress versions, template/schema version, output cap, and
  terminal receipt; missing/stale evidence or invalid fake output publishes no
  `continuity_briefs` row.

## Test plan

- **State/constraint:** every generation/procedure transition and invalid edge.
- **Fault:** build/swap crash, activation race, purge crash/resume, missing
  lineage, stale source before publication, concurrent invalidation.
- **Representation:** wrong dimension, NaN/Inf/zero, count/order mismatch,
  mixed generation, deterministic fake-vector reconstruction.
- **Graph/privacy:** multi-hop cross-scope attacks, independent source/target
  head invalidation, membership/egress revocation, taint downgrade and slow drip.
- **Admission:** sealed capability IDs, encrypted envelopes, terminal receipts,
  all five revision-1 contracts including continuity brief, output caps,
  invalid proposal extras, tool-target text, and zero publication.

## Notes / open questions

- CF-0 §5.4 and §13 are normative.
- These are production-grade contracts exercised only through isolated
  non-semantic test doubles or rollback-clean development fixtures. CF-1
  supplies measured models/backends and the first production projections
  without changing their safety grammar.

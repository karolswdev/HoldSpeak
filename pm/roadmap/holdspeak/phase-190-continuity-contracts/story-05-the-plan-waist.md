# HS-190-05 — The plan waist: policy, allocation, freeze, kernel binding

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-190-02, HS-190-03, HS-190-06
- **Unblocks:** HS-190-07, HS-190-10, HS-190-11
- **Owner:** unassigned

## Problem

If Ask, Threads, Recipes, Coder, and future capabilities each assemble memory
independently, privacy, scope, budgets, and correction behavior will drift.
Continuity requires one narrow, immutable planner artifact between owner policy
and every model-capable consumer.

## Scope

- **In:** versioned policy registry; purpose/destination/scope authorization;
  frozen source and claim inputs; tokenizer binding; deterministic allocation,
  ordering, truncation, disclosure, and exclusion reasons; assignment/route
  binding; `ContinuityPlan@1` schema, canonical bytes, digest, receipt, and
  pure preview/shadow validator; broker-owned execution binding fixture;
  deterministic fake tokenizer/runner for CF-0. Persisted private plan material
  uses the HS-190-06 encrypted envelope—there is no plaintext interim store.
- **Out:** vector search, real embeddings/reranking, relevance-quality claims,
  dynamic prompt rewriting, and production context injection.

## Acceptance criteria

- [ ] Planner input names capability, operation, purpose, destination, scope,
  server-derived principal/authority, assignment/route snapshot, policy
  version, source/claim revisions, tokenizer, and hard input/output/privacy
  budgets; caller-supplied actor claims have no authority.
- [ ] Same frozen input produces byte-identical plan and digest; changed policy,
  source revision, destination, tokenizer, or budget changes the digest.
- [ ] Included items carry qualified ref, exact revision/version, lineage,
  rendered byte/token counts, disclosure, and deterministic rank/order;
  exclusions carry stable non-sensitive reason codes.
- [ ] Budget arithmetic is tokenizer-exact and fails closed on overflow,
  unavailable tokenizer, unknown destination, stale revisions, or barred lineage.
- [ ] Preview/shadow plans use pure closed validation and are never
  kernel-bound. A fake `purpose=execution` fixture alone proves that the broker
  can bind a valid policy-matching plan to a kernel-minted child `op_*`; no real
  CF-0 shadow adapter can request or obtain that binding or injectable text.
- [ ] Receipts contain IDs, digests, counts, timing buckets, and reasons—not
  source text, queries, vectors, rendered prompts, or filesystem paths.

## Test plan

- **Golden:** representative direct/conceptual/related none-policy plans,
  composite scope, mixed destinations, exact boundary/over-budget cases.
- **Property:** determinism, permutation resistance where order is not semantic,
  monotonic caps, digest sensitivity, no barred/stale lineage.
- **Fault:** route with cloud fallback denied, tokenizer mismatch/unavailable,
  policy changes between plan and admission, timeout and cancellation.
- **Fence:** static/runtime proof that CF-0 exposes no plan text to a production
  model call.

## Notes / open questions

- CF-0 §8, TXN-005, INV-010/011 are normative.
- Model/vector selection remains CF-1; CF-0 makes that future choice explicit,
  reproducible, and unable to bypass policy.

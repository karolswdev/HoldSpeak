# HSEGHS001HS104-143-05 - Frozen Route Plans

- **Project:** holdspeak
- **Phase:** 143
- **Status:** done
- **Depends on:** 143-02, 143-03, 143-04
- **Unblocks:** 143-06 through 143-10
- **Owner:** unassigned

## Problem

A mutable assignment cannot authorize execution. Every parent must freeze exact capability, profile, binding, deployment, boundary, budget, and per-leg context truth before first egress.

## Scope

### In

- Implement the one canonical `InferenceRoutePlan@1` and pure server resolver;
  `ResolvedCapabilityRoutePlan` is not a second table or DTO.
- Freeze content-free route chains separately from private per-operation
  admitted-request plans; one-shot work creates both atomically, while each
  later meeting/tool child plans from its own immutable material snapshot.
- Adapt legacy one-target callers to one-leg plans without behavior change.
- Persist content-free plan evidence and reconstruct it after restart.
- Keep route-leg ordinal distinct from physical-attempt ordinal.

### Out

- No controller advance between legs.
- No prompt, Note, transcript, key, endpoint credential, or local path in plan rows/projections.

## Acceptance criteria

- [x] Profile/assignment/capability/route changes after freeze affect only the next parent.
- [x] Different tokenizer/template legs never reread, truncate, summarize, or mutate material.
- [x] Legacy target overrides become explicit one-leg plans before admission.
- [x] Route resolution performs no network, scan, probe, model load, or write and meets 10 ms p95 target.
- [x] Every physical child binds plan hash, leg ordinal, attempt ordinal, and exact DeploymentRevision.
- [x] Operation plans retain every leg's frozen eligibility; only executable
  legs carry admitted-request/context/serialized-request hashes.

## Test plan

- Mutation-after-freeze, later meeting/tool material, restart, tamper,
  lower/larger-context legs, Unicode/template drift.
- Dialect retry plus later route leg produces unique child identities.
- Zero-write/network/load census and route-resolution performance fixture.

## Implementation notes

- Follow [architecture-contract.md](./assets/architecture-contract.md), [owner-experience.md](./assets/owner-experience.md), and [repository-census.md](./assets/repository-census.md).
- Product code, schema, inventories, migrations, tests, and evidence land in this story; status changes only after the evidence ledger exists.
- Preserve unrelated dirty-worktree changes and do not create a second inference gateway, execution revision registry, or owner authority.

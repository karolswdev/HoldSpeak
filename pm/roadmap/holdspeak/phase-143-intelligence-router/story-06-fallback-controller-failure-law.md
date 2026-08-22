# HSEGHS001HS104-143-06 - Fallback Controller and Failure Law

- **Project:** holdspeak
- **Phase:** 143
- **Status:** backlog
- **Depends on:** 143-05
- **Unblocks:** 143-07 through 143-10, 143-14
- **Owner:** unassigned

## Problem

Fallback must be a durable server decision, not a provider retry, browser loop, or hopeful Config list. Unknown physical outcomes and effects make blind advancement unsafe.

## Scope

### In

- Implement RouteAttemptController above InferenceRunner with durable plan/attempt ledgers.
- Centralize closed disposition classification and bounded retry/fallback policy.
- Consume the immutable retry-policy registry from Story 02 and implement its
  runtime classification, reservation, budget, and terminal behavior.
- Reserve each leg/attempt transactionally with Stop, deadline, and budget fencing.
- Adopt existing receipts after crash; never reconstruct from current settings.
- Retire or rename fake workflow fallbackOnDevice/retryThenQueue semantics.
- Retire the Swift `WorkflowRunner`/`BlueprintInterpreter` client-owned
  retry/fallback loops or route every one of their physical attempts through
  the same durable server controller and `InferenceRunner` child law.

### Out

- No engine/provider hidden retry.
- No fallback after refusal, authority failure, cancellation, deadline,
  integrity, unclassified/unsafe context failure, or indeterminate completion.
  Planning-time `context_overflow` may advance only to an already exact-planned
  larger leg under explicit policy.

## Acceptance criteria

- [ ] Every provider-reaching try is a separately admitted inference.invoke@1 child.
- [ ] Known eligible failure advances exactly once; all forbidden dispositions create zero later egress.
- [ ] Local-to-cloud advance requires frozen saved disclosure and appears in receipt.
- [ ] Crash after failed receipt resumes once; unknown completion becomes indeterminate.
- [ ] RouteExecutionReceipt explains considered/attempted legs, dispositions, actual model/boundary, and terminal truth.
- [ ] Runner obtains a controller-backed durable reservation before any primary,
  retry, or dialect-compatibility physical child; Stop/deadline/budget fences it.
- [ ] Post-send timeout/disconnect is unknown and creates zero retry/fallback.
- [ ] “All N models failed” renders only when all N physically attempted and
  failed; skipped/unavailable entries use distinct receipt-driven copy.

## Test plan

- Disposition/policy table at budget -1/equality/+1, including primary overflow
  to larger planned leg and post-admission context drift refusal.
- Pre-send failure, explicit 429, post-send timeout/disconnect, missing key, and
  unavailable-leg fixtures.
- Local lease saturation at preflight, capacity return, and exact
  `local_capacity_unavailable` disposition.
- Stop/result, deadline/result, concurrent controller, lost response, every crash boundary.
- One-path monkeypatch census and exact 0/1/N child cardinality.

## Implementation notes

- Follow [architecture-contract.md](./assets/architecture-contract.md), [owner-experience.md](./assets/owner-experience.md), and [repository-census.md](./assets/repository-census.md).
- Product code, schema, inventories, migrations, tests, and evidence land in this story; status changes only after the evidence ledger exists.
- Preserve unrelated dirty-worktree changes and do not create a second inference gateway, execution revision registry, or owner authority.

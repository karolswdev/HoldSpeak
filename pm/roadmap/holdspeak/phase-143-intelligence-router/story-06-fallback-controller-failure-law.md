# HSEGHS001HS104-143-06 - Fallback Controller and Failure Law

- **Project:** holdspeak
- **Phase:** 143
- **Status:** done
- **Depends on:** 143-05
- **Unblocks:** 143-07 through 143-10, 143-14
- **Owner:** unassigned

## Problem

Fallback must be a durable server decision, not a provider retry, browser loop, or hopeful Config list. Unknown physical outcomes and effects make blind advancement unsafe.

## Scope

### In

- Implement the one canonical `InferenceFallbackController` above
  `InferenceRunner` with durable plan/attempt ledgers.
- Centralize closed disposition classification and bounded retry/fallback policy.
- Consume the immutable retry-policy registry from Story 02 and implement its
  runtime classification, reservation, budget, and terminal behavior.
- Reserve each leg/attempt transactionally with Stop, deadline, and budget fencing.
- Adopt existing receipts after crash; never reconstruct from current settings.
- Retire or rename fake workflow fallbackOnDevice/retryThenQueue semantics.
- Retire the Swift `WorkflowRunner`/`BlueprintInterpreter` client-owned
  retry/fallback loops or route every one of their physical attempts through
  the same durable server controller and `InferenceRunner` child law.
- Compose routed execution behind one sealed server-owned activation seam.
  Generic legacy `InvocationRequest` material cannot manufacture a capability,
  exact context plan, provider serialization, or token/tool/cost evidence.
  Therefore current v1 callers remain an enumerated temporary exception until
  their owning adopter story freezes that evidence and activates its route.

### Out

- No engine/provider hidden retry.
- No fallback after refusal, authority failure, cancellation, deadline,
  integrity, unclassified/unsafe context failure, or indeterminate completion.
  Planning-time `context_overflow` may advance only to an already exact-planned
  larger leg under explicit policy.

## Acceptance criteria

- [x] Every provider-reaching try for an activated v2 route is a separately
  admitted `inference.invoke@1` child with a controller reservation. Current v1
  exceptions are census-pinned; Stories 07/08/10 remove them by capability and
  Story 13 removes the final exception.
- [x] Known eligible failure advances exactly once; all forbidden dispositions create zero later egress.
- [x] Local-to-cloud advance requires frozen saved disclosure and appears in
  receipt. The controller's frozen-boundary integrity law is proven here; a
  lawful activated local-to-cloud traversal and the corresponding unsaved
  zero-egress fixture are proven by Story 07's first production adopter. See
  [Story 06 evidence](./evidence-story-06.md).
- [x] Crash after failed receipt resumes once; unknown completion becomes indeterminate.
- [x] RouteExecutionReceipt explains considered/attempted legs, dispositions, actual model/boundary, and terminal truth.
- [x] In activated routed mode, Runner obtains a controller-backed durable
  reservation before every primary, retry, or dialect-compatibility physical
  child; Stop/deadline/budget fences it. Routed mode fails closed when its
  composed runtime or admitted-evidence owner is unavailable.
- [x] Post-send timeout/disconnect is unknown and creates zero retry/fallback.
- [x] “All N models failed” renders only when all N physically attempted and
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
- Fail-closed activation census: no public request may supply a controller;
  production has zero accidental routed egress before an adopter is composed;
  every remaining v1 entrance is explicitly enumerated.

## Implementation notes

- Follow [architecture-contract.md](./assets/architecture-contract.md), [owner-experience.md](./assets/owner-experience.md), and [repository-census.md](./assets/repository-census.md).
- Product code, schema, inventories, migrations, tests, and evidence land in this story; status changes only after the evidence ledger exists.
- Preserve unrelated dirty-worktree changes and do not create a second inference gateway, execution revision registry, or owner authority.

## Evidence

- The canonical `InferenceFallbackController` reconstructs the exact frozen
  Story 05 operation/route pair and Story 02 policy in one transaction. It
  reserves distinct route-leg and physical-attempt ordinals under durable
  Stop, deadline, per-leg, total-attempt, and token fences.
- Activated routed attempts use a composition-owned `RoutedAttemptRuntime`;
  requests carry only a server-minted one-shot reservation. Claim, child bind,
  dispatch intent, settlement, Stop, and reconciliation are idempotent durable
  transitions. The remaining v1 entrances are census-pinned exceptions for
  the adopter stories, not a generic fallback adapter.
- Every provider-reaching attempt is an admitted `inference.invoke@1` child.
  Kernel terminal receipts are HMAC-attested, while a one-shot Runner evidence
  capability binds the closed signal and send phase; ordinary node callers
  cannot forge retry/fallback authority.
- The closed failure law covers compatibility and known-no-generation retry,
  permanent and local-capacity fallback, permission/refusal/cancel/deadline
  terminals, planning-time larger-context advancement, and conservative
  post-send unknown handling. SDK retries are disabled at both OpenAI-compatible
  provider leaves.
- `RouteExecutionReceipt@1` is restart-readable and reconstructs frozen profile,
  deployment, boundary, considerations, physical/possible-start truth, winning
  attempt, and the exact all-models-failed condition without rereading current
  assignments. A boundary crossing can only originate in the frozen chain;
  Stories 07/08/10 own activation with their exact cloud/local evidence.
- New route execution, transition, attempt, skip, budget, command, receipt, and
  kernel-attestation authorities are immutable, integrity-reconstructed, and
  explicitly refused by sync. The canonical schema snapshot and one-path
  capability/routing/surface censuses were regenerated and verified.
- Verification on 2026-08-22: the integrated controller, Runner, route-plan,
  schema, provider, dictation, endpoint-health, and census matrix reports
  `225 passed`; the focused controller/census/schema gate reports `148 passed`.
  The literal documented Ruff 0.16.4 command reports no findings and
  `git diff --check` is clean.

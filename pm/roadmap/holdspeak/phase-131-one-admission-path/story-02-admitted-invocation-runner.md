# HS-131-02 — The admitted invocation runner

- **Project:** holdspeak
- **Phase:** 131
- **Status:** done
- **Depends on:** HS-131-01
- **Unblocks:** HS-131-03, HS-131-04, HS-131-05, HS-131-07, HS-131-08, HS-131-09
- **Owner:** unassigned

## Problem

`RunLifecycle` can describe one outer UI run, but it does not own every provider
call. Most callers still resolve a target, call a model, and then optionally
write a receipt around that work. This allows direct execution, hidden fallback
calls, post-hoc cancellation, and domain-specific lifecycle forks.

## Scope

### In

- Add a typed child operation for an actual model dispatch, distinct from the
  outer domain run or session. Retain `inference.run` where it truthfully names
  an outer run; register an invocation operation with explicit parent or
  session causation, deployment revision, definition origin, deadline, and
  attempt ordinal.
- Model definition origin as a typed choice between a saved definition with a
  real revision and a versioned service contract such as Ask. Do not invent a
  fake saved definition or weaken revision validation for every caller.
- Add one inference runner/gateway that owns child admission, claim, exact-
  revision engine construction, provider dispatch, cancellation/deadline
  propagation, and one terminal receipt. It returns a domain result reference
  or typed terminal outcome; it does not shape Ask, Workbench, Sequence,
  Workflow, meeting, or dictation domain records.
- Treat every provider dispatch reached by retry or fallback as another actual
  invocation with its own operation and terminal receipt.
- Make cancellation cooperative where an adapter supports it. Gate result
  publication atomically so output arriving after cancellation cannot become a
  domain answer, artifact, memory, or step result. If the provider outcome
  cannot be known, close as `indeterminate` rather than guessing.
  *Amended 2026-08-09 (Sol counsel, orchestrator sustained; owner may
  overrule at the sitting):* the in-process publication gate, the atomic
  kernel transition-plus-receipt transaction, and defined publish-failure
  semantics ship here. The durable cross-table staging protocol for the
  crash window between an arbitrary caller's domain write and the runner's
  terminal receipt is deferred to **HS-131-03 as its blocking acceptance
  criterion** — one shared projection-staging primitive established before
  the first production caller migrates, required by every later domain
  migration story, with crash-recovery tests (stage-before-terminal,
  crash-after-stage-before-receipt, cancellation-after-stage, interrupted
  finalization, idempotent recovery). No caller may substitute a direct
  domain write under the runner's process lock.
- Preserve the existing immutable-receipt rule in
  `holdspeak/kernel/executor.py:43-69`: an identical repeated receipt is
  idempotent; a changed terminal result is refused.
- Keep prompts, tokens, audio frames, and streamed chunks out of the journal.
- Preserve `external_egress` as its own causally linked effect when a provider
  call crosses a boundary. Its operation/receipt neither replaces nor
  double-counts the invocation child and invocation receipt.

### Out

- Migrating every domain caller in this story. One reference adapter and a
  synthetic integration call prove the runner; following stories move callers.
- Domain-specific retry policy or result formatting.
- New approval UI. The owner's direct gesture and existing consent surfaces
  remain the authority sources.

## Acceptance criteria

- [ ] One public inference runner owns the complete path from invocation
  admission through provider dispatch to terminal receipt.
- [ ] A provider cannot be called by the runner before the invocation child is
  admitted and claimed against the captured deployment revision.
- [ ] Success, refusal, failure, cancellation, and indeterminate outcome each
  create exactly one immutable terminal receipt.
- [ ] Two provider calls caused by a fallback produce two admitted invocation
  children and two terminal receipts, not one logical receipt hiding both.
- [ ] Saved definitions carry their persisted revision; ad-hoc service calls
  carry an explicit service-contract revision and immutable request payload
  hash. Neither form lies about the other.
- [ ] Cancellation reaches the provider adapter when possible, prevents late
  result publication, and closes the child once. A non-reconcilable provider
  closes indeterminate.
- [ ] The runner authenticates/derives principal and authority through the
  kernel context. A caller cannot assert owner authority or placement.
- [ ] Every invocation admission and claim validates current parent/session,
  delegation, expiry, and revocation state. Immutable authority basis never
  becomes cached permission to execute after the right is revoked.
- [ ] Runner code contains no branch on product surface or domain type.
- [ ] A remote provider call has one invocation child/receipt plus its existing
  causally linked egress effect/receipt; neither lifecycle substitutes for the
  other.
- [ ] Journal tests prove no prompt body, token stream, audio frame, or model
  output body is stored.

## Test plan

- Unit: `uv run pytest -q tests/unit/test_inference_kernel.py tests/unit/test_kernel_broker.py` plus new runner tests for every terminal outcome, fallback cardinality, service-contract origin, and late-output rejection.
- Integration: `uv run pytest -q tests/integration/test_kernel_real_hub.py` with one local reference invocation and one cancelled streaming invocation.
- Manual / device: run one real LAN invocation, inspect parent/child causation,
  cancel another during output, and verify the late result is absent.

## Notes / open questions

The implementation may version `inference.run` or introduce a separate
`inference.invoke` operation. The non-negotiable contract is semantic: outer
run/session and actual provider dispatch are distinct, and dispatch cardinality
must equal child-admission and terminal-receipt cardinality.

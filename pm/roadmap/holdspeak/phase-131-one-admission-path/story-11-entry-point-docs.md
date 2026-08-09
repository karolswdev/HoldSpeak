# HS-131-11 — The entry-point contract

- **Project:** holdspeak
- **Phase:** 131
- **Status:** backlog
- **Depends on:** HS-131-10
- **Unblocks:** HS-131-12
- **Owner:** unassigned

## Problem

Phase 131 changes the meaning of an inference run, cancellation, scheduled
authority, and session admission. If the entry points still describe one outer
run receipt or imply that the scheduler acts as the owner, the product remains
hard to integrate against even when the code is correct.

## Scope

### In

- Update `README.md`, `docs/ARCHITECTURE.md`,
  `docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md`, `docs/SECURITY.md`, and
  `docs/MODELS.md` at the places where callers, operators, and integrators first
  learn how inference runs.
- Document the distinction between parent run/session, actual invocation child,
  immutable deployment revision, domain result reference, and terminal receipt.
- Document the truthful Ask service-contract revision versus saved Agent
  definition revision.
- Document meeting/dictation/configured-wake per-session authority, including
  shared local Whisper and pre-session preload/warmup authority, with one child
  per actual model call, live
  validity/revocation checks on each child, and no token/audio/prompt journaling.
- Document bounded schedule delegation: exact work/target/cadence, scheduler as
  actor, owner as delegator, invalidation on edit/disable, and named refusals.
- Document cancellation, late-output rejection, retry/fallback cardinality, and
  indeterminate outcomes.
- Document the Python/web sync registry as authoritative. State plainly that no
  Swift work or Swift-driven compatibility contract is part of this phase.
- Update API/manifests or generated snapshots only where production routes or
  schemas actually changed; run their drift guards.

### Out

- Product-language consolidation from Phase 133.
- New user-facing prose in the Desk.
- Marketing claims, release ceremony, or Swift migration instructions.
- A copy of implementation details in every document. Each entry point links to
  one canonical architecture contract.

## Acceptance criteria

- [ ] All five entry points agree on one inference runner and one receipt per
  actual provider dispatch.
- [ ] Parent/child/session, deployment revision, cancellation, fallback, and
  indeterminate semantics match shipped code and tests.
- [ ] Security documentation distinguishes scheduler actor from owner delegator
  and names exact delegation bounds and revocation behavior.
- [ ] Meeting/dictation/wake docs state per-session authority, per-invocation
  child receipts, and live revocation checks without implying audio or token
  journaling or exempting local Whisper.
- [ ] Sync documentation names the Python/web registry as authority and contains
  no instruction to shape the contract around Swift.
- [ ] Every command, route, schema, operation name, and claim is verified against
  current code; stale direct-call claims are removed.
- [ ] Documentation and API-surface drift guards pass.

## Test plan

- Unit: focused docs/schema/API-surface guards, including
  `uv run pytest -q tests/unit/test_api_surface.py tests/unit/test_primitive_contract.py` where present in the current tree.
- Integration: n/a; HS-131-12 proves the documented runtime contract.
- Manual / device: read the five entry points in order as an integrator and
  verify that each can answer who acts, what was admitted, which deployment ran,
  and where the receipt lives.

## Notes / open questions

This dedicated docs story lands after the mechanical fence. Documentation must
follow the proven execution boundary rather than describing the intended design
before migration finishes.

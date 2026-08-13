# HS-131-13 — Residual services take the admitted door

- **Project:** holdspeak
- **Phase:** 131
- **Status:** ready
- **Depends on:** HS-131-02, HS-131-06, HS-131-07
- **Unblocks:** HS-131-10
- **Owner:** unassigned

## Problem

The final fence found three service-side intelligence paths outside the admitted
runner: Cadence request-time planning, a second Decisions route, and dormant
Delivery PR review. They share `build_intel_for_target`, a mutable-target legacy
factory that cannot prove the claimed child, frozen deployment revision, or
terminal receipt required by Constitution Articles V.2 and XI.2–3.

## Scope

### In

- Migrate `holdspeak/services/cadence_service.py:_cadence_llm` under an
  authenticated Cadence domain parent and one `inference.invoke@1` child per
  physical provider attempt. Preserve the distinction established by HS-131-06:
  request-time Cadence intelligence is not scheduler authority and may not
  manufacture an owner principal.
- Delete the duplicate model seam in `holdspeak/web/routes/decisions.py` by
  routing it through the admitted Decision promotion service, or remove it if it
  duplicates that service contract. Do not create a second Decision parent or
  projection protocol.
- Delete dormant `DeliveryService.prepare_pr_review` if unreachable; otherwise
  route it through the admitted Delivery review parent, frozen revision, staged
  publication, and terminal receipt established by HS-131-07.
- Remove `build_intel_for_target` and every `LEGACY_UNCONTEXTUAL` call site once
  the last caller leaves. The validating exact-revision factory remains the only
  construction path.
- Keep domain shaping and persistence in the owning services. The generic runner
  must not branch on Cadence, Decision, or Delivery types.
- Add the three families to the fifteen-surface provenance/cardinality harness
  where they represent distinct real invocations, then remove their
  `NAMED_FINDINGS` pins from the census.

### Out

- Cadence UI, loop semantics, schedule cadence, or new scheduled authority.
- A second Decision or Delivery implementation.
- Compatibility wrappers around `build_intel_for_target`.
- Any constitutional exception or allowlist entry for a service or route.

## Acceptance criteria

- [ ] Cadence model work has an authenticated domain parent, frozen deployment
  revision, one invocation child per physical attempt, and one immutable
  terminal receipt; it never authenticates as the owner or scheduler by default.
- [ ] The Decisions route reaches the existing admitted Decision service or is
  deleted; no route-held engine or `run_prompt` callable remains.
- [ ] Dormant Delivery review is deleted or reaches the existing admitted
  Delivery parent and staging protocol.
- [ ] `build_intel_for_target`, its `LEGACY_UNCONTEXTUAL` marker, and every
  executable caller are absent.
- [ ] Cancellation or parent invalidation prevents late Cadence, Decision, or
  Delivery output from publishing.
- [ ] The one-path census removes `cadence`, `decisions-route`,
  `delivery-legacy-factory`, and the related `legacy-uncontextual-factory`
  sites without adding an adapter exception or unregistered site.

## Test plan

- Unit: focused Cadence, Decision, Delivery, exact-revision factory,
  provenance, cardinality, cancellation, and one-path census suites.
- Mutation: reintroduce a bound `run_prompt` in a route and a call to
  `build_intel_for_target`; prove the exact `UNREGISTERED_MODEL_EXECUTION`
  failures, then restore green.
- Integration: exercise each retained service entry through its production
  route/service boundary and inspect parent, child, revision, projection, and
  terminal receipt rows.
- Manual / device: n/a; HS-131-12 performs the assembled live-model proof.

## Notes / open questions

Deletion is preferred when the Decisions or Delivery seams duplicate shipped
services. “Dormant” does not make model construction exempt from Article XI.

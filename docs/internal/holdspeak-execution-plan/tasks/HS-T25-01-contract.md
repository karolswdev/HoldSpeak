# HS-T25-01 · Set the effective person-review contract

**Characterization/decision task; implementation not assigned.** Depends on [HS-T00](HS-T00-baseline.md). Parent: [HS-S25](../stories/HS-S25-current-person-review.md). G-REVIEW/G25 remain one pending local gate.

## Mandatory context

[Safety](../AGENT_START.md#authority-and-checkout-safety); story [policy](../stories/HS-S25-current-person-review.md#g25-local-policy-choices), [design](../stories/HS-S25-current-person-review.md#narrow-target-design), [matrix](../stories/HS-S25-current-person-review.md#acceptance-matrix) and [rollback](../stories/HS-S25-current-person-review.md#rollback-and-stops); [V25](../VALIDATION.md#v25-current-person-review-verification); [I16/I18/I21/I22](../INVARIANTS.md); current root/backend/test guides. No whole-library reading.

## Work

1. Revalidate provider normalization, source cache quality, direct read, launch projection, Program gate, owner/direct runner merge and visible reader symbols. Record normalized facts versus omitted evidence and exact target identity. Identify any drift that already removes the latch.
2. Resolve A latest-applied usable observation versus sticky historical alternative. For A, explicitly accept malformed/unknown handling, matching-changes precedence, provider-reported approval across a newly observed head, no new TTL/live read, legacy-unverified behavior and local application-order meaning. Strict reviewed-commit evidence is a different branch.
3. Freeze the additive row/source read association and per-launch observation application contract. Demonstrate how direct-view cache mutation cannot be mistaken for a source sweep's successful snapshot. Exact field names are proposed, not a new global registry.
4. Freeze admission limits: historical boolean is never the fallback; shared read-only runner gate; URL target; durable-marker repeat guard; no new lock semantics or exactly-once promise. Explicitly accept unsolved simultaneous-before-marker and command-before-persistence windows, or stop for the stronger design.
5. Separate feedback from gate truth. Preserve timestamp/seen dedup and recorded words while naming skipped/failed/unknown delivery; no new replay loop. Freeze meaningful change announcements and current wait/report/turn wording.
6. Establish the exact V25 ownership and real-producer/fake-provider test setup. Source review is not baseline execution. Characterization tests need an assigned checkout and test authority; verify all local Git remotes and machine/provider opt-outs first.

## Acceptance and stops

Return accepted or unresolved G25 choices, exact producer/consumer/target map, allowed paths, actual baseline status and proof gaps in the [completion report](../COMPLETION_REPORT_TEMPLATE.md). No app mutation is intended without separate test assignment. Unresolved semantics, unsafe provider fallback, required schema/locking changes or source drift blocks dependent implementation. Preserve other work; no read-only rollback is needed.

# HS-126-06 — Identify owner decisions

- **Project:** holdspeak
- **Phase:** 126
- **Status:** backlog
- **Depends on:** HS-126-02
- **Unblocks:** HS-126-07
- **Owner:** unassigned

## The thesis (the bar)

The brief must lead with what only the owner can decide. Rank active
authorization and decision work above passive receipts, so the desk asks for
judgment instead of merely recounting activity.

### What changes

1. Collect pending authorization proposals.
2. Collect decision-lifecycle reviews that require owner action.
3. Include urgent loops when they call for an owner decision.
4. Apply one deterministic priority policy: authorization proposals,
   decision reviews, and urgent loops lead passive receipts.
5. Emit cited decision candidates with their available action or review path.

## Acceptance criteria

1. Pending authorization proposals appear as owner decisions.
2. Decision-lifecycle reviews requiring action appear as owner decisions.
3. Urgent decision-bearing loops outrank passive receipts.
4. Items that are informative but require no owner action do not displace
   active decisions.
5. Each item preserves source provenance and a usable action path.

## Test plan

- Unit: rank proposals, lifecycle reviews, urgent loops, and passive receipts.
- Unit: assert non-actionable records are excluded or ranked below decisions.
- Unit: assert deterministic tie-breaking and source references.
- Integration: collect from persisted actuator, decision, and loop fixtures.

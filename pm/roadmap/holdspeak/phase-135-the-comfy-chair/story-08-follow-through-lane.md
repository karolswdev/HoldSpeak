# HS-135-08 — The Follow-Through lane

- **Project:** holdspeak
- **Phase:** 135
- **Status:** done
- **Depends on:** HS-135-05
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

What you owe, second lane: NOW/OVERDUE first, at a glance, one verb to
act — and the forward door for Wave 2's manual commitments.

## Scope

### In

- The lane composes the Follow-Through board's NOW + OVERDUE (then
  WAITING to the curated bound), each item with owner/age and its
  complete/dismiss verb where the surface exposes one; header-click
  opens Intelligence on the Follow-Through wing.
- The counsel-mandated forward-compatible slot: the lane header
  accepts a `newCommitmentVerb` prop, null/hidden today — when Wave 2
  lands manual creation, the door shows it with zero Chair work.
  Hidden means absent, not disabled (Article VI).

### Out

- Manual commitment creation (Wave 2); board redesign.

## Acceptance criteria

- [x] Seeded overdue/now items render truthfully ordered; verbs
  persist effects; empty state honest (tests).
- [x] The hidden slot exists (prop-level test) and renders nothing.

## Test plan

- `cd web && npx vitest run` — new lane suite + follow-through suites
  touched.

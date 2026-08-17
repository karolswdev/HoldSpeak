# HS-135-04 — Sparse surfaces shed chrome

- **Project:** holdspeak
- **Phase:** 135
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

Sparse surfaces show more chrome than data: Meetings with 1 record
renders a filter bar + count badge; Cadence with zero loops renders
full section scaffolding (counsel own-eyes finding; five-jobs
job3-cadence shot). L10 (ratified): below a shared threshold, filter
chrome hides, zero-metrics collapse, VERBS REMAIN, the empty well
speaks.

## Scope

### In

Per assets/design-laws.md L10 verbatim: a shared `SPARSE_THRESHOLD`
constant (JS, value per the law — 5) consumed by `LedgerFilter` and
`MetricStrip` (and any surface the law names); below threshold the
filter row does not render and zero-value metric tiles collapse; verb
bars and empty states always render. Tests per component (above/below
threshold rendering).

### Out

- New empty-state designs (SurfaceState is the kit); per-surface
  bespoke thresholds; the Chair (its lanes inherit this for free).

## Acceptance criteria

- [ ] Meetings with 1 record shows no filter chrome; with ≥5 it
  returns (test + screenshot pair).
- [ ] Cadence empty shows verbs + empty well, no dead scaffolding
  (screenshot).
- [ ] One constant, imported everywhere it applies (grep proof).

## Test plan

- `cd web && npx vitest run` scoped to LedgerFilter/MetricStrip +
  touched surfaces; shots in evidence.

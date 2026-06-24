# How features ship

## Rollout ladder

Every user-facing change rides the same ladder, gated by a flag in
`src/lib/flags.ts`:

1. **off** — merged, flag default false. Code in prod, dark.
2. **dogfood** — enabled for the internal team only. We use it daily.
3. **10%** — enabled for a 10% holdout-controlled cohort. Watch WAQC,
   activation, and error rate against the 90% control.
4. **GA** — flag flipped to 100%, then the flag is scheduled for
   removal once metrics hold for two weeks.

A feature does not advance a rung without its **tracked event** firing
correctly at the current rung — instrumentation precedes rollout.

## PR review rules

- Every PR links an issue (QL-3xx) or PRD.
- Every PR that touches user behavior names its flag and its event in
  the description.
- Schema changes (`prisma/schema.prisma`) require a reviewed migration
  and the eng lead's approval.
- Streak logic (`src/server/streaks.ts`) requires a test that covers a
  non-UTC timezone — see QL-322. This is a hard gate.
- a11y: keyboard path + screen-reader labels checked before GA.
- Two approvals for anything social/guild-related (moderation surface).

## Cadence

- Weekly product review reads WAQC and the active 10% experiments.
- Monthly roadmap review re-ranks `docs/roadmap-Q3.md` candidates.

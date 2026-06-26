# ledgerline — open issues

## LL-118 — double-post under retry storm (FIXED, watching)
Severity: high. During an April gateway retry storm we saw a small
number of charges posted twice. Root cause: a race where two
concurrent retries with the same `Idempotency-Key` both missed the
store before either wrote it. Fixed by making the
check-and-record atomic inside the charge transaction. See
`docs/POSTMORTEM-2026-04-double-post.md`. Kept open to confirm the
fix holds under load and to add the regression load test.

## LL-122 — reconcile drift on cross-day settlements
Severity: medium. `reconcile` reports small drift when a charge is
recorded just before midnight UTC but settles the next day at the
gateway. Suspected timezone-boundary bucketing in the reconciliation
window, not an actual unbalanced ledger. Needs the window to key off
the posting timestamp, not the settlement date.

## LL-130 — should the ledger be sharded / event-sourced? (architecture)
Severity: design question. SQLite single-writer is fine today but
`ledger_entries` is growing and the single writer is becoming a
throughput ceiling. Options on the table: (a) shard by account
range, (b) move to an event-sourced log with periodic snapshots, (c)
stay on SQLite and add read replicas. This is the open question
driving Stage 5. No decision yet — needs an ADR and an architect
review.

## LL-134 — reversal() lacks a "reason" field
Severity: low. Refund reversals don't capture why a reversal
happened (chargeback vs. customer refund vs. correction). Want a
`reason` enum on the reversing posting group for audit. Append-only,
so this is additive.

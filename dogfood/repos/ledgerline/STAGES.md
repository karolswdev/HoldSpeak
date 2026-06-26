# ledgerline — stages

A narrative of the phases this project has shipped. Each stage is a
coherent slice of capability with a single outcome line.

## Stage 1 — the posting engine  ✅ (2026-01-12)
Built `ledger.post()` and `ledger.reversal()` on an append-only
`ledger_entries` table. Outcome: every charge writes a balanced
debit/credit pair that sums to zero; corrections are reversals, never
edits.

## Stage 2 — the charges endpoint  ✅ (2026-02-03)
Mounted `POST /charges` (FastAPI) on top of the posting engine.
Outcome: external callers can record a charge over HTTP; the API
validates amount and currency and refuses fractional money.

## Stage 3 — idempotency  ✅ (2026-03-09)
Added the `idempotency_keys` store and the `Idempotency-Key` header
contract. Outcome: a retried charge replays its original result and
posts nothing new. (See ADR-0002.)

## Stage 4 — reconciliation  ✅ (2026-05-04)
Added the periodic `reconcile` job that checks the ledger sums to zero
and agrees with the gateway. Outcome: drift is detected within the
SLO window and pages rather than silently accumulating. Surfaced
LL-122 (cross-day settlement drift), tracked separately.

## Stage 5 — ledger sharding / event sourcing  🟡 IN DESIGN (LL-130)
The single SQLite writer is becoming a throughput ceiling as
`ledger_entries` grows. Open architecture question — no decision yet.
Options on the table:
- (a) shard `ledger_entries` by account range
- (b) move to an event-sourced append log with periodic balance
  snapshots
- (c) stay on SQLite, add read replicas, push only the write path
  harder

Needs an architect review and an ADR before any code. This is the
next big decision for the project.

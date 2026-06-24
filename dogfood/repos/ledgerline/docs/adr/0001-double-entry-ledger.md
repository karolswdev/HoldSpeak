# ADR-0001 — Append-only double-entry ledger on SQLite

Status: Accepted (2026-01-12)

## Context

ledgerline records money. We need a representation where every value
is auditable, no balance can silently change, and a mistake can be
traced and corrected without rewriting history. We are a small
service and want operational simplicity.

## Decision

- Use **double-entry** accounting: every event posts two rows (a
  debit and an equal-and-opposite credit) so each posting group sums
  to zero.
- Make `ledger_entries` **append-only**: no `UPDATE`, no `DELETE`.
  Corrections are new reversing entries.
- Store money as **integer minor units** (cents). No floats anywhere
  in the money path.
- Use **SQLite** as the system of record (WAL mode, single writer)
  for now. It is durable, transactional, and simple to operate.

## Consequences

- The ledger is fully auditable: history is immutable and every
  balance is derivable by summing entries.
- We trade write throughput for simplicity. A single SQLite writer is
  a known future ceiling (revisited in Stage 5 / LL-130).
- Every posting path must be covered by a "sums to zero" test, and
  reviewers must check the append-only invariant on the money path.

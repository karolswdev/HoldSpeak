# ADR-0002 — Idempotency keys for charges

Status: Accepted (2026-03-09)

## Context

Payment gateways and clients retry aggressively. Network timeouts,
load balancer retries, and client-side retries mean the same charge
request can arrive many times. Without dedupe, a retry posts a second
charge — the customer is billed twice. This is unacceptable for a
ledger.

## Decision

- Require an `Idempotency-Key` header on `POST /charges`. Requests
  without one are rejected (400).
- Record the first successful charge for a key in an
  `idempotency_keys` table mapping key → (group_id, amount_minor).
- On any later request with the same key, replay the stored result
  and post nothing new.
- Make the check-and-record **atomic** so concurrent retries for the
  same key cannot both miss-then-post. Back it with a UNIQUE
  constraint on `key` as a last-resort guard.

## Consequences

- Retries become safe no-ops; the ledger never double-posts a charge
  whose key it has already seen.
- Clients must generate and reuse a stable key per logical charge.
- The atomicity requirement is load-bearing: the original
  non-atomic implementation caused LL-118 (see the April postmortem).

# Postmortem — double-post during gateway retry storm (LL-118)

Date: 2026-04-17
Severity: SEV-2 (customer-impacting, money)
Authors: payments-core
Status: resolved (fix shipped in 0.3.1, regression load test pending)

## Summary

During a roughly 40-minute window on 2026-04-17, a payment gateway
upstream of ledgerline entered a retry storm (elevated latency caused
its client to retry the same charges). A small number of charges
(`23` confirmed) were posted to the ledger **twice**, double-billing
those customers. All affected charges were reversed and customers
re-credited the same day.

## Impact

- 23 charges double-posted, total $4,118.00 over-charged.
- All reversed via `ledger.reversal()` within 6 hours of detection.
- No ledger entries were lost or mutated (append-only held); the
  ledger was internally balanced throughout — the bug was a duplicate
  *valid* posting, not corruption.

## Timeline (UTC)

- 13:02 — gateway latency climbs; its client begins retrying.
- 13:05 — duplicate charges begin landing.
- 13:31 — reconcile flags account balances higher than the gateway's
  settled view; on-call paged.
- 13:48 — root cause identified: non-atomic idempotency check.
- 14:10 — mitigation: serialized the charge path per key.
- 19:00 — all 23 double-posts reversed; customers re-credited.
- next day — atomic check-and-record shipped as 0.3.1.

## Root cause

The idempotency check and the record-of-key were two separate steps
with the ledger post in between. Two concurrent retries carrying the
same `Idempotency-Key` could **both** read "no key present", both
proceed to `ledger.post()`, and both write a charge before either
recorded the key. The dedupe was correct for sequential retries and
wrong under concurrency.

## What went right

- Append-only ledger meant nothing was corrupted; reversals made the
  fix clean and auditable.
- Reconciliation detected the drift inside the SLO window.

## Action items

- [x] Make check-and-record atomic (serialize per key + UNIQUE
      constraint on `key`). Shipped 0.3.1.
- [ ] Add a concurrency regression test: N parallel retries of one
      key post exactly once. (LL-118 stays open until merged.)
- [ ] Add a load test that simulates a retry storm in CI.
- [ ] Alert on duplicate `(account, amount, ~window)` postings as a
      defense in depth.

# Durable facts (do not re-derive these)

- **Append-only ledger.** `ledger_entries` is immutable. Never UPDATE or DELETE
  a posted row; corrections are new reversing entries.
- **Idempotency.** Every write endpoint accepts an `Idempotency-Key` header.
  Keys are stored in `idempotency_keys(key, request_hash, response_json)` and a
  replay returns the stored response — it must never post a second entry.
- **Double-entry invariant.** Every charge posts two rows that sum to zero
  (debit customer, credit revenue). A transaction that leaves the ledger
  unbalanced is a bug.
- **Money is integer minor units** (cents), never floats.
- **Retries.** The gateway retries 5xx with the same `Idempotency-Key`; the
  retry must be a no-op if the first attempt committed.

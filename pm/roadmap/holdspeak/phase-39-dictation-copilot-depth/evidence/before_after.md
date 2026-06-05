# Phase 39 — before / after (real `.43`, same dictation)

Same rough spoken input, Phase-18/19 baseline (single-pass) vs Phase-39 depth
(multi-pass over the same `.hs` project context).

## SPOKEN (raw)

> ok so um claude i need you to add idempotency to the charge endpoint because right now if the gateway retries we post the entry twice and the customer gets double charged which is really bad so use the idempotency key header and store it and if we see the same key just return what we returned before dont post another entry and make sure it still balances and write a test for the retry case

## BEFORE — Phase 18/19 (single-pass, `rewrite_passes=1`)

```
Task: Implement idempotency for the `POST /charges` endpoint in `src/ledgerline/api/charges.py`.

**Specification:**
1.  **Header Parsing**: Extract the `Idempotency-Key` header from incoming charge requests.
2.  **Lookup & Replay**: Before posting, check if the key exists in `idempotency_keys(key, request_hash, response_json)`.
    *   If found: Return the stored `response_json` immediately without executing the ledger write.
    *   If not found: Proceed with the standard charge flow.
3.  **Storage**: Upon successful posting of a new entry in `src/ledgerline/db/entries.py`, store the key, request hash, and response JSON to ensure future retries are handled as no-ops.
4.  **Invariant Preservation**: Ensure the double-entry invariant (debit customer, credit revenue) is maintained for all *new* entries. The idempotency check must not alter existing balanced rows.

**Acceptance Criteria:**
- [ ] A request with a valid `Idempotency-Key` that has already been processed returns the cached response without creating a new row in `ledger_entries`.
- [ ] A retry of a 5xx error using the same key results in a no-op (no double posting).
- [ ] All ledger entries created via this endpoint maintain the zero-sum double-entry invariant.
- [ ] Money values remain integers (minor units); no floats are introduced.
- [ ] A unit test exists specifically verifying that a second request with an existing idempotency key does not duplicate the entry and returns the original response.
```

(1483 chars)

## AFTER — Phase 39 (multi-pass, `rewrite_passes=2`)

```
**Task:** Implement idempotency for `src/ledgerline/api/charges.py` to prevent double-counting on gateway retries.

**Specification:**
1.  **Header Parsing:** Extract the `Idempotency-Key` header from incoming requests.
2.  **Lookup & Replay:** Before executing logic in `src/ledgerline/ledger.py`, check `idempotency_keys(key, request_hash, response_json)`.
    *   If a match exists: Return the stored `response_json` immediately. Do not call the ledger posting engine or create new rows.
    *   If no match exists: Proceed with standard double-entry posting (debit customer, credit revenue), then store the key, request hash, and response JSON.
3.  **Invariant Preservation:** Ensure replaying a cached response strictly adheres to the append-only invariant; never mutate existing rows or create duplicate debits/credits for the same movement.

**Acceptance Criteria:**
- [ ] A request with a previously processed `Idempotency-Key` returns the exact stored response without creating new ledger entries.
- [ ] A request with a new `Idempotency-Key` processes normally, creates balanced rows in `ledger_entries`, and stores the key for future replays.
- [ ] Gateway retries (5xx) using an existing key result in a no-op that returns the cached response rather than failing or posting again.
- [ ] A unit test simulates a gateway retry scenario to verify that no duplicate ledger entries are created for the same idempotency key.
```

(1430 chars)

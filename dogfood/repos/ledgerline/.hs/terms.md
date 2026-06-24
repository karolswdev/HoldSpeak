# ledgerline — domain glossary

**Posting** — a single balanced accounting event made of two rows: a
debit and a credit of equal magnitude. Written by `ledger.post()`.
The atomic unit of the ledger.

**Entry** — one row in `ledger_entries`. Each entry has an account, a
side (debit/credit), an `amount_minor`, and the posting group it
belongs to. Entries are never modified once written.

**Reversal** — a compensating posting that undoes an earlier one by
appending its mirror image (debit becomes credit and vice versa).
This is how refunds and corrections are made. We never delete the
original.

**Idempotency key** — a client-supplied token (the `Idempotency-Key`
header) that uniquely names a charge attempt. The first success for a
key is recorded; later attempts with the same key replay that result
without posting again.

**Reconcile** — the periodic check that the ledger is internally
balanced (sums to zero per group) and agrees with the upstream
payment gateway's view. Disagreement is "drift".

**Minor units** — the smallest indivisible unit of a currency (cents
for USD). All amounts are integers in minor units; there are no
fractional amounts in the system.

**Settlement** — when funds actually move at the gateway/bank, as
opposed to when we record the intent to charge. ledgerline records
the accounting event; settlement is reconciled against it later.

**Drift** — a measured disagreement between the ledger and the
gateway (or an internally unbalanced state). Drift is an incident,
tracked under LL-122.

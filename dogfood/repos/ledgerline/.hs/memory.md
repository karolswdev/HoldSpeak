# ledgerline — durable memory

These invariants are load-bearing. Breaking any one of them is a
correctness incident, not a style nit. Never relax them to make a
test pass.

**The ledger is append-only.** Never emit `UPDATE` or `DELETE`
against `ledger_entries`. Corrections are made by appending new
reversing entries via `ledger.reversal()`. If you find yourself
wanting to edit a row, you want a reversal instead.

**Every posting is double-entry and sums to zero.** A `post()` writes
exactly two rows whose `amount_minor` values are equal and opposite
(one debit, one credit). The sum of any well-formed posting group is
0. A test must assert this for any new posting path.

**Money is integer minor units.** Amounts are stored and computed as
integer cents in `amount_minor`. Never introduce floats into the
money path — no `float(...)`, no division that can produce a
fraction. Rounding bugs in money are real bugs.

**Idempotency-Key replays are no-ops.** The same `Idempotency-Key`
must produce the original result and write zero new ledger rows.
Retries from the gateway are expected and frequent; a charge path
that double-posts under retry is the failure mode that caused LL-118.

**Reconciliation drift is a page.** If `reconcile` finds the ledger
sum is non-zero or disagrees with the gateway, treat it as an
incident, not a warning. The system tolerates zero unbalanced
states.

**One writer to SQLite.** The DB is single-writer in WAL mode. Don't
add a second concurrent writer; serialize through the existing
connection/transaction boundary.

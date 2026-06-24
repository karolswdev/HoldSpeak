# ledgerline — context

ledgerline is a payment-ledger service. It records money as immutable
double-entry rows and exposes a small FastAPI surface for charging,
refunding, and reconciling. The design bias is correctness and
auditability over cleverness: nothing in the ledger is ever mutated,
only appended to.

## Stack

- Python 3.11
- FastAPI + uvicorn (HTTP surface)
- SQLite as the system of record (single-writer, WAL mode)

## Primary entry points

- `src/ledgerline/ledger.py` — the double-entry posting engine.
  `post()` writes two balanced rows; `reversal()` writes the
  compensating pair. This is the only module that writes to
  `ledger_entries`.
- `src/ledgerline/api/charges.py` — `POST /charges`. Reads the
  `Idempotency-Key` header, dedupes via the idempotency store, then
  calls the posting engine.
- `src/ledgerline/db/entries.py` — append-only repository for
  `ledger_entries`. Exposes `append()` and `balance_of()`; there is
  deliberately no `update` or `delete`.
- `src/ledgerline/db/idempotency.py` — the `idempotency_keys` store
  that maps a key to the result of its first successful charge.

## How a request flows

1. Client sends `POST /charges` with an `Idempotency-Key`.
2. The endpoint checks the idempotency store. A hit replays the
   stored result and writes nothing new.
3. A miss calls `ledger.post()`, which appends a balanced debit and
   credit inside one SQLite transaction, then records the key.

## Where to look first

- Money math or balance bugs → `ledger.py` + `db/entries.py`.
- Double-charge / retry bugs → `api/charges.py` + `db/idempotency.py`.
- "What did we already decide?" → `docs/adr/` and `STAGES.md`.

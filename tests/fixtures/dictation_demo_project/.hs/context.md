# Project: ledgerline

`ledgerline` is a Python payment-ledger service. It records money movements
as immutable double-entry rows and exposes a small FastAPI surface for
charging, refunding, and reconciling. It is the system of record for balances;
correctness and auditability beat cleverness every time.

Primary entry points:

- `src/ledgerline/api/charges.py` — the `POST /charges` endpoint.
- `src/ledgerline/ledger.py` — the double-entry posting engine.
- `src/ledgerline/db/entries.py` — the `ledger_entries` table repository.

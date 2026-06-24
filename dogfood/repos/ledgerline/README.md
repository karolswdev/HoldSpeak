# ledgerline

An append-only double-entry payment ledger with a small FastAPI
surface. ledgerline records money as immutable rows and exposes
endpoints for charging, refunding (reversal), and reconciling.

The design bias is **correctness and auditability over cleverness**.

## Invariants

- The ledger is **append-only** — no `UPDATE`/`DELETE` on
  `ledger_entries`. Corrections are reversals.
- Every posting is **double-entry** and **sums to zero**.
- Money is **integer minor units** (cents). No floats.
- `Idempotency-Key` replays are **no-ops** — safe to retry.

## Stack

Python 3.11 · FastAPI · uvicorn · SQLite (system of record, WAL).

## Layout

| path | what |
| --- | --- |
| `src/ledgerline/ledger.py` | the posting engine (`post`, `reversal`) |
| `src/ledgerline/api/charges.py` | `POST /charges` + idempotency |
| `src/ledgerline/db/entries.py` | append-only `ledger_entries` repo |
| `src/ledgerline/db/idempotency.py` | the `idempotency_keys` store |
| `docs/adr/` | architecture decisions |
| `STAGES.md` | what's shipped and what's in design |

## Develop

```bash
pip install -e ".[dev]"
python -m pytest -q
```

See `CHANGELOG.md` for releases and `STAGES.md` for the roadmap
(Stage 5 — ledger sharding / event sourcing — is in design).

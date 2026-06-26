# ledgerline — dev workflow

How a change ships, start to finish.

## 1. Branch + spec

Cut a branch named `ll-<issue>-<slug>` (e.g. `ll-118-retry-dedupe`).
If there's no issue, open one first — ledger changes are always
tracked.

## 2. Implement

Keep the change inside the module that owns the concern (see
`.hs/context.md`). Only `ledger.py` writes to `ledger_entries`.

## 3. Test

- `python -m pytest -q` must be green.
- Any posting path needs a "sums to zero" assertion.
- Any charge path needs an idempotent-replay test.
- New money math needs an integer-only test.

## 4. Review

Two-eyes required on anything in the money path (`ledger.py`,
`db/entries.py`, `api/charges.py`). Reviewer checks the invariants in
`.hs/memory.md` explicitly, not just the diff.

## 5. Records

- Schema/contract change → ADR in `docs/adr/`.
- User-visible change → `CHANGELOG.md` Unreleased section.
- Phase-level work → a line in `STAGES.md`.

## 6. Deploy

Merge to `main` → CI builds and runs the full suite → tagged release
→ rolling deploy of the uvicorn workers. SQLite is migrated forward
only (no destructive migrations on `ledger_entries`).

# Turning dictation into a coding-agent task

Produce a task spec a coding agent can execute without guessing.

- Name the concrete files to touch. Use real paths from this repo
  (`src/ledgerline/ledger.py`, `src/ledgerline/api/charges.py`,
  `src/ledgerline/db/entries.py`, `src/ledgerline/db/idempotency.py`,
  `tests/test_ledger.py`). Do not say "the ledger module".
- Write the spec as imperatives. "Add a `reversal()` overload that
  takes a posting group id" — not "we could maybe support reversals".
- End with an acceptance-criteria checklist the agent can self-verify.
- Call out the invariants the change touches (append-only, sums to
  zero, integer minor units, idempotent replay) and state how the
  change preserves each.
- Prefer new reversing entries over editing existing rows. If the
  task implies mutating `ledger_entries`, reframe it as an append.
- Any change with a double-counting or double-post risk MUST require
  a test that replays the path and asserts the row count and balance
  are unchanged.
- If the dictation asks for money math, require integer-only
  arithmetic and a balanced-posting assertion in the test.
- If the change alters a contract or schema, require an ADR under
  `docs/adr/` and a `CHANGELOG.md` Unreleased entry.

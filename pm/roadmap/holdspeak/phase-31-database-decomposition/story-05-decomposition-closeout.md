# HS-31-05 — Decomposition closeout (size + schema-parity evidence)

**Status:** not-started.

## Goal

Confirm the phase exit criteria, record the final evidence, and close the phase.

## Scope

- Record before/after line counts: `db.py` → the `holdspeak/db/` package total,
  and confirm `MeetingDatabase` is gone (`grep -r MeetingDatabase` empty).
- Record the fresh-build `sqlite_master` parity result vs. the pre-refactor v18 schema.
- Confirm `SCHEMA_VERSION` reset to 1 and the dev DB rebuild is documented.
- Write `final-summary.md`; flip the phase to done in `current-phase-status.md`
  and the project README.

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green, count recorded.

## Done when

- [ ] All Phase 31 exit criteria checked with evidence.
- [ ] Final size + god-class-deleted + fresh-build schema-parity numbers recorded.
- [ ] `final-summary.md` written; phase marked done in status doc + README.

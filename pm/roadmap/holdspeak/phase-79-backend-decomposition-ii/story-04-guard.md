# HS-79-04 — the density guard locks the new shapes

- **Project:** holdspeak
- **Phase:** 79
- **Status:** todo
- **Depends on:** 01–03.
- **Unblocks:** the phase staying decomposed.

## Problem

Phase 63 proved a carve regrows without a lock. Its guard
(`tests/unit/test_backend_density_guard.py`) covers `runtime/` and
`meeting_session/` and names the old meetings route file as a watch item —
which Phase 72 resolved. Nothing guards `db/`, `routes/system/`, or
`routes/primitives/`.

## The design

Extend the existing guard file: per-module budgets for the three new packages
(composed `__init__` small; every concern module under the shared module
budget), the same carve-don't-bump doctrine comment, and `db/core.py` named
as the deliberate watch item (schema DDL + migrations, snapshot-pinned — a
different budget conversation). Include the fires-on-regrowth self-test shape
the P63 guard uses.

## Test plan

The guard red against a fabricated oversized module (tmp copy), green on the
shipped tree; full unit suite green.

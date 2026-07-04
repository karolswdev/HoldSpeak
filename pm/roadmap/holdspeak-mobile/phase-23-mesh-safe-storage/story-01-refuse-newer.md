# HSM-23-01 — Refuse-newer on the iPad store

- **Project:** holdspeak-mobile
- **Phase:** 23
- **Status:** done (pre-paid, Equilibrium Wave 4, 2026-06-27) — see
  [`evidence-story-01.md`](./evidence-story-01.md). `SQLiteStorage` reads `user_version`
  BEFORE migrate/stamp and throws `StorageError.tooNew` (handle closed, data untouched)
  when the stored version exceeds the build's, mirroring the desktop refuse-newer matrix.
- **Depends on:** the desktop matrix it mirrors (Phase 50, `holdspeak/db/core.py`
  `_ensure_schema` + `SchemaVersionError`).
- **Unblocks:** HSM-23-02 (the backup rides the same open path), HSM-23-03 (the panel
  reports the refusal honestly).
- **Owner:** unassigned

## Problem

The audit's sharpest mobile finding (theme 6): the iPad store migrated only
`userVersion < 2`, then **unconditionally stamped `user_version = 2`** — the exact
data-loss case the desktop refuses. As sync brings a newer-build peer's DB into reach,
downgrade-stamping silently corrupts the newer peer's data.

## The design

Read the stored `user_version` *before* any migrate or stamp. If it exceeds
`SQLiteStorage.schemaVersion`, close the handle and throw
`StorageError.tooNew(stored:build:)` — never write, never stamp. A fresh DB reads 0 and
falls through to the create/equal paths unchanged.

## Scope

- **In:** the read-before-stamp guard + the typed error
  (`apple/Sources/Providers/Storage/SQLiteStorage.swift:44-49`); tests proving a
  future-versioned DB is refused, keeps its `user_version`, and keeps its data.
- **Out:** any UI for the refusal (HSM-23-03); desktop-side changes (already Phase 50).

## Test plan

- `swift test --filter SQLiteStorageSchemaSafetyTests`
  (`testNewerDatabaseIsRefusedAndLeftUntouched` + siblings) — green.

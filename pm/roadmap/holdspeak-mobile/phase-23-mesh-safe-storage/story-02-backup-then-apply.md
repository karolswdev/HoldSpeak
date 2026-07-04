# HSM-23-02 — Backup-then-apply (timestamped) before migration

- **Project:** holdspeak-mobile
- **Phase:** 23
- **Status:** done (pre-paid, Equilibrium Wave 4, 2026-06-27) — see
  [`evidence-story-02.md`](./evidence-story-02.md). An older-than-build DB is copied to a
  timestamped `.bak` sibling BEFORE the v1→v2 ALTERs run; equal/fresh opens take no
  backup.
- **Depends on:** HSM-23-01 (the same read-before-stamp open path decides which matrix
  arm runs).
- **Unblocks:** HSM-23-03 (the panel can point at the backup when an upgrade ran).
- **Owner:** unassigned

## Problem

The v1→v2 ALTERs ran in place with no recoverable copy — an interrupted or buggy
migration was unrecoverable, where the desktop (Phase 50) never migrates without
`backup_database` first.

## The design

On the `stored > 0 && stored < schemaVersion` arm only, copy the SQLite file to
`<path>.<yyyyMMdd-HHmmss>.bak` (collision-suffixed) before `migrateIfNeeded`. Best-effort
and logged: a failed copy must not block opening the store (the desktop safety-net rule).
The backup naming matches the desktop's so a sibling reads the same on both surfaces.

## Scope

- **In:** `backupBeforeMigrate`
  (`apple/Sources/Providers/Storage/SQLiteStorage.swift:65-90`); tests proving the backup
  exists, is the pre-migration copy (`user_version` still 1), and that equal-version opens
  take none.
- **Out:** a user-facing restore flow (the desktop CLI owns restore; the iPad panel in
  HSM-23-03 reports, not repairs).

## Test plan

- `swift test --filter SQLiteStorageSchemaSafetyTests`
  (`testOlderDatabaseIsBackedUpThenMigrated`, `testEqualVersionDatabaseIsNoOp`) — green.

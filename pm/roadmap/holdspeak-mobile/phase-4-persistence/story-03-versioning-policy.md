# HSM-4-03 — Versioning policy

- **Project:** holdspeak-mobile
- **Phase:** 4
- **Status:** done
- **Depends on:** HSM-4-01, HSM-0-03
- **Owner:** unassigned

## Problem

The mobile SQLite store needs a stated version policy, and it must not silently
re-couple to the wire `contract_version` the way the desktop almost coupled its
DB version. The app is greenfield (no installs, no users), so the policy should
say plainly that there is nothing to migrate from and no compat ceremony is owed
yet.

## Scope

- **In:** a short written policy: the DB ships at `SCHEMA_VERSION = 1`; the
  relationship between `SCHEMA_VERSION` and Phase-0's `contract_version` (default:
  independent, with the DB recording which `contract_version` it was built
  against); greenfield discipline (no migration ladder, no compat shims
  pre-release); and the trigger that would change this (first real install base /
  TestFlight).
- **Out:** actual migration tooling (nothing to migrate). Encryption-at-rest
  (Phase 11). The schema itself (HSM-4-01). Sync versioning (Phase 10).

## Acceptance criteria

- [ ] The policy document states `SCHEMA_VERSION = 1` and the greenfield posture
      (no migrations/shims) explicitly.
- [ ] The `SCHEMA_VERSION` ↔ `contract_version` relationship is recorded as
      independent (or argued otherwise), so a contract bump does not force a DB
      bump with no storage change, and vice-versa.
- [ ] The trigger that ends greenfield discipline (first TestFlight/public install
      base) is named, with what changes at that point.

## Test plan

- Unit: a guard asserting the DB reports `SCHEMA_VERSION = 1` and records its
  built-against `contract_version`.
- Manual: n/a (policy deliverable; HSM-4-01/02 carry the behavior).

## Notes / open questions

- This mirrors the desktop's greenfield posture (memory: HoldSpeak treated its DB
  as greenfield pre-release). Keep it that lean until there is a real install base.
- Decoupling from `contract_version` is the load-bearing point — it's the desktop
  near-miss this story exists to avoid repeating.

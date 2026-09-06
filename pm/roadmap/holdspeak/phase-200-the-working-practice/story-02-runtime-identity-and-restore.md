# HS-200-02: Expose loaded runtime identity and prove restore

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-01
- **Unblocks:** HS-200-04, HS-200-05, HS-200-31, HS-200-40
- **Owner:** unassigned
- **Gate:** G0
- **Trace:** AA-ENV-001–005; AC-01–02; C1

## Problem

A user can inspect a new checkout while an older process serves a different database or frontend. Recovery must identify and preserve the actual installation.

## Scope

Implement the missing C1 identity fields and mismatch repair state. Rehearse backup, upgrade, and restore on a copy.

Implementation seams: holdspeak/web/routes/system/health.py; holdspeak/web_runtime.py; existing backup and restore commands; Settings diagnostics.

Out: Automatic replacement of the running owner hub or a new database engine.

## Acceptance criteria

- [ ] Backend and frontend identify the loaded build and process start independently of the current Git checkout.
- [ ] Diagnostics identify the database and schema without exposing sensitive paths on ordinary surfaces.
- [ ] A stale bundle and two competing runtimes produce specific diagnoses.
- [ ] A copy of the selected database survives backup, supported upgrade, restore, and record reopen.
- [ ] Restore evidence includes permitted attachments and the protected-store boundary.

## Test plan

Planned unit/integration suite: phase200_runtime_identity. Exercise an old running process after changing checkout, stale assets, two instances, and interrupted restore. Manual: inspect the recovered copy.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G0](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.

# HS-200-31: Choose and prove the durable execution host

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-02, HS-200-21, HS-200-24
- **Unblocks:** HS-200-32, HS-200-33, HS-200-36, HS-200-40
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** AA-ENV; AA-AUT-003; AC-01–03, AC-18; C1, C9–10

## Problem

Reach cannot run work when the actual hub is asleep or unavailable. The deployment must identify where execution and state live.

## Scope

Prepare and test one owner-controlled always-on hub arrangement, using the existing application runtime.

Implementation seams: Web runtime and health; Reach; existing platform service setup; backup/restore.

Out: Cloud hosting, a relay service, or assuming the inference server already runs HoldSpeak.

## Acceptance criteria

- [ ] The runbook identifies hub, inference host, database custody, network boundary, startup, and expected availability.
- [ ] No active-active writers or shared multi-writer SQLite storage are introduced.
- [ ] Required capture, text insertion, People, and review paths work on the selected topology. Desktop-only dependencies are identified.
- [ ] A supervised trial verifies source/model access and one preparation result on the selected host.
- [ ] Sleep, reboot, network loss, and restore expose availability and missed coverage accurately.
- [ ] Deployment and rollback are concrete and reviewable before any owner runtime replacement.

## Test plan

Integration: temporary deployment with controlled availability failures. Physical: selected host startup, reboot, network loss, and restored copy.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.

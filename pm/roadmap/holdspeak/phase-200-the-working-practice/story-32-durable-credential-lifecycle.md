# HS-200-32: Implement a scoped credential lifecycle for recurring work

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-24, HS-200-31
- **Unblocks:** HS-200-33, HS-200-35, HS-200-36, HS-200-40
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** AA-AUT-006; AA-INT-001–003; AC-15, AC-20; C10

## Problem

Current Reach credentials disappear at hub restart. Recurring operation needs a deliberate durable enrollment contract.

## Scope

Design and implement machine enrollment separately from transient agent credentials using protected credential storage.

Implementation seams: AgentCredentialStore; CredentialService; Reach authentication; existing protected secret storage.

Out: Permanent owner-equivalent remote tokens or a new identity provider.

## Acceptance criteria

- [ ] Persisted authorization includes explicit machine identity, scope, expiry, rotation, and revocation.
- [ ] Restart recovery does not persist every current session token or broaden its rights.
- [ ] Expiry and clock behavior are defined across process restart and time changes.
- [ ] Revocation blocks new dispatch and is visible in the recipe's recovery state.
- [ ] Logs, prompts, process arguments, exports, and evidence contain no token values.

## Test plan

Planned suite: phase200_machine_credentials. Test restart, expiry, rotation, revoke races, changed clock, protected-store failure, and insufficient scope.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.

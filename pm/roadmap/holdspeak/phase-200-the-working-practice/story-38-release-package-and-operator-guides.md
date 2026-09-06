# HS-200-38: Package the verified product and recovery procedures

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-23, HS-200-30, HS-200-36
- **Unblocks:** HS-200-39, HS-200-40
- **Owner:** unassigned
- **Gate:** G5
- **Trace:** AA-ENV; AA-INT; AC-01–03, AC-25; C1, C12

## Problem

A source checkout with useful workflows still needs an installable release and accurate operating instructions.

## Scope

Prepare the release candidate, update public procedures and generated references, and document the selected supported deployment.

Implementation seams: Packaging and release scripts; README and guides; API/MCP generators; recovery documentation.

Out: Publishing a release before the actual repository release authorization and G5 exit.

## Acceptance criteria

- [ ] A clean packaged installation includes the tested frontend/backend and required assets.
- [ ] Upgrade and restore work from the supported prior installation without unplanned data loss.
- [ ] Guides describe the three recipes, assignment review, scheduling owner, credential recovery, and actual limits.
- [ ] Generated HTTP/MCP references match registered contracts.
- [ ] Support claims identify the physically verified platform and retained Linux checks. Unproved native parity is not advertised.

## Test plan

Build/install candidate in an isolated location. Run release gate, documentation navigation, relevant drift checks, and upgrade/restore proof.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G5](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.

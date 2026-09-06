# HS-200-17: Define three executable recipe contracts

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-06, HS-200-10, HS-200-11, HS-200-13
- **Unblocks:** HS-200-18, HS-200-19, HS-200-21, HS-200-24, HS-200-33, HS-200-40
- **Owner:** unassigned
- **Gate:** G2
- **Trace:** AA-IVW-007–009; AA-INT-002; AC-34–35; C5

## Problem

A suggestion needs a supported execution path and exact configuration fields before Interview can install useful behavior.

## Scope

Create versioned descriptors and compilation for preparation, decision review, and weekly update using existing services.

Implementation seams: Interview descriptors; existing recipes; preparation/update services; MCP registry and tool metadata.

Out: A general workflow language or arbitrary graph executor.

## Acceptance criteria

- [ ] Each recipe declares input schema, source requirements, output, execution owner, effects, and supported triggers.
- [ ] Compilation binds qualified refs, source scope, route policy, limits, and acceptance criteria.
- [ ] Missing adapters and unavailable prerequisites produce typed gaps.
- [ ] A manual run and later scheduled run can share the same recipe definition.
- [ ] The catalog is discoverable through supported Web and MCP paths without widening the ordinary Thread palette.

## Test plan

Planned suite: phase200_recipe_catalog. Contract-test all three recipes, stale descriptor versions, missing adapter, and unsupported trigger. Execute one manual result per recipe.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G2](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.

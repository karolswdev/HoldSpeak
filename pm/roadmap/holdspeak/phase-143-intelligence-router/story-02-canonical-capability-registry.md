# HSEGHS001HS104-143-02 - Canonical Capability Registry

- **Project:** holdspeak
- **Phase:** 143
- **Status:** done
- **Depends on:** 143-01
- **Unblocks:** 143-04, 143-05, 143-07 through 143-10, 143-13
- **Owner:** unassigned

## Problem

Capability strings are scattered across speech, meetings, Ask, Workbench, agents, recipes, Rails, and delivery. The browser cannot lawfully invent requirements or compatibility.

## Scope

### In

- Implement InferenceCapabilityDefinition@1 and a deterministic composition-time registry.
- Register every censused production capability with operation/result schema, modality, context, boundary, tool, and fallback requirements.
- Implement immutable `InferenceRetryPolicyDefinition@1` registry; each
  capability freezes its permitted policy IDs/default and startup validates all
  references before assignment/plan code exists.
- Expose safe owner labels/groups and exact compatibility facts.
- Fail startup on unknown, duplicate, confusable, or schema-drifted definitions.

### Out

- No assignment persistence.
- No browser-authored registry or plugin string passthrough.

## Acceptance criteria

- [x] Registry canonical bytes and schema hashes are stable across restart and registration order.
- [x] Every production inference call site references one registered definition revision.
- [x] Plugin capabilities require a bounded plugin definition revision.
- [x] Unknown capability requests refuse before profile/runner access.
- [x] Owner projection contains labels and requirements but no secrets or implementation paths.
- [x] Retry-policy definitions are canonical/hash-bound and every capability
  default/allowed reference resolves without cycles or unknown IDs.

## Test plan

- Unit fixtures for every definition and duplicate/confusable/schema drift.
- Generated call-site-to-capability census equality.
- Startup, restart, plugin, and HTTP/MCP projection tests.

## Implementation notes

- Follow [architecture-contract.md](./assets/architecture-contract.md), [owner-experience.md](./assets/owner-experience.md), and [repository-census.md](./assets/repository-census.md).
- Product code, schema, inventories, migrations, tests, and evidence land in this story; status changes only after the evidence ledger exists.
- Preserve unrelated dirty-worktree changes and do not create a second inference gateway, execution revision registry, or owner authority.

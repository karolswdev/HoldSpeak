# HSEGHS001HS104-143-03 - Reusable Model Profile Authority

- **Project:** holdspeak
- **Phase:** 143
- **Status:** done
- **Depends on:** 143-01, Phase 142
- **Unblocks:** 143-04, 143-05, 143-12
- **Owner:** unassigned

## Problem

ProfileRecord and InferenceTarget conflate friendly model identity, mutable endpoint/path/secret configuration, readiness, and execution identity. MCP can also reach ProfileService without service-level OWNER enforcement.

## Scope

### In

- Add immutable ModelProfileRevision@2 and hub-local ProfileBinding authority.
- Bind profiles only to existing deployment heads and immutable DeploymentRevision execution truth.
- Adapt historical v1 profiles without rewriting their bytes.
- Enforce OWNER in the application/service layer for list/get/create/update/delete/probe/bind.
- Stop new profile bindings and active policies from syncing local paths, endpoints, or secrets.
- Split legacy `download-and-use`, `use-existing`, and hosted
  connect-and-route effects so model availability is separately receipted and
  cannot mutate a legacy/new assignment as a side effect.

### Out

- No second deployment revision registry.
- No automatic assignment when a model is added or connected.

## Acceptance criteria

- [x] Profiles contain no secret, locator, live readiness, or mutable endpoint discovery.
- [x] Bindings are hub-local, revisioned, CAS-protected, and resolve one exact DeploymentRevision.
- [x] AGENT/MODEL_TURN cannot discover or mutate profiles via HTTP, MCP, or direct service call.
- [x] Legacy v1 executes byte-identically through one adapter binding.
- [x] Deleting a referenced profile refuses with exact dependent assignments.
- [x] V2 profile revisions and bindings are hub-local; hostile sync cannot
  create either, and v1 historical bytes remain the only compatibility case.
- [x] Add/download/connect/use-existing changes zero assignment revisions.

## Test plan

- Authority matrix across service/HTTP/MCP principals.
- V1 migration, path privacy, sync inertness, secret replacement, readiness drift, and restart.
- Hash forgery and binding/deployment-head race tests.

## Implementation notes

- Follow [architecture-contract.md](./assets/architecture-contract.md), [owner-experience.md](./assets/owner-experience.md), and [repository-census.md](./assets/repository-census.md).
- Product code, schema, inventories, migrations, tests, and evidence land in this story; status changes only after the evidence ledger exists.
- Preserve unrelated dirty-worktree changes and do not create a second inference gateway, execution revision registry, or owner authority.

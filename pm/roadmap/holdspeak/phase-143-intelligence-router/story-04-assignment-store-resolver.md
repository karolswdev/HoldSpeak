# HSEGHS001HS104-143-04 - Assignment Store and Resolver

- **Project:** holdspeak
- **Phase:** 143
- **Status:** done
- **Depends on:** 143-02, 143-03
- **Unblocks:** 143-05, 143-07 through 143-10, 143-11, 143-13
- **Owner:** unassigned

## Problem

There is no canonical ordered profile-chain authority. Existing Config, subject, recipe, and Workbench pointers would become competing truth if fallbacks were added in place.

## Scope

### In

- Implement the one canonical hub-local `InferenceAssignment@1` persistence;
  `CapabilityRoutePolicy` is not a second table or service.
- Implement precedence: invocation, subject, capability, group, global; first defined chain wins whole.
- Add atomic ordered-chain set/clear commands with idempotency and narrow CAS.
- Project effective named chains, inheritance source, readiness, compatibility, and boundary warnings.
- Build one-way adapters/migration markers for legacy pointer families.
- Retire/split setup command effects that previously combined making a model
  available with changing the Thoughts target before enabling this authority.

### Out

- No fallback execution yet.
- No partial per-slot autosave or chain concatenation.

## Acceptance criteria

- [x] Chains are nonempty, unique, bounded to four, cycle-free, compatible, and recursively closed.
- [x] Use default deletes only the sparse override and names the effective chain.
- [x] Unrelated assignment edits do not conflict; same assignment races have one winner.
- [x] Adding/downloading/connecting a profile leaves all assignments byte-identical.
- [x] No consumer dual-reads Config after its migration marker commits.
- [x] Fresh no-model and dangling upgrade states project one named repair and
  never auto-assign a newly added model.
- [x] An explicit starter bundle preview/apply is the only multi-group setup.
- [x] Group/global chains use each capability's default retry policy unless one
  override is server-proven permitted by every member; differing policy sets,
  registry growth, and incompatible inherited entries become named issues.
- [x] Use-default preview shows the exact capability-specific result before clear.
- [x] Saving during local runtime lease saturation succeeds when structural
  compatibility holds; later execution observes capacity at preflight.

## Test plan

- All precedence layers, clear-to-inherit preview, duplicate/cycle/incompatible/dangling entries.
- Group/global compatibility intersections, differing policy sets, and registry growth.
- Heterogeneous global chain inherited by Speech recognition produces the exact
  chain or `no_compatible_assignment`; it never filters/substitutes entries.
- Replay/lost response/changed payload/concurrent same and unrelated assignment CAS.
- Fresh and upgraded DB migrations for each legacy pointer family.

## Implementation notes

- Follow [architecture-contract.md](./assets/architecture-contract.md), [owner-experience.md](./assets/owner-experience.md), and [repository-census.md](./assets/repository-census.md).
- Product code, schema, inventories, migrations, tests, and evidence land in this story; status changes only after the evidence ledger exists.
- Preserve unrelated dirty-worktree changes and do not create a second inference gateway, execution revision registry, or owner authority.

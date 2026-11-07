# HS-T12-01 · Fix navigation semantics and the removal boundary

**Proposed characterization/decision task; no product edits.** Depends on [HS-T00](HS-T00-baseline.md). Parent: [HS-S12](../stories/HS-S12-focused-navigation.md). This task may finish with G-OPEN pending; implementation then stays blocked.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [choices](../stories/HS-S12-focused-navigation.md#g-open-choices-and-proposed-bounded-branch), [ownership](../stories/HS-S12-focused-navigation.md#target-ownership), [matrix](../stories/HS-S12-focused-navigation.md#acceptance-matrix) and [source map](../stories/HS-S12-focused-navigation.md#exact-source-owned-paths-and-task-handoff); [V12](../VALIDATION.md#v12-focused-navigation-verification); [I16/I17/I18/I21/I25](../INVARIANTS.md); current root/web architecture and UX instructions.

## Work

1. Trace every current registration owner, public shell wrapper, alias and readiness caller. Distinguish active built-ins, parked compatibility, arbitrary test seams and any supported extension contract. Check the actual current import/caller graph before removing an export; an old literal scan is not a compiler proof.
2. Record accepted G-OPEN ordering separately for transient opens and staged route arrival. Proposed FIFO means command application; it does not by itself establish final cross-family focus. Conductor can schedule a later restore. If deterministic final focus is required, record the needed scope amendment instead of hiding that extra behavior change.
3. Specify all staged-slot transitions: successful storage, failed write/read/remove, A success then B failure, failure then later success, malformed values, remount and reload limits. One in-memory fallback represents the same latest staged slot; it must not become another queued opener. No durable exactly-once guarantee is implied when storage fails.
4. Map recovery admission, clear-first-use, retained-off-glass windows, reveal and readiness publication to one proposed transient state owner. Verify those fields will be excluded from workspace/hub persistence. A callback bridge that merely renames registration does not satisfy the target.
5. Preserve public Boolean/fallback semantics and exact alias/default-scope composition. The existing store open action returns void and admits parked rows; it cannot itself be treated as proof of lawful navigation. Establish handling for unknown/non-surface/parked keys and Conductor/Drawer before changing wrappers.
6. Verify no new static cycle, especially shell→Chair/NeedsDrawer/openObject→shell. Retain the existing Dock-origin compact Dictate compatibility branch at its current UI boundary; do not assume a Speak tile is currently visible on the phone Dock or change running/minimized-chip behavior.
7. Establish the V12 baseline if execution is assigned. Preserve exact proposal/request handoff and editor-step-aside tests, lazy chunk recovery and mounted-read/layout mechanisms. Observe unavailable/settled target behavior without deciding a new policy silently.

## Acceptance

Return the accepted policy or exact unresolved alternatives; caller/support-contract closure; source/import map; synchronous public-interface meaning; readiness/reveal ownership; field persistence exclusions; staged-fault truth table; baseline results or explicit blockers; and the exact editable/test budget. Other Program/People decisions are not prerequisites.

If retirement is unsupported or the owner prefers retention, return preservation-test work as a separate useful scope rather than pretend the map can be deleted. Use the [completion report](../COMPLETION_REPORT_TEMPLATE.md), marked characterization rather than implementation.

## Stops and rollback

No product rollback should be needed. Stop for an unassigned environment, incompatible source drift, unknown supported callers, required new state/persistence framework, ambiguous focus policy or unsafe browser fixtures. Never run broader app code merely to satisfy a static removal claim, and never infer approval from the user requesting a plan.

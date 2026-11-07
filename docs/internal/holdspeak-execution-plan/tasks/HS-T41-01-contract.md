# HS-T41-01 · Set the director identity contract

**Characterization and decision task; no implementation assignment.** Depends on [HS-T00](HS-T00-baseline.md). Parent: [HS-S41](../stories/HS-S41-director-person-identity.md). D16/G41 remain pending.

## Mandatory context

[Safety](../AGENT_START.md#authority-and-checkout-safety); story [choices](../stories/HS-S41-director-person-identity.md#d16-and-g41-choices), [custody](../stories/HS-S41-director-person-identity.md#interaction-and-outcome-custody) and [matrix](../stories/HS-S41-director-person-identity.md#acceptance-matrix); [V41](../VALIDATION.md#v41-director-person-identity-verification); [I16/I18/I21/I23/I25](../INVARIANTS.md); current root/web/backend test instructions. No whole-library reading requirement.

## Work

1. Verify the pinned/current chain: Meeting owner text → confirm route → ordinary action/commitment IDs → Door action-ID person metadata; Room typed candidate projection → owner-only alias POST → current attribution. Record action IDs and commitment IDs separately.
2. Resolve D16 branch A reusable alias versus branch B per-obligation assignment. For A, explicitly accept scoped People-list context display, name-only Meeting control, separate Link confirmation, unresolved identity stop and in-memory-only receipt limits. Record whether both UI branches or only Meeting clarity are assigned.
3. Characterize both permission layers: full hub People REST GET/POST require the owner; separately, service/MCP reads can admit live launched readers, never alias writes. Do not turn the service capability into a new HTTP permission. Preserve no-private-fields-in-Room tests and People-free reads. Do not infer an absent Door person means locked or ambiguous.
4. Freeze G41 identity sufficiency: equal names/roles are not distinguished by UUID order, a confirmation checkbox or mere navigation. Inspect existing exact-ID People context, retain unresolved if the owner still cannot distinguish, and never guess. Also accept or revise the [explicit Room Check after exact inspection](../VALIDATION.md#exact-person-inspection-and-return-proof): the person pullout does not supply the roster return event. Check must work without an inline POST receipt; automatic return/focus would require a separately scoped design rather than presumed existing behavior.
5. Freeze producer/test/browser ownership in V41. Characterization case creation and execution require a separate scoped test/environment assignment; source reading is not a baseline pass. Establish synthetic encrypted-store/ordinary-DB isolation before any collection.
6. Record supported caller and concurrency limits, exact API errors, stale read/write scenarios, unprojected obligations and no durable/cross-device receipt guarantee. Stop branch A if broader identity/state semantics are required.

## Acceptance, stops and rollback

Return the selected or unresolved G41 choices, exact source/custody map, permitted edit/test budget, actual baseline status and remaining gaps in the [completion report](../COMPLETION_REPORT_TEMPLATE.md). No app mutation belongs to this decision task unless separately assigned as characterization. Preserve other work; no rollback operation is needed for read-only inspection. Missing authority, unsafe fixtures, material drift or unresolved assignment semantics blocks dependent implementation.

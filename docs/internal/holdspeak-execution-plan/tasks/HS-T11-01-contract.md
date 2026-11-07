# HS-T11-01 · Confirm the creation interaction and baseline

**Status:** proposed assignment. Depends on [HS-T00](HS-T00-baseline.md). Parent: [HS-S11](../stories/HS-S11-program-creation-context.md). This task grants no implementation authority.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [decision](../stories/HS-S11-program-creation-context.md#d13-and-g11-decision-boundary), [outcome states](../stories/HS-S11-program-creation-context.md#proposed-interaction-and-truthful-outcomes), [matrix](../stories/HS-S11-program-creation-context.md#acceptance-matrix) and [source map](../stories/HS-S11-program-creation-context.md#exact-source-map-and-ownership); [V11](../VALIDATION.md#v11-program-creation-verification); [I02/I16/I17/I18/I21/I24/I25](../INVARIANTS.md). Read current root/web instructions and their named UX/surface contracts, not the whole research library.

## Scope

Read the producer/caller/test contracts and settle D13/G11. Run the unchanged named baseline only if the assignment authorizes test execution. Do not edit production, test or fixture files in this task. No browser/device/provider action follows from the package alone.

## Steps

1. Revalidate the current source and all global entry paths. Confirm New, template, compact template and empty-state actions use the same creation action; compare the exact current POST with the route/service precondition. Keep source finding separate from observed runtime failure.
2. Confirm the project-list DTO, active-project semantics and selector behavior. The list filter is not a creation source; a repository registry ID is not a local path. Inspect `CycleGadget` off-roster behavior and require explicit current-list membership at submission. Do not copy StartAgent's remembered/first default or incorrect archived-field spelling.
3. Record D13 branch A or B. For A, record accepted G11 interaction, explicit selection, default-title/template behavior, request capture, cancel/unmount and known/unknown/acknowledged recovery. A recommendation is not acceptance. If B is chosen, return the required lifecycle-design questions and stop the implementation dependency.
4. Trace real create persistence and failure boundaries. Use actual ApiError status/payload code, not HTTP class or message text, to identify the proved 400/repository_required and 409/no_repository refusals. Specify an assertion-only fault after save proving generic500 can retain a Program. Record which known refusals precede persistence, which errors can follow a save, and how an acknowledged ID survives reveal/list failures. Do not promise cancellation, global exactly-once creation or identify a new Program by matching its title.
5. Establish the V11 baseline and fixture provenance when execution is authorized. The current `program.drafting.json` was not recorded from a Fast-cycle project-create request. Name the sole real HTTP capture owner, coherent cross-response IDs and proposed fixture files rather than repurposing that fixture as proof. The independent refusal/post-save fault case writes no capture.
6. Confirm the owned edit set and UI geometry/focus cases. Existing Run as a program and raw-repository API mode remain unchanged. No new project registration, raw-path picker, navigation rewrite, backend lifecycle change or Start action belongs here.

## Acceptance and output

Return accepted D13/G11 text or the exact unresolved choice; actual baseline revision/instructions/tool readiness; current request/response/side-effect trace; existing versus proposed cases; fixture capture plan; and the bounded owned files for HS-T11-02. If testing is not authorized, say so and do not invent a baseline result. Other stories' decisions are not prerequisites.

This task can finish with a decision pending, but HS-T11-02 remains blocked. Use the [completion report](../COMPLETION_REPORT_TEMPLATE.md), marked contract/characterization rather than implementation.

## Rollback and stops

No product rollback should be needed. Stop for branch B, conflicting instructions, source drift that changes the seam, unsafe real-service fixtures, unavailable current project identity, required ownership expansion or an unexplained failing baseline. Ask for the smallest scope/decision amendment. Do not change tests to make characterization pass.

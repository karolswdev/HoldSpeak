# Decisions and gates

**Historical draft, not the current backlog.** Detailed planning has resumed in the [HS- hierarchy](EXECUTION_INDEX.md); this earlier outline remains unapproved reference material and grants no implementation permission.
A gate is an explicit evidence requirement, not an extra approval ritual. The current repository fast cycle remains in force. These gates prevent an agent from turning an unproved hypothesis into a code change or expanding this task.

## Candidate target decisions not yet accepted

- D01 Reuse existing Desk query ownership for Program detail only; preserve its consumer-facing shape unless a documented caller need requires the smallest change.
- D02 Introduce one small public interactive turn handle owned by ThreadService, not a universal execution framework. Completion is tied to final persistence, not polling a private running flag.
- D03 Relocate the already-shared project-update helpers into a focused common module and replace private cross-layer imports. Policy outcomes and authority inputs stay unchanged.
- D04 Project checkpoint recoverability locally and show it in both ledger branches. Pin failure stays nonblocking; no automatic retry, history rewrite or extra live Git probe on ordinary reads.
- Preserve invariants I13–I15: memory freshness/admission and decision reader distinctions. Research questions do not authorize implementation.

## Bounded technical decisions the receiving agent may settle

| Gate | Owner task | Evidence required | Permitted decision | Stop condition |
| --- | --- | --- | --- | --- |
| G00 Baseline | T00 | Current SHA, working tree, instructions and path/symbol drift | Re-anchor package to equivalent current code | Conflicting ownership, changed product behavior or missing authorization |
| G10 Program read shape | T10 | Caller contracts, key collision census, event/reload/apply ordering tests | Use `useQuery` directly with the existing client/key helper, or minimally adapt `usePrimitiveDetail` if semantics remain exact | Requires global cache defaults, endpoint semantics or cross-app migration |
| G20 Turn contract | T20 | Current Thread start/persist/fail/cancel/event paths plus Ask and Calls tests | Exact handle type/name/location and subscription disposal policy | Cannot identify a reliable persisted terminal boundary; needs durable-job schema or changes to approval/late-answer behavior |
| G40 Checkpoint classification | T40 | Actual pin outcomes, no-worktree behavior, imported/history rows and handoff matching | A Program-local pure projection from existing wire data with honest legacy fallback | Existing data cannot distinguish states and new persistent schema/API semantics are required |
| G41 Pin message safety | T40 | Actual `pin_note` producers | Display a safe plain failure category; retain original diagnostic through established safe disclosure only | Raw diagnostics may reveal secrets or unnecessary absolute paths; no known safe mapping |
| G90 Completion | T90 | All accepted task reports, focused tests, quick check, required shots | Mark core plan built/verified to the actual evidence tier | Skipped/failed required check or unresolved invariant regression |

The draft handle's semantic operations are proposed in [Target design](TARGET_DESIGN.md); any example names there are **proposed**, not existing APIs. A gate may choose exact syntax but may not weaken semantics.

## Research decisions remain parked

R01 (reserved research question; brief not authored) tests the global canonical-count/legacy limit boundary with two projects before proposing a change. R02 (reserved research question; brief not authored) traces whether current summary text was derived from the corrected transcript. Both are discovery-only and do not block any accepted implementation scope. Constructor-level `ChannelService.automation_origin` recomposition is also deferred: a convenience refactor has not yet justified risking provenance or send recovery.

## When facts change

Record old claim, new evidence, affected task IDs and smallest plan amendment in the task report and package changelog. If a seam is already fixed, verify it and close that task as already satisfied with evidence; do not reimplement it. If repository guidance changes, follow the current instruction and explain the change. The package is not a license to restore an older architecture.

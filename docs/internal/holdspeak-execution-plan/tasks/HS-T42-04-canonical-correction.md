# HS-T42-04 · Correct canonical projects without moving other filing axes

**Conditional implementation task.** Requires [HS-T00](HS-T00-baseline.md), [HS-T42-01](HS-T42-01-contract.md), accepted correction subset of G42 and an assigned code lane. It may proceed independently of the meeting-create tasks if only correction is selected. Parent: [HS-S42](../stories/HS-S42-decision-filing.md).

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [G42](../stories/HS-S42-decision-filing.md#g42-local-decisions-before-implementation), [outcomes/matrix](../stories/HS-S42-decision-filing.md#target-interaction-and-outcome-custody), [source map](../stories/HS-S42-decision-filing.md#exact-source-map-and-ownership); [V42](../VALIDATION.md#v42-meeting-decision-filing-verification); [I13/I16/I17/I18/I21/I23/I25](../INVARIANTS.md); actual baseline/contract report and current scoped web instructions.

## Owned files

Existing production: `web/src/desk/pullouts/DecisionPullout.tsx` and `web/src/desk/components/DeskFilingStrip.tsx`. Reuse current classes/public primitives; a new CSS/module/API is not part of this task. Tests: the strip/pullout cases and new real producer chain assigned in V42, coordinated with creation work. Backend membership, source history, refs and admission code remain read-only.

## Steps

1. Model canonical lookup for the current source decision as loading, verified none, exactly one valid record, ambiguous or unavailable. Check nonempty string IDs and actual response status/shape. Key the state to the current source ID; a late A response cannot activate B's filing controls or briefly leave A's target enabled. Do not select an arbitrary first record.
2. For one resolved record, keep source `objectRef`/`objectId` for collections and drawers; introduce only a narrow project-axis target override or equivalent composition. Proposed property names are not existing APIs. Undefined legacy behavior, resolved canonical target and blocked unresolved target must not collapse to the same falsy fallback.
3. Read current canonical project membership separately from retained source membership. Label canonical projects as the editable current decision filing; disclose retained source projects separately without silently deleting/migrating them. Do not union both sets into a remove-all action. Retain the actual relation kind. Implement only the accepted G42 member-only or all-relationship control: neither matching project ID nor a checked chip permits silently converting/deleting a source/output/related edge. Keep legacy/noncanonical consumers' relation behavior unchanged. Keep the source's collection/drawer actions unchanged. A verified legacy-only decision retains its existing source project actions; ambiguity/unavailability cannot masquerade as that state.
4. Keep meeting/source provenance and historical About context unchanged. Explain that removing an explicit decision project may leave visibility through source or meeting links. Do not infer actual inherited membership from stale tags; a general scope explanation is preferable to an unverified project list.
5. Check non-OK status and response shape on every touched read/write before success feedback. Preserve current admission, optional revision and replay contracts. Capture exact target ref/project/verb per press, guard overlapping toggles and ignore stale UI completion for another identity. Validate the returned ref/project/member acknowledgement separately from current state; an acknowledged DELETE with removed=false is not a performed removal. A client read guard is not revision-CAS. A known write followed by a failed read remains known; an unknown write requires read reconciliation before another effect, not an automatic inverse toggle.
6. Create the bounded new producer/needed fixture subset if correction-only is assigned; otherwise extend the task02 producer under coordinated ownership. Exercise the actual canonical chain with PUT→relationship GET→DELETE using `decision_record:<id>`. Assert canonical membership changes and retained source tags, record sources and meeting association do not. Preserve the legacy alias tests, launch-owned refusal/replay semantics and KB/directory behavior; do not weaken kernel admission to make the test app convenient.
7. Add app/strip cases for C42-08–13 and C42-15: canonical-only, source-only, mixed edges, multiple/no/error mappings, A→B stale results, member/source/output/related and unknown/malformed relationship rows, HTTP 4xx/5xx and post-write refresh failure. Prove the selected explicit role-change/removal contract and no automatic recovery mutation of a known non-member edge. Show the exact project ref in request assertions while KB operations still use the source ref. No success sound/count after refused/unconfirmed mutation.
8. Run the named task04 subset, then the full accepted-slice budget before independent review. Do not infer passing visual/correction proof from old directory-only strip tests.

## Acceptance

Current canonical project membership is visible/editable under the correct identity without redirecting source collections/drawers. Source memberships and inherited/historical context are not erased or falsely represented. Legacy-only behavior remains; unknown/ambiguous mapping blocks the affected effect. Actual status and effect identity govern feedback/recovery.

Return [completion evidence](../COMPLETION_REPORT_TEMPLATE.md) and exact request/store/source assertions. Correction-only completion must be labeled as that subset, not the whole meeting-create journey.

## Rollback and stops

Reverse only the scoped UI/strip/test change; never delete canonical/source edges as rollback of code. Stop for required source-history correction, identity cardinality not covered by G42, new backend aliasing, collection migration, unsupported command replay or an out-of-scope styling/primitive change. Hold for independent verification and separate shipping authority.

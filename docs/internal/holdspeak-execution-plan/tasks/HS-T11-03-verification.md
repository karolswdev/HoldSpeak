# HS-T11-03 · Prove the creation journey and hand it off

**Status:** conditional verification assignment, not shipping authority. Requires [HS-T11-02](HS-T11-02-implementation.md) and its final diff/evidence. Parent: [HS-S11](../stories/HS-S11-program-creation-context.md). A reviewer must be independent of the implementation; current repository role instructions decide who performs each part.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); accepted D13/G11 report; story [matrix](../stories/HS-S11-program-creation-context.md#acceptance-matrix), [outcome contract](../stories/HS-S11-program-creation-context.md#proposed-interaction-and-truthful-outcomes) and [owned paths](../stories/HS-S11-program-creation-context.md#exact-source-map-and-ownership); [V11](../VALIDATION.md#v11-program-creation-verification); [I02/I16/I17/I18/I21/I24/I25](../INVARIANTS.md); implementation report and actual current diff. No full-library onboarding.

## Scope

Review and run authorized named checks; no production/test/fixture edits in this task. Return failures to HS-T11-02, then verify the new final state. Do not weaken expectations, regenerate fixtures to hide a mismatch or broaden authority to live providers/repositories.

## Verification sequence

1. Verify assignment, accepted branch and actual source revision. Check that only the declared files changed and the backend still requires creation context. A new unbound state, project auto-selection, raw-path feature or shell move is a scope failure.
2. Inspect the producer tests independently. They must use real create/repository resolution, the actual HTTP tuple and temporary local data. Assert semantics beyond fixture shape: selected project/repository, Drafting state, no launch and no persisted Program for the specifically proved pre-write refusals. A mocked `_project_source` from a preservation test is not the new resolver proof. Check exact ApiError status/code classification and the assertion-only post-save checkpoint fault: generic500 must coexist with the exact new persisted ID and zero launch, with no title-based inference.
3. Inspect fixture provenance. New create response must come from the matching project/Fast-cycle request, not the older overnight/planned drafting fixture. Only the four declared wire files may be new/rewritten. One producer alone owns all four; captured roster IDs must match the successful request/Program and the browser’s selected no-repository refusal. The second producer writes no fixture. Verify semantic equality of IDs even though `_fixture` fences only shape. Confirm the test-only request/response metadata stays outside the real response body and consumers replay `response.body`; the refusal ID comes from recorded `request.json`, not a nonexistent response field. Record nondeterministic fields honestly; shape equivalence is not byte-for-byte semantic equality.
4. Rerun V11 with all fixture-writing flags disabled, after the final edit. Record exact collection/test counts, skips, command/exit status and logs. Run source-defined type/architecture checks. Baseline/expected-red/final results must remain distinguishable.
5. Trace C11-01–12 across producer and app proof: all entry points, explicit current-list selection, filter independence, immutable request, one in-flight press, known versus uncertain result, acknowledged-ID recovery and no late reveal after abandonment. The request assertion and real producer contract must match. Preserve existing action/project and note entry behavior.
6. Independently inspect the proposed glass test before running it: interception is installed before navigation, all Program mutations are intercepted or fail closed, known refusal data is captured wire, isolated DB count stays zero and `finally` closes the browser/server. A disabled engine ticker alone does not make HTTP creation safe. Run the named V11 browser test with non-skipped proof and inspect its actual shots.
7. The assigned integration owner runs the current quick check and inspects the actual stages/shots. Confirm 1440 and 393, including the creation well, unavailable/empty/error states and a narrow window inside a wide Desk. The generic sweep does not substitute for the specific new-well browser test. If either required lane is skipped or misses its case, report incomplete proof.
8. Verify keyboard focus, selection, Escape/cancel and 44px compact hit ownership through an authorized browser check when required for the claim. Unit DOM assertions alone do not prove geometry/touch behavior. Do not use a real repository create as a visual test; use the safe rig/fixture lane.
9. Recheck the final diff/state after all corrective edits. Preserve no automatic retry, no false `Nothing changed`, no guessed ID and no automatic Start. A green command does not accept the proposed UX or authorize shipping.

## Acceptance and output

If both S11 and S13 are accepted, coordinate with T13-02/03 on [the creation-to-Room integration gate](../VALIDATION.md#creation-to-room-integration-gate). S11 may be verified independently; do not claim the same-request Room journey merely because both isolated suites pass. The conditional joint consumer uses the same recorded request/ID as the real full-hub producer and needs one serialized owner of `programs.app.test.tsx`.

Return [completion report](../COMPLETION_REPORT_TEMPLATE.md) with accepted decision, code/fixture ownership, producer-to-UI proof, exact passing/failing/skipped checks, geometry evidence or explicit gap, remaining decisions and rollback. Mark the slice incomplete if required proof is missing. Report `ready for assigned shipping review`, not shipped; retain current SHIP gate.

## Stop and rollback

Stop for changed semantics, out-of-scope edits, nondeterministic fixture values asserted as stable identity, dangerous fixtures, a swallowed failure, broad recording or incomplete current-state proof. No reset/restore/clean. A code reversal cannot undo a server-side Program; unknown results must not be converted to safe-to-retry. Corrective implementation returns to the owning task, followed by renewed independent verification.

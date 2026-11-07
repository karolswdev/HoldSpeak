# HS-T42-05 · Prove the accepted meeting-decision journey

**Conditional independent verification task.** Requires the implementation reports for the accepted G42 subset and the assigned review/test role. No production/test/fixture edits or shipping authority. Parent: [HS-S42](../stories/HS-S42-decision-filing.md).

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); accepted G42 and baseline report; story [matrix](../stories/HS-S42-decision-filing.md#acceptance-matrix), [source map](../stories/HS-S42-decision-filing.md#exact-source-map-and-ownership) and [outcomes](../stories/HS-S42-decision-filing.md#target-interaction-and-outcome-custody); [V42](../VALIDATION.md#v42-meeting-decision-filing-verification); [I13/I16/I17/I18/I21/I23/I25](../INVARIANTS.md); actual final diff and task02/03/04 reports as applicable.

## Verification

1. Verify accepted scope, current source and exact owned paths. Do not mark the entire story complete from a correction-only assignment. Confirm there is no backend schema/lifecycle change, provenance rewrite, source-edge migration or new recovery engine.
2. Independently inspect the producer test: real canonical route and retained source, actual admitted canonical membership PUT/GET/DELETE, real principal checks and isolated DB. Old legacy `_decide`/mocked app responses do not prove the new chain. Assert identity and preserved source/meeting facts, not just fixture shape.
3. Trace each applicable C42 case to producer, app or browser proof. Missing/malformed creation, partial filing and failed read must not result in new creation/fallback; a known receipt must remain known. Verify the actual persistence boundary and late-draft protection, including close/reopen. Do not call a local guard cross-browser exactly-once.
4. Inspect correction separately: only the Projects axis uses canonical identity; source collections/drawers and legacy-only correction keep their contracts. Mixed memberships remain distinguishable. A lookup error, multiple records or stale A response cannot choose a target. Historical About/meeting visibility is not promised to change on DELETE.
5. Run V42's named final suites with fixture-writing disabled after the last edit. Record collection counts, skips, commands, logs and exits. Do not regenerate fixtures, weaken tests or omit a required failing case. Return fixes to the implementing task and repeat final validation.
6. Inspect safe browser setup before running: isolated HOME/DB/hub, fake/off external capabilities, authorized local server/build/browser, and no owner data. Exercise actual meeting well/correction states through the bounded real-browser lane. Require non-skipped cases, screenshots, keyboard/focus/mic-target behavior and real compact/narrow hit ownership. Injected faults are not live incidents.
7. The current integration owner performs quick check and inspects real stages and shots. A no-change exit, skipped browser, tolerated no-test selection or generic sweep that misses the new state is not proof. Verify current comparison base and platform cache. Independent app tests and a server fixture do not by themselves prove a rendered complete journey.
8. Recheck final diff/state and report actual remaining gaps. Green checks do not approve the proposed UX or grant commit/PR/push/merge/deploy permission.

## Exit report

Use the [completion report](../COMPLETION_REPORT_TEMPLATE.md): accepted subset and decision, producer/consumer identity proof, known/unknown recovery behavior, source/axis preservation, exact checked files, fixture provenance, actual browser evidence, remaining limits and rollback. Mark blocked required proof incomplete. Hold for the assigned shipping review.

## Stops and rollback

Stop for uncertain effects, hidden source migration, unsupported legacy inference, dangerous fixtures, swallowed HTTP errors, identity guessed from text or missing final-state verification. Do not clean/reset another lane or change product data to force a passing result. A code reversal cannot undo already acknowledged creation or filing.

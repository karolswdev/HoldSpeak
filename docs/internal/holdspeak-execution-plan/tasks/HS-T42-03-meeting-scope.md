# HS-T42-03 · Make meeting scope and the creation receipt visible

**Conditional implementation task.** Depends on accepted G42, [HS-T42-01](HS-T42-01-contract.md) and [HS-T42-02](HS-T42-02-creation-receipts.md), with an assigned code lane. Parent: [HS-S42](../stories/HS-S42-decision-filing.md).

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [G42](../stories/HS-S42-decision-filing.md#g42-local-decisions-before-implementation), [outcomes/matrix](../stories/HS-S42-decision-filing.md#target-interaction-and-outcome-custody), [source map](../stories/HS-S42-decision-filing.md#exact-source-map-and-ownership); [V42](../VALIDATION.md#v42-meeting-decision-filing-verification); [I16/I17/I18/I21/I23/I25](../INVARIANTS.md); predecessor reports and current web UX/surface contracts.

## Owned scope

Existing production: `web/src/meetings/MeetingDecideWell.tsx`, optional narrowly scoped `web/src/meetings/meeting-decide.css`, and the meeting-context read/input portion of `web/src/desk/decide.ts`, coordinated after task02. Reuse existing surface controls and workspace draft helpers without changing their general implementations. Tests/fixtures/browser target are only those assigned in V42. No new screen, app, API, storage table or generic selector.

## Steps

1. Replace the highest-ranked-or-null meeting context with explicit loading, known candidates, no association and lookup-failed states. Read current active choices only as needed for an intentional alternative project; do not confuse meeting association DTO IDs with project-list IDs. Guard stale read completion and preserve newer explicit scope.
2. Show accepted G42 scope beside the title before Save. One known project can be visibly preselected only under the accepted policy. Multiple candidates require a choice, including deliberate unfiled; failed lookup cannot silently mean unfiled. Keep retry read-only. Do not mutate meeting associations or canonical membership while merely choosing.
3. Preserve the keyed-per-meeting wrapper, existing title persistence, shared microphone/input behavior and one-primary-action rule. Capture meeting/title/scope at submission and prevent same-surface overlapping presses synchronously. Do not claim cross-browser exactly-once.
4. Consume task02's explicit outcome. Keep a created receipt with both acknowledged IDs and separate filing status before trying refresh/reveal. A failed filing cannot leave the same submitted title under a generic Save/Try again action that calls creation. Offer same-ID read/filing recovery. If creation is unconfirmed, retain that distinction and never guess an identity from the title.
5. Use the bounded existing-workspace receipt/draft strategy accepted in G42 and specified in the story. Persist the captured pending/unconfirmed attempt before sending, without inventing IDs; retain it after timeout separately from editable text. Test timeout followed by close/reopen and successful-storage reload: it must not restore generic Save for that same attempt. A late old response cannot clear a newer title/receipt or move to another meeting. Closing is not server cancellation. On reopen, reconcile acknowledged IDs against current server data before further effects. Missing state cannot be fabricated as failed/no-write; do not introduce a new journal or reuse `useWriteReceipt`'s closure retry as an implicit create retry.
6. Preserve existing source-decision opening through the acknowledged source identity and canonical lookup. Reveal/read failure does not negate the created record. Do not let an abandoned flow force late navigation; leave its durable server result intact.
7. Add canonical-response-backed app cases for C42-01–07 and the actual state/receipt/draft boundaries. Update the old compatibility-only meeting mock so the revised meeting path is genuinely exercised. Keep global New Decision and unrelated source-edit tests as preservation proof, not a reason to retain ambiguous fallback.
8. Implement the scoped safe browser cases in V42 for the actual well and feedback, including single/multiple/unavailable context, pending/failed filing and narrow layout. Distinguish injected fault state from real producer proof. Run named final tests after the last edit, not a broad suite.

## Acceptance

The owner sees the decision's scope and a truthful created/filed result. No write occurs before an intentional Save; no unknown/partial result is mislabeled as no creation; no generic retry duplicates an acknowledged decision. Drafts remain meeting-specific and newer edits survive late work. Existing source/canonical identities and context remain separate.

Return [completion evidence](../COMPLETION_REPORT_TEMPLATE.md), including actual receipt persistence limits and UI/browser gaps. Creation is not fully ready until independent task05 proof; source tests and a mocked receipt are not live behavior claims.

## Rollback and stops

Reverse scoped UI/context/test changes only; do not erase created records or workspace data beyond this task's own test fixtures. Stop for an unaccepted scope choice, required generic draft-store change, unsupported recovery after reload, source-history mutation, new route/permission or unsafe browser setup. Request a bounded amendment and preserve known IDs.

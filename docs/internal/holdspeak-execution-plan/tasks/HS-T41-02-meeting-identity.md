# HS-T41-02 · Make meeting owner and person navigation truthful

**Conditional implementation brief; execution not authorized.** Depends on [HS-T00](HS-T00-baseline.md), [HS-T41-01](HS-T41-01-contract.md) and an accepted G41 Meeting subset. Parent: [HS-S41](../stories/HS-S41-director-person-identity.md).

## Mandatory context

[Safety](../AGENT_START.md#authority-and-checkout-safety); story [Meeting interaction](../stories/HS-S41-director-person-identity.md#meeting), [matrix](../stories/HS-S41-director-person-identity.md#acceptance-matrix) and [rollback](../stories/HS-S41-director-person-identity.md#rollback-and-stops); [V41](../VALIDATION.md#v41-director-person-identity-verification); [I16/I17/I18/I23/I25](../INVARIANTS.md); current scoped guides. Read only the named producer/read/control symbols.

## Owned change and procedure

Production edit: existing `web/src/pages/cores/history/MeetingDetail.tsx` only. Tests/producer ownership: the accepted T41-02 subset in V41; coordinate shared files with T41-03/04. Other source paths are read-only, not permission to alter APIs or identity storage.

1. Establish named baseline and real producer captures before replacing assertions. Preserve custom owner strings, proposal-keyed task/due drafts, Me/blank choices and current Confirm payload. Collapse exact duplicate display-name options; do not case-normalize or assign a relationship by display name. Use clear name-versus-person wording within current shared controls.
2. Give the existing Door lookup explicit pending/success/failure and read-attempt identity. Preserve wanted action IDs, duplicate/conflicting mapping suppression and existing source checks. A late promise must match both current identity and read attempt before publishing. Disable stale destinations while pending; absence remains inconclusive.
3. Add explicit read-only Check without creating a new event/cache/registration layer. It may reissue Door GET only, never Confirm, alias POST, Save or Send. Keep existing exact `openPerson` navigation only for known action-ID metadata. Preserve the current Project menu; it opens the project, not a selected owner row. Do not widen Room eligibility.
4. Keep existing task/due/confirmation/dismissal/completion, source navigation, menu focus and one-primary-action behavior. On protected/read failure, retire stale protected lookup content while preserving ordinary drafts. No People metadata enters persisted draft storage or ordinary producer payloads.
5. Extend the named app suite with actual producer fixtures plus labeled pending/absent/failure/conflict/late-response variants. Correct stale test selectors to the actual More menu; an absent old `proposal-person-btn` is not proof the current menu is safe. Cover A→B→A and repeated Check ordering.

## Acceptance and handoff

Prove C41-01/02/03/11 and the Meeting portion of C41-12 with V41's assigned app/producer/browser evidence. Record baseline, new-case red and final results separately; do not claim the Room resolution journey complete if T41-03 is not assigned. Return [completion report](../COMPLETION_REPORT_TEMPLATE.md) with exact payloads, read-state behavior, remaining identity/navigation limits and diff ownership.

Rollback is limited to owned UI/test edits; no ordinary record/alias should have been changed by the new read affordance. Stop for a required backend person-ID field, generalized navigation target, private persistence, changed confirmation semantics, unexpected writes or unsafe testing. Shipping remains separate.

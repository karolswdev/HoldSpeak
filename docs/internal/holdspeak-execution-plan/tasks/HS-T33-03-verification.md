# HS-T33-03 · Prove the People promise recovery journey

**Independent verification assignment; no shipping authority.** Requires final [HS-T33-02](HS-T33-02-request-recovery.md) diff/evidence. Parent: [HS-S33](../stories/HS-S33-people-add-recovery.md). Current repository role instructions decide who runs each lane.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); accepted G33-A report; story [matrix](../stories/HS-S33-people-add-recovery.md#acceptance-matrix), [limits](../stories/HS-S33-people-add-recovery.md#g33-choices-and-limits) and [stops](../stories/HS-S33-people-add-recovery.md#rollback-and-stops); [V33](../VALIDATION.md#v33-people-add-recovery-verification); [I04/I16/I17/I18/I21/I23/I25](../INVARIANTS.md); final actual diff and predecessor evidence.

## Verification

1. Check accepted branch, source drift and one-file production budget. No new endpoint, store, schema, ordinary persisted receipt or global retry engine. Source-only plan facts are not runtime results.
2. Independently trace the raw producer chain with temporary encrypted state. Verify create uses varying IDs, same-ID acceptance returns one existing commitment and terminal replay does not reopen it. For post-commit faults, inspect actual stored state before/after response loss. Distinguish full HTTP admission from router tests with injected principals; remove both automatic auth headers for refusal cases.
3. Inspect the exact public relation/request/commitment envelope and malformed/mixed-read handling. Check absent arrays or roster fallback cannot become authoritative absence, and no read automatically accepts. Unknown creation cannot silently produce another POST; matched words are never an operation identity.
4. Exercise concurrent click/Enter, unrelated busy operations, known request in Asked-of-you, two person reads finishing out of order, Back/close, fold/lens, protection clearing, same-person refresh and draft edits including another window's away/back sequence. Exercise real lost/locked test-key readiness through the service/route, not only fabricated key-status errors. Verify generic503 readiness probing, ready-outage retention, nonready clearing and uncertain-readiness fallback. Validate call counts and exact IDs, not labels alone.
5. Verify saved acknowledgements survive refresh failure; completed/dismissed linkage remains terminal. Newer drafts survive all delayed outcomes. Full unmount/reload loses the new receipt as documented, and no UI copy promises durable or cross-window exactly-once behavior.
6. Run the accepted V33 budget with recording flags off after the final edit. Record collection/execution counts, skips, exits and proof artifacts. Inspect the real-browser mutation allowlist before execution, exact synthetic identities, actual screenshots/focus at wide/phone widths and final attempted request ledger. Current integration-owner checks remain separate and cannot be replaced by a zero-tests green exit.
7. Review final diff/state after corrections. Report C33 rows passed/failed/blocked, actual authority/custody limits and rollback using [completion report](../COMPLETION_REPORT_TEMPLATE.md). Passing fixture/browser proof does not establish live provider work, privacy redesign or accepted product scope.

## Stops and rollback

Do not edit production/tests or weaken assertions in this verification task; return findings to T33-02 and recheck its final state. Stop for any unproved request identity, owner protection, draft preservation, effect isolation or geometry requirement. No duplicate cleanup, new acceptance, data deletion or repository publication follows from verification. Any code reversal is separately assigned and cannot erase already saved promises.

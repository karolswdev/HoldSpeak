# HS-T32-03 · Carry the same recovery identity to every supported action

**Conditional consumer implementation/proof task.** Requires [HS-T32-02](HS-T32-02-recovery.md), its accepted G32 contract and scoped assignment. Parent: [HS-S32](../stories/HS-S32-delivery-recovery.md). No separate shipping authority.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [choices](../stories/HS-S32-delivery-recovery.md#g32-choices-and-proposed-first-branch) and [matrix](../stories/HS-S32-delivery-recovery.md#acceptance-matrix); [V32](../VALIDATION.md#v32-delivery-recovery-verification), exact consumer paths and owned outputs; predecessor report; [I10/I16/I18/I21](../INVARIANTS.md).

## Owned scope

Existing production: `web/src/desk/programs/ProgramWindow.tsx`, `web/src/desk/programs/types.ts`, narrowly needed transport forwarding in `web/src/desk/programs/api.ts`; `holdspeak/services/brief_words.py`, `holdspeak/services/briefing_service.py`; `holdspeak/sdk/programs.py`, `holdspeak/commands/program.py`, `holdspeak/mcp/families/program.py`. The task02 route/service/delivery contract is coordinated read-only unless a bounded amendment is agreed. No Calls engine, generic question lifecycle, new endpoint, app/window or source-storage changes.

Tests/fixtures/browser: only V32's task03 list and eight named wire outputs. Producer and fake edits shared with task02 are serialized. Proposed `tests/e2e/test_program_delivery_recovery_glass.py` is an isolated UI proof lane, not a live GitHub test.

## Work

1. Add the explicit Check verb to `VERBS.delivery`; returning a server choice alone renders no button today. Consume task02's safe `turn_item` recovery/status/ledger-ID projection in typed `YourTurnItem`, then include the displayed ID in `DecideBody` on each accepted action. Do not assume `ProgramCheckpoint.undo` is a declared UI field or fetch the latest ID at press time to bypass stale-context protection.
2. Keep Done visible and delivery outcome separate. Explain known PR, uncertain create, legacy identity limits, owner-requested/unconfirmed merge (which need not have started), queued result and action-specific errors in ordinary language. Show safe recorded PR links only. Do not expose raw stderr/credentials or announce Delivered merely because Check/merge request returned successfully.
3. Align `brief_words` questions/consequences/outcomes and `BriefingService` labels with the available choices. Check reads status; Merge requests the specified merge and may await confirmation; Skip ends local follow-up without a provider command and does not delete/close/cancel a PR. Under the accepted G32 distinction, retain supported known no-effect wording, but do not render “not delivered” for queued/unconfirmed effects. Keep any acknowledged safe PR identity and the unresolved observation visible in the agreed receipt/projection and settled briefing output after the held row disappears. The current choice-only settled phrase cannot by itself prove that result; coordinate any bounded representation amendment with task02 rather than silently selecting a schema. Existing initial control-level behavior and unrelated held-item words remain intact.
4. Store the expected delivery checkpoint in newly composed frozen briefing content. Answer using that stored value; a re-read current item must not replace it. Unbound legacy pages must refuse the protected write. A successful Check can consume that page's one answer; require fresh current context for the subsequent Merge rather than converting the old response into new permission.
5. Add optional binding forwarding to SDK, CLI and MCP schema/handler under the accepted compatibility contract. Inputs without a required binding receive a truthful refusal before effects. Never auto-fill it by looking up the newest row. For direct channel `decide_item` callers without a bound displayed identity, preserve non-delivery behavior and explicitly refuse protected delivery writes; do not retrofit Calls readback/approval semantics in this slice.
6. Record the exact V32 response fixtures from real isolated producer routes after the backend semantics are implemented. Shape parity alone is insufficient: assert actual ID/action/status values, expected token in the browser/client request and absence of unexpected effects. Do not manually fabricate source-of-truth fixtures or rewrite unrelated outputs.
7. Extend the window app test and safe browser lane for Check→open, already-merged, failed read, queued result, stale row and legacy/uncertain blocks. Browser writes are intercepted with producer outputs; it proves the real controls/requests/layout, not a real remote merge. Integration tests separately prove the route/service/fake-command chain.
8. Verify old briefing page→new ledger row with the same Merge choice refuses; fresh page is bound; duplicate/stale presses cannot silently select another PR. Test CLI/SDK/MCP forwarding and unbound refusal, and preserve existing non-delivery Calls decisions. Run the accepted V32 budget and inspect actual 1440/393/narrow layout and focus.

## Exit, rollback and stops

Return the accepted consumer support matrix, exact field/fixture producer trace, observed requests, tests/screenshots and unresolved legacy restrictions. Together with task02 this is one coherent change; hold for independent task04 and separate SHIP authority.

Rollback reverses backend/consumer contracts together while retaining historical receipts. An older server ignores the request marker and can reoffer Merge; retain a reviewed compatibility refusal or do not resume that downgrade while markers remain. Stop for additional channel authority, an unavailable frozen-binding seam, a need to rework generic briefing/Calls behavior, unbounded fixture rewrites or a real GitHub/device/owner-state dependency. Do not hide unsupported actions or report mocked provider results as live proof.

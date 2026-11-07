# HS-T13-03 · Prove the project-to-Program journey

**Independent verification assignment; no shipping authority.** Requires final [HS-T13-02](HS-T13-02-room-continuity.md) diff/evidence. Parent: [HS-S13](../stories/HS-S13-project-program-continuity.md). Current repository role instructions decide who runs each lane.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); accepted G13 report; story [matrix](../stories/HS-S13-project-program-continuity.md#acceptance-matrix) and [stops](../stories/HS-S13-project-program-continuity.md#rollback-and-stop-conditions); [V13](../VALIDATION.md#v13-project-program-continuity-verification); [I02/I16/I17/I18/I21/I24/I25](../INVARIANTS.md); final actual diff and implementation evidence. No full-library onboarding.

## Verification

1. Check scope, current instructions/revision and accepted branch. Three production owners only; unchanged legacy RoomPrograms, backend filter/lifecycle and shell are preservation constraints. Return undeclared changes to the implementation owner rather than silently expanding this task.
2. Independently inspect real full-hub producer setup and its assertions: actual admitted Room/detail routes, exact project_id membership, all rows/order, no Start/tick/provider, real refusal boundary and fixture identity. The existing recorded section or recursive type shape is not sufficient proof.
3. Inspect and rerun the Programs-only decoder matrix, current/old read completion races and retained last-read UI. Malformed must not look empty; late Phase 2/3 failures must not invalidate a successful Phase 1. Preserve sibling sections and catch-up/read-marker behavior.
4. Deliver the real full coalesced `desk_changed` frame through the actual debounced hook predicate, checking the Program entry via `deskChanges` rather than forcing top-level `kind: "program"`. Check newly associated unknown IDs, moved-out rows, bursts, windows-only and known unrelated frames. Preserve current unknown-kind compatibility; don't call this a reproduced prior refresh bug.
5. Rerun V13 with recording flags off after the final edit. Record collected/executed counts, skips, exits, logs and generated proof. Run type/architecture checks and the current integration-owner gate where assigned. A no-change/empty/skipped result is not a pass for this slice.
6. Inspect the existing-file new glass node before running it. Confirm read interceptions and fail-closed Program mutation guard precede navigation, temporary DB has no created/started Programs, exact Program detail matches the row, and cleanup runs in finally. Existing Room read markers/window state are a separate allowed list, not blanket mutation permission.
7. Verify actual exact-window content, repeated/hidden existing behavior, keyboard focus and hit geometry at wide, phone and a genuinely narrowed wide-Desk window. Inspect screenshots, not a ready flag or mocked opener. Use no real provider/repository Program as a visual probe.
8. If the combined S11/S13 gate is assigned, verify [the linked creation-to-Room proof](../VALIDATION.md#creation-to-room-integration-gate): exact project-only request through real resolver, acknowledged ID across Room/detail, missing-event explicit Refresh, and persisted-but-unconfirmed fault. Confirm sole capture ownership, serialized S11 consumer edit and no fake direct-ID reconciliation in the UI. This is composed producer/consumer proof, not a single live browser transaction; standalone completion must not claim it.
9. Recheck final diff/state after fixes. Report each C13 row passed/failed/blocked, remaining decisions and rollback limitations using [completion report](../COMPLETION_REPORT_TEMPLATE.md). A Program summary/Done word does not prove delivery or private obligation completeness.

## Stops and rollback

This task does not edit production/tests/fixtures or relax assertions. Send failures back to T13-02 and verify the new final state. Stop if scope, effect guard, current identity, app admission, actual geometry or required checks are unproved. No reset/clean, deletion of Programs, automatic retry, association correction or shipping follows from verification. Reverse only separately assigned owned diff; historical read/window bookkeeping is not erased.

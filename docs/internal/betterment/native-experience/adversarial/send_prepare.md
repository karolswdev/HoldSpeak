# send_prepare — adversarial review

Workflow id: `send_prepare`  
Job: Prepare exact content and destination before sending  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_send_prepare`  
Evidence class: source and representative assertions inspected; no tests, Desk walk, provider call, or owner observation.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts in two materially different ways: an owner opens Send, previews a destination, then presses owner-only `channel.send`; or an agent/steward/automation persists `channel.prepare` for the owner to inspect in Needs you. It ends when the owner sends or discards, or recovers a failed/unknown result and returns to the document. The audit joins these paths without naming their different persistence, authority, or identifiers. `channel.preview` is a read and `channel.send` carries a preview digest (`holdspeak/channel_operations.py:181-224`, `251-296`); durable preparation has `send_id`, `prepare_operation_id`, frozen bytes, and a later owner press (`holdspeak/services/channel_service.py:563-594`).

FINDINGS:

1. **P1 — The state model is under-specified.** The assigned source is `web/src/features/channels/SendWell.tsx:1-120`, but the active species and its two paths are `web/src/desk/surface/send/SendWell.tsx:438-497,653-935`, with Needs wiring at `web/src/desk/needs/NeedsDrawer.tsx:460-500`. Owner cost: an implementer can add a second state machine, lose the frozen preview, or make an agent action look like an owner action. This fails Tenets 1, 3 and 5. Correction: split inline preview → owner send from durable prepare → owner Send/Discard; name shared `document_ref`, `destination_id`, `preview_digest`, `send_id`, `command_id`, and terminal receipt.

2. **P1 — The whole job omits destination readiness and source-change branches.** Add destination is an in-world Settings form (`web/src/desk/surface/send/SendWell.tsx:797-819`); preview and dispatch can refuse parked/changed destinations, missing documents, size limits, or account/key readiness (`holdspeak/channel_operations.py:195-218,278-287`). The source refreshes after `PREVIEW CHANGED` (`web/src/desk/surface/send/SendWell.tsx:687-705`). Owner cost: a Tuesday send can stop at a vague stale or credential state. This fails Tenets 3 and 6. Correction: add falsifiable branches with named refusal, no egress, fresh preview, and inline Add destination preserved. Preserve the existing prepared-send exception: a deleted source may still send its frozen bytes, except Brief; changed existing bytes are checked separately (`holdspeak/services/channel_service.py:669-685`). Do not replace that policy with a blanket freshness gate.

3. **P1 — Recovery and return are not a complete loop.** Existing custody keeps original bytes and the command key through lost answer, reload, and retry (`web/src/desk/surface/send/SendWell.tsx:438-485`); Needs uses the same adapter and withholds retry when provenance is unavailable (`web/src/desk/needs/NeedsDrawer.tsx:471-498`). The audit must state Back, Look, Edit, source change, and late/unknown behavior. Owner cost: duplicate effects or lost context. This fails Tenets 2, 3 and Article V. Correction: require same-key replay for unknown, a new key only for known failure, stable return to the originating `DocRef`, and a retained receipt.

## Convergence

Converge `send_prepare` with `send_commit` on the existing Send row, frozen preview, egress chip, receipt, and Needs membership; keep `send_commit` separate because it owns the external effect and owner authorization. First consumers are `project_update`, `automation_build`, `ask_whole_desk`, `meeting_aftercare`, and `mcp_tools`, which should produce existing `DocRef`/`channel.prepare` records rather than new UI. `notes_editor` and `capture_thought` reuse the existing Edit-to-`note:<id>` route and `NoteSendWells` (`web/src/desk/surface/send/SendWell.tsx:737-761`). Do not merge producer editors or every host into one wizard: draft/IME and source provenance remain host-owned boundaries.

## User experience

The composition has a credible fast path: three presses from a meeting and two from a note, with Send in view at 1440 and 393 (`docs/internal/betterment/send/RECIPE.md:170-202`). Assertions cover frozen previews, refusal/unknown states, document identity, and prepared-row order (`web/src/desk/surface/send/__tests__/SendWell.test.tsx:454-657,660-700`; `tests/unit/test_desk_needs_you.py:1194-1268`). This is source confidence, not beauty or owner acceptance. The audit must still judge row legibility with warnings/receipts and whether Needs → Look/Send returns the owner to useful work.

CONDITIONS: Add the two-path state/identifier table, destination and source-change branches, and recovery/return ownership to the audit; name the first consumers and preserve existing guards. No new interface or runtime is justified.

MISSED: (1) credential/account or parked-destination readiness, highest cost; (2) source mutation after preview/prepare; (3) Edit-to-note return and loss of original context; (4) unknown answer after reload and far-side Check.

TUESDAY: Likely yes for a saved destination, but the audit is not yet sufficient to make the failed, prepared, and return paths equally clear.

## Acceptance challenges

1. An agent prepares `project_update:<id>` to a saved folder. Within one refresh, Needs shows the exact label, destination, producer, and frozen preview; Look matches it, owner Send writes once, and the row leaves with a receipt.
2. From a meeting or note, the owner selects a destination, sees the receiver preview, presses Send, and sees the correct `document_ref` and receipt at 1440 and 393 without scroll; Edit creates `note:<id>` and returns with the same destination while the original remains unchanged.
3. After preview, park/change the destination or mutate the source. Send must refuse by name with no egress, retain context, and present a fresh preview or an explicit recovery action.
4. Let a send answer become unknown, reload, then Try again. The original `command_id` replays once, Check opens the far side, and returning to Needs or the source document never creates a second dispatch.

UNKNOWN: No test was executed; no live face, provider/account readiness, far-side result, performance, or owner acceptance was observed. The inventory's tests-exist and source-only evidence do not prove those outcomes.

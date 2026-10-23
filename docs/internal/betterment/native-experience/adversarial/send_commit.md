# send_commit — Send a stored document and retain the receipt

Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_send_commit`  
Evidence class: source and assertion inventory only; no test execution, Desk walk, provider call, or owner observation.

VERDICT: DO-NOT-RATIFY

This is a useful gap note, but it is not yet a sufficient implementation brief: its sources omit the active send contract and return path.

## Totality

The real job is: open a document, choose a saved destination, inspect the exact preview and egress, press owner-only Send, see a proof or named refusal, and find the same outcome after reload. A prepared row from an agent or automation is a second entry path, not a different commit rule. The audit correctly keeps S2 open (`docs/internal/betterment/TRACKER.md:218-229`), but omits meeting forms, notes, decisions, artifacts, Needs-you, supported channel variants, and Edit-before-Send.

FINDINGS:

1. **P0 — The evidence set misses the live workflow.** The inventory names only `web/src/features/channels/SendWell.tsx:1-700`, a project-update host (the active shared species is `web/src/desk/surface/send/SendWell.tsx:653-936`). It misses destination selection, held custody, prepared-row commit, Add destination, Edit, and closed receipts. It also omits the route/service (`holdspeak/web/routes/channels.py:136-145`; `holdspeak/services/channel_service.py:617-651`) and recovery assertions (`tests/unit/test_channel_send_recovery.py:101-198`; `tests/unit/test_desk_send.py:327-383`). Owner cost: an implementation can satisfy this record while breaking first send or replay. Tenets 2 and 3 fail. Correction: replace the source set with the species, each host/Needs consumer, backend recovery, and representative assertions; label tests unexecuted.

2. **P1 — “Retain the receipt” has no settled meaning.** The HTTP adapter returns `operation_id` and `receipt` (`holdspeak/web/routes/_room_kernel.py:26-30`), but the client keeps only `r.send` (`web/src/features/channels/channels.ts:659-660`). The row preserves channel proof and `send_operation_id` (`web/src/features/channels/channels.ts:48-82`), yet the audit never defines the user receipt or its reload lineage. Owner cost: SAVED/POSTED may lack an inspectable act record. Tenet 3 and Article V are at risk. Correction: map `command_id → operation_id → send id → receipt/proof`, then assert it through read failure, reload, and Needs-you return. Keep backend identity available for inspection, but show the user the actual destination, proof and outcome rather than raw kernel metadata.

3. **P1 — Needs-you success has no return/receipt scenario.** Send and Try again only run the adapter and refresh the list (`web/src/desk/needs/NeedsDrawer.tsx:460-490`; `web/src/desk/needs/NeedsDrawer.tsx:175-187`); the inline preview has only Close (`web/src/desk/needs/NeedsDrawer.tsx:517-530`). A successful row can disappear without leaving the owner at the document or receipt. Owner cost: a Tuesday press loses the answer to verify. Tenets 2 and 3 fail. Correction: specify and test a quiet success acknowledgement and a usable receipt/source return, plus reload and failed/unknown recovery. Clearing a completed attention row is useful; do not force navigation or a popup to replace it.

## Convergence

Converge `send_commit` with `send_prepare` on frozen preview, destination identity, egress, `retry_command`, and `send_id` (`web/src/desk/surface/send/SendWell.tsx:477-505`); keep prepare agent/automation-owned and commit owner-only. Converge with `accounts` for readiness (`web/src/desk/surface/send/SendWell.tsx:197-238`), but keep Settings state out of the receipt. `project_update` owns Delivery history (`web/src/features/channels/SendWell.tsx:123-135`); `notes_editor` stays separate because Edit creates a new Note (`web/src/desk/surface/send/SendWell.tsx:737-755`). Do not create one generic outbound page: meeting form identity and host history remain distinct.

## User experience

The source suggests a pleasing fast path: pick, read the inline preview, press Send; the Button, row egress, named refusal, and no-modal sheet fit Workbench craft. But “first real sends” remains open (`docs/internal/betterment/send/RECIPE.md:81-104`), so external arrival, proof links, narrow layout, and owner delight are unknown.

CONDITIONS: expand evidence to the active end-to-end paths; define receipt lineage and Needs-you return; add the scenarios below without adding a new runtime or approval surface.

MISSED:

1. P0: Needs-you Send success and receipt return after refresh.
2. P0: lost response, reload, same-key replay, exactly one effect.
3. P1: destination park/change or provider refusal after preview.
4. P1: Edit creates a Note, preserves the source, and retains the new receipt.

TUESDAY: The direct document path looks short, but a Needs-you press can currently lose the owner’s visible receipt and source return.

## Acceptance challenges

1. From a published meeting Summary at 1440 and 393, choose a saved file or Slack destination, confirm the exact preview/egress, Send, and find its proof after reopening the document.
2. From Needs-you, Send an agent-prepared row; refresh the Desk and confirm one receipt, one operation, and no remaining prepared row.
3. Drop the HTTP answer after dispatch, reload, press Retry, and prove the same `command_id`, one external effect, and one retained receipt.
4. Change or park the destination after preview; Send must refuse by name, show NOTHING SENT, and allow a fresh preview.
5. Use Edit, change one line, Send the Note copy, and verify the original document is unchanged and the new receipt is findable.

UNKNOWN: No tests, builds, browser shots, live provider/native sends, performance checks, or owner acceptance were run. External arrival and visual craft therefore remain unproved.

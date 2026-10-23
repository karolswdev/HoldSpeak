# feedback

Job: Know immediately what an operation did, refused or cannot yet prove  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_feedback`  
Evidence class: active React/TypeScript/Python source and representative assertions; no tests, live Desk/API/provider/native actions, captures, or owner acceptance.

VERDICT: DO-NOT-RATIFY

## Totality

The end-to-end job is: invoke a supported verb, see admission/consent and egress, watch pending/running work, receive a named terminal result, retain its receipt after close/reconnect, retry or reconcile without a second effect, and return to the exact source and target. It includes parent/child work, stale events, external uncertainty, and refusal. The inventory names “all operation hosts” while citing a distinct job: reporting a UI problem with window state, screenshot and audio. Both need an explicit boundary under this id; dropping the reporting job would repeat the scope error. The mismatched evidence is (`USE-CASE-INVENTORY.json:3497-3526`).

FINDINGS:

1. **P0 — cited sources do not implement the named job.** `web/src/desk/feedback/runtime.ts:1-53` only hydrates whether “Give feedback” is enabled and launches a picker. `UiFeedbackHost` records screenshot/audio and transcribes it (`web/src/desk/feedback/UiFeedbackHost.tsx:24-40,270-365`); its test covers save/retry/transcription (`web/src/desk/feedback/feedback.app.test.tsx:248-336`), not operation results across hosts. Owner cost: a worker can build a second mechanism while missing the lifecycle. This fails Tenets 2, 3, and 5. Correction: split user-feedback capture from operation outcomes, or preserve this id but replace its evidence with the active operation contract and consumers.

2. **P0 — the audit omits an existing operation surface and misstates the gap.** The process ledger folds pending, running, waiting, unknown, refusal, indeterminate, and terminal states (`web/src/desk/processWindowReducer.ts:32-90,116-177`) and renders state, target, child rows, retry-on-unreachable, and a footer (`web/src/pages/cores/ProcessCore.tsx:161-223`). Assertions cover lifecycle groups and refusal retention (`web/src/desk/__tests__/processWindowReducer.test.ts:65-185`; `web/src/pages/cores/__tests__/processCore.test.tsx:47-112`). This is not proof of completeness, but omission is not an observed bug. It fails Tenets 3 and 6 if an implementation brief ignores an honest surface. Correction: map this ledger, then state remaining host-local/return/egress gaps; do not invent another registry or runtime.

3. **P1 — “partial” is unbounded and recovery/return are absent.** Kernel terminal outcomes are `succeeded`, `failed`, `cancelled`, `refused`, and `indeterminate` (`holdspeak/kernel/executor.py:120-132`); partial is not automatically a universal kernel state. The brief never says which host owns partial progress, where a receipt survives close, or how retry/reconcile links to the original. This fails Tenets 1, 3, and 7. Correction: map kernel receipt/journal facts to each first consumer with operation id, parent/correlation, target, egress, reason, and return route. Keep domain-specific partial coverage in `send_prepare`, `meeting_aftercare`, or `mcp_tools`.


4. **P1 — the actual user-reporting loop must also be audited.** The window/element capture binds a generation and snapshots context, screenshot, and the hub row before starting audio (`web/src/desk/feedback/UiFeedbackHost.tsx:151-219`). Saving retains one bundle id; transcription failure keeps the saved path and retries transcription only (`:270-313,338-367,394-403`). The server uses the configured admitted speech route (`holdspeak/web/routes/system/ui_feedback.py:65-119`), so “use the same transcription engine” is already a source contract to preserve. Tests assert save retry, ASR-only retry and cancellation of late capture/grants (`web/src/desk/feedback/feedback.app.test.tsx:278-377`); they were not executed here. Owner cost: an operation-only rewrite would omit the exact reporting workflow the owner uses. Correction: cover each window's launch, selected element/state, capture failure/cancel, mic-floor conflict, saved-versus-transcribed truth, Firefox repeat capture, and a usable return/path for review. Keep the two jobs distinct within this traceable family; no second reporting service is proposed.

## Convergence

Converge with `navigation_commands` and `desktop_workspace` for invocation and reconnect (catalogue capabilities `desk.execute`/`desk.runtime` are not additional workflow IDs); `mcp_tools` for parent/child identity, egress and receipts; `send_prepare`/`send_commit` for destination, uncertainty and retry; `voice_commands`/`navigation_commands` for verb scope; and `today_followthrough` for durable return. First consumers are ProcessCore, SendWell, Ask/tool results, and Needs. Share operation id, receipt, state, target/egress and row/footer composition. Keep host-local receipts and domain-specific partial semantics separate; do not add a generic wizard or registry.

## User experience

Source suggests the process ledger can be a fast architect-facing answer: compact state tokens, named targets, child rows, and a truthful `KERNEL UNREACHABLE` footer (`ProcessCore.tsx:99-145,190-221`). No capture or owner walk was inspected, so consistency, 393 geometry, focus return, accessibility, latency, and delight are unknown. Tuesday value requires the same operation to remain findable after close and an external unknown not to look successful.

CONDITIONS: Cover both the user-reporting job and operation outcomes, with separate evidence and contracts. Reconcile the family id and cited sources with the actual operation job; include ProcessCore/reducer/kernel evidence; define state boundaries, egress, durable receipt, retry/reconcile, parent-child identity, and return; name first consumers and retained domain boundaries.

MISSED:

1. High: close/reopen or reconnect during pending/unknown work and return to the same operation.
2. High: refusal and external-send uncertainty without duplicate retry.
3. Medium: child tool/voice operation grouped under its parent while preserving exact target and egress.

TUESDAY: Not yet; a process ledger exists, but this audit does not prove that every invoked operation leaves one findable, honest result at the user’s point of work.

## Acceptance challenges

1. Run a supported local operation from an open host; assert pending → running → succeeded/refused, one receipt at the origin, one ProcessCore row, and no duplicate after refresh.
2. Invoke a supported action that the kernel refuses for a named authority or permission reason; assert the reason at the host and ledger, no success state, and one retry after the condition changes.
3. Send a stored document through a supported saved destination; assert the egress badge, frozen content/target, and an indeterminate provider result that can reconcile or retry without a second send.
4. Start a parent operation with a supported child tool, close the source window before the child ends, then reopen; assert one parent/child tree, preserved target/egress, terminal receipt, and return to the source context.

5. From the Settings window in Firefox, make three consecutive window reports with state, screenshot and audio; cancel one delayed capture and retry one failed transcription. Confirm one saved bundle per report, late results cannot replace the next report, ASR retry does not recapture/resave, the configured speech route is used, and the original window remains usable. This is proposed acceptance, not a claimed reproduction or fix.

UNKNOWN: No tests were executed. No live Desk, backend/provider, native, performance, accessibility, 1440/393, or owner-acceptance evidence was observed; source and assertions do not certify rendered behavior or delight.

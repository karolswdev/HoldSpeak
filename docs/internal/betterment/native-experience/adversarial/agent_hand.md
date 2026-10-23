# agent_hand — Hand selected work to an agent and steer it with permission

Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd`
Reviewer task: `review_agent_hand`
Evidence: source/assertions inspected; no tests, live walk, provider/native action, or owner observation.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The complete job is: select a handable item from Desk, Drawer, Room, Object
menu, or drag; inspect the brief, source cut, repository/branch,
control mode and egress; approve or cancel; deliver to one agent; then follow
pending, refused, queued, interrupted, answered and review outcomes back to the
originating work. Audit covers preview/launch and correctly says semantic
Hand is not general file transfer. It omits the backend seam,
queue cancellation, restart/resume, Hand again, and post-launch answer/review;
“steer” is too broad unless that loop is bounded with `agent_result`.

FINDINGS:

1. **P1 — the evidence corpus stops before the consequential seam.** The
inventory names only `HandSheet.tsx` and `drag.ts` as inspected
(`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:2608-2647`),
while the active operation checks admission, repository/clone, worktree, queue
and receipt in `holdspeak/services/agent_hand_service.py:334-371,394-505,539-575`
and exposes preview, delivery and queue endpoints in
`holdspeak/web/routes/agent_hand.py:88-194`. Cost: may bypass
receipt/authority/recovery. This fails Tenets 2, 3 and 7.
Correction: add these seams plus preview, edge, cap and resume assertions;
state where “steer” ends.

2. **P1 — transfer is not bounded sharply enough.** The application model
separates internal references, browser file drops and OS file-manager transfer
(`docs/internal/betterment/native-experience/APPLICATION-MODEL.md:113-140`),
and the active drag MIME carries only a semantic `kind:id` and accepts only
agent targets (`web/src/desk/hand/drag.ts:10-13,36-70`; `web/src/desk/agentHand.ts:21-35`).
Cost: may turn Hand into a file mover or mislabel an Ask attachment. This fails
Tenets 1 and 3. Correction: define
this as object-to-agent handoff; keep `explorer_repo` and Ask attachment
separate, with explicit unsupported-target/refusal behavior.

3. **P1 — recovery and return are split across surfaces but absent from the
brief.** A queued hand closes the sheet and opens an Agents row
(`web/src/desk/components/HandSheet.tsx:400-445`); cancellation is owned by
`agents_conductor` (`web/src/desk/conductor/open.ts:92-110` and
`ConductorWindow.tsx:605-621`), while restart resume/Hand again and answer
delivery live in other paths (`ConductorWindow.tsx:807-861`,
`web/src/desk/lane/LaneWindow.tsx:524-569`). Cost: after a failure, the owner
may not know where the work went or how to continue. This
fails Tenets 3 and 7. Correction: require queue-cancel, interrupted-delivery,
restart-resume, answer/review and same-worktree Hand-again scenarios, including
source-window recovery.

4. **P2 — the fast path and launch sheet do not share the same declared
operation inputs.** YOLO chooses `HandConfirm`, while Secure/Normal chooses
`HandSheet` (`web/src/desk/hand/begin.ts:39-63`); the sheet sends `review_by`
and an instruction (`HandSheet.tsx:400-414`), but the YOLO line sends neither
(`web/src/desk/hand/HandConfirm.tsx:166-184`). This may be intentional, but
the audit must say why and prove parity of source, consent, egress and receipt.
It fails Tenet 5. Correction: document the mode boundary and test each ingress
against one command/operation contract; do not add a wizard.

## Convergence

First consumers are `agents_conductor` (flight, queue cancel, Resume/Hand again),
`agent_result` (answer/review), `terminals_processes` (run/input/scroll),
`feedback` (operation outcomes), and `ask_whole_desk` (attachment).
`explorer_repo` remains separate: its resource identity and OS transfer must
not be absorbed into Hand. Share launch/flight identity, target-aware commands,
source/provenance, outcome and focus; retain semantic object-to-agent delivery.

## User experience

Source-based inference is promising: preview-before-press, named egress,
plain refusals and a 393 menu path reduce surprise (`HandConfirm.tsx:1-12`,
`web/src/desk/hand/__tests__/hand.test.tsx:457-478`). The fast line is likely
pleasant when the object is already selected. No capture was inspected, so craft,
hit areas, accessibility, speed and owner delight remain unknown; compare 1440
and 393 after recovery is specified.

CONDITIONS:

- Expand evidence to the active service/routes and recovery assertions.
- Bound transfer and “steer” against the named neighboring workflows.
- Add the challenges below, including return-to-work behavior.

MISSED:

1. Queue cancellation and restart/failed-delivery recovery (highest owner cost).
2. Answer/review/Hand-again return loop in `agent_result`.
3. Internal-vs-browser-vs-OS transfer refusal and provenance.

TUESDAY: The initial Hand is close to a useful Tuesday press, but the audit is not sufficient until a failed or queued hand has an obvious path back to the work.

## Acceptance challenges

1. At 1440, select an action in a Drawer, inspect its brief and egress, press Hand, and verify the receipt and agent row without losing Drawer context.
2. At 393 in Secure mode, use the row/menu Hand path, add one sentence, cancel before launch, then reopen the same item with no stale preview or accidental operation.
3. At the working limit, press “Start when one is free,” cancel the queue from Agents, and verify no worktree or launch starts and the source remains available.
4. Let delivery fail or the hub restart; use Send again/Resume, inspect answer/review, then Hand again on the ended launch and verify its same-worktree continuation.
5. Drop a browser file on the Hand target, or drag a supported note/action to a non-agent destination: verify a named refusal or separate Ask reference path, never a file move.

UNKNOWN: No tests were executed; no owner walk, screenshot, backend live run,
tracker/provider read, native file transfer, performance measurement, or
appearance acceptance was observed. Anchors are baseline-specific. Omission
findings are audit gaps, not observed production defects.

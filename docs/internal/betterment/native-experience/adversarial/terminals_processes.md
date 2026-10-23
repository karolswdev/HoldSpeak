# terminals_processes — inspect a running process or terminal and stop it safely

Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_terminals_processes`  
Evidence class: source inspection and existing assertions only; no execution, capture, or owner observation.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts at a run, launch, or arbitrary pane: identify the operation, launch/session, pane generation, and output; inspect; optionally send an answer/key through the guarded path; stop the intended session; see a durable outcome; recover from stale, gone, or unavailable state; and return to the same run and receipt. The audit names gaps but not this end-to-end path.

Today `Processes` reads the kernel journal but its rows have no open, inspect, or stop verb (`web/src/pages/cores/ProcessCore.tsx:92-153,161-223`). `Terminals` is a transient Panes launcher (`web/src/desk/applications.ts:616`; `web/src/desk/components/SessionPullout.tsx:240-318`); a launched agent is handled by `LaneWindow`, whose stop is bound to its session (`web/src/desk/lane/laneStore.ts:385-420`). Useful seams, incomplete job.

FINDINGS:

1. **P1 — The audit does not close ledger → run → stop → return.** The process row has operation id, target, state, and placement, but no action or link into launch/session/pane (`web/src/pages/cores/ProcessCore.tsx:92-146`; `web/src/desk/processWindowReducer.ts:232-246`). Owner cost: the senior architect must hunt Conductor or Terminals and may stop wrong work. This fails Tenets 3 and 7. Correction: define a stable cross-reference (`operation_id`, `launch_id`, `session_key`, pane generation), open the owning Lane/Session, and return to the same ledger row with its receipt. Only associate a terminal where existing evidence actually binds one; otherwise state that no terminal is associated. Not every kernel operation is a killable process. Do not make the ledger a second terminal UI.

2. **P1 — Follow/pause is absent despite a bounded viewer.** The stripped fallback jumps to bottom on new lines (`web/src/desk/surface/Surface.tsx:512-519`); xterm clears, repaints, and calls `scrollToBottom()` on every snapshot (`web/src/desk/surface/XtermPane.tsx:147-168`). `RawPane` supplies no follow state (`web/src/desk/lane/LaneWindow.tsx:838-874`). The assertion proves read-only, copy, search, and the 4,000-line bound, not an old-output position (`web/src/desk/surface/__tests__/terminalWell.test.tsx:101-149`). Owner cost: prior failure output cannot be inspected while output continues. This fails Tenet 6. Correction: preserve scroll anchor/selection until an explicit Follow; retain xterm and its bound.

3. **P1 — Stop outcome and identity do not converge with the operation ledger.** Lane stop captures `launch_id`/`session_key` and posts `/kill`, then reports local `STOPPED` only for immediate `killed` (`web/src/desk/lane/laneStore.ts:393-420`). Kernel assertions prove admitted text/key receipts (`tests/unit/test_process_input_kernel.py:119-159,190-223`), and lane assertions prove own-session routing/two-step stop (`web/src/desk/lane/__tests__/laneWindow.c2.test.tsx:408-415,493-510`), but neither covers process-row id, pane generation, reload, or uncertain kill. Owner cost: after timeout/restart, “NOT STOPPED” may be stale or unknown without return. This fails Tenets 3 and 6. Correction: specify ID mapping and receipt/state projection for success, refusal, stale, and indeterminate; reconcile on reopen without blind re-kill.

## Convergence

Converge with `agents_conductor` (`:2567-2601`), `agent_result` (`:2650-2680`), and `feedback` (`:3490-3535`). First consumers: `LaneWindow`, `SessionPullout`, `ProcessCore`, `PaneWell`, and kernel receipts. Share identity, focus, follow, and outcomes. Keep terminal input (read-only PaneWell plus armed steer/Keys), session control (Arm/Rename/Kill), and operation ledger (read-only lifecycle) separate; one universal monitor would blur authority and fail Tenets 1 and 3. `native_input` (`:3454-3490`) informs IME/focus, not generic terminal editing.

## User experience

Source craft is promising: Workbench tokens, raw/stripped honesty, search, copy, and a steady cursor are shared (`web/src/desk/surface/XtermPane.tsx:105-145`). The fast path is not pleasing: Processes cannot drill into a run, Terminals is transient, and polling steals historical position. No capture was inspected; this is source inference, not owner verdict.

CONDITIONS: Add the ID/state map, return path, and follow/pause semantics; cover stale, timeout, reload, arbitrary-pane, and launch-session cases. Preserve kernel admission, own-session, read-only/copy, and bounded-scrollback guards.

MISSED: (1) highest cost, a row opened after stop or pane-generation change; (2) hub loss after kill may have happened; (3) reading old output during new output; (4) arbitrary pane versus launch session; (5) focus/receipt after reopen.

TUESDAY: Not yet — the owner can watch or stop from specialized surfaces, but cannot move from one visible run to a confirmed, recoverable stop and return without hunting.

## Acceptance challenges

1. From a live Process row, open its lane, inspect matching `operation_id`/`launch_id`/`session_key`, Stop under Normal and YOLO, and confirm only that pane/session ends with one durable receipt.
2. With multiple screens of output, scroll up, let two polls arrive, copy an old line, then Follow; the old anchor remains until Follow.
3. Submit Stop, lose the hub response, reload, and reopen; distinguish stopped, refused, stale-pane, and indeterminate without blind re-kill.
4. Open an arbitrary Panes pane beside a launch lane, send an existing guarded key/text action, close/reopen, and verify focus, target identity, and receipts do not cross.

UNKNOWN: No tests, builds, live process/terminal walk, native/provider action, performance measurement, screenshot, or owner acceptance was performed. Source does not prove that an operation ledger row can currently join a launch or that kill timeout recovery is durable.

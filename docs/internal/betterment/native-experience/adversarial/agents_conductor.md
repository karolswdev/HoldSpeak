# agents_conductor

Job: See agent sessions, state and work that needs an answer  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430; anchors may drift)  
Reviewer task: `review_agents_conductor`  
Evidence class: active source, representative assertions, and existing 1440/393 captures; no tests, live Desk/API/provider/native actions, or owner acceptance.

VERDICT: DO-NOT-RATIFY

## Totality

The end-to-end job is: open Agents or arrive from handed work; identify the launch/session; see ask, approval, work, completion or process loss; answer/allow once; inspect terminal/result; stop, resume or retry; then close/reopen with the same identity and receipt. It includes owner panes, completion without a PR, stale reads, restart recovery, and partial Start-an-agent setup.

The brief’s “canonical manifest host” is too narrow. `ConductorWindow` has launched flights, detected agents, and owner panes, but does not define one population or the boundary between them. The inventory’s `active_declared_partial` status is justified; this is not a sufficient implementation brief.

FINDINGS:

1. **P0 — owner-started sessions are invisible to attention and failure truth.** `ownAgents` is read separately (`web/src/desk/conductor/store.ts:178-186`) and rendered only in a bottom fold (`web/src/desk/conductor/ConductorWindow.tsx:870-875`). Header ordering/counts omit `ownMembers` (`ConductorWindow.tsx:448-499`), and the Dock derives only sessions/flights (`web/src/desk/conductor/fleetTile.ts:17-33`). A pane therefore cannot contribute through this Dock/count adapter. A cold read failure can look empty, while a failed refresh retains prior rows without a named stale/read-failed state because `ownAgentsState` is absent from `failed`/`loading` (`ConductorWindow.tsx:467-481`). Owner cost: an urgent question can be missed. This fails Tenets 2, 3 and 6. Correction: define one identity adapter (retain owner-pane authority), when this feature is enabled and exposes waiting work, include those panes in attention/counts/Dock; distinguish disabled from unavailable, and show `OWN AGENTS · NOT READ` with retry.

2. **P1 — the audit does not trace the existing completion/seen contract.** `ConductorMember` already carries `isNew` and `turnId` (`web/src/desk/conductor/members.ts:59-62`); `Done · New` becomes `Quiet` after opening (`web/src/desk/conductor/ConductorWindow.tsx:301-304`). The compact row links onward with Open (`:589-625`). These are useful seams, not proof that completion has no identity. The audit must follow Open into `agent_result`/LaneWindow, the durable seen mark, retained launch history and a no-PR result, rather than infer absent behavior from the overview row. Owner cost: duplicate result UI or an unproved return after history expires. This fails Tenets 2, 3 and 7. Correction: inventory the existing launch/turn/seen fields and prove completion → result → return after refresh; keep detail in its existing result view unless a real discovery gap is observed.

3. **P1 — Start-an-agent has a stranded partial-write path.** The form creates a note, files it, then hands it (`web/src/desk/conductor/StartAgent.tsx:91-112`). If hand fails, only a generic error remains (`:120-123`); the note id is not retained for retry or linked to a partial outcome. A retry can duplicate the note, while a malformed success with neither launch nor queue id closes the form through `onStarted(null)` (`ConductorWindow.tsx:725-734`). This fails Tenets 1, 3 and 6. Correction: retain note identity/step receipt, retry only the failed step, and stay open until a launch/queue id exists. Valid queued success already has a `queue:` identity (`web/src/desk/conductor/StartAgent.tsx:109-119`) and should not wait for a launch.

## Convergence

Converge with `agent_hand` on `originRef`, `launchId`/`queueId` and focus-to-row; `agent_result` on `turnId`, result, seen/close; `terminals_processes` on `launchId + sessionKey`, input and stop/restart; `windows` on selection/focus; and `today_followthrough` on New attention. First consumers: ConductorWindow, Dock/fleetTile, LaneWindow, HandSheet/StartAgent and Today/Needs. Share identity, outcome and receipts, but keep owner-pane authority and terminal controls distinct; one runtime would violate Tenet 1.

## User experience

The captures (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/conductor-1440.png` and `conductor-393.png`) show a clean known-state path: one `Start an agent`, one `Open`, readable at both widths. That likely pleases for a launched PR. They do not show an ask, result, owner pane, partial handoff or recovery, so trust, focus return, accessibility, performance and delight remain unknown. Put urgent rows first, expose results in-face, and keep one receipt.

CONDITIONS: Add the three identity/result/partial-write contracts, explicit read-failure states, first consumers, retained boundaries and close/reopen return. Preserve Button, state-pill, egress and stale-answer guards; this is an audit correction, not a new owner gate.

MISSED:

1. High: owner-started asks, restart loss, and `/api/coders/own-agents` failure.
2. High: done without PR, result details, and seen after reload.
3. Medium: no projects or project-read failure in Start-an-agent.
4. Medium: terminal → stop/restart → return without changing selection.

TUESDAY: Not yet; the known launched-PR path is compact, but the owner can miss his own pane and still needs the existing completion return proved and a failed start retried without duplicate notes.

## Acceptance challenges

1. With an owner-started pane asking and a launched agent working, assert the pane appears in Needs/Dock attention, answers through its route, and keeps one receipt after refresh.
2. Finish a launch without a PR; assert `Done · New` has result facts, Open lands there, reopening marks only that turn seen, and reload keeps `Quiet`.
3. Let note creation/file succeed but hand fail; assert the same note retries hand, no duplicate is made, and success selects the returned launch/queue row.
4. Open a working launch’s terminal, stop, simulate restart and return; assert the same `launchId`/`sessionKey`, named outcome and no redirected kill.
5. Change the wait while Answer is visible; assert named refusal, no delivery, and retry after fresh read.

UNKNOWN: No tests were executed. No live Desk, backend/API, provider, native, performance, accessibility, 1440/393 execution, or owner acceptance was observed; captures are static desk-sweep evidence, not an owner walk.

# Desktop behavior audit across use cases

**Audit date:** 2026-10-23. **Baseline:** `8a41884a4` (product `787`; PR1429
research). Source/test inventory only: no test runs, Desk walk, owner-state
inspection, or full workflow atlas. Anchors are baseline-specific and can
drift.

## Adversarial follow-up

All 47 inventory families now have [individual adversarial reviews](adversarial/README.md).
Read their [reconciliation](adversarial/SYNTHESIS.md) before using this baseline
matrix as an implementation brief. They correct active/retained routes, public-job
associations and over-broad missing-behavior claims. The original matrix remains
a source snapshot; neither it nor the reviews establishes live task acceptance.

## Readout and scope

The Desk has a credible shell, not a complete desktop application model. The
application manifest centralizes app/window identity and projections
(`web/src/desk/applications.ts:4-10`), the compositor owns window geometry and
front state, and several task families have strong async/receipt guards. The
reusable behavior is uneven: repository windows still behave like tree-shaped
pages, selection is partly global/singular, and transfer is an in-app semantic
hand rather than clipboard or OS file-manager exchange.
Presence is broken and disabled, so it supplies no native-host evidence
(`docs/internal/betterment/native-experience/CURRENT-STATE.md:102-118`).

The [reconciled use-case inventory](USE-CASE-INVENTORY.json) is a source-
coverage index, not a second catalog: 13 public job rows, 87 capability IDs,
25 manifest rows (21 active, 4 parked), 117 cluster-qualified recipe slices,
47 family records and 34 requested domains. Canonical authority remains
`docs/USE_CASES.md`, `docs/CAPABILITIES.md`, the manifest and tracker. The 47
records map below to behavior-facing families and shared axes; this is not
every form, list, or renderer. **Good** means a reusable seam exists, not
universal adoption; **partial** means the common contract is incomplete;
**missing** means the acceptance behavior is absent; **unverified** means
source/tests exist but were not executed or observed; **disabled** is an
explicit owner operation state.

### Use-case families mapped to behavior axes

| Family (current jobs) | Behavior axes that must hold |
| --- | --- |
| Voice and dictation (dictate, correct/replay, wake, delivery) | F, E, A, K, O: focused target, IME/caret insertion, one mic owner, captured request, consent and receipt. |
| Meetings and live media (capture/import, review intelligence, aftercare) | W, F, N, X, A, O, P: stable meeting identity, reader scroll, retry/cancel/recovery, provenance and egress. |
| Projects and People (Ask about work, 1:1 preparation, follow-through) | S, N, C, E, A, O: collection/detail selection, scoped commands, stale-read fencing, saved edits and external-action authority. |
| Ask, Threads and Memory (ask, keep answer, specialist conversation) | W, F, C, E, A, O: request snapshot, draft preservation, source selection, stream abort and local/cloud truth. |
| Agents, Coder and Gate (reply, tool approval, review) | W, F, C, A, O, K: pane/session identity, front-window routing, held calls, interruption, answer authority and receipt. |
| Automations and workflows | W, N, A, O, P: run identity, progress, stop/restart, retained result and failure state. |
| Engines and destinations | C, N, O, K, P: scoped selection, readiness, destination/egress, permission, retry and persisted setup. |
| Send and connectors (Slack/GitHub/Jira/calendar) | C, E, A, O, P: exact source/target, draft retention, permission, unknown outcome and receipt. |
| Desk shell and resource browser | W, F, S, N, C, V, T, X: independent windows, navigation/history, selection/range, view modes, transfer and recovery. |
| Settings, Setup and Doctor | W, F, E, A, O, P: dirty state, revisions, focus return, offline/read failure, retry and truthful readiness. |
| Companion clients and device bridges | W, F, N, O, K: paired identity, reconnect, capture ownership, authority boundaries and no silent machine access. |

Axis key: W app/window/document identity and lifecycle; F focus/activation;
S selection/anchor/range; N navigation/history/restore; C command context;
E editing/IME/voice/undo; V collection views; T transfer/clipboard/drop;
X panes/scroll; A async snapshot/dirty/retry/cancel; O operations/permission/
receipts; K keyboard/accessibility; P native adapters/performance/feedback.

The inventory uses more granular codes. Crosswalk: W = APP_ID/WIN_LIFE;
F = FOCUS; S = SELECTION; N = NAV_HISTORY/PERSISTENCE; C = COMMANDS;
E = EDIT_IME; V = VIEW_MODES/RESOURCE_ADAPTER; T = TRANSFER; X = SCROLL/SURFACE;
A = ASYNC_STALE; O = OP_OUTCOME/EGRESS/SOURCE; K = COVERAGE for keyboard/AT
proof; P = NATIVE_BOUNDARY/FEEDBACK/COVERAGE for native/performance proof.
The codes support traceability; they are not another runtime registry.

## Shared behavior matrix

P0/P1 below prioritize framework investment and dependencies; they are not
new release/merge gates or a claim that every existing job is broken.


| Axis | Native user expectation | Current implementation (source anchors) | Coverage exists (existence, not execution) | Gap, affected families, priority |
| --- | --- | --- | --- | --- |
| W Identity/lifecycle | App identity, separate window instances, durable document/resource identity; close/minimize/reopen must not lose dirty work or background work. | Manifest projects app identity; surface hosts use `applicationKey` and window id (`applications.ts:4-10`; `SurfaceWindows.tsx:55-70,169-181`). Workspace persists windows, geometry, min/max, drafts, places and recent opens (`workspaceStorage.ts:20-59,343-390`). | `web/src/desk/store/__tests__/windowSingleInstance.test.ts`; `web/src/desk/__tests__/windows.test.tsx`; `windowUndo.test.ts`. | **Partial:** repository/document identity is not a shared contract; `RepoWindow` has local path/selection only (`RepoWindow.tsx:51-67`). Affects all families, highest reuse risk. **P0**. |
| F Focus/activation | Raise the clicked window, focus its control, preserve focus on async completion, return focus to opener; incoming events must not steal input. | Frame focuses on open and restores opener (`DeskWindow.tsx:1104-1121`); pointer press raises (`:1225-1229`); front authority is compositor-derived (`windowRegistry.ts:132-149`). Settings captures the originating control before await and returns to it (`SettingsCore.tsx:1552-1588`). | `web/src/desk/chair/__tests__/chairWindows.philo1311.test.tsx`; `web/src/desk/compositor/__tests__/CompositorLayer.test.tsx`; `web/src/components/signal/Signal.test.tsx`. | **Good shell / partial apps:** no shared focus contract for collection/detail or editor panes. Meetings, People, Ask, Settings most exposed. **P1**. |
| S Selection/anchor/range | Click selects; primary modifier toggles; Shift extends from anchor; focus and selected identities survive sort, refresh, view change and window switching. | Screen owns global `selectedIds`, then prunes it to visible objects on refresh (`screen/Screen.tsx:104-117`); icon press replaces selection (`:237-251`). ObjectList accepts a set but only `onSelect(id)` (`ObjectList.tsx:80-94,163-185`). Key context publishes one ref only (`keymap.ts:112-115`). | `screen/__tests__/Screen.test.tsx`; `surface/__tests__/objects.test.tsx`; `surface/__tests__/roving.test.tsx`. | **Partial/missing:** no shared anchor, range or modifier intent; refresh can affect unrelated selection. The common multi-item command path is incomplete across resource, People, Projects, Ask and Send; individual feature controllers may already support plural context. **P0**. |
| N Navigation/history/restore | Each window has location, Back/Forward, breadcrumb state, restore validation and stale-location handling; folder expansion is not navigation. | Repo window changes local `path`, clears selection and refreshes; breadcrumbs only ascend (`RepoWindow.tsx:112-130,193-225`). Provider exposes tree/read/write but no UI open/history (`repository.ts:43-60`). Workspace persists generic `places`, not repository history (`workspaceStorage.ts:50-59`). | `tests/unit/test_repository_routes.py`; `tests/unit/test_repository_walk_fixture.py`; old repository glass cases are parked (`tests/e2e/_parked/test_philo15_16_project_repo_glass.py`). | **Missing/unverified UI:** no Back/Forward, file-open view, stale response fence or per-window scroll restore. Explorer/resource, document, project and meeting deep-link jobs. **P0**. |
| C Commands/context/multi-items | Menus, shortcuts, context menus and voice proposals resolve the same active target set; selected ranges remain the command target. | One registry defines verbs/ghost reasons (`verbRegistry.ts:1-12,58-105`); keyboard dispatch is centralized (`keymap.ts:133-145`). But `VerbContext.selectedRef` is singular and `selected()` resolves one object (`verbRegistry.ts:58-63,119-132`). | `web/src/desk/__tests__/keymap.test.ts`; `verbRegistry.test.ts`; `objectMenu.test.ts`. | **Partial:** shell consistency is good, target cardinality is not. Stage, archive, send, Ask, file and agent-hand actions cannot share a multi-item context. **P0**. |
| E Typed editing/IME/voice/undo | Native text editing keeps caret/range, composition and undo; voice inserts at current target; AI changes are proposals with explicit apply/reject. | CodeMirror has history, selection-aware insertion and IME-safe editor keymap (`DeskEditor.tsx:209-235,244-305`). Note AI proposal applies a captured range with undo wording (`NoteEditor.tsx:50-107`). Generic note voice appends to body, not caret (`NoteEditor.tsx:171-183`). String/Pad gadgets expose mic and latest-writer protection (`gadgets.tsx:262-347,363-467`). | `web/src/desk/components/DeskEditor.test.tsx`; `web/src/lib/__tests__/micSession.test.ts`; `pullouts/editors/ThoughtNoteEditor.test.tsx`; `tests/integration/test_voice_custody.py`. | **Partial:** editor path is strong; generic dictation and repository file editing do not share it. Dictation, Notes, Settings, Ask and document family. **P1**. |
| V Collections/tree/table/columns/typeahead | Correct tree/grid/treegrid semantics; stable row identity; sort/columns/typeahead; focus and selection do not depend on DOM order. | ObjectList is a grid with sort buttons and roving rows (`ObjectList.tsx:127-185`); DeskSortableTable is a sortable table with row focus/context hooks (`DeskSortableTable.tsx:73-101,225-250`). Repo has flat current-folder table and sort (`RepoWindow.tsx:89-107,226-236`). | `surface/__tests__/objects.test.tsx`; `surface/__tests__/roving.test.tsx`; `surface/__tests__/wings.test.tsx`; `web/src/desk/components/DeskSortableTable.tsx` has no dedicated test file. | **Partial:** no tree/treegrid contract, typeahead, column persistence, or open-vs-expand distinction. Resource, People, Meetings, Projects and Engines. **P1**. |
| T Clipboard/cross-window DND | Copy/paste has explicit payload and scope; internal move/copy/link differs from OS file transfer; drop refusal is visible and keyboard-equivalent. | Hand MIME is an in-app semantic reference and only agent targets accept it (`hand/drag.ts:12-14,48-72`). Browser file drops are a separate permissioned capability; OS file-manager integration is outside ReactDOM (`BROWSER-PLATFORM.md:13-18,32`). | `web/src/desk/hand/__tests__/hand.test.tsx`; `tests/unit/test_agent_hand.py`; parked global file-drop tests are not active. | **Partial/disabled boundary:** no clipboard adapter, resource transfer between explorer windows, or Finder/native transfer. Ask attachment is not file move. Agents, Ask, resource browser, Send. **P0**. |
| X Panes/resize/scroll | Resizable windows and panes preserve minimums; one declared scroller retains position, selection and reading anchor across reflow. | Shared window dividers use pointer capture, keyboard resize and minimum clamping (`CompositorLayer.tsx:16-64`; `sharedResize.ts:98-127`). Surface split/reading/scroll hints exist (`Surface.tsx:329-360`; `ReadingDocument.tsx:42-43`). | `compositor/__tests__/sharedResize.test.ts`; `compositor/__tests__/arrange.test.ts`; `surface/__tests__/ReadingDocument.test.tsx`; `surface/__tests__/scrollHint.test.ts`. | **Partial:** frame geometry is reusable; per-app pane widths and scroll restoration are inconsistent. Ask, Meetings, People, terminal and large collections. **P1**. |
| A Async snapshot/dirty/retry/cancel | A request uses its captured input; newer edits remain; stale responses are dropped; cancel is real; retry repeats the right operation; dirty state survives interruption. | Ask snapshots prompt/context and fences request id/AbortController (`AskPanel.tsx:210-264,457-533`). Settings queues changed paths with revisions, keeps pending/failed edits and retries (`SettingsCore.tsx:1487-1520,1552-1672`). Meeting reads fence record and revision (`useMeetingData.tsx:215-313`). Repo refresh has no request identity fence (`RepoWindow.tsx:69-87`). | `web/src/desk/__tests__/ask.app.test.tsx`, `askPanelExperience.test.tsx`, `ask.test.ts`; `web/src/pages/cores/__tests__/settingsWriters.test.ts`, `settingsLeave.philo17.test.tsx`; `history/__tests__/meetingWindowR1.philo17.test.tsx`; `tests/integration/test_meeting_intel_recovery.py`, `test_meeting_kill_recovery.py`. | **Partial/unverified:** strong in Ask/Settings/Meetings, missing in Explorer and not common. All families inherit the risk; resource/document first. **P0**. |
| O Operations/permission/egress/receipts | Every effect names actor, target, destination, authority, outcome and unknown state; refusal says why; no UI claims success before durable result. | Policy descriptors and hard invariants include destination/payload/pane binding and audit receipt (`holdspeak/operation_policy.py:15-30,40-83`). Write failures use one named receipt with exact retry (`useWriteReceipt.ts:1-9,25-41,137-185`). | `tests/unit/test_operation_policy.py`; `test_authority_grants.py`; `test_delivery_receipts_db.py`; `web/src/desk/components/__tests__/writeReceipts.test.tsx`; `tests/integration/test_coder_gate_yolo_real_hub.py`. | **Good kernel / partial face:** resource operations have no shared authority adapter; transfer/refusal/indeterminate states are not proven in an explorer. Send, Gate, Coder, Meetings, Settings, repository. **P1**. |
| K Keyboard/accessibility | Shortcuts respect text fields and IME; composite widgets expose focus/selection semantics; pointer, keyboard, touch and AT paths agree. | Keymap ignores repeat, default-prevented and composing events and guards typing (`keymap.ts:133-145`). Wings use tablist/roving focus or measured strip menu (`wings.tsx:74-109`). | `web/src/desk/__tests__/keymap.test.ts`; `surface/__tests__/roving.test.tsx`; `surface/__tests__/wings.test.tsx`; `tests/e2e/test_desk_sweep.py`; `tests/e2e/test_components_glass.py`. | **Partial/unverified:** no manual VoiceOver/NVDA, no live WebKit application task, and no range/treegrid AT contract. Every family, especially explorer/editor. **P0**. |
| P Native adapters/performance/feedback | Native host owns OS-only affordances; progressive browser features degrade honestly; timing and feedback are measured locally, not inferred from geometry. | Browser note explicitly limits ReactDOM and points OS windows/file transfer to Python/AppKit (`BROWSER-PLATFORM.md:8-19`). Presence adapter exists but is broken and owner-disabled (`CURRENT-STATE.md:102-118`). Feedback captures semantic context plus screenshot/audio with abort (`UiFeedbackHost.tsx:70-109,152-180`). No compositor frame/long-task telemetry (`CURRENT-STATE.md:120-133`). | `tests/unit/test_desktop_presence.py`; `test_desktop_presence_cocoa.py`; `web/src/desk/components/__tests__/windowFeedbackButton.test.tsx`; capability probes cover API exposure only (`BROWSER-PLATFORM.md:53-69`). | **Disabled/unverified:** no WebKit app task, native Finder/OS window proof, or performance baseline. All families; prioritize shared frame and explorer before adapter work. **P1**, with Presence **disabled**. |

## Tuesday journeys and falsifiable acceptance

These are five proposed acceptance journeys rooted in the existing registered
repository/resource browser and real available operations. Missing selection,
history and document behaviors are implementation targets, not claims that
the journeys already run today. They are not a full OS file manager and
do not authorize unsupported create/move/delete UI.

1. **Compare two resources.** Open two repository windows at different
   locations; navigate one, switch focus, select a range in each, sort one,
   return to the first, and confirm its view state and command target are
   unchanged. Failure cases: stale folder response and
   missing location. Acceptance: two stable window ids; no cross-window
   selection mutation; Back/Forward restores exact locations; stale response
   cannot replace the newer view.
2. **Inspect and edit.** From a selected resource, Enter/double-click opens
   `fetchFile` content; type, compose with IME, speak into the caret,
   undo, leave dirty, close/reopen, and retry a refused write. Acceptance:
   editor identity is separate from title/path; draft and selection survive a
   failed write; only an authoritative write clears dirty state; refusal names
   the reason and offers retry.
3. **Ask across windows.** Select a bounded resource set, invoke the same
   command by context menu, keyboard and voice proposal, attach a reference in
   Ask, start a request, edit a newer follow-up, then cancel or switch windows.
   Acceptance: the request uses the captured set, later edits remain, cancel
   stops its invocation only, and the destination/egress is visible. A private
   Ask reference must not claim OS file movement.
4. **Interrupted meeting follow-through.** Open a saved meeting while
   intelligence is queued/running; change focus, stop or lose the read, retry,
   inspect source provenance, and confirm an aftercare action only after
   authority. Acceptance: the meeting id and current revision fence responses;
   prior result remains visible during failed reread; action has a receipt and
   unknown outcome is not shown as sent.
5. **Agent/connector handoff.** Hand a selected work item to an agent or
   prepare a connector send; refuse permission, interrupt the operation, then
   retry the exact target. Acceptance: source/target identity and authority
   are stable, refusal is named, newer text is not overwritten, and one
   terminal receipt exists. No OS-wide drag or native Presence is required.

### Proof tiers and delivery order

* **Source/test tier:** line-anchored inspection and focused unit/component
  tests establish a seam or invariant, not a usable app.
* **Automated task tier:** isolated glass tests at 1440 and 393, including
  keyboard and failure states, establish repeatable browser behavior. The
  existing quick 110-case desk sweep is geometry/interaction fencing, not
  native-UX acceptance (`CURRENT-STATE.md:120-133`).
* **Manual owner tier:** a live Desk shot and task completion, plus IME,
  VoiceOver/NVDA, and native-host observations, establish Tuesday usability.
  The PR1429 research packet ran three-engine API probes but no WebKit
  application task or performance benchmark (`BROWSER-PLATFORM.md:53-69,124-151`).

Prioritize the reusable P0 gaps: per-window selection/range and command
context; repository navigation/history/document identity; cross-window
supported transfer; and common async fencing. Prove the first useful journey incrementally, then extend the others as their
consumers land. Typeahead and clipboard belong with the consumers that need
them; virtualization and native integration need measured or functional need.
Do not turn completion of all five journeys into another merge gate.
This is a risk/reuse-prioritized coverage walk,
not a cartesian plan that blocks delivery. Unknowns stay visible until proof
closes them.

**Tuesday:** the new explorer-style acceptance workload is not ready. Existing
apps have useful individual jobs, but comparing resources, preserving a shared
multi-item command target and recovering a cross-window edit are not yet
proved through a coherent application contract.

# windows

job: Open, focus, arrange, minimize, restore and close windows  
baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd`  
reviewer task: `review_windows`  
evidence class: source/assertions and captures; no tests, live walk, owner observation, provider/native, or owner-state action.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts at Go, menu, Dock, object, deep link, or restore. It resolves
an action to an application, window instance, and scope;
brings the frame forward; arranges it; minimizes/restores without losing the
place; keeps an operation or draft honest; then closes or returns to the
opener and reopens the same work after reload. The manifest projects
the doors and aliases
(`web/src/desk/applications.ts:570-669`), while the store creates or raises a
surface instance (`web/src/desk/store/compositorSlice.ts:417-465`).

Inventory names shell verbs plus one lifecycle gap, but not trigger, scope,
close refusal, recovery, stale identity, or return
(`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:3121-3159`).
Keep this a window-framework audit, not explorer navigation or domain
operations.

FINDINGS:

1. **High — identity and return are not an implementation contract.** The
   evidence map omits application action, stable `windowId`, and resource
   scope, although aliases compose scopes and the parser validates records
   (`web/src/desk/applications.ts:647-669`;
   `web/src/desk/store/workspaceStorage.ts:160-175,207-255`). Reload only
   proves a Meetings record returns, not deep link, alias, minimize, missing
   surface, or opener convergence
   (`web/src/desk/__tests__/surface-windows.test.tsx:62-87`). Owner cost: a
   Tuesday return can raise wrong work or duplicate (Tenets 3, 5, 6, 7).
   Correction: add an identity/transition table using ids such as
   `surface-meetings`, `surface-settings`, and scoped object pullouts; preserve
   the existing compositor and single-instance rule.

2. **High — mounted view, retained operation, and dirty document are
   conflated.** Hosted surfaces opt into `unmountOnMinimize`
   (`web/src/desk/components/SurfaceWindows.tsx:222-240`), while the frame
   can hide or unmount content and independently awaits `beforeClose`
   (`web/src/desk/components/DeskWindow.tsx:798-799,1045-1053,1134-1135`).
   Meanwhile the process watcher retains operation ids, events, and objects
   outside the window (`web/src/desk/processWindow.ts:13-24,121-190`). Owner
   cost: an implementation may lose a result or draft on minimize, or invent
   a universal operation manager (Tenets 1, 3, 6). Correction: define shell
   lifecycle separately from domain retention; each app names its
   operation/draft identity, receipt, and close guard. Do not change the
   compositor into that authority.

3. **Medium — recovery and fast-path pleasure are absent.** Recovery-only
   mounting can clear/hold windows, then admits Setup doors
   (`web/src/desk/components/SurfaceWindows.tsx:92-152`;
   `web/src/desk/__tests__/surface-windows.test.tsx:174-202`). Touch long-press,
   opener focus return, and restored minimization are separate frame behaviors
   (`web/src/desk/components/DeskWindow.tsx:951-976,1104-1132`), not covered by
   the brief. Cost: the owner may get stranded in setup or lose the quickest
   return path (Tenets 3, 6, 7). Correction: make recovery, pointer/keyboard,
   and 1440/393 fast-path scenarios explicit.

## Convergence

Converge with `desktop_workspace` on arrival/recovery and the workspace
document; `navigation_commands` on manifest doors, aliases, and the shared
verb registry; and `objects_pullouts` on semantic refs, origin return, and
single-instance focus (`web/src/desk/store/__tests__/windowSingleInstance.test.ts:35-82`).
Converge with `agent_result` and `automation_schedule` only on retained
operation ids, receipts, and outcomes. `explorer_repo` is a first consumer of
window/view persistence, not a reason to make every window an explorer. Keep
selection, navigation, dirty editing, and provider authority in their
families. A universal manager imposes explorer ceremony on Settings, Ask, and
simple object views (Tenets 1 and 3).

## User experience

The optional 1440 capture shows a Workbench field and Dock; the 393
capture shows a compact Go list and persistent Dock
(`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/desk-1440.png`,
`desk-393.png`). This supports a familiar fast path, but neither capture
shows an open window, return animation, dirty state, or recovery. Source
inference is promising: one compositor, front authority, dock seats, and no
modal trap. Craft remains unknown until transitions are seen live.

CONDITIONS: Add the app/window/scope identity table, the retained-domain
boundary, and the recovery/return scenarios below. Keep the existing
compositor, registry, manifest, and single-instance decisions.

MISSED:

1. Deep-link or alias open, minimize, reload, and return to the same scoped
   work (highest cost).
2. First-use recovery clearing/holding existing windows, then returning to
   the normal Desk.
3. Close during a dirty edit or retained operation, including refusal and
   retry.
4. Touch long-press and keyboard focus return at 393.

TUESDAY: The shell has a credible Workbench fast path, but the audit cannot
yet promise that the owner returns to the same work without loss or surprise.

## Acceptance challenges

1. From Go and a deep link, open `surface-meetings` with `meeting:m1`; opening
   it again focuses one instance, and reload preserves its scope and seat.
2. Minimize an active app, let its domain operation finish, restore it, and
   find the same operation receipt without requiring the view to stay mounted.
3. Edit a dirty document, attempt Close, refuse the guard, then retry; the
   draft remains and focus returns only after an accepted close.
4. Enter first-use recovery with a saved Desk, use the admitted Setup door,
   leave recovery, and verify unrelated windows return without duplication.
5. At 393, use long-press and keyboard/Dock restore; the named window regains
   focus and the owner can return to the prior task.

UNKNOWN: No tests or builds were run, no live pointer/keyboard/touch walk or
owner acceptance occurred, and no provider/native, accessibility, performance,
or operation-retention claim was proved. Captures are prior visual context;
omission is not an observed product bug.

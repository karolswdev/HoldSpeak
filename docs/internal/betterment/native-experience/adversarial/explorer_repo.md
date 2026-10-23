# explorer_repo — adversarial review

Job: Browse a registered repository in multiple windows and open a supported file.  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (source anchors may drift).  
Reviewer task: `review_explorer_repo`.  
Evidence class: repository source and representative test assertions only; no execution, Desk walk, provider call, or owner observation.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts at a repository object and mounts `RepoWindow` (`web/src/desk/DeskApp.tsx:279-282`). The drawer opener also calls `openRepositoryWindow` (`web/src/desk/drawer/open.ts:18-37`), but that project drawer is retained for restoration, not the current project door (`web/src/desk/drawer/DrawerWindows.tsx:10-13`), loads a root, browses folders, opens a file, and returns to work after switching, minimizing, or restarting. It must distinguish loading/empty, unreadable files, stale responses, and failure. The face also exposes checkout, stage, and commit, so those are in scope unless parked (`web/src/desk/components/RepoWindow.tsx:196-223,248-267`).

The inventory names history, selection, transfer, identity, stale reads, and file opening, but does not close their loops. “Multiple windows” is undefined: two repository objects or two locations of one repository? The factory deduplicates by key (`web/src/desk/store/windowFactory.ts:41-53`).

FINDINGS:

P0/P1 rank audit-brief completeness, not observed production incidents.

1. **P0 — the audit under-specifies the mutation boundary.** `selectedFile` is set but never opened (`web/src/desk/components/RepoWindow.tsx:53-55,226-236`), although `fetchFile`/`writeFile` exist (`web/src/desk/repository.ts:49-60`); the face offers branch, stage, and commit (`RepoWindow.tsx:131-149,196-223`), backed by write routes (`holdspeak/web/routes/repositories.py:267-335`). Owner cost: a dead “open” or unexamined commit path. This fails Tenets 3 and 6. Correction: split browsing from editing, or specify each operation’s authority, receipt, refusal, dirty-state, and recovery.

2. **P0 — multi-window and restoration are not an implementable contract.** `RepoWindow` is keyed as `repository:${repositoryId}` (`web/src/desk/components/RepoWindow.tsx:176-187`); persistence stores ids, not path/history/selection (`web/src/desk/store/workspaceStorage.ts:370-382`). The assertion proves only ids return after reload (`web/src/desk/__tests__/deskRemembers.philo1307.test.tsx:63-77`). Owner cost: independent locations cannot be falsified and reopening can lose the work place. This fails Tenets 3 and 5. Correction: define same-repository instance identity (or constrain to distinct ids), then persist and validate location, history, selection, view, and missing-location recovery.

3. **P0 — interaction and async acceptance are named, not closed.** `refresh` has no request identity/cancellation and applies whichever `Promise.all` finishes (`RepoWindow.tsx:69-87,118-130`); `DeskSortableTable` exposes one `selectedKey` and row click (`web/src/desk/components/DeskSortableTable.tsx:15-31,225-247`). Repository tests cover backend behavior only (`tests/unit/test_repository_routes.py:47-86`); no RepoWindow test exists. Owner cost: fast navigation can show the wrong folder, and Shift/range selection cannot be verified. This fails Tenets 5 and 6. Correction: add scoped selection, a stale fence, loading/empty states, and UI assertions for pointer, keyboard, sort, and recovery.

4. **P1 — the narrow face is not addressed.** The frame sets `minW={600}` (`RepoWindow.tsx:176-184`) and the table merely scrolls (`RepoWindow.css:5-10`). Cost: phone work is likely clipped (Tenets 5 and 6). Add a container-aware narrow composition and prove it at 393; no relevant repository capture was available.

## Convergence

Converge `objects_pullouts` and `source_context`: reuse semantic opening, context, and the command registry (`objectMenu.ts:132-153`; `verbRegistry.ts:58-105`), while keeping repository authority in its adapter. Converge collection state with `drawers`, `knowledge_drawers`, `meeting_archive`, and `memory`: stable ids, sort/focus/selection, scroll, restoration; keep domain adapters/provenance separate. Converge `agent_hand` only for explicit source/target refs and refusal (`web/src/desk/hand/drag.ts:12-14,48-73`); repository copy/move and OS drop remain distinct. For editing, target `native_input`/`notes_editor`, not a new runtime.

## User experience

Source judgment: the Desk frame, library Buttons, branch/dirty indicators, sortable table, and footer provide a credible shell (`RepoWindow.tsx:175-271`). Tuesday is not yet pleasing: no file opens, no Back/Forward, no range selection, generic errors, and a likely clipped 393 face leave the architect hunting. This is inference, not visual acceptance; no repository shot exists in the optional sweep set.

CONDITIONS: specify operation boundary, instance/persistence, stale/selection proof, convergence, and 1440/393 expectations before implementation.

MISSED:

1. Existing branch/stage/commit and file-read/write semantics (highest owner cost).
2. Same-repository window identity and restored path/selection.
3. Loading, stale, non-text/read-only, and interrupted-operation outcomes.
4. Narrow layout and the absence of a document-opening surface.

TUESDAY: Not yet—the owner can reach a repository, but cannot reliably open a file, keep two locations, or recover from fast navigation on this screen.

## Acceptance challenges

These are proposed checks for missing behavior, not claims of current support.

1. From a repository drawer member, open two supported repository windows (or two explicitly supported instances), navigate one to `src` and leave the other at root; switching focus preserves each path, selection, and scroll.
2. From a file row, Enter/double-click reads the file through the supported adapter; a missing or non-text file produces a named outcome and returns to the same folder without losing selection.
3. Delay a root response, navigate to `src`, then `docs`; the final `docs` response wins, and a stale/error response cannot replace it.
4. Select a non-contiguous/range set, sort it, and invoke only a declared command; its targets remain the same resource identities, with refusal or success visible at the operation location.
5. Minimize, reload, and reopen; a valid location returns, while a removed location becomes an honest recoverable state and unrelated Desk windows remain intact.

UNKNOWN: No tests/builds, owner walk, visual acceptance, provider/native action, performance/accessibility proof, or same-repository multi-instance behavior was observed. Route tests assert backend behavior, not the RepoWindow workflow.

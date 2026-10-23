# drawers — adversarial review

Workflow id: drawers  
Job: Create, browse and use a named collection drawer  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_drawers`  
Evidence class: source and existing assertions only; no execution, capture or owner observation.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The real job has four collection families, not one filesystem drawer. A Directory is created by New Drawer, named, filled or unfilled, then opened from the root projection; its pullout shows child directories and member refs (`web/src/desk/verbRegistry.ts:303-314`, `web/src/desk/store/dataSlice.ts:856-893`, `web/src/desk/pullouts/DirectoryPullout.tsx:22-87`). A KB is a separately loaded hub collection (`web/src/desk/api.ts:813-828`, `web/src/desk/pullouts/KbPullout.tsx:25-105`). A Project’s active entry is Project Room; the old drawer is retained for restoration. A Repository is a local DeliveryRegistry-backed Git window (`web/src/desk/shell.ts:123-132`, `holdspeak/web/routes/repositories.py:1-6`). “Use” means open a supported member or perform a provider-supported action, then return with identity and outcome intact. Recovery must cover unavailable members, failed reads, refused writes and stale refresh.

FINDINGS:

1. **High — the audit names a parked host as active.** `web/src/desk/screen/open.ts:22-27` and `web/src/desk/openObject.ts:172-176` route Project refs to Room; `web/src/desk/drawer/DrawerWindows.tsx:10-13` says the Drawer key is parked, and `web/src/desk/store/compositorSlice.ts:359-360` says no live door opens a zone window. The assertion confirms this split (`web/src/desk/drawer/__tests__/drawer.test.tsx:336-346`). This would cost the owner a dead Tuesday path (Tenets 3 and 6). Correction: split active DirectoryPullout, KbPullout, Project Room, parked DrawerWindow and RepoWindow; retain `drawers` only for traceability and name each first consumer.

2. **High — provider boundaries and the create/use loop are under-specified.** KB and Directory membership are kernel-admitted hub operations (`holdspeak/web/routes/primitives/kbs.py:117-151`, `holdspeak/web/routes/primitives/directories.py:131-172`); Project resources are a project service (`holdspeak/web/routes/projects.py:333-390`); Repository reads and Git verbs use a server-side path (`holdspeak/web/routes/repositories.py:196-265`). The shared `RESOURCE_ADAPTER` label risks a filesystem abstraction and omits New Drawer, file/unfile, and provider refusal/receipt behavior, costing the owner clear recovery (Tenets 1, 3 and 5). Correction: add a provider matrix for create, browse, use, refresh, refusal and return. Share identity and controls only; keep provider authority separate.

3. **Medium — selection, navigation and return are not one demonstrated contract.** `DrawerWindow` owns one local `selectedId` (`web/src/desk/drawer/DrawerWindow.tsx:143-149`); KB and Directory rows only open refs (`web/src/desk/pullouts/KbPullout.tsx:53-65`, `web/src/desk/pullouts/DirectoryPullout.tsx:46-62`); Repository selection is path-local and cleared on navigation (`web/src/desk/components/RepoWindow.tsx:54-63,118-129`). Existing tests prove opens and honest unavailable/empty states, not cross-host return, costing the owner re-finding work (Tenets 3, 6 and 7) (`web/src/desk/pullouts/DirectoryPullout.test.tsx:35-86`, `web/src/desk/pullouts/KbPullout.test.tsx:45-88`). Correction: specify scoped selection/focus, then challenge refresh, close/reopen, child navigation and stale identity. Do not impose range selection without a multi-item job.

## Convergence

Converge with `knowledge_drawers` on qualified refs, filing and `SurfaceSection`/`SurfaceRows`/`DeskFilingStrip`; first consumers are KbPullout and DirectoryPullout. Converge with `projects_room` on project identity, source status, retry and return. Converge with `explorer_repo` only on window/view identity and command context, never Git authority. `objects_pullouts`, `windows`, and `navigation_commands` supply open/raise/restore. Keep provider adapters separate: one explorer template would erase semantic objects, receipts and local-Git boundaries.

## User experience

Source evidence suggests good craft in honest unresolved rows, canonical opens and named Project retry (`web/src/desk/pullouts/DirectoryPullout.test.tsx:62-86`, `web/src/desk/pullouts/KbPullout.test.tsx:63-88`, `web/src/desk/drawer/useDrawerData.ts:95-110`). The audit must test the coherence of the taxonomy: Go’s “Drawers” opens Directory refs, a Project opens Room, and a Repository opens a Git window. Different destinations are not themselves a UX defect; they can be appropriate to the material. No capture was inspected; source cannot prove beauty, touch reach, performance or owner delight.

CONDITIONS: Correct the active-host trace; add the provider matrix and end-to-end create/browse/use/recovery/return scenarios; define scoped selection and stale-refresh behavior. No new owner gate.

MISSED:

1. Project Room versus parked DrawerWindow routing (highest cost).
2. New Drawer plus file/unfile and provider refusal receipts.
3. Cross-window return, stale membership and selection retention.

TUESDAY: Not yet: the owner can open each kind of collection, but cannot yet rely on one coherent named-drawer job to create, file, use, recover and return.

## Acceptance challenges

1. From New Drawer, create and rename a Directory, file a note, refresh, open it from Go, open the note, close it, and verify identity and membership remain.
2. Open a Directory containing a child and unavailable ref: child and available note open by qualified ref; the unavailable row stays distinct from empty; refresh and reopen the source.
3. Open a KB with available and unresolved members; use the supported filing control to add/remove one; a refusal names failure and a later read does not claim success.
4. Open a Project from Desk/Go and a return path: both land in scoped Room; a failed read exposes Retry; close/reopen preserves identity without reviving parked DrawerWindow.
5. Open a registered Repository, descend and return by breadcrumb, select a file, and induce read failure; Retry names it. If file opening is unsupported, withhold that verb.

UNKNOWN: No tests or builds were run; no live Desk, provider, native, viewport, performance, or owner-acceptance observation was made. The baseline anchors may drift.

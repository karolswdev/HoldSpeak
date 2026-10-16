# Drawers and live wallpapers — delegated source counsel

2026-10-15. One initial finished-source round and one finished-fix recheck
against base `bea522beb` in `wt-desk-drawers-live-20261015`.

**DRAFT — delegated source counsel for Astra's root session. This is not
Muad'Dib's check and is not the formal postmerge review.** This report is
UNCHECKED — awaiting Muad'Dib if it is later used as a formal authored
artifact. The owner explicitly reversed the old still-only interpretation;
that parked interpretation is not a condition here.

Scope: the changed Screen composition, directory contents and phone rows;
the existing Atmosphere host mounted on Screen; readiness, still fallback,
layering, motion control and the changed focused tests. Product and test code
were read only. No test, build, browser, provider, model, native operation or
owner-state access was run for this counsel.

## Final source recheck

VERDICT: RATIFY

FINDINGS:

1. **Closed P1 — cycle reachability. Tenets 2, 3 and 6.** The projection
   follows a valid explicit parent or resolved membership parent
   (`web/src/desk/screen/compose.ts:136`) and retains a deterministic root
   when that chain cycles (`web/src/desk/screen/compose.ts:156`). The selected
   parent edges are actual child/member doors in DirectoryPullout, so keeping
   one cycle root preserves access to the component. Focused tests cover
   ancestor filing, membership-only cycles, reversed input order and
   self-parent/self-member cases
   (`web/src/desk/screen/__tests__/Screen.test.tsx:436`).
2. **Closed P2 — directory menu Open. Tenet 3; UX-CANON A.11.** The shared
   verb now calls the existing qualified directory pullout path and retains
   the pointer origin (`web/src/desk/verbRegistry.ts:435`). The context menu
   offers Open (`web/src/desk/objectMenu.ts:17`). The rendered Screen test
   presses the menu-bar and context-menu actions and checks their canonical
   dispatch (`web/src/desk/screen/__tests__/Screen.test.tsx:185`); the focused
   registry test also checks the origin.
3. **Closed P2 — ambiguous bare membership. Tenets 3 and 6.** The shared
   projection helper resolves each member through the existing lookup before
   canonicalization (`web/src/desk/screen/compose.ts:123`); roots and loose
   filing use that result (`web/src/desk/screen/compose.ts:139`,
   `web/src/desk/screen/compose.ts:308`). A bare ref now hides only the same
   object the contents reader resolves. The collision test retains the
   other Directory and Decision and leaves an unresolved bare person visible
   (`web/src/desk/screen/__tests__/Screen.test.tsx:422`).

CONDITIONS: None outstanding in this bounded source counsel. Root retains
the production walks and shipping decision. No new framework, backend or
filing-writer change was needed.

MISSED: The initial owner-cost order was disappearing drawer trees,
cross-kind legacy hiding, then the dead menu Open. All three are fixed in
the single recheck round; no further concrete source defect was found.

TUESDAY: Source now provides reachable root and child drawers, actual members
and canonical opens on desktop and phone; the live owner's experience is
root's independent observation.

UNKNOWN:

- Actual scene motion, appearance, pointer ownership, scrolling, 1440/393
  geometry and the real filing/menu production walks were not observed by
  this reviewer. Root owns those checks and must report them separately.
- I read the expanded collection entries and real red/green run tails:
  `.tmp/desk-drawers-live/folders-review-expanded-list.log:13`,
  `.tmp/desk-drawers-live/folders-review-expanded-red.log` (6 failed / 46
  passed), and `.tmp/desk-drawers-live/folders-review-expanded-green.log`
  (5 files, 52 passed). I ran no suite. Root reports type-check/build checks;
  those were not independently rerun here.
- The inherited partially mounted runtime cleanup limitation remains as
  disclosed below and in BUILD-BACKGROUND.md. The new host's own observer
  cleanup and still fallback do not prove disposal of a real renderer whose
  first resize/render throws.

## Initial review — retained record

The following verdict and source anchors are the initial reviewed state,
before the one finished fix round. They are superseded by the final source
verdict above.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **P1 — filing a root drawer into its child can remove the entire drawer
   tree from both root lists. Tenets 2, 3 and 6.** Take root A and child B
   (`B.parentId = A.id`). A's existing Filed strip offers B and calls
   `fileIntoDir` (`web/src/desk/components/DeskFilingStrip.tsx:134`,
   `web/src/desk/components/DeskFilingStrip.tsx:143`); that writes `zone:A`
   into B and refreshes (`web/src/desk/store/dataSlice.ts:803`). The current
   membership service accepts that edge
   (`holdspeak/services/primitive_service.py:475`). The new projection hides
   B because its parent exists (`web/src/desk/screen/compose.ts:127`) and A
   because B names it as a member (`web/src/desk/screen/compose.ts:129`).
   `GoHome` uses the same root projection
   (`web/src/desk/screen/GoHome.tsx:34`). After the windows close neither
   drawer has a root door. This is a deterministic source trace, not an
   executed browser reproduction. A local root projection that preserves an
   entry into each component can recover this without changing storage.

2. **P2 — Object > Open is enabled for a selected restored drawer and does
   nothing. Tenet 3; UX-CANON A.11.** Screen now selects the canonical drawer
   ref (`web/src/desk/screen/Screen.tsx:197`). The menu bar builds Open from
   the registry (`web/src/desk/components/DeskMenuBar.tsx:239`);
   `needSelection` accepts the resolved directory
   (`web/src/desk/verbRegistry.ts:111`), but the Open handler returns for
   directory (`web/src/desk/verbRegistry.ts:435`). The context menu separately
   withholds Open (`web/src/desk/objectMenu.ts:17`). The added folder test
   checks context-menu presence and the icon's Enter path only
   (`web/src/desk/screen/__tests__/Screen.test.tsx:184`). Use the existing
   qualified opener consistently for the restored drawer.

3. **P2 — a bare legacy member ref can hide a different object that the
   drawer cannot reach. Tenets 3 and 6.** Let A contain bare ref `shared`,
   with both a Note and a root Directory named by id `shared`. The contents
   lookup resolves the Note first (`web/src/desk/pullouts/DirectoryPullout.tsx:32`,
   `web/src/desk/world.ts:31`, `web/src/desk/world.ts:96`). Root projection
   nevertheless hides the Directory by its bare id
   (`web/src/desk/screen/compose.ts:130`). The new loose-object suppression
   likewise hides every loose kind with that bare id
   (`web/src/desk/screen/compose.ts:271`,
   `web/src/desk/screen/compose.ts:278`). Qualified refs correctly preserve
   cross-kind identity; bare refs must resolve to the same single canonical
   object before either hiding decision. The current collision tests cover
   qualified refs, not this legacy case
   (`web/src/desk/pullouts/DirectoryPullout.test.tsx:49`,
   `web/src/desk/screen/__tests__/Screen.test.tsx:424`).

CONDITIONS:

- Preserve an accessible root for directory cycles, including a parent edge
  combined with a membership edge and membership-only cycles.
- Make the directory Open verb perform the existing qualified open from the
  shared menu paths.
- Resolve bare membership to one canonical object before root/loose hiding.
- Return the finished fixes for one source recheck. Root owns focused test
  evidence and the production walks; this report imposes no wider suite or
  new framework.

MISSED:

1. Highest owner cost: an ordinary filing choice can strand a drawer tree.
2. A legacy bare ref plus a permitted cross-kind id collision can hide an
   unrelated drawer or loose item.
3. Restoring a selectable drawer also reactivates old menu assumptions that
   said no face draws directories.

TUESDAY: The ordinary root/child/Note path is present in source; drawer
reachability and the shared Open verb need the fixes above before this
counsel can ratify that job.

UNKNOWN:

- Actual motion for all eight scenes, visual quality, pointer ownership,
  scrolling, geometry, 1440/393 shots and real producer walks belong to the
  root session. They were not independently observed in this read-only pass.
- The worker reports and root's reported focused green/type-check/build
  results were read as claims; no suite was rerun by this reviewer.
- The background host correctly retains the still on import/mount rejection,
  cancels stale lazy loads and releases its own activity observer. The
  existing runtime can still lose its cleanup if an authored first
  resize/render throws after listeners are installed
  (`web/src/desk/gl/atmosphereRuntime.ts:148`,
  `web/src/desk/gl/atmosphereRuntime.ts:164`). This is inherited and already
  disclosed in BUILD-BACKGROUND.md; no new runtime framework is requested.
- No further concrete source regression was found in the changed Atmosphere
  readiness, CSS layer, Quiet Desk or persisted Motion control paths.

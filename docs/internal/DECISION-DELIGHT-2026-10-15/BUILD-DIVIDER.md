# Shared divider — build record

**HOLD FOR SHIP.** Base `c910cd580`, worktree
`/Users/karol/dev/tools/wt-decision-delight-20261015`. Implements the shared
resize section of [DESIGN.md](DESIGN.md). Tuesday: the active unrelated
window must cover the seam, and the exposed seam must still resize its two
windows. Tenets 3/5/6; Constitution VIII.

## Change

`web/src/desk/compositor/CompositorLayer.tsx:94` now uses the highest
participant window z, without adding one. Its later DOM position puts it
above the participant at the same z; a higher unrelated window can cover
both its paint and pointer target. Removed the redundant band cap and
unused `Z` import. No event, resize geometry, constraint or mode logic changed.

New `web/src/desk/compositor/__tests__/CompositorLayer.test.tsx` renders the
real layer against the real store, window mount registry, rank derivation
and touching-boundary calculation. No modules or store actions are mocked.
The typed `PanelRect` fixtures place Today over the middle of a full shared
Settings/Decision seam. Tests cover the separator's derived geometry and
z below Today, reactivity when Settings is raised, and a real ArrowRight
store write that resizes and marks both participants saved while retaining
Today's rectangle.

## Scoped proof

All commands used the orchestrator's `locked.py`: a fresh temporary HOME,
the machine test lock, and exactly these four files with `--maxWorkers=2`:

```text
src/desk/compositor/__tests__/CompositorLayer.test.tsx
src/desk/compositor/__tests__/sharedResize.test.ts
src/desk/compositor/__tests__/layers.test.ts
src/desk/compositor/__tests__/live.test.ts
```

Collection before the product fix, exit 0, in
`.tmp/decision-delight/divider-collect.log` (18 names total):

```text
src/desk/compositor/__tests__/CompositorLayer.test.tsx > the shared divider follows its participant windows > stays below an unrelated front window covering the seam
src/desk/compositor/__tests__/CompositorLayer.test.tsx > the shared divider follows its participant windows > keeps the seam at its highest participant when that window is raised
src/desk/compositor/__tests__/CompositorLayer.test.tsx > the shared divider follows its participant windows > still saves both participant rects from the exposed seam's arrow key
```

Red before the product fix, exit 1, in
`.tmp/decision-delight/divider-red.log`: the first new test received z 44
instead of participant z 43; the raised-participant test received 45 instead
of 44. The keyboard case and existing tests passed.

```text
Test Files  1 failed | 3 passed (4)
     Tests  2 failed | 16 passed (18)
  Duration  936ms
```

Green after the fix, exit 0, in
`.tmp/decision-delight/divider-green.log`:

```text
Test Files  4 passed (4)
     Tests  18 passed (18)
  Duration  1.06s
```

## Boundaries

The component tests establish rendered z ordering and real keyboard writes.
jsdom does not prove paint or pointer ownership. Root owns the production
after probe, exposed drag/key walk, 1440/393 shots, typecheck/build and quick
check. This lane ran no browser, build, install, broad suite or owner-state
operation. Only the component, its new test and this record were edited;
nothing was staged or committed. No new debt identified in this bounded lane.

# HS-129-04 — Shell-scroller and double-scroll repairs

- **Project:** holdspeak
- **Phase:** 129
- **Status:** in-progress
- **Depends on:** HS-129-01
- **Unblocks:** HS-129-11
- **Owner:** unassigned

## The thesis (the bar)

One scroll owner per window. Audit A found the stragglers that scroll the
wrong thing: DeliveryBoard and DeskToolInspector put `overflow: auto` on the
window shell so their heads (and DeliveryBoard's foot) scroll away;
ConstitutionalContextCore nests a second `.desk-surface-body`
(ConstitutionalContextCore.tsx:101-112,190-191); DeliveryDossier declares a
second full-body scroller (`.desk-dlv-dossier-body`, delivery.css:126-129);
Activity's list clips at the window border with no inner scrollbar (audit B
P2); legacy `WorkbenchCore` is unhosted (orphan).

### What changes

1. DeliveryBoard (delivery.css:2-18) and DeskToolInspector
   (chrome-menus.css:412-427): shell stops scrolling; body becomes the one
   scroll owner; head fixed, foot (where present) pinned. The board's sticky
   table-head z-escalation (delivery.css:230-234) drops to normal once its
   scroll boundary is right.
2. ConstitutionalContextCore drops its duplicate `.desk-surface-body`; one
   scroll identity.
3. DeliveryDossier keeps its RAW/code wells as bounded inner scrollers but
   loses the second full-body `max-height: 60vh` scroller.
4. Activity's records list scrolls inside the body instead of clipping.
5. Legacy `WorkbenchCore` disposition: rehost it or delete it — decided by
   whether anything routes to it; an orphan surface may not survive the
   phase.

## Acceptance criteria

1. No window in the product scrolls its own title bar; verified for the two
   named shells plus a sweep assertion in the walk harness.
2. One primary scroll owner per repaired surface; intentional bounded wells
   (terminal panes, logs, RAW folds) are the only nested scrollers.
3. Activity shows a scrollbar and reaches its last row inside the window.
4. WorkbenchCore is either reachable through a host or removed with its
   routes/tests.

## Test plan

- Web: scroll-ownership assertions for the four repaired surfaces; existing
  delivery/activity suites green; typecheck.
- Walk: Playwright — DeliveryBoard, ToolInspector, Activity, Constitutional
  Context, DeliveryDossier scrolled top/middle/bottom; heads asserted
  stationary.

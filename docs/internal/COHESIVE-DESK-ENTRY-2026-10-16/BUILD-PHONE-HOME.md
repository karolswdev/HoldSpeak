# Phone home

Status: built; frozen, HOLD for SHIP. Root read all four canvas captures and
accepted the direction before product edits. No staging or commit by worker.

Tuesday: find an application or drawer and open the exact destination with
one consistent Workbench grammar. Tenets 3, 5, 6 and 7 govern this change.

GoHome now composes one existing `desk-menu-list` paper well with
SurfaceSection captions: Apps, optional Projects, Drawers and New. Rows use
the shared menu glyph, label, separator and ghost material and retain native
chrome Buttons. Scoped screen.css rules arrange 44 px rows and let long names
and reasons wrap. No replicated paper, bevel, ink or focus styling.

Existing phoneGo order, registry context, verb callbacks, qualified zone
references, rootDirectories and openScreenRef stay in place. No new
availability predicate, menu layer or key handler. Screen, world, desktop
mounting, registries and shared menu/Button styles are outside this lane.

Owned product/test paths:
- `web/src/desk/screen/GoHome.tsx`
- GoHome rules in `web/src/desk/screen/screen.css`
- `web/src/desk/__tests__/phoneDoors.test.tsx`
- `web/src/desk/screen/__tests__/chairScreen.test.tsx`

Proof read by worker:
- `.tmp/entry/phone-home-collect.log`: 12 named tests in the two assigned files.
- `.tmp/entry/phone-home-run.log`: 2 files, 12 tests passed, duration 1.79 s.
- Native Enter and Space each activate once per gesture and use updated
  single/multiple selection context. Ghost rows stay focusable, show their
  reason and refuse pointer/Enter/Space. Optional Projects open the exact id.
  Same-name Meetings app and drawer use separate exact existing destinations.
- Path-scoped `git diff --check`: clean.

The run emitted jsdom's unsupported canvas getContext message from existing
DeskIcon.tsx:209 in the ChairHome screen case. This was not a test failure;
no DeskIcon or canvas shim was changed in this lane.

Canvas source is `canvas-phone-home/`. Root-reviewed direction captures are
local at `.tmp/entry/canvas-phone-home-shots/phone-home-{top,drawers-new}-
{1440,393}.png`; the log and observation JSON record 15 specimen rows fitting
the width, at least 44 px tall, and actual Dock heights of 76/56 px. The
Project ghost there is a declared visual fixture, not a product predicate.
The forced 1440 specimen does not change desktop GoHome mounting.

Limits: unit tests exercise view-store, verb and shell seams, not live writers
or complete window outcomes. Actual browser geometry, all-nine pointer
ownership, native keys on the delivered bundle and real application/drawer
opening remain root's proof. Root owns bundle build, complete quick check,
actual task tour and delivery. Worker did not build or rebuild a bundle.

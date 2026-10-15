# Workbench pickers — 2026-10-14

Owner: browser-native dropdown menus break immersion throughout the app.
One shared concern, one release. Base 91275406b; isolated worktree
`/Users/karol/dev/tools/wt-workbench-pickers-20261014`.

## Tuesday job and settled design

Pick a language, provider, destination, person or schedule choice in the
same Workbench grammar without a browser menu interrupting the desk.
Tenets 3, 5 and 6: one clear operation, common components, Workbench.

Keep CycleGadget's existing value/options/onChange API and native select
ownership (form values, labels, disabled state, existing change events).
Replace its native popup with one shared library-rendered listbox: square
beveled ground frame, paper choice rows, accent active row, checked current
choice, ghosted unavailable rows. No rounded web cards, modal, prose,
new dependencies, per-face popup implementation, or form-state framework.
Draw the proposal on the real component canvas before product build.

The popup opens beside the owning control and stays within the viewport;
portal above window clipping using the existing z token. Long lists scroll,
long labels wrap. Open pointer/keyboard suppresses the native picker. Keep
focus and labelled combobox semantics on the owner; arrows/Home/End and
type-ahead move the active choice; Enter/Space commit one change; Escape
cancels without saving or closing the containing window; Tab exits without
trapping; outside pointer closes without swallowing its destination action.
Off-roster values remain named. Unavailable options cannot commit. Close
on unmount/disabled/scroll or reposition safely. Phone rows and control own
44px targets. No selection changes merely from opening/cancelling.

Extend the existing species. The native select may remain the accessible,
form-owning trigger, with native opening intercepted and the owned listbox
drawn by the library. Do not create a hidden test-only select or loosen
behaviour tests. Legacy Signal Select must use the same shared core; avoid
an import cycle by a minimal Button extraction if required. Convert the
one raw Thread elicitation enum to CycleGadget. Inventory all active source
selects and retain exact value/writer ownership.

## Lanes and boundaries

- Kit: shared picker/core, Signal/optional Button extraction, CycleGadget,
  related CSS, shared tests, contract and DESIGN_SYSTEM picker wording,
  canvas, KIT.md. No product face files.
- Adoption: read-only census then ThreadPullout/InterviewPanel as needed,
  focused tests for those faces, AUDIT.md. No shared library/CSS edits.
- Root: brief, coordination, independent production evidence at1440/393,
  bounded finished source review, combined quick, PR/status/deployment.

Anchors from base, verify before edit: gadgets.tsx150/159/180;
gadgets.css208; Signal.tsx127; ThreadPullout.tsx191;
InterviewPanel.tsx57; DESIGN_SYSTEM.md132. Other lanes may move anchors.

Workers run only scoped tests stated in their brief with isolated HOME;
no full web/pytest/nightly suite, no metal, no owner state. Provide exact
collection/run tails and shot paths; distinguish source claims from runs.
Root owns combined quick. HOLD FOR SHIP: no stage/commit/push; report and
freeze finished source. Never stash/reset/restore/clean/switch, add-A,
delete, or modify a sibling lane. Park obsolete code only if needed.
No owner visual acceptance or Muad'Dib check inferred from tests.

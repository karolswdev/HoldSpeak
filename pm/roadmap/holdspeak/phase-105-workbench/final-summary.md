# Phase 105 — Workbench — final summary

**Chartered 2026-07-25 from the owner's verdict** ("I honestly want the
Desk OS to feel like an OS. Not a gimmick… Think Workbench 2.0 but on
steroids") and the follow-up diagnosis that re-ordered the build
("Gimmick comes from some of the art, but really from the fact that
there's no real idea of directories, properties of them…"). Built in
two days, story by story, each through the AGENT_BRIEF §2 method:
mock → owner gate → build → live walk → guard → gated commit.

## What shipped

- **HS-105-01 — the icon system** (+ the drawers-on-glass rider the
  owner's own screenshot forced): 64px pixel art rendered 1:1 in one
  uniform cell (the 1.375× fractional upscale was the mush), REAL
  state images on disk for all 68 sprites, badges only from named
  live routes, a drawer for directories, deterministic clean-grid
  defaults, the list leading at phone density. PRs #369/#370.
- **HS-105-03 — zones are windows**: drawers open into real
  coexisting desk windows (Icons/List views, sortable), and THE
  WINDOW REMEMBERS (view/sort per zone, the open set, rect) across
  reloads; dive survives as Focus. PR #371.
- **HS-105-04 — Info on everything**: one contract-derived Info card
  for every kind and drawer; name edits in place through the real
  update paths; tooltypes at their honest v1 (the vocabulary pinned
  to `recipe.runs_on`, round-trip-proven on the wire). PR #372.
- **HS-105-02 — drop-onto**: the matrix as contract data; targets
  light via their `_sel` images; verb tags name the release; a drop
  holds content beside the run verb (never fires a model); Knowledge
  filing proven on the wire. PR #373.
- **HS-105-05 — the menu bar**: one verb registry, menus render from
  it, ghosted-with-reason over hidden, Go ≡ DESK_TOOLS pinned; the
  wire face deliberately waits for the kernel's userland dispatch
  (Article V). PR #373.
- **HS-105-06 — docs**: USER_GUIDE "Using The Desk", the NEW
  `docs/internal/DESK_GRAMMAR.md` (six laws, each citing its guard),
  ARCHITECTURE + AGENT_BRIEF + README updated; SECURITY deliberately
  unchanged (no new boundary). PR #373.

## The walks earned their keep

Defects caught by driving the real product and fixed at cause, never
patched: the fractional-upscale mush itself; jittered default homes
stacking cells at density; the phone's impossible 33-object grid; a
zustand fresh-object selector looping React and unmounting the world;
menus surviving outside clicks; six em-dashes the doc guard refused;
the API-surface manifest and two stale ledger pins the closeout sweep
caught (one turned from a moving total into a floor).

## The spec ledger (web-desk-is-the-spec, standing direction)

**Contract-specified atoms** (a Swift recreation reads these):
- The icon law: cell constants in `sceneModel.ts` (SPRITE 64 1:1,
  LIFT 80, OBJ_W 104), the state-image set + derivation script, badge
  anchors + their named source routes
  (`research-badge-source-map.md`).
- The drop matrix: `dropMatrix.ts` (accepts/verb/action per kind).
- The Info contract: `infoContract.ts` (footprint measures, the
  pinned property vocabulary + update paths).
- The verb registry: `verbRegistry.ts` (ids, menus, ghost rules,
  Go ≡ DESK_TOOLS).
- Persistence keys: `hs.desk.zone-views`, `hs.desk.zone-windows`,
  `hs.desk.view` (+ the density default rule), the panel system's
  existing keys.
- The law prose: `DESK_GRAMMAR.md` + `web/ICON-DISCIPLINE.md`.

**Spec debt (TypeScript-only behavior, named)**: the engine's drag
physics and thresholds (tap arm 400ms/8px, drag threshold 4, drop
lighting mechanics); the clean-grid layout math (`objUnit`); the bob
animation envelope; zone-window fly-out motion; the menu dismissal
grammar; the Info card's section composition order. These need
contract prose before a Swift build starts.

## Bookkeeping

- BACKLOG candidates recorded: drawer-window drag-reorder (unlocks
  Clean up/Snapshot + free arrangement), cross-window drag re-filing,
  the orb as a drop target, multi-object drops, per-object receipts
  (the kernel journal's feed), window-head menus + keyboard
  equivalents, artifact/paper sprite regeneration, pull-down
  screens/workspaces, the icon editor.
- Phase 104 (Borrowed Fire II) unblocks at this phase's close; the
  kernel RFC's prerequisites may ride any phase as riders.

## The close

The sitting-loop verdict is recorded in
[evidence-story-07](./evidence-story-07.md); the phase closed only on
the owner's acceptance per Article IX.4.

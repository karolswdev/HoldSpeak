# HS-202-03 - Shared controls on the first-use path become library species

- **Project:** holdspeak
- **Phase:** 202
- **Status:** done
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

From the surface inventory of 2026-09-20 (`docs/internal/SURFACE-INVENTORY-2026-09-20.md`, §6 story 03; appendices 01–04; Astra's check `docs/internal/checks/surface-inventory-astra.md`). The Seven Tenets govern: first-use first (2), one obvious move (3), the component framework (5), Workbench 2.0+ (6); Articles III and VI; UX-CANON A.

## Scope

- **In:** Menu items, wing tabs, the dock, DeskEditor's controls, and the consumers those flows touch (bounded by the 157-site source census, migrated in this order; the rest ledgered)
- **Out:** everything the inventory's §6 ledger records; faces the five owner jobs do not touch; the broad census numbers as gates (they are diagnostics re-run at phase close).

## Acceptance criteria

- [x] the source-button ratchet moves down by the migrated sites; no raw control on the five jobs' screens — A1 **174 -> 106** across 68 sites in 31 files; `A1_RATCHET` and `tests/ux_canon_ceiling.json` both carry 106.
- [x] Every change has a fence proven red first on a real isolated hub; shots at 1440 and 393 in this story's assets; the first-use smoke (story 01) green after the change — the source fence red at 18 files, the lowered ratchet red at 174 on `main`'s tree, both green here; 8 shots; the smoke green at both widths.
- [x] Every verb the library Button; no prose; no modal; no counter of zero; one filled primary per window; labels in ASD-STE100 — no label string was touched (story 04 owns those); the species change is ink-neutral by construction (no stylesheet defines `.btn--chrome`, fenced).

## Test plan

- **Unit:** the fences the story names; vitest for face rules.
- **Integration:** the first-use smoke at both widths; the focused rigs the story touches.
- **Manual / device:** shots; story 06 is the owner's sitting.

## Notes / open questions

Lanes are assigned at build time under TWO-BRAINS §4 (default: Astra takes the backend and verification-harness work, Muad'Dib the faces; either brain checks the other's built lane before merge).

### What was built

The library `Button` gained ONE new variant, `chrome`
(`web/src/components/signal/Signal.tsx`, contract line in
`web/src/desk/surface/contract.md`): the verb species WITHOUT the plate, for
a control whose material is drawn by the strip it rides. It stamps only the
marker `btn--chrome` — a class **no stylesheet in the product defines**, so
the menu row, the wing tab, the dock chip and the rail key keep their ink to
the pixel. The same change gave the species a `type="button"` default (a raw
`<button>` in a form submits; the species never does unless asked).

The four named strips, in the story's order, then every raw control on the
five first-use jobs' screens, then the shared library species those screens
compose (Disclosure, ChoiceCardGroup, ActionNotice, ProvenanceChip,
LedgerFilter, ProgressPlan, citations, `SurfaceRow`/`SurfaceState`/
`EditInPlace` in `Surface.tsx`). 68 sites, 31 files.

`CatalogRail.tsx:211` was the one control that was not a `<button>` at all —
a `div role="button" tabIndex={0}`, the Meetings stream's row body. It is now
the library Button, and `.meetings-stream-row-body` erases the UA button
plate (`appearance/background/border/padding`) so the row draws exactly what
the div drew; the glass rig reads all five properties back off the screen.

### LEDGERED — raw controls NOT migrated (106 A1 residue)

Named out of scope by the brief (faces the five owner jobs do not touch):
`WorkbenchWindow` 23, `DeskToolInspector` 10, `SessionPullout` 6,
`GroundingSection` 5, `CoderPullout` 5, `ThreadPullout` 3.

Left for the same reason, each with its count:
`InfoWindow` 4, `MissionControlConveyor` 4,
`DeliveryBoard` 3, `GlassDropLayer` 3, `WorldStage` 3, `ArtifactPullout` 3,
`WorkflowEditor` 3, `CapabilitySection` 3, `EmptyDesk` 2 (the ＋Create face
the census found unreachable), `WorkbenchResourceful` 2,
`WorkbenchTemplatePicker` 2, `ZoneWindow` 2, `ChainPullout` 2, `KbEditor` 2,
`UpdatePosture` 2, and 15 one-site faces (`CallChip`, `SpeakerGlyph` and
`ModeTabs` belong to the Thread pullout; `TopologySurface`,
`ComponentsCore`, `WorkbenchesHomeCore`, `RailsPicker`, `DeliveryBoard`'s
dossier and list sections, `DirectoryPullout`, `RecipeEditor`,
`FollowThroughView`, `DeskSortableTable`, `StewardPosture`).

### Found on the way, NOT fixed (each is someone else's story)

1. **Escape from a menu-bar menu drops focus to the body.** `WorkMenu`
   accepts `returnFocus` and `DeskMenuBar.tsx` has never passed it — on
   `main` as well as here (`git show HEAD:…/DeskMenuBar.tsx | grep
   returnFocus` finds nothing). The rig asserts Escape CLOSES the panel and
   records where focus lands as NOT ASSESSED.
2. **Under `prefers-reduced-motion: reduce` the desk-chrome controls report
   `outline-width: 0px` while `outline-style` stays `solid`.** The plated
   `.btn` verbs keep their 2px ring in the same page. It reproduces on
   controls this story never touched (`.desk-mark`,
   `.desk-verbbar-title`, the egress badge) and I could not explain it — no
   stylesheet in `web/src` declares an outline for those classes and the
   `--focus-outline-width` token reads `2px` on the element itself. The
   census measured its 69 tab stops without reduced motion, which is why it
   reported zero ringless stops. **UNKNOWN, not broken** — it belongs with
   story 05 (the tokens). The ring assertions here run in the default motion
   state; reduced motion is emulated only for the shots.
3. `NotePullout.test.tsx > scrolls a successful Original reveal…` failed
   once in three full web-suite runs and passed 3/3 in isolation and on the
   re-run. Reported as a flake, not a regression.

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
- [x] Every change has a fence proven red first on a real isolated hub; shots at 1440 and 393 in this story's assets; the first-use smoke (story 01) green after the change — the source fence red at 18 files, the lowered ratchet red at 174 on `main`'s tree, both green here; 8 shots; the smoke green at both widths. **Scope of the glass rig, exactly:** it presses the keys listed in its docstring on four strips and asserts those results; it is not a proof of complete keyboard equivalence, and nothing in this story compares images.
- [x] Every verb the library Button; no prose; no modal; no counter of zero; one filled primary per window; labels in ASD-STE100 — no label string was touched (story 04 owns those). The ink argument is **by construction, not by image comparison**: no stylesheet in the product defines `.btn--chrome` (fenced in `web/src/desk/__tests__/hs202ChromeSpecies.test.tsx`), so the marker cannot paint; the one site that changed element type (`CatalogRail`) has its computed box read back off the glass. **Pixel identity is not claimed.**

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

### Found on the way, NOT fixed (each has an owner below)

1. **Escape from a menu-bar menu drops focus to the body — INHERITED.**
   `WorkMenu` accepts `returnFocus` (`web/src/desk/components/DeskMenu.tsx:455`,
   consumed at `:559` and `:562`) and `DeskMenuBar` renders it without that
   prop (`web/src/desk/components/DeskMenuBar.tsx:134-144`; the same call site
   at the base commit is `73758ef3:web/src/desk/components/DeskMenuBar.tsx:133-143`
   and `git show 73758ef3:…/DeskMenuBar.tsx | grep -c returnFocus` returns 0).
   The rig asserts Escape CLOSES the panel and says in its docstring that the
   landing spot is deliberately unasserted. Ledgered in the phase status with
   an owner.

2. **Reduced-motion focus-ring loss — INHERITED, by paired reproduction.**
   Counsel was right that "untouched controls" proves nothing (`.desk-mark`
   IS migrated, `web/src/desk/components/DeskChrome.tsx:161`), so the claim
   is now measured instead of argued.
   `assets/story-03-shots/reduced-motion-paired-baseline.json` holds it: the
   same hub, the same cold seeded desk at 1440, the same 26 Tab stops, the
   same `prefers-reduced-motion: reduce`, three rounds, with ONLY the built
   bundle swapped — built from `git archive 73758ef3 -- web` for the base and
   from this branch for the branch. (`web/src` is byte-identical between this
   branch's base 10e22669 and 73758ef3, so the base bundle IS main's.)

   | round | ringless rows, base 73758ef3 | ringless rows, branch | ringless ONLY on branch |
   |---|---|---|---|
   | 1 | 18 / 26 | 17 / 26 | none |
   | 2 | 18 / 26 | 17 / 26 | none |
   | 3 | 18 / 26 | 18 / 26 | none |

   **Zero controls lose a ring only on this branch.** The one stop that
   varies is the FIRST Tab target (`.desk-mark`): 2px/2px/0px across the
   three branch rounds against 0px/0px/0px on the base — unstable at stop 0,
   so it is claimed as neither a heal nor a regression.

   Mechanism **UNKNOWN**, with what was ruled out recorded: no
   `@media (prefers-reduced-motion: reduce)` block in the built CSS resets an
   outline; `--focus-outline-width` computes to `2px` on the ringless
   elements themselves; and those elements compute
   `outline-color: currentColor` — the INITIAL value — so the single global
   `:focus-visible { outline: var(--focus-outline-width) solid var(--accent) }`
   rule did not apply to them at all. It is a cascade question, not a token
   question, which is why parking it on story 05 (the tokens) would not have
   resolved it. Ledgered in the phase status with an owner.

3. `NotePullout.test.tsx > scrolls a successful Original reveal…` failed once
   in three full web-suite runs and passed 3/3 in isolation and on the
   re-run. Reported as a flake, not a regression.

### For the combined revision (counsel, combined section, finding 2)

Story 05's type rig records EVERY class on a wing tab
(`tests/e2e/test_hs202_05_first_use_type_floor.py:245`), so the twelve
recorded wing signatures will not match once `btn--chrome` is present. The
marker name is load-bearing here — the contract, the library comment, two
vitest fences and the glass rig all key on it — so **it is not renamed**;
05's worker normalizes that one marker out of its recorded signature, or
re-records the twelve entries, keeping the semantic classes and the size
checks. Told to 05 separately.

Real file overlaps with the sibling lanes, for the integrator:
`web/src/pages/cores/LiveCore.tsx` and
`web/src/pages/cores/history/CatalogRail.tsx` with 04 (03 changed only the
element and its variant on those two; every label string is 04's), distant
hunks in `web/src/desk/surface/surface.css` with 05, and
`current-phase-status.md` with every lane. `web/src/components/signal/Signal.tsx`
is 03's alone.

### Counsel round (#598, RATIFY-WITH-CONDITIONS)

Read at `.tmp/two-brains/20260921-123218-counsel-202-345-counsel/last.md`.

- Condition "correct the overclaims" — done: the rig docstring now states
  what it presses and what it does not prove, the contradiction between its
  opening claim and its Escape exclusion is gone, and both acceptance lines
  above are re-worded. Pixel identity is not claimed anywhere.
- Condition "paired baseline reproduction" — done, INHERITED (table above).
- Condition "ledger Escape's `returnFocus` with file:line" — done (item 1).
- Condition "regenerate the Philo inventories" — done: all six scripts
  regenerated then `--check`ed clean; `docs/generated/api-reference.json`
  (+2 rows: this story's new rig registering as a caller) and
  `docs/generated/boundary-candidates.json` (16 line-number shifts in the
  files whose imports moved) ship with this round.
- MISSED, "give the reduced-motion item a surviving home" — done: it is a
  phase-status ledger row with an owner, no longer parked on story 05.

### The strips owe their rows 44 px at 393 (story 05's measurement)

05's canon splits the duty: a PLATED Button owns 44 px through its halo; a
CHROME Button is a strip ROW, so the STRIP owes it the height. 03 owns two
such strips, and both were short on the live 393 screens. Measured, fixed in
each strip's own CSS, and re-measured —
`assets/story-03-shots/strip-touch-targets-393.json`:

| row | class | before | after |
|---|---|---|---|
| Outcomes · Review · Record · Artifacts | `desk-wing` | 23 px | 44 px |
| the wing gear door (`Meeting plumbing`) | `desk-wing desk-wing-door` | 24 px | 44 px |
| Overview · Reset layout | `desk-dock-reset` | 22 px | 44 px |
| Record a meeting | `desk-orb` | 40 px | 44 px |
| Hide the menus · Change places | `btn btn--secondary` | 36 px | 44 px |

Ten short rows before, **none after**. The gear door was not in the note; the
measurement found it and it is paid with the rest.

- `web/src/desk/components/pullout.css` — a new `@media (max-width: 720px)`
  block gives `.desk-wing` `min-height: 44px`. The breakpoint is the
  product's ONE declared phone width (`web/src/desk/useCompactViewport.ts:5`,
  the same query `dock.css` already uses), so no third seam is invented.
- `web/src/desk/components/dock.css` — inside the EXISTING
  `@media (max-width: 720px)` block (the one HS-202-02 used to pay the
  launchers and the chip close): `.desk-dock-reset` becomes a 44×44
  `inline-grid` around its 14 px glyph, `.desk-dock .desk-orb` 40→44 px
  (the 40 px sprite stays 40 px, centred), and
  `.desk-room-actions > button` 36→44 px. Real geometry, which composes
  with 05's halo rather than arguing with it.

**The 1440 face is untouched, by measurement, not by assertion:** the same
page measured with the pre-fix bundle and the post-fix bundle swapped
underneath it — 19 rows compared, **0 changed**, dock box 53 px → 53 px.
Both rules live inside the phone media query.

Fenced in the glass rig (`tests/e2e/test_hs202_03_species_glass.py`,
`_strip_targets`): at 393 every row of the dock and of the wing bar has a
bounding height ≥ 44 px and no two rows overlap (one pixel allowed — the wing
segments butt with a shared hairline by design). The dock is measured twice,
the second time with a window open, because `Overview` and `Reset layout` do
not exist until then. Proven red on the pre-fix bundle:
`the dock: rows under 44px at 393 … 'Hide the menus' 36px, 'Change places'
36px, 'Record a meeting' 40px`. `wings-393.png` and `dock-393.png` re-shot.
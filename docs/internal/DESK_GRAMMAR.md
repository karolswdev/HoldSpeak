# The Desk Grammar

The written law of the desk's world layer, forged in Phase 105
(Workbench) from the owner's standard: an OS, not a gimmick — Workbench
2.0 on steroids. This document records FACT about the shipped tree, in
the Constitution's voice; where a rule and the code disagree, one of
them is a defect to fix consciously, never to paper over. Cited by
stories as law. Read [`AGENT_BRIEF.md`](AGENT_BRIEF.md) before any UI
work; the [Constitution](CONSTITUTION.md) outranks both.

## 1. The icon law (HS-105-01)

1. World art is 64×64 pixel art rendered **1:1** — never fractionally
   scaled, tilted, or size-jittered. Integer-true or absent.
2. One uniform cell for every kind (`sceneModel.ts`: SPRITE 64, LIFT
   80, OBJ_W 104). Importance is expressed by state, never by scale.
3. Distinct silhouette per kind; color supports, never substitutes.
   A directory is a drawer.
4. Every sprite ships as a REAL state set on disk — rest, `_sel`
   (brightened, rimmed), `_stale` (desaturated) — derived by
   `web/scripts/gen-sprite-states.py`. Runtime filters never
   substitute for a state image.
5. Badges ride only NAMED live fields (the audited source map in the
   phase directory): member count bottom-right, freshness (48h)
   top-right, needs-you top-left, posture marks bottom-left. Anchors
   sit on the art at rest and on the box when selected. Absent data
   renders as absence.
6. Default homes grid deterministically (the Clean Up rule); a user
   drag parks anything anywhere and the arrangement is sacred.
7. Density has altitudes: a compact desk with no saved view choice
   leads with the List above 16 objects; an explicit choice always
   wins.

Guard: `web/src/desk/gl/__tests__/iconCell.test.ts`. Art recipe:
`web/ICON-DISCIPLINE.md`.

## 2. The selection and open law (HS-101 round 9 + 105)

Mouse: single click SELECTS (cell box + inverted label chip);
double-click OPENS. Touch/pen: tap opens. Escape closes the front
card only. Windows COEXIST — object cards, drawer windows, and Info
cards are all real desk windows on the one panel system (rect,
stacking, dock chips, restoration).

## 3. The drawer law (HS-105-03)

1. A zone IS a drawer icon in the uniform cell — never a tray, never
   instruction prose.
2. Open = a real window flying from the gesture point; several
   coexist; dive survives only as the context menu's Focus verb.
3. Two views, one truth: Icons (the cell contract) and List (Name /
   Kind / Modified, sortable both ways). THE WINDOW REMEMBERS — view,
   sort, direction per zone (`hs.desk.zone-views`), the open set
   (`hs.desk.zone-windows`), rect via panels — and restores.
4. Take out un-files through the real membership DELETE. Empty says
   "Empty".

Guard: `zoneWindow.test.tsx`.

## 4. The drop law (HS-105-02)

1. The matrix is CONTRACT DATA (`dropMatrix.ts`): a target kind
   declares what it accepts and the NAMED verb; unlisted pairs are
   inert. Components never hardcode kind pairs.
2. A viable target lights via its real `_sel` image; the verb tag
   rides the cursor and states exactly what release does — the
   consent surface.
3. A drop that would run a model instead HOLDS the content as run
   material beside the run verb; the human presses it.
4. A drop is an entrance, not a move: the dragged object returns
   home.

Guard: `dropMatrix.test.ts`.

## 5. The Info law (HS-105-04)

1. ONE Info card for every kind and for drawers, derived from
   `infoContract.ts` — a kind declares its footprint measure and its
   property keys; no kind hand-builds its Info.
2. Identity's name edits in place through the existing update paths.
3. Properties (tooltypes) exist ONLY where a real update path backs
   them; the guard pins the whole vocabulary (today:
   `recipe.runs_on`). Growth is one real field at a time.
4. Receipts wait for a per-object journal route (the kernel's feed);
   until then the section does not render.

Guard: `infoContract.test.ts`.

## 6. The verb law (HS-105-05)

1. A verb is a REGISTERED capability (`verbRegistry.ts`); every face
   renders the registry. Faces today: the menu bar and the ⌘K shelf
   (Go ≡ DESK_TOOLS, pinned). The wire face lands with the kernel's
   userland dispatch — never before its consent model (Article V).
2. Menus GHOST with the reason; they never hide. The system admits
   what it can do.
3. An open menu dismisses on any outside pointer-down and on Escape
   from anywhere.

Guard: `verbRegistry.test.ts`.

## 7. Standing remainders (recorded, not waived)

Clean up / Snapshot verbs + free member arrangement inside drawer
windows (need drag-reorder); cross-window drag re-filing; the orb as
a drop target; multi-object drops; keyboard equivalents beyond ⌘K;
menus on window heads; per-object receipts (kernel journal); the
artifact "paper" sprite reads poorly at cell scale (regenerate per
the icon discipline).

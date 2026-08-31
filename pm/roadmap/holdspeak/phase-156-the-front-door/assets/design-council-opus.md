# Direction memo -- OPUS voice on the component-library reform

## 1. Architecture: surface/ is the library; name it so and fence it

**Position:** Promote `web/src/desk/surface/` to the canonical component library by renaming it `web/src/desk/lib/` (or `surface-lib/`), publishing a barrel `index.ts` with the public contract, and adding an architectural guard rule that flags any new `.tsx` in `desk/components/` or `desk/pullouts/` that renders layout primitives (sections, rows, verb bars, gadget sheets, footers) WITHOUT importing from the library.

**Evidence:**
- Surface.tsx:1 already declares itself "the ONE way to build window content."
- The lane system (`chair/Lane.tsx:6-7`) composes exclusively from `SurfaceSection`, `SurfaceRows`, `SurfaceRow` -- this is the proof that the contract works when adopted.
- Adoption is at 52% in components/ (32 of 61 non-test tsx files import from `surface/`). The other 29 build their own structures.
- `guard-architecture.mjs` enforces five structural rules (no Astro, no innerHTML, no global selectors, no raw fetch, no forbidden deps) but has ZERO rules about Surface usage. The gate exists; it just does not guard the thing that matters.
- The token chain is already settled: `design-tokens.json` -> `generate-tokens.cjs` -> `tokens.css` (339 lines, three layers) -> `validate-tokens.cjs` gate. `desk-tokens.css` is a 6-line re-export. No reform needed here; the split is justified (convenience index, not a second source).

**Rejected counter-argument:** "Moving surface/ to a new path breaks every import." True, but a barrel re-export at the old path eliminates breakage. The rename is a signal, not a migration: the barrel is the contract boundary, and consumers that import internal modules get a lint warning. The alternative -- leaving the name `surface/` while calling it "the library" -- means Phase 156 stories will keep writing `from "../surface/Surface"` with no clear distinction between library-grade primitives and surface-specific internals like `sparse.ts` or `XtermPane.tsx`.

**Concrete recommendation:** Add one rule to `guard-architecture.mjs`: any file in `desk/components/` or `desk/pullouts/` that defines a `className` matching the pattern `surface-section|surface-row|gadget-row` (i.e., re-implements a library primitive's DOM) fails the guard. This is a fence, not a migration -- existing files are allowlisted, but new code cannot add more one-offs.

---

## 2. The delight layer: five candidates for library promotion

**Position:** These five behaviors recur across rooms and should become library exports with contracts, not local re-implementations:

| # | Candidate | Current home | Contract shape |
|---|---|---|---|
| 1 | **StateChip** (status labels: OFF/LISTENING/THINKING) | `CallChip.tsx` uses inline labels; `thread-head-instruments` in thread-pullout.css:53-62 styles the same grammar | A `<StateChip state="..." />` with 4-5 canonical states (off, active, busy, error, warn), desk-token colors, uppercase mono 11px -- the thread head's label, the lane's badge, the health strip's indicator |
| 2 | **In-flow popover** (a popover attached to a row verb, never a modal) | Each pullout re-implements tooltips/menus locally; `chrome-menus.css` (904 lines) is a CSS monolith for one component's menus | A `<Popover anchor={ref} />` that positions via the Popover API or absolute+portal, keyboard-dismissable, desk-token styled, owns its own z-index from the ladder (`--desk-z-popover: 82`) |
| 3 | **ProgressPlan** (a live plan with per-item progress) | Does not exist yet; HS-156-03 acceptance criteria demand it ("the live plan view, per-item progress, in-flow, no modal") | A `<ProgressPlan items={[{label, status, progress?}]} />` rendering as a compact list with status chips |
| 4 | **Keyboard roving for tab-like composites** | `useRovingRows` (`roving.ts`) handles row lists; `ModeTabs.tsx:86-100` and `CallChip.tsx` reimplement arrow-key navigation locally | Extend `useRovingRows` with a `horizontal` mode (ArrowLeft/Right walk tabs) or export a `useRovingTabs` peer |
| 5 | **RAW fold** (a disclosure that hides advanced content behind one toggle) | The front door's "advanced layer fold" (HS-156-03) and the existing RAW debug posture (CLAUDE.md: "debug hides behind RAW") both need the same pattern | A `<Fold label="..." defaultOpen={false}>{children}</Fold>` with desk-token hairline + mono label, animated height, remembers state per key |

**Rejected counter-argument:** "Building library components before their second consumer exists is speculative." Fair for most libraries, but HoldSpeak's UIUX_JUDGMENT.md (HS-100-02) already names the pattern: the thread head, the lane badges, the health strip, and the door's plan view all need a state chip. The demand for StateChip has four known consumers before the first line ships. The fold has two (RAW debug, the front door's advanced layer).

---

## 3. Reform without a rewrite: fence new, adopt opportunistically

**Position:** Two mechanisms, different enforcement levels:

**Hard fence (guard-architecture.mjs, blocks the build):**
- New files in `desk/components/` or `desk/pullouts/` must not re-implement library layout primitives (the className-pattern rule from position 1).
- New CSS files in `desk/` must not contain raw hex/rgb/z-index/ms literals (already enforced by `validate-tokens.cjs`).

**Soft adoption (opportunistic, story-by-story):**
- When a story touches an existing file that uses bespoke layout, it MAY migrate that file to Surface primitives. It is not required to.
- thread-pullout.css (1,229 lines) is the single largest CSS file and the most obvious candidate for opportunistic extraction: its state-chip, mode-tab, and fold patterns should migrate to the library as they are touched. No dedicated "migration story" -- the migration travels with feature work.
- The 17 CSS files in `components/` (6,465 lines total) are not rewritten. They shrink only when a feature story touches them.

**Rejected counter-argument:** "A soft adoption will never converge -- nobody will voluntarily migrate old CSS." The evidence says otherwise: the pullout directory already adopted Surface primitives across 13 of 14 pullouts (every one imports from `surface/`). The pattern is: when you build something new in a room, you reach for the library. The fence prevents NEW sprawl; time and feature work erode the old sprawl. A big-bang migration is the real risk -- it would touch 29 files that work, creating a combinatorial regression surface with no feature value.

---

## 4. Visual gates: shot sheets at the story close, not every commit

**Position:** A screenshot-walk is mandatory at story close (CLAUDE.md already says "screenshot-walk before claiming UI done; 1440+393 on the real hub"). The reform is: formalize the artifact.

**Mechanism:**
- Every story that touches `web/src/desk/` carries a **shot sheet** in its evidence file: 1440px and 393px screenshots of the affected surface, labeled with the story ID, annotated with red rectangles around changed regions.
- The shot sheet is checked by the HUMAN at the story-done gate (the owner or a delegate). No automated pixel-diff -- that tooling cost is not justified at this scale.
- The existing `dw evidence capture` path records the command, exit code, and output. Screenshots land as assets next to the evidence file (`assets/hs-NNN-NN-shot-1440.png`).
- The visual gate is a checkbox on the story acceptance criteria, not a CI step. It is cheap because the glass leg already renders both widths; the cost is one extra Playwright `page.screenshot()` call per width, saved as an asset.

**Rejected counter-argument:** "Automated visual regression (Percy, Chromatic, Storybook) catches drifts humans miss." True, but the setup cost (Storybook stories for 40+ components, a hosted visual-diff service, flake management) is disproportionate for a one-user product built by two people. The owner's eyes on two screenshots per story IS the quality gate. If the team grows, revisit.

---

## 5. Phase 156 consumption: four library pieces BEFORE stories 03 and 05

**Position:** The front door (HS-156-03) and topology map (HS-156-05) should be the reform's first customers. Four library pieces must exist before those stories build:

| # | Library piece | Needed by | Why before, not during |
|---|---|---|---|
| 1 | **StateChip** | 03 (health strip), 05 (node health: reachable/unreachable/downloading) | story-05 acceptance: "a vitest asserts no new one-off styled primitives where a library component exists." If StateChip does not exist as a library primitive, story 05 must invent one locally and then a test cannot distinguish it from a one-off. |
| 2 | **Fold** | 03 (the advanced-layer fold: "the health strip above the UNCHANGED advanced Library/Assignments view") | The fold is the entire door/advanced-layer boundary. Building it as a one-off in story 03 then extracting it for RAW debug is backwards. |
| 3 | **ProgressPlan** | 03 ("the live plan view, per-item progress from 02, in-flow, no modal") | The plan view is a new visual pattern. If it ships as local CSS in the models surface, a future room (e.g. a workbench run plan) must copy-paste or extract. Building it in the library first costs the same lines and prevents the copy. |
| 4 | **guard-architecture rule** (the fence from position 1) | 05 (the topology map's acceptance: "a vitest asserts no new one-off styled primitives where a library component exists") | The fence makes the vitest assertion enforceable at build time, not just in a single test. |

**Rejected counter-argument:** "Building library pieces in a separate story before their consumer is waterfall -- build them inline with the feature." The HS-156-05 acceptance criteria explicitly demand the fence ("a vitest asserts no new one-off styled primitives where a library component exists"). That fence cannot be written if the library does not have a published contract to test against. The library pieces are not speculative; they are acceptance criteria for stories already chartered.

---

## First 10 moves (ordered for Phase 156 to consume)

1. Add barrel `web/src/desk/surface/index.ts` exporting the public contract: `Surface*`, `SurfaceFooter`, `Material`, gadgets, `useRovingRows`, `Fold` (new), `StateChip` (new), `ProgressPlan` (new).
2. Write `StateChip` in `surface/StateChip.tsx` + `surface/state-chip.css`: uppercase mono 11px, four canonical states (off/active/busy/error), desk-token colors, focusable.
3. Write `Fold` in `surface/Fold.tsx` + amend `surface/gadgets.css`: hairline + mono label, animated height, `defaultOpen` prop, remembers-open keyed by a caller-supplied `id`.
4. Write `ProgressPlan` in `surface/ProgressPlan.tsx` + `surface/progress-plan.css`: items list with state chips and optional progress bar, desk-token only.
5. Extend `useRovingRows` with a `direction: "horizontal"` option so tab-like composites (ModeTabs, future topology tabs) can share the hook instead of reimplementing arrow-key navigation.
6. Add the library-primitive fence to `guard-architecture.mjs`: files outside `surface/` that define CSS classes matching library-primitive patterns fail the guard. Allowlist every existing file.
7. Write vitest for StateChip, Fold, ProgressPlan (the library's own test coverage -- `surface/__tests__/`).
8. Migrate `CallChip.tsx` to use `StateChip` (its four states map 1:1) -- proof that the library serves a real consumer and the migration path works.
9. Migrate `ModeTabs.tsx` to use `useRovingRows({ direction: "horizontal" })` -- proof that the horizontal mode works.
10. Add the shot-sheet convention to the Phase 156 story template: acceptance criteria require 1440+393 screenshots as evidence assets.

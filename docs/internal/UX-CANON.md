# The UX Canon — what every face must do (ratified by the owner's rulings)

The Constitution is the supreme canon (docs/internal/CONSTITUTION.md);
DESIGN_SYSTEM.md is the material canon (tokens, the interior type
scale, the composition rules, the chrome ladder); the surface library
contract (web/src/desk/surface/contract.md) is the species canon. This
document is the FACE canon: the rules a Fedaykin must build to before
touching anything a user sees, gathered from the owner's rulings and
the scars of Phases 100–169. Where a face disagrees with this, the
face is wrong. Every rule names its ruling.

## A. The owner's rulings (verbatim where he ruled)

1. **Every verb is the library Button.** A raw `<button>` in a face is
   a bounce ("Why is the edit button such a generic HTML button, but
   not a button of our design component library…?", 2026-09-04).
   Lead/primary splits are species bugs, fixed in the library.
2. **Design the face on the library, on the canvas, BEFORE build.** The
   owner ratifies artboards, not code ("HECK YES, a BIG YES to this",
   2026-09-03; "word", 2026-09-04). Then: **build what was ratified** —
   the artboard beside the shot every round (169's five rounds).
3. **No prose in the UI.** Tokens, verbs, counts, names. A sentence on
   a face is a defect; a helper paragraph is a bounce ("Walls of
   text…, complete disregard to our component", 2026-09-03). The one
   exception: an empty state is ONE true line with the next time
   something happens.
4. **No modals; edit in-world.** Wizards, pickers, Adjust, answers:
   wells that unfold under the row, or aerogel insets. A modal is a
   bounce.
5. **Streamlined means one screen where one screen will do.** The
   169 door: what was 17 face steps is 5 clicks. A plan of steps, a
   review page, a wizard with its own plan — each must earn its place
   against "will you use this on a Tuesday?" (Phase 139).
6. **A window's wings never leave the window** — titles shrink first
   (`min-width: 0` on every nowrap ellipsis title).
7. **The name is said once per face.** The title bar carries it; the
   head repeats the outcome only when the title bar truncates it.
8. **No counters of zero.** `0 Watches`, `REV 1`, `0 today` are bounces;
   omit the zero token or say the true thing (`CLEAR`, `Nothing today`).
9. **Egress exactly where egress happens.** The host chip on the row
   that leaves the machine, never in a header for decoration, never
   missing where a fetch is triggered (Article III).
10. **Honest states, plain reasons.** `CAN'T CHECK · Jira rejected the
    query`, never a stack, never a smoothed-over green.
11. **A verb that does nothing is a lie.** Withhold it (and ledger it)
    rather than ship it dead; a section-level interim verb is honest
    when it opens a real face.
12. **Setup flows must be joyful** (2026-08-17): the first open is the
    most important face; a stranger must know what to do first without
    narration.
13. **Beauty pass after every functional pass; the owner sees shots
    before merge** (Workbench 2.0 directive).

## B. The species a face composes from (never hand-rolled)

Button (primary · ghost · dense) · StateChip (success · warning ·
failure · idle · unreachable; `●` for health) · EgressChip (the host)
· ProvenanceChip · surface-token[data-chip] · SurfaceLedger /
SurfaceLedgerRow (52px lead slot; hover verbs; `wrap`) · SurfaceSection
(caption + count) · SurfaceIdentity · SurfaceStream/Day/Entry ·
SurfaceWell · SurfaceFooter (egress · receipt · verbs; portaled — use
its `className` hook) · ChoiceCard/Group · CheckGadget (incl.
`variant="token"`) · StringGadget · CycleGadget · Disclosure ·
EditInPlace · MicButton (square; on every text input — the voice law)
· ScrollHint (every scrolling well announces itself) · LedgerFilterBar
· ProgressPlan (only for things that genuinely RUN). A recurring
element a face needs and the library lacks is ADDED to the library,
documented in contract.md, then used — never invented inline.

## C. The type steps (the interior canon)

display 26/650 `--font-display` — ONCE per face, the one big fact ·
primary 15/600 `--font-sans` — the thing's name · body 13 · secondary
12 mono — counts, times, hosts · caption 11 mono uppercase 0.06em —
section labels, chips. A face uses at least three steps; a face that
collapses to one is a defect (the geometry probe).

## D. Grammar rules the scars taught

- One row grammar per species at both widths; the same object never
  drawn two ways (compose repeated things as one object).
- 393 stacks under a container query named `surface` (the desk's
  container; `surface-window` never matched) — never viewport media.
- A control that must be clicked LOOKS clickable (the beveled gadget
  with a stroke chevron), and an entry card carries its verb.
- Owning the body means UNMOUNT the rest; an inline wizard under other
  content is a scroll hunt.
- The empty first paint never happens: first paint carries the counts
  already fetched; sections rise in; idle never moves; reduced motion
  = instant. Four named motion moments per face at most.
- Empty slots never move their neighbours (the footer's egress slot).
- Filters are flat tokens; wings are the beveled strip; the two never
  look alike.

## E. The review protocol (how a face flips)

1. Artboards at 1440 + 393 on the ratified shell; counsel hunts the
   canon before the owner; the owner's word.
2. The build's rig asserts the ARTBOARD, not presence: type steps,
   token positions, no intersecting row children, the well in frame,
   an honest count, one display element; shots at both widths.
3. The orchestrator reads every PNG beside the artboard; a worker's
   "matches" is a claim.
4. Guards make the canon mechanical: no raw `<button>` in a face; no
   `border-left` accent rail; no emoji glyphs; no raw snake_case kinds
   on a face; no counters of zero in copy; the product-copy guard; the
   design-system token guard; the density guard.
5. The owner's walk on his desk, both widths, the window shot per
   step; his words verbatim; scars become laws here.

**Guards.** `tests/unit/test_ux_canon_ratchet.py` runs the canon
scanner (`scripts/ux_canon_scan.py`) against the live `web/src` tree
and enforces three invariants.  (i) *Ratchet*: per-rule violation
counts must not exceed the committed ceiling file
`tests/ux_canon_ceiling.json`; a regression names the rule, the delta,
and the faces that rose.  (ii) *Hard zeros*: DS6 (accent rail) and A9
(missing egress) must stay at 0; A1 (raw `<button>`) must stay within
a named allowlist (4 residues with reasons).  (iii) *Healing*: when a
count drops below the ceiling, the test passes with a notice to lower
the ceiling.  To lower the ceiling after fixing violations, run:
`python scripts/ux_canon_scan.py --write-ceiling tests/ux_canon_ceiling.json`.

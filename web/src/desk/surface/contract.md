# Surface Library Contract (HS-156-03)

## Import path
Feature code imports from `desk/surface` (the barrel). Private paths are fenced.

## States vocabulary
The closed state set: idle, active, working, success, warning, failure, unreachable.
Every state renders icon + text; never color alone.

## Accessibility
- Composites (ChoiceCardGroup, ProgressPlan) use roving tabindex via useRovingRows
- Disclosures have button triggers with aria-expanded, content regions with aria-labelledby
- Popovers trap focus, dismiss on Escape
- Status updates use aria-live="polite" on transition only
- Radio groups use real input[type=radio] with proper grouping

## Tokens
All styling uses design tokens from design-tokens.json. Raw values are forbidden (validate-tokens.cjs enforces).

## surface-token[data-chip] (HS-167-05)
The chip variant of `surface-token` gives it the full chip geometry (border, well bg, etch shadow, 10px mono, 0.06em tracking) used by token rows (steward grant, run receipt refs). Stamp `data-chip` on any `surface-token` that should render as a discrete chip rather than inline text. Tone data-attrs still work.

## Motion
All transitions use --duration-* tokens and --ease-* curves. prefers-reduced-motion removes animation.

## Container behavior
Patterns respond to the surface container (@container surface). They push layout (in-flow); never overlay/modal.

## Composition
- ProvenanceChip and Receipt compose into SurfaceFooter's egress/receipt/verbs slots
- StateChip composes into SurfaceVerbs status slot and standalone
- ActionNotice is a standalone flow element
- ProgressPlan and ChoiceCardGroup are section-level patterns
- Disclosure wraps any content as a collapsible section

## ChoiceCardShell (HS-159)
The card visual language without an interaction model. Owns all `surface-choice-card-*` CSS classes: shell, head (emblem + label), description, summary anchor, fact chips, cost, fold (behind Disclosure), selected/recommended/disabled presence.
- `as` — wrapper element tag (default "div"); ChoiceCard passes "label", features may pass any semantic element
- `beforeHead` — content before the head (e.g. a visually-hidden radio whose `:focus-visible + .head` needs DOM adjacency)
- `selected` — stamps `data-selected` for the accent-wash selection presence
- `recommended`, `disabled` — stamp `data-recommended`, `data-disabled`
- `tier` — accent-temperature key stamped as `data-tier`
- `children` — rendered after the built-in slots, before the fold
- All extra props pass through to the wrapper element (role, aria-*, data-*, event handlers)
- ChoiceCard composes the shell internally (one source of material)

## SurfaceIdentity (HS-167-03)
The project orientation band: name (the Primary type step, 15px/600), chip row (wraps at the narrow container), optional purpose (folds past two lines via Disclosure), outcome as a target token row, optional fold body, trailing token (e.g. read time).
- `name: string` -- rendered at `--desk-type-primary-size`
- `chips: ReactNode` -- StateChips + tokens, one row, wraps
- `purpose?: string` -- one line, folds past two lines via Disclosure
- `outcome?: string` -- rendered as a target token row with a target mark
- `fold?: ReactNode` -- Disclosure body (additional content)
- `trailing?: ReactNode` -- right-aligned on the chip row (e.g. read-time token)

## SurfaceLedgerRow.trailing (HS-167-03)
A new prop: one quiet verb or a chevron, right-aligned after `cells`, its own grid slot (never overlapping the 52px time column). The grid extends to 6 columns when `trailing` is present (stamped via `data-has-trailing`).
- `trailing?: ReactNode` -- quiet Button or chevron
- `wrap?: boolean` -- when true, primary wraps instead of ellipsizing; at the narrow container cells fall under

## SurfaceVerbs.active (HS-167-03)
A new prop: the verb key rendered lit (`aria-current="true"` on the verb button, the verb bar stamps `data-active-verb` on the wrapper). The active verb gets the etched lit state (sunken well via `--desk-window-etch`). Count chips inside verb buttons use the `.surface-verb-count` class.
- `active?: string` -- the verb key rendered lit

## ScrollHint (HS-167-03)
Gradient edge fades for scrolling wells. ONE species with an `axis` prop. Promoted from DoorBoardLane.tsx (horizontal) and steward/model.ts (vertical); both copies replaced with barrel imports.
- `axis: "x" | "y"` -- fade direction
- `scrollRef: RefObject<HTMLElement | null>` -- the scrollable element (when null, falls back to wrapRef.parentElement)
- `className?: string` -- additional class on the wrapper
- Pure function: `computeScrollHint(scrollOffset, scrollExtent, clientExtent)` returns `ScrollHintState` ("none" | "start" | "end" | "both")
- Hook: `useScrollHint(wrapRef, scrollRef, axis)` -- attaches scroll/resize listeners, sets `data-scroll-hint` on the wrapper
- Fence: `computeScrollHint`/`computeVerticalScrollHint` must not be defined outside `desk/surface/`, `desk/chair/lanes/DoorBoardLane.tsx` (thin re-export), and `features/project-room/steward/model.ts` (thin re-export)

## DeskEditor (sanctioned non-barrel import)
`web/src/desk/components/DeskEditor.tsx` is the ONE sanctioned non-barrel import for feature code. It provides the rich text editor used by the Update posture. Feature code may import DeskEditor directly from `desk/components/DeskEditor` without going through the barrel.

## ChoiceCard object slots (HS-156-08)
A ChoiceCard is an OBJECT, not a list. Beyond label/description/facts/cost:
- `summary` — the one-line anchor the eye lands on (what this choice does, one breath)
- `emblem` — a tier mark beside the label, aria-hidden, colored by `tier`
- `tier` — accent-temperature key stamped as `data-tier` (library palettes: light/balanced/full; unknown keys fall back neutral)
- `fold` + `foldLabel` — per-item detail behind a Disclosure; clicks inside the fold inspect, they never flip the radio
- `facts` and `cost` render as chips, not rows
- ChoiceCardGroup `layout="row"` lays cards out as equal siblings where width allows (stacks narrow); RECOMMENDED renders as presence (accent wash + rail), not just a corner tag

## countToken / countLabel (HS-170-02)

- `countToken(n, singular, plural?)` → `"N NOUN"` or `null` at zero — the one way a face says a count (UX-CANON A8: no counters of zero). Render nothing (or the face's one true line) when it returns null.
- `countLabel(label, n)` → `"LABEL N"` at n>0, `"LABEL"` at zero — for section captions.

## FilterTokens (HS-176-03)

The flat one-tap filter strip: `role="group"` over library `Button` species,
one active at a time. Promoted from the composition ratified on the Project
Room's history wing (`ProjectRoomCore.tsx:1550-1566`) per canon B — a
recurring element the library lacked.

- `options: FilterTokenOption[]` — `{ value, label }`; the label is a
  caption-step word (`ALL`, `DICTATION`), never a sentence
- `value: string` — the active option's `value` (the caller owns the state;
  an empty string is the usual "no filter" wire value)
- `onChange(next: string)` — the one-tap toggle
- `label: string` — the group's accessible name (e.g. `"Source filter"`)
- `className?: string` — an extra class on the group span

Presence rules (they are the species, not the caller's business):

- The active token is `Button` **primary dense**, the resting ones **ghost
  dense**; each carries `aria-pressed` and the active one `data-filter-active`.
  No raw `<button>` (UX-CANON A.1).
- **No sparse rule — it never returns `null`.** A strip that vanishes on a
  short or empty list leaves no way to widen the view; it renders over an
  empty stream. This is the difference from `LedgerFilterBar`, which returns
  `null` below `SPARSE_THRESHOLD` (`LedgerFilter.tsx:104`, `sparse.ts:4`).
- **It carries no count.** `matchCount/total` would be a second count on a
  face that says its one count elsewhere (UX-CANON A.7/A.8).
- Not to be confused with `SurfaceWings`: filters are flat tokens, wings are
  the beveled strip, and the two never look alike (canon D).

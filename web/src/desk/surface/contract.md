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

## ChoiceCard object slots (HS-156-08)
A ChoiceCard is an OBJECT, not a list. Beyond label/description/facts/cost:
- `summary` — the one-line anchor the eye lands on (what this choice does, one breath)
- `emblem` — a tier mark beside the label, aria-hidden, colored by `tier`
- `tier` — accent-temperature key stamped as `data-tier` (library palettes: light/balanced/full; unknown keys fall back neutral)
- `fold` + `foldLabel` — per-item detail behind a Disclosure; clicks inside the fold inspect, they never flip the radio
- `facts` and `cost` render as chips, not rows
- ChoiceCardGroup `layout="row"` lays cards out as equal siblings where width allows (stacks narrow); RECOMMENDED renders as presence (accent wash + rail), not just a corner tag

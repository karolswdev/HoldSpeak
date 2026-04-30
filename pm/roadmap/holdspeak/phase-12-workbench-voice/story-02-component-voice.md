# HS-12-02 - Component voice pass

- **Project:** holdspeak
- **Phase:** 12
- **Status:** backlog
- **Depends on:** HS-12-01
- **Unblocks:** HS-12-03

## Problem

The component library was built against soft modern surfaces
(rounded corners, elevation shadows, accent-soft backgrounds).
Once HS-12-01 swaps the token values, the components need a
voice pass: hard 1 px borders, no shadows, hard-edged pills, flat
buttons that read as *gadgets* without going full inset/outset
bevel.

## Scope

- **In:**
  - `Button.astro` — flat-with-hard-border treatment; `--primary`
    uses orange accent on white surface; `--danger` keeps the
    Workbench red; `--ghost` is text-only with hover underline.
  - `Pill.astro` — square corners, hard border per tone, no
    accent-soft fills.
  - `Panel.astro` — hairline border, no shadow, white surface,
    panel header reads as a divider line not a stripe.
  - `Toolbar.astro`, `ListRow.astro`, `EmptyState.astro`,
    `InlineMessage.astro`, `LocalPill.astro` — same voice pass.
  - `CommandPreview.astro` — hard frame, monospace stays, copy
    button restyled as a small gadget.
  - `ConfirmDialog.astro` — hard border, no rounded corners, no
    shadow; close behaviour and focus management unchanged.
  - `TopNav.astro` — fix the active-route underline once more
    against the new palette; ensure brand mark renders at the
    new pixel-font size.
  - `AppMark.astro` / `HoldMark.astro` — review against the new
    palette; AppMark may need a 2-tone simplification to read
    well at 16/24 px.
- **Out:**
  - New components.
  - Per-route page CSS (HS-12-03).
  - Stripe title bar pattern; full inset/outset gadget bevels.

## Acceptance Criteria

- [ ] Every component has zero rounded corners (or a documented
  exception).
- [ ] No `box-shadow` values referencing legacy `--elev-*`
  tokens remain in component CSS.
- [ ] `/design/components` gallery renders every component +
  state legibly.
- [ ] The destructive-action red still meets AA contrast against
  the new white surface.
- [ ] Pill tones stay distinguishable when stacked in a Toolbar.

## Test Plan

- Component gallery at `/design/components` — eyeball every
  state.
- Keyboard-only walk through ConfirmDialog stays intact.
- Existing motion + a11y guarantees from HS-10-12 remain.

## Notes

The voice pass is the *hardest* part of phase 12 — it's where the
Workbench feel either lands or doesn't. If a component clearly
fights density on the dashboard or `/activity`, prefer
"slightly less Workbench" over "less legible". The phase brief
explicitly allows skipping authentic Workbench grammar that
fights dense data.

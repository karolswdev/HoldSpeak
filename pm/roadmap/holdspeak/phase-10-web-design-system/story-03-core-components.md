# HS-10-03 - Core component library

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** HS-10-01, HS-10-02
- **Unblocks:** HS-10-04, HS-10-06, HS-10-07, HS-10-08, HS-10-09
- **Owner:** unassigned

## Problem

`designer-handoff/style-handoff.md` enumerates the component families
that need to exist (Button, Pill, Panel, Toolbar, ListRow, EmptyState,
InlineMessage). Today these are ad-hoc inline-styled `<div>`s repeated
across five files with subtle variation. The route-rebuild stories
cannot proceed until this library exists.

## Scope

- **In:**
  - `web/src/components/` Astro components for:
    - `Button.astro` — `variant=primary|secondary|danger|ghost`,
      `loading`, `disabled`, `iconOnly`, `size=sm|md`.
    - `Pill.astro` — `tone=neutral|info|success|warn|danger|local`,
      with optional leading dot/icon.
    - `Panel.astro` — header slot, toolbar slot, body slot, footer slot;
      `density=comfortable|dense`.
    - `Toolbar.astro` — horizontal action group with overflow rules.
    - `ListRow.astro` — primary line + secondary line + meta + actions
      slot; hover/focus/selected states.
    - `EmptyState.astro` — icon, title, description, single primary
      action slot.
    - `InlineMessage.astro` — `tone=info|success|warn|danger`, dismissible
      optional.
  - One "components gallery" route (`/_design/components`) used only in
    dev that renders every component in every state for visual review.
  - All components consume tokens from HS-10-02 — no raw hex, no raw
    pixel values for color/space/radius.
  - Visible focus rings on every interactive component.
- **Out:**
  - Form input components beyond Button (text input, select, textarea
    are scoped into HS-10-09 alongside the dictation editor work).
  - `CommandPreview` (HS-10-10).
  - Confirmation/destructive UI (HS-10-11).
  - `TopNav` (HS-10-04).

## Acceptance Criteria

- [x] Every listed component exists in `web/src/components/` and is
  rendered in the components gallery in all documented states.
- [x] No component file references a literal color, radius, or motion
  duration; all reference tokens.
- [x] Loading/disabled states on Button block double-submit (the click
  handler is no-op when `loading || disabled`).
- [x] Keyboard focus rings are visible on Button, Pill (when
  interactive), ListRow, and EmptyState's action.
- [x] Tab order across the gallery is sensible (no negative tabindex
  abuse).

## Test Plan

- Manual gallery walk in two viewports (desktop ~1440px, narrow ~420px)
  with screenshots stored in `evidence-story-03.md`.
- Keyboard-only navigation pass of the gallery; recorded as a step list
  in evidence.
- `npm run build` emits the gallery; FastAPI serves it; no console
  errors.

## Notes

This story is sized large on purpose — splitting it would force
inconsistency between, say, Button and ListRow built weeks apart. Treat
the gallery route as the durable artifact: it stays in the repo as
living documentation.

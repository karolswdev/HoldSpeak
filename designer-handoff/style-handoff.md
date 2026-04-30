# Style Handoff

## Current Visual Language

Phase 10 landed a real design system. The runtime now reads as a
quiet local workbench. Every visual value flows from
`web/src/styles/tokens.css`.

- **Surfaces**: a near-black canvas (`--canvas`), raised panel layer
  (`--canvas-raised`), and an "elevated" tier for modals and toasts.
- **Borders**: 1 px hairline (`--line`) for default panel edges, a
  stronger weight (`--line-strong`) for separators that need to read
  at a glance, and a third (`--line-emphasis`) reserved for hover.
- **Text**: high-contrast `--text` for body, muted secondary
  `--text-muted` for dense metadata, and a single `--accent`
  (HoldSpeak cyan) for primary actions, status, and identity.
- **Tones**: cyan accent, success green, warn amber, danger red,
  and a dedicated `local` token for the "stays on this machine"
  privacy signal.
- **Shape**: a 6-step radius scale (`--radius-1`..`--radius-4` plus
  `--radius-pill`); list rows + buttons land on `--radius-2`,
  panels on `--radius-3`, hero on `--radius-4`.
- **Type**: Sora UI (400/500/600), JetBrains Mono for monospace.
  Sizes drive off `--font-size-{xs,sm,md,lg,xl,2xl,3xl}`; line
  heights are `normal` and `relaxed`.
- **Motion**: three duration tokens (`--duration-short` 120 ms,
  `--duration-medium` 220 ms, `--duration-long` 360 ms) with three
  easing curves (`standard`, `emphasized`, `decelerate`). All of
  them collapse to `0ms` under
  `prefers-reduced-motion: reduce` via a single global rule.
- **Identity**: the `AppMark` keycap glyph (24 px) is the canonical
  brand mark; `HoldMark` is the larger hold-to-talk motif used on
  empty states. Both render `currentColor` and respect aria.

## Desired Direction

Holding (still): a private local workbench — calm, precise, fast
to scan, technical without being chaotic, and confident around
destructive actions.

Avoid (still):

- Marketing-style hero layouts.
- Decorative gradients or large illustration cards.
- Nested cards inside cards.
- Overly large type inside dense tool panels.

## Component Library

The full inventory lives in `web/src/components/` and renders end-
to-end in `/design/components`. The phase-10 set is:

| Component | Purpose |
|---|---|
| `Button` | primary / secondary / danger / ghost × sm/md, with loading + disabled. |
| `Pill` | tone-driven status pills, optional dot, optional `interactive`. |
| `Panel` | the canonical container — header, toolbar, body, footer slots. |
| `Toolbar` | right-aligned action strip used inside panel headers. |
| `ListRow` | dense row primitive for record / candidate / job lists. |
| `EmptyState` | "nothing here yet" frame with a single useful next action. |
| `InlineMessage` | success / warn / danger / info banners inside panels. |
| `TopNav` | unified app shell nav; route identity + status slot + overflow. |
| `AppMark` / `HoldMark` | identity glyphs. |
| `LocalPill` | the canonical "local-only" privacy signal. |
| `CommandPreview` | shell command / dry-run trace renderer with copy. |
| `ConfirmDialog` | destructive-action confirmation; one `<dialog>` per page mounted by `AppLayout`. |

## Accessibility And Responsiveness

- Visible focus ring on every interactive element via the global
  `:focus-visible` rule (`--focus-outline-width` solid `--accent`
  with `--focus-outline-offset`).
- All decorative SVGs declare `aria-hidden="true"`; identity marks
  expose `role="img"` + `aria-label` when consumers pass one.
- Modals (`ConfirmDialog`, bookmark, metadata) trap focus, default
  to Cancel, and restore focus to the originating element on close.
- Keyboard-only walks of the four canonical workflows complete
  without dead-ends (see HS-10-12 evidence).
- Mobile (`/activity` mobile shot, 390 × 1200) keeps the dense
  list layout legible and avoids horizontal overflow.

## Resolved Style Questions

- **Unified dark theme, or light + dark tokens now?** — Stays
  dark-only for the v0.2.0 surface. A light-theme token map is
  deferred until there's a real user ask; the token layer is
  structured so a sibling `:root[data-theme="light"]` block is the
  drop-in extension point.
- **Should activity, history, and dictation share one global nav?**
  — Yes. `TopNav.astro` mounted by `AppLayout.astro` is the only
  nav surface; the legacy hand-rolled per-page nav is gone.
- **Visual grammar for "local-only" status across the product?**
  — `LocalPill.astro` is the canonical signal. It carries the
  `local` tone, a leading dot, and a tooltip with the canonical
  privacy copy. It appears in the `TopNav` status slot and inside
  any `ConfirmDialog` whose action is local-data-only.
- **How should connector command previews be displayed so they
  are inspectable but not intimidating?** — `CommandPreview.astro`
  (HS-10-10) renders a `<figure>` with three tones (`neutral`,
  `warn`, `danger`), a left-edge tone accent (no surface tint),
  and an in-component copy button. Long arguments wrap at
  character boundaries, never horizontal-scroll.
- **How should meeting candidate state be visualized across
  candidate, meeting, and history surfaces?** — Reuses the `Pill`
  tone palette: `info` for "candidate (preview)", `success` for
  "saved", `warn` for "needs review", `neutral` for "dismissed".
  This is consistent with the rest of the system and keeps
  candidate state legible in any context.

## Deferred Style Questions

- A light-theme token map (see above).
- Per-route hero illustrations beyond `HoldMark` — only revisit if
  a route's empty state genuinely needs a different metaphor.
- Page-level transitions / route animations — explicitly out of
  scope per HS-10-12 ("conflicts with the calm and precise
  direction").

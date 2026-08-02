# Phase 110 - The Cohesion

**Status:** done (7/7). Chartered, rescoped, and shipped 2026-07-31.
The material model pivot is in: opaque surfaces, beveled depth, 2px
corners, mono chrome font, solid bars, rectangular gadgets, no
`backdrop-filter` on any desk chrome. The owner accepted it as the
foundation with a strict condition: a fast-follow Phase 111 must
immediately refine every UI surface diligently — dropdowns, list
views, window interiors, configuration panes — to full Signal
Workbench coherence.

**Last updated:** 2026-07-31 (CLOSED — owner accepted the foundation;
Phase 111 chartered as the fast-follow surface refinement pass.)

## Why this phase exists

The Desk has the bones of an OS — the icon cell contract, the drawer
metaphor, the verb registry, the kernel spine — but the skin is macOS
Ventura. Every material decision is Apple 2020s:

- **Frosted glass** (`backdrop-filter: blur(26px) saturate(160%)`) on
  windows, dock, and menu bar
- **Traffic-light circles** (`#ff5f56` / `#ffbd2e` / `#27c93f`) as
  window controls — the exact macOS palette
- **18px corner radius** on every window
- **Gaussian drop shadows** for depth (68px ambient blur)
- **Pill-shaped chips** with 999px radius
- **Spring entrance animations** on windows
- **Animated gradient backdrop** with pulsing glows (already killed)

The pixel-art icon family (cassette, tome, automaton, drawer) is the
only element that speaks Workbench. Everything around it negates the
character. The owner's verdict: "you just reskinned the whole thing
but forgot all of those windows have insides."

## The thesis: Signal Workbench

Replace the macOS material model with the structural grammar of
Workbench 2.0, rendered for a dark, dense, 2000s-techy aesthetic:

| macOS (what we have) | Signal Workbench (what we need) |
|---|---|
| `backdrop-filter: blur(26px)` | Opaque solid surface fills |
| Traffic-light circles | Rectangular beveled gadget buttons |
| 18px `border-radius` | 2px everywhere, 0px on gadgets |
| Gaussian drop shadows | Two-tone bevels (light top-left, dark bottom-right) |
| Pill-shaped chips | Rectangular etched chips |
| `Space Grotesk` / `Inter` | `JetBrains Mono` promoted to chrome font |
| Frosted floating dock | Solid opaque taskbar strip |
| Gradient backdrop + glow | Flat dark floor, subtle crosshatch tile |

The **bevel** is the key grammar: Workbench communicated depth with
1px two-tone borders. In a dark theme:
- Raised: `inset 1px 1px 0 rgba(255,255,255,0.14), inset -1px -1px 0 rgba(0,0,0,0.40)`
- Sunken: the inverse
- Flat: 1px solid border only

## Constitutional grounding

- **Article VII** — chrome is quiet. Frosted glass, spring animations,
  and animated glows are not quiet. Opaque surfaces with beveled edges
  are.
- **Article VIII** — native-grade craft. The Desk must feel like an OS.
  The macOS material model makes it feel like a macOS *app*, not like
  its own OS.
- **Article I / II** — the Desk is the operating surface. The surface
  should have its own identity, not borrow Apple's.

## Honest limits

**This is a visual/material pass, not a feature phase.** The kernel,
consent spine, verb registry, window physics (drag, resize, snap,
expose, minimize) — all unchanged in behavior. The z-ladder, the
hit-test model, the store — unchanged. What changes is what every
surface LOOKS like.

**The interior structure is mostly sound.** The agent audit found that
most window interiors (dense rows, grouped-inset settings, hairline
separators, the well/rail distinction) already read as OS-native. The
main interior fixes are killing the aerogel blur, making windows
opaque, and tightening typography.

## Stories

| # | Story | Depends on | Status |
|---|-------|-----------|--------|
| 01 | [The token pivot](./story-01-token-pivot.md) | — | done |
| 02 | [The window material](./story-02-window-material.md) | 01 | done |
| 03 | [The bars](./story-03-the-bars.md) | 01 | done |
| 04 | [The interior pass](./story-04-interior-pass.md) | 02 | done |
| 05 | [The backdrop and sprites](./story-05-backdrop-sprites.md) | 01 | done |
| 06 | [The typography pivot](./story-06-typography.md) | 01 | done |
| 07 | [The cohesion walk](./story-07-cohesion-walk.md) | 01–06 | done |

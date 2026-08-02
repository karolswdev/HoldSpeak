# HS-110-02 - The window material

- **Project:** holdspeak
- **Phase:** 110
- **Status:** backlog
- **Depends on:** HS-110-01
- **Unblocks:** HS-110-04, HS-110-07
- **Owner:** unassigned

## The thesis (the bar)

Windows are macOS Ventura: frosted glass at 58% opacity, 18px corners,
traffic-light circles, Gaussian shadows, spring entrance animations.
The bar: **opaque windows with beveled chrome, rectangular gadgets,
2px corners, and honest depth from borders — not blur.**

## Recipe

1. **Window body.** `DeskWindowFrame` body fill becomes solid
   `--surface-1` (opaque, no `backdrop-filter`). Border: `1px solid
   var(--border)`. Corner radius: `2px`. No glass-edge rim. No
   drop shadow — depth comes from the bevel on the title bar and the
   `--border` / `--border-strong` distinction (front vs rest).

2. **Title bar.** 32px tall (down from 40). `--surface-2` fill with
   the raised bevel (`inset 1px 1px 0 var(--bevel-light), inset
   -1px -1px 0 var(--bevel-dark)`). The front window's title bar
   gets `--surface-3` and a 1px `--accent` bottom edge. Title:
   left-aligned, `JetBrains Mono 12px/500`. Window icon: 16x16
   pixel sprite before the title.

3. **Gadgets.** Replace the three CSS traffic-light circles with
   rectangular gadget buttons (16x14px). CSS-rendered (not pixel-art
   sprites — the first attempt proved 16px generated sprites are
   unreadable). Each gadget: `--surface-2` fill, raised bevel, 0px
   radius. Glyphs: simple 1px-stroke SVG marks (×, −, □) in
   `--text-muted`, brightened to `--text` on hover. Close gadget on
   front window: dim red fill (`#3a1c1c`) instead of a traffic light.
   No cluster-hover-to-reveal — gadgets are always visible.

4. **Entrance/exit.** Kill the spring slide-in. Windows appear with a
   fast fade (80ms) or instant. Minimize fly-to-chip can stay (it's
   functional, not decorative).

5. **Focus ring.** The front window wears `--border-strong`; rest
   windows wear `--border`. No accent-mixed keyline ring. No shadow
   difference.

## Test plan

- Windows render with opaque solid fill, no blur behind them.
- 2px corners everywhere.
- Gadgets are rectangular, always visible, with × / − / □ marks.
- Front window distinguished by border and title bar color, not shadow.
- Drag, resize, snap, expose, minimize/maximize — all unchanged.
- Screenshot at 1440 and 393 with a window open over desk objects:
  the window reads as a solid surface sitting ON the desk, not
  floating in glass above it.

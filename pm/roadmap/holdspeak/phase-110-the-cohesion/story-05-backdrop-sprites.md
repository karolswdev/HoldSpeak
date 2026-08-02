# HS-110-05 - The backdrop and sprites

- **Project:** holdspeak
- **Phase:** 110
- **Status:** backlog
- **Depends on:** HS-110-01
- **Unblocks:** HS-110-07
- **Owner:** unassigned

## The thesis (the bar)

The first attempt's backdrop tile was garish — a quilted-cushion
pattern that competed with the objects on the desk. The Speak dock
sprite was unreadable. The bar: **a backdrop so subtle it disappears
under objects, and sprites iterated on the real populated desk.**

## Recipe — the backdrop

1. **The floor.** A flat solid color: `--bg` (`#0c0d11`). No gradient.

2. **The crosshatch.** A 4x4px or 8x8px repeating CSS pattern
   (generated in code, not via Pixellab) at ~3% white opacity on the
   floor. The pattern should be a fine diagonal crosshatch or a dot
   grid — visible on an empty desk, invisible under a populated one.
   Implementation: a CSS `background-image` using a tiny inline
   data-URI or a `repeating-linear-gradient` pair.

   Example (diagonal crosshatch):
   ```css
   background:
     repeating-linear-gradient(
       45deg, transparent, transparent 3px,
       rgba(255,255,255,0.025) 3px, rgba(255,255,255,0.025) 4px
     ),
     repeating-linear-gradient(
       -45deg, transparent, transparent 3px,
       rgba(255,255,255,0.025) 3px, rgba(255,255,255,0.025) 4px
     );
   ```

3. **No animation.** The backdrop is static. No pulse, no glow.

## Recipe — sprite iteration

1. **The Speak mic.** Regenerate via Pixellab Pro at 32x32. Review
   ALL 64 candidates. Pick by placing each on the real populated desk
   at 24px rendering size and checking: does the silhouette read as
   "microphone" at a glance? Does the palette match the cassette
   family? Reject mushy outlines.

2. **The window gadgets.** The first attempt's 16px pixel-art gadgets
   were unreadable. Story 02 switches to CSS-rendered rectangular
   gadgets instead. The sprites are retired.

3. **Overview and reset buttons.** The `⊞` and `⟲` Unicode glyphs
   on the dock's utility buttons should become small pixel sprites
   or clean SVG marks matching the gadget style.

4. **Sprite state variants.** Run `scripts/gen-sprite-states.py` on
   any new or changed sprites to generate `_sel` and `_stale`
   variants.

## Test plan

- Empty desk: the crosshatch pattern is barely visible — a texture,
  not a feature.
- Populated desk (≥20 objects): the pattern disappears under the
  icons and labels.
- The Speak dock sprite reads as a microphone at 24px.
- No Pixellab-generated tile artifact (the quilted cushion is gone).

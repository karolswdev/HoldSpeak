# HS-110-01 - The token pivot

- **Project:** holdspeak
- **Phase:** 110
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-110-02, HS-110-03, HS-110-04, HS-110-05, HS-110-06, HS-110-07
- **Owner:** unassigned

## The thesis (the bar)

The design token system defines a macOS material language: translucent
washes for borders, Gaussian blur for elevation, 18px corner radius.
The bar: **new tokens for the Workbench depth grammar — bevels, etched
borders, solid surfaces, 2px corners — as the foundation everything
else builds on.**

## Recipe

1. **Bevel primitives.** Add to `design-tokens.json` layer 2 (semantic):
   - `--bevel-light: rgba(255,255,255,0.14)` — top-left highlight on
     raised surfaces
   - `--bevel-dark: rgba(0,0,0,0.40)` — bottom-right shadow on raised
   - `--etch-light: rgba(255,255,255,0.07)` — bottom-right highlight
     on sunken surfaces
   - `--etch-dark: rgba(0,0,0,0.30)` — top-left shadow on sunken
   - Utility classes or mixins: `.raised`, `.sunken`, `.flat`

2. **Solid borders.** Replace the white-wash border system:
   - `--border: #2a2e3e` — solid 1px, not alpha
   - `--border-strong: #363b50` — focused / front-window
   - Keep `--border-subtle` for hairline interior dividers

3. **Corner radius.** Set `--radius-sm` and `--radius-md` to `2px`.
   Kill `--radius-lg` (18px) and `--radius-pill` (999px) from
   component tokens. Gadgets and dock chips: 0px.

4. **Elevation.** Replace the 5-level Gaussian shadow system with
   bevel declarations. The front window is distinguished by
   `--border-strong`, not by a 68px ambient blur.

5. **Window material tokens.** Replace:
   - `--desk-window-fill: rgba(21,17,29,0.58)` → a solid
     `--surface-1` (`#151720`)
   - `--desk-window-head-fill` → `--surface-2` (`#1e2130`)
   - `--desk-window-radius: 18px` → `2px`
   - Remove `--desk-aerogel-blur` (no more backdrop-filter)

6. **Regenerate.** Run the token generation script to update
   `tokens.css` and `tokens.gen.ts`.

## What does NOT change

- The ink ramp (`#0e0f13` → `#242833`) — it works.
- The accent orange (`#ff6b35`) — it's the Signal identity.
- The status colors (ok/warn/danger/info) — they work.
- The spacing scale — it works.
- The glow pool per icon kind — it works.

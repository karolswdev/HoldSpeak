# HS-110-04 - The interior pass

- **Project:** holdspeak
- **Phase:** 110
- **Status:** backlog
- **Depends on:** HS-110-02
- **Unblocks:** HS-110-07
- **Owner:** unassigned

## The thesis (the bar)

The window interiors are the part the owner said was missing from the
first attempt. The agent audit found most interiors already read as
OS-native (dense rows, grouped-inset settings, hairline separators).
The bar: **kill the glass remnants inside windows and tighten
everything to match the opaque, beveled exterior.**

## Recipe

1. **Aerogel receipts.** Kill `backdrop-filter: blur(18px)
   saturate(140%)` on `.surface-aerogel`. Replace with: solid
   `--surface-2` fill, 1px `--border` all around, 2px radius.
   No drop shadow. The receipt is a bordered inset, not a floating
   frosted card.

2. **Surface groups.** Corner radius from 10px to 2px. Border stays
   as-is (1px solid). The rail fill (`rgba(255,255,255,0.05)`)
   becomes a solid `--surface-2` value — no transparency.

3. **Surface code blocks.** Currently a flat `--wash-1` background.
   Change to the sunken bevel treatment (dark inset, like a terminal
   well): `--surface-1` fill with `inset 1px 1px 0 var(--etch-dark),
   inset -1px -1px 0 var(--etch-light)`.

4. **Scrollbars.** Currently 6px overlay pills. Change to 8px always-
   visible scrollbars: `--surface-2` track, `rgba(255,255,255,0.18)`
   thumb, 2px radius. Workbench scrollbars were always present — it
   communicates content length honestly.

5. **Row hover.** Currently 6px border-radius on the hover highlight.
   Change to 0px — a full-width highlight band, not a rounded chip.

6. **Section labels.** Currently `Inter 11px/600 uppercase`. Change
   to `JetBrains Mono 10px/600 uppercase` — the system-label style
   from the typography pivot.

7. **Library tiles and switchboard bays.** Corner radius from 12px
   to 2px. The card-grid layout stays (it's functional), but the
   rounded-card feel flattens to rectangular etched containers.

## Test plan

- Open a window with aerogel receipts (e.g., a meeting with
  artifacts): receipts are solid bordered insets, no frosted blur.
- Open Settings: grouped insets have 2px corners, not 10px.
- Scroll a long window: scrollbar is always visible, 8px wide.
- Section labels render in JetBrains Mono.
- No `backdrop-filter` inside any window content.

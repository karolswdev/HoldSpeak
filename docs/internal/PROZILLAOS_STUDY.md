# The ProzillaOS study (HS-99)

**Provenance:** [ProzillaOS](https://github.com/prozilla-os/ProzillaOS),
MIT License, © 2023 Sieben De Beule. Studied 2026-07-18 at the owner's
direction ("see what we can borrow, what we can embrace") after the
Phase 98 verdict. We borrow *techniques* (and adapt small CSS
patterns); the Signal grammar stays canon (Article X records the
deviation model, as with the Phase 96 skills). Where code-level
patterns are adapted, this file is the attribution record.

Three source sweeps: the window system
(`packages/core/src/components/windows`), the skin/control system
(`packages/skins`, `packages/core/src/styles`), and the desktop shell
(taskbar/desktop/app framework). Verdict up front: ProzillaOS is
~150 lines of window CSS plus a small set of relentless techniques.
Its power is consistency, not machinery. Ours is the opposite failure:
strong machinery (placement, snap, per-edge resize, focus depth,
exposé — all beyond the reference) wearing no skin.

## Borrow (lands in this phase)

| Technique | What it is | Lands in |
|---|---|---|
| Tonal depth ladder | 5 background steps; head/toolbar/rail/well/body separate by TONE, not borders — this is most of "solid object" | HS-99-01 tokens; 02/06 apply |
| The title bar is a bar | 40px two-tone head, full-height `aspect-ratio: 1` buttons flush to the edge, hover color as a CSS **variable override**, close remaps it to red, `focus-visible` ≡ hover for free | HS-99-02 |
| Square corners on maximize | `border-radius: 0` only when maximized — reads as "docked to the frame" | HS-99-02 |
| Head context menu | right-click on the bar: Minimize/Maximize/Close | HS-99-02 (menu primitive: 04) |
| Custom scrollbars everywhere | thin pill thumb (`border: transparent` + `background-clip: padding-box`), transparent track, token color; Firefox `scrollbar-width/color` | HS-99-04 |
| Skinned selects | flat fill, no border, radius, styled `<option>` inheriting colors; we go further: `appearance: none` + drawn chevron | HS-99-03 |
| Replace-not-style checkboxes | native inputs hidden or `accent-color`-driven; controls are buttons + icons | HS-99-03 |
| One menu vocabulary | a single Actions/menu primitive reused by desktop, head, and taskbar menus; per-corner radius squares the anchor corner | HS-99-04 |
| Frosted two-layer bars | tint pseudo-layer (opacity) + separate `backdrop-filter` blur layer | HS-99-05 |
| Running-app underline | `::after` pill under running chips, grows on hover; the taskbar carries system state | HS-99-05 |
| Hover icon zoom + halo | chip icons scale ~125%; icon buttons get a circular `::after` halo | HS-99-05/06 |
| Tint math | hover = ~20% `color-mix` tint, selected = ~40% — formulas, not guesses | HS-99-06 (via existing wash/accent-tint tokens) |
| Easing family | quart `cubic-bezier(.76,0,.24,1)` default, expo/back variants; short/medium/long durations | HS-99-01 tokens |
| Interior archetypes | Settings = left rail + panel (active row one tonal step up); explorer = toolbar / sidebar / grid / status bar | HS-99-06 |
| Three-var button theming | `--text/--normal/--hover-color` overridden by consumers, one base rule | already close to ours; adopted where chrome is rebuilt |

## Embrace (we already do this — keep, do not regress)

- **Focus chrome**: front window keyline + elevation split (ProzillaOS
  has NO focus styling; the taskbar carries it — ours is stronger).
- **Placement/snap/per-edge resize/exposé/MRU**: the reference uses
  `react-draggable` + CSS `resize: both` (one corner grip, no
  tiling). Our Phase 97 physics floors stay.
- **Directional consistency of light**: theirs is top-right; ours is
  straight-down and already consistent family-wide. Keep ours.
- **Reduced motion**: absent in the reference; ours is a floor.
- **Held-opacity pop animation**: their open holds opacity 0 through
  25% of the timeline so motion reads before content. Our spring-in
  is a floor; the easing family lands so future motion speaks it.
- **Wallpaper/desktop icons**: our GL world IS the desktop.

## Skip (recorded, with reasons)

- **Skin/theme switching registry** (Skin class, per-app overrides):
  one skin done well is the Phase 96 decision. The public-classname
  seam (`ProzillaOS-*` stable classes for skin CSS) is the rider to
  copy IF theming ever lands.
- **Custom select popup component**: browsers cap `<option>` styling;
  we skin the native select first. A full custom dropdown is the
  rider if the skinned native still offends.
- **`resize: both` native grip / react-draggable**: strictly worse
  than our frame.
- **`pointer-events: none` root trick, boot screen, dock badges,
  nested submenus**: no current need; riders.

## The numbers worth keeping (from the source)

- Header: `2.5rem`; buttons full-height `aspect-ratio: 1`, hover
  `rgba(255,255,255,5%)`, close `--red-0` via variable override.
- Window: radius 6px, `min 300×150`; maximized reserves the taskbar
  and squares corners.
- Motion: 75/250/400ms; quart easing; open = `translateY(25vh)
  scale(0)` with opacity held to 25%.
- Scrollbar: `width 1.25rem`, pill radius, `border: 5px transparent`
  + `background-clip: padding-box`, thumb = 25% mix of surface.
- Taskbar: `3rem`, tint at 0.75 over `blur(1rem)`; underline
  `0.15rem` × 90% (100% on hover); icon hover scale 125%.
- List tints: hover 20% mix, selected 40% mix.

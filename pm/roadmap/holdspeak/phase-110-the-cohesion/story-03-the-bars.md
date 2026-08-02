# HS-110-03 - The bars

- **Project:** holdspeak
- **Phase:** 110
- **Status:** backlog
- **Depends on:** HS-110-01
- **Unblocks:** HS-110-07
- **Owner:** unassigned

## The thesis (the bar)

The dock is a macOS-style frosted-glass floating pill. The menu bar is
a frosted-glass overlay. The bar: **both become solid, opaque,
beveled strips — a taskbar and a system bar, not glass islands.**

## Recipe — the dock (taskbar)

1. **Material.** Kill the frosted-glass pill. The dock becomes a
   solid `--surface-2` strip with a raised bevel on the top edge
   only (`inset 0 1px 0 var(--bevel-light)`). 0px corner radius.
   Height: 42px.

2. **Launcher slots.** 36x36px squares with a 1px etched border
   (sunken bevel), holding a 24x24px pixel-art sprite. Labels below
   in `JetBrains Mono 10px`. The active (running) app gets a 2px
   `--accent` bottom border. The front app's slot gets `--surface-3`
   fill.

3. **Pixel-art sprites.** The cassette (Meetings), automaton (Agents),
   and wrench (Settings) sprites from the first attempt are passable.
   The Speak mic needs regeneration with more careful candidate
   selection — iterate through candidates on the REAL desk before
   picking.

4. **Window chips.** Open-window chips are rectangular (no pills),
   0px radius, etched background, mono text (`JetBrains Mono 10px`).
   The front chip gets `--accent-tint` fill. Close button: a simple
   `×` in `--text-muted`.

5. **RecordOrb.** Keep the pixel-art orb from the first attempt — it
   looks good. It sits in the dock as the one deliberately warm
   element. The CSS glow stays as a drop-shadow on the sprite.

6. **Separators.** The 1px vertical separator between app slots and
   window chips stays.

7. **Magnification swell.** Already killed in the first attempt.
   Stays dead.

## Recipe — the menu bar (system bar)

1. **Material.** Kill the frosted-glass overlay. Solid `--surface-2`
   fill, raised bevel on the bottom edge, full viewport width.
   Height: 28px. 0px radius.

2. **HoldSpeak mark.** The 14px pixel-art mark sprite from the first
   attempt. Followed by "HoldSpeak" in `JetBrains Mono 12px/600`.

3. **Menu items.** `JetBrains Mono 12px/500`, padding `0 10px`.
   Hover: `--accent` fill, `--bg` text (the Workbench selection-bar
   behavior — inverted highlight, not a subtle wash).

4. **Dropdown menus.** Flat `--surface-3` rectangles, 1px
   `--border`, 2px radius, no shadow, no blur. Items: 28px tall,
   same hover rule.

5. **Hub status.** The CSS dot becomes an 8px square LED: `--ok`
   fill when live, `--danger` when degraded, `--text-faint` when
   connecting. 1px darker ring. No glow, no animation.

6. **Attention bell and search.** Keep the pixel-art sprites from the
   first attempt (they looked fine at 14px).

7. **Clock.** `JetBrains Mono 12px` in `--text-muted`. Right-justified.

## Test plan

- Dock is a solid strip, not a floating pill.
- Menu bar is a solid strip, not a frosted overlay.
- Hover on menu items produces Workbench-style inverted highlight.
- No `backdrop-filter` on either bar.
- Screenshot at 1440 and 393.

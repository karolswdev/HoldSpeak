# HS-110-06 - The typography pivot

- **Project:** holdspeak
- **Phase:** 110
- **Status:** backlog
- **Depends on:** HS-110-01
- **Unblocks:** HS-110-07
- **Owner:** unassigned

## The thesis (the bar)

The current type hierarchy is 2024-startup: Space Grotesk for display,
Inter for body. It reads as a SaaS dark theme, not an OS. The bar:
**JetBrains Mono promoted to the primary chrome font — the chrome
speaks in monospace; only running prose falls back to proportional.**

## Recipe

| Role | Before | After |
|------|--------|-------|
| Title bars | Space Grotesk 15px/600 | JetBrains Mono 12px/500 |
| Dock labels | Inter 11px | JetBrains Mono 10px |
| Menu items | Inter 13px | JetBrains Mono 12px/500 |
| Section labels | Inter 11px/600 uppercase | JetBrains Mono 10px/600 uppercase |
| Window body text | Inter 13px/400 | Inter 13px/400 (unchanged) |
| Display numbers | Space Grotesk 26px/650 | Space Grotesk 22px/650 (kept, demoted) |
| Values, paths, data | JetBrains Mono 12px | JetBrains Mono 12px (unchanged) |
| Badges | Inter 11px | JetBrains Mono 10px/700 |

1. **Update the type tokens.** In `design-tokens.json`, adjust the
   component-level type scale to reference `--font-mono` for chrome
   roles.

2. **Title bars.** `DeskWindowFrame`'s `.desk-window-title` and
   `.desk-pullout-title` classes: switch to `--font-mono`, reduce
   to 12px, weight 500.

3. **Dock.** `.desk-dock-label`: switch to `--font-mono` 10px.

4. **Menu bar.** `.desk-mark`, `.desk-chrome` text, menu items: switch
   to `--font-mono` 12px/500.

5. **Section labels.** `.surface-section label`: switch to
   `--font-mono` 10px/600.

6. **Body text stays.** `Inter 13px` for running prose inside windows
   is fine — it reads well at density. The pivot is chrome, not
   content.

## Test plan

- Title bars, dock labels, menu items, section labels all render in
  JetBrains Mono.
- Running body text inside windows still renders in Inter.
- The type hierarchy reads as "developer tool OS" rather than "SaaS
  dashboard."
- No clipping or overflow from the font change (mono is wider than
  proportional at the same size — verify at 393px viewport).

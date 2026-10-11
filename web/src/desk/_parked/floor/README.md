# Parked: the Floor (PHILO-17, 2026-10-10)

Owner ruling, verbatim: "Yes, everything must become one desk."

The Screen (`ChairHome` → `screen/Screen.tsx`) is the one desk. The spatial
Floor, its desk-wide list view, its right-click menu, its empty face, its
file drop and the Chair/Floor switch are parked here, unchanged. Nothing
imports them; `tsconfig.json` and vitest exclude `_parked/`.

- `gl/WorldStage.tsx`: the spatial Floor (zones, the GL world).
- `components/DeskListView.tsx`: the desk-wide List view (`desk.toggle-view`).
- `components/EmptyDesk.tsx`: the empty Floor.
- `components/GlassDropLayer.tsx`: the Floor's file drop.
- `floorMenu.ts`: the Floor and zone right-click menus. `objectMenuEntries`
  moved live to `desk/objectMenu.ts` (the Screen's right-click).
- `chairState.ts`: the Chair/Floor switch. A saved workspace that says
  `screen: "floor"` now loads the Screen.
- `floorVerbs.ts`: `desk.toggle-view`, `desk.arrange`, `desk.new-zone`,
  `zone.focus`, cut from `verbRegistry.ts`.
- `__tests__/`: the vitest files whose subject is only the Floor.

Kept live: the zone data and the `zone_*` MCP tools; `gl/Atmosphere.tsx`
(the design preview uses it); `glassDrop.ts` (its suffix table is tested).
The GL engine under `desk/gl/` is now reached only by the design preview.

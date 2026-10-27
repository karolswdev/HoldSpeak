// W1-DOORS (atlas 2026-10-27): one source of truth for a menu's verb rows.
// The menu bar's Desk, Go and Window menus and the blank floor's right-click
// menu draw the same rows from the one verb registry (menuVerbs); a verb with
// a `submenu` rides in one submenu of that name, at the place of its first
// verb (PHILO-13-11 C1).
import { menuVerbs, offeredHere, verbLabel, type MenuId, type VerbContext } from "../verbRegistry";
import type { WorkMenuEntry } from "./DeskMenu";

export function menuVerbEntries(id: MenuId, ctx: VerbContext, out: WorkMenuEntry[] = []): WorkMenuEntry[] {
  let lastGroup: string | undefined;
  const subs = new Map<string, WorkMenuEntry[]>();
  for (const v of menuVerbs(id)) {
    if (!offeredHere(v)) continue;
    const item: WorkMenuEntry = {
      type: "item",
      id: v.id,
      label: verbLabel(v, ctx),
      glyph: v.glyph,
      keycap: v.key,
      ghost: v.ghost(ctx),
      ...(v.checked ? { checked: v.checked(ctx) } : {}),
      onSelect: () => v.run(ctx),
    };
    if (v.submenu) {
      const known = subs.get(v.submenu);
      if (known) {
        known.push(item);
        continue;
      }
      const entries: WorkMenuEntry[] = [item];
      subs.set(v.submenu, entries);
      if (out.length && v.group !== lastGroup)
        out.push({ type: "sep", id: `sep-${v.id}` });
      lastGroup = v.group;
      out.push({ type: "sub", id: `sub-${v.group ?? v.id}`, label: v.submenu, entries });
      continue;
    }
    if (out.length && v.group !== lastGroup)
      out.push({ type: "sep", id: `sep-${v.id}` });
    lastGroup = v.group;
    out.push(item);
  }
  return out;
}

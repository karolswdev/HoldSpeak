/** The right-click menu of one desk object, derived from the ONE verb
 * registry (HS-111-07); this module mints nothing. It moved out of the
 * parked floorMenu.ts (PHILO-17, one desk): the Screen uses it. */
import { menuVerbs, verbLabel, type Verb, type VerbContext } from "./verbRegistry";
import type { WorkMenuEntry } from "./components/DeskMenu";

function item(v: Verb, ctx: VerbContext): WorkMenuEntry {
  return {
    type: "item",
    id: v.id,
    label: verbLabel(v, ctx),
    glyph: v.glyph,
    keycap: v.key,
    ghost: v.ghost(ctx),
    onSelect: () => v.run(ctx),
  };
}

/** The object menu: the object.* verbs, the danger group after a separator. */
export function objectMenuEntries(target: { ref: string }): WorkMenuEntry[] {
  const ctx: VerbContext = { selectedRef: target.ref };
  const verbs = menuVerbs("object");
  const ordinary = verbs.filter((v) => v.group !== "danger");
  const danger = verbs.filter((v) => v.group === "danger");
  return [
    ...ordinary.map((v) => item(v, ctx)),
    ...(danger.length ? [{ type: "sep" as const, id: "object.danger-sep" }] : []),
    ...danger.map((v) => item(v, ctx)),
  ];
}

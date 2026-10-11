/** The right-click menu of one desk object, derived from the ONE verb
 * registry (HS-111-07); this module mints nothing. It moved out of the
 * parked floorMenu.ts (PHILO-17, one desk): the Screen uses it. */
import { menuVerbs, verbLabel, type Verb, type VerbContext } from "./verbRegistry";
import type { WorkMenuEntry } from "./components/DeskMenu";
import { objectByRef } from "./world";
import { useDesk } from "./store";

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

/** PHILO-17 (owner 2026-10-10, "Yes, everything must become one desk"): the
 * object a pullout window shows (`pullout:<ref>`), when the desk knows it.
 * Agents, workflows, Knowledge and Sequences are not on the desk, so their
 * windows carry their object verbs (Delete through the one receipt). */
export function windowObjectRef(winId: string | null): string | null {
  if (!winId || !winId.startsWith("pullout:")) return null;
  const ref = winId.slice("pullout:".length);
  return objectByRef(useDesk.getState().items, ref) ? ref : null;
}

/** The window menu's `Object ▸`: the object verbs of the window's object.
 * Delete closes the window first, so its receipt on the desk is in view. */
export function windowObjectEntry(winId: string | null, closeWindow: () => void): WorkMenuEntry | null {
  const ref = windowObjectRef(winId);
  if (!ref) return null;
  const entries = objectMenuEntries({ ref }).map((e) =>
    e.type === "item" && e.id === "object.delete" && !e.ghost
      ? { ...e, onSelect: () => { closeWindow(); e.onSelect(); } }
      : e,
  );
  return { type: "sub", id: "window-object", label: "Object", entries };
}

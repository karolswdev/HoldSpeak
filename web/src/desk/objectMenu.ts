/** The right-click menu of one desk object, derived from the ONE verb
 * registry (HS-111-07); this module mints nothing. It moved out of the
 * parked floorMenu.ts (PHILO-17, one desk): the Screen uses it. */
import { menuVerbs, verbLabel, type Verb, type VerbContext } from "./verbRegistry";
import type { WorkMenuEntry } from "./components/DeskMenu";
import { objectByRef, type WorldObject } from "./world";
import { useDesk } from "./store";
import { primitiveCan } from "../lib/primitives";
import { handKindOf } from "./agentHand";
import { deleteSeatShown } from "./deleteSeat";
import { askableKind } from "./askAbout";

/** Object menus only list verbs the selected kind can run. State conditions
 * (for example a missing delete receipt) use the registry's ghost reason;
 * kind conditions are removed from this menu so every remaining row acts. */
/** A kind's capability; a kind that is not a primitive (a person's window) has none. */
function can(kind: string, capability: Parameters<typeof primitiveCan>[1]): boolean {
  try {
    return primitiveCan(kind as WorldObject["kind"], capability);
  } catch {
    return false;
  }
}

function offeredForKind(v: Verb, kind: WorldObject["kind"] | string): boolean {
  switch (v.id) {
    case "object.open":
      return true;
    case "object.file":
      return kind !== "directory";
    case "object.draft-update":
      return kind === "project";
    // Betterment Q5: Ask about this, on every object he can ask about.
    case "object.ask-about":
      return askableKind(kind);
    case "object.hand-to-agent":
      return can(kind, "hand") && handKindOf(kind as WorldObject["kind"]) !== null;
    case "object.edit":
      return can(kind, "edit");
    case "object.rename":
      return kind !== "directory" && can(kind, "rename");
    case "object.duplicate":
      return can(kind, "duplicate");
    case "object.delete":
      return can(kind, "delete") && deleteSeatShown();
    case "object.archive":
      return kind === "project" && can(kind, "archive");
    default:
      return true;
  }
}

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

/** The object menu: the object.* verbs, the danger group after a separator.
 *
 * Betterment Q5: a row that does not apply is not shown: no greyed row with
 * its excuse. A ref the desk does not hold as an item (a person's window, an
 * older meeting) offers only the verbs that work without one. */
export function objectMenuEntries(target: { ref: string }): WorkMenuEntry[] {
  const ctx: VerbContext = { selectedRef: target.ref };
  const verbs = menuVerbs("object");
  const object = objectByRef(useDesk.getState().items, target.ref);
  const kind = object?.kind ?? target.ref.split(":", 1)[0];
  const offered = verbs
    .filter((v) => offeredForKind(v, kind))
    .filter((v) => !v.ghost(ctx));
  const ordinary = offered.filter((v) => v.group !== "danger");
  const danger = offered.filter((v) => v.group === "danger");
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
  if (!winId) return null;
  // Betterment Q5: the Meetings window shows one meeting; its Object menu is that meeting's.
  if (winId === "surface-meetings") {
    const scope = String(useDesk.getState().windowsById?.[winId]?.scope ?? "");
    return scope.startsWith("meeting:") && scope.length > "meeting:".length ? scope : null;
  }
  if (!winId.startsWith("pullout:")) return null;
  const ref = winId.slice("pullout:".length);
  if (objectByRef(useDesk.getState().items, ref)) return ref;
  // A person is not a desk item; her window is still hers (Betterment Q5).
  if (ref.startsWith("people:") && ref !== "people:people" && !ref.startsWith("people:project:")) return ref;
  return ref.startsWith("meeting:") && ref.length > "meeting:".length ? ref : null;
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

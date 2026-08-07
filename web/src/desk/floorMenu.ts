/** HS-111-07 - the desktop right-click content (owner P0), derived
 * from the ONE verb registry; this module mints NOTHING. The floor
 * menu is: NEW > (desk.new-*, the exact createPrimitive path),
 * LAUNCH > (go.*, the exact openSurfaceOr path), then the floor
 * verbs. The object menu re-derives from object.* (its inline
 * duplicates were parallel list #4). Zone menus are the same registry
 * verbs, executed with a directory selection. */
import {
  menuVerbs,
  verbById,
  verbLabel,
  verbsFor,
  type Verb,
  type VerbContext,
} from "./verbRegistry";
import type { WorkMenuEntry } from "./components/DeskMenu";
import type { WorldMenuTarget } from "./gl/engine";

const FLOOR_CTX: VerbContext = { selectedRef: null };

function item(v: Verb, ctx: VerbContext): WorkMenuEntry {
  return {
    type: "item",
    id: v.id,
    label: verbLabel(v, ctx),
    keycap: v.key,
    ghost: v.ghost(ctx),
    onSelect: () => v.run(ctx),
  };
}

export function floorMenuEntries(): WorkMenuEntry[] {
  const floor = verbsFor("floor");
  const creates = floor.filter((v) => v.group === "new");
  const verbs = floor.filter(
    (v) => v.group === "floor" || v.group === "view",
  );
  return [
    {
      type: "sub",
      id: "floor.new",
      label: "New",
      entries: creates.map((v) => item(v, FLOOR_CTX)),
    },
    {
      type: "sub",
      id: "floor.launch",
      label: "Launch",
      entries: verbsFor("go").map((v) => item(v, FLOOR_CTX)),
    },
    { type: "sep", id: "floor.sep" },
    ...verbs.map((v) => item(v, FLOOR_CTX)),
  ];
}

export function objectMenuEntries(
  target: Extract<WorldMenuTarget, { type: "object" }>,
): WorkMenuEntry[] {
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

export function zoneMenuEntries(
  target: Extract<WorldMenuTarget, { type: "zone" }>,
  origin: { x: number; y: number },
): WorkMenuEntry[] {
  const ctx: VerbContext = {
    selectedRef: `directory:${target.id}`,
    origin,
  };
  return ["object.open", "object.info", "zone.focus", "object.rename"]
    .map((id) => verbById(id))
    .filter((verb): verb is Verb => Boolean(verb))
    .map((verb) => item(verb, ctx));
}

/** The world's pure layout math (HS-73-01) — bit-faithful ports of the
 * original desk's `worldObjects` / `worldZones` / `objUnit` (looseHome) /
 * `objGlow`, so the island lays the same desk out the same way. */
import { oh } from "./hash";
import { GLOW_POOL } from "../lib/tokens.gen";
import type { Primitive, PrimitiveKind } from "../lib/primitives";
import type { Items } from "./api";
import { qualifiedRef } from "./api";
import type { UnitPos } from "./store";

export interface WorldObject {
  kind: PrimitiveKind;
  id: string;
  title: string;
  ref: Primitive;
}

/** Kinds that have their own rendering path (zones, or never surfaced). */
const WORLD_ONLY_EXCLUDE = [
  "directory",
  "game",
  "layout",
  "intelligence",
  "people",
] as const;

/** The exhaustive iteration order — every PrimitiveKind is listed, but
 * the world_exclude kinds are placed at the end (allObjects filters
 * them out of the visual list; objectByRef still resolves them). */
const ORDER = [
  "meeting",
  "note",
  "decision",
  "kb",
  "project",
  "recipe",
  "artifact",
  "chain",
  "workflow",
  "coder",
  "roadmap",
  "story",
  "repository",
  "workbench",
  ...WORLD_ONLY_EXCLUDE,
] as const satisfies readonly PrimitiveKind[];

/** Compile-time gate (HS-117-14): a missing PrimitiveKind in ORDER is a
 * type error here. Adding a new kind to the union without listing it in
 * ORDER makes `Exclude` produce that kind, which is not assignable to
 * `never`. */
type _OrderKinds = (typeof ORDER)[number];
type _AssertOrderComplete =
  [Exclude<PrimitiveKind, _OrderKinds>] extends [never] ? true : never;
const _orderExhaustive: _AssertOrderComplete = true;
void _orderExhaustive;

/** Every primitive as a world object — including kinds the visual desk
 * renders through their own path (directories = zones, game/layout =
 * local-only). Used by objectByRef for lookup; the visual list and spatial
 * stage filter from allObjects instead. */
function _allPrimitives(items: Items): WorldObject[] {
  const out: WorldObject[] = [];
  for (const kind of ORDER) {
    for (const it of items[kind] || []) {
      const prim = it as Primitive;
      const id = String(
        prim.id || ("sessionId" in prim ? prim.sessionId : "") || ("title" in prim ? prim.title : "") || "",
      );
      out.push({
        kind,
        id,
        title: String(("title" in prim ? prim.title : "") || ("name" in prim ? prim.name : "") || id || kind),
        ref: prim,
      });
    }
  }
  return out;
}

const WORLD_EXCLUDE = new Set<PrimitiveKind>(WORLD_ONLY_EXCLUDE);

/** Every primitive as a world object, excluding kinds with their own
 * rendering path (directories are zones; game/layout are local-only).
 * A FILED object still appears (it opens from its zone); this is the
 * lookup surface for pull-outs/editors and the DeskListView. */
export function allObjects(items: Items): WorldObject[] {
  return _allPrimitives(items).filter((o) => !WORLD_EXCLUDE.has(o.kind));
}

/** Resolve a pull-out/source identity without collapsing cross-kind id
 * collisions. Searches ALL primitive kinds (including directories). */
export function objectByRef(items: Items, ref: string): WorldObject | null {
  return (
    _allPrimitives(items).find(
      (object) =>
        object.id === ref || qualifiedRef(object.kind, object.id) === ref,
    ) ?? null
  );
}

export function worldObjects(
  items: Items,
  divedZone: string | null,
): WorldObject[] {
  const out = allObjects(items);
  if (divedZone) {
    const dir = (items.directory || []).find((d) => d.id === divedZone);
    const members = new Set(dir?.memberIds || []);
    return out.filter(
      (o) => members.has(o.id) || members.has(qualifiedRef(o.kind, o.id)),
    );
  }
  // The iPad grammar (owner feedback, 2026-07-02): a filed object lives on
  // its shelf, not on the open desk — the root stage shows only unfiled
  // objects; dive to see a zone's members. (Live coder sessions are never
  // filed and always show.)
  const filed = new Set<string>();
  for (const d of items.directory || []) {
    for (const mid of d.memberIds || []) filed.add(mid);
  }
  return out.filter(
    (o) =>
      o.kind === "coder" ||
      (!filed.has(o.id) && !filed.has(qualifiedRef(o.kind, o.id))),
  );
}

export interface WorldZone {
  id: string;
  title: string;
  count: number;
  ref: Primitive;
}

export function worldZones(
  items: Items,
  divedZone: string | null,
): WorldZone[] {
  if (divedZone) return [];
  return (items.directory || []).map((d) => ({
    id: String(d.id),
    title: String(d.name || "Zone"),
    count: (d.memberIds || []).length,
    ref: d,
  }));
}

export function objGlow(kind: string): string {
  // One generated source with the CSS glow tokens (HS-96-02).
  return GLOW_POOL[kind] || GLOW_POOL.recipe;
}

/** A saved drag position, else the density-aware `looseHome` grid. */
export function objUnit(
  o: WorldObject,
  i: number,
  n: number,
  positions: Record<string, UnitPos>,
): UnitPos {
  const saved = positions[o.id];
  if (saved && typeof saved.x === "number") return saved;
  // HS-105-01: the default home is a DETERMINISTIC clean grid (the
  // Workbench Clean Up rule) — the per-object random jitter died with the
  // mascot scale: at forty objects it stacked cells and occluded labels.
  // A user drag still parks anything anywhere; only defaults grid.
  const compact = typeof window !== "undefined" && window.innerWidth <= 720;
  const cols = Math.max(
    compact ? 3 : 4,
    Math.min(compact ? 4 : 8, Math.ceil(Math.sqrt(Math.max(1, n) * 1.6))),
  );
  const rows = Math.max(1, Math.ceil(n / cols));
  const col = i % cols;
  const row = Math.floor(i / cols);
  // Default homes stay clear of the chrome band and the zone band.
  const yMin = compact ? 0.32 : 0.2;
  const xMin = compact ? 0.12 : 0.06;
  return {
    x: Math.min(
      1 - xMin,
      Math.max(xMin, xMin + (1 - 2 * xMin) * ((col + 0.5) / cols)),
    ),
    y: Math.min(
      0.9,
      Math.max(yMin, yMin + (1 - yMin - 0.1) * ((row + 0.5) / rows)),
    ),
  };
}

/** Pixel art is rendered integer-true and axis-aligned at its rest state. */
export function objMotion(_o: WorldObject) {
  return {
    phase: 0,
    tilt: 0,
    scale: 1,
  };
}

export function worldRows(n: number): number {
  const cols = Math.max(
    2,
    Math.min(6, Math.ceil(Math.sqrt(Math.max(1, n) * 1.25))),
  );
  return Math.max(1, Math.ceil(n / cols));
}

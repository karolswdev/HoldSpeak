/** The world's pure layout math (HS-73-01) — bit-faithful ports of the
 * original desk's `worldObjects` / `worldZones` / `objUnit` (looseHome) /
 * `objGlow`, so the island lays the same desk out the same way. */
import { oh } from "./hash";
import { GLOW_POOL } from "../lib/tokens.gen";
import type { DeskItem, Items, Kind } from "./api";
import { qualifiedRef } from "./api";
import type { UnitPos } from "./store";

export interface WorldObject {
  kind: Kind;
  id: string;
  title: string;
  ref: DeskItem;
}

const ORDER: Kind[] = [
  "meeting",
  "note",
  "kb",
  "recipe",
  "artifact",
  "chain",
  "workflow",
  "coder",
];

/** Every primitive as a world object, unfiltered — the lookup surface for
 * pull-outs/editors (a FILED object still opens; it just doesn't float on
 * the root stage). */
export function allObjects(items: Items): WorldObject[] {
  const out: WorldObject[] = [];
  for (const kind of ORDER) {
    for (const it of items[kind] || []) {
      const id = String(it.id || (it as any).sessionId || it.title || "");
      out.push({
        kind,
        id,
        title: String(it.title || it.name || id || kind),
        ref: it,
      });
    }
  }
  return out;
}

/** Resolve a pull-out/source identity without collapsing cross-kind id collisions. */
export function objectByRef(items: Items, ref: string): WorldObject | null {
  return (
    allObjects(items).find(
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
    const members = new Set(((dir as any)?.memberIds as string[]) || []);
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
    for (const mid of ((d as any).memberIds as string[]) || []) filed.add(mid);
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
  ref: DeskItem;
}

export function worldZones(
  items: Items,
  divedZone: string | null,
): WorldZone[] {
  if (divedZone) return [];
  return (items.directory || []).map((d) => ({
    id: String(d.id),
    title: String(d.title || d.name || "Zone"),
    count: (((d as any).memberIds as string[]) || []).length,
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
    x: Math.min(1 - xMin, Math.max(xMin, xMin + (1 - 2 * xMin) * ((col + 0.5) / cols))),
    y: Math.min(
      0.9,
      Math.max(yMin, yMin + (1 - yMin - 0.1) * ((row + 0.5) / rows)),
    ),
  };
}

/** Per-object float phase. HS-105-01: the random tilt and 0.92–1.08 scale
 * jitter died with the mascot scale — pixel art renders integer-true and
 * axis-aligned (the Workbench discipline); the positional bob keeps the
 * desk alive without blurring a single pixel. */
export function objMotion(o: WorldObject) {
  return {
    phase: -(oh(o.id) * 4.5),
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

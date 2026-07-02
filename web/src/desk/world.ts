/** The world's pure layout math (HS-73-01) — bit-faithful ports of the
 * Alpine desk's `worldObjects` / `worldZones` / `objUnit` (looseHome) /
 * `objGlow`, so the island lays the same desk out the same way. */
import { oh } from "./hash";
import type { DeskItem, Items, Kind } from "./api";
import type { UnitPos } from "./store";

export interface WorldObject {
  kind: Kind;
  id: string;
  title: string;
  ref: DeskItem;
}

const ORDER: Kind[] = [
  "meeting", "note", "kb", "agent", "artifact", "chain", "workflow", "coder",
];

export function worldObjects(items: Items, divedZone: string | null): WorldObject[] {
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
  if (divedZone) {
    const dir = (items.directory || []).find((d) => d.id === divedZone);
    const members = new Set(((dir as any)?.memberIds as string[]) || []);
    return out.filter((o) => members.has(o.id));
  }
  return out;
}

export interface WorldZone {
  id: string;
  title: string;
  count: number;
  ref: DeskItem;
}

export function worldZones(items: Items, divedZone: string | null): WorldZone[] {
  if (divedZone) return [];
  return (items.directory || []).map((d) => ({
    id: String(d.id),
    title: String(d.title || d.name || "Directory"),
    count: (((d as any).memberIds as string[]) || []).length,
    ref: d,
  }));
}

export function objGlow(kind: string): string {
  return (
    {
      meeting: "#56C7F5", note: "#34D399", kb: "#FBBF24", agent: "#FF6B35",
      artifact: "#FF9E64", chain: "#A78BFA", workflow: "#56C7F5",
      directory: "#E0A458", coder: "#FF6B35",
    } as Record<string, string>
  )[kind] || "#FF6B35";
}

/** A saved drag position, else the density-aware `looseHome` grid. */
export function objUnit(
  o: WorldObject, i: number, n: number,
  positions: Record<string, UnitPos>,
): UnitPos {
  const saved = positions[o.id];
  if (saved && typeof saved.x === "number") return saved;
  const cols = Math.max(2, Math.min(6, Math.ceil(Math.sqrt(Math.max(1, n) * 1.25))));
  const rows = Math.max(1, Math.ceil(n / cols));
  const col = i % cols;
  const row = Math.floor(i / cols);
  const jx = (oh(o.id + "x") - 0.5) * (0.7 / cols);
  const jy = (oh(o.id + "y") - 0.5) * (0.6 / rows);
  return {
    x: Math.min(0.94, Math.max(0.06, (col + 0.5) / cols + jx)),
    y: Math.min(0.94, Math.max(0.06, (row + 0.5) / rows + jy)),
  };
}

/** Per-object float phase / tilt / scale (the CSS custom props). */
export function objMotion(o: WorldObject) {
  return {
    phase: -(oh(o.id) * 4.5),
    tilt: (oh(o.id + "t") - 0.5) * 5,
    scale: 0.92 + oh(o.id + "s") * 0.16,
  };
}

export function worldRows(n: number): number {
  const cols = Math.max(2, Math.min(6, Math.ceil(Math.sqrt(Math.max(1, n) * 1.25))));
  return Math.max(1, Math.ceil(n / cols));
}

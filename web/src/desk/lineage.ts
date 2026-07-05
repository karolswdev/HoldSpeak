/** Provenance → render-ready lineage (HS-73-04) — the faithful port of the
 * Alpine desk's `resolveRef` / `lineage` (desk-app.js), tolerating the same
 * wire drift: `{source_type, source_ref}` (canonical), bare strings, and
 * `{type, ref}` / `{source}` variants. */
import type { Items, Kind } from "./api";

const RESOLVE_ORDER: Kind[] = [
  "meeting", "artifact", "note", "directory", "kb", "recipe", "chain", "workflow",
];

export interface ResolvedRef {
  kind: string;
  label: string;
  resolved: boolean;
}

export function resolveRef(items: Items, ref: string): ResolvedRef {
  if (!ref) return { kind: "", label: "", resolved: false };
  for (const kind of RESOLVE_ORDER) {
    const hit = (items[kind] || []).find((x) => x.id === ref);
    if (hit) {
      return {
        kind,
        label: String(hit.title || hit.name || hit.id),
        resolved: true,
      };
    }
  }
  // Not loaded on this surface (synced elsewhere) — show the id honestly.
  return { kind: "", label: ref, resolved: false };
}

export interface LineageEntry extends ResolvedRef {
  type: string;
  ref: string;
}

export interface Lineage {
  from: LineageEntry[];
  via: LineageEntry | null;
  any: boolean;
}

export function lineage(items: Items, sources: unknown): Lineage {
  const list = Array.isArray(sources) ? sources : [];
  const from: LineageEntry[] = [];
  let via: LineageEntry | null = null;
  for (const s of list) {
    if (!s) continue;
    const type = (typeof s === "string"
      ? "" : String((s as any).source_type || (s as any).type || "")).toLowerCase();
    const ref = typeof s === "string"
      ? s
      : String((s as any).source_ref || (s as any).ref || (s as any).source || (s as any).id || "");
    if (!ref) continue;
    const r = resolveRef(items, ref);
    const entry: LineageEntry = { type, ref, ...r };
    // "recipe" is canonical; "agent" is its pre-rename wire alias (older stored
    // rows still carry it); "ask" is the Ask atom's own via row (HSM-16-09).
    if (["recipe", "agent", "chain", "workflow", "ask"].includes(type) ||
        ["recipe", "chain", "workflow"].includes(r.kind)) {
      if (!via) via = entry;
      else from.push(entry);
    } else {
      from.push(entry);
    }
  }
  return { from, via, any: from.length > 0 || via != null };
}

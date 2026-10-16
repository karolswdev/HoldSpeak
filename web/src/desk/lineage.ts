/** Provenance → render-ready lineage (HS-73-04) — the faithful port of the
 * original desk's `resolveRef` / `lineage`, tolerating the same
 * wire drift: `{source_type, source_ref}` (canonical), bare strings, and
 * `{type, ref}` / `{source}` variants. */
import { qualifiedRef, type Items } from "./api";
import { objectByRef } from "./world";

export interface ResolvedRef {
  kind: string;
  label: string;
  resolved: boolean;
  /** The chosen object's canonical identity, independent of legacy wire IDs. */
  actionRef?: string;
}

export function resolveRef(items: Items, ref: string): ResolvedRef {
  if (!ref) return { kind: "", label: "", resolved: false };
  const colon = ref.indexOf(":");
  const identity = colon < 0 ? ref : qualifiedRef(ref.slice(0, colon), ref.slice(colon + 1));
  // A qualified identity never falls back to a bare ID from another kind.
  // The shared resolver still owns legacy bare-ID order and object names.
  const candidates = colon < 0 ? items : Object.fromEntries(Object.entries(items).map(([kind, rows]) => [
    kind, rows.filter((row: { id: string }) => qualifiedRef(kind, row.id) === identity),
  ])) as Items;
  const hit = objectByRef(candidates, identity);
  if (hit) return { kind: hit.kind, label: hit.title, resolved: true, actionRef: qualifiedRef(hit.kind, hit.id) };
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

/** Wire-format lineage source — tolerates canonical + legacy shapes. */
interface LineageSource {
  source_type?: string;
  type?: string;
  source_ref?: string;
  ref?: string;
  source?: string;
  id?: string;
}

export function lineage(items: Items, sources: unknown): Lineage {
  const list = Array.isArray(sources) ? sources : [];
  const from: LineageEntry[] = [];
  let via: LineageEntry | null = null;
  for (const s of list) {
    if (!s) continue;
    const type = (
      typeof s === "string"
        ? ""
        : String((s as LineageSource).source_type || (s as LineageSource).type || "")
    ).toLowerCase();
    const ref =
      typeof s === "string"
        ? s
        : String(
            (s as LineageSource).source_ref ||
              (s as LineageSource).ref ||
              (s as LineageSource).source ||
              (s as LineageSource).id ||
              "",
          );
    if (!ref) continue;
    const r = resolveRef(items, ref);
    const entry: LineageEntry = { type, ref, ...r };
    // "recipe" is canonical; "agent" is its pre-rename wire alias (older stored
    // rows still carry it); "ask" is the Ask atom's own via row (HSM-16-09).
    if (
      ["recipe", "agent", "chain", "workflow", "ask"].includes(type) ||
      ["recipe", "chain", "workflow"].includes(r.kind)
    ) {
      if (!via) via = entry;
      else from.push(entry);
    } else {
      from.push(entry);
    }
  }
  return { from, via, any: from.length > 0 || via != null };
}

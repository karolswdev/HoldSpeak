/** HS-105-04 — the Info contract (the tooltypes rule): a kind DECLARES
 * its Info — its footprint measure and its property keys — and the one
 * InfoWindow derives; no kind ever hand-builds its Info surface. A
 * property exists here ONLY when a real update path backs it (the gate's
 * honesty constraint: the vocabulary grows key by real key, never by
 * aspiration). Absent values render as absence, never as invention. */
import type { Items } from "./api";
import { qualifiedRef } from "./api";
import type { WorldObject } from "./world";
import { useDesk } from "./store";
import { primitiveUpdateUrl } from "./store/dataSlice";
import { productLabel } from "../lib/productLanguage";

export interface InfoProperty {
  key: string;
  /** Scoped display label (HS-130-01); falls back to the humanized key. */
  label?: string;
  /** Control shape the one surface renders. */
  type: "choice";
  /** Choice ids + labels; the current value's id, "" when absent. */
  choices(o: WorldObject, items: Items): { id: string; label: string }[];
  value(o: WorldObject): string;
  /** Commit through the object's EXISTING update path — never a new one. */
  set(o: WorldObject, value: string): Promise<void>;
}

export interface KindInfo {
  /** The kind's honest footprint line, or null (no measure declared). */
  footprint(o: WorldObject, items: Items): string | null;
  properties: InfoProperty[];
}

function chars(body: unknown): string | null {
  const s = String(body || "");
  return s ? `${s.length.toLocaleString()} characters` : null;
}

function memberCount(o: WorldObject): string | null {
  if (!("memberIds" in o.ref)) return null;
  const m = o.ref.memberIds;
  return Array.isArray(m)
    ? `${m.length} ${m.length === 1 ? "member" : "members"}`
    : null;
}

/** The declared table. Kinds not listed inherit UNIVERSAL sections only. */
export const INFO: Record<string, KindInfo> = {
  note: {
    footprint: (o) => "bodyMarkdown" in o.ref ? chars(o.ref.bodyMarkdown) : null,
    properties: [],
  },
  kb: { footprint: (o) => memberCount(o), properties: [] },
  directory: { footprint: (o) => memberCount(o), properties: [] },
  artifact: {
    footprint: (o) => "bodyMarkdown" in o.ref ? chars(o.ref.bodyMarkdown) : null,
    properties: [],
  },
  meeting: {
    footprint: (o) => {
      if (!("segmentCount" in o.ref)) return null;
      const n = Number(o.ref.segmentCount || 0);
      return n > 0 ? `${n} ${n === 1 ? "segment" : "segments"}` : null;
    },
    properties: [],
  },
  project: {
    footprint: (o) => {
      if (!("meetingCount" in o.ref)) return null;
      const n = Number(o.ref.meetingCount || 0);
      return `${n} ${n === 1 ? "meeting" : "meetings"}`;
    },
    properties: [],
  },
  recipe: {
    footprint: () => null,
    properties: [
      {
        // Default runs on: the ONE property with a real update path today
        // (the recipe PUT's profile_id, the same field the composer writes).
        // HS-130-01: unset = INHERIT (empty resolves through the global
        // default), reconciled with RecipeEditor — same label vocabulary,
        // same empty-value meaning, same token (null).
        key: "runs_on",
        label: "Default runs on",
        type: "choice",
        choices: (_o, _items) => [
          { id: "", label: "Inherit default" },
          ...useDesk.getState().profiles.map((p) => ({
            id: String(p.id),
            label: String(p.name || p.id),
          })),
        ],
        value: (o) => String("profileId" in o.ref ? o.ref.profileId || "" : ""),
        set: async (o, value) => {
          await useDesk
            .getState()
            .updatePrimitive("recipe", o.id, { profile_id: value || null });
        },
      },
    ],
  },
};

export function kindInfo(kind: string): KindInfo {
  return INFO[kind] || { footprint: () => null, properties: [] };
}

/* ── rename honesty (HS-132-07) ───────────────────────────────────────
 * Identity edits commit through the EXISTING update paths (the rule at the
 * top of this file). Get Info offered Rename for every kind anyway, so a
 * meeting/artifact/chain rename typed itself into a dead end. Rename is now
 * offered only where a real path takes it; every other kind keeps its name
 * presented and names who owns it. */
const RENAME_LOCKS: Record<string, string> = {
  artifact: "Named by the run that minted it",
  repository: "Named by its git remote",
  roadmap: "Named by its roadmap file",
  story: "Named by its story file",
  coder: "Named by the live coder session",
  game: "Named by the game",
  layout: "Named by the desk layout",
  intelligence: "Named by the desk",
};

/** Why this kind's name cannot be edited, or null when Rename is real. */
export function renameLock(kind: string): string | null {
  // Zones rename through renameZone, not the primitive update path.
  if (kind === "directory") return null;
  if (primitiveUpdateUrl(kind, "id")) return null;
  return RENAME_LOCKS[kind] ?? "No rename path";
}

/** The zones an object is filed into (chips, openable). */
export function filedZones(o: WorldObject, items: Items) {
  const ref = qualifiedRef(o.kind, o.id);
  return (items.directory || []).filter((d) => {
    const members = d.memberIds || [];
    return members.includes(o.id) || members.includes(ref);
  });
}

export function kindLabel(kind: string): string {
  return productLabel(kind);
}

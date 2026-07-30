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
import { productLabel } from "../lib/productLanguage";

export interface InfoProperty {
  key: string;
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
  const m = (o.ref as any).memberIds as string[] | undefined;
  return Array.isArray(m)
    ? `${m.length} ${m.length === 1 ? "member" : "members"}`
    : null;
}

/** The declared table. Kinds not listed inherit UNIVERSAL sections only. */
export const INFO: Record<string, KindInfo> = {
  note: {
    footprint: (o) => chars((o.ref as any).bodyMarkdown),
    properties: [],
  },
  kb: { footprint: (o) => memberCount(o), properties: [] },
  directory: { footprint: (o) => memberCount(o), properties: [] },
  artifact: {
    footprint: (o) => chars((o.ref as any).bodyMarkdown),
    properties: [],
  },
  meeting: {
    footprint: (o) => {
      const n = Number((o.ref as any).segmentCount || 0);
      return n > 0 ? `${n} ${n === 1 ? "segment" : "segments"}` : null;
    },
    properties: [],
  },
  project: {
    footprint: (o) => {
      const n = Number((o.ref as any).meetingCount || 0);
      return `${n} ${n === 1 ? "meeting" : "meetings"}`;
    },
    properties: [],
  },
  recipe: {
    footprint: () => null,
    properties: [
      {
        // Runs on: the ONE property with a real update path today (the
        // recipe PUT's profile_id, the same field the composer writes).
        key: "runs_on",
        type: "choice",
        choices: (_o, _items) => [
          { id: "", label: "This device" },
          ...useDesk.getState().profiles.map((p) => ({
            id: String(p.id),
            label: String(p.name || p.id),
          })),
        ],
        value: (o) => String((o.ref as any).profileId || ""),
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

/** The zones an object is filed into (chips, openable). */
export function filedZones(o: WorldObject, items: Items) {
  const ref = qualifiedRef(o.kind, o.id);
  return (items.directory || []).filter((d) => {
    const members = ((d as any).memberIds as string[]) || [];
    return members.includes(o.id) || members.includes(ref);
  });
}

export function kindLabel(kind: string): string {
  return productLabel(kind);
}

// HS-104-04 — PR receipts: read-only rows for registered delivery
// sources. A receipt says WHEN it observed (observed_at always
// rendered); a failing poll degrades to stale with the rows
// retained. Refresh is the verb here, never ambient. The one egress
// badge on the section is the whole privacy story.
import { create } from "zustand";
import { apiFetch } from "../lib/api";

export type PrAttribution = "exact" | "heuristic" | "none";

export interface PrRow {
  source_id: string;
  number: number;
  title: string;
  url: string;
  head_ref: string;
  base_ref: string;
  head_sha: string;
  base_sha: string;
  state: "draft" | "open" | "merged" | "closed";
  ci: "failing" | "pending" | "passing" | "none";
  author: string;
  observed_at: string;
  attribution: PrAttribution;
  basis: string;
}

export interface PrSource {
  source_id: string;
  label: string;
  status: "live" | "stale" | "unavailable";
  detail: string;
  observed_at: string;
  /** null only when never observed; [] is a known-empty source. */
  prs: PrRow[] | null;
}

export interface PrDiff {
  status: "ok" | "absent" | "unknown_pr" | "failed";
  spec?: string;
  diff?: string;
  detail?: string;
  offer_fetch?: boolean;
}

interface PrReceiptsStore {
  sources: PrSource[];
  loaded: boolean;
  busy: boolean;
  load: () => Promise<void>;
  refresh: (sourceId?: string) => Promise<void>;
  diff: (sourceId: string, number: number) => Promise<PrDiff>;
  fetchShas: (sourceId: string, number: number) => Promise<void>;
}

export const usePrReceipts = create<PrReceiptsStore>((set, get) => ({
  sources: [],
  loaded: false,
  busy: false,

  load: async () => {
    try {
      const data = await apiFetch<{ sources: PrSource[] }>("/api/delivery/prs");
      set({ sources: data.sources ?? [], loaded: true });
    } catch {
      set({ loaded: true });
    }
  },

  refresh: async (sourceId) => {
    set({ busy: true });
    try {
      const url = sourceId
        ? `/api/delivery/prs/refresh?source_id=${encodeURIComponent(sourceId)}`
        : "/api/delivery/prs/refresh";
      const data = await apiFetch<{ sources: PrSource[] }>(url, { method: "POST" });
      set({ sources: data.sources ?? [], loaded: true });
    } catch {
      // The next load() shows the standing truth.
    } finally {
      set({ busy: false });
    }
  },

  diff: async (sourceId, number) => {
    try {
      return await apiFetch<PrDiff>(
        `/api/delivery/prs/${encodeURIComponent(sourceId)}/${number}/diff`,
      );
    } catch {
      return { status: "failed", detail: "diff read failed" };
    }
  },

  fetchShas: async (sourceId, number) => {
    try {
      await apiFetch(
        `/api/delivery/prs/${encodeURIComponent(sourceId)}/${number}/fetch`,
        { method: "POST" },
      );
    } catch {
      // The follow-up diff renders the honest state either way.
    }
  },
}));

export function attributionLabel(row: PrRow): string {
  if (row.attribution === "exact") return "exact";
  if (row.attribution === "heuristic") return "name match";
  return "unattributed";
}

export function prStateLabel(row: PrRow): string {
  if (row.state === "open") {
    if (row.ci === "failing") return "open · CI failing";
    if (row.ci === "pending") return "open · CI running";
    if (row.ci === "passing") return "open · CI green";
    return "open";
  }
  return row.state;
}

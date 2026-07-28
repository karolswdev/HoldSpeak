// HS-104-04 — PR receipts: read-only rows for registered delivery
// sources. A receipt says WHEN it observed (observed_at always
// rendered); a failing poll degrades to stale with the rows
// retained. Refresh is the verb here, never ambient. The one egress
// badge on the section is the whole privacy story.
import { create } from "zustand";
import { apiFetch } from "../lib/api";

export type PrAttribution = "exact" | "heuristic" | "none";

export interface PrVerbAvailability {
  available: boolean;
  reason: string;
}

export interface PrRow {
  source_id: string;
  number: number;
  title: string;
  url: string;
  repo?: string;
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
  needs_you?: boolean;
  worktree_id?: string;
  verbs?: {
    send_agent: PrVerbAvailability;
    draft_review: PrVerbAvailability;
    post_comment: PrVerbAvailability;
    post_status: PrVerbAvailability;
  };
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

export interface PrActionResult {
  operation_id?: string;
  instruction_operation_id?: string;
  artifact_id?: string;
  output?: string;
  proposal_id?: string;
  preview?: string;
  state?: string;
  error?: string;
  reason?: string;
  proposal?: { status?: string; result?: unknown; error?: string };
}

interface PrReceiptsStore {
  sources: PrSource[];
  loaded: boolean;
  busy: boolean;
  load: () => Promise<void>;
  refresh: (sourceId?: string) => Promise<void>;
  diff: (sourceId: string, number: number) => Promise<PrDiff>;
  fetchShas: (sourceId: string, number: number) => Promise<void>;
  sendAgent: (row: PrRow, instruction: string) => Promise<PrActionResult>;
  draftReview: (row: PrRow) => Promise<PrActionResult>;
  propose: (row: PrRow, body: string, kind?: "comment" | "status") => Promise<PrActionResult>;
  decide: (proposalId: string, decision: "approve" | "reject") => Promise<PrActionResult>;
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

  sendAgent: async (row, instruction) =>
    apiFetch<PrActionResult>(
      `/api/delivery/prs/${encodeURIComponent(row.source_id)}/${row.number}/send-agent`,
      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ instruction }) },
    ),

  draftReview: async (row) =>
    apiFetch<PrActionResult>(
      `/api/delivery/prs/${encodeURIComponent(row.source_id)}/${row.number}/draft-review`,
      { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
    ),

  propose: async (row, body, kind = "comment") =>
    apiFetch<PrActionResult>(
      `/api/delivery/prs/${encodeURIComponent(row.source_id)}/${row.number}/propose`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(kind === "comment" ? { kind, body } : { kind, description: body, state: "pending" }),
      },
    ),

  decide: async (proposalId, decision) =>
    apiFetch<PrActionResult>(`/api/delivery/prs/proposals/${proposalId}/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    }),
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

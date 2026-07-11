import { create } from "zustand";
import { apiFetch, readableError } from "../lib/api";

export interface DeskProjection {
  version: number;
  id: string;
  projection_kind: "attention" | "receipt";
  subject_ref: string;
  subject_label: string;
  title: string;
  summary: string;
  reason_code: string;
  decision_kind: string;
  attention_state: "unseen" | "needs_attention" | "acknowledged" | "resolved";
  actual_destination: string | null;
  authority_basis: string | null;
  attempt: number | null;
  outcome: string;
  timestamp: string;
  correlation_id: string | null;
  source_kind: string;
  source_id: string;
  source_api: string;
  detail_url: string;
  severity: "normal" | "warning" | "error";
  dismissed: boolean;
}

interface ProjectionEnvelope {
  projections: DeskProjection[];
  counts: Record<string, number>;
  subject_counts: Record<string, { needs_attention: number; receipts: number }>;
  page: { offset: number; limit: number; total: number; has_more: boolean };
}

interface ProjectionState extends ProjectionEnvelope {
  ambient: DeskProjection[];
  ambientTotal: number;
  open: boolean;
  loading: boolean;
  error: string;
  query: string;
  kind: "" | "attention" | "receipt";
  selectedId: string | null;
  setOpen(open: boolean): void;
  setQuery(query: string): void;
  setKind(kind: "" | "attention" | "receipt"): void;
  select(id: string | null): void;
  refresh(reset?: boolean): Promise<void>;
  refreshAmbient(): Promise<void>;
  loadMore(): Promise<void>;
  present(id: string, action: "acknowledge" | "dismiss" | "restore"): Promise<void>;
}

const EMPTY_PAGE = { offset: 0, limit: 50, total: 0, has_more: false };

export const useProjections = create<ProjectionState>((set, get) => ({
  projections: [],
  ambient: [],
  ambientTotal: 0,
  counts: {},
  subject_counts: {},
  page: EMPTY_PAGE,
  open: false,
  loading: false,
  error: "",
  query: "",
  kind: "",
  selectedId: null,

  setOpen(open) {
    set({ open, selectedId: open ? get().selectedId : null });
    if (open && get().projections.length === 0) void get().refresh(true);
  },
  setQuery(query) {
    set({ query });
  },
  setKind(kind) {
    set({ kind });
  },
  select(selectedId) {
    set({ selectedId });
  },
  async refresh(reset = true) {
    const offset = reset ? 0 : get().page.offset;
    const params = new URLSearchParams({ offset: String(offset), limit: "50" });
    if (get().query.trim()) params.set("q", get().query.trim());
    if (get().kind) params.set("kind", get().kind);
    set({ loading: true, error: "" });
    try {
      const body = await apiFetch<ProjectionEnvelope>(
        `/api/desk/projections?${params.toString()}`,
      );
      set({
        projections: reset ? body.projections : [...get().projections, ...body.projections],
        counts: body.counts,
        subject_counts: body.subject_counts,
        page: body.page,
        loading: false,
      });
    } catch (error) {
      set({ loading: false, error: readableError(error) });
    }
  },
  async refreshAmbient() {
    try {
      const body = await apiFetch<ProjectionEnvelope>(
        "/api/desk/projections?attention_state=needs_attention&offset=0&limit=4",
      );
      set({ ambient: body.projections, ambientTotal: body.page.total });
    } catch {
      // Ambient consumers retain last-known memory while the hub is offline.
    }
  },
  async loadMore() {
    if (!get().page.has_more || get().loading) return;
    set({ page: { ...get().page, offset: get().page.offset + get().page.limit } });
    await get().refresh(false);
  },
  async present(id, action) {
    try {
      await apiFetch(`/api/desk/projections/${encodeURIComponent(id)}/presentation`, {
        method: "PUT",
        json: { action },
      });
      set({ selectedId: action === "dismiss" ? null : get().selectedId });
      await Promise.all([get().refresh(true), get().refreshAmbient()]);
    } catch (error) {
      set({ error: readableError(error) });
    }
  },
}));

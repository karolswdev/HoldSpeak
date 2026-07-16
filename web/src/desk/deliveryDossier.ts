/** Evidence dossiers on the Desk (HS-94-08 / §5.3, §10).
 *
 * A Story or Phase dossier opens IN a desk window — a past completed phase and
 * its evidence are reachable without changing routes to a separate Delivery
 * Workbench app. The hub's dossier route is the sole path authority (§10): the
 * client asks by {project, story|phase} and renders the manifest-bound members,
 * captured runs (pass/fail explicit), and trace it returns. Asset BYTES are
 * fetched separately, manifest-bound, from `/api/delivery/evidence/{b}/{a}`.
 *
 * Typed recovery is preserved (§13): a changed source answers `bundle_changed`
 * with the manifest metadata still attached, an offline source answers
 * `unavailable`, and a missing story answers `not_found` — each a distinct,
 * non-fabricated state, never a blank window.
 */

import { create } from "zustand";
import { apiRequest } from "../lib/api";

export interface DossierMember {
  assetId: string;
  role: string;
  label: string;
  mediaType: string;
  bytes: number;
  sha256: string;
}

export interface CapturedRun {
  timestamp: string;
  command: string;
  exitCode: number | null;
  passed: boolean;
}

export interface StoryDossier {
  kind: "story";
  bundleId: string;
  bundleChanged: boolean;
  freshness: string;
  detail: string;
  sourceId: string;
  project: string;
  storyId: string;
  phase: number | null;
  status: string;
  headSha: string;
  indexTree: string;
  summary: { assets: number; passing: number; failing: number };
  members: DossierMember[];
  capturedRuns: CapturedRun[];
  storyMarkdown: string | null;
  evidenceMarkdown: string | null;
}

export interface PhaseStoryRow {
  storyId: string;
  title: string | null;
  status: string | null;
  state: string;
  bundleId: string | null;
  passing: number;
  failing: number;
}

export interface PhaseDossier {
  kind: "phase";
  project: string;
  phase: number;
  title: string | null;
  status: string | null;
  storiesDone: number | null;
  storiesTotal: number | null;
  stories: PhaseStoryRow[];
}

export type DossierRefusalCode =
  | "bundle_changed"
  | "unavailable"
  | "not_found"
  | "error";

const fromWireMember = (m: any): DossierMember => ({
  assetId: String(m?.asset_id || ""),
  role: String(m?.role || ""),
  label: String(m?.label || m?.role || "Asset"),
  mediaType: String(m?.media_type || "application/octet-stream"),
  bytes: Number(m?.bytes ?? 0),
  sha256: String(m?.sha256 || ""),
});

const fromWireRun = (r: any): CapturedRun => ({
  timestamp: String(r?.timestamp || ""),
  command: String(r?.command || ""),
  exitCode: typeof r?.exit_code === "number" ? r.exit_code : null,
  passed: Boolean(r?.passed),
});

export function fromWireStoryDossier(d: any): StoryDossier {
  const evidence = Array.isArray(d?.evidence) ? d.evidence : [];
  const firstEvidence = evidence.find((e: any) => e?.markdown) || evidence[0];
  return {
    kind: "story",
    bundleId: String(d?.bundle_id || ""),
    bundleChanged: Boolean(d?.bundle_changed),
    freshness: String(d?.freshness || ""),
    detail: String(d?.detail || ""),
    sourceId: String(d?.source_id || ""),
    project: String(d?.project || ""),
    storyId: String(d?.story_id || ""),
    phase: typeof d?.phase === "number" ? d.phase : null,
    status: String(d?.status || ""),
    headSha: String(d?.source_revision?.head_sha || ""),
    indexTree: String(d?.source_revision?.index_tree || ""),
    summary: {
      assets: Number(d?.summary?.assets ?? 0),
      passing: Number(d?.summary?.passing_captures ?? 0),
      failing: Number(d?.summary?.failing_captures ?? 0),
    },
    members: (d?.members || []).map(fromWireMember),
    capturedRuns: (d?.captured_runs || []).map(fromWireRun),
    storyMarkdown: d?.story?.markdown ? String(d.story.markdown) : null,
    evidenceMarkdown: firstEvidence?.markdown
      ? String(firstEvidence.markdown)
      : null,
  };
}

export function fromWirePhaseDossier(d: any): PhaseDossier {
  return {
    kind: "phase",
    project: String(d?.project || ""),
    phase: Number(d?.phase ?? 0),
    title: d?.title ? String(d.title) : null,
    status: d?.status ? String(d.status) : null,
    storiesDone: typeof d?.stories_done === "number" ? d.stories_done : null,
    storiesTotal: typeof d?.stories_total === "number" ? d.stories_total : null,
    stories: (d?.stories || []).map(
      (s: any): PhaseStoryRow => ({
        storyId: String(s?.story_id || ""),
        title: s?.title ? String(s.title) : null,
        status: s?.status ? String(s.status) : null,
        state: String(s?.state || "ready"),
        bundleId: s?.bundle_id ? String(s.bundle_id) : null,
        passing: Number(s?.summary?.passing_captures ?? 0),
        failing: Number(s?.summary?.failing_captures ?? 0),
      }),
    ),
  };
}

/** The URL for a manifest-bound asset's bytes (§5.3). The hub authorizes it. */
export function assetHref(bundleId: string, assetId: string): string {
  return `/api/delivery/evidence/${encodeURIComponent(
    bundleId,
  )}/${encodeURIComponent(assetId)}`;
}

interface DossierState {
  dossier: StoryDossier | PhaseDossier | null;
  loading: boolean;
  /** A typed refusal with the recovery it offers — never a blank window. */
  refusal: { code: DossierRefusalCode; detail: string } | null;
  openStory(project: string, storyId: string, source?: string): Promise<void>;
  openPhase(project: string, phase: number, source?: string): Promise<void>;
  close(): void;
}

function classifyRefusal(status: number, body: any): {
  code: DossierRefusalCode;
  detail: string;
} {
  const raw = String(body?.refusal || body?.error || "");
  if (status === 409 || raw === "bundle_changed" || raw === "hash_mismatch")
    return { code: "bundle_changed", detail: body?.detail || "source changed" };
  if (status === 503 || raw === "unavailable")
    return { code: "unavailable", detail: body?.detail || "source offline" };
  if (status === 404 || raw === "not_found" || raw === "not_in_manifest")
    return { code: "not_found", detail: body?.detail || raw || "not found" };
  return { code: "error", detail: body?.detail || raw || `HTTP ${status}` };
}

export const useDeliveryDossier = create<DossierState>((set) => ({
  dossier: null,
  loading: false,
  refusal: null,

  async openStory(project, storyId, source) {
    set({ loading: true, refusal: null, dossier: null });
    const q = source ? `?source=${encodeURIComponent(source)}` : "";
    try {
      const res = await apiRequest(
        `/api/delivery/stories/${encodeURIComponent(
          project,
        )}/${encodeURIComponent(storyId)}/dossier${q}`,
      );
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        set({ dossier: fromWireStoryDossier(body), loading: false });
      } else {
        set({ refusal: classifyRefusal(res.status, body), loading: false });
      }
    } catch {
      set({
        refusal: { code: "unavailable", detail: "hub unreachable" },
        loading: false,
      });
    }
  },

  async openPhase(project, phase, source) {
    set({ loading: true, refusal: null, dossier: null });
    const q = source ? `?source=${encodeURIComponent(source)}` : "";
    try {
      const res = await apiRequest(
        `/api/delivery/phases/${encodeURIComponent(project)}/${phase}/dossier${q}`,
      );
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        set({ dossier: fromWirePhaseDossier(body), loading: false });
      } else {
        set({ refusal: classifyRefusal(res.status, body), loading: false });
      }
    } catch {
      set({
        refusal: { code: "unavailable", detail: "hub unreachable" },
        loading: false,
      });
    }
  },

  close() {
    set({ dossier: null, refusal: null, loading: false });
  },
}));

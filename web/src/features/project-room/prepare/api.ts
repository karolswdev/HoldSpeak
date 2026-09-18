// HS-200-11 — typed wrappers for the preparation-brief wire.
// Every endpoint named, path-encoded, decoded in ONE place.

import { apiFetch, ApiError } from "../../../lib/api";
import {
  decodeBrief,
  decodeManifest,
  decodeRoute,
  type Brief,
  type BriefManifest,
  type BriefRoute,
  type PrepareRefusal,
} from "./model";

const project = (id: string) => `/api/projects/${encodeURIComponent(id)}`;

/** GET /api/projects/{id}/briefs/route — the route the drafter would use.  No dispatch. */
export async function fetchBriefRoute(projectId: string): Promise<BriefRoute> {
  const raw = await apiFetch<{ route?: Record<string, unknown> }>(`${project(projectId)}/briefs/route`);
  return decodeRoute(raw?.route);
}

/** GET /api/projects/{id}/briefs/manifest — the manifest a prepare would bind now.  No write. */
export async function fetchBriefManifest(projectId: string): Promise<BriefManifest> {
  const raw = await apiFetch<{ manifest?: Record<string, unknown> }>(`${project(projectId)}/briefs/manifest`);
  return decodeManifest(raw?.manifest);
}

/** POST /api/projects/{id}/briefs/prepare — returns the brief, or the hub's refusal. */
export async function prepareBrief(
  projectId: string,
  purpose: string,
  opts: { generator?: "model" | "deterministic"; signal?: AbortSignal; attemptId?: string } = {},
): Promise<{ ok: true; brief: Brief } | { ok: false; refusal: PrepareRefusal }> {
  try {
    const raw = await apiFetch<{ brief: Record<string, unknown> }>(`${project(projectId)}/briefs/prepare`, {
      method: "POST",
      json: { purpose, generator: opts.generator ?? "model", attempt_id: opts.attemptId ?? "" },
      signal: opts.signal,
    });
    return { ok: true, brief: decodeBrief(raw.brief) };
  } catch (error) {
    if (error instanceof ApiError && error.status === 409 && error.payload && typeof error.payload === "object") {
      const payload = error.payload as Record<string, unknown>;
      return {
        ok: false,
        refusal: {
          route: decodeRoute(payload.route as Record<string, unknown>),
          purpose: String(payload.purpose ?? purpose),
          error: String(payload.error ?? error.message),
        },
      };
    }
    throw error;
  }
}

/** GET /api/projects/{id}/briefs?lifecycle=kept — the kept briefs, newest first. */
export async function fetchBriefs(projectId: string, lifecycle?: string): Promise<Brief[]> {
  const params = lifecycle ? `?lifecycle=${encodeURIComponent(lifecycle)}` : "";
  const raw = await apiFetch<{ briefs?: Record<string, unknown>[] }>(`${project(projectId)}/briefs${params}`);
  return Array.isArray(raw?.briefs) ? raw.briefs.map(decodeBrief) : [];
}

/** GET /api/briefs/{id} — one brief, its manifest freeze re-verified by the hub. */
export async function fetchBrief(briefId: string): Promise<Brief> {
  const raw = await apiFetch<{ brief: Record<string, unknown> }>(`/api/briefs/${encodeURIComponent(briefId)}`);
  return decodeBrief(raw.brief);
}

/** POST /api/briefs/{id}/keep — the lifecycle flip. */
export async function keepBrief(briefId: string): Promise<Brief> {
  const raw = await apiFetch<{ brief: Record<string, unknown> }>(`/api/briefs/${encodeURIComponent(briefId)}/keep`, {
    method: "POST",
    json: {},
  });
  return decodeBrief(raw.brief);
}

/** POST /api/briefs/{id}/discard — a state, never a delete. */
export async function discardBrief(briefId: string): Promise<Brief> {
  const raw = await apiFetch<{ brief: Record<string, unknown> }>(`/api/briefs/${encodeURIComponent(briefId)}/discard`, {
    method: "POST",
    json: {},
  });
  return decodeBrief(raw.brief);
}

/** POST /api/projects/{id}/briefs/stop — cancel the attempt's kernel operation;
 *  a run that still completes writes no draft. */
export async function stopBrief(projectId: string, attemptId: string): Promise<{ stopped: boolean; disposition: string }> {
  const raw = await apiFetch<{ stopped?: boolean; disposition?: string }>(`${project(projectId)}/briefs/stop`, {
    method: "POST",
    json: { attempt_id: attemptId },
  });
  return { stopped: Boolean(raw?.stopped), disposition: String(raw?.disposition ?? "") };
}

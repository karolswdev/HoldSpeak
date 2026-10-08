// HS-162-05 -- typed API wrappers for the update wire.
// Every endpoint is named, path-encoded, and carries its response type.
// Fixture shapes mined from tests/integration/test_update_routes.py.

import { apiFetch } from "../../../lib/api";
import type { Delivery, ProjectUpdate } from "./model";
import { decodeDelivery, decodeUpdate } from "./model";

/** GET /api/projects/{id}/updates — list all (optionally filtered). */
export async function fetchUpdates(
  projectId: string,
  lifecycle?: string,
): Promise<ProjectUpdate[]> {
  const params = lifecycle ? `?lifecycle=${encodeURIComponent(lifecycle)}` : "";
  const raw = await apiFetch<{ updates: Record<string, unknown>[] }>(
    `/api/projects/${encodeURIComponent(projectId)}/updates${params}`,
  );
  return (raw.updates ?? []).map(decodeUpdate);
}

/** POST /api/projects/{id}/updates/draft — draft an update. */
export async function draftUpdate(
  projectId: string,
  generator: "deterministic" | "model",
): Promise<ProjectUpdate> {
  const raw = await apiFetch<{ success: boolean; update: Record<string, unknown> }>(
    `/api/projects/${encodeURIComponent(projectId)}/updates/draft`,
    { method: "POST", json: { generator } },
  );
  return decodeUpdate(raw.update);
}

/** PUT /api/updates/{id} — save the owner's edit (draft only). */
export async function saveUpdate(
  updateId: string,
  bodyMd: string,
): Promise<ProjectUpdate> {
  const raw = await apiFetch<{ success: boolean; update: Record<string, unknown> }>(
    `/api/updates/${encodeURIComponent(updateId)}`,
    { method: "PUT", json: { body_md: bodyMd } },
  );
  return decodeUpdate(raw.update);
}

/** PHILO-15 B64: POST /api/updates/{id}/claims/{span}/review — the owner's
 *  Accept / Reject on one claim (draft only). */
export async function reviewClaim(
  updateId: string,
  spanId: string,
  acceptance: "accepted" | "rejected",
): Promise<{ update: ProjectUpdate; reviewedAt: string }> {
  const raw = await apiFetch<{ success: boolean; update: Record<string, unknown>; reviewed_at: string }>(
    `/api/updates/${encodeURIComponent(updateId)}/claims/${encodeURIComponent(spanId)}/review`,
    { method: "POST", json: { acceptance } },
  );
  return { update: decodeUpdate(raw.update), reviewedAt: String(raw.reviewed_at ?? "") };
}

/** POST /api/updates/{id}/regenerate — supersede + fresh draft. */
export async function regenerateUpdate(
  updateId: string,
  generator: "deterministic" | "model",
): Promise<ProjectUpdate> {
  const raw = await apiFetch<{ success: boolean; update: Record<string, unknown> }>(
    `/api/updates/${encodeURIComponent(updateId)}/regenerate`,
    { method: "POST", json: { generator } },
  );
  return decodeUpdate(raw.update);
}

/** POST /api/updates/{id}/publish — lifecycle publish. */
export async function publishUpdate(
  updateId: string,
): Promise<ProjectUpdate> {
  const raw = await apiFetch<{ success: boolean; update: Record<string, unknown> }>(
    `/api/updates/${encodeURIComponent(updateId)}/publish`,
    { method: "POST", json: {} },
  );
  return decodeUpdate(raw.update);
}

/** POST /api/updates/{id}/delivered (PHILO-9-02's route; the Q0 ruling):
 *  he confirms he delivered the published text himself. One press of Mark
 *  delivered mints ONE command_id and keeps it across its retries; the hub
 *  replays that key to the original row. */
export async function markDelivered(
  updateId: string,
  deliveredTo: string,
  commandId: string,
): Promise<Delivery> {
  const raw = await apiFetch<{ delivery: Record<string, unknown> }>(
    `/api/updates/${encodeURIComponent(updateId)}/delivered`,
    { method: "POST", json: { delivered_to: deliveredTo.trim() || null, command_id: commandId } },
  );
  return decodeDelivery(raw.delivery);
}

/** GET /api/updates/{id}/markdown — the copyable body. */
export async function fetchUpdateMarkdown(
  updateId: string,
): Promise<string> {
  // apiFetch returns parsed text when content-type is text/markdown
  const text = await apiFetch<string>(
    `/api/updates/${encodeURIComponent(updateId)}/markdown`,
  );
  return String(text);
}

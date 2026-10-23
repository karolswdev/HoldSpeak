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

/** Turn the project's saved Friday start on. */
export async function enableFridayUpdate(workbenchId: string): Promise<void> {
  await apiFetch(`/api/workbenches/${encodeURIComponent(workbenchId)}`, {
    method: "PUT",
    json: { schedule: "0 15 * * 5", schedule_enabled: true },
  });
}

/** GET /api/updates/{id} — one update by id. */
export async function fetchUpdate(updateId: string): Promise<ProjectUpdate> {
  const raw = await apiFetch<{ update: Record<string, unknown> }>(
    `/api/updates/${encodeURIComponent(updateId)}`,
  );
  return decodeUpdate(raw.update);
}

/** POST /api/projects/{id}/updates/draft — draft an update. */
export async function draftUpdate(
  projectId: string,
  generator: "deterministic" | "model",
  commandId?: string,
): Promise<ProjectUpdate> {
  // P0: each press sends a command_id, so a failed draft leaves a record.
  const json: Record<string, unknown> = { generator };
  if (commandId) json.command_id = commandId;
  const raw = await apiFetch<{ success: boolean; update: Record<string, unknown> }>(
    `/api/projects/${encodeURIComponent(projectId)}/updates/draft`,
    { method: "POST", json },
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

/* ── Betterment P1: the engine pass behind Write update ── */

export type EngineJob = {
  id: string;
  baseUpdateId: string;
  state: "running" | "succeeded" | "failed" | "stopped" | "applied";
  reason: string | null;
  detail: string | null;
  startedAt: string;
  finishedAt: string | null;
  appliedUpdateId: string | null;
  resultUpdateId: string | null;
  generatorModel: string | null;
};

function decodeJob(raw: Record<string, unknown>): EngineJob {
  const text = (v: unknown) => (typeof v === "string" && v ? v : null);
  return {
    id: String(raw.id ?? ""),
    baseUpdateId: String(raw.base_update_id ?? ""),
    state: String(raw.state ?? "running") as EngineJob["state"],
    reason: text(raw.reason),
    detail: text(raw.detail),
    startedAt: String(raw.started_at ?? ""),
    finishedAt: text(raw.finished_at),
    appliedUpdateId: text(raw.applied_update_id),
    resultUpdateId: text(raw.result_update_id),
    generatorModel: text(raw.generator_model),
  };
}

/** POST /api/updates/{id}/engine-pass — the engine improves this draft in the background. */
export async function startEnginePass(updateId: string, automationId?: string): Promise<EngineJob> {
  const raw = await apiFetch<{ job: Record<string, unknown> }>(
    `/api/updates/${encodeURIComponent(updateId)}/engine-pass`,
    { method: "POST", json: automationId ? { automation_id: automationId } : {} },
  );
  return decodeJob(raw.job);
}

/** GET /api/update-jobs/{id} — the pass, polled. */
export async function fetchEngineJob(jobId: string): Promise<EngineJob> {
  const raw = await apiFetch<{ job: Record<string, unknown> }>(
    `/api/update-jobs/${encodeURIComponent(jobId)}`,
  );
  return decodeJob(raw.job);
}

/** POST /api/update-jobs/{id}/stop — its late answer is dropped. */
export async function stopEngineJob(jobId: string): Promise<EngineJob> {
  const raw = await apiFetch<{ job: Record<string, unknown> }>(
    `/api/update-jobs/${encodeURIComponent(jobId)}/stop`,
    { method: "POST", json: {} },
  );
  return decodeJob(raw.job);
}

/** POST /api/update-jobs/{id}/apply — the engine's draft becomes the next
 *  revision. Refused 409 `draft_changed` when he edited, unless `force`. */
export async function applyEngineJob(jobId: string, force = false): Promise<ProjectUpdate> {
  const raw = await apiFetch<{ update: Record<string, unknown> }>(
    `/api/update-jobs/${encodeURIComponent(jobId)}/apply`,
    { method: "POST", json: { force } },
  );
  return decodeUpdate(raw.update);
}

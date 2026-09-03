// HS-163-05 -- typed API wrappers for the steward wire.
// Endpoint paths match holdspeak/web/routes/steward.py.

import { apiFetch } from "../../../lib/api";
import type { StewardRun, StewardStep, StewardPolicy, StewardWatch } from "./model";
import { decodeRun, decodeStep, decodePolicy, decodeWatch } from "./model";

/** POST /api/projects/{id}/steward/runs -- start a run (immediate-id). */
export async function startRun(projectId: string): Promise<{
  success: boolean;
  runId: string | null;
  code?: string;
  message?: string;
}> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/api/projects/${encodeURIComponent(projectId)}/steward/runs`,
    { method: "POST", json: {} },
  );
  return {
    success: Boolean(raw.success),
    runId: raw.run_id != null ? String(raw.run_id) : null,
    code: raw.code != null ? String(raw.code) : undefined,
    message: raw.message != null ? String(raw.message) : undefined,
  };
}

/** GET /api/projects/{id}/steward/runs -- list runs. */
export async function listRuns(projectId: string): Promise<StewardRun[]> {
  const raw = await apiFetch<{ runs: Record<string, unknown>[] }>(
    `/api/projects/${encodeURIComponent(projectId)}/steward/runs`,
  );
  return (raw.runs ?? []).map(decodeRun);
}

/** GET /api/steward/runs/{runId} -- pollable state. */
export async function getRun(runId: string): Promise<{
  run: StewardRun;
  steps: StewardStep[];
}> {
  const raw = await apiFetch<{
    run: Record<string, unknown>;
    steps: Record<string, unknown>[];
  }>(`/api/steward/runs/${encodeURIComponent(runId)}`);
  return {
    run: decodeRun(raw.run),
    steps: (raw.steps ?? []).map(decodeStep),
  };
}

/** POST /api/steward/runs/{runId}/stop -- STW-003. */
export async function stopRun(runId: string): Promise<{ success: boolean }> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/api/steward/runs/${encodeURIComponent(runId)}/stop`,
    { method: "POST", json: {} },
  );
  return { success: Boolean(raw.success) };
}

/** GET /api/projects/{id}/steward/policy -- get policy. */
export async function getPolicy(projectId: string): Promise<StewardPolicy | null> {
  const raw = await apiFetch<{ policy: Record<string, unknown> | null }>(
    `/api/projects/${encodeURIComponent(projectId)}/steward/policy`,
  );
  return raw.policy ? decodePolicy(raw.policy) : null;
}

/** PUT /api/projects/{id}/steward/policy -- update policy. */
export async function putPolicy(
  projectId: string,
  payload: {
    eligible_effect_kinds?: string[];
    max_retries?: number;
    max_actions_per_run?: number;
    cooldown_seconds?: number;
    bounds?: Record<string, unknown>;
    enabled?: boolean;
    unattended_enabled?: boolean;
    evaluation_cadence_minutes?: number;  // HS-167-02
  },
): Promise<{ success: boolean; policy: StewardPolicy; error?: string }> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/api/projects/${encodeURIComponent(projectId)}/steward/policy`,
    { method: "PUT", json: payload },
  );
  if (raw.success === false) {
    return {
      success: false,
      policy: null as unknown as StewardPolicy,
      error: String(raw.message ?? "Validation failed"),
    };
  }
  return {
    success: true,
    policy: decodePolicy(raw.policy as Record<string, unknown>),
  };
}

/** GET /api/projects/{id}/watches -- project watches (for grant text + circuit). */
export async function listProjectWatches(projectId: string): Promise<StewardWatch[]> {
  const raw = await apiFetch<{ watches: Record<string, unknown>[] }>(
    `/api/projects/${encodeURIComponent(projectId)}/watches`,
  );
  return (raw.watches ?? []).map(decodeWatch);
}

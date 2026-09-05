// HS-169-02 — typed client for the streamlined Door routes.
// Mirrors holdspeak/services/door_service.py (count + create).

import { apiFetch } from "../../../lib/api";

/* ── Wire types ── */

export interface CountToken {
  key: string;
  label: string;
  count: number;
}

export interface CountResponse {
  tokens: CountToken[];
  plain: string;
  checkedAt: string;
  host: string;
  state: "live" | "cant_check";
  reason: string | null;
}

export interface CreateResponse {
  projectId: string;
}

export interface DoorSourcePayload {
  provider: string;
  scope: string | { connection_ref: string; projects: string[] };
  watches: string[];
  adjust?: Record<string, unknown>;
}

/* ── Decoders ── */

function decodeCountToken(raw: Record<string, unknown>): CountToken {
  return {
    key: String(raw.key ?? ""),
    label: String(raw.label ?? ""),
    count: typeof raw.count === "number" ? raw.count : 0,
  };
}

function decodeCountResponse(raw: Record<string, unknown>): CountResponse {
  const tokens = Array.isArray(raw.tokens)
    ? (raw.tokens as Record<string, unknown>[]).map(decodeCountToken)
    : [];
  return {
    tokens,
    plain: String(raw.plain ?? ""),
    checkedAt: String(raw.checked_at ?? raw.checkedAt ?? ""),
    host: String(raw.host ?? ""),
    state: raw.state === "cant_check" ? "cant_check" : "live",
    reason: typeof raw.reason === "string" ? raw.reason : null,
  };
}

function decodeCreateResponse(raw: Record<string, unknown>): CreateResponse {
  return {
    projectId: String(raw.project_id ?? raw.projectId ?? ""),
  };
}

/* ── API calls ── */

export async function doorCount(
  provider: string,
  scope: string | { connection_ref: string; projects: string[] },
  watches: string[],
  adjust?: Record<string, unknown>,
): Promise<CountResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    "/api/projects/door/count",
    { method: "POST", json: { provider, scope, watches, adjust } },
  );
  return decodeCountResponse(raw);
}

export async function doorCreate(
  outcome: string,
  sources: DoorSourcePayload[],
): Promise<CreateResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    "/api/projects/door",
    { method: "POST", json: { outcome, sources } },
  );
  return decodeCreateResponse(raw);
}

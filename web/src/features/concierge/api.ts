// HS-170-03 — typed client for the Concierge routes.
// Mirrors holdspeak/services/concierge_service.py (detect + propose + probe + apply + download).

import { apiFetch } from "../../lib/api";

/* ── Wire types ── */

export type EngineKind = "lan" | "local" | "cloud" | "preset";
export type EngineState = "READY" | "WAITING" | "NOT_SET" | "UNREACHABLE" | "CHECKING";

export interface Engine {
  id: string;
  kind: EngineKind;
  name: string;
  host: string;
  state: EngineState;
  latencyMs?: number | null;
  sizeBytes?: number | null;
  runtimeToken?: string | null;
  quantToken?: string | null;
  visionToken?: string | null;
  keySet?: boolean;
  profileId?: string;
  presetId?: string;
  installed?: boolean;
  path?: string;
}

export interface HardwareInfo {
  capability?: {
    apple_silicon?: boolean;
    system?: string;
    architecture?: string;
    brand?: string;
    ram_gb?: number;
  };
}

export interface DetectResponse {
  engines: Engine[];
  hardware: HardwareInfo;
  runtimes: Array<{ id: string; state: string }>;
  checkedAt: string;
}

export interface ProposalRow {
  group: string;
  label: string;
  engineId: string | null;
  host: string;
  state: EngineState;
  presetId?: string;
  alternatives?: Engine[];
}

export interface ProposeResponse {
  rows: ProposalRow[];
  receipt: {
    groups: number;
    engines: number;
    waiting: number;
  };
}

export interface ProbeResponse {
  state: EngineState;
  host: string;
  latencyMs: number | null;
  keySet?: boolean;
  cost?: { tokens: number };
  plainReason?: string;
}

export interface ApplyResponse {
  receipt: string;
  summary: {
    groups: number;
    engines: number;
    ready: number;
    off: number;
  };
  results: Array<{
    group: string;
    state: string;
    plainReason?: string;
  }>;
}

export interface DownloadResponse {
  jobId: string;
  presetId: string;
  progress: { received: number; total: number };
}

/* ── Decoders ── */

function decodeEngine(raw: Record<string, unknown>): Engine {
  return {
    id: String(raw.id ?? ""),
    kind: (raw.kind ?? "local") as EngineKind,
    name: String(raw.name ?? ""),
    host: String(raw.host ?? ""),
    state: (raw.state ?? "WAITING") as EngineState,
    latencyMs: typeof raw.latencyMs === "number" ? raw.latencyMs : null,
    sizeBytes: typeof raw.sizeBytes === "number" ? raw.sizeBytes : null,
    runtimeToken: typeof raw.runtimeToken === "string" ? raw.runtimeToken : null,
    quantToken: typeof raw.quantToken === "string" ? raw.quantToken : null,
    visionToken: typeof raw.visionToken === "string" ? raw.visionToken : null,
    keySet: typeof raw.keySet === "boolean" ? raw.keySet : undefined,
    profileId: typeof raw.profileId === "string" ? raw.profileId : undefined,
    presetId: typeof raw.presetId === "string" ? raw.presetId : undefined,
    installed: typeof raw.installed === "boolean" ? raw.installed : undefined,
    path: typeof raw.path === "string" ? raw.path : undefined,
  };
}

function decodeDetect(raw: Record<string, unknown>): DetectResponse {
  const engines = Array.isArray(raw.engines)
    ? (raw.engines as Record<string, unknown>[]).map(decodeEngine)
    : [];
  return {
    engines,
    hardware: (raw.hardware ?? {}) as HardwareInfo,
    runtimes: Array.isArray(raw.runtimes)
      ? (raw.runtimes as Array<{ id: string; state: string }>)
      : [],
    checkedAt: String(raw.checkedAt ?? ""),
  };
}

function decodeProposal(raw: Record<string, unknown>): ProposeResponse {
  const rows = Array.isArray(raw.rows)
    ? (raw.rows as Record<string, unknown>[]).map((r) => ({
        group: String(r.group ?? ""),
        label: String(r.label ?? ""),
        engineId: r.engineId != null ? String(r.engineId) : null,
        host: String(r.host ?? ""),
        state: (r.state ?? "WAITING") as EngineState,
        presetId: typeof r.presetId === "string" ? r.presetId : undefined,
      }))
    : [];
  const receipt = (raw.receipt ?? {}) as Record<string, unknown>;
  return {
    rows,
    receipt: {
      groups: typeof receipt.groups === "number" ? receipt.groups : 0,
      engines: typeof receipt.engines === "number" ? receipt.engines : 0,
      waiting: typeof receipt.waiting === "number" ? receipt.waiting : 0,
    },
  };
}

/* ── API calls ── */

export async function conciergeDetect(): Promise<DetectResponse> {
  const raw = await apiFetch<Record<string, unknown>>("/api/concierge/detect");
  return decodeDetect(raw);
}

export async function conciergePropose(): Promise<ProposeResponse> {
  const raw = await apiFetch<Record<string, unknown>>("/api/concierge/propose", {
    method: "POST",
  });
  return decodeProposal(raw);
}

export async function conciergeProbe(
  engineId: string,
  generate?: boolean,
): Promise<ProbeResponse> {
  const raw = await apiFetch<Record<string, unknown>>("/api/concierge/probe", {
    method: "POST",
    json: { engineId, ...(generate ? { generate: true } : {}) },
  });
  return {
    state: (raw.state ?? "UNREACHABLE") as EngineState,
    host: String(raw.host ?? ""),
    latencyMs: typeof raw.latencyMs === "number" ? raw.latencyMs : null,
    keySet: typeof raw.keySet === "boolean" ? raw.keySet : undefined,
    cost: raw.cost as ProbeResponse["cost"],
    plainReason: typeof raw.plainReason === "string" ? raw.plainReason : undefined,
  };
}

export async function conciergeApply(
  rows: Array<{ group: string; engineId: string | null; state: string }>,
): Promise<ApplyResponse> {
  const raw = await apiFetch<Record<string, unknown>>("/api/concierge/apply", {
    method: "POST",
    json: { rows },
  });
  return raw as unknown as ApplyResponse;
}

export async function conciergeDownload(presetId: string): Promise<DownloadResponse> {
  const raw = await apiFetch<Record<string, unknown>>("/api/concierge/download", {
    method: "POST",
    json: { presetId },
  });
  return {
    jobId: String(raw.jobId ?? ""),
    presetId: String(raw.presetId ?? presetId),
    progress: (raw.progress ?? { received: 0, total: 0 }) as { received: number; total: number },
  };
}

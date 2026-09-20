// HS-170-03 — typed client for the Concierge routes.
// Mirrors holdspeak/services/concierge_service.py (detect + propose + probe + apply + download).

import { apiFetch } from "../../lib/api";
import type { EndpointDraft } from "./endpointDraft";

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
  legacyLabel?: string;
  keySet?: boolean;
  profileId?: string;
  presetId?: string;
  installed?: boolean;
  path?: string;
  baseUrl?: string;
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

/* HS-200-04 — the named repair states. One verb each; `control` says which
   existing control that verb opens. The face never decides the policy. */
export type RepairToken =
  | "MODEL FILE MISSING"
  | "ENDPOINT UNREACHABLE"
  | "TOOL INCOMPATIBLE"
  | "CREDENTIAL EXPIRED";

export type RepairControl =
  | "model_library"
  | "endpoint_editor"
  | "engine_picker"
  | "connections";

export interface Repair {
  id: string;
  token: RepairToken;
  subject: string;
  host: string;
  scope: "local" | "cloud";
  groups: string[];
  groupLabels: string[];
  verb: string;
  control: RepairControl;
  engineId: string;
  presetId: string;
  baseUrl: string;
  detail: string;
}

/* HS-201-09 — the APPLIED summary truth, read from the same projection the
   deferred queue resolves. The face shows this, never the proposal, for the
   Meetings row: `assigned` names the engine that will run, `off` is the
   owner's own OFF still standing after a reload. */
export interface SummaryAssignment {
  capabilityId: string;
  status: "assigned" | "attention" | "off" | "unassigned";
  assignmentRevision: number;
  profileId: string | null;
  profileRevision: number | null;
  label: string | null;
  boundary: string | null;
  readiness: string | null;
}

export interface DetectResponse {
  engines: Engine[];
  hardware: HardwareInfo;
  runtimes: Array<{ id: string; state: string }>;
  checkedAt: string;
  repairs: Repair[];
  summaryAssignment: SummaryAssignment | null;
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

/* HS-200-04 — the task probe: one real request through the assigned route. */
export interface TaskProbeResponse {
  state: "READY" | "UNREACHABLE" | "REFUSED";
  ok: boolean;
  capabilityId: string;
  group: string;
  outcome?: string;
  reasonCode: string;
  engine?: string;
  model?: string;
  boundary?: string;
  host?: string;
  latencyMs?: number;
  routePlanId?: string;
  executionId?: string;
  paid?: boolean;
  legs: Array<{
    ordinal: number;
    profileId?: string;
    deploymentRevisionId: string;
    boundary: string;
    status?: string;
    disposition?: string;
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
    legacyLabel: typeof raw.legacyLabel === "string" ? raw.legacyLabel : undefined,
    presetId: typeof raw.presetId === "string" ? raw.presetId : undefined,
    installed: typeof raw.installed === "boolean" ? raw.installed : undefined,
    path: typeof raw.path === "string" ? raw.path : undefined,
    baseUrl: typeof raw.baseUrl === "string" ? raw.baseUrl : undefined,
  };
}

function decodeRepair(raw: Record<string, unknown>): Repair {
  const groups = Array.isArray(raw.groups) ? raw.groups.map(String) : [];
  const labels = Array.isArray(raw.groupLabels)
    ? raw.groupLabels.map(String)
    : groups;
  return {
    id: String(raw.id ?? ""),
    token: String(raw.token ?? "") as RepairToken,
    subject: String(raw.subject ?? ""),
    host: String(raw.host ?? ""),
    scope: raw.scope === "cloud" ? "cloud" : "local",
    groups,
    groupLabels: labels,
    verb: String(raw.verb ?? ""),
    control: String(raw.control ?? "engine_picker") as RepairControl,
    engineId: String(raw.engineId ?? ""),
    presetId: String(raw.presetId ?? ""),
    baseUrl: String(raw.baseUrl ?? ""),
    detail: String(raw.detail ?? ""),
  };
}

function decodeSummaryAssignment(
  raw: unknown,
): SummaryAssignment | null {
  if (typeof raw !== "object" || raw === null) return null;
  const row = raw as Record<string, unknown>;
  const status = String(row.status ?? "unassigned");
  return {
    capabilityId: String(row.capabilityId ?? ""),
    status:
      status === "assigned" || status === "attention" || status === "off"
        ? status
        : "unassigned",
    assignmentRevision:
      typeof row.assignmentRevision === "number" ? row.assignmentRevision : 0,
    profileId: typeof row.profileId === "string" ? row.profileId : null,
    profileRevision:
      typeof row.profileRevision === "number" ? row.profileRevision : null,
    label: typeof row.label === "string" ? row.label : null,
    boundary: typeof row.boundary === "string" ? row.boundary : null,
    readiness: typeof row.readiness === "string" ? row.readiness : null,
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
    repairs: Array.isArray(raw.repairs)
      ? (raw.repairs as Record<string, unknown>[]).map(decodeRepair)
      : [],
    summaryAssignment: decodeSummaryAssignment(raw.summaryAssignment),
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

export async function conciergeTaskProbe(
  capabilityId?: string,
  confirmOffMachine?: boolean,
): Promise<TaskProbeResponse> {
  const raw = await apiFetch<Record<string, unknown>>("/api/concierge/probe", {
    method: "POST",
    json: {
      task: true,
      ...(capabilityId ? { capabilityId } : {}),
      ...(confirmOffMachine ? { confirmOffMachine: true } : {}),
    },
  });
  return {
    ...(raw as unknown as TaskProbeResponse),
    legs: Array.isArray(raw.legs)
      ? (raw.legs as TaskProbeResponse["legs"])
      : [],
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

/* HS-201-09 — Check: ask the HUB to read the endpoint's /models.
   The hub is the one that leaves this machine, never the browser. */
export interface EndpointCheck {
  ok: boolean;
  models: string[];
  detail: string;
}

export async function checkEndpoint(baseUrl: string): Promise<EndpointCheck> {
  const { apiFetch, ApiError } = await import("../../lib/api");
  // An unreachable endpoint answers 422 carrying the SAME body as a reachable
  // one; the plain reason is in it, so the refusal is read, not re-worded.
  let raw: Record<string, unknown>;
  try {
    raw = await apiFetch<Record<string, unknown>>("/api/setup/discover-models", {
      method: "POST",
      json: { base_url: baseUrl },
    });
  } catch (err) {
    if (err instanceof ApiError && err.payload && typeof err.payload === "object") {
      raw = err.payload as Record<string, unknown>;
    } else {
      return {
        ok: false,
        models: [],
        detail: err instanceof Error ? err.message : "Could not reach the model server.",
      };
    }
  }
  return {
    ok: raw.ok === true,
    models: Array.isArray(raw.models) ? raw.models.map(String) : [],
    detail: String(raw.detail ?? "Could not reach the model server."),
  };
}

/* HS-201-09 — define one endpoint through the Model Library command the
   service already accepts (see endpointDraft.ts for why the body is built
   there). The receipt names the immutable profile revision the summary
   selection must carry. */
export interface DefinedEndpoint {
  profileId: string;
  profileRevision: number;
}

export async function defineEndpoint(
  draft: EndpointDraft,
): Promise<DefinedEndpoint> {
  const { apiFetch } = await import("../../lib/api");
  const raw = await apiFetch<Record<string, unknown>>(
    "/api/inference/model-library/define-endpoint",
    { method: "POST", json: { draft, secret: null } },
  );
  const provider = (raw.provider ?? {}) as Record<string, unknown>;
  return {
    profileId: String(provider.profile_id ?? ""),
    profileRevision:
      typeof provider.profile_revision === "number"
        ? provider.profile_revision
        : 0,
  };
}

/* HS-201-09 — the one explicit summary gesture (lane A's documented seam).
   HTTP 200 alone does not mean it succeeded: read `result.state`. */
export interface SummarySelectionResult {
  status: string;
  state: string;
  plainReason: string;
  summaryAssignment: SummaryAssignment | null;
}

export async function conciergeSummarySelection(body: {
  commandId: string;
  expectedAssignmentRevision: number;
  profileId: string;
  profileRevision: number;
}): Promise<SummarySelectionResult> {
  const { apiFetch } = await import("../../lib/api");
  const raw = await apiFetch<Record<string, unknown>>(
    "/api/concierge/summary-selection",
    { method: "POST", json: body },
  );
  const result = (raw.result ?? {}) as Record<string, unknown>;
  return {
    status: String(raw.status ?? ""),
    state: String(result.state ?? ""),
    plainReason: String(result.plainReason ?? ""),
    summaryAssignment: decodeSummaryAssignment(raw.summaryAssignment),
  };
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

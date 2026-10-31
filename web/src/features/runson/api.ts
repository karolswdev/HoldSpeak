// PHILO-16 (C) — Runs on: the reads and writes the Switchboard makes.
//
// Reads: the assignment roster (fast, painted first) and the Concierge
// detection (engines, repairs, the summary row; its LAN probes take up to
// 1.5 s each, so it fills in after the first paint). Writes: one
// `/api/inference/assignments/set` per drop (the whole chain, CAS), the
// clear that undoes a first patch, and the acquisition poll for a download.
// The summary row, the probes, the download start and the Model Library
// writes are the Concierge's own clients (features/concierge/api.ts).

import { apiFetch } from "../../lib/api";
import type { Engine, Repair, SummaryAssignment } from "../concierge/api";

/* ── the roster (GET /api/inference/assignments) ── */

export interface RosterEntry {
  profile_id: string;
  profile_revision: number;
  label: string;
  boundary: string;
  readiness: string;
}

export interface RosterIssue {
  code: string;
  severity: string;
  capability_id?: string;
}

export interface RosterRow {
  /** `global` (Default for AI work) or a group id. */
  id: string;
  label: string;
  inherited_from: "group" | "global" | null;
  assignment: { revision: number; entries: RosterEntry[]; issues: RosterIssue[] } | null;
  status: string;
  repair: string | null;
  editor_capability_id: string | null;
  /** The revision a write to THIS row presents (tombstones included). */
  expected_revision: number;
}

export interface RosterTask {
  id: string;
  label: string;
  group: { id: string; label: string };
  /** The task has its own exact row (not inherited from its group/default). */
  has_override: boolean;
  /** The task's own engines (its exact row), when it has one. */
  entries?: RosterEntry[];
}

export interface Roster {
  rows: RosterRow[];
  tasks: RosterTask[];
}

function decodeEntry(raw: Record<string, unknown>): RosterEntry {
  return {
    profile_id: String(raw.profile_id ?? ""),
    profile_revision: typeof raw.profile_revision === "number" ? raw.profile_revision : 0,
    label: String(raw.label ?? ""),
    boundary: String(raw.boundary ?? "unknown"),
    readiness: String(raw.readiness ?? "unknown"),
  };
}

function decodeRow(raw: Record<string, unknown>): RosterRow {
  const assignment = raw.assignment as Record<string, unknown> | null | undefined;
  const inherited = raw.inherited_from;
  return {
    id: String(raw.id ?? ""),
    label: String(raw.label ?? ""),
    inherited_from: inherited === "group" || inherited === "global" ? inherited : null,
    assignment: assignment
      ? {
          revision: typeof assignment.revision === "number" ? assignment.revision : 0,
          entries: Array.isArray(assignment.entries)
            ? (assignment.entries as Record<string, unknown>[]).map(decodeEntry)
            : [],
          issues: Array.isArray(assignment.issues) ? (assignment.issues as RosterIssue[]) : [],
        }
      : null,
    status: String(raw.status ?? "no_assignment"),
    repair: typeof raw.repair === "string" ? raw.repair : null,
    editor_capability_id:
      typeof raw.editor_capability_id === "string" ? raw.editor_capability_id : null,
    expected_revision: typeof raw.expected_revision === "number" ? raw.expected_revision : 0,
  };
}

export async function readRoster(): Promise<Roster> {
  const raw = await apiFetch<Record<string, unknown>>("/api/inference/assignments");
  const rows = Array.isArray(raw.rows) ? (raw.rows as Record<string, unknown>[]).map(decodeRow) : [];
  const tasks = Array.isArray(raw.task_overrides)
    ? (raw.task_overrides as Record<string, unknown>[]).map((task) => {
        const group = (task.group ?? {}) as Record<string, unknown>;
        const effective = (task.effective ?? {}) as Record<string, unknown>;
        const assignment = (effective.assignment ?? null) as Record<string, unknown> | null;
        const own = effective.inherited_from === "capability" && assignment && Array.isArray(assignment.entries)
          ? (assignment.entries as Record<string, unknown>[]).map(decodeEntry)
          : undefined;
        return {
          id: String(task.id ?? ""),
          label: String(task.label ?? ""),
          group: { id: String(group.id ?? ""), label: String(group.label ?? "") },
          has_override: task.has_override === true,
          ...(own?.length ? { entries: own } : {}),
        };
      })
    : [];
  return { rows, tasks };
}

/* ── detection (GET /api/concierge/detect), with the Runs on fields ── */

export interface GroupFit {
  state: string;
  blocked?: string[];
}

/** Betterment E2: an agent engine's spend limit and its reported cost. */
export interface AgentSpend {
  /** The limit per run in US dollars; null = No limit. */
  limitUsd: number | null;
  /** The CLI stops a run at the limit itself (Claude Code); Codex cannot. */
  canLimit: boolean;
  /** The CLI reports what a run cost. */
  reportsCost: boolean;
  todayUsd: number;
  weekUsd: number;
}

/** Programs PG21: a Claude Code or Codex engine's usage-limit notice. Verified:
 *  the screen watcher read a real stop on this desk (its time, the reset it
 *  named). Documented: only the harness's documented wording is known. */
export interface LimitNotice {
  verified: boolean;
  /** The notice: its shape (times and dates replaced) or the documented line. */
  notice: string;
  stoppedAt: string | null;
  resetsAt: string | null;
}

export interface RunsOnEngine extends Engine {
  /** The machine has it; the library does not (one verb: Use it). */
  found?: boolean;
  /** Betterment E2: the agent CLI preset (`claude`, `codex`). */
  agentPreset?: string;
  /** yes · no (its last run said so) · unknown (try once) · not_read. */
  signedIn?: string;
  /** The vendor word on the egress chip (ANTHROPIC). */
  vendor?: string;
  /** Betterment E7: `private_network` for pi on his LAN model, else `cloud`. */
  vendorScope?: string;
  /** The model the agent engine asks for (`default` = the CLI's own). */
  model?: string;
  /** W1-TRUTH: an endpoint engine's model id (meta under its name). */
  modelId?: string;
  spend?: AgentSpend;
  limitNotice?: LimitNotice;
  /** The host a preset's file comes from. */
  downloadHost?: string;
  /** The authority's answer per group (PHILO-16 C, concierge detect route). */
  fits?: Record<string, GroupFit>;
  audioCapable?: boolean;
}

/** Betterment E4: a catalog preset on a service tile (shown on top of the picker). */
export interface ServicePreset {
  id: string;
  label: string;
  summary: string;
  model: string;
  contextTokens: number | null;
}

/** Betterment E4: a named service on the Add an engine tiles. */
export interface ServiceTile {
  id: string;
  name: string;
  baseUrl: string;
  host: string;
  presets: ServicePreset[];
}

/** Betterment E4: an agent preset on the *An agent on this Mac* tile. */
export interface AgentTile {
  preset: string;
  name: string;
  vendor: string;
  /** Betterment E7: `private_network` for pi on his LAN model, else `cloud`. */
  vendorScope: string;
  installed: boolean;
  added: boolean;
  /** The one-line install command, for a CLI that is not on this Mac. */
  install: string;
}

export interface Detection {
  engines: RunsOnEngine[];
  services?: ServiceTile[];
  agents?: AgentTile[];
  hardware: { capability?: { apple_silicon?: boolean; ram_gb?: number; total_memory_bytes?: number } };
  checkedAt: string;
  repairs: Repair[];
  summaryAssignment: SummaryAssignment | null;
}

function str(value: unknown): string | undefined {
  return typeof value === "string" && value ? value : undefined;
}

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function decodeEngine(raw: Record<string, unknown>): RunsOnEngine {
  const fits: Record<string, GroupFit> = {};
  if (raw.fits && typeof raw.fits === "object") {
    for (const [group, value] of Object.entries(raw.fits as Record<string, unknown>)) {
      const fit = (value ?? {}) as Record<string, unknown>;
      fits[group] = {
        state: String(fit.state ?? "UNKNOWN"),
        blocked: Array.isArray(fit.blocked) ? fit.blocked.map(String) : undefined,
      };
    }
  }
  return {
    id: String(raw.id ?? ""),
    kind: (str(raw.kind) ?? "local") as Engine["kind"],
    name: String(raw.name ?? ""),
    host: String(raw.host ?? ""),
    state: (str(raw.state) ?? "UNKNOWN") as Engine["state"],
    latencyMs: num(raw.latencyMs),
    sizeBytes: num(raw.sizeBytes),
    runtimeToken: str(raw.runtimeToken) ?? null,
    quantToken: str(raw.quantToken) ?? null,
    visionToken: str(raw.visionToken) ?? null,
    legacyLabel: str(raw.legacyLabel),
    keySet: typeof raw.keySet === "boolean" ? raw.keySet : undefined,
    profileId: str(raw.profileId),
    profileRevision: typeof raw.profileRevision === "number" ? raw.profileRevision : undefined,
    presetId: str(raw.presetId),
    installed: typeof raw.installed === "boolean" ? raw.installed : undefined,
    path: str(raw.path),
    baseUrl: str(raw.baseUrl),
    found: raw.found === true,
    downloadHost: str(raw.downloadHost),
    fits: Object.keys(fits).length ? fits : undefined,
    audioCapable: raw.audioCapable === true,
    agentPreset: str(raw.agentPreset),
    signedIn: str(raw.signedIn),
    vendor: str(raw.vendor),
    vendorScope: str(raw.vendorScope),
    model: str(raw.model),
    modelId: str(raw.modelId),
    spend: decodeSpend(raw.spend),
    limitNotice: decodeLimitNotice(raw.limitNotice),
  };
}

function decodeLimitNotice(raw: unknown): LimitNotice | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const row = raw as Record<string, unknown>;
  return {
    verified: row.verified === true,
    notice: String(row.notice ?? ""),
    stoppedAt: str(row.stoppedAt) ?? null,
    resetsAt: str(row.resetsAt) ?? null,
  };
}

function decodeSpend(raw: unknown): AgentSpend | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const row = raw as Record<string, unknown>;
  return {
    limitUsd: num(row.limitUsd),
    canLimit: row.canLimit === true,
    reportsCost: row.reportsCost === true,
    todayUsd: num(row.todayUsd) ?? 0,
    weekUsd: num(row.weekUsd) ?? 0,
  };
}

function decodeRepair(raw: Record<string, unknown>): Repair {
  const groups = Array.isArray(raw.groups) ? raw.groups.map(String) : [];
  return {
    id: String(raw.id ?? ""),
    token: String(raw.token ?? "") as Repair["token"],
    subject: String(raw.subject ?? ""),
    host: String(raw.host ?? ""),
    scope: raw.scope === "cloud" ? "cloud" : "local",
    groups,
    groupLabels: Array.isArray(raw.groupLabels) ? raw.groupLabels.map(String) : groups,
    verb: String(raw.verb ?? ""),
    control: String(raw.control ?? "engine_picker") as Repair["control"],
    engineId: String(raw.engineId ?? ""),
    presetId: String(raw.presetId ?? ""),
    baseUrl: String(raw.baseUrl ?? ""),
    detail: String(raw.detail ?? ""),
  };
}

function decodeSummary(raw: unknown): SummaryAssignment | null {
  if (!raw || typeof raw !== "object") return null;
  const row = raw as Record<string, unknown>;
  const status = String(row.status ?? "unassigned");
  return {
    capabilityId: String(row.capabilityId ?? ""),
    status:
      status === "assigned" || status === "attention" || status === "off" ? status : "unassigned",
    assignmentRevision: typeof row.assignmentRevision === "number" ? row.assignmentRevision : 0,
    profileId: str(row.profileId) ?? null,
    profileRevision: typeof row.profileRevision === "number" ? row.profileRevision : null,
    label: str(row.label) ?? null,
    boundary: str(row.boundary) ?? null,
    readiness: str(row.readiness) ?? null,
  };
}

function decodeService(raw: Record<string, unknown>): ServiceTile {
  return {
    id: String(raw.id ?? ""),
    name: String(raw.name ?? ""),
    baseUrl: String(raw.baseUrl ?? ""),
    host: String(raw.host ?? ""),
    presets: Array.isArray(raw.presets)
      ? (raw.presets as Record<string, unknown>[]).map((preset) => ({
          id: String(preset.id ?? ""),
          label: String(preset.label ?? ""),
          summary: String(preset.summary ?? ""),
          model: String(preset.model ?? ""),
          contextTokens: num(preset.contextTokens),
        }))
      : [],
  };
}

function decodeAgent(raw: Record<string, unknown>): AgentTile {
  return {
    preset: String(raw.preset ?? ""),
    name: String(raw.name ?? ""),
    vendor: String(raw.vendor ?? ""),
    vendorScope: String(raw.vendorScope ?? "cloud"),
    installed: raw.installed === true,
    added: raw.added === true,
    install: String(raw.install ?? ""),
  };
}

/** `fresh`: every endpoint is checked now (Check all, Try again); without it
 *  the hub answers an endpoint that does not answer from its last check. */
export async function readDetection(fresh = false): Promise<Detection> {
  const raw = await apiFetch<Record<string, unknown>>(fresh ? "/api/concierge/detect?fresh=1" : "/api/concierge/detect");
  return {
    engines: Array.isArray(raw.engines)
      ? (raw.engines as Record<string, unknown>[]).map(decodeEngine)
      : [],
    services: Array.isArray(raw.services) ? (raw.services as Record<string, unknown>[]).map(decodeService) : [],
    agents: Array.isArray(raw.agents) ? (raw.agents as Record<string, unknown>[]).map(decodeAgent) : [],
    hardware: (raw.hardware ?? {}) as Detection["hardware"],
    checkedAt: String(raw.checkedAt ?? ""),
    repairs: Array.isArray(raw.repairs)
      ? (raw.repairs as Record<string, unknown>[]).map(decodeRepair)
      : [],
    summaryAssignment: decodeSummary(raw.summaryAssignment),
  };
}

export interface LanDiscovery {
  engines: RunsOnEngine[];
  checkedAt: string;
  partial: boolean;
  unavailable: boolean;
  reason?: string;
  hostsChecked: number;
}

export async function discoverLan(): Promise<LanDiscovery> {
  const raw = await apiFetch<Record<string, unknown>>("/api/concierge/discover-lan", {
    method: "POST",
    json: {},
  });
  return {
    engines: Array.isArray(raw.engines)
      ? (raw.engines as Record<string, unknown>[]).map(decodeEngine)
      : [],
    checkedAt: String(raw.checkedAt ?? ""),
    partial: raw.partial === true,
    unavailable: raw.unavailable === true,
    reason: str(raw.reason),
    hostsChecked: typeof raw.hostsChecked === "number" ? raw.hostsChecked : 0,
  };
}

/* ── writes ── */

export type AssignmentScope =
  | { kind: "global" }
  | { kind: "group"; group_id: string }
  /** Betterment E5: one job everywhere (`capability:<cap>`). */
  | { kind: "capability"; capability_id: string };

/** Betterment E5: one row of What runs where, as the hub's assignment
 *  editor decides it (`POST /api/inference/assignments/editor`). */
export interface EditorCandidate {
  profileId: string;
  profileRevision: number;
  label: string;
  boundary: string;
  readiness: string;
  /** compatible · savable_with_repair */
  status: string;
}

export interface RowEditor {
  /** The revision a write to this row presents. */
  baseRevision: number;
  /** The row's own first engine (null: it follows another row). */
  own: { profileId: string; profileRevision: number; label: string } | null;
  /** The engine the job runs on now, and the row it comes from. */
  effective: { profileId: string; label: string; inheritedFrom: string } | null;
  candidates: EditorCandidate[];
}

function firstEntry(raw: unknown): Record<string, unknown> | null {
  const projection = (raw ?? null) as Record<string, unknown> | null;
  const entries = projection && Array.isArray(projection.entries) ? (projection.entries as Record<string, unknown>[]) : [];
  return entries[0] ?? null;
}

export async function readEditor(scope: AssignmentScope, capabilityId: string): Promise<RowEditor> {
  const raw = await apiFetch<Record<string, unknown>>("/api/inference/assignments/editor", {
    method: "POST",
    json: { scope, capability_id: capabilityId },
  });
  const own = firstEntry(raw.configured_assignment);
  const effective = (raw.effective ?? {}) as Record<string, unknown>;
  const lead = effective.status === "no_assignment" ? null : firstEntry(effective.assignment);
  return {
    baseRevision: typeof raw.draft_base_revision === "number" ? raw.draft_base_revision : 0,
    own: own
      ? { profileId: String(own.profile_id ?? ""), profileRevision: Number(own.profile_revision ?? 0), label: String(own.label ?? "") }
      : null,
    effective: lead
      ? { profileId: String(lead.profile_id ?? ""), label: String(lead.label ?? ""), inheritedFrom: String(effective.inherited_from ?? "") }
      : null,
    candidates: Array.isArray(raw.candidates)
      ? (raw.candidates as Record<string, unknown>[]).map((c) => ({
          profileId: String(c.profile_id ?? ""),
          profileRevision: Number(c.profile_revision ?? 0),
          label: String(c.label ?? ""),
          boundary: String(c.boundary ?? ""),
          readiness: String(c.readiness ?? ""),
          status: String(c.status ?? ""),
        }))
      : [],
  };
}

export function newCommandId(prefix: string): string {
  const entropy =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID().replace(/-/g, "").slice(0, 12)
      : Math.random().toString(36).slice(2, 14);
  return `${prefix}-${Date.now()}-${entropy}`;
}

/** One drop: the job's whole chain, against the revision the roster read. */
export async function writeChain(args: {
  scope: AssignmentScope;
  expectedRevision: number;
  entries: Array<{ profile_id: string; profile_revision?: number }>;
}): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>("/api/inference/assignments/set", {
    method: "POST",
    json: {
      command_id: newCommandId("runson-set"),
      expected_revision: args.expectedRevision,
      scope: args.scope,
      entries: args.entries.map((entry) =>
        entry.profile_revision && entry.profile_revision > 0
          ? { profile_id: entry.profile_id, profile_revision: entry.profile_revision }
          : { profile_id: entry.profile_id },
      ),
    },
  });
}

/** Betterment E2: add (or change) an agent CLI engine. The same profile id
 *  with its current revision changes the spend limit in place. */
export async function connectCliEngine(draft: {
  preset: string;
  profileId: string;
  expectedProfileRevision: number;
  label?: string;
  model?: string;
  spendLimitUsd?: number | null;
}): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>("/api/inference/model-library/connect-cli-engine", {
    method: "POST",
    json: {
      draft: {
        request_id: newCommandId("runson-agent"),
        profile_id: draft.profileId,
        expected_profile_revision: draft.expectedProfileRevision,
        preset: draft.preset,
        ...(draft.label ? { label: draft.label } : {}),
        ...(draft.model ? { model: draft.model } : {}),
        ...(draft.spendLimitUsd != null ? { spend_limit_usd: draft.spendLimitUsd } : {}),
      },
    },
  });
}

/** Undo of a first patch: the row goes back to following its parent. */
export async function clearChain(args: {
  scope: AssignmentScope | { kind: "capability"; capability_id: string };
  capabilityId: string;
  expectedRevision: number;
}): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>("/api/inference/assignments/clear", {
    method: "POST",
    json: {
      command_id: newCommandId("runson-clear"),
      expected_revision: args.expectedRevision,
      scope: args.scope,
      capability_id: args.capabilityId,
    },
  });
}

/* ── the download bar (GET /api/inference/acquisitions/{job}) ── */

export interface Acquisition {
  state: string;
  percent: number;
  /** The hub's failure code (`model_download_network`), kept, never dropped. */
  error: string | null;
}

export async function readAcquisition(jobId: string): Promise<Acquisition> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/api/inference/acquisitions/${encodeURIComponent(jobId)}`,
  );
  const row = (raw.acquisition ?? {}) as Record<string, unknown>;
  const total = num(row.bytes_total) ?? 0;
  const got = Math.max(num(row.verified_bytes) ?? 0, num(row.transport_bytes) ?? 0);
  const state = String(row.state ?? "indeterminate");
  const failure = row.error && typeof row.error === "object" ? (row.error as Record<string, unknown>) : null;
  return {
    state,
    percent: state === "ready" ? 100 : total > 0 ? Math.min(100, (got / total) * 100) : 0,
    error: failure && typeof failure.code === "string" ? failure.code : null,
  };
}

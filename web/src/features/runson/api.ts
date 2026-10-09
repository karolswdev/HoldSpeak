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
        return {
          id: String(task.id ?? ""),
          label: String(task.label ?? ""),
          group: { id: String(group.id ?? ""), label: String(group.label ?? "") },
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

export interface RunsOnEngine extends Engine {
  /** The machine has it; the library does not (one verb: Use it). */
  found?: boolean;
  /** The host a preset's file comes from. */
  downloadHost?: string;
  /** The authority's answer per group (PHILO-16 C, concierge detect route). */
  fits?: Record<string, GroupFit>;
  audioCapable?: boolean;
}

export interface Detection {
  engines: RunsOnEngine[];
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

export async function readDetection(): Promise<Detection> {
  const raw = await apiFetch<Record<string, unknown>>("/api/concierge/detect");
  return {
    engines: Array.isArray(raw.engines)
      ? (raw.engines as Record<string, unknown>[]).map(decodeEngine)
      : [],
    hardware: (raw.hardware ?? {}) as Detection["hardware"],
    checkedAt: String(raw.checkedAt ?? ""),
    repairs: Array.isArray(raw.repairs)
      ? (raw.repairs as Record<string, unknown>[]).map(decodeRepair)
      : [],
    summaryAssignment: decodeSummary(raw.summaryAssignment),
  };
}

/* ── writes ── */

export type AssignmentScope = { kind: "global" } | { kind: "group"; group_id: string };

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
}

export async function readAcquisition(jobId: string): Promise<Acquisition> {
  const raw = await apiFetch<Record<string, unknown>>(
    `/api/inference/acquisitions/${encodeURIComponent(jobId)}`,
  );
  const row = (raw.acquisition ?? {}) as Record<string, unknown>;
  const total = num(row.bytes_total) ?? 0;
  const got = Math.max(num(row.verified_bytes) ?? 0, num(row.transport_bytes) ?? 0);
  const state = String(row.state ?? "indeterminate");
  return {
    state,
    percent: state === "ready" ? 100 : total > 0 ? Math.min(100, (got / total) * 100) : 0,
  };
}

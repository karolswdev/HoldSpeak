// PHILO-16 (C) — Runs on, as data: the roster and the detection become the
// board's jobs, engines and wires. Pure; the controller and the tests share it.

import type { Repair } from "../concierge/api";
import type { Detection, Roster, RosterEntry, RosterRow, RunsOnEngine } from "./api";
import { stateWord, type StateWord } from "./stateWord";

/** The default job's board id; the roster calls it `global`. */
export const DEFAULT_JOB = "default";
export const SPEECH_JOB = "speech_recognition";
export const MEETINGS_JOB = "meetings";
export const THOUGHTS_JOB = "thoughts_notes";

/** The canvas order; the Default for AI work closes the column. */
export const JOB_ORDER = [
  SPEECH_JOB,
  "writing_dictation",
  THOUGHTS_JOB,
  MEETINGS_JOB,
  "agents_tools",
  "background",
  DEFAULT_JOB,
] as const;

const JOB_NAMES: Record<string, string> = {
  [SPEECH_JOB]: "Speech",
  [DEFAULT_JOB]: "Default for AI work",
};

export function rosterId(job: string): string {
  return job === DEFAULT_JOB ? "global" : job;
}

export function jobOf(rowId: string): string {
  return rowId === "global" ? DEFAULT_JOB : rowId;
}

/** A caller's scope, as the job it asks about (or null: no job). Accepts a
 *  job id, `group:<id>`, a task id (`meeting.deferred_analysis`), and the
 *  meeting-path blocker keys (`speech`, `summary`). */
export function jobForScope(scope: string | undefined | null, roster: Roster | null): string | null {
  const value = String(scope ?? "").trim();
  if (!value) return null;
  const bare = value.startsWith("group:") ? value.slice("group:".length) : value;
  if ((JOB_ORDER as readonly string[]).includes(bare)) return bare;
  if (bare === "global") return DEFAULT_JOB;
  if (bare === "speech") return SPEECH_JOB;
  if (bare === "summary" || bare === "summaries") return MEETINGS_JOB;
  const task = roster?.tasks.find((t) => t.id === bare || `capability:${t.id}` === bare);
  return task ? task.group.id : null;
}

export interface BoardEngine {
  /** The board key: the model record when there is one, else detection's id. */
  key: string;
  detectId?: string;
  profileId?: string;
  profileRevision?: number;
  name: string;
  kind: "local" | "lan" | "cloud" | "preset";
  host: string;
  emblem: "MAC" | "LAN" | "API";
  /** The raw state (detection's, or the binding's readiness). */
  state: string;
  latencyMs?: number | null;
  sizeBytes?: number | null;
  tokens: string[];
  audio: boolean;
  fits?: RunsOnEngine["fits"];
  found: boolean;
  baseUrl?: string;
  model?: string;
  presetId?: string;
  downloadHost?: string;
  keySet?: boolean;
}

export function emblemFor(kind: string, boundary?: string): "MAC" | "LAN" | "API" {
  if (kind === "cloud" || boundary === "cloud") return "API";
  if (kind === "lan" || boundary === "private_network" || boundary === "lan" || boundary === "mesh") return "LAN";
  return "MAC";
}

/** Off this machine: a probe there waits for the owner's press (Article III). */
export function offMachine(engine: BoardEngine): boolean {
  return engine.emblem !== "MAC";
}

/** The host an egress chip names for one engine. */
export function hostLabel(engine: BoardEngine): string {
  if (engine.emblem === "MAC") return "THIS DEVICE";
  return (engine.host || "NOT SET").toUpperCase();
}

export function sizeToken(bytes: number | null | undefined): string | null {
  if (bytes == null || bytes <= 0) return null;
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
  if (bytes >= 1e6) return `${Math.round(bytes / 1e6)} MB`;
  return `${Math.round(bytes / 1e3)} KB`;
}

function engineTokens(e: RunsOnEngine): string[] {
  const tokens: string[] = [];
  const size = sizeToken(e.sizeBytes);
  if (size) tokens.push(size);
  if (e.kind === "lan" && e.host) tokens.push(e.host);
  if (e.runtimeToken) tokens.push(e.runtimeToken);
  if (e.quantToken) tokens.push(e.quantToken);
  if (e.visionToken) tokens.push(e.visionToken);
  if (e.audioCapable) tokens.push("SPEECH");
  // PHILO-15 05: a provider with no execution adapter says so on its plate.
  if (e.state === "NOT_SUPPORTED") tokens.push("NOT SUPPORTED YET");
  if (e.kind === "cloud") {
    tokens.push(e.keySet ? "KEY SET" : "NO KEY");
    tokens.push("$");
  }
  if (e.kind === "preset") tokens.push("NOT DOWNLOADED");
  if (typeof e.latencyMs === "number") tokens.push(`${e.latencyMs} MS`);
  return tokens;
}

/** Every engine the board draws, keyed by model record. The roster's own
 *  entries come first (painted before detection lands); detection fills
 *  them in and adds the rest. */
export function buildEngines(roster: Roster | null, detection: Detection | null): BoardEngine[] {
  const out = new Map<string, BoardEngine>();
  // Before detection names an engine's modalities, an engine wired to
  // Speech's own chain is a speech engine (the roster only holds it there
  // because the authority admitted it for audio).
  const speech = new Set(
    ownEntries(roster?.rows.find((r) => r.id === SPEECH_JOB)).map((e) => e.profile_id),
  );
  for (const row of roster?.rows ?? []) {
    for (const entry of row.assignment?.entries ?? []) {
      if (!entry.profile_id || out.has(entry.profile_id)) continue;
      const emblem = emblemFor("", entry.boundary);
      out.set(entry.profile_id, {
        key: entry.profile_id,
        profileId: entry.profile_id,
        profileRevision: entry.profile_revision,
        name: entry.label || entry.profile_id,
        kind: emblem === "API" ? "cloud" : emblem === "LAN" ? "lan" : "local",
        host: "",
        emblem,
        state: entry.readiness,
        tokens: speech.has(entry.profile_id) ? ["SPEECH"] : [],
        audio: speech.has(entry.profile_id),
        found: false,
      });
    }
  }
  for (const e of detection?.engines ?? []) {
    const key = e.profileId || e.id;
    const prior = out.get(key);
    out.set(key, {
      key,
      detectId: e.id,
      profileId: e.profileId,
      profileRevision: e.profileRevision ?? prior?.profileRevision,
      name: e.name || prior?.name || key,
      kind: e.kind,
      host: e.host,
      emblem: emblemFor(e.kind),
      state: e.state,
      latencyMs: e.latencyMs,
      sizeBytes: e.sizeBytes,
      tokens: engineTokens(e),
      audio: Boolean(e.audioCapable) || Boolean(prior?.audio),
      fits: e.fits,
      found: Boolean(e.found),
      baseUrl: e.baseUrl,
      model: e.legacyLabel,
      presetId: e.presetId,
      downloadHost: e.downloadHost,
      keySet: e.keySet,
    });
  }
  return [...out.values()];
}

/** The engines column: what the owner has (a model record) and the
 *  downloads; FOUND is the rest that one verb can accept. */
export function splitEngines(engines: BoardEngine[]): { have: BoardEngine[]; found: BoardEngine[] } {
  const have = engines.filter((e) => !e.found);
  // A found row must carry its one verb; only an address can be accepted
  // through the Model Library from here (define-endpoint).
  const found = engines.filter((e) => e.found && Boolean(e.baseUrl));
  return { have, found };
}

/** The job's own chain (empty when it follows its parent). */
export function ownEntries(row: RosterRow | undefined): RosterEntry[] {
  if (!row || !row.assignment) return [];
  if (row.id === "global") return row.assignment.entries;
  return row.inherited_from === "group" ? row.assignment.entries : [];
}

export interface Accept {
  ok: boolean;
  reason?: string;
}

/** May this engine run this job? The backend's fit decides; speech takes
 *  speech engines only. */
export function accepts(job: string, engine: BoardEngine | undefined): Accept {
  if (!engine) return { ok: false, reason: "NO ENGINE" };
  if (!engine.profileId) {
    return { ok: false, reason: engine.kind === "preset" ? "WAITS FOR DOWNLOAD" : "NO MODEL RECORD" };
  }
  if (engine.state === "NOT_SUPPORTED") return { ok: false, reason: "NOT SUPPORTED" };
  // A pre-library endpoint record names no immutable revision: the
  // assignment authority would refuse the write, so the board does first.
  if (!engine.profileRevision && !engine.profileId.startsWith("legacy-")) {
    return { ok: false, reason: "NO MODEL RECORD" };
  }
  if (job === SPEECH_JOB) return engine.audio ? { ok: true } : { ok: false, reason: "SPEECH ENGINES ONLY" };
  if (engine.audio) return { ok: false, reason: "TEXT ENGINES ONLY" };
  if (job === DEFAULT_JOB) return { ok: true };
  const fit = engine.fits?.[job];
  if (fit && stateWord(fit.state) === "BROKEN") {
    const blocked = (fit.blocked ?? []).map((name) => name.toUpperCase());
    return { ok: false, reason: blocked.length ? `WITHOUT ${blocked.join(" · ")}` : "INCOMPATIBLE" };
  }
  return { ok: true };
}

/** The work this engine cannot do in this job, as tokens. */
export function limitTokens(job: string, engine: BoardEngine | undefined): string[] {
  const fit = engine?.fits?.[job];
  if (!fit || stateWord(fit.state) !== "LIMITED") return [];
  return (fit.blocked ?? []).map((name) => `WITHOUT ${name.toUpperCase()}`);
}

/** One job's word: the roster's status, the binding of its first engine,
 *  the authority's fit, and any repair that names the job. */
export function jobState(
  job: string,
  row: RosterRow | undefined,
  engines: BoardEngine[],
  repairs: Repair[],
): StateWord {
  const repair = repairs.find((r) => r.groups.includes(job));
  if (repair) return repair.token === "MODEL FILE MISSING" && repair.presetId ? "WAITING" : "BROKEN";
  if (!row || !row.assignment) return "OFF";
  const first = row.assignment.entries[0];
  if (first && (first.readiness === "missing" || first.readiness === "disabled")) {
    return stateWord(first.readiness);
  }
  const engine = engines.find((e) => e.profileId === first?.profile_id);
  const fit = job === DEFAULT_JOB ? undefined : engine?.fits?.[job];
  if (fit) {
    const word = stateWord(fit.state);
    if (word === "BROKEN" || word === "LIMITED") return word;
  }
  return stateWord(row.status);
}

/** The job's tasks, as one token line. */
export function taskLine(job: string, roster: Roster | null, row: RosterRow | undefined): string {
  if (job === DEFAULT_JOB) return "EVERY JOB WITHOUT ITS OWN WIRE";
  const labels = (roster?.tasks ?? []).filter((t) => t.group.id === job).map((t) => t.label);
  const parts = labels.slice(0, 2);
  if (labels.length > 2) parts.push(`${labels.length} TASKS`);
  if (job === SPEECH_JOB) parts.push("THIS DEVICE ONLY");
  if (row && row.inherited_from === "global") parts.push("FOLLOWS DEFAULT");
  return parts.join(" · ").toUpperCase();
}

// PHILO-16 (C) — Runs on, as data: the roster and the detection become the
// board's jobs, engines and wires. Pure; the controller and the tests share it.

import type { Repair } from "../concierge/api";
import { hostPlace } from "../../desk/surface/egress";
import type { AgentSpend, Detection, LimitNotice, Roster, RosterEntry, RosterRow, RunsOnEngine } from "./api";
import { stateWord, type StateWord } from "./stateWord";

/** The default job's board id; the roster calls it `global`. */
export const DEFAULT_JOB = "default";
export const SPEECH_JOB = "speech_recognition";
export const MEETINGS_JOB = "meetings";
export const THOUGHTS_JOB = "thoughts_notes";

/** The canvas order; Everything else (the default) closes the column. */
export const JOB_ORDER = [
  SPEECH_JOB,
  "writing_dictation",
  THOUGHTS_JOB,
  MEETINGS_JOB,
  "agents_tools",
  "background",
  DEFAULT_JOB,
] as const;

/** PHILO-17 (U16): a job is named for what the owner gets, never for the
 *  internal group (`Writing & dictation`, `Default for AI work`). */
export const JOB_NAMES: Record<string, string> = {
  [SPEECH_JOB]: "Speech to text",
  writing_dictation: "Dictation clean-up",
  [THOUGHTS_JOB]: "Answers and notes",
  [MEETINGS_JOB]: "Meeting summaries",
  agents_tools: "Custom tasks",
  background: "Background work",
  [DEFAULT_JOB]: "Default engine",
};

/** One bounded sample through an actual task route. The default is not a task. */
export const JOB_PROBE_CAPABILITIES: Readonly<Record<string, string>> = {
  writing_dictation: "speech.rewrite",
  [THOUGHTS_JOB]: "ask.answer",
  [MEETINGS_JOB]: "meeting.deferred_analysis",
  agents_tools: "recipe.run",
  background: "background.rails_summary",
};

/** The job's outcome name; an unknown group keeps the roster's label. */
export function jobName(job: string, row?: { label?: string } | null): string {
  return JOB_NAMES[job] ?? (row?.label || job);
}

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
  kind: "local" | "lan" | "cloud" | "preset" | "agent";
  host: string;
  /** CLI: an agent CLI on this Mac; its prompt goes to its vendor. */
  emblem: "MAC" | "LAN" | "API" | "CLI";
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
  /** W1-TRUTH: the model id the server serves (meta, never the name). */
  modelId?: string;
  presetId?: string;
  downloadHost?: string;
  keySet?: boolean;
  /** Betterment E2: an agent CLI engine (or a found one). */
  agentPreset?: string;
  agentModel?: string;
  signedIn?: string;
  vendor?: string;
  vendorScope?: string;
  installed?: boolean;
  spend?: AgentSpend;
  /** Programs PG21: Claude Code and Codex only. */
  limitNotice?: LimitNotice;
}

/** Betterment E7: an agent's egress chip. pi on his LAN model reads like any
 *  LAN host (`192.168.1.43 · LAN`, the local tone); every other agent names
 *  its vendor in the cloud tone. */
export function agentChip(vendor: string, vendorScope?: string): { label: string; scope: "local" | "cloud" } {
  return vendorScope === "private_network" ? { label: `${vendor} · LAN`, scope: "local" } : { label: vendor, scope: "cloud" };
}

export function emblemFor(kind: string, boundary?: string): BoardEngine["emblem"] {
  if (kind === "agent") return "CLI";
  if (kind === "cloud" || boundary === "cloud") return "API";
  if (kind === "lan" || boundary === "private_network" || boundary === "lan" || boundary === "mesh") return "LAN";
  return "MAC";
}

/** Off this machine: disclose its destination before the owner's press. */
export function offMachine(engine: BoardEngine): boolean {
  return enginePlace(engine).place !== "mac";
}

/** Where one engine runs, from the one host helper (desk/surface/egress.ts
 *  hostPlace): its address when it has one, else its host, read with its
 *  emblem's kind. */
export function enginePlace(engine: BoardEngine): ReturnType<typeof hostPlace> {
  const kind = engine.emblem === "API" || engine.emblem === "CLI" ? "cloud" : engine.emblem === "LAN" ? "lan" : "local";
  return hostPlace(engine.baseUrl || engine.host, kind);
}

/** The host an egress chip names for one engine. */
export function hostLabel(engine: BoardEngine): string {
  const place = enginePlace(engine);
  if (place.place === "mac") return "THIS DEVICE";
  return place.host || engine.host || "NOT SET";
}

/** The summary route while it is not known yet: still being read, or the
 *  read failed. The lead never guesses it from the Meetings wire. */
export type LeadUnknown = "checking" | "unknown";

/** PHILO-17 (U16, Astra r1 M2, r2 M1): the engine a job's lead names.
 *  Meeting summaries run on the `meeting.deferred_analysis` capability's
 *  own effective assignment (concierge_service.py
 *  summary_assignment_projection), which can differ from the Meetings
 *  group's wire; until detection says it, the lead says `checking` (or
 *  `unknown` when the read failed). Every other job runs on its group's
 *  first engine. `null`: summaries are off. */
export function leadEngine(
  job: string,
  groupEngine: BoardEngine | undefined,
  detection: Pick<Detection, "summaryAssignment"> | null | undefined,
  engines: BoardEngine[],
  detectionFailed = false,
): BoardEngine | undefined | null | LeadUnknown {
  if (job !== MEETINGS_JOB) return groupEngine;
  if (!detection) return detectionFailed ? "unknown" : "checking";
  const summary = detection.summaryAssignment;
  if (!summary) return "unknown";
  if (summary.status === "off") return null;
  if (summary.status !== "assigned" || !summary.profileId) return undefined;
  const known = engines.find((e) => e.profileId === summary.profileId && !e.found);
  if (known) return known;
  const emblem = emblemFor("", summary.boundary ?? undefined);
  return {
    key: summary.profileId,
    profileId: summary.profileId,
    profileRevision: summary.profileRevision ?? undefined,
    name: summary.label || summary.profileId,
    kind: emblem === "API" ? "cloud" : emblem === "LAN" ? "lan" : "local",
    host: "",
    emblem,
    state: summary.readiness ?? "unknown",
    tokens: [],
    audio: false,
    found: false,
  };
}

/** PHILO-17 (U16): the job card's lead, in plain words: what the owner
 *  gets and where it runs (`Meeting summaries → Qwen 27B · on this Mac`). */
export function leadLine(
  job: string,
  row: { label?: string } | null | undefined,
  engine: BoardEngine | undefined | null | LeadUnknown,
): string {
  const name = jobName(job, row);
  if (engine === "checking") return `${name} → checking…`;
  if (engine === "unknown") return `${name} → not known`;
  if (engine === null) return `${name} → off`;
  if (!engine) return `${name} → no engine`;
  return `${name} → ${engine.name} · on ${enginePlace(engine).words}`;
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
  // Betterment E2: an agent engine says what stops it, in words.
  if (e.kind === "agent" && !e.found) {
    if (e.installed === false) tokens.push("NOT INSTALLED");
    else if (e.signedIn === "no") tokens.push("NOT SIGNED IN");
  }
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
  // A job's own engine and a task's own engine (an exact row, such as
  // Answers set in What runs where): a known engine is never hidden.
  const chains = [
    ...(roster?.rows ?? []).map((row) => row.assignment?.entries ?? []),
    ...(roster?.tasks ?? []).map((task) => task.entries ?? []),
  ];
  for (const entries of chains) {
    for (const entry of entries) {
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
      modelId: e.modelId,
      presetId: e.presetId,
      downloadHost: e.downloadHost,
      keySet: e.keySet,
      agentPreset: e.agentPreset,
      agentModel: e.model,
      signedIn: e.signedIn,
      vendor: e.vendor,
      vendorScope: e.vendorScope,
      installed: e.installed,
      spend: e.spend,
      limitNotice: e.limitNotice,
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
  // Betterment E2: a found agent CLI is accepted with connect-cli-engine.
  const found = engines.filter((e) => e.found && (Boolean(e.baseUrl) || Boolean(e.agentPreset)));
  return { have, found };
}

/** Betterment E2: the found agent's name with its sign-in, in words
 *  (`Claude Code · signed in`). The hub never says "no" before a run: a
 *  sign-in it cannot read is "not known", and Add tries it once. */
export function foundAgentName(engine: BoardEngine): string {
  return `${engine.name} · ${engine.signedIn === "yes" ? "signed in" : "sign-in not known"}`;
}

/** A moment as the faces' clock words, with its weekday (`Tue 14:02`). */
function dayClock(iso: string | null): string {
  if (!iso) return "";
  const moment = new Date(iso);
  if (Number.isNaN(moment.getTime())) return "";
  const day = moment.toLocaleDateString("en-US", { weekday: "short" });
  const clock = `${String(moment.getHours()).padStart(2, "0")}:${String(moment.getMinutes()).padStart(2, "0")}`;
  return `${day} ${clock}`;
}

/** Programs PG21: the Limit notice fact in words. Verified: `Verified · last
 *  stop Tue 14:02 · resets Fri 02:00` (`reset` once that moment is past);
 *  documented: `Documented · never read here`. */
export function limitNoticeWords(notice: LimitNotice, now: Date = new Date()): string {
  if (!notice.verified) return "Documented · never read here";
  const parts = ["Verified"];
  const stop = dayClock(notice.stoppedAt);
  if (stop) parts.push(`last stop ${stop}`);
  const reset = dayClock(notice.resetsAt);
  if (reset) parts.push(`${new Date(notice.resetsAt as string) > now ? "resets" : "reset"} ${reset}`);
  return parts.join(" · ");
}

/** US dollars for a cost or a limit (`$0.25`; a cost under a cent says so). */
export function usd(value: number): string {
  if (value > 0 && value < 0.005) return "under $0.01";
  return `$${value.toFixed(2)}`;
}

/** The unfolded agent row's cost words: today and this week, never a zero
 *  counter (UX canon A8). */
export function costTokens(spend: AgentSpend | undefined, label: string): string[] {
  if (!spend) return [];
  if (!spend.reportsCost) return [`${label} REPORTS NO COST`];
  if (!(spend.weekUsd > 0)) return ["NOTHING SPENT THIS WEEK"];
  const tokens: string[] = [];
  if (spend.todayUsd > 0) tokens.push(`TODAY ${usd(spend.todayUsd)}`);
  tokens.push(`THIS WEEK ${usd(spend.weekUsd)}`);
  return tokens;
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
    const blocked = fit.blocked ?? [];
    return { ok: false, reason: blocked.length ? `WITHOUT ${blocked.join(" · ")}` : "INCOMPATIBLE" };
  }
  return { ok: true };
}

/** The work this engine cannot do in this job, as tokens. */
export function limitTokens(job: string, engine: BoardEngine | undefined): string[] {
  const fit = engine?.fits?.[job];
  if (!fit || stateWord(fit.state) !== "LIMITED") return [];
  return (fit.blocked ?? []).map((name) => `WITHOUT ${name}`);
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

/** The job's tasks, by name: the card's details (its title), never its
 *  face. */
export function taskDetail(job: string, roster: Roster | null): string {
  if (job === DEFAULT_JOB) return "Every job with no engine of its own";
  return (roster?.tasks ?? []).filter((t) => t.group.id === job).map((t) => t.label).join(" · ");
}

/** The token line under the lead: only what the lead cannot say. */
export function taskLine(job: string, _roster: Roster | null, row: RosterRow | undefined): string {
  const parts: string[] = [];
  if (row && row.inherited_from === "global") parts.push("Uses default engine");
  return parts.join(" · ");
}

/** W1-TRUTH: how old the last check is, in quiet words: `checked just now`,
 *  `checked 4 min ago`, `checked 2 h ago`. An unreadable time says nothing. */
export function checkedWords(iso: string | null | undefined, now: number = Date.now()): string | null {
  const at = iso ? Date.parse(iso) : NaN;
  if (!Number.isFinite(at)) return null;
  const minutes = Math.floor(Math.max(0, now - at) / 60_000);
  if (minutes < 1) return "checked just now";
  if (minutes < 60) return `checked ${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `checked ${hours} h ago`;
  return `checked ${Math.floor(hours / 24)} d ago`;
}

/** A check older than this reads as stale (quiet, never a warning). */
export const STALE_CHECK_MS = 10 * 60_000;

/** True when the engine's server did not answer the last check. */
export function notAnswering(engine: BoardEngine | undefined): boolean {
  return String(engine?.state ?? "").trim().toUpperCase() === "UNREACHABLE";
}

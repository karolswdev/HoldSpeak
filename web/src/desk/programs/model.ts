/* Programs (design §4, §9): what a state looks like. Pure: the tones, the
 * station track's stations, the band order of the Programs list, the
 * words a row shows. Every word a face draws goes through `stateWords`. */
import type { ChipState } from "../surface";
import type { ObjectTone } from "../surface/objects/kinds";
import { stateWords } from "../surface/words";
import type { ProgramState, ProgramStep, ProgramSummary, Requirement, RequirementKind, RequirementsMet, StationKey, StepState } from "./types";

export type Tone = ObjectTone | "idle";

/** The ladder, low to high. */
export const CONTROLS: readonly { value: "secure" | "normal" | "yolo"; word: string; line: string }[] = [
  { value: "secure", word: "Secure", line: "You press every merge and every finding" },
  { value: "normal", word: "Normal", line: "HoldSpeak merges green and reviewed steps; core questions come to you" },
  { value: "yolo", word: "YOLO", line: "HoldSpeak decides all it can; only core questions come to you" },
];

/** A control wire value (the Program's, or the desk policy's `safe` /
 *  `neutral`) as its ladder word. */
export function controlValue(raw: string | null | undefined): "secure" | "normal" | "yolo" {
  const value = String(raw ?? "").trim().toLowerCase();
  if (value === "safe" || value === "secure" || value === "owner") return "secure";
  if (value === "yolo" || value === "delegate") return "yolo";
  return "normal";
}

export function controlWord(raw: string | null | undefined): string {
  return CONTROLS.find((row) => row.value === controlValue(raw))!.word;
}

/** The six stations of a step (BRIEF · WORK · CHECK · REVIEW · PR · MERGE). */
export const STATIONS: readonly StationKey[] = ["brief", "work", "check", "review", "pr", "merge"];
export const STATION_WORDS: Record<StationKey, string> = {
  brief: "Brief", work: "Work", check: "Check", review: "Review", pr: "PR", merge: "Merge", file: "File",
};

/** A step state's tone: blue while an agent works, ember when it waits on
 *  him, red for a red check or a failure, green when merged. */
export function stepTone(state: StepState | string): Tone {
  switch (state) {
    case "briefed": case "working": case "checking": case "review": case "pr_open": return "info";
    case "waiting": case "findings": case "merge_ask": return "ask";
    case "check_failed": case "failed": return "fail";
    // PG19: the agent stopped at its usage limit.
    case "limited": return "warn";
    case "merged": case "done": return "ok";
    default: return "idle";
  }
}

/** Live states: the lit station breathes (the RecordOrb's breath). */
export function stepBreathes(state: StepState | string): boolean {
  return ["briefed", "working", "checking", "review", "waiting", "findings", "merge_ask", "pr_open"].includes(state);
}

/** The Program's StateChip (canvas kit list: active = Your turn, working =
 *  Running, idle = Drafting / Parked, success = Done). */
export function programChip(state: ProgramState | string): ChipState {
  switch (state) {
    case "waiting": return "active";
    case "running": return "working";
    case "done": return "success";
    case "failed": return "failure";
    default: return "idle";
  }
}

export function programTone(state: ProgramState | string): Tone {
  switch (state) {
    case "waiting": return "ask";
    case "running": return "info";
    case "done": return "ok";
    case "failed": return "fail";
    default: return "idle";
  }
}

/** The step's StateChip at 393 (the track folds to a chip). */
export function stepChip(state: StepState | string): ChipState {
  const tone = stepTone(state);
  if (tone === "ask") return "active";
  if (tone === "info") return "working";
  if (tone === "ok") return "success";
  if (tone === "fail") return "failure";
  if (tone === "warn") return "warning";
  return "idle";
}

/** Waiting first (DeckHand): the bands of the Programs list, in order. */
export const BANDS: readonly { state: ProgramState; word: string }[] = [
  { state: "waiting", word: "Your turn" },
  { state: "failed", word: "Failed" },
  { state: "running", word: "Running" },
  { state: "drafting", word: "Drafting" },
  { state: "done", word: "Done" },
  { state: "parked", word: "Parked" },
];

export function banded(programs: readonly ProgramSummary[]): { state: ProgramState; word: string; rows: ProgramSummary[] }[] {
  return BANDS.map((band) => ({
    ...band,
    rows: programs
      .filter((row) => row.state === band.state)
      .sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at))),
  })).filter((band) => band.rows.length > 0);
}

/** A step's state word, with the PR number on a merge or a merged step
 *  (`Merged #1585`, `Merge? #1591`) and the race's count. */
export function stepWord(step: ProgramStep): string {
  const base = stateWords(step.state_word || step.state);
  // A race of 2 is the step's own agent and one contender.
  if (step.contenders?.length) return `Race of ${Math.max(step.race || 0, step.contenders.length + 1)}`;
  if ((step.state === "merged" || step.state === "merge_ask") && step.pr?.number) return `${base} #${step.pr.number}`;
  if (step.state === "check_failed") return `${base} · log`;
  // PG-IMPORT IMP2: how the lane ended, beside the state ("Parked · interrupted").
  if ((step.state === "parked" || step.state === "failed") && (step.ending === "failed" || step.ending === "interrupted")) {
    return `${base} · ${step.ending}`;
  }
  // PG19: the row keeps "Limited until 14:00"; the rest ("continuing in
  // Codex") is the Your turn row's and the word's hover.
  if (step.state === "limited") return base.split(" · ")[0];
  if (step.gate.review === "person" && (step.state === "pr_open" || step.state === "review") && step.for_person) {
    return `Waits for ${step.for_person}`;
  }
  return base;
}

/** Seconds → `41 min`, `2 h`, `1 h 04`, `3 days`. */
export function durationWords(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds) || seconds < 0) return "";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 1) return "now";
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    const rest = minutes % 60;
    return rest ? `${hours} h ${String(rest).padStart(2, "0")}` : `${hours} h`;
  }
  const days = Math.floor(hours / 24);
  return `${days} ${days === 1 ? "day" : "days"}`;
}

/** `after 4, 5` (`after 1 to 19` for a run). */
/** PG17: `29 Oct 14:02`, the local day and time of a merge. */
export function mergedWords(at: string | null | undefined): string {
  const ms = Date.parse(String(at ?? ""));
  if (!Number.isFinite(ms)) return "";
  const when = new Date(ms);
  const day = when.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  const time = when.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
  return `${day} ${time}`;
}

/** PG17: `Imported from PR #1584` for a step that merged before the Program. */
export function importedWords(step: Pick<ProgramStep, "history">): string {
  return step.history ? `Imported from PR #${step.history.pr_number}` : "";
}

export function afterWords(after: readonly number[]): string {
  if (!after.length) return "";
  const sorted = [...after].sort((a, b) => a - b);
  const run = sorted.length > 2 && sorted.every((value, index) => index === 0 || value === sorted[index - 1] + 1);
  return run ? `after ${sorted[0]} to ${sorted[sorted.length - 1]}` : `after ${sorted.join(", ")}`;
}

/** The agent's name with its engine for pi (`pi · qwen3.8-27b on karol`). */
export function runsOnWords(agent: string, engine: ProgramStep["engine"]): string {
  if (!engine) return agent;
  if (engine.assignment) return `${agent} · the desk's assignment`;
  return `${agent} · ${engine.label || engine.short}`;
}

/** The sprite agent key of a profile (`claude`, `codex`, `pi`). */
export function agentKey(profile: string | null | undefined, agent?: string): string {
  const value = `${profile ?? ""} ${agent ?? ""}`.toLowerCase();
  if (value.includes("codex")) return "codex";
  if (value.includes("pi")) return "pi";
  return "claude";
}

export type StationState = "passed" | "current" | "ahead" | "skip";

export interface StationView {
  key: StationKey;
  word: string;
  /** The quiet word after it (`green`, `passed`, `#1591`, `log`). */
  sub?: string;
  state: StationState;
  tone: Tone;
  /** The current station breathes. */
  live?: boolean;
  /** A person's review: her name (the station draws her portrait). */
  person?: string;
}

/** PG-LANG JRN8: an audit step (its track ends at FILE): it reads its
 *  surface and writes nothing. */
export function isAuditStep(step: Pick<ProgramStep, "stations">): boolean {
  return Boolean(step.stations?.includes("file"));
}

/** An audit step's surface, in place of Owns (`Reads web/src/desk/notes/`). */
export function readsWords(step: Pick<ProgramStep, "owns">): string {
  return step.owns?.length ? `Reads ${step.owns.join(", ")}` : "";
}

/** The stations of one step. */
export function stationsOf(step: ProgramStep): StationView[] {
  const lit = step.station;
  const tone = stepTone(step.state);
  const finished = step.state === "merged" || step.state === "done";
  // The hub's track: the six, or an audit's BRIEF · WORK · REVIEW · FILE
  // (its findings are read, so its Review is never skipped).
  const keys = step.stations?.length ? step.stations : STATIONS;
  const audit = isAuditStep(step);
  return keys.map((key, index) => {
    let state: StationState = index < lit ? "passed" : index === lit ? "current" : "ahead";
    if (finished) state = index === keys.length - 1 ? "current" : "passed";
    if (key === "review" && !audit && step.gate.review === "none" && state !== "current") state = "skip";
    if (key === "merge" && step.gate.merge === "none" && state !== "current") state = "skip";
    let sub: string | undefined;
    if (key === "check" && step.check.verdict) sub = step.check.verdict === "green" ? "green" : "log";
    if (key === "review" && step.review.verdict) sub = step.review.verdict === "pass" ? "passed" : "findings";
    if (key === "pr" && step.pr?.number) sub = `#${step.pr.number}`;
    if (key === "merge" && finished && step.pr?.number) sub = `#${step.pr.number}`;
    const person = key === "review" && step.gate.review === "person" && step.for_person ? step.for_person : undefined;
    return {
      key, word: STATION_WORDS[key], sub, state, person,
      tone: state === "current" ? tone : state === "passed" ? "idle" : "idle",
      live: state === "current" && stepBreathes(step.state),
    };
  });
}

/* ── PG-REQ (PROGRAMS-REQUIREMENTS-2026-10-31 §4, §7, §9) ── */

/** A requirement's tone: Met ok, Unmet fail, Checking info, his word ask
 *  (ember), Not yet and Waived idle (Not yet draws a hollow dot). */
export function requirementTone(row: Pick<Requirement, "state" | "running" | "state_word" | "kind">): Tone {
  if (row.state === "met") return "ok";
  if (row.state === "unmet") return "fail";
  if (row.running) return "info";
  if (row.state === "not_yet" && /waits for you/i.test(row.state_word)) return "ask";
  return "idle";
}

/** His word on a requirement (`Checking` while it is judged). */
export function requirementWord(row: Pick<Requirement, "state_word" | "running">): string {
  return row.running ? "Checking" : stateWords(row.state_word || "Not yet");
}

/** An every-step parent's state, read off its copies: Unmet when one is,
 *  Met when every copy is Met or Waived, else the parent's own. */
export function everyStepState(row: Requirement): { state: Requirement["state"]; word: string; met: number; total: number } {
  const copies = row.steps ?? [];
  const met = copies.filter((copy) => copy.state === "met" || copy.state === "waived").length;
  if (row.state === "waived") return { state: "waived", word: "Waived", met, total: copies.length };
  if (copies.some((copy) => copy.state === "unmet")) return { state: "unmet", word: "Unmet", met, total: copies.length };
  if (copies.length && met === copies.length) return { state: "met", word: "Met", met, total: copies.length };
  return { state: row.state, word: requirementWord(row), met, total: copies.length };
}

/** The Programs list's Met cell (§7): `4 of 5 met`, `7 requirements` while
 *  none is judged (never `0 of 7 met`), nothing when there is none. */
export function metWords(met: RequirementsMet | null | undefined): { text: string; tone: Tone | null; all: boolean; title?: string } | null {
  if (!met || !met.total) return null;
  const waived = met.waived ? `${met.waived} waived` : undefined;
  if (!met.met && !met.unmet) {
    return { text: `${met.total} ${met.total === 1 ? "requirement" : "requirements"}`, tone: met.his ? "ask" : null, all: false };
  }
  const all = met.met >= met.total;
  return { text: `${met.met} of ${met.total} met`, tone: all ? "ok" : met.unmet || met.his ? "ask" : null, all, title: waived };
}

/** A step's Met cell on the board (§7): `2 of 3`, `3 to meet` while none of
 *  its three is met, nothing when it has none. */
export function stepMetWords(met: RequirementsMet | null | undefined, his = false): { text: string; tone: Tone | null; all: boolean } | null {
  if (!met || !met.total) return null;
  const all = met.met >= met.total;
  const tone: Tone | null = all ? "ok" : met.unmet ? "fail" : his || met.his ? "ask" : null;
  if (!met.met) return { text: `${met.total} to meet`, tone, all: false };
  return { text: `${met.met} of ${met.total}`, tone, all };
}

/** The kind by rule as he types (design §4, decision 5; the hub's
 *  `program_requirements.guess`): backticks are a Check with that command;
 *  "<name> window at 393|1440" is a Shot; anything else a Review. Your
 *  word is only his choice. */
export function guessKind(text: string): { kind: RequirementKind; command?: string; case?: string; width?: number } {
  const command = /`([^`]+)`/.exec(text);
  if (command && command[1].trim()) return { kind: "check", command: command[1].trim() };
  const shot = /\b([A-Za-z][\w-]*)\s+window\s+at\s+(393|1440)\b/i.exec(text);
  if (shot) return { kind: "shot", case: shot[1].toLowerCase(), width: Number(shot[2]) };
  return { kind: "review" };
}

export const KIND_WORDS: Record<RequirementKind, string> = { check: "Check", review: "Review", shot: "Shot", word: "Your word" };

/** Find a program (§7): every typed word is in the row's `search_words`. */
export function matchesFind(row: Pick<ProgramSummary, "search_words" | "title">, query: string): boolean {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return true;
  const hay = `${row.search_words ?? ""} ${row.title}`.toLowerCase();
  return words.every((word) => hay.includes(word));
}

/** The persons a summary names (the step persons and the Program's own). */
export function personsOf(row: Pick<ProgramSummary, "persons" | "for_person">): { id: string; name: string }[] {
  const out = new Map<string, string>();
  for (const person of row.persons ?? []) out.set(person.id, person.name);
  if (row.for_person) out.set(row.for_person.id, row.for_person.name);
  return [...out].map(([id, name]) => ({ id, name }));
}

const STATE_RANK: Record<string, number> = { waiting: 0, failed: 1, running: 2, drafting: 3, done: 4, parked: 5 };

/** Group by project (§7): bands by project name, "No project" last; inside
 *  a band the worst state first, then the most recently changed. */
export function bandedByProject(programs: readonly ProgramSummary[]): { key: string; word: string; rows: ProgramSummary[] }[] {
  const bands = new Map<string, { key: string; word: string; rows: ProgramSummary[] }>();
  for (const row of programs) {
    const key = row.project?.id ?? row.project_id ?? "";
    const word = row.project?.name ?? (key ? key : "No project");
    if (!bands.has(key)) bands.set(key, { key, word, rows: [] });
    bands.get(key)!.rows.push(row);
  }
  for (const band of bands.values()) {
    band.rows.sort((a, b) => (STATE_RANK[a.state] ?? 9) - (STATE_RANK[b.state] ?? 9)
      || String(b.updated_at).localeCompare(String(a.updated_at)));
  }
  return [...bands.values()].sort((a, b) => (a.key ? 0 : 1) - (b.key ? 0 : 1) || a.word.localeCompare(b.word));
}

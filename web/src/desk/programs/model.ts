/* Programs (design §4, §9): what a state looks like. Pure: the tones, the
 * station track's stations, the band order of the Programs list, the
 * words a row shows. Every word a face draws goes through `stateWords`. */
import type { ChipState } from "../surface";
import type { ObjectTone } from "../surface/objects/kinds";
import { stateWords } from "../surface/words";
import type { ProgramState, ProgramStep, ProgramSummary, StationKey, StepState } from "./types";

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
  brief: "Brief", work: "Work", check: "Check", review: "Review", pr: "PR", merge: "Merge",
};

/** A step state's tone: blue while an agent works, ember when it waits on
 *  him, red for a red check or a failure, green when merged. */
export function stepTone(state: StepState | string): Tone {
  switch (state) {
    case "briefed": case "working": case "checking": case "review": case "pr_open": return "info";
    case "waiting": case "findings": case "merge_ask": return "ask";
    case "check_failed": case "failed": return "fail";
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
  if (step.contenders?.length) return `Race of ${step.contenders.length}`;
  if ((step.state === "merged" || step.state === "merge_ask") && step.pr?.number) return `${base} #${step.pr.number}`;
  if (step.state === "check_failed") return `${base} · log`;
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

/** `after 4, 5` (`after 1–19` for a run). */
export function afterWords(after: readonly number[]): string {
  if (!after.length) return "";
  const sorted = [...after].sort((a, b) => a - b);
  const run = sorted.length > 2 && sorted.every((value, index) => index === 0 || value === sorted[index - 1] + 1);
  return run ? `after ${sorted[0]}–${sorted[sorted.length - 1]}` : `after ${sorted.join(", ")}`;
}

/** The agent's name with its engine for pi (`pi · qwen3.8-27b on karol`). */
export function runsOnWords(agent: string, engine: ProgramStep["engine"]): string {
  if (!engine) return agent;
  if (engine.assignment) return `${agent} · the desk's assignment`;
  return `${agent} · ${engine.short || engine.label}`;
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

/** The stations of one step. */
export function stationsOf(step: ProgramStep): StationView[] {
  const lit = step.station;
  const tone = stepTone(step.state);
  const finished = step.state === "merged" || step.state === "done";
  return STATIONS.map((key, index) => {
    let state: StationState = index < lit ? "passed" : index === lit ? "current" : "ahead";
    if (finished) state = index === STATIONS.length - 1 ? "current" : "passed";
    if (key === "review" && step.gate.review === "none" && state !== "current") state = "skip";
    if (key === "merge" && step.gate.merge === "none" && state !== "current") state = "skip";
    let sub: string | undefined;
    if (key === "check" && step.check.verdict) sub = step.check.verdict === "green" ? "green" : "log";
    if (key === "review" && step.review.verdict) sub = step.review.verdict === "pass" ? "passed" : "findings";
    if (key === "pr" && step.pr?.number) sub = `#${step.pr.number}`;
    if (key === "merge" && step.state === "merged" && step.pr?.number) sub = `#${step.pr.number}`;
    const person = key === "review" && step.gate.review === "person" && step.for_person ? step.for_person : undefined;
    return {
      key, word: STATION_WORDS[key], sub, state, person,
      tone: state === "current" ? tone : state === "passed" ? "idle" : "idle",
      live: state === "current" && stepBreathes(step.state),
    };
  });
}

/** Betterment A3 — the automation window's words (DESIGN §4, "The words").
 *
 * Pure helpers: what the hub sends (WorkbenchService._wb_payload and
 * automation_runs.results_of) becomes the sentence and the result lines.
 * The user never sees a cron string, a ref or an internal id. */
import type { WorkbenchDetail } from "../../detail-types";
import { wireClock, wireDate } from "../../surface/format";
import type { AgentUse } from "../../used";

/** One run's result (`automation_runs.results_of`). */
export interface AutomationResult {
  item_id: string;
  title: string;
  status: string;
  artifact_id: string | null;
  new: boolean;
  error: string | null;
  text: string | null;
  completed_at: string | null;
  seconds: number | null;
  model: string;
  boundary: string;
  note_id: string | null;
  /** The cost an agent CLI engine reported for this result's runs (Engines
   *  E2, linked by item in MCP M2); null when none was reported. */
  cost_usd?: number | null;
  /** What the run's agent looked at, wrote and prepared (MCP M2); null when
   *  it touched nothing. */
  used?: AgentUse | null;
}

export type { UsedRow, AgentUse as AutomationUse } from "../../used";
export { sendWords, usedWords } from "../../used";

export interface AutomationSource {
  ref: string;
  kind: string;
  label: string;
  missing: boolean;
}

/** An event the hub can deliver (When > When something happens). */
export interface AutomationEventChoice {
  id: string;
  words: string;
  /** What the event needs from him (a GitHub repository). */
  needs: string;
  /** Betterment A5: the thing that happened, as the About line reads it. */
  subject?: string;
  event_pattern: string;
}

export interface AutomationDetail extends WorkbenchDetail {
  /** Betterment AG14: Do kind and installed agent hand configuration. */
  do_kind?: "run" | "hand_to_agent" | string;
  agent_profile?: string;
  agent_profile_label?: string | null;
  agent_binding?: {
    profile_id?: string | null;
    label?: string | null;
    executable?: string | null;
  } | null;
  review_by?: string;
  assignment_summary?: WorkbenchDetail["assignment_summary"] & {
    /** Betterment A4: the engine in use, and where its prompt goes. */
    profile_id?: string | null;
    boundary?: string | null;
    /** Betterment A10: an agent engine's vendor ("Anthropic"); absent otherwise. */
    vendor?: string | null;
  };
  /** Betterment A4: when the schedule fires next (only while it is on). */
  next_run_at?: string | null;
  /** Betterment A4: this automation's Spend limit per run; null = the engine's. */
  spend_limit_usd?: number | null;
  when_events?: AutomationEventChoice[];
  /** Betterment A7: a blank its starter could not guess, while it is open
   *  (`{ about: "which people?" }`). */
  blanks?: Record<string, string>;
  instruction?: string;
  instruction_shown?: string;
  instruction_from?: string;
  output_target?: string;
  results?: AutomationResult[];
  sources_shown?: AutomationSource[];
  event_starts?: Array<{ id?: string; name: string; enabled: boolean; event_pattern?: string }>;
}

const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

function clock(minute: string, hour: string): string | null {
  if (!/^\d+$/.test(minute) || !/^\d+$/.test(hour)) return null;
  const h = Number(hour);
  const m = Number(minute);
  if (h > 23 || m > 59) return null;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function dayList(field: string): string | null {
  const parts = field.split(",");
  const names: string[] = [];
  for (const part of parts) {
    if (!/^\d$/.test(part)) return null;
    const day = DAYS[Number(part) % 7];
    if (!day) return null;
    names.push(day);
  }
  if (names.length === 1) return names[0];
  return `${names.slice(0, -1).join(", ")} and ${names.at(-1)}`;
}

/** A stored schedule in plain words. Never the cron string: a schedule the
 *  words do not cover reads "On a set schedule". */
export function scheduleWords(cron: string | null | undefined): string | null {
  const value = String(cron ?? "").trim();
  if (!value) return null;
  const f = value.split(/\s+/);
  if (f.length !== 5) return "On a set schedule";
  const [minute, hour, dom, month, dow] = f;
  if (value === "* * * * *") return "Every minute";
  if (dom !== "*" || month !== "*") return "On a set schedule";
  if (hour === "*" && /^\d+$/.test(minute) && dow === "*") return "Every hour";
  const at = clock(minute, hour);
  if (!at) return "On a set schedule";
  if (dow === "*") return `Every day at ${at}`;
  if (dow === "1-5") return `Every weekday at ${at}`;
  const days = dayList(dow);
  return days ? `Every ${days} at ${at}` : "On a set schedule";
}

/** The When line: the schedule, the events that start it, or the press. */
export function whenWords(detail: AutomationDetail): string {
  const schedule = scheduleWords(detail.schedule);
  // Betterment A4: an event start reads in the When editor's words.
  const words = new Map((detail.when_events ?? []).map((c) => [c.event_pattern, c.words]));
  const events = (detail.event_starts ?? [])
    .map((e) => words.get(e.event_pattern ?? "") ?? e.name).filter(Boolean);
  const parts = [schedule, ...events].filter(Boolean) as string[];
  return parts.length ? parts.join(" · ") : "Only when I press Run now";
}

/** Betterment A5: an event start's About line, the thing that happened
 *  ("the review request that came in"); null when no event starts it. */
export function eventSubjectWords(detail: AutomationDetail): string | null {
  const starts = detail.event_starts ?? [];
  if (!starts.length) return null;
  const subjects = new Map((detail.when_events ?? []).map((c) => [c.event_pattern, c.subject]));
  const words = starts.map((e) => subjects.get(e.event_pattern ?? "") || "the event that happened");
  return [...new Set(words)].join(" · ");
}

/** On means a start is armed: the schedule, or an event start. */
export function hasStarts(detail: AutomationDetail): boolean {
  return Boolean(scheduleWords(detail.schedule)) || (detail.event_starts ?? []).length > 0;
}

export function isOn(detail: AutomationDetail): boolean {
  return (Boolean(detail.schedule) && detail.schedule_enabled)
    || (detail.event_starts ?? []).some((e) => e.enabled);
}

const SHORT_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/** `Next: Fri 15:00` in the viewer's zone; nothing when it is not on. */
export function nextWords(value: string | null | undefined): string | null {
  const date = wireDate(value);
  if (!date) return null;
  return `Next: ${SHORT_DAYS[date.getDay()]} ${wireClock(date)}`;
}

/** The stored schedule as the When editor's picks; null when the pickers
 *  cannot show it (a cron that no picker makes). */
export interface SchedulePick {
  every: "day" | "weekday" | "week" | "hour";
  time: string;
  day: number | null;
}

export function schedulePick(cron: string | null | undefined): SchedulePick | null {
  const f = String(cron ?? "").trim().split(/\s+/);
  if (f.length !== 5) return null;
  const [minute, hour, dom, month, dow] = f;
  if (dom !== "*" || month !== "*") return null;
  if (hour === "*" && minute === "0" && dow === "*") return { every: "hour", time: "09:00", day: null };
  const time = clock(minute, hour);
  if (!time) return null;
  if (dow === "*") return { every: "day", time, day: null };
  if (dow === "1-5") return { every: "weekday", time, day: null };
  if (/^[0-6]$/.test(dow)) return { every: "week", time, day: Number(dow) };
  return null;
}

/** The lessons fold's token: words, never a bare count. */
export function lessonWords(count: number): string | undefined {
  if (count <= 0) return undefined;
  return count === 1 ? "1 lesson" : `${count} lessons`;
}

/** The Put it in line. A destination reads by its saved name (Betterment
 *  A6); it only prepares the send, so the words say he presses Send. */
export function putWords(target: string | null | undefined, destinationName?: string | null): string {
  const value = String(target ?? "inbox");
  if (value === "needs_you") return "Needs you";
  if (value === "today") return "Today";
  if (value.startsWith("destination:")) {
    const name = String(destinationName ?? "").trim();
    return name ? `${name} (you press Send)` : "A saved destination (you press Send)";
  }
  return "My Inbox";
}

export function engineWords(detail: AutomationDetail): string | null {
  if (detail.do_kind === "hand_to_agent") {
    if (!detail.agent_profile) return null;
    const label = detail.agent_profile_label || detail.agent_binding?.label || "";
    return label || detail.agent_profile;
  }
  const chain = detail.assignment_summary?.chain ?? [];
  return chain.length ? chain[0] : null;
}

/** A qualified ref or an internal id in an engine's answer: `note:abc123`,
 *  `artifact_7cbd3b862891`, `wbocc_…`. It is hidden from the reading. */
const INTERNAL_ID =
  /\s*[([]?\b(?:(?:note|meeting|artifact|decision|project|people|person|zone|drawer|workbench|item|thread|transcript):[A-Za-z0-9][\w-]{3,}|(?:artifact|wbocc|wbrun|wbi|note_result|op|rcpt)_[0-9a-f]{6,})\b[)\]]?/g;

export function withoutIds(text: string): string {
  return String(text ?? "").replace(INTERNAL_ID, "");
}

/** The one-line name of a result: its first heading or line, without marks. */
export function resultLine(result: AutomationResult): string {
  const text = withoutIds(result.text ?? "");
  const first = text.split("\n").map((l) => l.trim()).find(Boolean) ?? "";
  const plain = first.replace(/^#{1,6}\s+/, "").replace(/^[-*+]\s+/, "").replace(/[*_`]/g, "").trim();
  return plain || result.title;
}

/** `Sun 18 Oct, 09:27` in the viewer's zone. */
export function resultWhen(value: string | null | undefined): string {
  const date = wireDate(value);
  if (!date) return "";
  const day = date.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
  return `${day}, ${wireClock(date)}`;
}

/** `10 Oct`: fits the ledger's time slot (52 px). */
export function resultDay(value: string | null | undefined): string {
  const date = wireDate(value);
  if (!date) return "";
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export function secondsWords(seconds: number | null | undefined): string | null {
  if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds < 0) return null;
  if (seconds < 60) return `${Math.round(seconds)} s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return s ? `${m} min ${s} s` : `${m} min`;
}

export function costWords(cost: number | null | undefined): string | null {
  if (typeof cost !== "number" || !Number.isFinite(cost) || cost <= 0) return null;
  return cost < 0.01 ? "<$0.01" : `$${cost.toFixed(2)}`;
}

/** A failure in words. The hub stores the engine's own reason; a bare code
 *  or an empty reason reads as a plain sentence. */
export function failureWords(error: string | null | undefined): string {
  const text = withoutIds(String(error ?? "")).trim();
  if (!text || text.toLowerCase() === "failed") return "It stopped without a reason";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Betterment A9: an old queue automation's typed tasks (not its run
 *  occurrences, not parked), as results the window can show: a done task
 *  reads its answer, a failed one its reason, a waiting one its title. */
export function queueTasks(detail: AutomationDetail): AutomationResult[] {
  return (detail.items ?? [])
    .filter((item) => !item.parked && !(item as { context?: { occurrence?: unknown } }).context?.occurrence)
    .map((item) => {
      const failed = item.status === "failed";
      return {
        item_id: item.id,
        title: item.title,
        status: item.status,
        artifact_id: item.result_artifact_id,
        new: false,
        error: failed ? String(item.result ?? "").replace(/^Error: /, "") : null,
        text: item.status === "done" ? item.result : null,
        completed_at: item.completed_at,
        seconds: null,
        model: "",
        boundary: String(item.result_egress?.boundary ?? ""),
        note_id: null,
      };
    });
}

/** A task's state in words (its ledger meta). */
export function taskStateWords(status: string): string {
  if (status === "done") return "Done";
  if (status === "failed") return "Failed";
  if (status === "claimed") return "Working…";
  return "Waiting";
}

/** Betterment A9: the agent's prompt can become this automation's Do. */
export function canMakeOne(detail: AutomationDetail): boolean {
  return detail.instruction_from === "agent" && Boolean(String(detail.instruction_shown ?? "").trim());
}

/** An old queue automation: its Do comes from an agent and it holds typed
 *  tasks. The parked queue view stays reachable for it (RAW). */
export function isOldQueue(detail: AutomationDetail): boolean {
  if (detail.instruction_from === "automation") return false;
  return Boolean(detail.recipe_id) || (detail.items ?? []).length > (detail.results ?? []).length;
}

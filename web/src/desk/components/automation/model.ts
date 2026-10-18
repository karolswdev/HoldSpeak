/** Betterment A3 — the automation window's words (DESIGN §4, "The words").
 *
 * Pure helpers: what the hub sends (WorkbenchService._wb_payload and
 * automation_runs.results_of) becomes the sentence and the result lines.
 * The user never sees a cron string, a ref or an internal id. */
import type { WorkbenchDetail } from "../../detail-types";
import { wireClock, wireDate } from "../../surface/format";

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
  used?: AutomationUse | null;
}

/** One object a run's agent touched: its qualified ref, title and kind. */
export interface UsedRow {
  ref: string;
  label: string;
  kind?: string;
}

export interface AutomationUse {
  looked_at?: UsedRow[];
  /** `undo`: the run made it, so the desk's delete (with its Undo) takes it back. */
  wrote?: Array<UsedRow & { undo?: boolean }>;
  /** A send the agent prepared; he presses Send. */
  prepared?: Array<UsedRow & { send_id?: string; destination?: string }>;
}

const KIND_NOUNS: Record<string, [string, string]> = {
  meeting: ["meeting", "meetings"],
  note: ["note", "notes"],
  decision: ["decision", "decisions"],
  knowledge: ["knowledge base", "knowledge bases"],
  zone: ["zone", "zones"],
  sequence: ["sequence", "sequences"],
  workflow: ["workflow", "workflows"],
  project: ["project", "projects"],
  people: ["person", "people"],
  person: ["person", "people"],
  workbench: ["automation", "automations"],
  artifact: ["result", "results"],
};

/** `1 send`, `2 sends`. */
export function sendWords(n: number): string {
  return n === 1 ? "1 send" : `${n} sends`;
}

/** `3 meetings, 1 note`: the rows counted by kind, in first-seen order. */
export function usedWords(rows: UsedRow[]): string {
  const counts = new Map<string, number>();
  for (const row of rows) {
    const kind = row.kind || row.ref.split(":", 1)[0] || "";
    counts.set(kind, (counts.get(kind) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([kind, n]) => {
      const [one, many] = KIND_NOUNS[kind] ?? ["item", "items"];
      return `${n} ${n === 1 ? one : many}`;
    })
    .join(", ");
}

export interface AutomationSource {
  ref: string;
  kind: string;
  label: string;
  missing: boolean;
}

export interface AutomationDetail extends WorkbenchDetail {
  instruction?: string;
  instruction_shown?: string;
  instruction_from?: string;
  output_target?: string;
  results?: AutomationResult[];
  sources_shown?: AutomationSource[];
  event_starts?: Array<{ id?: string; name: string; enabled: boolean }>;
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
  const events = (detail.event_starts ?? []).map((e) => e.name).filter(Boolean);
  const parts = [schedule, ...events].filter(Boolean) as string[];
  return parts.length ? parts.join(" · ") : "Only when I press Run now";
}

/** On means a start is armed: the schedule, or an event start. */
export function hasStarts(detail: AutomationDetail): boolean {
  return Boolean(scheduleWords(detail.schedule)) || (detail.event_starts ?? []).length > 0;
}

export function isOn(detail: AutomationDetail): boolean {
  return (Boolean(detail.schedule) && detail.schedule_enabled)
    || (detail.event_starts ?? []).some((e) => e.enabled);
}

export function putWords(target: string | null | undefined): string {
  const value = String(target ?? "inbox");
  if (value === "needs_you") return "Needs you";
  if (value.startsWith("destination:")) return "A saved destination (you press Send)";
  return "My Inbox";
}

export function engineWords(detail: AutomationDetail): string | null {
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

/** An old queue automation: its Do comes from an agent and it holds typed
 *  tasks. The parked queue view stays reachable for it (RAW). */
export function isOldQueue(detail: AutomationDetail): boolean {
  if (detail.instruction_from === "automation") return false;
  return Boolean(detail.recipe_id) || (detail.items ?? []).length > (detail.results ?? []).length;
}

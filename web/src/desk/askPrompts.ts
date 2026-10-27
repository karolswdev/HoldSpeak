// Ask D1 (canvas ask-direction-2026-10-27, ratified 2026-10-27): what a
// fresh Ask offers, built in the client from reads the desk already makes.
// No hub endpoint suggests questions (the canvas's gap 4), so each prompt
// names the desk fact it came from. A press fills the composer and does not
// send (owner ruling 2026-10-21).
import { countWords } from "./surface/kit";
import { humanTime } from "./surface/format";

export interface AskPrompt {
  key: string;
  /** The question the press puts in the composer. */
  text: string;
  /** Where it comes from, quiet at the row's right (`14 in Needs you`). */
  source: string;
  /** The object kind whose glyph leads the row. */
  kind: "action" | "decision" | "person" | "meeting";
}

export interface AskPromptInputs {
  needsCount: number;
  decisions: ReadonlyArray<{ title: string; status?: string; tags?: readonly string[]; createdAt?: string; decidedAt?: string }>;
  /** People with something he owes them (`you_owe_count > 0`). */
  waiting: ReadonlyArray<{ name: string }>;
  meetingsThisWeek: number;
}

function firstName(name: string): string {
  return name.trim().split(/\s+/)[0] || name;
}

/** `Avery`, `Avery and Jordan`, `Avery, Jordan and Sam`, `Avery, Jordan and 2 more`. */
export function namesWords(names: readonly string[]): string {
  const first = names.map(firstName);
  if (first.length <= 1) return first[0] ?? "";
  if (first.length === 2) return `${first[0]} and ${first[1]}`;
  if (first.length === 3) return `${first[0]}, ${first[1]} and ${first[2]}`;
  return `${first[0]}, ${first[1]} and ${first.length - 2} more`;
}

/** The newest decision's topic: its first tag, else its own title. */
function decisionTopic(decision: AskPromptInputs["decisions"][number]): string {
  const tag = decision.tags?.find((t) => t.trim());
  return tag ? tag.trim() : `“${decision.title.trim()}”`;
}

const STATUS_WORD: Record<string, string> = {
  proposed: "Proposed",
  accepted: "Accepted",
  superseded: "Superseded",
  deprecated: "Deprecated",
};

/** At most three questions from this desk. "What needs my attention today?"
 *  is always first; the others appear only when the desk has the fact. */
export function deskPrompts(inputs: AskPromptInputs): AskPrompt[] {
  const out: AskPrompt[] = [{
    key: "needs",
    text: "What needs my attention today?",
    source: inputs.needsCount > 0 ? `${inputs.needsCount} in Needs you` : "",
    kind: "action",
  }];
  const newest = [...inputs.decisions]
    .filter((d) => d.title?.trim())
    .sort((a, b) => String(b.decidedAt || b.createdAt || "").localeCompare(String(a.decidedAt || a.createdAt || "")))[0];
  if (newest) {
    const when = newest.decidedAt || newest.createdAt;
    out.push({
      key: "decision",
      text: `What did we decide about ${decisionTopic(newest)}?`,
      source: [STATUS_WORD[String(newest.status)] ?? "Decision", when ? humanTime(when) : ""].filter(Boolean).join(", "),
      kind: "decision",
    });
  }
  if (inputs.waiting.length) {
    out.push({ key: "waiting", text: "Who is waiting on me?", source: namesWords(inputs.waiting.map((p) => p.name)), kind: "person" });
  }
  if (out.length < 3 && inputs.meetingsThisWeek > 0) {
    out.push({
      key: "week",
      text: "Summarize this week's meetings",
      source: countWords(inputs.meetingsThisWeek, "meeting") ?? "",
      kind: "meeting",
    });
  }
  return out.slice(0, 3);
}

/** What "My whole desk" covers, for the status bar:
 *  `My whole desk: 3 projects · 3 meetings this week · 4 people · 2 decisions`.
 *  A count of zero is not said (UX-CANON A.8). */
export function wholeDeskWords(
  counts: { projects: number; meetingsThisWeek: number; people: number; decisions: number },
  /** On a phone the bar is short: no lead words, no decisions. */
  short = false,
): string {
  const parts = [
    countWords(counts.projects, "project"),
    countWords(counts.meetingsThisWeek, "meeting this week", "meetings this week"),
    countWords(counts.people, "person", "people"),
    short ? null : countWords(counts.decisions, "decision"),
  ].filter(Boolean);
  if (short) return parts.join(" · ");
  return parts.length ? `My whole desk: ${parts.join(" · ")}` : "My whole desk";
}

/** What a chosen scope covers: `About 1 project · 1 note`. */
export function chosenScopeWords(refs: readonly string[]): string {
  const words: Record<string, [string, string]> = {
    project: ["project", "projects"], note: ["note", "notes"], meeting: ["meeting", "meetings"],
    people: ["person", "people"], person: ["person", "people"], decision: ["decision", "decisions"],
    directory: ["drawer", "drawers"], kb: ["drawer", "drawers"], meetings: ["set of meetings", "sets of meetings"],
  };
  const counts = new Map<string, number>();
  for (const ref of refs) {
    const kind = ref.split(":")[0];
    counts.set(kind, (counts.get(kind) ?? 0) + 1);
  }
  const parts = [...counts].map(([kind, n]) => {
    const [one, many] = words[kind] ?? ["item", "items"];
    return countWords(n, one, many);
  }).filter(Boolean);
  return parts.length ? `About ${parts.join(" · ")}` : "";
}

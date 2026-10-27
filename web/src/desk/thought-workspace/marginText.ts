/* Direction A (2026-10-27): the note's margin ties its rows to lines by the
 * text alone. The hub's found rows carry no position (noteOutcomes.ts), so a
 * row finds its line by matching its words in the note; a row with no match
 * stays in its place in the list. */
import { initialsOf } from "../surface/kit";

export interface LineRange {
  from: number;
  to: number;
}

const WORD = /[\p{L}\p{N}]+/gu;

function words(text: string): string[] {
  return (text.toLowerCase().match(WORD) ?? []).filter((word) => word.length > 2);
}

function lines(body: string): Array<LineRange & { text: string }> {
  const out: Array<LineRange & { text: string }> = [];
  let from = 0;
  for (const text of body.split("\n")) {
    out.push({ from, to: from + text.length, text });
    from += text.length + 1;
  }
  return out;
}

/** The line of the note that says `text`: the line that holds it, else the
 *  line that shares most of its words (at least 60 % of them). */
export function findLine(body: string, text: string): LineRange | null {
  const needle = text.trim().toLowerCase();
  if (!needle || !body) return null;
  const all = lines(body);
  const exact = all.find((line) => line.text.toLowerCase().includes(needle));
  if (exact) return { from: exact.from, to: exact.to };
  const want = words(needle);
  if (!want.length) return null;
  let best: { line: LineRange; score: number } | null = null;
  for (const line of all) {
    const have = new Set(words(line.text));
    if (!have.size) continue;
    const score = want.filter((word) => have.has(word)).length / want.length;
    if (score >= 0.6 && (!best || score > best.score)) best = { line: { from: line.from, to: line.to }, score };
  }
  return best?.line ?? null;
}

export interface DecisionLine extends LineRange {
  text: string;
  /** A `decision:<id>` link on the line, when the note has one. */
  recordId: string | null;
}

const DECISION = /^\s*(?:[-*+>]\s+)?(?:\*\*|__)?Decision(?:\*\*|__)?\s*:\s*(?:\*\*|__)?\s*(.+)$/i;
const DECISION_REF = /\]\((?:decision|decision_record):([^)\s]+)\)/i;
const LINK = /\[([^\]]*)\]\([^)]*\)/g;

/** The note's decision lines: each line that starts with "Decision:". */
export function decisionLines(body: string): DecisionLine[] {
  const out: DecisionLine[] = [];
  for (const line of lines(body)) {
    const match = DECISION.exec(line.text);
    if (!match) continue;
    const text = match[1].replace(LINK, "$1").replace(/\*\*|__/g, "").trim();
    if (!text) continue;
    out.push({ from: line.from, to: line.to, text, recordId: DECISION_REF.exec(line.text)?.[1] ?? null });
  }
  return out;
}

const MENTION = /(^|[^\p{L}\p{N}_])@([\p{Lu}][\p{L}\p{N}_-]*)/gu;
const PERSON_REF = /\]\((?:people|person):([^)\s]+)\)/gi;

/** The people the note names: each @Name and each People link, once. */
export function peopleNamed(body: string): number {
  const seen = new Set<string>();
  for (const match of body.matchAll(MENTION)) seen.add(`@${match[2].toLowerCase()}`);
  for (const match of body.matchAll(PERSON_REF)) seen.add(`ref:${match[1].toLowerCase()}`);
  return seen.size;
}

/** The owner's pill: "Me" stays "Me"; a name gives its initials (kit
 *  `initialsOf`). */
export function ownerInitials(owner: string): string {
  const name = owner.trim();
  if (!name || name.toLowerCase() === "me") return "Me";
  return initialsOf(name);
}

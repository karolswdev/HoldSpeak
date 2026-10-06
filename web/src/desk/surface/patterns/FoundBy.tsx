/** FoundBy — the retriever that found a memory hit, as one caption token.
 *
 *  ⌘K memory results, option B "Two-line hit" (canvas YDTpkaJqFs3hyrZ4g581Mx
 *  §3, owner ratified 2026-10-05). The word maps from the real
 *  `retrieval_origin` that `GET /api/memory/search` returns per hit
 *  (holdspeak/db/memory.py MemoryHit): a hit carries ONE origin, the first
 *  retriever that found it, so the row shows one token. An origin with no
 *  word (an `observation`, or one a later retriever adds) shows no token:
 *  never a guess.
 */
import { wireDate } from "../format";
import "./found-by.css";

export const FOUND_BY_WORD: Readonly<Record<string, string>> = {
  lexical: "KEYWORD",
  vector: "MEANING",
  time: "TIME",
  entity: "NAME",
  relationship: "LINK",
};

/** The FoundBy word of a `retrieval_origin`, or null when it has none. */
export function foundByWord(origin: unknown): string | null {
  return FOUND_BY_WORD[String(origin ?? "")] ?? null;
}

/** The day of a hit: `10-01` this year, `2025-10-01` another year; empty
 *  when the value is not a time. */
export function foundByDay(value: unknown, now: Date = new Date()): string {
  const date = wireDate(value);
  if (!date) return "";
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return date.getFullYear() === now.getFullYear()
    ? `${mm}-${dd}`
    : `${date.getFullYear()}-${mm}-${dd}`;
}

export function FoundBy({ origin, className }: { origin: unknown; className?: string }) {
  const word = foundByWord(origin);
  if (!word) return null;
  return (
    <span
      className={"surface-token surface-foundby" + (className ? ` ${className}` : "")}
      data-chip
      data-by={word}
    >
      {word}
    </span>
  );
}

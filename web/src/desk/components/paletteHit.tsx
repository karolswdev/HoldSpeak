// ⌘K memory results, option B "Two-line hit" (canvas YDTpkaJqFs3hyrZ4g581Mx
// §3, owner ratified 2026-10-05): under the hit's title, the snippet with
// the match marked, a FoundBy token and the day.
//
// The snippet is the REDACTED text `/api/memory/search` returns; nothing
// here reads the source again. A keyword snippet carries the server's own
// `<mark>` grammar. A snippet without it (a meaning hit, or a keyword
// snippet the server cut again because the source held a secret) marks the
// words of the question it holds. A `[redacted]` marker is never marked and
// never cut by a mark.
import { Fragment } from "react";
import { FoundBy, foundByDay, foundByWord } from "../surface/patterns/FoundBy";

export const REDACTED = "[redacted]";

export interface SnippetPart {
  text: string;
  mark?: boolean;
  redacted?: boolean;
}

const MARKED = /(<mark>[\s\S]*?<\/mark>)/i;

function splitRedacted(part: SnippetPart): SnippetPart[] {
  const out: SnippetPart[] = [];
  const pieces = part.text.split(REDACTED);
  pieces.forEach((piece, index) => {
    if (index > 0) out.push({ text: REDACTED, redacted: true });
    if (piece) out.push(part.mark ? { text: piece, mark: true } : { text: piece });
  });
  return out;
}

function questionTerms(query: string): string[] {
  const words = (query.toLocaleLowerCase().match(/[\p{L}\p{N}]+/gu) ?? []).filter((w) => w.length >= 2);
  return [...new Set(words)].sort((a, b) => b.length - a.length);
}

function markTerms(text: string, terms: string[]): SnippetPart[] {
  if (!terms.length) return [{ text }];
  const lower = text.toLocaleLowerCase();
  const out: SnippetPart[] = [];
  let at = 0;
  let from = 0;
  while (from < text.length) {
    let best = -1;
    let len = 0;
    for (const term of terms) {
      let i = lower.indexOf(term, from);
      // A term marks the start of a word only (never the middle of one).
      while (i > 0 && /[\p{L}\p{N}]/u.test(lower[i - 1])) i = lower.indexOf(term, i + 1);
      if (i >= 0 && (best < 0 || i < best)) { best = i; len = term.length; }
    }
    if (best < 0) break;
    if (best > at) out.push({ text: text.slice(at, best) });
    out.push({ text: text.slice(best, best + len), mark: true });
    at = best + len;
    from = at;
  }
  if (at < text.length) out.push({ text: text.slice(at) });
  return out;
}

/** A memory chunk opens with its source's title (the chunker writes it);
 * the row draws the title on line one, so line two leaves it out. */
function withoutLeadingTitle(parts: SnippetPart[], title: string): SnippetPart[] {
  const head = title.trim();
  const text = parts.map((part) => part.text).join("");
  if (!head || !text.startsWith(head) || text.length === head.length || !/[\s:·.,-]/.test(text[head.length])) return parts;
  let drop = head.length;
  while (drop < text.length && /[\s:·.,-]/.test(text[drop])) drop += 1;
  const out: SnippetPart[] = [];
  for (const part of parts) {
    if (drop >= part.text.length) { drop -= part.text.length; continue; }
    out.push(drop ? { ...part, text: part.text.slice(drop) } : part);
    drop = 0;
  }
  return out;
}

/** The snippet as plain parts: marked, redacted or neither. With `title`, a
 * snippet that opens with the title leaves it out. */
export function snippetParts(snippet: string | undefined, query: string, title = ""): SnippetPart[] {
  const flat = String(snippet ?? "").replace(/\s+/g, " ").trim();
  if (!flat) return [];
  const served: SnippetPart[] = flat
    .split(MARKED)
    .filter(Boolean)
    .map((piece) =>
      /^<mark>[\s\S]*<\/mark>$/i.test(piece)
        ? { text: piece.replace(/^<mark>|<\/mark>$/gi, ""), mark: true }
        : { text: piece.replace(/<\/?mark>/gi, "") },
    )
    .filter((part) => part.text);
  const hadMarks = served.some((part) => part.mark);
  const parts = withoutLeadingTitle(served.flatMap(splitRedacted), title);
  if (hadMarks) return parts;
  const terms = questionTerms(query);
  return parts.flatMap((part) => (part.redacted ? [part] : markTerms(part.text, terms)));
}

/** The words of a snippet, without marks. */
export function snippetText(parts: SnippetPart[]): string {
  return parts.map((part) => part.text).join("");
}

export interface PaletteHit {
  parts: SnippetPart[];
  origin?: string;
  at?: string;
}

/** The second line of a MEMORY row: the snippet, then FoundBy and the day. */
export function PaletteHitLine({ hit }: { hit: PaletteHit }) {
  const day = foundByDay(hit.at);
  return (
    <span className="desk-deck-hit">
      {hit.parts.length ? (
        <span className="desk-deck-snippet">
          {hit.parts.map((part, index) =>
            part.mark ? (
              <mark className="desk-deck-mark" key={index}>{part.text}</mark>
            ) : part.redacted ? (
              <span className="desk-deck-redacted" key={index}>{part.text}</span>
            ) : (
              // Plain words stay text: a wrapped inline box per part reads as overlap.
              <Fragment key={index}>{part.text}</Fragment>
            ),
          )}
        </span>
      ) : null}
      {foundByWord(hit.origin) || day ? (
        <span className="desk-deck-hit-meta">
          <FoundBy origin={hit.origin} />
          {day ? <span className="surface-token desk-deck-day">{day}</span> : null}
        </span>
      ) : null}
    </span>
  );
}

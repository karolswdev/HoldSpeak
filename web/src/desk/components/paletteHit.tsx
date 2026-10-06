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

const MARK_TAG = /<\/?mark>/gi;
/** The separator between a chunk's leading title and its text: a colon or a
 * dash with its spaces, or plain spaces. Nothing else is removed. */
const TITLE_SEPARATOR = /^(?:\s*[:\u2014\u2013|\u00b7]\s*|\s+-\s+|\s+)/u;

/** The snippet as plain text, and which of its characters the server marked.
 * Offsets are into the original text: nothing changes its length. */
function readServed(flat: string): { plain: string; served: boolean[] } {
  let plain = "";
  const served: boolean[] = [];
  let inside = false;
  let at = 0;
  for (const tag of flat.matchAll(MARK_TAG)) {
    const piece = flat.slice(at, tag.index);
    plain += piece;
    for (let i = 0; i < piece.length; i += 1) served.push(inside);
    inside = tag[0][1] !== "/";
    at = (tag.index ?? 0) + tag[0].length;
  }
  const rest = flat.slice(at);
  plain += rest;
  for (let i = 0; i < rest.length; i += 1) served.push(inside);
  return { plain, served };
}

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** The question's words, matched case-insensitively ON THE ORIGINAL text
 * (`iu`), at the start of a word only. No case conversion: a character whose
 * lower case is longer (İ, ẞ) can never shift a mark. */
function questionMarks(plain: string, query: string): boolean[] {
  const marked: boolean[] = new Array(plain.length).fill(false);
  const words = [...new Set(query.match(/[\p{L}\p{N}]+/gu) ?? [])]
    .filter((w) => [...w].length >= 2)
    .sort((a, b) => b.length - a.length);
  if (!words.length) return marked;
  const pattern = new RegExp(`(?<![\\p{L}\\p{N}])(?:${words.map(escapeRegExp).join("|")})`, "giu");
  for (const match of plain.matchAll(pattern)) {
    const from = match.index ?? 0;
    for (let i = from; i < from + match[0].length; i += 1) marked[i] = true;
  }
  return marked;
}

/** The snippet as plain parts: marked, redacted or neither. With `title`, a
 * snippet that opens with the title and a separator leaves both out.
 *
 * Order: the plain text first (the server's tags stripped, its marks kept as
 * a per-character flag); then every `[redacted]` marker on that plain text;
 * then the marks, only outside a marker. A marker is always whole and never
 * marked. */
export function snippetParts(snippet: string | undefined, query: string, title = ""): SnippetPart[] {
  const flat = String(snippet ?? "").replace(/\s+/g, " ").trim();
  if (!flat) return [];
  let { plain, served } = readServed(flat);
  // A memory chunk opens with its source's title (the chunker writes it);
  // the row draws the title on line one. Only the title and the separator
  // right after it go; when the text after the title is not a separator,
  // the snippet stays whole.
  const head = title.trim();
  if (head && plain.startsWith(head)) {
    const separator = TITLE_SEPARATOR.exec(plain.slice(head.length));
    const cut = head.length + (separator ? separator[0].length : 0);
    if (separator && cut < plain.length) {
      plain = plain.slice(cut);
      served = served.slice(cut);
    }
  }
  const redacted: boolean[] = new Array(plain.length).fill(false);
  for (let at = plain.indexOf(REDACTED); at >= 0; at = plain.indexOf(REDACTED, at + REDACTED.length)) {
    for (let i = at; i < at + REDACTED.length; i += 1) redacted[i] = true;
  }
  const outside = (flags: boolean[]) => flags.map((flag, i) => flag && !redacted[i]);
  let marked = outside(served);
  if (!marked.some(Boolean)) marked = outside(questionMarks(plain, query));
  const parts: SnippetPart[] = [];
  let i = 0;
  while (i < plain.length) {
    if (redacted[i] && plain.startsWith(REDACTED, i)) {
      parts.push({ text: REDACTED, redacted: true });
      i += REDACTED.length;
      continue;
    }
    let j = i + 1;
    while (j < plain.length && marked[j] === marked[i] && !(redacted[j] && plain.startsWith(REDACTED, j))) j += 1;
    parts.push(marked[i] ? { text: plain.slice(i, j), mark: true } : { text: plain.slice(i, j) });
    i = j;
  }
  return parts;
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

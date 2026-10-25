/* StandingPage + RefTokens (memory on the Desk, canvas section 2, option B
 * "Where the work lives", ratified 2026-10-05).
 *
 * StandingPage: one standing answer memory keeps (MEMORY-DESIGN.md §3.4).
 * The question as the title, the served sentences as a numbered list with
 * the refs each rests on, the BUILT time, and `STALE · N NEW SOURCES` with a
 * warn border when memory changed after the page saw it.  A withheld
 * sentence is simply not drawn: no gap, no counter, no marker.  No verb
 * rewrites a page (no on-demand rewrite exists).
 *
 * RefTokens: the short source tokens, in sentence-case words (window
 * grammar 2026-10-24: `Meeting 10-01 · 14:20`, `Decision 10-01`, `Risk`).
 * A ref the Desk opens is a library Button that opens its window; a ref
 * with no window is plain text (A.11).  A ref that contradicts reads
 * `Against · <token>` in the danger ink.
 */
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { countToken } from "../count";
import { StateChip } from "./StateChip";
import "./standing-page.css";

export interface MemoryRefToken {
  ref: string;
  token: string;
  opens: boolean;
  against?: boolean;
}

const REF_WORDS: Record<string, string> = { MTG: "Meeting", DEC: "Decision", ACT: "Action", CMT: "Action" };

/** A wire token in sentence-case words: an all-caps word of three letters
 *  or more reads as a word (`MTG` → `Meeting`, `RISK` → `Risk`, `THREAD
 *  10-11` → `Thread 10-11`); dates, times, ids and two-letter forms
 *  (`PR #4`) stay as they are. */
export function refWords(token: string): string {
  return token.replace(/\b[A-Z]{3,}\b/g, (word) => REF_WORDS[word] ?? word.charAt(0) + word.slice(1).toLowerCase());
}

/** PHILO-17 (owner: "double references"): one chip per distinct source
 *  object (the same ref, for or against, is one chip); past three, the
 *  first two and `+N`, which opens the rest. */
export function distinctRefs(refs: MemoryRefToken[]): MemoryRefToken[] {
  const seen = new Set<string>();
  return refs.filter((r) => {
    const key = `${r.ref}:${r.against ? "against" : "for"}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function RefTokens({
  refs,
  onOpen,
  label = "Sources",
}: {
  refs: MemoryRefToken[];
  onOpen: (ref: string) => void;
  label?: string;
}) {
  const [all, setAll] = useState(false);
  const distinct = distinctRefs(refs);
  if (!distinct.length) return null;
  const shown = all || distinct.length <= 3 ? distinct : distinct.slice(0, 2);
  const rest = distinct.length - shown.length;
  return (
    <span className="memory-ref-tokens" role="group" aria-label={label}>
      {shown.map((r) => {
        const text = refWords(r.against ? `AGAINST · ${r.token}` : r.token);
        return r.opens ? (
          <Button
            key={`${r.ref}:${r.against ? "against" : "for"}`}
            variant="chrome"
            className="desk-chip quiet memory-ref-token"
            data-tone={r.against ? "danger" : undefined}
            data-testid="memory-ref"
            aria-label={`Open the source: ${text}`}
            onClick={() => onOpen(r.ref)}
          >
            {text}
          </Button>
        ) : (
          <span
            key={`${r.ref}:${r.against ? "against" : "for"}`}
            className="desk-chip quiet memory-ref-token"
            data-tone={r.against ? "danger" : undefined}
            data-testid="memory-ref-plain"
          >
            {text}
          </span>
        );
      })}
      {rest > 0 ? (
        <Button
          variant="chrome"
          className="desk-chip quiet memory-ref-token memory-ref-more"
          data-testid="memory-ref-more"
          aria-label={`Show ${rest} more sources`}
          onClick={() => setAll(true)}
        >
          +{rest}
        </Button>
      ) : null}
    </span>
  );
}

export interface StandingSentence {
  text: string;
  refs: MemoryRefToken[];
}

export function StandingPage({
  title,
  sentences,
  built,
  stale = false,
  newSources = 0,
  onOpenRef,
}: {
  title: string;
  sentences: StandingSentence[];
  /** `BUILT 09:12` / `BUILT MON 08:02` / `BUILT 09-28` (the caller's clock). */
  built: string;
  stale?: boolean;
  newSources?: number;
  onOpenRef: (ref: string) => void;
}) {
  if (!sentences.length) return null;
  const more = countToken(newSources, "NEW SOURCE");
  return (
    <article
      className="standing-page"
      data-stale={stale || undefined}
      data-testid="standing-page"
      aria-label={title}
    >
      <header className="standing-page-head">
        <h4 className="surface-primary standing-page-title">{title}</h4>
        <span className="standing-page-meta">
          {stale ? (
            <StateChip state="warning" label={more ? `STALE · ${more}` : "STALE"} data-testid="standing-page-stale" />
          ) : null}
          <span className="surface-token" data-testid="standing-page-built">{built}</span>
        </span>
      </header>
      <ol className="standing-page-sentences">
        {sentences.map((s, index) => (
          <li key={`${index}:${s.text}`} data-testid="standing-sentence">
            <span className="standing-page-sentence">{s.text}</span>
            <RefTokens refs={s.refs} onOpen={onOpenRef} />
          </li>
        ))}
      </ol>
    </article>
  );
}

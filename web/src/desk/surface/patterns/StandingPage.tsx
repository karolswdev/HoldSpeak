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
 * RefTokens: the short source tokens (`MTG 10-01 · 14:20`, `DEC 10-01`).
 * A ref the Desk opens is a library Button that opens its window; a ref
 * with no window is plain text (A.11).  A ref that contradicts reads
 * `AGAINST · <token>` in the danger ink.
 */
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

export function RefTokens({
  refs,
  onOpen,
  label = "Sources",
}: {
  refs: MemoryRefToken[];
  onOpen: (ref: string) => void;
  label?: string;
}) {
  if (!refs.length) return null;
  return (
    <span className="memory-ref-tokens" role="group" aria-label={label}>
      {refs.map((r) => {
        const text = r.against ? `AGAINST · ${r.token}` : r.token;
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

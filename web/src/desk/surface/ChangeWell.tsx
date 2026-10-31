/* ChangeWell (PG-LANG §9.2, §11): the inset that holds a proposed change.
 *
 * Its head is one line that says what changes (the shaping engine's `say`,
 * or the typed text's own words) with a muted fact beside it (the engine and
 * its time, or the line count); then one DiffRow per change; then the verbs
 * (Apply, Not this: library Buttons the host passes) and a failure line.
 * It is only drawn when there are rows: the host does not mount it empty.
 *
 * Motion (UX-CANON D, four moments at most): the rows fade in from the
 * well one after the other; a refused row shakes once; on `settling` the
 * well settles (fades up and closes) before the host unmounts it. None
 * under reduced motion. The text, shaping, the draft and the rounds share
 * this one well (the rows come from any source). */
import { useEffect, useRef, type ReactNode } from "react";
import "./change-well.css";

export function ChangeWell({
  label = "Proposed change",
  head,
  fact,
  verbs,
  failure,
  settling,
  children,
  className,
  "data-testid": testId,
}: {
  label?: string;
  /** What changes, in one line. */
  head: ReactNode;
  /** A muted fact beside the head (`qwen3.8-27b · 2.8 s`). */
  fact?: ReactNode;
  /** Apply, Not this: library Buttons. */
  verbs: ReactNode;
  /** A press that did not land: its words, and the raw cause as the title. */
  failure?: { words: string; title?: string } | null;
  /** The change applied: the well settles and closes. */
  settling?: boolean;
  /** The DiffRows. */
  children: ReactNode;
  className?: string;
  "data-testid"?: string;
}) {
  // The well opens where the eye is: in view, however far he scrolled.
  const ref = useRef<HTMLElement | null>(null);
  useEffect(() => { ref.current?.scrollIntoView?.({ block: "nearest" }); }, []);
  return (
    <section ref={ref} className={className ? `kit-changewell ${className}` : "kit-changewell"} aria-label={label}
      data-settling={settling ? "" : undefined} data-testid={testId}>
      <div className="kit-changewell-head">
        <span className="kit-changewell-say">{head}</span>
        {fact ? <span className="kit-changewell-fact">{fact}</span> : null}
      </div>
      <ul className="kit-changewell-rows">{children}</ul>
      <div className="kit-changewell-foot">
        <span className="kit-changewell-verbs">{verbs}</span>
        {failure ? (
          <span className="kit-changewell-failure" role="status" title={failure.title} data-testid="kit-changewell-failure">{failure.words}</span>
        ) : null}
      </div>
    </section>
  );
}

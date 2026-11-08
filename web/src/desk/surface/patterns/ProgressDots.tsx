/** ProgressDots: the one row of progress dots (the Walk, the New program
 *  wizard). One 6 px dot a step; done steps fill; the current step is a
 *  16 px pill. The dots draw in `currentColor`, so the caller sets the
 *  colour: paper ink on the blue window head, accent on steel. */
import "./progress-dots.css";

export type ProgressDotsProps = {
  count: number;
  /** The current step, 0-based. */
  at: number;
  /** The done steps: a predicate or a set of indexes. */
  done?: ((index: number) => boolean) | ReadonlySet<number>;
  /** The accessible "n of m". Without it the dots are hidden from
   *  assistive technology (the caller says the count elsewhere). */
  label?: string;
  className?: string;
  "data-testid"?: string;
  [data: `data-${string}`]: string | undefined;
};

export function ProgressDots({ count, at, done, label, className, ...data }: ProgressDotsProps) {
  const isDone = (index: number): boolean =>
    typeof done === "function" ? done(index) : done ? done.has(index) : false;
  return (
    <span
      {...data}
      className={className ? `surface-progress-dots ${className}` : "surface-progress-dots"}
      role={label ? "img" : undefined}
      aria-label={label || undefined}
      aria-hidden={label ? undefined : true}
    >
      {Array.from({ length: count }, (_, index) => (
        <span
          key={index}
          className="surface-progress-dot"
          data-state={index === at ? "now" : isDone(index) ? "done" : undefined}
        />
      ))}
    </span>
  );
}

// HS-170-04 — the transcript well with speaker tokens.
// Board: `KAROL` / `ANIA` in mono caption before each segment,
// accent for the owner. Timestamp as secondary when no speaker.
import { useEffect, useRef, type ReactNode } from "react";
import { SurfaceState } from "./Surface";
import { useWholeLines } from "./wholeLines";
import { Disclosure } from "./patterns";
import { useReadingEndAnchor } from "./useReadingEndAnchor";
import "./transcript-well.css";

export function TranscriptWell({
  id,
  mark,
  live,
  footer,
  seat = false,
  segments,
  momentSegmentIndex,
  defaultOpen,
  wordCount,
  emptyLabel = "No transcript",
  open,
  onOpenChange,
}: {
  id: string;
  /** A named moment or caught decision, by line identity. */
  mark?: (line: Record<string, unknown>, index: number) => boolean;
  live?: boolean;
  footer?: ReactNode;
  /** A tab supplies its own name and reading well. */
  seat?: boolean;
  segments: Record<string, unknown>[];
  momentSegmentIndex?: number | null;
  /** When supplied, wrap this well in the shared fold species. */
  defaultOpen?: boolean;
  /** Durable transcript word count shown on the folded trigger. */
  wordCount?: number | null;
  /** PHILO-17 speech: the empty line names why ("No transcript: speech is
   *  not set up") when the record says so. */
  emptyLabel?: string;
  /** PHILO-17: the fold, controlled (the meeting window opens it from its
   *  foot's Open transcript and from a decision moment). */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}) {
  const reading = useRef<HTMLDivElement>(null);
  useReadingEndAnchor(reading, live !== undefined);
  const bounded = live !== undefined || seat;
  useWholeLines(reading, bounded);
  useEffect(() => {
    if (momentSegmentIndex == null || !segments.length) return;
    const frame = window.requestAnimationFrame(() => {
      document.getElementById(`transcript-${id}-${momentSegmentIndex}`)?.scrollIntoView({
        block: "center",
        behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth",
      });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [id, momentSegmentIndex, segments.length]);

  // Inside the fold the fold's label is the head (said once).
  const content = (
    <div ref={reading} className="surface-transcript-well" data-seat={bounded || undefined}
      role={live !== undefined ? "log" : undefined} aria-label={live !== undefined ? "Transcript" : undefined}
      aria-live={live !== undefined ? "off" : undefined} data-working={live || undefined}
      data-feedback-redact="true" data-testid={live !== undefined ? "live-transcript" : undefined}>
      {segments.length ? (
        <ol className="transcript-list" data-feedback-redact="true">
          {segments.map((row, index) => {
            const label = String(row.speaker ?? "").trim();
            const s = Number(row.start_time ?? row.start ?? NaN);
            const timestamp = Number.isFinite(s)
              ? `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`
              : String(row.timestamp ?? "");
            // Older callers supply a joined speaker/time label. Split that
            // exact suffix once so both modes draw each fact only once.
            const suffix = timestamp ? ` · ${timestamp}` : "";
            const speaker = suffix && label.endsWith(suffix) ? label.slice(0,-suffix.length) : label;

            return (
              <li
                key={String(row.id ?? row.segment_id ?? index)}
                id={`transcript-${id}-${index}`}
                data-moment={index === momentSegmentIndex || undefined}
                data-mark={mark?.(row, index) || undefined}
                data-testid={live !== undefined ? "live-transcript-line" : undefined}
              >
                <time>{timestamp}</time>
                {speaker ? (
                  <span className="transcript-speaker" data-testid="transcript-speaker">
                    {speaker}
                  </span>
                ) : null}
                <p>{String(row.text ?? row.transcript ?? "")}</p>
              </li>
            );
          })}
        </ol>
      ) : (
        <SurfaceState empty emptyLabel={emptyLabel} emptyGlyph="¶" />
      )}
      {footer}
    </div>
  );
  if (bounded || defaultOpen === undefined && open === undefined) return content;
  const words = typeof wordCount === "number" && wordCount > 0
    ? `${wordCount} words`
    : undefined;
  return (
    <Disclosure
      label={segments.length ? `Transcript · ${segments.length}` : "Transcript"}
      token={words}
      defaultOpen={defaultOpen}
      open={open}
      onOpenChange={onOpenChange}
      variant="dense"
    >
      {content}
    </Disclosure>
  );
}

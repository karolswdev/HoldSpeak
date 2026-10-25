// HS-170-04 — the transcript well with speaker tokens.
// Board: `KAROL` / `ANIA` in mono caption before each segment,
// accent for the owner. Timestamp as secondary when no speaker.
import { useEffect } from "react";
import {
  SurfaceState,
  SurfaceWell,
} from "../../../desk/surface/Surface";
import { countLabel } from "../../../desk/surface";
import { Disclosure } from "../../../desk/surface/patterns";
import { rowId } from "../../pageSupport";

export function TranscriptWell({
  id,
  segments,
  momentSegmentIndex,
  defaultOpen,
  wordCount,
  emptyLabel = "No transcript",
  open,
  onOpenChange,
}: {
  id: string;
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
  useEffect(() => {
    if (momentSegmentIndex == null || !segments.length) return;
    const frame = window.requestAnimationFrame(() => {
      document
        .getElementById(`transcript-${id}-${momentSegmentIndex}`)
        ?.scrollIntoView({ block: "center", behavior: "smooth" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [id, momentSegmentIndex, segments.length]);

  // Inside the fold the fold's label is the head (said once).
  const folded = defaultOpen !== undefined || open !== undefined;
  const well = (
    <SurfaceWell head={folded ? undefined : countLabel("TRANSCRIPT", segments.length)}>
      {segments.length ? (
        <ol className="transcript-list">
          {segments.map((row, index) => {
            const speaker = String(row.speaker ?? "").trim();
            const s = Number(row.start_time ?? row.start ?? NaN);
            const timestamp = Number.isFinite(s)
              ? `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`
              : String(row.timestamp ?? "");

            return (
              <li
                key={rowId(row, index)}
                id={`transcript-${id}-${index}`}
                data-moment={index === momentSegmentIndex || undefined}
              >
                {speaker ? (
                  <span className="transcript-speaker" data-testid="transcript-speaker">
                    {speaker}
                  </span>
                ) : (
                  <time>{timestamp}</time>
                )}
                <p>{String(row.text ?? row.transcript ?? "")}</p>
              </li>
            );
          })}
        </ol>
      ) : (
        <SurfaceState empty emptyLabel={emptyLabel} emptyGlyph="¶" />
      )}
    </SurfaceWell>
  );
  if (defaultOpen === undefined && open === undefined) return well;
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
      {well}
    </Disclosure>
  );
}

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
}: {
  id: string;
  segments: Record<string, unknown>[];
  momentSegmentIndex?: number | null;
  /** When supplied, wrap this well in the shared fold species. */
  defaultOpen?: boolean;
  /** Durable transcript word count shown on the folded trigger. */
  wordCount?: number | null;
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

  const well = (
    <SurfaceWell head={countLabel("TRANSCRIPT", segments.length)}>
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
                    {speaker.toUpperCase()}
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
        <SurfaceState empty emptyLabel="No transcript" emptyGlyph="¶" />
      )}
    </SurfaceWell>
  );
  if (defaultOpen === undefined) return well;
  const words = typeof wordCount === "number" && wordCount > 0
    ? `${wordCount} WORDS`
    : undefined;
  return (
    <Disclosure
      label="TRANSCRIPT"
      token={words}
      defaultOpen={defaultOpen}
      variant="dense"
    >
      {well}
    </Disclosure>
  );
}

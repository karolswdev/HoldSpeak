// HS-170-04 — the transcript well with speaker tokens.
// Board: `KAROL` / `ANIA` in mono caption before each segment,
// accent for the owner. Timestamp as secondary when no speaker.
import { useEffect } from "react";
import {
  SurfaceState,
  SurfaceWell,
} from "../../../desk/surface/Surface";
import { countLabel } from "../../../desk/surface";
import { rowId } from "../../pageSupport";

export function TranscriptWell({
  id,
  segments,
  momentSegmentIndex,
}: {
  id: string;
  segments: Record<string, unknown>[];
  momentSegmentIndex?: number | null;
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

  return (
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
}

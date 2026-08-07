// HS-117-09 — extracted from MeetingDetail (lines 689-717).
import { useEffect } from "react";
import {
  SurfaceState,
  SurfaceWell,
} from "../../../desk/surface/Surface";
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
    <SurfaceWell head={`TRANSCRIPT · ${segments.length} SEG`}>
      {segments.length ? (
        <ol className="transcript-list">
          {segments.map((row, index) => (
            <li
              key={rowId(row, index)}
              id={`transcript-${id}-${index}`}
              data-moment={index === momentSegmentIndex || undefined}
            >
              <time>
                {(() => {
                  const s = Number(row.start_time ?? row.start ?? NaN);
                  if (!Number.isFinite(s)) {
                    return String(row.timestamp ?? "");
                  }
                  const m = Math.floor(s / 60);
                  const sec = Math.floor(s % 60);
                  return `${m}:${String(sec).padStart(2, "0")}`;
                })()}
              </time>
              <p>{String(row.text ?? row.transcript ?? "")}</p>
            </li>
          ))}
        </ol>
      ) : (
        <SurfaceState empty emptyLabel="No transcript" emptyGlyph="¶" />
      )}
    </SurfaceWell>
  );
}

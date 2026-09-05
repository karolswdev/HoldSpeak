// HS-117-09 — extracted from MeetingDetail (lines 524-549).
import { Button } from "../../../components/signal/Signal";
import { SurfaceState } from "../../../desk/surface/Surface";
import { StateTokenSpan } from "./StateTokenSpan";
import { ledgerDate, durationToken, stateToken } from "./helpers";
import { countToken } from "../../../desk/surface";
import type { MeetingData } from "./useMeetingData";

export function MeetingHeader({
  meeting,
  data,
  onClose,
}: {
  meeting: Record<string, unknown>;
  data: MeetingData;
  onClose(): void;
}) {
  const { detail, error, segments, artifactRows, captureBad, intelOff, startedAt, durationS } = data;
  return (
    <>
      {/* 0 — the record index line: title over ONE mono facts line. */}
      <div className="surface-detail-head">
        <div className="surface-detail-title">
          <strong className="surface-primary">
            {String(detail?.title ?? meeting.title ?? "Meeting")}
          </strong>
          <span className="surface-detail-facts">
            {[
              ledgerDate(startedAt),
              durationS > 0
                ? durationToken(durationS) || "1 MIN"
                : "",
              countToken(segments.length, "SEG") ?? "",
              countToken(artifactRows.length, "ART") ?? "",
            ]
              .filter(Boolean)
              .join(" · ")}
            {captureBad || intelOff ? " · " : ""}
            {captureBad || intelOff ? (
              <StateTokenSpan token={stateToken(detail ?? meeting)} />
            ) : null}
          </span>
        </div>
        <Button dense variant="ghost" onClick={onClose}>
          Close
        </Button>
      </div>
      {error ? <SurfaceState error={error} /> : null}
    </>
  );
}

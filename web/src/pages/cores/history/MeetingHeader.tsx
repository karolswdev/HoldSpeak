// HS-170-04 — the detail header: display title + token row.
// Board: `Design review` (display) + `SEP 02 · 45 MIN · SAVED` tokens.
// Middle dot (U+00B7) between every token, equal space both sides.
import type { ReactNode } from "react";
import { StateTokenSpan } from "./StateTokenSpan";
import { ledgerDate, durationToken, stateToken } from "./helpers";
import type { MeetingData } from "./useMeetingData";

export function MeetingHeader({
  meeting,
  data,
}: {
  meeting: Record<string, unknown>;
  data: MeetingData;
}) {
  const { detail, startedAt, durationS } = data;
  const token = stateToken(detail ?? meeting);
  const title = String(detail?.title ?? meeting.title ?? "Meeting");
  const dateStr = ledgerDate(startedAt);
  const durStr = durationS > 0 ? (durationToken(durationS) || "1 MIN") : "";

  const parts: ReactNode[] = [];
  if (dateStr) parts.push(<span key="date" className="meetings-stream-fact">{dateStr}</span>);
  if (durStr) parts.push(<span key="dur" className="meetings-stream-fact">{durStr}</span>);
  parts.push(<StateTokenSpan key="state" token={token} />);

  // Interleave dots as sibling flex children for equal spacing
  const interleaved: ReactNode[] = [];
  parts.forEach((part, i) => {
    if (i > 0) interleaved.push(
      <span key={`dot-${i}`} className="meetings-stream-dot" aria-hidden="true">{"·"}</span>
    );
    interleaved.push(part);
  });

  return (
    <div className="meetings-detail-head">
      <div className="surface-display">{title}</div>
      <div className="meetings-detail-facts">
        {interleaved}
      </div>
    </div>
  );
}

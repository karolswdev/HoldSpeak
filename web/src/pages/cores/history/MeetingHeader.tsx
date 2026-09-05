// HS-172 — the detail header: display title + token row.
// Board: `SEP 05 · 30 MIN · ● RAN · 41 S · 192.168.1.43 · LAN` tokens.
// Middle dot (U+00B7) between every token, equal space both sides.
import type { ReactNode } from "react";
import { StateTokenSpan } from "./StateTokenSpan";
import { StateChip } from "../../../desk/surface";
import { ledgerDate, durationToken, stateToken, intelDurationToken } from "./helpers";
import { EgressChip } from "../../../desk/surface/gadgets";
import type { MeetingData } from "./useMeetingData";

function egressLabel(host: string): string {
  if (host === "local" || host === "LOCAL" || host === "this_device") return "THIS DEVICE";
  if (host === "THIS DEVICE") return host;
  if (/^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/.test(host)) return `${host} · LAN`;
  return `${host} · CLOUD`;
}

function egressScope(host: string): "local" | "cloud" {
  if (host === "local" || host === "LOCAL" || host === "this_device" || host === "THIS DEVICE") return "local";
  if (/^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/.test(host)) return "local";
  return "cloud";
}

export function MeetingHeader({
  meeting,
  data,
}: {
  meeting: Record<string, unknown>;
  data: MeetingData;
}) {
  const { detail, startedAt, durationS } = data;
  const source = detail ?? meeting;
  const token = stateToken(source);
  const title = String(detail?.title ?? meeting.title ?? "Meeting");
  const dateStr = ledgerDate(startedAt);
  const durStr = durationS > 0 ? (durationToken(durationS) || "1 MIN") : "";
  // HS-172: source from the wire's intel_model_host / intel_duration_s,
  // not from proposals.
  const intelDurS = Number(source.intel_duration_s ?? 0);
  const intelDur = intelDurS > 0 ? `${intelDurS} S` : null;
  const rawHost = String(source.intel_model_host ?? "") || null;

  const parts: ReactNode[] = [];
  if (dateStr) parts.push(<span key="date" className="meetings-stream-fact">{dateStr}</span>);
  if (durStr) parts.push(<span key="dur" className="meetings-stream-fact">{durStr}</span>);
  if (token.label === "RAN") {
    parts.push(<StateChip key="state" state="success" label="RAN" icon="●" />);
  } else if (token.label === "RUNNING") {
    parts.push(<StateChip key="state" state="working" label="RUNNING" />);
  } else {
    parts.push(<StateTokenSpan key="state" token={token} />);
  }
  if (token.label === "RAN" && intelDur) {
    parts.push(<span key="intel-dur" className="meetings-stream-fact">{intelDur}</span>);
  }
  if ((token.label === "RAN" || token.label === "RUNNING") && rawHost) {
    parts.push(<EgressChip key="intel-host" label={egressLabel(rawHost)} scope={egressScope(rawHost)} />);
  }

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

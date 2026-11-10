import { useEffect, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { PaneActions } from "../../../desk/surface";
import { apiFetch } from "../../../lib/api";
import { MeetingSummary, readMeetingIntel } from "../../../meetings/MeetingSummarySlab";
import type { MeetingDecision } from "./useMeetingData";
import { durationToken, ledgerDate, clockTime } from "./helpers";
import { listMeetingState } from "./CatalogRail";
import { TranscriptWell } from "./TranscriptWell";

/** A selection read is cancelled on change; an old reply cannot replace the new preview. */
export function MeetingPreview({ meeting, state }: { meeting: Record<string, unknown>; state?: string }) {
  const id = String(meeting.id);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [decisions, setDecisions] = useState<MeetingDecision[]>([]);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let current = true;
    setError(false);
    void Promise.all([
      apiFetch<Record<string, unknown>>(`/api/meetings/${encodeURIComponent(id)}`),
      apiFetch<{ decisions?: MeetingDecision[] }>(`/api/decisions/ledger?limit=500&meeting_id=${encodeURIComponent(id)}`),
    ]).then(([fresh, ledger]) => {
      if (!current) return;
      setDetail(fresh); setDecisions(ledger.decisions ?? []);
    }).catch(() => { if (current) setError(true); });
    return () => { current = false; };
  }, [id, meeting, retry]);
  const intel = readMeetingIntel(detail);
  return <div data-testid="meeting-list-preview">
    <strong>{String(meeting.title || "Meeting")}</strong>
    <p>{[ledgerDate(meeting.started_at ?? meeting.created_at), clockTime(meeting.started_at ?? meeting.created_at), durationToken(meeting.duration_seconds), state ?? listMeetingState(meeting, { runningId: null })?.label].filter(Boolean).join(" · ")}</p>
    {error ? <PaneActions><span role="alert">Summary not read</span><Button dense onClick={() => setRetry(retry + 1)}>Retry</Button></PaneActions>
      : !detail ? <p>Reading summary…</p> : <>
        <MeetingSummary intel={intel} receipt={null} />
        {Array.isArray(detail.segments) && detail.segments.length ? <TranscriptWell id={id} segments={detail.segments} /> : null}
        {!intel?.summary?.trim() ? <p>No summary</p> : null}
        {decisions.length ? <><strong>Decisions</strong><ul>{decisions.filter((row) => row.lifecycle !== "rejected").map((row) => <li key={row.id}>{row.text}</li>)}</ul></> : null}
      </>}
  </div>;
}

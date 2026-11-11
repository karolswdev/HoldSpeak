import { useCallback, useEffect, useState } from "react";
import { useWindowBack } from "../../../desk/surface/back";
import { Button } from "../../../components/signal/Signal";
import { InspectorFacts, PaneActions, PreferencePane, PreferenceWell, PaneViews } from "../../../desk/surface";
import { apiFetch } from "../../../lib/api";
import { MeetingSummary, readMeetingIntel } from "../../../meetings/MeetingSummarySlab";
import { MeetingSendWellLazy } from "../../../meetings/MeetingSendWellLazy";
import { SEND_OPEN, useAnnounceWindowDocument } from "../../../desk/windowSend";
import { useWindowId } from "../../../desk/components/window/windowIdContext";
import { useMeetingTasks } from "./MeetingTasks";
import type { MeetingDecision } from "./useMeetingData";
import { durationToken, ledgerDate, clockTime } from "./helpers";
import { listMeetingState } from "./CatalogRail";
import { TranscriptWell } from "./TranscriptWell";

/** A selection read is cancelled on change; an old reply cannot replace the new preview. */
export function MeetingPreview({ meeting, state, sendRequest = 0, onSendState, onChanged = () => {}, view, onViewChange }: { view?: string; onViewChange?(view: string): void; meeting: Record<string, unknown>; state?: string; sendRequest?: number; onSendState?(open: boolean): void; onChanged?(): void }) {
  const id = String(meeting.id);
  const [localTab, setLocalTab] = useState(Number(meeting.needs_you_count) > 0 ? "tasks" : "summary");
  const tab = view ?? localTab;
  const setTab = onViewChange ?? setLocalTab;
  const winId = useWindowId();
  const closeSend = useCallback(() => setTab("summary"), [setTab]);
  useWindowBack(tab === "send" ? {onBack:closeSend,onCloseRequest:()=>{closeSend();return true;},testId:"meeting-list-send-back"} : null,[tab]);
  useEffect(() => {
    onSendState?.(tab === "send");
    return () => onSendState?.(false);
  }, [tab, onSendState]);
  useAnnounceWindowDocument(tab === "send" ? null : { kind: "meeting", id, form: "summary" });
  useEffect(() => { if (sendRequest) setTab("send"); }, [sendRequest]);
  useEffect(() => {
    const open = (event: Event) => { if ((event as CustomEvent).detail?.winId === winId) setTab("send"); };
    window.addEventListener(SEND_OPEN, open);
    return () => window.removeEventListener(SEND_OPEN, open);
  }, [winId]);
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
  const tasks = useMeetingTasks({ meeting, onChanged });
  if (tab === "tasks" && tasks.inspector) return tasks.inspector;
  if (tab === "send") return <PreferencePane label="Send meeting" testId="meeting-list-preview" data-feedback-redact="true">
    <MeetingSendWellLazy meetingId={id} title={String(meeting.title || "Meeting")} startedAt={String(meeting.started_at ?? meeting.created_at ?? "")} onBack={closeSend} />
  </PreferencePane>;
  const contents = <PreferencePane label="Selected meeting" testId="meeting-list-preview" data-feedback-redact="true">

    <div className="surface-tab-panel" hidden={tab !== "summary"}><PreferenceWell>
    <InspectorFacts name={String(meeting.title || "Meeting")} rows={[
      {label:"Date",value:ledgerDate(meeting.started_at ?? meeting.created_at).toLowerCase().replace(/^./, letter => letter.toUpperCase())},
      {label:"Time",value:clockTime(meeting.started_at ?? meeting.created_at)},
      {label:"Length",value:durationToken(meeting.duration_seconds).toLowerCase()},
      {label:"State",value:state ?? listMeetingState(meeting, {runningId:null})?.label},
    ]} />
    {error ? <PaneActions><span role="alert">Summary not read</span><Button dense onClick={() => setRetry(retry + 1)}>Retry</Button></PaneActions>
      : !detail ? <p>Reading summary…</p> : <>
        <MeetingSummary intel={intel} receipt={null} />
        {Array.isArray(detail.segments) && detail.segments.length ? <TranscriptWell id={id} segments={detail.segments} /> : null}
        {!intel?.summary?.trim() ? <p>No summary</p> : null}
        {decisions.length ? <><strong>Decisions</strong><ul>{decisions.filter((row) => row.lifecycle !== "rejected").map((row) => <li key={row.id}>{row.text}</li>)}</ul></> : null}
      </>}
    </PreferenceWell></div>
    <div className="surface-tab-panel" hidden={tab !== "tasks"}>{tasks.list}</div>

  </PreferencePane>;
  return view !== undefined ? contents : <PaneViews label="Meeting contents" value={tab} onChange={setTab} tabs={[{ id: "summary", label: "Summary" }, { id: "tasks", label: "Tasks to confirm" }]}>{contents}</PaneViews>;
}

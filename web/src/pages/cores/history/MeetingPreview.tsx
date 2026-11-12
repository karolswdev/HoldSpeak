import { useCallback, useEffect, useState } from "react";
import { useWindowBack } from "../../../desk/surface/back";
import type { StatusBarItem } from "../../../desk/surface";
import { SummaryFailure, summaryFailureReason } from "./SummaryState";
import { Button } from "../../../components/signal/Signal";
import { InspectorBody, InspectorFacts, PaneActions, PreferencePane, PreferenceWell, PaneViews, SegmentedTabs } from "../../../desk/surface";
import { apiFetch } from "../../../lib/api";
import { MeetingSummary, readMeetingIntel } from "../../../meetings/MeetingSummarySlab";
import { MeetingSendWellLazy } from "../../../meetings/MeetingSendWellLazy";
import { SEND_OPEN, useAnnounceWindowDocument } from "../../../desk/windowSend";
import { useWindowId } from "../../../desk/components/window/windowIdContext";
import { useMeetingTasks } from "./MeetingTasks";
import type { MeetingDecision } from "./useMeetingData";
import { durationToken, ledgerDate, clockTime } from "./helpers";
import { useSummaryRun } from "./useSummaryRun";
import { readPlannedRoute } from "../../../meetings/summaryRoute";
import { listMeetingState } from "./CatalogRail";
import { TranscriptWell } from "./TranscriptWell";

/** A selection read is cancelled on change; an old reply cannot replace the new preview. */
export function MeetingPreview({ meeting, state, sendRequest = 0, onSendState, onChanged = () => {}, view, onViewChange, onTaskStatus }: { onTaskStatus?(parts: StatusBarItem[]): void; view?: string; onViewChange?(view: string): void; meeting: Record<string, unknown>; state?: string; sendRequest?: number; onSendState?(open: boolean): void; onChanged?(): void }) {
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
  const summary = useSummaryRun(() => readPlannedRoute(detail ?? meeting), () => { setRetry(value => value + 1); onChanged(); });
  const tasks = useMeetingTasks({ meeting, onChanged, onStatus: onTaskStatus, kind: "action", feedbackKey: tab });
  if (tab === "tasks" && tasks.inspector) return tasks.inspector;
  const contents = <SegmentedTabs label="Meeting contents" value={tab} onChange={setTab} tabs={[{id:tab,label:tab === "send" ? "Send meeting" : tab === "tasks" ? "Tasks to confirm" : "Summary"}]}>
    <PreferencePane label="Selected meeting" testId="meeting-list-preview" data-feedback-redact="true">
    {tab === "send" ? <MeetingSendWellLazy meetingId={id} title={String(meeting.title || "Meeting")} startedAt={String(meeting.started_at ?? meeting.created_at ?? "")} onBack={closeSend} />
    : tab === "summary" ? <InspectorBody>
    <InspectorFacts header={false} name={String(meeting.title || "Meeting")} rows={[
      {label:"Date",value:ledgerDate(meeting.started_at ?? meeting.created_at).toLowerCase().replace(/^./, letter => letter.toUpperCase())},
      {label:"Time",value:clockTime(meeting.started_at ?? meeting.created_at)},
      {label:"Length",value:durationToken(meeting.duration_seconds).toLowerCase()},
      {label:"State",value:state ?? listMeetingState(meeting, {runningId:null})?.label},
    ]} />
    <PreferenceWell>{error ? <PaneActions><span role="alert">Summary not read</span><Button dense onClick={() => setRetry(retry + 1)}>Retry</Button></PaneActions>
      : !detail ? <p>Reading summary…</p> : <>
        <SummaryFailure meeting={detail ?? meeting} retry={() => void summary.run(id)} disabled={summary.runningId === id} />
        <MeetingSummary intel={intel} receipt={null} />
        {Array.isArray(detail.segments) && detail.segments.length ? <TranscriptWell id={id} segments={detail.segments} /> : null}
        {!intel?.summary?.trim() && !summaryFailureReason(detail ?? meeting) ? <p>No summary</p> : null}
        {decisions.length ? <><strong>Decisions</strong><ul>{decisions.filter((row) => row.lifecycle !== "rejected").map((row) => <li key={row.id}>{row.text}</li>)}</ul></> : null}
      </>}
    </PreferenceWell></InspectorBody> : tasks.list}

  </PreferencePane></SegmentedTabs>;
  return view !== undefined ? contents : <PaneViews label="Meeting contents" value={tab} onChange={setTab} tabs={[{ id: "summary", label: "Summary" }, { id: "tasks", label: "Tasks to confirm" }]}>{contents}</PaneViews>;
}

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiBlob, apiFetch, readableError } from "../../../lib/api";
import { WorkMenu } from "../../../desk/components/DeskMenu";
import { AddToProject } from "../../../desk/AddToProject";
import { useDesk } from "../../../desk/store";
import { openSurfaceOr } from "../../../desk/shell";
import { openRef } from "../../../desk/openObject";
import { useWindowId } from "../../../desk/components/window/windowIdContext";
import { publishListMenu, clearListMenu, useListMenu, ownsListMenu } from "../../../desk/components/window/listMenu";
import { useWindowTitle } from "../../../desk/surface/title";
import { useWindowInterior } from "../../../desk/surface/interior";
import { useWindowBack } from "../../../desk/surface/back";
import { SEND_OPEN, useAnnounceWindowDocument } from "../../../desk/windowSend";
import { useRuntimeBus } from "../../../runtime/RuntimeBus";
import { frameNames } from "../../../desk/components/window/dockState";
import { MEETING_CHANGE_KINDS } from "../../../desk/useDeskChangedRefresh";
import { burstTimer } from "../../../desk/burstTimer";
import { onReturnToTask } from "../../../desk/returnToTask";
import { SPEECH_SETUP_EVENT } from "../../../desk/firstrun/SpeechSetup";
import { MEETING_OPEN_EVENT, peekMeetingRequest, takeMeetingRequest, type MeetingOpenRequest } from "../../../desk/objectWindows";
import { parkMeeting, restoreMeeting, renameMeeting } from "../../../desk/api";
import { SendWellReadContext } from "../../../desk/surface/send/SendWell";
import { MeetingSendWellLazy } from "../../../meetings/MeetingSendWellLazy";
import { MeetingDecideWell } from "../../../meetings/MeetingDecideWell";
import { MeetingConflictRecovery } from "../../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../../meetings/MeetingIntelRecovery";
import { readMeetingIntel } from "../../../meetings/MeetingSummarySlab";
import { readPlannedRoute, readRunReceipt, routeReady } from "../../../meetings/summaryRoute";
import { speechWasMissing, NO_TRANSCRIPT_SPEECH } from "../../../desk/firstrun/speechTruth";
import { RunAttempts, routeTitle } from "../../../meetings/RouteDisclosure";
import {
  ConfirmVerb, Elapsed, InspectorFacts, InspectorForm, LiveWell, ListView,
  PaneInspector, PreferencePane, PreferenceWell, ReadingDocument, SegmentedTabs,
  StatusBar, StringGadget, SurfaceState, Toolbar, PaneNotice, listVerbEntries,
  ParkReceipt, parkedOutcome, restoredOutcome, restoreFailedOutcome,
  type ListVerb, type ParkOutcome, type StatusBarItem,
} from "../../../desk/surface";
import { useSummaryRun } from "./useSummaryRun";
import { useMeetingData } from "./useMeetingData";
import { useMeetingTasks } from "./MeetingTasks";
import { MeetingOutcomes, MeetingProposals, MEETING_TRANSCRIPT_OPEN, meetingOutcomes, type OutcomeSelection } from "./MeetingDetail";
import { TranscriptWell } from "./TranscriptWell";
import { CaptureSlab } from "./CaptureSlab";
import { PreparedResults, PREPARED_OPEN, type PreparedOpen } from "./PreparedResults";
import { AudioOnlyVerb } from "./TranscribeVerb";
import { readSinceLast, sinceFacts } from "./SinceLastWell";
import { SummaryFailure, summaryFailureReason } from "./SummaryState";
import { peopleNames } from "./plate";
import { clockTime, durationToken, ledgerDate, unclearLampLabel, download, intelStateOf, ACTIVE_RUN_STATES, FINAL_RUN_STATES, adoptDurableRunReceipt, type Receipt } from "./helpers";

export function MeetingRecord({ meetingId, onClose }: { meetingId: string; onClose(): void }) {
  const initial = peekMeetingRequest(meetingId);
  const [view, setView] = useState(initial?.segment != null ? "transcript" : "summary");
  const [segment, setSegment] = useState<number | null>(initial?.segment ?? null);
  const [meeting, setMeeting] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [parkOutcome, setParkOutcome] = useState<ParkOutcome | null>(null);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false), round = useRef(0), target = useRef(meetingId);
  target.current = meetingId;
  const [outcomeSelections, setOutcomeSelections] = useState<Record<string, OutcomeSelection>>({});
  const [preparedKind, setPreparedKind] = useState<string | null>(null);
  const preparedNotes = useRef(new Map<string, string>());
  const [taskStatus, setTaskStatus] = useState<StatusBarItem[]>([]);
  const [menu, setMenu] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null), deleteSeat = useRef<HTMLSpanElement>(null);
  const winId = useWindowId();
  const sendSeat = useRef<HTMLDivElement>(null);
  const sendRead = useCallback((ready: boolean) => {
    if (ready) requestAnimationFrame(() => { if (target.current === meetingId) sendSeat.current?.querySelector<HTMLElement>("button:not(:disabled), input, textarea")?.focus({ preventScroll: true }); });
  }, [meetingId]);
  useWindowInterior("list");
  const title = String(meeting?.title ?? "").trim();
  useWindowTitle(title || null, [title]);
  const load = useCallback(async () => {
    const mine = ++round.current;
    try {
      const fresh = await apiFetch<Record<string, unknown>>(`/api/meetings/${encodeURIComponent(meetingId)}?include_parked=true`);
      if (mine !== round.current || target.current !== meetingId) return;
      setMeeting(current => current && Object.keys(fresh).every(key => JSON.stringify(current[key]) === JSON.stringify(fresh[key])) ? current : { ...current, ...fresh });
      setError("");
    } catch (cause) { if (mine === round.current && target.current === meetingId) setError(readableError(cause)); }
  }, [meetingId]);
  const refresh = useCallback(() => { setRevision(value => value + 1); void load(); }, [load]);
  useEffect(() => {
    setMeeting(null); setView(peekMeetingRequest(meetingId)?.segment != null ? "transcript" : "summary");
    takeMeetingRequest(meetingId); void load();
    void apiFetch(`/api/meetings/${encodeURIComponent(meetingId)}/ready/read`, { method: "POST" }).catch(() => null);
    return () => { round.current++; };
  }, [meetingId, load]);
  const { subscribe } = useRuntimeBus();
  useEffect(() => {
    const burst = burstTimer(refresh, 300);
    const off = subscribe("desk_changed", frame => { if (frameNames(frame?.data, MEETING_CHANGE_KINDS)) burst.bump(); });
    const after = subscribe("aftercare_ready", burst.bump), returned = onReturnToTask(refresh);
    window.addEventListener("focus", refresh); window.addEventListener(SPEECH_SETUP_EVENT, refresh);
    return () => { burst.cancel(); off(); after(); returned(); window.removeEventListener("focus", refresh); window.removeEventListener(SPEECH_SETUP_EVENT, refresh); };
  }, [subscribe, refresh]);
  const data = useMeetingData(meeting, setReceipt, revision);
  const current = data.detail?.id === meetingId ? { ...meeting, ...data.detail } : meeting;
  const route = readPlannedRoute(current), intel = readMeetingIntel(current);
  const summary = useSummaryRun(() => route, refresh);
  const taskMeeting = useMemo(() => meeting ?? { id: meetingId }, [meeting, meetingId]);
  const tasks = useMeetingTasks({ meeting: taskMeeting, onChanged: refresh, onStatus: setTaskStatus, kind: "action" });
  const state = intelStateOf(current?.intel_status);
  const running = ACTIVE_RUN_STATES.has(state) || summary.runningId === meetingId;
  const run = summary.receipt?.run;
  const adopted = useRef(false), seenActive = useRef<string | null>(null);
  useEffect(() => {
    if (!current || adopted.current) return;
    adopted.current = true;
    const saved = adoptDurableRunReceipt([current]);
    if (saved) summary.setReceipt(value => value ?? saved.receipt);
  }, [current, summary.setReceipt]);
  useEffect(() => {
    if (!run) return;
    const key = `${run.meetingId}:${run.jobId}`;
    if (ACTIVE_RUN_STATES.has(state)) seenActive.current = key;
    else if (FINAL_RUN_STATES.has(state) && seenActive.current === key) { seenActive.current = null; summary.settleRun(run, state); }
  }, [state, run, summary.settleRun]);
  useEffect(() => {
    const request = (event: Event) => {
      const next = (event as CustomEvent<MeetingOpenRequest>).detail;
      if (next?.meetingId === meetingId) { setSegment(next.segment); setView(next.segment != null ? "transcript" : "summary"); takeMeetingRequest(meetingId); }
    };
    const transcript = (event: Event) => { if ((event as CustomEvent).detail === meetingId) setView("transcript"); };
    const send = (event: Event) => { if ((event as CustomEvent).detail?.winId === winId) setView("send"); };
    const prepared = (event: Event) => { if ((event as CustomEvent<PreparedOpen>).detail?.meetingId === meetingId) { setPreparedKind((event as CustomEvent<PreparedOpen>).detail.kind); setView("results"); } };
    window.addEventListener(MEETING_OPEN_EVENT, request); window.addEventListener(MEETING_TRANSCRIPT_OPEN, transcript);
    window.addEventListener(SEND_OPEN, send); window.addEventListener(PREPARED_OPEN, prepared);
    return () => { window.removeEventListener(MEETING_OPEN_EVENT, request); window.removeEventListener(MEETING_TRANSCRIPT_OPEN, transcript); window.removeEventListener(SEND_OPEN, send); window.removeEventListener(PREPARED_OPEN, prepared); };
  }, [meetingId, winId]);
  useAnnounceWindowDocument(view === "send" ? null : { kind: "meeting", id: meetingId, form: "summary" });
  const closeRef = useRef(onClose); closeRef.current = onClose;
  useWindowBack({ onBack: view === "send" || view === "rename" || view === "project" || view === "decide" ? () => setView("summary") : () => closeRef.current(), testId: view === "send" ? "meeting-send-back" : "meeting-record-back" }, [view]);
  const write = async (action: () => Promise<unknown>, words: string) => {
    if (pending.current) return;
    pending.current = true; setBusy(true);
    try { await action(); setReceipt({ text: words }); }
    catch (cause) { setReceipt({ text: `${words} failed · ${readableError(cause)}`, tone: "danger" }); }
    finally { pending.current = false; setBusy(false); }
  };
  const park = () => void write(async () => {
    await parkMeeting(meetingId); setParkOutcome(parkedOutcome([meetingId])); setMeeting(value => value ? { ...value, parked: true } : value);
    void useDesk.getState().refresh().catch(() => undefined);
  }, "Deleted");
  const restore = async (ids: string[]) => {
    try { await Promise.all(ids.map(restoreMeeting)); setParkOutcome(restoredOutcome(ids)); refresh(); }
    catch { setParkOutcome(restoreFailedOutcome(ids)); }
  };
  const exportRecord = (format: string) => void write(async () => {
    const blob = await apiBlob(`/api/meetings/${encodeURIComponent(meetingId)}/export?format=${format}`);
    download(blob, `holdspeak-meeting-${meetingId}.${format === "markdown" ? "md" : format}`);
  }, `Export ${format === "markdown" ? "Markdown" : "SRT"}`);
  const hasSummary = Boolean(intel?.summary?.trim()), canRun = Boolean(current?.transcriptWords || data.segments.length) && routeReady(route) && !running;
  const verbs: ListVerb[] = [
    { id: "summary", label: "Summarise", testId: "meeting-summarise", title: routeTitle(route), enabled: () => Boolean(meeting) && canRun, run: () => { setView("summary"); void summary.run(meetingId); } },
    { id: "send", label: "Send to…", testId: "meeting-send", enabled: () => hasSummary || Boolean(current?.has_summary), run: () => setView("send") },
    { id: "markdown", label: "Export MD", enabled: () => Boolean(meeting), run: () => exportRecord("markdown") },
    { id: "srt", label: "Export SRT", enabled: () => Boolean(meeting), run: () => exportRecord("srt") },
    { id: "rename", label: "Rename", enabled: () => Boolean(meeting), run: () => setView("rename") },
    { id: "decide", label: "Decide", enabled: () => Boolean(meeting), run: () => setView("decide") },
    { id: "project", label: "Add to Project", enabled: () => Boolean(meeting), run: () => setView("project") },
    { id: "bulk", label: "Confirm all", enabled: () => ["tasks", "decisions"].includes(view) && !data.busy && !tasks.inspector && !Object.values(outcomeSelections).some(value => value.draft) && data.ftProposals.some(row => row.kind === "action" && row.state === "proposed" && Boolean(row.owner || row.owner_hint) && Boolean(row.due || row.due_hint) && ["supported", "source_linked"].includes(row.support || "") && !row.unknowns?.length && (!data.reviewRevision || !row.extraction_revision || row.extraction_revision === data.reviewRevision)), run: () => void data.confirmAll() },
    { id: "skip", label: "Skip summary", enabled: () => ["pending", "queued"].includes(state), run: () => void write(async () => { await apiFetch(`/api/meetings/${encodeURIComponent(meetingId)}/intel-recovery/skip`, { method: "POST" }); refresh(); }, "Skipped") },
    { id: "engine", label: "Choose engine", run: () => openSurfaceOr("open-concierge", "/models", "meetings") },
    { id: "settings", label: "Settings", run: () => openSurfaceOr("configure-settings", "/settings", "meetings") },
    { id: "back", label: "All meetings", run: onClose },
    { id: "delete", label: "Delete", enabled: () => Boolean(meeting) && !busy && !meeting?.parked, run: () => deleteSeat.current?.querySelector<HTMLButtonElement>('[data-testid="meeting-delete"]')?.click() },
  ];
  const verbsRef = useRef(verbs); verbsRef.current = verbs;
  const menuKey = JSON.stringify(verbs.map(verb => [verb.id, verb.label, verb.title, verb.enabled?.(null)]));
  const entries = useMemo(() => listVerbEntries(verbs.map(verb => ({ ...verb, run: () => verbsRef.current.find(current => current.id === verb.id)?.run(null) })), null), [menuKey]);
  const publish = () => { if (winId) publishListMenu(winId, "meeting-object", entries); };
  const facts = [
    { label: "Date", value: ledgerDate(current?.started_at).replace(/\b([A-Z])([A-Z]+)/g, (_, first: string, rest: string) => first + rest.toLowerCase()) },
    { label: "Time", value: clockTime(current?.started_at) },
    { label: "Length", value: durationToken(current?.duration_seconds ?? current?.duration).toLowerCase() },
    { label: "People", value: peopleNames(data.segments).join(", ") },
    { label: "Words", value: Number(current?.transcriptWords) > 0 ? Number(current?.transcriptWords).toLocaleString() : null },
    { label: "Unclear spans", value: Number(current?.unclearSpans) > 0 ? Number(current?.unclearSpans).toLocaleString() : null },
  ];
  const job = current?.intel_job as Record<string, unknown> | null, status = current?.intel_status as Record<string, unknown> | null;
  const failure = summaryFailureReason(current);
  const statusItems: (StatusBarItem | null)[] = [
    !meeting ? { key: "read", text: error ? "Meeting not read" : "Reading meeting…", lamp: error ? "fail" : undefined } : null,
    failure ? { key: "failed", text: "Summary failed", lamp: "fail", testId: "meeting-summary-state" } : null,
    running ? { key: "running", text: state === "queued" || state === "pending" ? "Summary queued" : "Summary running", lamp: "info", testId: "meeting-summary-state" } : null,
    summary.runRefusal ? { key: "refusal", lamp: "fail", text: summary.runRefusal.refusal.plainReason } : null,
    data.needsCount ? { key: "review", text: `${data.needsCount} to review`, lamp: "ask", testId: "meeting-review-count" } : null,
    unclearLampLabel(current) ? { key: "unclear", lamp: "ask", text: unclearLampLabel(current)!.replace(/^WARN · /, "").toLowerCase() } : null,
    ...taskStatus,
    receipt && !parkOutcome ? { key: "receipt", text: receipt.text, lamp: receipt.tone === "danger" ? "fail" : undefined } : null,
    !receipt && !taskStatus.length && summary.receipt ? { key: "summary-receipt", text: summary.receipt.text, lamp: summary.receipt.tone === "danger" ? "fail" : undefined, testId: "meetings-run-receipt" } : null,
  ];
  const outcomes = meetingOutcomes(data), since = readSinceLast(data.aftercare), looked = readRunReceipt(current)?.looked_at ?? [];
  const [contextPicked, setContextPicked] = useState<string | null>(null);
  const contextRows = [
    ...(since?.previous_meeting?.id ? [{ id: `meeting:${since.previous_meeting.id}`, name: since.previous_meeting.title || "Previous meeting", facts: sinceFacts(since) }] : []),
    ...looked.map(row => ({ id: row.ref, name: row.title || row.ref, facts: row.at?.slice(0, 10) || "" })),
    ...[...(since?.closed_actions ?? []), ...(since?.still_open_actions ?? []), ...(since?.new_actions ?? []), ...(since?.new_decisions ?? [])].map((row, index) => ({ id: typeof row.provenance?.segment_index === "number" ? `meeting:${meetingId}?segment=${row.provenance.segment_index}` : `meeting:${since?.previous_meeting?.id}#${index}`, name: row.task || row.decision || "Action", facts: row.owner || "" })),
  ];
  const tabs = [
    { id: "summary", label: "Summary" }, { id: "transcript", label: "Transcript" }, { id: "tasks", label: "Tasks" }, { id: "decisions", label: "Decisions" },
    ...(data.proposalRows.length ? [{ id: "proposals", label: "Proposals" }] : []),
    ...(outcomes.commitments.length ? [{ id: "commitments", label: "Commitments" }] : []),
    ...(data.prepared.length || data.canPrepare.length ? [{ id: "results", label: "Results" }] : []),
    ...(contextRows.length ? [{ id: "context", label: "Context" }] : []),
    { id: "facts", label: "Facts" }, { id: "recovery", label: "Recovery" },
  ];
  const tab = tabs.some(item => item.id === view) ? view : "summary";
  const active = !meeting ? <SurfaceState loading={!error} error={error || undefined} onRetry={() => void load()} />
    : view === "summary" ? running ? <PreferenceWell><PaneNotice><Elapsed start={String(status?.requested_at || job?.created_at || "")} /></PaneNotice>
      <LiveWell label="Summary work" working lines={[{ id: String(job?.id || meetingId), text: String(status?.detail || (state === "pending" || state === "queued" ? "Summary queued" : "Summary running")) }]} /></PreferenceWell>
      : <PreferenceWell><SummaryFailure meeting={current} retry={() => void summary.run(meetingId)} disabled={!canRun} />
        {hasSummary ? <><PaneNotice><ReadingDocument data-testid="meeting-summary">{intel!.summary!}</ReadingDocument></PaneNotice><RunAttempts receipt={readRunReceipt(current)} testId="summary-record-attempts" /></> : !failure ? <PaneNotice>{speechWasMissing(current) ? NO_TRANSCRIPT_SPEECH : "No summary"}</PaneNotice> : null}</PreferenceWell>
    : view === "transcript" ? <PreferenceWell><TranscriptWell seat id={meetingId} segments={data.segments} momentSegmentIndex={segment} /></PreferenceWell>
    : view === "tasks" ? tasks.inspector ?? tasks.list
    : view === "decisions" || view === "commitments" ? <MeetingOutcomes data={data} meeting={current!} mode={view} onDecide={() => setView("decide")} selection={outcomeSelections[meetingId + view]} onSelection={next => setOutcomeSelections(current => ({ ...current, [meetingId + view]: next }))} />
    : view === "proposals" ? <MeetingProposals data={data} />
    : view === "results" ? <PreparedResults initialPicked={preparedKind} onPick={setPreparedKind} noteIds={preparedNotes.current} meetingId={meetingId} results={data.prepared} canPrepare={data.canPrepare} selectionHash={route?.selection_hash} onChanged={data.refreshPrepared} />
    : view === "context" ? <ListView label="Meeting context" ordered selectedId={contextPicked} onSelect={setContextPicked} rows={contextRows.map(row => ({ ...row, kind: "source", cells: { facts: row.facts } }))}
      columns={[{ key: "name", word: "Source", track: "minmax(0,1fr)", priority: 100 }, { key: "facts", word: "Facts", track: "200px", priority: 20 }]} defaultVerb="open"
      verbs={[{ id: "open", label: "Open", enabled: row => Boolean(row), run: row => { if (row) openRef(row.id.split("#")[0]); } }]} />
    : view === "facts" ? <PreferenceWell><PaneNotice><InspectorFacts name={title || "Meeting"} header={false} rows={facts} /></PaneNotice></PreferenceWell>
    : <PreferenceWell><CaptureSlab detail={current} meeting={meeting} />
      <MeetingConflictRecovery meetingId={meetingId} onResolved={result => { if (result.deleted) onClose(); else refresh(); }} />
      <MeetingIntelRecovery meetingId={meetingId} revision={revision} onChanged={async () => refresh()} /></PreferenceWell>;
  return <PreferencePane label="Meeting" testId="meeting-record" data-feedback-redact="true">
    <MeetingObjectMenu windowId={winId} entries={entries} /><div onFocusCapture={publish}><Toolbar label="Meeting actions" data-testid="meeting-toolbar">
      {speechWasMissing(current) ? <AudioOnlyVerb row={current!} onTranscribe={async id => { await apiFetch(`/api/meetings/${encodeURIComponent(id)}/transcribe`, { method: "POST" }); refresh(); }} setUpSpeech testId="meeting-transcribe" /> : null}
      {verbs.slice(0, 2).map(verb => <Button key={verb.id} dense title={verb.title} data-testid={verb.testId} disabled={!verb.enabled?.(null)} onClick={() => verb.run(null)}>{verb.label}</Button>)}
      <Button ref={menuButton} dense aria-haspopup="menu" aria-expanded={menu} onClick={() => setMenu(!menu)}>Actions ▾</Button>
      {menu && menuButton.current ? <WorkMenu label="Meeting actions" x={menuButton.current.getBoundingClientRect().left} y={menuButton.current.getBoundingClientRect().bottom} entries={listVerbEntries(verbs.slice(2, -1), null)} autoFocus opener={menuButton.current} onClose={() => setMenu(false)} returnFocus={() => menuButton.current?.focus()} /> : null}
      <span ref={deleteSeat}><ConfirmVerb label="Delete" confirmLabel="Delete meeting?" targetId={meetingId} disabled={!meeting || busy || Boolean(meeting.parked)} busy={busy} onConfirm={park} data-testid="meeting-delete" /></span>
    </Toolbar></div>
    {view === "send" ? <div ref={sendSeat} className="surface-preference-pane"><SendWellReadContext.Provider value={sendRead}><MeetingSendWellLazy meetingId={meetingId} title={title || "Meeting"} startedAt={String(meeting?.started_at || "")} onBack={() => setView("summary")} /></SendWellReadContext.Provider></div>
      : view === "rename" ? <Rename meetingId={meetingId} title={title} onDone={refresh} close={() => setView("summary")} />
      : view === "project" ? <PreferenceWell><AddToProject meetingId={meetingId} autoOpen onReceipt={next => setReceipt({ text: next.text, tone: next.tone === "danger" ? "danger" : undefined, title: next.title })} /></PreferenceWell>
      : view === "decide" ? <PreferenceWell><MeetingDecideWell defaultOpen meetingId={meetingId} title={title || "Meeting"} summary={intel?.summary} /></PreferenceWell>
      : <SegmentedTabs label="Meeting contents" value={tab} onChange={setView} tabs={tabs}>{active}</SegmentedTabs>}
    {view !== "send" ? <StatusBar data-testid="meeting-status" items={statusItems} verbs={parkOutcome ? <ParkReceipt outcome={parkOutcome} onRestore={ids => void restore(ids)} data-testid="meeting-park-receipt" /> : null} /> : null}
  </PreferencePane>;
}

function Rename({ meetingId, title, onDone, close }: { meetingId: string; title: string; onDone(): void; close(): void }) {
  const [name, setName] = useState(title), [error, setError] = useState(""), [busy, setBusy] = useState(false);
  return <PaneInspector label="Rename meeting"><InspectorForm rows={[{ label: "Name", control: <StringGadget label="Name" value={name} onChange={setName} /> }]} notice={error ? <span role="alert">{error}</span> : null}
    completion={{ cancel: close, primary: { label: "Save", disabled: !name.trim() || busy, busy, run: async () => { setBusy(true); try { await renameMeeting(meetingId, name.trim()); onDone(); close(); } catch (cause) { setError(`Not saved · ${readableError(cause)}`); } finally { setBusy(false); } } } }} /></PaneInspector>;
}

/** Menu notifications stay below the object reader: a focused list republishes
 * its current selection after a render and must not cause its parent to render. */
function MeetingObjectMenu({ windowId, entries }: { windowId: string | null; entries: ReturnType<typeof listVerbEntries> }) {
  const menu = useListMenu(windowId);
  useEffect(() => {
    if (windowId && (!menu.length || ownsListMenu(windowId, "meeting-object")) && menu !== entries) publishListMenu(windowId, "meeting-object", entries);
  }, [windowId, entries, menu]);
  useEffect(() => () => { if (windowId) clearListMenu(windowId, "meeting-object"); }, [windowId]);
  return null;
}

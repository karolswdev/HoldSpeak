import { useWindowMast } from "../../desk/surface";
// PaneViews has no public nested-list boundary; keep the record View on its own toolbar.
import { PaneViewContext } from "../../desk/surface/patterns/PaneViews";
import { useGuideView } from "../../desk/walk/viewState";
import { SPEECH_SETUP_EVENT } from "../../desk/firstrun/SpeechSetup";
import { useEffect, useMemo, useRef, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import { openSourceRef } from "../../desk/surface/citations";
import type { CoreProps } from "./core-types";
import { apiFetch } from "../../lib/api";
import type { ListRead } from "../../desk/surface";
import { useResource } from "../pageSupport";
import {
  ParkReceipt,
  ListApp, useListApp, InspectorFacts, SurfaceState, PaneViews,
  parkedOutcome, notParkedOutcome, parkClock,
  type ListVerb,
  restoredOutcome,
  restoreFailedOutcome,
  type ParkOutcome,
} from "../../desk/surface";
import { parkMeeting } from "../../desk/api";
import {
  readPlannedRoute,
  routeOff,
  routeReady,
} from "../../meetings/summaryRoute";
import { useCoreWings } from "./core-hooks";
import { useRuntimeBus, useRuntimeFrame } from "../../runtime/RuntimeBus";
import { burstTimer } from "../../desk/burstTimer";
import { onReturnToTask } from "../../desk/returnToTask";
import { renderHeroSlot } from "./core-layout";
import {
  intelStateOf,
  ACTIVE_RUN_STATES, FINAL_RUN_STATES, adoptDurableRunReceipt,
  ImportSection, DoorSection, meetingFailed,
} from "./history";
import { useSummaryRun } from "./history/useSummaryRun";
import { IMPORT_ACCEPT } from "./history/importWhen";
import { RecordHome } from "./history/RecordHome";
import { StatusBar, countWords, type StatusBarItem } from "../../desk/surface/kit";
import { objectWindowStandIn } from "../../desk/objectWindows";
import { useWindowInterior } from "../../desk/surface/interior";
import { routeTitle } from "../../meetings/RouteDisclosure";
import { listMeetingState, meetingListRow, meetingColumns } from "./history/CatalogRail";
import { readMeetingIntel } from "../../meetings/MeetingSummarySlab";
import { MeetingPreview } from "./history/MeetingPreview";
import { MeetingWindow } from "../../desk/pullouts/MeetingWindow";
import { Token } from "../../desk/surface/Token";
import { MEETING_CHANGE_KINDS } from "../../desk/useDeskChangedRefresh";
import { frameNames } from "../../desk/components/window/dockState";

const LIST_WINGS = [
  { id: "outcomes", label: "Records" },
  { id: "deleted", label: "Deleted" },
  { id: "record", label: "Record" },
];

type Meeting = Record<string, unknown>;
const keyOf = (row: Meeting) => String(row.id);
function listRecord(saved: Meeting, previous?: Meeting): Meeting {
  return { ...previous, ...saved,
    duration_seconds: saved.duration_seconds ?? saved.duration ?? previous?.duration_seconds,
    has_summary: Boolean(readMeetingIntel(saved)?.summary?.trim()),
  };
}
async function readMeetings({ query, offset, limit }: ListRead) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (query) params.set("search", query);
  if (offset) params.set("offset", String(offset));
  const answer = await apiFetch<{ meetings?: Meeting[]; total?: number }>(`/api/meetings?${params}`);
  return { rows: answer.meetings ?? [], total: answer.total };
}
async function readDeleted() {
  const answer = await apiFetch<{ meetings?: Meeting[] }>("/api/meetings?parked=true");
  return { rows: answer.meetings ?? [] };
}
const findDeleted = (row: Meeting, query: string) => String(row.title ?? "").toLocaleLowerCase().includes(query);

export function HistoryCore({ hero, scope }: CoreProps) {
  const scopedMeetingId = scope?.startsWith("meeting:")
    ? scope.slice("meeting:".length).split(/[?#]/, 1)[0] || null
    : null;
  const recordingTarget = useRef(scopedMeetingId);
  recordingTarget.current = scopedMeetingId;
  const forwarded = useRef<string | null>(null);
  useEffect(() => {
    if (!scope?.startsWith("meeting:")) return;
    if (!scope.includes("?")) return;
    if (forwarded.current === scope) return;
    forwarded.current = scope;
    openSourceRef(scope);
  }, [scope]);
  const [recordedPreview, setRecordedPreview] = useState<string | null>(null);
  const wings = useCoreWings(LIST_WINGS, scope === "record" ? "record" : "outcomes", "Meeting plumbing", !scopedMeetingId || recordedPreview === scopedMeetingId);
  const [parkOutcome, setParkOutcome] = useState<ParkOutcome | null>(null);
  const meetings = useListApp({ read: readMeetings, keyOf });
  useWindowMast({ line: meetings.page ? countWords(meetings.total ?? meetings.rows.length, "meeting") ?? undefined : undefined, figures: [{ value: meetings.rows.reduce((n, row) => n + Number(row.needs_you_count ?? row.needsYouCount ?? 0), 0), label: "to review", tone: "ask" }] }, !scopedMeetingId || recordedPreview === scopedMeetingId);
  const deleted = useListApp({ read: readDeleted, keyOf, search: findDeleted });
  const parkedOn = wings.view === "deleted";
  const marked = meetings.picked;
  const [deleting, setDeleting] = useState(false);
  const deletingRef = useRef(false);
  const [previewView, setPreviewView] = useState("summary");
  useEffect(() => {
    setPreviewView(Number(meetings.selected?.needs_you_count) > 0 ? "tasks" : "summary");
  }, [marked]);
  const [taskStatus, setTaskStatus] = useState<StatusBarItem[]>([]);
  useEffect(() => { setTaskStatus([]); }, [marked]);
  const [sendRequest, setSendRequest] = useState(0);
  const [sending, setSending] = useState(false);
  const [handoffError, setHandoffError] = useState("");
  useGuideView(() => ({sendRequest,view:wings.view,doorOpen:wings.doorOpen}), saved => {setSendRequest(saved.sendRequest);wings.setView(saved.view);wings.setDoorOpen(saved.doorOpen);}, undefined, 1);
  useEffect(() => {
    if (scopedMeetingId) meetings.setPicked(scopedMeetingId);
  }, [scopedMeetingId]);
  const importPicker = useRef<HTMLInputElement | null>(null);
  const [importFile, setImportFile] = useState<File | null>(null);
  const startImport = (file: File | null | undefined) => {
    if (!file) return;
    setImportFile(file);
    wings.setDoorOpen(false);
    wings.setView("record");
  };
  useEffect(() => {
    if (wings.view !== "record") setImportFile(null);
  }, [wings.view]);

  const queueFrame = useRuntimeFrame<{ drainer?: string }>("runtime_queue");
  const drainerAbsent = queueFrame?.drainer === "absent";

  const doorActions = useResource<Record<string, unknown>>("/api/all-action-items", {});
  const doorSpeakers = useResource<Record<string, unknown>>("/api/speakers", {});
  const doorProjects = useResource<Record<string, unknown>>("/api/projects", {});
  const doorIntel = useResource<Record<string, unknown>>("/api/intel/jobs", {});
  const doorPlugin = useResource<Record<string, unknown>>("/api/plugin-jobs", {});
  const [queueStatus, setQueueStatus] = useState("pending");
  const meetingRows = meetings.rows;

  const reloadMeetings = meetings.reload;
  const summary = useSummaryRun(
    (meetingId) => readPlannedRoute(meetingRows.find((item) => String(item.id) === meetingId)),
    () => void reloadMeetings(),
  );
  const { receipt, setReceipt, settleRun, runningId, runRefusal } = summary;

  const seenActive = useRef<string | null>(null);
  const adoptedDurable = useRef(false);
  useEffect(() => {
    if (adoptedDurable.current || meetingRows.length === 0) return;
    adoptedDurable.current = true;
    const adopted = adoptDurableRunReceipt(meetingRows);
    if (!adopted) return;
    if (adopted.active && adopted.receipt.run) {
      seenActive.current = `${adopted.receipt.run.meetingId}:${adopted.receipt.run.jobId}`;
    }
    setReceipt((current) => current ?? adopted.receipt);
  }, [meetingRows, setReceipt]);
  useEffect(() => {
    const run = receipt?.run;
    if (!run) return;
    const row = meetingRows.find((item) => String(item.id) === run.meetingId);
    if (!row) return;
    const state = intelStateOf(row.intel_status);
    const key = `${run.meetingId}:${run.jobId}`;
    if (ACTIVE_RUN_STATES.has(state)) {
      seenActive.current = key;
      return;
    }
    if (FINAL_RUN_STATES.has(state) && seenActive.current === key) {
      seenActive.current = null;
      const job = row.intel_job as Record<string, unknown> | null | undefined;
      settleRun(run, state, typeof job?.updated_at === "string" ? job.updated_at : undefined);
    }
  }, [meetingRows, receipt, settleRun]);
  useEffect(() => {
    if (receipt) setParkOutcome(null);
  }, [receipt]);

  const reloadRef = useRef(reloadMeetings);
  reloadRef.current = async () => { await Promise.all([meetings.reload(), deleted.reload()]); };
  useEffect(() => {
    if (queueFrame) void reloadRef.current();
  }, [queueFrame]);
  const { subscribe: subscribeFrames } = useRuntimeBus();
  useEffect(() => {
    const refresh = () => void reloadRef.current();
    const burst = burstTimer(refresh, 300);
    const offDeskChanged = subscribeFrames("desk_changed", (frame) => {
      if (frameNames(frame?.data, MEETING_CHANGE_KINDS)) burst.bump();
    });
    const offAftercare = subscribeFrames("aftercare_ready", burst.bump);
    const offReturn = onReturnToTask(refresh);
    window.addEventListener("focus", refresh);
    window.addEventListener(SPEECH_SETUP_EVENT, refresh);
    return () => {
      window.removeEventListener(SPEECH_SETUP_EVENT, refresh);
      burst.cancel();
      offDeskChanged();
      offAftercare();
      offReturn();
      window.removeEventListener("focus", refresh);
    };
  }, [subscribeFrames]);

  const faceRoute = useMemo(
    () => readPlannedRoute(meetingRows.find((row) => readPlannedRoute(row))),
    [meetingRows],
  );
  const routeWord = faceRoute && !routeReady(faceRoute)
    ? (routeOff(faceRoute) ? "Summaries off" : "No engine for summaries")
    : null;

  const recordsFace = !wings.doorOpen && wings.view !== "record" && (!scopedMeetingId || recordedPreview === scopedMeetingId);
  useWindowInterior(recordsFace ? "list" : scopedMeetingId ? undefined : null);

  const showParkOutcome = (outcome: ParkOutcome) => {
    setReceipt(null);
    setParkOutcome(outcome);
  };
  const restoreParked = async (ids: string[]) => {
    if (deletingRef.current) return;
    deletingRef.current = true; setDeleting(true);
    try {
      for (const id of ids) {
        const answer = await apiFetch<{ meeting: Meeting }>(`/api/meetings/${encodeURIComponent(id)}/restore`, { method: "POST" });
        if (!answer.meeting?.id) throw new Error("Meeting not restored");
        meetings.apply(listRecord(answer.meeting, deleted.rows.find(row => String(row.id) === id)));
        deleted.drop(id);
      }
      showParkOutcome(restoredOutcome(ids));
      meetings.setQuery("");
      meetings.setPicked(ids[ids.length - 1] ?? null);
      wings.setView("outcomes");
    } catch {
      showParkOutcome(restoreFailedOutcome(ids));
    } finally { deletingRef.current = false; setDeleting(false); }
  };


  const tasksCount = meetingRows.reduce((sum, row) => sum + Number(row.needs_you_count ?? 0), 0);
  const needsCount = meetingRows.filter(meetingFailed).length;
  const taskFailed = taskStatus.some(part => part.lamp === "fail");
  const statusItems: StatusBarItem[] = [
    (parkedOn ? deleted.loading : meetings.loading) ? { key: "read", text: "Reading meetings…" } : null,
    ...(!parkedOn ? taskStatus.map(part => part.lamp === "fail" ? part : ({ ...part, lamp: part.lamp || (tasksCount ? "ask" as const : undefined), text: <>{part.text}{tasksCount ? ` · ${tasksCount} ${tasksCount === 1 ? "task" : "tasks"} to confirm` : ""}</> })) : []),
    { key: "count", text: countWords(parkedOn ? deleted.visible.length : meetings.visible.length, "meeting"), testId: "meetings-count" },
    (parkedOn ? deleted.selected : meetings.selected) && recordsFace ? { key: "selection", text: "1 selected" } : null,
    !parkedOn && !taskStatus.length && tasksCount ? { key: "tasks", lamp: "ask" as const, text: `${tasksCount} ${tasksCount === 1 ? "task" : "tasks"} to confirm` } : null,
    !parkedOn && !taskFailed && needsCount ? { key: "failed", lamp: "fail" as const, text: countWords(needsCount, "failed", "failed") } : null,
    !parkedOn && routeWord ? { key: "route", lamp: "warn" as const, text: routeWord, testId: "meetings-route-state" } : null,
    receipt && !parkedOn && !taskStatus.length
        ? {
            key: "receipt",
            text: (
              <Token className="surface-footer-receipt-line" data-words="" data-tone={receipt.tone} data-testid={receipt.run ? "meetings-run-receipt" : undefined} title={receipt.title || undefined}>
                {receipt.text}
              </Token>
            ),
          }
        : null,
  ].filter((item): item is NonNullable<typeof item> => Boolean(item)) as StatusBarItem[];

  const remove = async (id: string) => {
    if (deletingRef.current) return;
    deletingRef.current = true; setDeleting(true);
    try {
      await parkMeeting(id);
      const row = meetingRows.find((item) => String(item.id) === id);
      meetings.drop(id);
      if (row) deleted.apply(row);
      showParkOutcome(parkedOutcome([id], parkClock()));
      void deleted.reload();
    } catch {
      showParkOutcome(notParkedOutcome("Meeting not deleted", "Try again"));
    } finally { deletingRef.current = false; setDeleting(false); }
  };
  const selectedMeeting = meetings.selected;
  const verbs: ListVerb[] = [
    { enabled: () => true, id: "record", label: "Record", testId: "meetings-record", run: () => openSurfaceOr("record-live", "/live", scope) },
    { enabled: () => true, id: "import", label: "Import", testId: "meetings-import", run: () => importPicker.current?.click() },
    { id: "open", label: "Open", key: "Enter", enabled: (row) => Boolean(row), run: (row) => { if (row) { setRecordedPreview(null); openSourceRef(`meeting:${row.id}`); } } },
    { id: "send", label: "Send to…", testId: "meetings-send", enabled: (row) => Boolean(row && meetingRows.find((entry) => String(entry.id) === row.id)?.has_summary), run: () => setSendRequest((value) => value + 1) },
    { id: "summarise", label: "Summarise", title: routeTitle(readPlannedRoute(selectedMeeting)), enabled: (row) => {
      const meeting = meetingRows.find((entry) => String(entry.id) === row?.id);
      return Boolean(meeting && meeting.transcriptWords && routeReady(readPlannedRoute(meeting))
        && !ACTIVE_RUN_STATES.has(intelStateOf(meeting.intel_status)) && runningId !== row?.id);
    }, run: (row) => { if (row) void summary.run(row.id); } },
    { id: "delete", label: "Delete", key: "Delete", enabled: (row) => Boolean(row) && !deleting, run: (row) => { if (row) void remove(row.id); } },

  ];
  const restoreSelected: ListVerb["run"] = (row) => { if (row) void restoreParked([row.id]); };
  const deletedVerbs: ListVerb[] = [
    { id: "restore", label: "Restore", enabled: row => Boolean(row) && !deleting, run: restoreSelected },
    { id: "undo", label: "Undo", enabled: row => Boolean(row && parkOutcome?.kind === "parked" && parkOutcome.ids.includes(row.id)) && !deleting, run: restoreSelected },
  ];
  const collection = <ListApp app={parkedOn ? deleted : meetings} label="Meetings"
    ids={{ windowTestId: "meetings-collection", listTestId: "meetings-list", paneTestId: "meetings-preview", toolbarTestId: "meetings-toolbar", statusTestId: "meetings-status" }}
    words={{ find: "Find a meeting", empty: parkedOn ? "No deleted meetings" : "Record or import a meeting", noMatch: "No meeting matches", select: parkedOn ? "Select a deleted meeting" : "Select a meeting to read its summary." }}
    row={row => parkedOn ? { ...meetingListRow(row, { runningId: null }), state: undefined } : meetingListRow(row, { runningId, drainerAbsent, refusal: runRefusal?.meetingId === String(row.id) ? runRefusal.refusal : null })}
    list={{ columns: meetingColumns, verbs: parkedOn ? deletedVerbs : verbs, defaultVerb: parkedOn ? "restore" : "open", rowProps: row => ({ "data-testid": `meeting-row-${row.id}` }) }}
    onSelect={() => setSendRequest(0)} status={[]}
    pane={selected => !selected ? null : parkedOn
      ? <InspectorFacts name={String(selected.title || "Meeting")} rows={[{ label: "State", value: "Deleted" }]} />
      : <PaneViewContext.Provider value={null}><MeetingPreview key={marked} meeting={selected} onTaskStatus={setTaskStatus} view={previewView} onViewChange={setPreviewView} sendRequest={sendRequest} onSendState={setSending} onChanged={() => void reloadMeetings()}
          state={listMeetingState(selected, { runningId, drainerAbsent, refusal: runRefusal?.meetingId === marked ? runRefusal.refusal : null })?.label} /></PaneViewContext.Provider>}
  >
    {sending ? null : <StatusBar data-testid="meetings-status" items={statusItems}
      verbs={parkOutcome ? <ParkReceipt outcome={parkOutcome} onRestore={ids => void restoreParked(ids)} data-testid="meetings-park-receipt" /> : null} />}
  </ListApp>;
  const records = <PaneViews label="Meeting contents" value={parkedOn ? "details" : previewView} onChange={setPreviewView}
    tabs={parkedOn ? [{ id: "details", label: "Details" }] : [{ id: "summary", label: "Summary" }, { id: "tasks", label: "Tasks to confirm" }]}>{collection}</PaneViews>;
  const showRecorded = async () => {
    if (!scopedMeetingId) return;
    setHandoffError("");
    try {
      const saved = await apiFetch<Meeting>(`/api/meetings/${encodeURIComponent(scopedMeetingId)}`);
      if (recordingTarget.current !== scopedMeetingId) return;
      if (!saved.id) throw new Error("Meeting not read");
      meetings.apply(listRecord(saved));
      meetings.setQuery("");
      meetings.setPicked(scopedMeetingId);
      setRecordedPreview(scopedMeetingId);
    } catch {
      if (recordingTarget.current === scopedMeetingId) setHandoffError("Saved meeting not read");
    }
  };

  const pane = wings.doorOpen ? (
    <DoorSection actions={doorActions} speakers={doorSpeakers} projects={doorProjects} intel={doorIntel}
      plugin={doorPlugin} queueStatus={queueStatus} setQueueStatus={setQueueStatus} />
  ) : wings.view === "record" && !importFile ? (
    <RecordHome onRecord={() => openSurfaceOr("record-live", "/live", scope)} onImport={() => importPicker.current?.click()} />
  ) : wings.view === "record" ? (
    <ImportSection
      onDone={() => {
        setImportFile(null);
        wings.setView("outcomes");
      }}
      onImported={() => void meetings.reload()}
      scope={scope}
      initialFile={importFile}
    />
  ) : scopedMeetingId && handoffError ? (
    <SurfaceState error={handoffError} onRetry={() => void showRecorded()} />
  ) : scopedMeetingId ? (
    <MeetingWindow key={scopedMeetingId} object={objectWindowStandIn(`meeting:${scopedMeetingId}`)!}
      onRecorded={() => void showRecorded()}
      onClose={() => openSurfaceOr("review-meetings", "/history")} />
  ) : records;
  const showsMeeting = Boolean(scopedMeetingId) && !recordsFace && !wings.doorOpen && wings.view !== "record";

  return (
    <>
      {renderHeroSlot(hero, null)}
      <div
        className="surface-preference-pane"
        data-testid="meetings-drop"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          startImport(event.dataTransfer?.files?.[0]);
        }}
      >
        {recordsFace ? records : <div className="surface-preference-pane mt-pane" data-testid="meetings-pane">{pane}</div>}
        {/* Capture C7: the picker is mounted on every face, so Import on
            Meetings ▸ Record opens it too. */}
        <input
          ref={importPicker}
          type="file"
          hidden
          accept={IMPORT_ACCEPT}
          aria-label="Choose a recording or transcript"
          data-testid="meetings-import-picker"
          onChange={(event) => {
            startImport(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
      </div>
      {/* One foot per window: the picked meeting's own status bar, else this. */}
      {recordsFace || showsMeeting || sending ? null : (
        <StatusBar
          data-testid="meetings-status"
          verbs={parkOutcome && !parkedOn ? <ParkReceipt outcome={parkOutcome} onRestore={(ids) => void restoreParked(ids)} data-testid="meetings-park-receipt" /> : null}
          items={statusItems}
        />
      )}
    </>
  );
}

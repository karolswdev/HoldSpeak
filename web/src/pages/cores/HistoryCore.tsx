// Records uses the shared selection list and a bounded preview below it.
import { SPEECH_SETUP_EVENT } from "../../desk/firstrun/SpeechSetup";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import { openSourceRef } from "../../desk/surface/citations";
import type { CoreProps } from "./core-types";
import { asRows } from "../pageSupport";
import { useResource } from "../pageSupport";
import {
  ParkReceipt,
  ListPane,
  parkedOutcome, notParkedOutcome, parkClock,
  type ListVerb,
  restoredOutcome,
  restoreFailedOutcome,
  type ParkOutcome,
  type ParkedRow,
} from "../../desk/surface";
import { fetchParkedMeetings, restoreMeeting, parkMeeting } from "../../desk/api";
import { StringGadget } from "../../desk/surface";
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
  ledgerDate, intelStateOf,
  ACTIVE_RUN_STATES, FINAL_RUN_STATES, adoptDurableRunReceipt,
  ImportSection, CatalogRail, DoorSection, meetingFailed,
} from "./history";
import { useSummaryRun } from "./history/useSummaryRun";
import { IMPORT_ACCEPT } from "./history/importWhen";
import { RecordHome } from "./history/RecordHome";
import { StatusBar, countWords, type StatusBarItem } from "../../desk/surface/kit";
import { objectWindowStandIn } from "../../desk/objectWindows";
import { useWindowInterior } from "../../desk/surface/interior";
import { useMeetingList } from "./history/useMeetingList";
import { routeTitle } from "../../meetings/RouteDisclosure";
import { listMeetingState } from "./history/CatalogRail";
import { MeetingPreview } from "./history/MeetingPreview";
import { MeetingWindow } from "../../desk/pullouts/MeetingWindow";
import { Token } from "../../desk/surface/Token";
import { MEETING_CHANGE_KINDS } from "../../desk/useDeskChangedRefresh";
import { frameNames } from "../../desk/components/window/dockState";

/** PHILO-17: the list window's faces: the list, and Record (capture C7: the
 *  one home for recording; a chosen file opens the import form). Chrome lane
 *  2026-10-24: the title bar already says "Meetings", so the list wing says
 *  its own noun, "Records" (as the Activity window does). */
const LIST_WINGS = [
  { id: "outcomes", label: "Records" },
  { id: "record", label: "Record" },
];

export function HistoryCore({ hero, scope }: CoreProps) {
  const scopedMeetingId = scope?.startsWith("meeting:")
    ? scope.slice("meeting:".length).split(/[?#]/, 1)[0] || null
    : null;
  // PHILO-17: a meeting scope belongs to the meeting's own window (the store
  // routes it there); one that reaches this list is passed on, once.
  const forwarded = useRef<string | null>(null);
  useEffect(() => {
    if (!scope?.startsWith("meeting:")) return;
    // SurfaceWindows now owns the canonical `meeting:<id>` scope. Forward
    // only an old scoped request; sending the canonical scope back through
    // the opener remounts this list and can loop.
    if (!scope.includes("?")) return;
    if (forwarded.current === scope) return;
    forwarded.current = scope;
    openSourceRef(scope);
  }, [scope]);
  // The app's wings: Records (the rail and the meeting), Record (the one
  // home for recording, in the pane) and the plumbing door.
  const wings = useCoreWings(LIST_WINGS, scope === "record" ? "record" : "outcomes", "Meeting plumbing");
  // PHILO-13-02: Restore of a parked meeting; the outcome is a receipt in
  // the footer's receipt slot.
  const [parkOutcome, setParkOutcome] = useState<ParkOutcome | null>(null);
  const [parked, setParked] = useState<ParkedRow[]>([]);
  const [parkedOn, setParkedOn] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const deletingRef = useRef(false);
  // The rail marks the last meeting picked (Back returns to it) and the one
  // Restore brought back.
  const [marked, setMarked] = useState<string | null>(null);
  const [sendRequest, setSendRequest] = useState(0);
  const [sending, setSending] = useState(false);
  const [recordedPreview, setRecordedPreview] = useState<string | null>(null);
  useEffect(() => {
    if (scopedMeetingId) setMarked(scopedMeetingId);
  }, [scopedMeetingId]);
  // Capture C3: Import opens the file picker at once, and a file dropped on
  // the Meetings window does the same; the chosen file opens the import form.
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

  // Intelligence run state
  // HS-200-42 (counsel N1): the same drainer fact the Chair reads, from the
  // same frame, so the catalog's QUEUED token is not a claim that something
  // is about to run. `null` = no frame yet = unknown, never reported absent.
  const queueFrame = useRuntimeFrame<{ drainer?: string }>("runtime_queue");
  const drainerAbsent = queueFrame?.drainer === "absent";

  // HS-170-04: search (StringGadget with mic in the list head)
  const [searchQuery, setSearchQuery] = useState("");

  const meetingParams = useMemo(() => {
    const params = new URLSearchParams({ limit: "100" });
    if (searchQuery) params.set("search", searchQuery);
    return params;
  }, [searchQuery]);

  const meetings = useMeetingList(`/api/meetings?${meetingParams.toString()}`);

  // HS-170-04: gear door plumbing data (DoorSection)
  const doorActions = useResource<Record<string, unknown>>("/api/all-action-items", {});
  const doorSpeakers = useResource<Record<string, unknown>>("/api/speakers", {});
  // HS-200-03 follow-through: the Rooms list lives at /api/projects.
  const doorProjects = useResource<Record<string, unknown>>("/api/projects", {});
  const doorIntel = useResource<Record<string, unknown>>("/api/intel/jobs", {});
  const doorPlugin = useResource<Record<string, unknown>>("/api/plugin-jobs", {});
  const [queueStatus, setQueueStatus] = useState("pending");
  const meetingRows = useMemo(
    () => asRows(meetings.data, ["meetings"]),
    [meetings.data],
  );
  // PHILO-13-02: the parked meetings, read through H-A1's client.
  const loadParked = useCallback(async () => {
    try {
      const rows = await fetchParkedMeetings();
      setParked(rows.map((m) => ({ id: m.id, title: m.title, at: ledgerDate(m.startedAt) })));
    } catch {
      // The strip keeps its last read; the list's own state says the rest.
    }
  }, []);
  useEffect(() => {
    void loadParked();
  }, [loadParked, meetings.data]);
  useEffect(() => {
    if (!parked.length) setParkedOn(false);
  }, [parked.length]);

  // A row's Run summary (the record's own run lives in its window).
  const reloadMeetings = meetings.reload;
  const summary = useSummaryRun(
    (meetingId) => readPlannedRoute(meetingRows.find((item) => String(item.id) === meetingId)),
    () => void reloadMeetings(),
  );
  const { receipt, setReceipt, settleRun, runningId, runRefusal } = summary;

  // PHILO-15-07 (B15): a `QUEUED hh:mm` receipt is bound to its run. It
  // turns into `RAN · hh:mm` only for that run: from the poll, or when a
  // refreshed list row shows the meeting active and then final.
  const seenActive = useRef<string | null>(null);
  // Astra iteration 2 (reload): the face's first read of the rows adopts the
  // durable run state, so a reload never forgets the timed receipt.
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
  // A later receipt (a queued run) takes the slot from the restore outcome.
  useEffect(() => {
    if (receipt) setParkOutcome(null);
  }, [receipt]);

  /* ── the face re-reads itself (HS-202-02 job 2) ──
     `desk_changed`, a deferred summary's `aftercare_ready`, the return from
     a task and window focus re-read the list. The subscription is held for
     the life of the face (a ref keeps the reload current). */
  const reloadRef = useRef(reloadMeetings);
  reloadRef.current = reloadMeetings;
  // PHILO-17 (the autoflow lane): a summary that starts after an import moves
  // the queue, not the desk. The list reads again on the queue frame too, so
  // its row says what the meeting's window says (RUNNING, never IMPORTING).
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
    // PHILO-17 transcribe: speech set up in any window changes the
    // meetings' own Transcribe readiness (`transcribe_speech`).
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

  // HS-201-04 (UX-CANON A.9, audit "where the host is shown"): the footer
  // reads the same disclosed route every run verb on this face reads — the
  // SERVICE route for the next summary — and says so when there is none.
  const faceRoute = useMemo(
    () => readPlannedRoute(meetingRows.find((row) => readPlannedRoute(row))),
    [meetingRows],
  );
  // PHILO-13-04 (A3): a missing route is the AVAILABLE fact, not a place
  // data goes: the status bar says it with a lamp, never as an egress chip.
  const routeWord = faceRoute && !routeReady(faceRoute)
    ? (routeOff(faceRoute) ? "Summaries off" : "No engine for summaries")
    : null;

  // Window grammar: the Records face runs edge to edge (rail, pane, status
  // bar); Record, Import and the plumbing door keep the form inset.
  const recordsFace = !wings.doorOpen && wings.view !== "record" && (!scopedMeetingId || recordedPreview === scopedMeetingId);
  useWindowInterior(recordsFace ? "list" : scopedMeetingId ? undefined : null);

  // PHILO-13-02 (A1-F) — Restore (C1-5a–e).
  const showParkOutcome = (outcome: ParkOutcome) => {
    setReceipt(null);
    setParkOutcome(outcome);
  };
  const restoreParked = async (ids: string[]) => {
    if (deletingRef.current) return;
    deletingRef.current = true; setDeleting(true);
    try {
      await Promise.all(ids.map((id) => restoreMeeting(id)));
      showParkOutcome(restoredOutcome(ids));
      setParkedOn(false);
      setMarked(ids[ids.length - 1] ?? null);
      void meetings.reload();
      void loadParked();
    } catch {
      showParkOutcome(restoreFailedOutcome(ids));
    } finally { deletingRef.current = false; setDeleting(false); }
  };


  // The status bar's words (UX-CANON A.8: a zero is never said). With a
  // meeting picked, the meeting's own status bar is the window's foot.
  const tasksCount = meetingRows.reduce((sum, row) => sum + Number(row.needs_you_count ?? 0), 0);
  const needsCount = meetingRows.filter(meetingFailed).length;
  const statusItems: StatusBarItem[] = [
    { key: "count", text: countWords(parkedOn ? parked.length : meetingRows.length, "meeting"), testId: "meetings-count" },
    marked && (parkedOn ? parked.some((row) => row.id === marked) : meetingRows.some((row) => String(row.id) === marked)) && recordsFace ? { key: "selection", text: "1 selected" } : null,
    !parkedOn && tasksCount ? { key: "tasks", lamp: "ask" as const, text: `${tasksCount} ${tasksCount === 1 ? "task" : "tasks"} to confirm` } : null,
    !parkedOn && needsCount ? { key: "needs", lamp: "ask" as const, text: countWords(needsCount, "needs you", "need you") } : null,
    !parkedOn && routeWord ? { key: "route", lamp: "warn" as const, text: routeWord, testId: "meetings-route-state" } : null,
    receipt && !parkedOn
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
      meetings.setData((data) => ({ ...data, meetings: asRows(data, ["meetings"]).filter((row) => String(row.id) !== id) }));
      setMarked((current) => current === id ? null : current);
      showParkOutcome(parkedOutcome([id], parkClock()));
      void loadParked();
    } catch {
      showParkOutcome(notParkedOutcome("Meeting not deleted", "Try again"));
    } finally { deletingRef.current = false; setDeleting(false); }
  };
  const selectedMeeting = meetingRows.find((row) => String(row.id) === marked);
  const verbs: ListVerb[] = [
    { id: "record", label: "Record", testId: "meetings-record", run: () => openSurfaceOr("record-live", "/live", scope) },
    { id: "import", label: "Import", testId: "meetings-import", run: () => importPicker.current?.click() },
    { id: "open", label: "Open", key: "Enter", enabled: (row) => Boolean(row), run: (row) => { if (row) { setRecordedPreview(null); openSourceRef(`meeting:${row.id}`); } } },
    { id: "send", label: "Send to…", testId: "meetings-send", enabled: (row) => Boolean(row && meetingRows.find((entry) => String(entry.id) === row.id)?.has_summary), run: () => setSendRequest((value) => value + 1) },
    { id: "summarise", label: "Summarise", title: routeTitle(readPlannedRoute(selectedMeeting)), enabled: (row) => {
      const meeting = meetingRows.find((entry) => String(entry.id) === row?.id);
      return Boolean(meeting && meeting.transcriptWords && routeReady(readPlannedRoute(meeting))
        && !ACTIVE_RUN_STATES.has(intelStateOf(meeting.intel_status)) && runningId !== row?.id);
    }, run: (row) => { if (row) void summary.run(row.id); } },
    { id: "delete", label: "Delete", key: "Delete", enabled: (row) => Boolean(row) && !deleting, run: (row) => { if (row) void remove(row.id); } },
    ...(parked.length ? [{ id: "deleted", label: parkedOn ? "Records" : "Deleted…", run: () => { setParkedOn(!parkedOn); setMarked(null); } }] : []),
  ];
  const rail = <CatalogRail meetingRows={meetingRows} meetings={meetings} picked={marked} onPick={(row) => { setMarked(String(row.id)); setSendRequest(0); }}
    runningId={runningId} drainerAbsent={drainerAbsent} runRefusal={runRefusal} verbs={verbs}
    trailing={<StringGadget label="Find a meeting" value={searchQuery} onChange={setSearchQuery} placeholder="Find a meeting" />} />;
  const records = parkedOn ? <ListPane label="Deleted meeting" list={<CatalogRail
    meetingRows={parked.map((row) => ({ id: row.id, title: row.title, has_summary: true }))} meetings={meetings} picked={marked}
    onPick={(row) => { setMarked(String(row.id)); setSendRequest(0); }} runningId={null} verbs={[
      { id: "records", label: "Records", run: () => { setParkedOn(false); setMarked(null); } },
      { id: "restore", label: "Restore", enabled: (row) => Boolean(row) && !deleting, run: (row) => { if (row) void restoreParked([row.id]); } },
    ]} />}><p>Deleted meetings can be restored.</p></ListPane> : <ListPane list={rail} label="Meeting preview" listTestId="meetings-list" previewTestId="meetings-preview">
      {selectedMeeting ? <MeetingPreview key={marked} meeting={selectedMeeting} sendRequest={sendRequest} onSendState={setSending} onChanged={() => void reloadMeetings()} state={listMeetingState(selectedMeeting, { runningId, drainerAbsent, refusal: runRefusal?.meetingId === marked ? runRefusal.refusal : null })?.label} /> : <p>{meetingRows.length || meetings.error ? "Select a meeting to read its summary." : searchQuery ? "No meeting matches" : "Record or import a meeting"}</p>}
    </ListPane>;

  // The pane: the picked meeting (live while it records, else its record),
  // or one line and the verb that makes a meeting.
  const pane = wings.doorOpen ? (
    <DoorSection actions={doorActions} speakers={doorSpeakers} projects={doorProjects} intel={doorIntel}
      plugin={doorPlugin} queueStatus={queueStatus} setQueueStatus={setQueueStatus} />
  ) : wings.view === "record" && !importFile ? (
    // Capture C7: Meetings ▸ Record is the one home for recording. A chosen
    // file (Import, or a drop) opens the import form below.
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
  ) : scopedMeetingId ? (
    <MeetingWindow key={scopedMeetingId} object={objectWindowStandIn(`meeting:${scopedMeetingId}`)!}
      onRecorded={() => {
        setRecordedPreview(scopedMeetingId);
        setMarked(scopedMeetingId);
        void reloadMeetings();
      }}
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
      {showsMeeting || sending ? null : (
        <StatusBar
          data-testid="meetings-status"
          verbs={parkOutcome && !parkedOn ? <ParkReceipt outcome={parkOutcome} onRestore={(ids) => void restoreParked(ids)} data-testid="meetings-park-receipt" /> : null}
          items={statusItems}
        />
      )}
    </>
  );
}

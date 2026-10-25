// HS-170-04 — the Meetings face, rewritten to the settled design.
// PHILO-17 (owner 2026-10-10, "A meeting opens in one window"): the Meetings
// window owns the list and the selected meeting record. A row selects the
// record inside Meetings; its Back control returns to this list.
import { SPEECH_SETUP_EVENT } from "../../desk/firstrun/SpeechSetup";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import { openSourceRef } from "../../desk/surface/citations";
import type { CoreProps, MeetingsListResponse } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { asRows } from "../pageSupport";
import { useResource } from "../pageSupport";
import {
  ParkReceipt,
  ParkedStrip,
  restoredOutcome,
  restoreFailedOutcome,
  type ParkOutcome,
  type ParkedRow,
} from "../../desk/surface";
import { fetchParkedMeetings, restoreMeeting } from "../../desk/api";
import { EgressChip, StringGadget, CheckGadget } from "../../desk/surface/gadgets";
import {
  readPlannedRoute,
  routeOff,
  routeReady,
} from "../../meetings/summaryRoute";
import { egressFor } from "../../desk/surface/egress";
import { useCoreWings } from "./core-hooks";
import { useRuntimeBus, useRuntimeFrame } from "../../runtime/RuntimeBus";
import { burstTimer } from "../../desk/burstTimer";
import { onReturnToTask } from "../../desk/returnToTask";
import { renderHeroSlot } from "./core-layout";
import {
  ledgerDate, hasOpenMeetingActions, intelStateOf,
  ACTIVE_RUN_STATES, FINAL_RUN_STATES, adoptDurableRunReceipt,
  ImportSection, CatalogRail, DoorSection, meetingFailed,
} from "./history";
import { useSummaryRun } from "./history/useSummaryRun";
import { IMPORT_ACCEPT } from "./history/importWhen";
import { MeetingSelectionVerbs, meetingRowView } from "./history/CatalogRail";
import { RecordHome } from "./history/RecordHome";
import { StatusBar, ToolGlyph, Toolbar, countWords, type StatusBarItem } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { SYSTEM } from "../../desk/systemSprites";
import "./history/meetings-list.css";
import { MeetingWindow } from "../../desk/pullouts/MeetingWindow";
import { objectWindowStandIn } from "../../desk/objectWindows";

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
  const [selectedMeeting, setSelectedMeeting] = useState<Record<string, unknown> | null>(null);
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
  // The record owns its own wings and footer. Clearing the list wings while a
  // canonical meeting scope is active prevents two wing sets from competing
  // in the same Meetings window.
  const wings = useCoreWings(
    scopedMeetingId ? [] : LIST_WINGS,
    scope === "record" ? "record" : "outcomes",
    scopedMeetingId ? undefined : "Meeting plumbing",
    !scopedMeetingId,
  );
  // PHILO-13-02: Restore of a parked meeting; the outcome is a receipt in
  // the footer's receipt slot.
  const [parkOutcome, setParkOutcome] = useState<ParkOutcome | null>(null);
  const [parked, setParked] = useState<ParkedRow[]>([]);
  const [parkedOn, setParkedOn] = useState(false);
  const [restoredId, setRestoredId] = useState<string | null>(null);
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

  // HS-170-04: server-side facets (token toggles on the caption row)
  const [facets, setFacets] = useState<{
    date_from: string;
    date_to: string;
    speaker: string;
    tag: string;
    has_open_actions: boolean;
  }>({ date_from: "", date_to: "", speaker: "", tag: "", has_open_actions: false });
  const facetsResource = useResource<Record<string, unknown>>("/api/meetings/facets", {});

  // Build meeting params from search + facets.
  const meetingParams = useMemo(() => {
    const meetingParams = new URLSearchParams();
    meetingParams.set("limit", "100");
    const query = searchQuery;
    if (query) meetingParams.set("search", query);
    if (facets.date_from) meetingParams.set("date_from", facets.date_from);
    if (facets.date_to) meetingParams.set("date_to", facets.date_to);
    if (facets.speaker) meetingParams.set("speaker", facets.speaker);
    if (facets.tag) meetingParams.set("tag", facets.tag);
    if (facets.has_open_actions) meetingParams.set("has_open_actions", "true");
    return meetingParams;
  }, [searchQuery, facets]);

  const meetings = useResource<MeetingsListResponse>(
    `/api/meetings?${meetingParams.toString()}`, {},
  );

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
  useEffect(() => {
    if (!scopedMeetingId) return;
    const row = meetingRows.find((item) => String(item.id ?? "") === scopedMeetingId);
    if (row) setSelectedMeeting(row);
  }, [meetingRows, scopedMeetingId]);

  // Window grammar: a press selects the row (nothing opens); Enter or a
  // double press opens the meeting in this window.
  const selectMeeting = useCallback((row: Record<string, unknown> | null) => {
    setSelectedMeeting(row);
    if (row?.id) openSourceRef(`meeting:${String(row.id)}`);
  }, []);

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

  // HS-201-11: the HAS OPEN ACTIONS facet is drawn only when an open
  // action exists for it to find.
  const openActionsFacetDrawn = useMemo(
    () =>
      facets.has_open_actions ||
      hasOpenMeetingActions(asRows(doorActions.data, ["action_items"])),
    [facets.has_open_actions, doorActions.data],
  );

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
    const offDeskChanged = subscribeFrames("desk_changed", burst.bump);
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
  // PHILO-17 (U16): the foot names the summary engine; the rows do not say
  // the same host again (one chip per face).
  const footerHost = faceRoute && routeReady(faceRoute) ? egressFor(faceRoute.legs[0].host).label : null;
  // PHILO-13-04 (A3): a missing route is the AVAILABLE fact, not a place
  // data goes: the status bar says it with a lamp, never as an egress chip.
  const routeWord = faceRoute && !routeReady(faceRoute)
    ? (routeOff(faceRoute) ? "Summaries off" : "No engine for summaries")
    : null;
  const footerEgress = useMemo(() => {
    if (!faceRoute || !routeReady(faceRoute)) return null;
    const lead = egressFor(faceRoute.legs[0].host);
    return (
      <EgressChip
        label={lead.label}
        scope={lead.scope}
        title="Where a meeting summary runs."
      />
    );
  }, [faceRoute]);

  // PHILO-13-02 (C1-5d): the row Restore brought back is the selected row
  // (the list keeps it in view).
  useEffect(() => {
    if (!restoredId) return;
    const row = meetingRows.find((item) => String(item.id) === restoredId);
    if (row) setSelectedMeeting(row);
  }, [restoredId, meetingRows]);

  // Window grammar: the list face runs edge to edge (toolbar, list, status
  // bar); Record, Import and the plumbing door keep the form inset.
  const listFace = !scopedMeetingId && !wings.doorOpen && wings.view !== "record";
  // A meeting record says its own interior (MeetingRecord: edge to edge).
  useWindowInterior(scopedMeetingId ? undefined : listFace ? "list" : null);

  // SurfaceWindows routes `meeting:<id>` into this real core. Keep the list
  // mounted in the host, but draw the selected record in place so Back can
  // clear the scope and reveal the same list selection/state.
  if (scopedMeetingId) {
    return (
      <MeetingWindow
        key={scopedMeetingId}
        object={objectWindowStandIn(`meeting:${scopedMeetingId}`)!}
        onClose={() => openSurfaceOr("review-meetings", "/history")}
      />
    );
  }

  // PHILO-17 ALIVE: one obvious first move, ONE primary per window. With
  // no engine for summaries, Choose engine leads; else the selected
  // meeting's run verb leads when it can run; else Record meeting.
  const engineMissing = Boolean(faceRoute) && !routeReady(faceRoute) && !routeOff(faceRoute);
  const selectedRow = selectedMeeting
    ? meetingRows.find((row) => String(row.id) === String(selectedMeeting.id)) ?? null
    : null;
  const selectedRefusal = selectedRow && runRefusal && runRefusal.meetingId === String(selectedRow.id)
    ? runRefusal.refusal
    : null;
  const selectionRuns = Boolean(selectedRow) && ["Run summary", "Retry"].includes(
    meetingRowView(selectedRow!, { runningId, drainerAbsent, refusal: selectedRefusal }).verb ?? "",
  );
  const recordLeads = !engineMissing && !selectionRuns;

  // PHILO-13-02 (A1-F) — Restore (C1-5a–e).
  const showParkOutcome = (outcome: ParkOutcome) => {
    setReceipt(null);
    setParkOutcome(outcome);
  };
  const restoreParked = async (ids: string[]) => {
    try {
      await Promise.all(ids.map((id) => restoreMeeting(id)));
      showParkOutcome(restoredOutcome(ids));
      setParkedOn(false);
      setRestoredId(ids[ids.length - 1] ?? null);
      void meetings.reload();
      void loadParked();
    } catch {
      showParkOutcome(restoreFailedOutcome(ids));
    }
  };

  // PHILO-17 transcribe: the hub starts Transcribe on an audio-only meeting
  // (202); the face reads itself again now and on the worker's desk_changed.
  const transcribeMeeting = async (id: string) => {
    await apiFetch(`/api/meetings/${encodeURIComponent(id)}/transcribe`, { method: "POST" });
    await reloadMeetings();
  };

  // The toolbar verbs: icon + label (the Workbench way).
  const verbs = (
    <>
      {/* PHILO-17 ALIVE: a warning has its verb. With no engine for
          summaries, Choose engine is the first move (Runs on, on the
          Meeting summaries job). */}
      {engineMissing ? (
        <Button
          dense
          variant="primary"
          data-testid="meetings-choose-engine"
          onClick={() => openSurfaceOr("open-concierge", "/models", "meetings")}
        >
          <ToolGlyph kind="engine" />
          Choose engine
        </Button>
      ) : null}
      <Button
        dense
        variant={recordLeads ? "primary" : "secondary"}
        data-testid="meetings-record"
        onClick={() => openSurfaceOr("record-live", "/live", scope)}
      >
        <ToolGlyph kind="record" />
        Record meeting
      </Button>
      <Button
        dense
        variant="secondary"
        data-testid="meetings-import"
        onClick={() => importPicker.current?.click()}
      >
        <ToolGlyph kind="import" />
        Import
      </Button>
    </>
  );

  // The selected meeting's verbs sit at the status bar's right, beside the
  // route the run would use (egress where egress happens). Kept off the
  // toolbar so a selection never reflows the band above the list (a row
  // must stay under the pointer between the two presses of a double press).
  const selectionVerbs = selectedRow ? (
    <>
      <Button
        dense
        variant="secondary"
        data-testid="meetings-open"
        onClick={() => selectMeeting(selectedRow)}
      >
        <ToolGlyph kind="open" />
        Open
      </Button>
      <MeetingSelectionVerbs
        row={selectedRow}
        primary={!engineMissing && selectionRuns}
        saidOnFace={footerHost}
        onTranscribe={transcribeMeeting}
        onRunIntelligence={(id, route) => void summary.run(id, route)}
        runningId={runningId}
        drainerAbsent={drainerAbsent}
        refusal={selectedRefusal}
      />
    </>
  ) : null;

  // The status bar's words (UX-CANON A.8: a zero is never said).
  const failedCount = meetingRows.filter(meetingFailed).length;
  const reviewCount = meetingRows.reduce((sum, row) => sum + (Number(row.needs_you_count) || 0), 0);
  const statusItems: StatusBarItem[] = [
    { key: "count", text: countWords(meetingRows.length, "meeting"), testId: "meetings-count" },
    { key: "review", lamp: "ask" as const, text: countWords(reviewCount, "to review", "to review") },
    { key: "failed", lamp: "fail" as const, text: countWords(failedCount, "failed", "failed") },
    routeWord ? { key: "route", lamp: "warn" as const, text: routeWord, testId: "meetings-route-state" } : null,
    parkOutcome
      ? {
          key: "receipt",
          text: (
            <ParkReceipt
              outcome={parkOutcome}
              onRestore={(ids) => void restoreParked(ids)}
              data-testid="meetings-park-receipt"
            />
          ),
        }
      : receipt
        ? {
            key: "receipt",
            text: (
              <span className="surface-footer-receipt-line" data-tone={receipt.tone} data-testid={receipt.run ? "meetings-run-receipt" : undefined}>
                {receipt.text}
              </span>
            ),
          }
        : null,
  ].filter((item): item is NonNullable<typeof item> => Boolean(item)) as StatusBarItem[];

  const rail = (
    <CatalogRail
      meetingRows={meetingRows}
      meetings={meetings}
      selected={selectedMeeting}
      setSelected={setSelectedMeeting}
      onOpen={selectMeeting}
      runningId={runningId}
      drainerAbsent={drainerAbsent}
      runRefusal={runRefusal}
      emptyImage={SYSTEM.dockMeetings}
    />
  );

  const face = wings.doorOpen ? (
    <DoorSection
      actions={doorActions}
      speakers={doorSpeakers}
      projects={doorProjects}
      intel={doorIntel}
      plugin={doorPlugin}
      queueStatus={queueStatus}
      setQueueStatus={setQueueStatus}
    />
  ) : wings.view === "record" && !importFile ? (
    // Capture C7: Meetings ▸ Record is the one home for recording. A chosen
    // file (Import, or a drop) opens the import form below.
    <RecordHome
      onRecord={() => openSurfaceOr("record-live", "/live", scope)}
      onImport={() => importPicker.current?.click()}
    />
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
  ) : (
    <>
      {/* Window grammar: the toolbar under the title bar: verbs left, the
          search well and the open-actions filter right. */}
      <Toolbar
        label="Meetings"
        data-testid="meetings-toolbar"
        trailing={
          <>
            {/* HS-201-11: a filter that can match nothing is not drawn; it
                stays while it is ON (the way back). */}
            {openActionsFacetDrawn ? (
              <span className="meetings-facets" data-testid="meetings-facets">
                <CheckGadget
                  label="Open actions"
                  variant="token"
                  checked={facets.has_open_actions}
                  onChange={(next) => setFacets((f) => ({ ...f, has_open_actions: next }))}
                />
              </span>
            ) : null}
            {/* PHILO-13-02: the PARKED token (absent at zero); on, the
                parked rows take the list's place, each with Restore. */}
            <ParkedStrip
              rows={parked}
              on={parkedOn}
              onToggle={setParkedOn}
              onRestore={(ids) => void restoreParked(ids)}
              data-testid="meetings-parked"
            />
            <span className="meetings-search">
              <StringGadget
                label="Search meetings"
                value={searchQuery}
                onChange={setSearchQuery}
                placeholder="Search meetings"
              />
            </span>
          </>
        }
      >
        {verbs}
      </Toolbar>

      {/* The list view: a press selects, Enter or a double press opens. */}
      {parkedOn ? null : rail}
    </>
  );

  return (
    <>
      {renderHeroSlot(hero, null)}
      <div
        className="meetings-drop"
        data-testid="meetings-drop"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          startImport(event.dataTransfer?.files?.[0]);
        }}
      >
        {face}
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
      {/* Window grammar: the status bar says the count and the state in
          warm words (no zeros), the receipt beside them, and the engine's
          host at the right (egress where egress happens). */}
      <StatusBar
        data-testid="meetings-status"
        egress={footerEgress}
        verbs={listFace ? selectionVerbs : null}
        items={statusItems}
      />
    </>
  );
}

// HS-170-04 — the Meetings face, rewritten to the settled design.
// PHILO-17 (owner 2026-10-10, "A meeting opens in one window"): the Meetings
// window is the LIST (headline, Record/Import, search, filters, the stream).
// A row opens the meeting in its own window (`pullout:meeting:<id>`), which
// holds the whole record (history/MeetingRecord.tsx).
import { SPEECH_SETUP_EVENT } from "../../desk/firstrun/SpeechSetup";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import { openSourceRef } from "../../desk/surface/citations";
import type { CoreProps, MeetingsListResponse } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { asRows } from "../pageSupport";
import { useResource } from "../pageSupport";
import {
  countToken,
  ParkReceipt,
  ParkedStrip,
  restoredOutcome,
  restoreFailedOutcome,
  type ParkOutcome,
  type ParkedRow,
} from "../../desk/surface";
import { fetchParkedMeetings, restoreMeeting } from "../../desk/api";
import { EgressChip, StringGadget, CheckGadget } from "../../desk/surface/gadgets";
import { StateChip } from "../../desk/surface/patterns/StateChip";
import {
  readPlannedRoute,
  routeOff,
  routeReady,
  routeReasonToken,
} from "../../meetings/summaryRoute";
import { egressFor } from "../../desk/surface/egress";
import { useCoreWings } from "./core-hooks";
import { useRuntimeBus, useRuntimeFrame } from "../../runtime/RuntimeBus";
import { burstTimer } from "../../desk/burstTimer";
import { onReturnToTask } from "../../desk/returnToTask";
import { renderHeroSlot } from "./core-layout";
import {
  ledgerDate, meetingsHeadline, hasOpenMeetingActions, intelStateOf,
  ACTIVE_RUN_STATES, FINAL_RUN_STATES, adoptDurableRunReceipt,
  ImportSection, CatalogRail, DoorSection,
} from "./history";
import { useSummaryRun } from "./history/useSummaryRun";

/** PHILO-17: the list window's faces: the list, and Record (import). */
const LIST_WINGS = [
  { id: "outcomes", label: "Meetings" },
  { id: "record", label: "Record" },
];

/** A row opens its meeting's own window (an open one comes to the front). */
function openMeetingWindow(row: Record<string, unknown> | null): void {
  if (row?.id) openSourceRef(`meeting:${String(row.id)}`);
}

export function HistoryCore({ hero, scope }: CoreProps) {
  // PHILO-17: a meeting scope belongs to the meeting's own window (the store
  // routes it there); one that reaches this list is passed on, once.
  const forwarded = useRef<string | null>(null);
  useEffect(() => {
    if (!scope?.startsWith("meeting:") || forwarded.current === scope) return;
    forwarded.current = scope;
    openSourceRef(scope);
  }, [scope]);
  const wings = useCoreWings(LIST_WINGS, "outcomes", "Meeting plumbing");
  // PHILO-13-02: Restore of a parked meeting; the outcome is a receipt in
  // the footer's receipt slot.
  const [parkOutcome, setParkOutcome] = useState<ParkOutcome | null>(null);
  const [parked, setParked] = useState<ParkedRow[]>([]);
  const [parkedOn, setParkedOn] = useState(false);
  const [restoredId, setRestoredId] = useState<string | null>(null);

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
  const footerEgress = useMemo(() => {
    if (!faceRoute) return null;
    if (!routeReady(faceRoute)) {
      // PHILO-13-04 (A3): a missing route is the AVAILABLE fact, not a
      // place data goes; the egress chip drew it green (A.10).
      return (
        <StateChip
          state="warning"
          label={routeOff(faceRoute) ? "SUMMARIES OFF" : `NO SUMMARY ROUTE · ${routeReasonToken(faceRoute)}`}
        />
      );
    }
    const lead = egressFor(faceRoute.legs[0].host);
    return (
      <EgressChip
        label={lead.label}
        scope={lead.scope}
        title="Where a meeting summary runs."
      />
    );
  }, [faceRoute]);

  // The headline
  const headline = meetingsHeadline(
    meetingRows, meetings.loading,
    Boolean(faceRoute) && !routeReady(faceRoute) && !routeOff(faceRoute),
    routeOff(faceRoute),
  );

  // Verbs in the head
  const verbs = (
    <>
      {/* HS-201-04 (Astra's counsel finding 5; UX-CANON: one filled primary
          per face). The run verb on a row keeps the primary; `Record
          meeting` is the default species. */}
      <Button
        dense
        onClick={() => openSurfaceOr("record-live", "/live", scope)}
      >
        Record meeting
      </Button>
      <Button
        dense
        variant="ghost"
        onClick={() => {
          wings.setDoorOpen(false);
          wings.setView("record");
        }}
      >
        Import
      </Button>
    </>
  );

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

  const rail = (
    <CatalogRail
      saidOnFace={footerHost}
      onTranscribe={transcribeMeeting}
      meetingRows={meetingRows}
      restoredId={restoredId}
      meetings={meetings}
      selected={null}
      setSelected={openMeetingWindow}
      onRunIntelligence={(id, route) => void summary.run(id, route)}
      runningId={runningId}
      drainerAbsent={drainerAbsent}
      runRefusal={runRefusal}
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
  ) : wings.view === "record" ? (
    <ImportSection
      onDone={() => wings.setView("outcomes")}
      onImported={() => void meetings.reload()}
      scope={scope}
    />
  ) : (
    <>
      {/* HS-170-04: the headline (display step, ONE per face) */}
      <div className="meetings-headline" data-accent={headline.accent || undefined}>
        <span className="surface-display" data-testid="meetings-headline">
          {headline.text}
        </span>
      </div>

      {/* Head verbs */}
      <div className="meetings-head-verbs">
        {verbs}
      </div>

      {/* HS-170-04: search (StringGadget with mic in the list head) */}
      <div className="meetings-search">
        <StringGadget
          label="Search meetings"
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search meetings"
        />
      </div>

      {/* HS-170-04: server-side facets. HS-201-11: a filter that can match
          nothing is not drawn; it stays while it is ON (the way back). */}
      {openActionsFacetDrawn ? (
        <div className="meetings-facets" data-testid="meetings-facets">
          <CheckGadget
            label="HAS OPEN ACTIONS"
            variant="token"
            checked={facets.has_open_actions}
            onChange={(next) => setFacets((f) => ({ ...f, has_open_actions: next }))}
          />
        </div>
      ) : null}

      {/* PHILO-13-02: the PARKED token (absent at zero); on, the parked
          rows take the list's place, each with Restore. */}
      <ParkedStrip
        rows={parked}
        on={parkedOn}
        onToggle={setParkedOn}
        onRestore={(ids) => void restoreParked(ids)}
        data-testid="meetings-parked"
      />

      {/* The stream: a row opens the meeting's own window. */}
      {parkedOn ? null : <div className="surface-split-railed">{rail}</div>}
    </>
  );

  return (
    <>
      {renderHeroSlot(hero, null)}
      {face}
      <SurfaceFooter
        egress={footerEgress}
        receipt={
          parkOutcome ? (
            <ParkReceipt
              outcome={parkOutcome}
              onRestore={(ids) => void restoreParked(ids)}
              data-testid="meetings-park-receipt"
            />
          ) : (
            <span
              className="surface-footer-receipt-line"
              data-tone={receipt?.tone}
              role="status"
            >
              {receipt?.run ? (
                // PHILO-15-07 (coordinator ruling): the record count stays;
                // a fresh run receipt shows BESIDE it, count first.
                <>
                  {countToken(meetingRows.length, "RECORD") ?? "RECORDS"}
                  <span className="meetings-stream-dot" aria-hidden="true">{" · "}</span>
                  <span data-testid="meetings-run-receipt">{receipt.text}</span>
                </>
              ) : receipt
                ? receipt.text
                : countToken(meetingRows.length, "RECORD") ?? "RECORDS"}
            </span>
          )
        }
      />
    </>
  );
}

// HS-170-04 — the Meetings face, rewritten to the settled design.
// Board: display headline + Record/Import + stream rows + SurfaceSplit detail.
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps, MeetingsListResponse, MeetingDetailResponse } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { apiFetch, apiBlob, readableError } from "../../lib/api";
import { asRows } from "../pageSupport";
import { useResource } from "../pageSupport";
import { SurfaceSplit } from "../../desk/surface/Surface";
import {
  countToken,
  ParkReceipt,
  ParkedStrip,
  parkClock,
  parkedOutcome,
  restoredOutcome,
  restoreFailedOutcome,
  notParkedOutcome,
  type ParkOutcome,
  type ParkedRow,
} from "../../desk/surface";
import { fetchParkedMeetings, parkMeeting, restoreMeeting } from "../../desk/api";
import { writeFailureReason } from "../../desk/hooks/useWriteReceipt";
import { EgressChip, StringGadget, CheckGadget } from "../../desk/surface/gadgets";
import { StateChip } from "../../desk/surface/patterns/StateChip";
import {
  postSummaryRun,
  readPlannedRoute,
  routeOff,
  routeReady,
  routeReasonToken,
  type PlannedRoute,
  type SummaryRefusal,
} from "../../meetings/summaryRoute";
import { egressFor } from "../../desk/surface/egress";
import { useCoreWings } from "./core-hooks";
import { useRuntimeBus, useRuntimeFrame } from "../../runtime/RuntimeBus";
import { burstTimer } from "../../desk/burstTimer";
import { onReturnToTask } from "../../desk/returnToTask";
import { renderHeroSlot } from "./core-layout";
import {
  WINGS, clockTime, ledgerDate, download, needsIntelligence, summaryIsOff, meetingsHeadline,
  hasOpenMeetingActions, finishedRunReceipt, intelStateOf,
  ACTIVE_RUN_STATES, FINAL_RUN_STATES, type RunIdentity,
  type Receipt, type DetailView,
  MeetingDetail, ImportSection, CatalogRail, DoorSection,
} from "./history";

export function HistoryCore({ hero, scope }: CoreProps) {
  const requestedMeetingScope =
    scope && scope.startsWith("meeting:")
      ? scope.slice("meeting:".length)
      : null;
  const [requestedMeetingId, requestedMeetingQuery = ""] =
    requestedMeetingScope?.split("?", 2) ?? [null, ""];
  const requestedMomentSegment = requestedMeetingQuery
    ? Number(new URLSearchParams(requestedMeetingQuery).get("segment"))
    : null;
  const wings = useCoreWings(WINGS, "outcomes", "Meeting plumbing");
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);
  const markReadyRead = useCallback((meetingId: string) => {
    void apiFetch(`/api/meetings/${encodeURIComponent(meetingId)}/ready/read`, {
      method: "POST",
    }).catch((reason) => {
      setReceipt({
        text: `READY READ FAILED · ${readableError(reason)}`,
        tone: "danger",
      });
    });
  }, []);
  const openMeeting = useCallback((row: Record<string, unknown> | null) => {
    setSelected(row);
    if (row?.id) markReadyRead(String(row.id));
  }, [markReadyRead]);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  // PHILO-13-02 (A1-F): Park, never delete. One press, no confirm (Restore
  // undoes it); the outcome is a receipt in the footer's receipt slot.
  const [parking, setParking] = useState(false);
  const [parkOutcome, setParkOutcome] = useState<ParkOutcome | null>(null);
  const [parked, setParked] = useState<ParkedRow[]>([]);
  const [parkedOn, setParkedOn] = useState(false);
  const [restoredId, setRestoredId] = useState<string | null>(null);
  const parkTimes = useRef(new Map<string, string>());
  const [openedRequestedMeetingId, setOpenedRequestedMeetingId] = useState<
    string | null
  >(null);
  const [requestedMeetingError, setRequestedMeetingError] = useState("");
  // HS-200-12: `Open evidence` on the review wing lands on the outcomes face
  // scrolled to the proposal's segment.
  const [evidenceSegment, setEvidenceSegment] = useState<number | null>(null);

  // Intelligence run state
  // HS-200-42 (counsel N1): the same drainer fact the Chair reads, from the
  // same frame, so the catalog's QUEUED token is not a claim that something
  // is about to run. `null` = no frame yet = unknown, never reported absent.
  const queueFrame = useRuntimeFrame<{ drainer?: string }>("runtime_queue");
  const drainerAbsent = queueFrame?.drainer === "absent";
  const [runningId, setRunningId] = useState<string | null>(null);
  // HS-201-04: the hub's 409 refusal, kept as a refusal (code + plain
  // reason + the fresh route), never as an error surface.
  const [runRefusal, setRunRefusal] = useState<
    { meetingId: string; refusal: SummaryRefusal } | null
  >(null);

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
  // "/api/meetings/projects" matched no route (only
  // /api/meetings/{meeting_id}/projects and /api/meetings/facets exist),
  // so every /meetings arrival logged a console 404 and the door's
  // PROJECTS section drew from an error. Caught by
  // tests/e2e/test_hs144_door_glass.py::test_meetings_deep_link_waits_for_registered_surface_x15.
  const doorProjects = useResource<Record<string, unknown>>("/api/projects", {});
  const doorIntel = useResource<Record<string, unknown>>("/api/intel/jobs", {});
  const doorPlugin = useResource<Record<string, unknown>>("/api/plugin-jobs", {});
  const [queueStatus, setQueueStatus] = useState("pending");
  const meetingRows = useMemo(
    () => asRows(meetings.data, ["meetings"]),
    [meetings.data],
  );

  // PHILO-13-02: the parked meetings, read through H-A1's client. A row
  // parked here shows its park time; one parked earlier shows its date.
  const loadParked = useCallback(async () => {
    try {
      const rows = await fetchParkedMeetings();
      setParked(
        rows.map((m) => ({
          id: m.id,
          title: m.title,
          at: parkTimes.current.get(m.id) ?? ledgerDate(m.startedAt),
        })),
      );
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
  // PHILO-15-07 (B15): a `QUEUED hh:mm` receipt is bound to its run
  // (meeting id + job id, Astra r1 on #982). It turns into `RAN · hh:mm` only
  // for that run: from the poll below, or when a refreshed list row shows
  // the meeting active and then final (a row read before the run started
  // still holds the PREVIOUS run's final state and never counts).
  const settleRun = useCallback((run: RunIdentity, state: string) => {
    setReceipt((current) =>
      current?.run &&
      current.run.meetingId === run.meetingId &&
      current.run.jobId === run.jobId
        ? finishedRunReceipt(state, new Date().toISOString())
        : current,
    );
  }, []);
  const seenActive = useRef<string | null>(null);
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
      settleRun(run, state);
    }
  }, [meetingRows, receipt, settleRun]);
  // A later receipt (export, queued run) takes the slot from the park outcome.
  useEffect(() => {
    if (receipt) setParkOutcome(null);
  }, [receipt]);

  // HS-201-11: the HAS OPEN ACTIONS facet is drawn only when an open
  // action exists for it to find. `/api/all-action-items` already reaches
  // this face for the gear door and answers OPEN items alone.
  const openActionsFacetDrawn = useMemo(
    () =>
      facets.has_open_actions ||
      hasOpenMeetingActions(asRows(doorActions.data, ["action_items"])),
    [facets.has_open_actions, doorActions.data],
  );

  // Open requested meeting from scope
  const requestedMeeting = useMemo(
    () =>
      requestedMeetingId
        ? (meetingRows.find(
            (row) => String(row.id) === requestedMeetingId,
          ) ?? null)
        : null,
    [meetingRows, requestedMeetingId],
  );
  useEffect(() => {
    if (
      !requestedMeetingId ||
      openedRequestedMeetingId === requestedMeetingId ||
      meetings.loading
    )
      return;
    setOpenedRequestedMeetingId(requestedMeetingId);
    setRequestedMeetingError("");
    wings.setView("outcomes");
    if (requestedMeeting) {
      setSelected(requestedMeeting);
      markReadyRead(requestedMeetingId);
      return;
    }
    void apiFetch<MeetingDetailResponse>(
      `/api/meetings/${encodeURIComponent(requestedMeetingId)}`,
    )
      .then((detail) => {
        setSelected(detail);
        markReadyRead(requestedMeetingId);
      })
      .catch((reason) => setRequestedMeetingError(readableError(reason)));
  }, [
    meetings.loading,
    openedRequestedMeetingId,
    requestedMeeting,
    markReadyRead,
    requestedMeetingId,
  ]);

  /* ── the face re-reads itself (HS-202-02 job 2) ──
     The sober eye set the engine and the record did not change; he ran
     the summary and the record did not change; a browser reload was the
     only thing that moved either (04-sober-eye.md, rank 2). This face
     subscribed to one frame, `runtime_queue`, which names neither event,
     and the open record is a snapshot object that only a click replaced —
     so even a ledger reload could not repaint it.

     What actually carries the news:
      - an assignment write publishes NO server frame
        (holdspeak/services/inference_assignment_service.py), so the
        signal is the client's `holdspeak:settings-updated` return event,
        the one ChairHome has read since HS-201-01;
      - a deferred intel job's completion publishes `aftercare_ready`
        (holdspeak/intel_queue_conductor.py:96).
     `desk_changed` and window focus cover everything else. */
  const selectedId = selected ? String(selected.id ?? "") : "";
  const reloadMeetings = meetings.reload;
  /* HS-202-02 (Astra's counsel finding 3) — two rules here, both learned
     the hard way:

     1. the response is only for the record still OPEN. Start refreshing A,
        select B, let A resolve, and an unconditional `setSelected` put A
        back on the glass under B's row.
     2. MERGE, never replace. The ledger row and `/api/meetings/{id}` are
        different shapes — the detail path carries raw dicts and no
        `transcriptWords` (`services/meeting_service.py:788`), which the
        face's own `needsIntelligence` gate reads. Replacing the row with
        the detail silently withdrew `Run summary` from a meeting that had
        just gained a transcript (caught by the first-use smoke's
        `import-refresh` leg). The reloaded LIST row is the same shape the
        click put there, so it is preferred; the detail read is the
        fallback for a deep-linked meeting the list does not hold. */
  const keepOpen = useCallback(
    (id: string, patch: Record<string, unknown>) =>
      setSelected((current) => {
        if (!current || String(current.id ?? "") !== id) return current;
        return { ...current, ...patch };
      }),
    [],
  );
  const refreshFace = useCallback(async () => {
    const list = await reloadMeetings();
    if (!selectedId) return;
    const row = asRows(list ?? {}, ["meetings"]).find(
      (item) => String(item.id) === selectedId,
    );
    if (row) {
      keepOpen(selectedId, row);
      return;
    }
    try {
      const fresh = await apiFetch<MeetingDetailResponse>(
        `/api/meetings/${encodeURIComponent(selectedId)}`,
      );
      keepOpen(selectedId, fresh as Record<string, unknown>);
    } catch {
      // The ledger still reloaded; the record keeps what it has and the
      // next signal tries again. A failed re-read is never an error face.
    }
  }, [keepOpen, reloadMeetings, selectedId]);

  /* HS-202-02 — the open record FOLLOWS the ledger, whatever moved it.
     `refreshFace` merges only into a record that is already open, so a
     list read that was in flight when the owner clicked (or a re-read the
     search box started) lands its fresh rows AFTER `selected` was frozen,
     and no later frame arrives to reconcile them. The record then wears a
     snapshot the ledger beside it has already replaced. Guarded twice:
     by id, so a row for a record the owner left is dropped, and by
     content, so an unchanged row keeps the same object and the record's
     own reads are not re-fetched on every reload. */
  useEffect(() => {
    if (!selectedId) return;
    const row = meetingRows.find((item) => String(item.id) === selectedId);
    if (!row) return;
    setSelected((current) => {
      if (!current || String(current.id ?? "") !== selectedId) return current;
      const moved = Object.keys(row).some(
        (key) => JSON.stringify(current[key]) !== JSON.stringify(row[key]),
      );
      return moved ? { ...current, ...row } : current;
    });
  }, [meetingRows, selectedId]);

  const { subscribe: subscribeFrames } = useRuntimeBus();
  /* HS-202-02 (the first-use smoke's `import-refresh` leg) — the
     subscription is held for the life of the face, and the debounce with
     it. `refreshFace` changes whenever the open record changes, so an
     effect that listed it as a dependency tore itself down and
     `clearTimeout`-ed the pending refresh every time the owner clicked a
     row. The import worker announces the desk change the instant the
     transcript lands (`services/meeting_service.py:285`) — before the
     owner opens the row it just changed — so THAT announcement was the
     one the click cancelled: the ledger was never re-read, the record
     kept the `importing` snapshot the click had taken, and `Run summary`
     stayed off the record until a reopen. The ref keeps the callback
     current without making the subscription depend on it. */
  const refreshRef = useRef(refreshFace);
  refreshRef.current = refreshFace;
  useEffect(() => {
    const refresh = () => void refreshRef.current();
    const burst = burstTimer(refresh, 300);
    const bump = burst.bump;
    const offDeskChanged = subscribeFrames("desk_changed", bump);
    const offAftercare = subscribeFrames("aftercare_ready", bump);
    const offReturn = onReturnToTask(refresh);
    window.addEventListener("focus", refresh);
    return () => {
      burst.cancel();
      offDeskChanged();
      offAftercare();
      offReturn();
      window.removeEventListener("focus", refresh);
    };
  }, [subscribeFrames]);

  // Run the summary of a meeting
  const handleRunIntelligence = useCallback(async (
    meetingId: string,
    displayed?: PlannedRoute | null,
  ) => {
    setRunningId(meetingId);
    setRunRefusal(null);
    // HS-201-04 (lane A's interlock): the route the face DISCLOSED is the
    // route the request binds — the same object, never a second lookup.
    // Astra's counsel finding 1: reading it from the list row sent an EMPTY
    // hash for a deep-linked meeting the list never loaded, while the
    // record displayed its own fetched route beside the verb.
    const row = meetingRows.find((item) => String(item.id) === meetingId);
    const route = displayed ?? readPlannedRoute(row);
    try {
      const outcome = await postSummaryRun<{
        jobId: string;
        state: string;
        host: string;
        drainer?: string;
      }>(
        `/api/meetings/${encodeURIComponent(meetingId)}/intelligence/run`,
        route,
      );
      if (!outcome.ok) {
        // A refusal is a refusal, with its plain reason — never an error
        // surface, and it never erases the receipt of an earlier real run.
        setRunningId(null);
        setRunRefusal({ meetingId, refusal: outcome.refusal });
        setReceipt({
          text: `REFUSED · ${outcome.refusal.plainReason}`,
          tone: "danger",
        });
        void refreshFace();
        return;
      }
      const result = outcome.result;
      const run: RunIdentity = { meetingId, jobId: String(result.jobId ?? meetingId) };
      setReceipt({ text: `QUEUED ${clockTime(new Date().toISOString())}`, run });
      // HS-200-42: when the route says no drainer exists, polling every 3s for
      // 120s is a lie told forty times — nothing in the hub will move this job.
      // Stop the poll and refresh the row once.
      //
      // `runningId` is deliberately LEFT SET: where the run egresses is a
      // fact the click established and it is owed to the user whether or
      // not a drainer exists (HS-170 S-3). HS-201-04 moved that fact to the
      // row's own disclosed route (`row-route`), which says it through the
      // one egress mapper instead of echoing the POST response's raw host.
      // The row's token stays honest: NOT DRAINING rather than RUNNING.
      if (result.drainer !== "running") {
        void refreshFace();
        return;
      }
      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const statusResp = await apiFetch<MeetingDetailResponse>(
            `/api/meetings/${encodeURIComponent(meetingId)}`,
          );
          const intelStatus = statusResp?.intel_status;
          const state = typeof intelStatus === "object" && intelStatus !== null
            ? String((intelStatus as Record<string, unknown>).state ?? "")
            : String(intelStatus ?? "");
          if (state !== "queued" && state !== "running" && state !== "pending") {
            clearInterval(poll);
            setRunningId(null);
            // PHILO-15-07 (B15): this run's receipt (and only this run's)
            // follows it to the final state. It said `QUEUED 10:59` after
            // the summary RAN.
            settleRun(run, state);
            void refreshFace();
          }
        } catch {
          clearInterval(poll);
          setRunningId(null);
        }
      }, 3000);
      // Safety timeout
      setTimeout(() => {
        clearInterval(poll);
        setRunningId((current) => {
          if (current === meetingId) {
            void refreshFace();
            return null;
          }
          return current;
        });
      }, 120_000);
    } catch (reason) {
      setRunningId(null);
      const msg = readableError(reason);
      setReceipt({ text: `REFUSED · ${msg}`, tone: "danger" });
    }
  }, [meetings, meetingRows, settleRun]);

  // HS-201-04 (UX-CANON A.9, audit "where the host is shown"): the footer
  // chip was a prop-less constant that always read "This device". It reads
  // the same disclosed route every run verb on this face reads — the
  // SERVICE route for the next summary — and says so when there is none.
  const faceRoute = useMemo(
    () => readPlannedRoute(meetingRows.find((row) => readPlannedRoute(row))),
    [meetingRows],
  );
  const footerEgress = useMemo(() => {
    // Astra's counsel finding 4: a constant `<EgressChip />` is not
    // evidence of local execution. With no route read at all, the footer
    // says nothing; with an unresolved one it says the reason.
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
          per face). The Meetings face already draws a filled primary on the
          row and the record that need a summary — the thing the headline is
          pointing at. `Record meeting` is the way IN to this face, offered
          again on the Chair's own capture bar as its filled verb, so here it
          is the default species and the run verb keeps the primary. */}
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

  // Footer export verbs
  const exportMeeting = async (format: string) => {
    if (!selected) return;
    const id = String(selected.id);
    try {
      download(
        await apiBlob(
          `/api/meetings/${encodeURIComponent(id)}/export?format=${format}`,
        ),
        `holdspeak-meeting-${id}.${format === "markdown" ? "md" : format}`,
      );
      setReceipt({
        text: `EXPORTED ${format === "markdown" ? "MD" : format.toUpperCase()} ${clockTime(new Date().toISOString())}`,
      });
    } catch (reason) {
      setReceipt({
        text: `REFUSED · ${readableError(reason)}`,
        tone: "danger",
      });
    }
  };
  // PHILO-13-02 (A1-F) — Park and Restore (C1-5a–e).
  const showParkOutcome = (outcome: ParkOutcome) => {
    setReceipt(null);
    setParkOutcome(outcome);
  };
  const parkSelected = async () => {
    if (!selected) return;
    const id = String(selected.id);
    setParking(true);
    try {
      await parkMeeting(id);
      const at = parkClock();
      parkTimes.current.set(id, at);
      setSelected(null);
      showParkOutcome(parkedOutcome([id], at));
      void meetings.reload();
      void loadParked();
    } catch (reason) {
      showParkOutcome(notParkedOutcome(writeFailureReason(reason)));
    } finally {
      setParking(false);
    }
  };
  const restoreParked = async (ids: string[]) => {
    try {
      await Promise.all(ids.map((id) => restoreMeeting(id)));
      for (const id of ids) parkTimes.current.delete(id);
      showParkOutcome(restoredOutcome(ids));
      setParkedOn(false);
      setRestoredId(ids[ids.length - 1] ?? null);
      void meetings.reload();
      void loadParked();
    } catch {
      showParkOutcome(restoreFailedOutcome(ids));
    }
  };

  const rail = (
    <CatalogRail
      meetingRows={meetingRows}
      restoredId={restoredId}
      meetings={meetings}
      selected={selected}
      setSelected={openMeeting}
      onRunIntelligence={(id, route) => void handleRunIntelligence(id, route)}
      runningId={runningId}
      drainerAbsent={drainerAbsent}
      runRefusal={runRefusal}
      narrowed={Boolean(selected)}
    />
  );

  const detailPane = (paneView: DetailView) => (
    <MeetingDetail
      meeting={selected}
      view={paneView}
      momentSegmentIndex={evidenceSegment ?? requestedMomentSegment}
      onClose={() => setSelected(null)}
      onDeleted={() => void meetings.reload()}
      onReceipt={setReceipt}
      footerRunReceipt={
        receipt?.run && selected && receipt.run.meetingId === String(selected.id)
          ? receipt
          : null
      }
      runRefusal={
        runRefusal && selected && runRefusal.meetingId === String(selected.id)
          ? runRefusal.refusal
          : null
      }
      onRunIntelligence={
        // HS-201-04: a FAILED record's Retry is owned by the summary slab
        // (`MeetingIntelRecovery`), which runs it through the recovery
        // route with the same disclosed hash. NEEDS YOU must not draw a
        // SECOND Retry/Skip pair beside it (tenet 3, one verb per job).
        /* HS-202-02 (coordinator item 9): `needsIntelligence` reads
           `transcriptWords`, a LIST-only field. The open record's own
           transcript comes from the detail read, so a row clicked while
           its import was still running withheld `Run summary` even after
           the transcript was plainly on the glass. The gate here asks
           only whether the summary is OFF; `NeedsYouTable` owns the
           `hasTranscript` half and reads the real segments
           (`history/NeedsYouTable.tsx:51-56`). */
        selected && (summaryIsOff(selected) || paneView === "review")
          ? (displayed: PlannedRoute | null) =>
              void handleRunIntelligence(String(selected.id), displayed)
          : undefined
      }
      onReview={() => {
        wings.setDoorOpen(false);
        wings.setView("review");
      }}
      onOpenEvidence={(segmentIndex) => {
        setEvidenceSegment(segmentIndex);
        wings.setDoorOpen(false);
        wings.setView("outcomes");
      }}
    />
  );
  // HS-200-12: the review wing draws its own footer (egress where the
  // extraction happened, the receipt, `Accept reviewed`).
  const reviewOwnsFooter = wings.view === "review" && Boolean(selected) && !wings.doorOpen;

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
  ) : wings.view === "artifacts" ? (
    selected ? (
      detailPane("artifacts")
    ) : (
      rail
    )
  ) : wings.view === "review" ? (
    selected ? (
      detailPane("review")
    ) : (
      rail
    )
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

      {/* HS-170-04: server-side facets (token toggles on the caption row).
          HS-201-11: a filter that can match nothing is not drawn -- the
          desk held one meeting with zero actions and still offered
          `HAS OPEN ACTIONS`. It stays on the face while it is ON, so the
          owner always has the way back. */}
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

      {/* The stream + detail split */}
      <div className="surface-split-railed">
        <SurfaceSplit
          main={parkedOn ? null : rail}
          detailOpen={Boolean(selected)}
          detail={detailPane("outcomes")}
        />
      </div>
    </>
  );

  return (
    <>
      {renderHeroSlot(hero, null)}
      {requestedMeetingError ? (
        <div className="surface-state-error">
          <span>{requestedMeetingError}</span>
          <Button dense variant="ghost" onClick={() => {
            setRequestedMeetingError("");
            setOpenedRequestedMeetingId(null);
          }}>
            Retry
          </Button>
        </div>
      ) : null}
      {face}
      {reviewOwnsFooter ? null : <SurfaceFooter
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
              {receipt
                ? receipt.text
                : countToken(meetingRows.length, "RECORD") ?? "RECORDS"}
            </span>
          )
        }
        verbs={
          selected && wings.view !== "record" ? (
            <span className="surface-footer-verbs-group">
              <Button dense variant="ghost" onClick={() => void exportMeeting("markdown")}>
                MD
              </Button>
              <Button dense variant="ghost" onClick={() => void exportMeeting("srt")}>
                SRT
              </Button>
              <Button
                dense
                variant="ghost"
                disabled={parking}
                onClick={() => void parkSelected()}
              >
                Park
              </Button>
            </span>
          ) : null
        }
      />}
    </>
  );
}

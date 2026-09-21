// HS-170-04 — the Meetings face, rewritten to the settled design.
// Board: display headline + Record/Import + stream rows + SurfaceSplit detail.
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useCallback, useEffect, useMemo, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps, MeetingsListResponse, MeetingDetailResponse } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { apiFetch, apiBlob, readableError } from "../../lib/api";
import { asRows } from "../pageSupport";
import { useResource } from "../pageSupport";
import { ConfirmVerb, SurfaceSplit } from "../../desk/surface/Surface";
import { countToken } from "../../desk/surface";
import { EgressChip, StringGadget, CheckGadget } from "../../desk/surface/gadgets";
import {
  postSummaryRun,
  readPlannedRoute,
  routeReady,
  routeReasonToken,
  type PlannedRoute,
  type SummaryRefusal,
} from "../../meetings/summaryRoute";
import { egressFor } from "../../desk/surface/egress";
import { useCoreWings } from "./core-hooks";
import { useRuntimeBus, useRuntimeFrame } from "../../runtime/RuntimeBus";
import { onReturnToTask } from "../../desk/returnToTask";
import { renderHeroSlot } from "./core-layout";
import {
  WINGS, clockTime, download, needsIntelligence, summaryIsOff, meetingsHeadline,
  hasOpenMeetingActions,
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
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [removing, setRemoving] = useState(false);
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
      return;
    }
    void apiFetch<MeetingDetailResponse>(
      `/api/meetings/${encodeURIComponent(requestedMeetingId)}`,
    )
      .then(setSelected)
      .catch((reason) => setRequestedMeetingError(readableError(reason)));
  }, [
    meetings.loading,
    openedRequestedMeetingId,
    requestedMeeting,
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

  const { subscribe: subscribeFrames } = useRuntimeBus();
  useEffect(() => {
    let timer = 0;
    const bump = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => void refreshFace(), 300);
    };
    const offDeskChanged = subscribeFrames("desk_changed", bump);
    const offAftercare = subscribeFrames("aftercare_ready", bump);
    const offReturn = onReturnToTask(() => void refreshFace());
    const onFocus = () => void refreshFace();
    window.addEventListener("focus", onFocus);
    return () => {
      window.clearTimeout(timer);
      offDeskChanged();
      offAftercare();
      offReturn();
      window.removeEventListener("focus", onFocus);
    };
  }, [subscribeFrames, refreshFace]);

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
      setReceipt({ text: `QUEUED ${clockTime(new Date().toISOString())}` });
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
  }, [meetings, meetingRows]);

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
      return (
        <EgressChip
          label={`NO SUMMARY ROUTE · ${routeReasonToken(faceRoute)}`}
          title="No model is assigned to meeting summaries."
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
  const headline = meetingsHeadline(meetingRows, meetings.loading);

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
  const removeSelected = async () => {
    if (!selected) return;
    setRemoving(true);
    try {
      await apiFetch(`/api/meetings/${encodeURIComponent(String(selected.id))}`, {
        method: "DELETE",
      });
      setSelected(null);
      setReceipt({ text: `DELETED ${clockTime(new Date().toISOString())}` });
      void meetings.reload();
    } catch (reason) {
      setReceipt({
        text: `REFUSED · ${readableError(reason)}`,
        tone: "danger",
      });
    } finally {
      setRemoving(false);
    }
  };

  const rail = (
    <CatalogRail
      meetingRows={meetingRows}
      meetings={meetings}
      selected={selected}
      setSelected={setSelected}
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

      {/* The stream + detail split */}
      <div className="surface-split-railed">
        <SurfaceSplit
          main={rail}
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
          <span
            className="surface-footer-receipt-line"
            data-tone={receipt?.tone}
            role="status"
          >
            {receipt
              ? receipt.text
              : countToken(meetingRows.length, "RECORD") ?? "RECORDS"}
          </span>
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
              <ConfirmVerb
                label="Delete"
                confirmLabel="Delete?"
                busy={removing}
                onConfirm={() => void removeSelected()}
              />
            </span>
          ) : null
        }
      />}
    </>
  );
}

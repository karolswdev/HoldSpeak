// PHILO-17 (owner 2026-10-10, "A meeting opens in one window") — the saved
// meeting in its own window (`pullout:meeting:<id>`). The whole record moved
// here from the Meetings window's detail pane: MeetingDetail as it was
// (decisions above commitments, Needs you, the summary, Send, Decide, the
// transcript), its one face (Outcomes; betterment capture C5 parked the
// Artifacts wing), and its foot verbs (Open transcript, Send, Add to
// project, MD, SRT, Park).
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { WorkMenu, type WorkMenuEntry } from "../../../desk/components/DeskMenu";
import { SurfaceWell } from "../../../desk/surface/Surface";
import { AddToProject } from "../../../desk/AddToProject";
import { Button } from "../../../components/signal/Signal";
import { useCompactViewport } from "../../../desk/useCompactViewport";
import { apiBlob, apiFetch, readableError } from "../../../lib/api";
import { SurfaceState } from "../../../desk/surface/Surface";
import { SurfaceFooter } from "../../../desk/surface/SurfaceFooter";
import {
  ParkReceipt,
  parkClock,
  parkedOutcome,
  restoredOutcome,
  restoreFailedOutcome,
  notParkedOutcome,
  type ParkOutcome,
} from "../../../desk/surface";
import { parkMeeting, restoreMeeting } from "../../../desk/api";
import { writeFailureReason } from "../../../desk/hooks/useWriteReceipt";
import { EgressChip } from "../../../desk/surface/gadgets";
import { StateChip } from "../../../desk/surface/patterns/StateChip";
import { egressFor } from "../../../desk/surface/egress";
import { readPlannedRoute, routeOff, routeReady } from "../../../meetings/summaryRoute";
import { readMeetingIntel } from "../../../meetings/MeetingSummarySlab";
import { useRuntimeBus } from "../../../runtime/RuntimeBus";
import { SPEECH_SETUP_EVENT } from "../../../desk/firstrun/SpeechSetup";
import { burstTimer } from "../../../desk/burstTimer";
import { onReturnToTask } from "../../../desk/returnToTask";
import { useWindowTitle } from "../../../desk/surface/title";
import { useDesk } from "../../../desk/store";
import { useWindowId } from "../../../desk/components/window/windowIdContext";
import { SEND_OPEN, windowDoc } from "../../../desk/windowSend";
import { MEETING_OPEN_EVENT, peekMeetingRequest, takeMeetingRequest, type MeetingOpenRequest } from "../../../desk/objectWindows";
import { useCoreWings } from "../core-hooks";
import type { MeetingDetailResponse } from "../core-types";
import {
  ACTIVE_RUN_STATES, FINAL_RUN_STATES, adoptDurableRunReceipt, clockTime, download, intelStateOf,
  summaryIsOff, type DetailView,
} from "./helpers";
import { MeetingDetail, MEETING_TRANSCRIPT_OPEN } from "./MeetingDetail";
import { useSummaryRun } from "./useSummaryRun";

/** The meeting window's one wing (DESIGN §4: "One wing: Outcomes").
 *  Betterment capture C5 parked the Artifacts wing; its Results show under
 *  Outcomes ▸ Prepared. */
export const MEETING_WINGS = [
  { id: "outcomes", label: "Outcomes" },
];

/** Phase 16: a foot verb brings a well on the open record into view (and,
 *  for Send, puts the focus on its first control). */
function revealOnRecord(anchorId: string, focus = false): void {
  const el = document.getElementById(anchorId);
  if (!el) return;
  el.scrollIntoView?.({ block: "start", behavior: "smooth" });
  if (focus) el.querySelector<HTMLElement>("button:not(:disabled), input, textarea")?.focus({ preventScroll: true });
}

/** The existing menu species carries the record's secondary actions. */
function RecordMore({ entries }: { entries: WorkMenuEntry[] }) {
  const ref = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  return <>
    <Button ref={ref} dense variant="ghost" aria-label="More actions" aria-haspopup="menu" aria-expanded={open}
      onClick={() => setOpen((value) => !value)}>More</Button>
    {open && ref.current ? <WorkMenu label="More actions" anchor="above"
      x={ref.current.getBoundingClientRect().left} y={ref.current.getBoundingClientRect().top}
      entries={entries} autoFocus onClose={() => setOpen(false)} returnFocus={() => ref.current?.focus()} /> : null}
  </>;
}

export function MeetingRecord({ meetingId, onClose }: { meetingId: string; onClose(): void }) {
  const winId = useWindowId();
  // The place a door asked for (an Outcomes face or transcript row), once.
  // Peeked in render (a render may run again), taken once it is shown.
  const [request] = useState<MeetingOpenRequest | null>(() => peekMeetingRequest(meetingId));
  useEffect(() => { takeMeetingRequest(meetingId); }, [meetingId]);
  // Old deep links may still say `view=review`; Outcomes is now the one
  // review face and receives that request after the migration.
  // An old `view=artifacts` link lands on Outcomes (C5 parked that wing).
  const initialView = "outcomes";
  const wings = useCoreWings(MEETING_WINGS, initialView);
  const [meeting, setMeeting] = useState<Record<string, unknown> | null>(null);
  const [loadError, setLoadError] = useState("");
  // A source span opens on the Outcomes face and expands its transcript.
  const [segment, setSegment] = useState<number | null>(request?.segment ?? null);
  const [parking, setParking] = useState(false);
  const [parkOutcome, setParkOutcome] = useState<ParkOutcome | null>(null);
  // PHILO-17 (Astra r1): the meeting's own records (decisions, proposals)
  // read again on every signal, even when the meeting row did not change.
  const [revision, setRevision] = useState(0);
  const [requestedWell, setRequestedWell] = useState<"send" | "decide" | "project" | null>(null);
  const projects = useDesk((state) => state.projects);

  const load = useCallback(async () => {
    try {
      const fresh = await apiFetch<MeetingDetailResponse>(
        // A parked meeting still opens (the Parked drawer's Open).
        `/api/meetings/${encodeURIComponent(meetingId)}?include_parked=true`,
      );
      // MERGE, never replace (HS-202-02): a field the first read carried
      // stays until a read carries it again. An unchanged read keeps the
      // same object, so the record's own reads (and an open Send well's
      // form) are not reset on every desk change.
      setMeeting((current) => {
        const next = fresh as Record<string, unknown>;
        if (current && Object.keys(next).every((key) => JSON.stringify(current[key]) === JSON.stringify(next[key]))) {
          return current;
        }
        return { ...(current ?? {}), ...next };
      });
      setLoadError("");
    } catch (reason) {
      setLoadError(readableError(reason));
    }
  }, [meetingId]);

  useEffect(() => {
    void load();
    // Opening the meeting reads its READY (the Dock's Meetings count).
    void apiFetch(`/api/meetings/${encodeURIComponent(meetingId)}/ready/read`, { method: "POST" }).catch(() => null);
  }, [load, meetingId]);

  // A door asks an open window for a place: the window moves to it.
  const setView = wings.setView;
  const requestWell = useCallback((well: "send" | "decide" | "project") => {
    setView("outcomes");
    setRequestedWell(well);
    window.requestAnimationFrame(() => revealOnRecord(`meeting-${meetingId}-${well}`, true));
  }, [meetingId, setView]);
  useEffect(() => {
    const onSend = (event: Event) => {
      if (!winId || (event as CustomEvent<{ winId?: string }>).detail?.winId !== winId) return;
      const doc = windowDoc(winId);
      if (doc?.kind !== "meeting" || doc.id !== meetingId) return;
      requestWell("send");
    };
    window.addEventListener(SEND_OPEN, onSend);
    return () => window.removeEventListener(SEND_OPEN, onSend);
  }, [meetingId, requestWell, winId]);
  useEffect(() => {
    const onOpen = (event: Event) => {
      const next = (event as CustomEvent<MeetingOpenRequest>).detail;
      if (!next || next.meetingId !== meetingId) return;
      takeMeetingRequest(meetingId);
      setView("outcomes");
      setSegment(next.segment);
    };
    window.addEventListener(MEETING_OPEN_EVENT, onOpen);
    return () => window.removeEventListener(MEETING_OPEN_EVENT, onOpen);
  }, [meetingId, setView]);

  /* HS-202-02 — the record re-reads itself: `desk_changed`, a deferred
     summary's `aftercare_ready`, the return from a task, and window focus. */
  const { subscribe } = useRuntimeBus();
  useEffect(() => {
    const refresh = () => {
      setRevision((n) => n + 1);
      void load();
    };
    const burst = burstTimer(refresh, 300);
    const offDeskChanged = subscribe("desk_changed", burst.bump);
    const offAftercare = subscribe("aftercare_ready", burst.bump);
    const offReturn = onReturnToTask(refresh);
    window.addEventListener("focus", refresh);
    // PHILO-17 transcribe: speech set up in any window changes this
    // meeting's Transcribe readiness.
    window.addEventListener(SPEECH_SETUP_EVENT, refresh);
    return () => {
      window.removeEventListener(SPEECH_SETUP_EVENT, refresh);
      burst.cancel();
      offDeskChanged();
      offAftercare();
      offReturn();
      window.removeEventListener("focus", refresh);
    };
  }, [subscribe, load]);

  const route = useMemo(() => readPlannedRoute(meeting), [meeting]);
  const summary = useSummaryRun(() => route, load);
  const { receipt, setReceipt, settleRun } = summary;
  // PHILO-17 (Astra r1, from the list): the window adopts the durable run on
  // its first read (a reopen during a run says QUEUED, a run that ended
  // today says RAN), and a QUEUED receipt settles when the meeting's own
  // state goes final, whoever finished it (the poll, a deferred worker).
  const adopted = useRef(false);
  const seenActive = useRef<string | null>(null);
  useEffect(() => {
    if (!meeting || adopted.current) return;
    adopted.current = true;
    const durable = adoptDurableRunReceipt([meeting]);
    if (!durable) return;
    if (durable.active && durable.receipt.run) {
      seenActive.current = `${durable.receipt.run.meetingId}:${durable.receipt.run.jobId}`;
    }
    setReceipt((current) => current ?? durable.receipt);
  }, [meeting, setReceipt]);
  useEffect(() => {
    const run = receipt?.run;
    if (!run || !meeting || run.meetingId !== meetingId) return;
    const state = intelStateOf(meeting.intel_status);
    const key = `${run.meetingId}:${run.jobId}`;
    if (ACTIVE_RUN_STATES.has(state)) {
      seenActive.current = key;
      return;
    }
    if (FINAL_RUN_STATES.has(state) && seenActive.current === key) {
      seenActive.current = null;
      const job = meeting.intel_job as Record<string, unknown> | null | undefined;
      settleRun(run, state, typeof job?.updated_at === "string" ? job.updated_at : undefined);
    }
  }, [meeting, meetingId, receipt, settleRun]);
  // A later receipt (export, queued run) takes the slot from the park outcome.
  useEffect(() => {
    if (receipt) setParkOutcome(null);
  }, [receipt]);

  const title = String(meeting?.title ?? "").trim();
  const compact = useCompactViewport();
  // The record publishes its title again on every face change.
  useWindowTitle(title || null, [title, wings.view]);

  // PHILO-17 (U16, #1083): the window's foot names the summary engine.
  const footerHost =
    route && routeReady(route) ? egressFor(route.legs[0].host).label : null;
  // HS-201-04 (UX-CANON A.9): the foot says where this meeting's summary runs.
  const footerEgress = useMemo(() => {
    if (!route) return null;
    if (!routeReady(route)) {
      return (
        <StateChip
          state="warning"
          label={routeOff(route) ? "Summaries off" : "No engine for summaries"}
        />
      );
    }
    const lead = egressFor(route.legs[0].host);
    return <EgressChip label={lead.label} scope={lead.scope} title="Where a meeting summary runs." />;
  }, [route]);

  const exportMeeting = async (format: string) => {
    try {
      download(
        await apiBlob(`/api/meetings/${encodeURIComponent(meetingId)}/export?format=${format}`),
        `holdspeak-meeting-${meetingId}.${format === "markdown" ? "md" : format}`,
      );
      setReceipt({
        text: `EXPORTED ${format === "markdown" ? "MD" : format.toUpperCase()} ${clockTime(new Date().toISOString())}`,
      });
    } catch (reason) {
      setReceipt({ text: `REFUSED · ${readableError(reason)}`, tone: "danger" });
    }
  };
  // PHILO-13-02 (A1-F): Park, never delete. One press, no confirm; the
  // receipt in the foot carries Restore (the window stays, so the Undo is
  // in view where Park was pressed).
  const showParkOutcome = (outcome: ParkOutcome) => {
    setReceipt(null);
    setParkOutcome(outcome);
  };
  const park = async () => {
    setParking(true);
    try {
      await parkMeeting(meetingId);
      showParkOutcome(parkedOutcome([meetingId], parkClock()));
      void useDesk.getState().refresh().catch(() => undefined);
    } catch (reason) {
      showParkOutcome(notParkedOutcome(writeFailureReason(reason)));
    } finally {
      setParking(false);
    }
  };
  const restore = async (ids: string[]) => {
    try {
      await Promise.all(ids.map((id) => restoreMeeting(id)));
      showParkOutcome(restoredOutcome(ids));
      void useDesk.getState().refresh().catch(() => undefined);
    } catch {
      showParkOutcome(restoreFailedOutcome(ids));
    }
  };

  if (!meeting) {
    return loadError ? (
      <div className="surface-state-error">
        <span>{loadError}</span>
        <Button dense variant="ghost" onClick={() => void load()}>Retry</Button>
      </div>
    ) : (
      <SurfaceState loading />
    );
  }

  const view = wings.view as DetailView;
  const moreEntries: WorkMenuEntry[] = [
    { type: "item", id: "transcript", label: "Open transcript", onSelect: () => {
      wings.setView("outcomes");
      window.dispatchEvent(new CustomEvent(MEETING_TRANSCRIPT_OPEN, { detail: meetingId }));
      window.requestAnimationFrame(() => revealOnRecord(`meeting-${meetingId}-transcript`));
    } },
    { type: "item", id: "decide", label: "Decide", onSelect: () => requestWell("decide") },
    ...(projects.some((project) => !project.is_archived) ? [{ type: "item" as const, id: "project", label: "Add to Project", onSelect: () => requestWell("project") }] : []),
    { type: "item", id: "markdown", label: "Export MD", onSelect: () => void exportMeeting("markdown") },
    { type: "item", id: "srt", label: "Export SRT", onSelect: () => void exportMeeting("srt") },
    { type: "item", id: "park", label: "Park", ghost: parking ? "Busy" : undefined, onSelect: () => void park() },
  ];
  const hasSummary = meeting.has_summary === true || String(readMeetingIntel(meeting)?.summary ?? "").trim() !== "";

  return (
    <>
      {!compact ? (
        <Button
          dense
          variant="ghost"
          className="meeting-record-back"
          data-testid="meeting-record-back"
          onClick={onClose}
        >
          Back
        </Button>
      ) : null}
      <MeetingDetail
        sendRequested={requestedWell === "send"}
        decideRequested={requestedWell === "decide"}
        saidOnFace={footerHost}
        meeting={meeting}
        onTranscribe={async (id: string) => {
          // PHILO-17 transcribe: the hub starts it (202); the record reads again.
          await apiFetch(`/api/meetings/${encodeURIComponent(id)}/transcribe`, { method: "POST" });
          await load();
        }}
        view={view}
        momentSegmentIndex={segment}
        onClose={onClose}
        onDeleted={() => {
          setRevision((n) => n + 1);
          void load();
        }}
        revision={revision}
        onReceipt={setReceipt}
        runRefusal={summary.runRefusal?.meetingId === meetingId ? summary.runRefusal.refusal : null}
        onRunIntelligence={
          // HS-201-04: a FAILED record's Retry is owned by the summary slab;
          // the record offers a run only when the summary is OFF (and on the
          // Outcomes face).
          summaryIsOff(meeting)
            ? (displayed) => void summary.run(meetingId, displayed)
            : undefined
        }
      />
      {requestedWell === "project" ? <div id={`meeting-${meetingId}-project`}>
        <SurfaceWell head="Project"><AddToProject meetingId={meetingId} autoOpen
          onReceipt={(next) => setReceipt(next.tone === "danger" ? { text: next.text, tone: "danger" } : { text: next.text })} /></SurfaceWell>
      </div> : null}
      <>
        <SurfaceFooter
          egress={footerEgress}
          receipt={
            parkOutcome ? (
              <ParkReceipt outcome={parkOutcome} onRestore={(ids) => void restore(ids)} data-testid="meeting-park-receipt" />
            ) : (
              <span className="surface-footer-receipt-line" data-tone={receipt?.tone} role="status">
                {receipt ? <span data-testid="meetings-run-receipt">{receipt.text}</span> : null}
              </span>
            )
          }
          verbs={
            <span className="surface-footer-verbs-group">
              {view === "outcomes" && hasSummary ? (
                <Button dense variant="primary" data-testid="meeting-send" onClick={() => requestWell("send")}>Send</Button>
              ) : null}
              <RecordMore entries={moreEntries} />
            </span>
          }
        />
      </>
    </>
  );
}

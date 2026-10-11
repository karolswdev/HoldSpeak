// PHILO-17 (owner 2026-10-10, "A meeting opens in one window") — the saved
// meeting in its own window (`pullout:meeting:<id>`). The whole record moved
// here from the Meetings window's detail pane: MeetingDetail as it was
// (decisions above commitments, Needs you, the summary, Send, Decide, the
// transcript), its three faces (Outcomes, Review, Artifacts) as the
// window's wings, and its foot verbs (Open transcript, Send, Add to
// project, MD, SRT, Park).
import { useCallback, useEffect, useMemo, useState } from "react";
import { AddToProject } from "../../../desk/AddToProject";
import { Button } from "../../../components/signal/Signal";
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
import { readPlannedRoute, routeOff, routeReady, routeReasonToken } from "../../../meetings/summaryRoute";
import { readMeetingIntel } from "../../../meetings/MeetingSummarySlab";
import { useRuntimeBus } from "../../../runtime/RuntimeBus";
import { SPEECH_SETUP_EVENT } from "../../../desk/firstrun/SpeechSetup";
import { burstTimer } from "../../../desk/burstTimer";
import { onReturnToTask } from "../../../desk/returnToTask";
import { useWindowTitle } from "../../../desk/surface/title";
import { useDesk } from "../../../desk/store";
import { MEETING_OPEN_EVENT, peekMeetingRequest, takeMeetingRequest, type MeetingOpenRequest } from "../../../desk/objectWindows";
import { useCoreWings } from "../core-hooks";
import type { MeetingDetailResponse } from "../core-types";
import { clockTime, download, summaryIsOff, type DetailView } from "./helpers";
import { MeetingDetail } from "./MeetingDetail";
import { useSummaryRun } from "./useSummaryRun";

/** The meeting window's faces (the Meetings window's detail wings). */
export const MEETING_WINGS = [
  { id: "outcomes", label: "Outcomes" },
  { id: "review", label: "Review" },
  { id: "artifacts", label: "Artifacts" },
];

/** Phase 16: a foot verb brings a well on the open record into view (and,
 *  for Send, puts the focus on its first control). */
function revealOnRecord(anchorId: string, focus = false): void {
  const el = document.getElementById(anchorId);
  if (!el) return;
  el.scrollIntoView?.({ block: "start", behavior: "smooth" });
  if (focus) el.querySelector<HTMLElement>("button:not(:disabled), input, textarea")?.focus({ preventScroll: true });
}

export function MeetingRecord({ meetingId, onClose }: { meetingId: string; onClose(): void }) {
  // The place a door asked for (a Review wing, a transcript row), once.
  // Peeked in render (a render may run again), taken once it is shown.
  const [request] = useState<MeetingOpenRequest | null>(() => peekMeetingRequest(meetingId));
  useEffect(() => { takeMeetingRequest(meetingId); }, [meetingId]);
  const wings = useCoreWings(MEETING_WINGS, request?.view ?? "outcomes");
  const [meeting, setMeeting] = useState<Record<string, unknown> | null>(null);
  const [loadError, setLoadError] = useState("");
  // HS-200-12: `Open evidence` on the review wing lands on the outcomes face
  // scrolled to the proposal's segment.
  const [segment, setSegment] = useState<number | null>(request?.segment ?? null);
  const [parking, setParking] = useState(false);
  const [parkOutcome, setParkOutcome] = useState<ParkOutcome | null>(null);

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
  useEffect(() => {
    const onOpen = (event: Event) => {
      const next = (event as CustomEvent<MeetingOpenRequest>).detail;
      if (!next || next.meetingId !== meetingId) return;
      takeMeetingRequest(meetingId);
      setView(next.view);
      setSegment(next.segment);
    };
    window.addEventListener(MEETING_OPEN_EVENT, onOpen);
    return () => window.removeEventListener(MEETING_OPEN_EVENT, onOpen);
  }, [meetingId, setView]);

  /* HS-202-02 — the record re-reads itself: `desk_changed`, a deferred
     summary's `aftercare_ready`, the return from a task, and window focus. */
  const { subscribe } = useRuntimeBus();
  useEffect(() => {
    const refresh = () => void load();
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
  const { receipt, setReceipt } = summary;
  // A later receipt (export, queued run) takes the slot from the park outcome.
  useEffect(() => {
    if (receipt) setParkOutcome(null);
  }, [receipt]);

  const title = String(meeting?.title ?? "").trim();
  // The Review wing publishes its own title and clears it as it leaves: the
  // record publishes again on every face change.
  useWindowTitle(title || null, [title, wings.view]);

  // HS-201-04 (UX-CANON A.9): the foot says where this meeting's summary runs.
  const footerEgress = useMemo(() => {
    if (!route) return null;
    if (!routeReady(route)) {
      return (
        <StateChip
          state="warning"
          label={routeOff(route) ? "SUMMARIES OFF" : `NO SUMMARY ROUTE · ${routeReasonToken(route)}`}
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
  // HS-200-12: the review wing draws its own footer (egress where the
  // extraction happened, the receipt, `Accept reviewed`).
  const reviewOwnsFooter = view === "review";
  const hasSummary = meeting.has_summary === true || String(readMeetingIntel(meeting)?.summary ?? "").trim() !== "";

  return (
    <>
      <MeetingDetail
        meeting={meeting}
        onTranscribe={async (id: string) => {
          // PHILO-17 transcribe: the hub starts it (202); the record reads again.
          await apiFetch(`/api/meetings/${encodeURIComponent(id)}/transcribe`, { method: "POST" });
          await load();
        }}
        view={view}
        momentSegmentIndex={segment}
        onClose={onClose}
        onDeleted={() => void load()}
        onReceipt={setReceipt}
        footerRunReceipt={receipt?.run && receipt.run.meetingId === meetingId ? receipt : null}
        runRefusal={summary.runRefusal?.meetingId === meetingId ? summary.runRefusal.refusal : null}
        onRunIntelligence={
          // HS-201-04: a FAILED record's Retry is owned by the summary slab;
          // the record offers a run only when the summary is OFF (and on the
          // review wing).
          summaryIsOff(meeting) || view === "review"
            ? (displayed) => void summary.run(meetingId, displayed)
            : undefined
        }
        onReview={() => wings.setView("review")}
        onOpenEvidence={(segmentIndex) => {
          setSegment(segmentIndex);
          wings.setView("outcomes");
        }}
      />
      {reviewOwnsFooter ? null : (
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
              {/* Phase 16 (the canvas window "Cutover sync"): the foot's
                  Open transcript and Send (the meeting's one filled
                  primary) bring their wells into view on the record. */}
              {view === "outcomes" ? (
                <>
                  <Button dense variant="ghost" data-testid="meeting-open-transcript"
                    onClick={() => revealOnRecord(`meeting-${meetingId}-transcript`)}>
                    Open transcript
                  </Button>
                  {hasSummary ? (
                    <Button dense variant="primary" data-testid="meeting-send"
                      onClick={() => revealOnRecord(`meeting-${meetingId}-send`, true)}>
                      Send
                    </Button>
                  ) : null}
                </>
              ) : null}
              {/* PHILO-15 16 (B37): the meeting joins a Project. */}
              <AddToProject meetingId={meetingId} onReceipt={(next) => setReceipt(next.tone === "danger" ? { text: next.text, tone: "danger" } : { text: next.text })} />
              <Button dense variant="ghost" onClick={() => void exportMeeting("markdown")}>
                MD
              </Button>
              <Button dense variant="ghost" onClick={() => void exportMeeting("srt")}>
                SRT
              </Button>
              <Button dense variant="ghost" disabled={parking} onClick={() => void park()}>
                Park
              </Button>
            </span>
          }
        />
      )}
    </>
  );
}

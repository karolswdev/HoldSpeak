// The language (2026-11-08): the picked meeting in the Meetings app's pane.
// The MAST (the meeting sprite, the title, edited in place, and one mono
// facts line: when, who, how long; the verbs Send follow-up, Export, More),
// the SPINE (captured, transcribed, intelligence run, decisions filed), the
// PLATE (the one thing that matters now with its one verb: Resolve,
// Transcribe, Run intelligence, Retry, Confirm, Send the follow-up), then
// the LEDGER (MeetingDetail: the summary, the decisions and actions by
// weight, the prepared Results, the transcript) and one status bar.
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { WorkMenu, type WorkMenuEntry } from "../../../desk/components/DeskMenu";
import { SurfaceWell } from "../../../desk/surface/Surface";
import { AddToProject } from "../../../desk/AddToProject";
import { Button } from "../../../components/signal/Signal";
import { useCompactViewport } from "../../../desk/useCompactViewport";
import { apiBlob, apiFetch, readableError } from "../../../lib/api";
import { SurfaceState } from "../../../desk/surface/Surface";
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
import { readPlannedRoute, routeOff, routeReady } from "../../../meetings/summaryRoute";
import { readMeetingIntel } from "../../../meetings/MeetingSummarySlab";
import { useRuntimeBus } from "../../../runtime/RuntimeBus";
import { SPEECH_SETUP_EVENT } from "../../../desk/firstrun/SpeechSetup";
import { burstTimer } from "../../../desk/burstTimer";
import { onReturnToTask } from "../../../desk/returnToTask";
import { useWindowTitle } from "../../../desk/surface/title";
import { StatusBar, ToolGlyph, type StatusBarItem } from "../../../desk/surface/kit";
import { Mast } from "../../../desk/surface/patterns/Mast";
import { Spine } from "../../../desk/surface/patterns/Spine";
import { EditInPlace } from "../../../desk/surface/Surface";
import { renameMeeting } from "../../../desk/api";
import { useWindowInterior } from "../../../desk/surface/interior";
import { MeetingRunSlotContext } from "../../../meetings/runSlot";
import { mastFacts, meetingPlate, meetingSpine, meetingSummaryState, type PlateLead } from "./plate";
import "./meeting-record.css";
import { useDesk } from "../../../desk/store";
import { openSurfaceOr } from "../../../desk/shell";
import { useWindowId } from "../../../desk/components/window/windowIdContext";
import { ShowMe, useShowMe } from "../../../desk/walk/ShowMe";
import { SEND_OPEN, windowDoc } from "../../../desk/windowSend";
import { MEETING_OPEN_EVENT, peekMeetingRequest, takeMeetingRequest, type MeetingOpenRequest } from "../../../desk/objectWindows";
import { MEETING_CHANGE_KINDS } from "../../../desk/useDeskChangedRefresh";
import { frameNames } from "../../../desk/components/window/dockState";
import type { MeetingDetailResponse } from "../core-types";
import {
  ACTIVE_RUN_STATES, FINAL_RUN_STATES, adoptDurableRunReceipt, clockTime, download, intelStateOf,
  stateToken, summaryIsOff,
} from "./helpers";
import { MeetingDetail, MEETING_TRANSCRIPT_OPEN } from "./MeetingDetail";
import { useSummaryRun } from "./useSummaryRun";
import { Token } from "../../../desk/surface/Token";

/** Phase 16: a foot verb brings a well on the open record into view (and,
 *  for Send, puts the focus on its first control). */
function revealOnRecord(anchorId: string, focus = false): void {
  const el = document.getElementById(anchorId);
  if (!el) return;
  el.scrollIntoView?.({ block: "start", behavior: "smooth" });
  if (focus) el.querySelector<HTMLElement>("button:not(:disabled), input, textarea")?.focus({ preventScroll: true });
}

/** The existing menu species carries the record's secondary actions; in
 *  the toolbar it opens below its Button. */
function RecordMenu({ label, ariaLabel, entries, glyph }: {
  label: string;
  ariaLabel: string;
  entries: WorkMenuEntry[];
  glyph?: "import";
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  return <>
    <Button ref={ref} dense variant="secondary" aria-label={ariaLabel} aria-haspopup="menu" aria-expanded={open}
      onClick={() => setOpen((value) => !value)}>
      {glyph ? <ToolGlyph kind={glyph} /> : null}
      {label}
    </Button>
    {open && ref.current ? <WorkMenu label={ariaLabel} anchor="below"
      x={ref.current.getBoundingClientRect().left} y={ref.current.getBoundingClientRect().bottom}
      entries={entries} autoFocus onClose={() => setOpen(false)} returnFocus={() => ref.current?.focus()} /> : null}
  </>;
}

export function MeetingRecord({ meetingId, onClose }: { meetingId: string; onClose(): void }) {
  const winId = useWindowId();
  // The app's own walk: a Button at desk width, an entry of More on the phone.
  const showMe = useShowMe("review-meetings");
  // The place a door asked for (an Outcomes face or transcript row), once.
  // Peeked in render (a render may run again), taken once it is shown.
  const [request] = useState<MeetingOpenRequest | null>(() => peekMeetingRequest(meetingId));
  useEffect(() => { takeMeetingRequest(meetingId); }, [meetingId]);
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
  const sendButtonRef = useRef<HTMLButtonElement>(null);
  const wasSendOpen = useRef(false);
  const projects = useDesk((state) => state.projects);
  // Window grammar: the record runs edge to edge (toolbar, head, reader,
  // status bar); its run verbs are portaled into the toolbar's run slot.
  useWindowInterior("editor");
  const [runSlot, setRunSlot] = useState<HTMLSpanElement | null>(null);
  const [reviewCount, setReviewCount] = useState(0);
  const [lead, setLead] = useState<PlateLead | null>(null);
  const [conflicts, setConflicts] = useState(0);
  const [renameError, setRenameError] = useState("");

  useEffect(() => {
    const returning = wasSendOpen.current && requestedWell !== "send";
    wasSendOpen.current = requestedWell === "send";
    if (!returning) return;
    const frame = window.requestAnimationFrame(() => sendButtonRef.current?.focus());
    return () => window.cancelAnimationFrame(frame);
  }, [requestedWell]);

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
  const requestWell = useCallback((well: "send" | "decide" | "project") => {
    setRequestedWell(well);
    window.requestAnimationFrame(() => revealOnRecord(`meeting-${meetingId}-${well}`, true));
  }, [meetingId]);
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
      setSegment(next.segment);
    };
    window.addEventListener(MEETING_OPEN_EVENT, onOpen);
    return () => window.removeEventListener(MEETING_OPEN_EVENT, onOpen);
  }, [meetingId]);

  /* HS-202-02 — the record re-reads itself: `desk_changed`, a deferred
     summary's `aftercare_ready`, the return from a task, and window focus. */
  const { subscribe } = useRuntimeBus();
  useEffect(() => {
    const refresh = () => {
      setRevision((n) => n + 1);
      void load();
    };
    const burst = burstTimer(refresh, 300);
    const offDeskChanged = subscribe("desk_changed", (frame) => {
      if (frameNames(frame?.data, MEETING_CHANGE_KINDS)) burst.bump();
    });
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
  useWindowTitle(title || null, [title]);

  const routeWord = route && !routeReady(route)
    ? (routeOff(route) ? "Summaries off" : "No engine for summaries")
    : null;

  const exportMeeting = async (format: string) => {
    try {
      download(
        await apiBlob(`/api/meetings/${encodeURIComponent(meetingId)}/export?format=${format}`),
        `holdspeak-meeting-${meetingId}.${format === "markdown" ? "md" : format}`,
      );
      setReceipt({
        text: `Exported as ${format === "markdown" ? "Markdown" : format.toUpperCase()} at ${clockTime(new Date().toISOString())}`,
      });
    } catch (reason) {
      setReceipt({ text: `Could not export the meeting as ${format === "markdown" ? "Markdown" : format.toUpperCase()} · Nothing changed · Try again`, tone: "danger", title: readableError(reason) });
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
      showParkOutcome(notParkedOutcome("The hub did not accept it", writeFailureReason(reason)));
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
      <SurfaceState loading onRetry={() => void load()} />
    );
  }

  const moreEntries: WorkMenuEntry[] = [
    { type: "item", id: "transcript", label: "Open transcript", onSelect: () => {
      window.dispatchEvent(new CustomEvent(MEETING_TRANSCRIPT_OPEN, { detail: meetingId }));
      window.requestAnimationFrame(() => revealOnRecord(`meeting-${meetingId}-transcript`));
    } },
    { type: "item", id: "decide", label: "Decide", onSelect: () => requestWell("decide") },
    ...(projects.some((project) => !project.is_archived) ? [{ type: "item" as const, id: "project", label: "Add to Project", onSelect: () => requestWell("project") }] : []),
    { type: "item", id: "park", label: "Park", ghost: parking ? "Busy" : undefined, onSelect: () => void park() },
    ...(showMe.entry ? [showMe.entry] : []),
  ];
  const exportEntries: WorkMenuEntry[] = [
    { type: "item", id: "markdown", label: "Export MD", onSelect: () => void exportMeeting("markdown") },
    { type: "item", id: "srt", label: "Export SRT", onSelect: () => void exportMeeting("srt") },
  ];
  const hasSummary = meeting.has_summary === true || String(readMeetingIntel(meeting)?.summary ?? "").trim() !== "";

  const engineMissing = Boolean(routeWord) && !routeOff(route);
  const summaryState = meetingSummaryState(meeting, routeOff(route));
  const running = ["RUNNING", "QUEUED"].includes(stateToken(meeting).label);

  const facts = mastFacts(meeting);

  // The spine and the plate: where the meeting stands, the one thing now.
  const spine = meetingSpine(meeting, reviewCount);
  const plate = meetingPlate(meeting, { conflicts, lead, pending: reviewCount });
  const summariesOff = plate.kind === "run" && routeOff(route);
  const chooseEngine = (
    <Button dense variant={plate.kind === "run" ? "brass" : "secondary"} data-testid="meeting-choose-engine"
      onClick={() => openSurfaceOr("open-concierge", "/models", "meetings")}>
      <ToolGlyph kind="engine" />
      Choose engine
    </Button>
  );
  let plateVerb: ReactNode = null;
  if (plate.kind === "conflict") {
    plateVerb = <Button dense variant="brass" data-testid="meeting-plate-resolve"
      onClick={() => revealOnRecord(`meeting-${meetingId}-conflict`, true)}>Resolve</Button>;
  } else if (plate.kind === "proposal" && lead) {
    plateVerb = <Button dense variant="brass" loading={lead.busy} data-testid="meeting-plate-lead"
      aria-label={`${lead.verb}: ${lead.text}`} onClick={lead.act}>{lead.verb}</Button>;
  } else if (plate.kind === "review") {
    plateVerb = <Button dense variant="brass" data-testid="meeting-plate-review"
      onClick={() => document.querySelector<HTMLElement>(".meeting-record .meetings-detail-needs, .meeting-record [data-testid=meeting-decisions], .meeting-record [data-testid=meeting-commitments]")
        ?.scrollIntoView?.({ block: "start", behavior: "smooth" })}>Review</Button>;
  } else if (plate.kind === "send") {
    plateVerb = <Button ref={sendButtonRef} dense variant="brass" data-testid="meeting-send" onClick={() => requestWell("send")}>
      <ToolGlyph kind="send" />
      Send follow-up…
    </Button>;
  } else if (plate.kind === "run" && engineMissing) {
    plateVerb = chooseEngine;
  } else if (summariesOff) {
    plateVerb = <Button dense variant="secondary" data-testid="meeting-plate-settings"
      onClick={() => openSurfaceOr("configure-settings", "/settings", "meetings")}>Settings</Button>;
  }

  const rename = async (next: string) => {
    setRenameError("");
    try {
      const renamed = await renameMeeting(meetingId, next);
      setMeeting((current) => (current ? { ...current, title: renamed ?? next } : current));
      void useDesk.getState().refresh().catch(() => undefined);
    } catch (reason) {
      setRenameError(`Could not rename the meeting · ${readableError(reason)} · Nothing changed`);
    }
  };

  const statusItems: StatusBarItem[] = [
    { key: "state", lamp: summaryState.lamp, text: summaryState.text, testId: "meeting-summary-state" },
    reviewCount > 0 ? { key: "review", lamp: "ask" as const, text: `${reviewCount} to review`, testId: "meeting-review-count" } : null,
    routeWord && !(routeOff(route) && summaryState.text === "Summaries off")
      ? { key: "route", lamp: "warn" as const, text: routeWord, testId: "meeting-route-state" }
      : null,
    renameError ? { key: "rename", lamp: "fail" as const, text: renameError, testId: "meeting-rename-failed" } : null,
    parkOutcome
      ? { key: "receipt", text: <ParkReceipt outcome={parkOutcome} onRestore={(ids) => void restore(ids)} data-testid="meeting-park-receipt" /> }
      : receipt
        ? { key: "receipt", text: <Token className="surface-footer-receipt-line" data-words="" data-tone={receipt.tone} data-testid="meetings-run-receipt" title={receipt.title || undefined}>{receipt.text}</Token> }
        : null,
  ].filter(Boolean) as StatusBarItem[];

  return (
    <div className="meeting-record" data-testid="meeting-record" data-running={running || undefined}>
      <div className="meeting-record-scroll">
        <div className="mt-head">
          <Mast kind="meeting" id={meetingId} data-testid="meeting-mast" className="mt-mast"
            title={<EditInPlace label="Meeting title" value={title} placeholder="Meeting" onCommit={rename} />}
            facts={facts || undefined}>
            {/* The phone's frame carries its own Back. */}
            {compact ? null : (
              <Button dense variant="secondary" className="meeting-record-back" data-testid="meeting-record-back" onClick={onClose}>
                <span className="meeting-record-back-mark" aria-hidden="true">‹</span>
                Back
              </Button>
            )}
            {hasSummary && plate.kind !== "send" ? (
              <Button ref={sendButtonRef} dense variant="secondary" data-testid="meeting-send" onClick={() => requestWell("send")}>
                <ToolGlyph kind="send" />
                Send follow-up…
              </Button>
            ) : null}
            <RecordMenu label="Export" ariaLabel="Export" glyph="import" entries={exportEntries} />
            <RecordMenu label="More" ariaLabel="More actions" entries={moreEntries} />
            <Button dense variant="ghost" data-testid="meeting-settings" aria-label="Settings"
              title="Settings ▸ Meetings" onClick={() => openSurfaceOr("configure-settings", "/settings", "meetings")}>
              <svg className="kit-toolglyph" width={16} height={16} viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <circle cx="8" cy="8" r="2.25" stroke="currentColor" strokeWidth={1.5} />
                <path d="M8 1.75v1.75M8 12.5v1.75M1.75 8h1.75M12.5 8h1.75M3.6 3.6l1.25 1.25M11.15 11.15l1.25 1.25M3.6 12.4l1.25-1.25M11.15 4.85l1.25-1.25" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" />
              </svg>
            </Button>
            <ShowMe app="review-meetings" inMore />
          </Mast>
          <Spine segments={spine.segments} label={spine.label} data-testid="meeting-spine" className="mt-spine" />
        </div>
        {/* The plate: the one thing that matters now. The wells' run verbs
            (Transcribe, Run summary, Retry, Skip) land in its slot. */}
        <section className="mt-plate" data-kind={plate.kind} data-tone={plate.tone} aria-label={plate.title} data-testid="meeting-plate">
          <header className="mt-plate-head">
            <h3 className="mt-plate-title">{plate.title}</h3>
            {plate.facts ? <span className="mt-plate-facts">{plate.facts}</span> : null}
          </header>
          <div className="mt-plate-verbs">
            <span className="meeting-run-slot" ref={setRunSlot} />
            {plateVerb}
          </div>
        </section>
        <MeetingRunSlotContext.Provider value={runSlot}>
          <MeetingDetail
            onDecide={() => requestWell("decide")}
            sendRequested={requestedWell === "send"}
            decideRequested={requestedWell === "decide"}
            meeting={meeting}
            onTranscribe={async (id: string) => {
              // PHILO-17 transcribe: the hub starts it (202); the record reads again.
              await apiFetch(`/api/meetings/${encodeURIComponent(id)}/transcribe`, { method: "POST" });
              await load();
            }}
            view="outcomes"
            momentSegmentIndex={segment}
            onClose={onClose}
            onDeleted={() => {
              setRevision((n) => n + 1);
              void load();
            }}
            onSendBack={() => setRequestedWell(null)}
            revision={revision}
            onReceipt={setReceipt}
            onReviewCount={setReviewCount}
            onLead={setLead}
            onConflicts={setConflicts}
            runRefusal={summary.runRefusal?.meetingId === meetingId ? summary.runRefusal.refusal : null}
            onRunIntelligence={
              // HS-201-04: a FAILED record's Retry is owned by the summary slab;
              // the record offers a run only when the summary is OFF.
              summaryIsOff(meeting)
                ? (displayed) => void summary.run(meetingId, displayed)
                : undefined
            }
          />
        </MeetingRunSlotContext.Provider>
        {requestedWell === "project" ? <div id={`meeting-${meetingId}-project`} className="meeting-record-project">
          <SurfaceWell head="Project"><AddToProject meetingId={meetingId} autoOpen
            onReceipt={(next) => setReceipt(next.tone === "danger" ? { text: next.text, tone: "danger", title: next.title } : { text: next.text })} /></SurfaceWell>
        </div> : null}
      </div>
      {/* One status bar: the summary's state with its lamp, what is left to
          review, the receipt, and Choose engine when no engine runs summaries
          (in the plate when running a summary is the thing now). */}
      {requestedWell !== "send" ? (
        <StatusBar
          data-testid="meeting-status"
          items={statusItems}
          verbs={engineMissing && plate.kind !== "run" ? chooseEngine : null}
        />
      ) : null}
    </div>
  );
}

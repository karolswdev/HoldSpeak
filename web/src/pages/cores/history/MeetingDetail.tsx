// HS-170-04 — the meeting detail pane (the board's right side).
// Display title + tokens, NEEDS YOU section, TRANSCRIPT well, settled list.
import { NO_TRANSCRIPT_SPEECH, speechWasMissing } from "../../../desk/firstrun/speechTruth";
import { useCallback, useEffect, useLayoutEffect, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceState } from "../../../desk/surface";
import { MeetingConflictRecovery } from "../../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../../meetings/MeetingIntelRecovery";
import {
  MeetingSummarySlab,
  readMeetingIntel,
} from "../../../meetings/MeetingSummarySlab";
import {
  executedReceipt,
  readLastRefusal,
  readPlannedRoute,
  readRunReceipt,
  type PlannedRoute,
  type SummaryRefusal,
} from "../../../meetings/summaryRoute";
import { apiFetch } from "../../../lib/api";
import type { DetailView, Receipt } from "./helpers";
import {
  MEETING_READS_CAP_MS,
  useMeetingData,
  type FollowThroughProposal,
  type MeetingData,
  type MeetingDecision,
} from "./useMeetingData";
import { MeetingHeader } from "./MeetingHeader";
import { CaptureSlab } from "./CaptureSlab";
import { ArtifactsLibrary } from "./ArtifactsLibrary";
import { MeetingSendWellLazy as MeetingSendWell } from "../../../meetings/MeetingSendWellLazy";
import { SendWellReadContext } from "../../../desk/surface/send/SendWell";
import { MeetingDecideWell } from "../../../meetings/MeetingDecideWell";
import { NeedsYouTable, showsRunSummary } from "./NeedsYouTable";
import { TranscriptWell } from "./TranscriptWell";
import { AudioOnlyVerb } from "./TranscribeVerb";
import { CycleGadget, StringGadget } from "../../../desk/surface/gadgets";


/** PHILO-17: the meeting window's foot asks its record to open the
 *  transcript fold (`detail`: the meeting id). */
export const MEETING_TRANSCRIPT_OPEN = "holdspeak:meeting-transcript-open";

/** One row of the meeting's outcomes ledgers. */
type OutcomeRow = {
  key: string;
  plate: "DEC" | "ACT";
  text: string;
  meta: string;
  tone?: "ask" | "ok";
  actionItemId?: string;
  proposalId?: string;
  actionStatus?: string | null;
  owner?: string;
  due?: string;
  gap?: boolean;
  deferredUntil?: string | null;
  verbs?: ReactNode;
  children?: ReactNode;
};

function deferredToken(value: unknown): string {
  const stamp = String(value ?? "").trim();
  if (!stamp) return "";
  const date = new Date(stamp);
  if (Number.isNaN(date.getTime())) return `NOT NOW · UNTIL ${stamp}`;
  return `NOT NOW · UNTIL ${date.toLocaleDateString(undefined, { weekday: "short" }).toUpperCase()}`;
}

/** Phase 16 (the interior kit; the canvas window "Cutover sync"): the
 *  meeting's Decisions and Commitments, each a Section over a Ledger of
 *  kind-plated rows. A proposed decision carries Confirm and Dismiss; a
 *  confirmed one names its owner.
 *
 *  Commitments are OBLIGATIONS, one row each (Astra r1 M1): an action
 *  proposal names its action item (`action_item_id`, the producer's link in
 *  proposal_bridge_service.py), so the item and its proposal are ONE row
 *  while the proposal waits. A dismissed proposal or item is
 *  never drawn. The items are the aftercare's rows, else the meeting's own
 *  (`intel.action_items`). A Section with no rows is not drawn (A.8). */
export function meetingOutcomes(
  data: Pick<MeetingData, "ftProposals" | "openActions" | "settledActions"> &
    { completedActionIds?: ReadonlySet<string> }
    & { meetingDecisions?: readonly MeetingDecision[] },
  intelActions: readonly Record<string, unknown>[] = [],
): {
  decisions: OutcomeRow[];
  commitments: OutcomeRow[];
} {
  const owner = (value: unknown) => String(value ?? "").trim();
  const when = (value: unknown) => {
    const text = String(value ?? "").trim();
    return text ? `by ${text}` : "no date";
  };
  const live = data.ftProposals.filter((p) => p.state !== "dismissed");
  // PHILO-17 ("what did we decide yesterday?"): the decisions the meeting
  // recorded are on its record too (the ledger: never a confirmed action).
  // A proposal and a ledger row are the same decision only by identity: the
  // record the proposal wrote, or its artifact with the same words. The pair
  // is one row, and it says the RECORD's state (Astra r2: a record replaced
  // or disputed after Confirm is not DECIDED). A rejected one is not drawn.
  const said = (value: string) => value.trim().toLowerCase().replace(/\s+/g, " ");
  const same = (p: FollowThroughProposal, d: MeetingDecision) =>
    (Boolean(p.decision_record_id) && p.decision_record_id === d.record_id)
    || (Boolean(p.source_artifact_id) && p.source_artifact_id === d.source_artifact_id
      && said(p.text) === said(d.text));
  const recorded = data.meetingDecisions ?? [];
  const stateOf = (d: MeetingDecision | undefined) => {
    const lifecycle = String(d?.lifecycle ?? "").toLowerCase();
    return lifecycle === "superseded" ? "REPLACED" : lifecycle === "disputed" ? "DISPUTED" : "";
  };
  const decisions: OutcomeRow[] = [];
  for (const p of live) {
    if (p.kind !== "decision") continue;
    if (p.state === "proposed") {
      decisions.push({ key: `ft-${p.id}`, plate: "DEC", text: p.text, meta: "", tone: "ask" });
      continue;
    }
    const paired = recorded.find((d) => same(p, d));
    if (String(paired?.lifecycle ?? "").toLowerCase() === "rejected") continue;
    decisions.push({
      key: `ft-${p.id}`, plate: "DEC", text: p.text,
      meta: stateOf(paired) || owner(p.owner) || owner(p.owner_hint) || owner(p.speaker_label) || "DECIDED",
    });
  }
  const decisionProposals = live.filter((p) => p.kind === "decision");
  for (const d of recorded) {
    const lifecycle = String(d.lifecycle ?? "").toLowerCase();
    if (lifecycle === "rejected" || !String(d.text ?? "").trim() || decisionProposals.some((p) => same(p, d))) continue;
    decisions.push({ key: `dec-${d.id}`, plate: "DEC", text: d.text, meta: stateOf(d) || "DECIDED" });
  }

  const actionProposals = data.ftProposals.filter((p) => p.kind === "action");
  const toConfirm = (p: FollowThroughProposal): OutcomeRow => ({
    key: `ft-${p.id}`, plate: "ACT", text: p.text,
    meta: deferredToken(p.deferred_until) || `${owner(p.owner ?? p.owner_hint) || "no owner"} · ${when(p.due ?? p.due_hint)}`,
    tone: "ask", proposalId: p.id,
    owner: owner(p.owner ?? p.owner_hint), due: String(p.due ?? p.due_hint ?? "").trim(),
    gap: !owner(p.owner ?? p.owner_hint) || !String(p.due ?? p.due_hint ?? "").trim(),
    deferredUntil: p.deferred_until,
  });
  const commitments: OutcomeRow[] = [];
  const itemIds = new Set<string>();
  // Outcomes is a single projection.  Every linked action carries both the
  // proposal decision and the action completion fact from the server.
  for (const proposal of actionProposals) {
    if (proposal.state === "dismissed") continue;
    const id = String(proposal.action_item_id ?? "");
    if (id) itemIds.add(id);
    if (proposal.state === "proposed") {
      commitments.push(toConfirm(proposal));
      continue;
    }
    const text = proposal.text || "Action item";
    const who = owner(proposal.owner) || owner(proposal.owner_hint);
    const due = proposal.due ?? proposal.due_hint;
    const linkedStatus = String(proposal.action_status ?? proposal.action_item_status ?? "open").toLowerCase();
    const done = linkedStatus === "done" || linkedStatus === "dismissed";
    commitments.push({
      key: `item-${id || proposal.id}`, plate: "ACT", text,
      meta: done ? (who ? `${who} · Done` : "Done") : `${who || "no owner"} · ${when(due)}`,
      tone: done ? "ok" : undefined,
      actionItemId: id || undefined,
      proposalId: proposal.id,
      actionStatus: linkedStatus || null,
    });
  }
  const items = data.openActions.length || data.settledActions.length
    ? [...data.openActions, ...data.settledActions]
    : [...intelActions];
  for (const [index, row] of items.entries()) {
    const id = String(row.id ?? "");
    if (id && itemIds.has(id)) continue;
    const status = data.completedActionIds?.has(id)
      ? "done"
      : String(row.status ?? "").toLowerCase();
    if (status === "dismissed") continue;
    const text = String(row.task ?? row.text ?? row.title ?? "Action item");
    const who = owner(row.owner);
    const due = row.due;
    const done = status === "done";
    commitments.push({
      key: `item-${id || index}`, plate: "ACT", text,
      meta: done ? (who ? `${who} · Done` : "Done") : `${who || "no owner"} · ${when(due)}`,
      tone: done ? "ok" : undefined,
      actionItemId: id || undefined,
      actionStatus: status || null,
    });
  }
  return { decisions, commitments };
}

function OutcomeLedger({ label, rows, testId, controls }: { label: string; rows: OutcomeRow[]; testId: string; controls?: ReactNode }) {
  if (!rows.length) return null;
  return (
    <SurfaceSection label={label} count={rows.length || null} data-testid={testId}>
      <SurfaceLedger label={label} cols="kit" controls={controls}>
        <ul className="surface-ledger-rows">
          {rows.map((row) => (
            <SurfaceLedgerRow
              key={row.key}
              data-testid={`${testId}-row`}
              kind={row.plate}
              kindTitle={row.plate === "DEC" ? "Decision" : "Action"}
              primary={row.text}
              meta={row.meta}
              metaTone={row.tone}
              trailing={row.verbs}
              wrap
              expands={false}
            >{row.children}</SurfaceLedgerRow>
          ))}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

export function MeetingOutcomes({ data, meeting }: { data: MeetingData; meeting: Record<string, unknown> }) {
  const intel = ((data.detail ?? meeting)?.intel ?? null) as { action_items?: unknown } | null;
  const intelActions = Array.isArray(intel?.action_items)
    ? (intel!.action_items as unknown[]).filter((a): a is Record<string, unknown> => Boolean(a) && typeof a === "object")
    : [];
  const { decisions, commitments } = meetingOutcomes(data, intelActions);
  // The proposals' verbs: Confirm (the plate) and Dismiss. Never the filled
  // primary: the meeting's one primary is Send (the foot).
  const [people, setPeople] = useState<Array<{ display_name?: string }>>([]);
  const [drafts, setDrafts] = useState<Record<string, { owner: string; due: string }>>({});
  const [more, setMore] = useState<Record<string, boolean>>({});
  useEffect(() => {
    let live = true;
    void apiFetch<{ relationships?: Array<{ display_name?: string }> }>("/api/people/relationships")
      .then((body) => { if (live) setPeople(body.relationships ?? []); })
      .catch(() => undefined);
    return () => { live = false; };
  }, []);
  const ownerOptions = [
    { value: "", label: "Who?" },
    { value: "Me", label: "Me" },
    ...people
      .map((person) => String(person.display_name ?? "").trim())
      .filter(Boolean)
      .map((name) => ({ value: name, label: name })),
  ];
  const verbsFor = (row: OutcomeRow) => {
    const id = row.key.startsWith("ft-") ? row.key.slice(3) : "";
    const pending = id && data.ftProposals.some((p) => p.id === id && p.state === "proposed");
    if (!pending && row.actionItemId) {
      const actionId = row.actionItemId;
      if (row.actionStatus === "done") {
        return (
          <Button dense variant="secondary" loading={data.busy} data-testid="action-reopen-btn"
            aria-label={`Reopen: ${row.text}`} onClick={() => void data.completeAction?.(actionId, "reopen")}>
            Reopen
          </Button>
        );
      }
      if (row.actionStatus !== "dismissed") {
        return (
          <Button dense variant="secondary" loading={data.busy} data-testid="action-done-btn"
            aria-label={`Done: ${row.text}`} onClick={() => void data.completeAction?.(actionId)}>
            Done
          </Button>
        );
      }
    }
    if (!pending) return undefined;
    const draft = drafts[id] ?? { owner: row.owner ?? "", due: row.due ?? "" };
    const setDraft = (field: "owner" | "due", value: string) => {
      setDrafts((current) => ({ ...current, [id]: { ...draft, [field]: value } }));
    };
    return (
      <>
        <Button dense variant="secondary" loading={data.busy} data-testid="proposal-confirm-btn"
          aria-label={`Confirm: ${row.text}`} onClick={() => void data.confirmProposal(id, {
            owner: draft.owner || undefined,
            due: draft.due || undefined,
          })}>
          Confirm
        </Button>
        <Button dense variant="ghost" loading={data.busy} data-testid="proposal-more-btn"
          aria-expanded={more[id] || undefined} onClick={() => setMore((current) => ({ ...current, [id]: !current[id] }))}>
          More
        </Button>
        {more[id] ? (
          <>
            <Button dense variant="ghost" loading={data.busy} data-testid="proposal-defer-btn"
              aria-label={`Not now: ${row.text}`} onClick={() => void data.deferProposal(id)}>
              Not now
            </Button>
            <Button dense variant="ghost" loading={data.busy} data-testid="proposal-dismiss-btn"
              aria-label={`Dismiss: ${row.text}`} onClick={() => void data.dismissProposal(id)}>
              Dismiss
            </Button>
          </>
        ) : null}
      </>
    );
  };
  const gapFor = (row: OutcomeRow) => {
    if (!row.gap || !row.proposalId) return undefined;
    const id = row.proposalId;
    const draft = drafts[id] ?? { owner: row.owner ?? "", due: row.due ?? "" };
    const setDraft = (field: "owner" | "due", value: string) => {
      setDrafts((current) => ({ ...current, [id]: { ...draft, [field]: value } }));
    };
    return (
      <div className="meeting-outcome-gap" data-testid="outcome-gap">
        {!draft.owner ? <CycleGadget label="Who?" value={draft.owner} options={ownerOptions} onChange={(value) => setDraft("owner", value)} disabled={data.busy} /> : null}
        {!draft.due ? <StringGadget label="When?" type="date" value={draft.due} onChange={(value) => setDraft("due", value)} disabled={data.busy} /> : null}
      </div>
    );
  };
  const withVerbs = (rows: OutcomeRow[]) => rows.map((row) => ({
    ...row,
    verbs: verbsFor(row),
    children: gapFor(row),
  }));
  const eligible = commitments.filter((row) => {
    const id = row.proposalId;
    if (!id || row.gap) return false;
    const proposal = data.ftProposals.find((item) => item.id === id);
    if (!proposal || proposal.state !== "proposed") return false;
    if (!(proposal.support === "supported" || proposal.support === "source_linked")) return false;
    if (Array.isArray(proposal.unknowns) && proposal.unknowns.length > 0) return false;
    if (data.reviewRevision && proposal.extraction_revision
      && proposal.extraction_revision !== data.reviewRevision) return false;
    return true;
  });
  const controls = eligible.length ? (
    <Button dense variant="primary" loading={data.busy} data-testid="proposal-confirm-all-btn" onClick={() => void data.confirmAll()}>
      Confirm all {eligible.length}
    </Button>
  ) : null;
  return (
    <>
      <OutcomeLedger label="Decided" rows={withVerbs(decisions)} testId="meeting-decisions" />
      <OutcomeLedger label="Who owes what" rows={withVerbs(commitments)} testId="meeting-commitments" controls={controls} />
    </>
  );
}

export function MeetingDetail({
  meeting,
  view,
  momentSegmentIndex,
  onClose,
  onDeleted,
  onReceipt,
  onRunIntelligence,
  runRefusal,
  onTranscribe,
  saidOnFace,
  revision = 0,
}: {
  meeting: Record<string, unknown> | null;
  /** PHILO-17 (U16): the engine host the window's foot already names. */
  saidOnFace?: string | null;
  /** PHILO-17 transcribe: start Transcribe on this audio-only meeting. */
  onTranscribe?: (id: string) => Promise<unknown>;
  /** "outcomes" (the face) or "artifacts". */
  view: DetailView;
  /** HS-109-02/05: a resolved decision moment seeks this transcript row. */
  momentSegmentIndex?: number | null;
  onClose(): void;
  onDeleted(): void;
  /** HS-111-03 — outcomes land on the footer receipt bar. */
  onReceipt(receipt: Receipt): void;
  /** HS-201-04 — called with the route this RECORD displays, so the
   *  disclosure and the request are the same object. */
  onRunIntelligence?: (route: PlannedRoute | null) => void;
  /** HS-201-04 — the hub's 409 on this record's last run gesture. */
  runRefusal?: SummaryRefusal | null;
  /** PHILO-17: bumped by the meeting window when its records may have moved. */
  revision?: number;
}) {
  const id = String(meeting?.id ?? "");
  const data = useMeetingData(meeting, onReceipt, revision);
  // PHILO-17 (the desk sweep): the body is drawn once (per meeting) when
  // the record's first reads and its Send well's have ended, or at the cap.
  const [wellRead, setWellRead] = useState<{ id: string; read: boolean } | null>(null);
  const reportWell = useCallback((read: boolean) => setWellRead({ id, read }), [id]);
  const [cappedFor, setCappedFor] = useState("");
  useEffect(() => {
    const timer = window.setTimeout(() => setCappedFor(id), MEETING_READS_CAP_MS);
    return () => window.clearTimeout(timer);
  }, [id]);
  const [drawnFor, setDrawnFor] = useState("");
  // The Send well is drawn on the outcomes face of a meeting with a summary.
  const wellAsked = view === "outcomes" && Boolean(readMeetingIntel(data.detail ?? meeting)?.summary?.trim());
  const wellDone = !wellAsked || (wellRead?.id === id && wellRead.read);
  const ready = cappedFor === id || (data.firstRead && wellDone);
  useLayoutEffect(() => {
    if (ready && drawnFor !== id) setDrawnFor(id);
  }, [ready, drawnFor, id]);
  const shown = drawnFor === id || ready;
  // PHILO-17 (quiet by default): with a summary on the record the
  // transcript is folded; Open transcript (the foot) and a decision moment
  // open it. With no summary it is the record's content, open.
  const hasSummaryText = Boolean(readMeetingIntel(data.detail ?? meeting)?.summary?.trim());
  const [transcriptAsked, setTranscriptOpen] = useState<boolean | null>(null);
  const transcriptOpen = transcriptAsked ?? (!hasSummaryText || momentSegmentIndex != null);
  useEffect(() => {
    const onOpen = (event: Event) => {
      if ((event as CustomEvent<string>).detail === id) setTranscriptOpen(true);
    };
    window.addEventListener(MEETING_TRANSCRIPT_OPEN, onOpen);
    return () => window.removeEventListener(MEETING_TRANSCRIPT_OPEN, onOpen);
  }, [id]);
  useEffect(() => {
    if (momentSegmentIndex != null) setTranscriptOpen(true);
  }, [momentSegmentIndex]);
  const {
    detail,
    setDetail,
    segments,
    artifactRows,
    intelOff,
    intelState,
    needsRows,
    needsCount,
    timelineRows,
  } = data;

  if (!meeting) return null;

  // HS-201-04: the summary the hub persisted, and the route facts that
  // belong beside every verb that starts a run. The detail read model is
  // the source for all three (`intel`, `planned_route`, `run_receipt`).
  const summaryIntel = readMeetingIntel(detail ?? meeting);
  const plannedRoute = readPlannedRoute(detail ?? meeting);
  // The route the record DISPLAYS: a refusal's fresh route wins over it.
  const displayedRoute = runRefusal?.route ?? plannedRoute;
  const runReceipt = executedReceipt(id, readRunReceipt(detail ?? meeting));

  const meetingTitle = String(detail?.title ?? meeting.title ?? "Meeting");
  const hasTranscript = segments.length > 0 || (
    meeting.transcriptWords != null && Number(meeting.transcriptWords) > 0
  );

  return (
    <SurfaceSection>
      <MeetingHeader meeting={meeting} data={data} compact={false} saidOnFace={saidOnFace} />
      {/* PHILO-17 (the desk sweep): the record's body is mounted at once
          (its wells start their reads) but drawn only when its first reads
          end, the Send well's included, or at the cap: a late read never
          moves a row under the owner's eye (UX-CANON D; the Room's pattern,
          roomReads.ts and project-room.css .room-body[data-settling]). */}
      <SendWellReadContext.Provider value={reportWell}>
      <div className="meetings-detail-body" data-settling={shown ? undefined : "true"} aria-busy={shown ? undefined : true}>
      {shown ? null : <div className="meetings-detail-settling-line"><SurfaceState loading /></div>}
      {/* PHILO-17 transcribe: an audio-only meeting's one verb, under the
          strip that says "NO TRANSCRIPT · SPEECH NOT SET UP". */}
      {onTranscribe ? (
        <AudioOnlyVerb row={{ ...meeting, ...(detail ?? {}) }} onTranscribe={onTranscribe} setUpSpeech testId="meeting-transcribe" />
      ) : null}
      <CaptureSlab detail={detail} meeting={meeting} />
      <MeetingConflictRecovery
        meetingId={id}
        onResolved={(result) => {
          onDeleted();
          if (result.deleted) {
            onClose();
          } else if (result.meeting) {
            setDetail(result.meeting);
          }
        }}
      />
      <MeetingIntelRecovery
        meetingId={id}
        onChanged={async () => {
          setDetail(await apiFetch(`/api/meetings/${encodeURIComponent(id)}`));
          onDeleted();
        }}
      />
      {view === "artifacts" ? (
        <ArtifactsLibrary
          artifactRows={artifactRows}
          meetingTitle={meetingTitle}
        />
      ) : (
        <>
          {/* PHILO-17 (the Today language): what was said first (the
              summary), then what was decided and who owes what, then the
              follow-up (Send), the transcript last. */}
          <MeetingSummarySlab intel={summaryIntel} receipt={runReceipt} saidOnFace={saidOnFace} />
          <MeetingOutcomes data={data} meeting={meeting} />
          <NeedsYouTable
            needsRows={needsRows}
            needsCount={needsCount}
            intelOff={intelOff}
            intelState={intelState}
            hasTranscript={hasTranscript}
            plannedRoute={displayedRoute}
            refusal={runRefusal}
            durableRefusal={readLastRefusal(detail ?? meeting)}
            onRunIntelligence={
              onRunIntelligence ? () => onRunIntelligence(displayedRoute) : undefined
            }
            onRetryIntelligence={
              (intelState === "error" || intelState === "failed") && onRunIntelligence
                ? () => onRunIntelligence(displayedRoute)
                : undefined
            }
            onSkipIntelligence={
              // HS-201-04: error/failed belong to the summary slab, which
              // already carries Retry and Skip. Only the QUEUED state (the
              // slab suppresses itself there) keeps its Skip here.
              (intelState === "queued" || intelState === "pending")
                ? async () => {
                    try {
                      await apiFetch(
                        `/api/meetings/${encodeURIComponent(id)}/intel-recovery/skip`,
                        { method: "POST" },
                      );
                      setDetail(await apiFetch(`/api/meetings/${encodeURIComponent(id)}`));
                      onDeleted();
                    } catch { /* stays */ }
                  }
                : undefined
            }
          />
          {/* PHILO-11-05 (canvas C1, C4): SUMMARY, then SEND; no summary, no well.
              The old aftercare Slack rows are gone (R7): the digest and the
              follow-up are forms of this one well. */}
          {summaryIntel?.summary?.trim() ? (
            <div id={`meeting-${id}-send`} className="meetings-detail-anchor">
              <MeetingSendWell meetingId={id} title={meetingTitle}
                startedAt={String((detail ?? meeting)?.started_at ?? "") || null} />
            </div>
          ) : null}
          {/* PHILO-13-08 (B3): Decide, next to SEND; with or without a summary. */}
          <MeetingDecideWell meetingId={id} title={meetingTitle}
            startedAt={String((detail ?? meeting)?.started_at ?? "") || null}
            summary={summaryIntel?.summary ?? null}
            runSummaryOnFace={showsRunSummary({
              intelOff, hasTranscript, plannedRoute: displayedRoute,
              onRunIntelligence: onRunIntelligence ? () => undefined : undefined,
            })} />
          <div id={`meeting-${id}-transcript`} className="meetings-detail-anchor">
            <TranscriptWell
              id={id}
              segments={segments}
              momentSegmentIndex={momentSegmentIndex}
              open={transcriptOpen}
              onOpenChange={setTranscriptOpen}
              emptyLabel={speechWasMissing(detail ?? meeting) ? NO_TRANSCRIPT_SPEECH : undefined}
            />
          </div>
          {/* RAW · ROUTING — the intent timeline section (only when data present) */}
          {timelineRows.length > 0 ? (
            <div className="meetings-detail-routing">
              <span className="surface-caption">RAW · ROUTING</span>
              <ul>
                {timelineRows.map((row, i) => (
                  <li key={i}>{String(row.kind ?? row.intent ?? row.text ?? "")}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      )}
      </div>
      </SendWellReadContext.Provider>
    </SurfaceSection>
  );
}

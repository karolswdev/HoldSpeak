// HS-170-04 — the meeting detail pane (the board's right side).
// Display title + tokens, NEEDS YOU section, TRANSCRIPT well, settled list.
import type { ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceSection } from "../../../desk/surface";
import { presentValue } from "../../../desk/surface/format";
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
import { MeetingReview } from "./MeetingReview";
import { useMeetingData, type FollowThroughProposal, type MeetingData } from "./useMeetingData";
import { MeetingHeader } from "./MeetingHeader";
import { CaptureSlab } from "./CaptureSlab";
import { ArtifactsLibrary } from "./ArtifactsLibrary";
import { MeetingSendWellLazy as MeetingSendWell } from "../../../meetings/MeetingSendWellLazy";
import { MeetingDecideWell } from "../../../meetings/MeetingDecideWell";
import { NeedsYouTable, showsRunSummary } from "./NeedsYouTable";
import { TranscriptWell } from "./TranscriptWell";


/** One row of the meeting's outcomes ledgers. */
type OutcomeRow = {
  key: string;
  plate: "DEC" | "ACT";
  text: string;
  meta: string;
  tone?: "ask" | "ok";
  verbs?: ReactNode;
};

/** Phase 16 (the interior kit; the canvas window "Cutover sync"): the
 *  meeting's Decisions and Commitments, each a Section over a Ledger of
 *  kind-plated rows. A decision the meeting proposed asks to be decided
 *  (`TO DECIDE`, Confirm / Dismiss); a confirmed one names its owner.
 *
 *  Commitments are OBLIGATIONS, one row each (Astra r1 M1): an action
 *  proposal names its action item (`action_item_id`, the producer's link in
 *  proposal_bridge_service.py), so the item and its proposal are ONE row,
 *  `TO CONFIRM` while the proposal waits. A dismissed proposal or item is
 *  never drawn. The items are the aftercare's rows, else the meeting's own
 *  (`intel.action_items`). A Section with no rows is not drawn (A.8). */
export function meetingOutcomes(
  data: Pick<MeetingData, "ftProposals" | "openActions" | "settledActions">,
  intelActions: readonly Record<string, unknown>[] = [],
): {
  decisions: OutcomeRow[];
  commitments: OutcomeRow[];
} {
  const owner = (value: unknown) => presentValue(value).toUpperCase();
  const live = data.ftProposals.filter((p) => p.state !== "dismissed");
  const decisions: OutcomeRow[] = live
    .filter((p) => p.kind === "decision")
    .map((p) => p.state === "proposed"
      ? { key: `ft-${p.id}`, plate: "DEC" as const, text: p.text, meta: "TO DECIDE", tone: "ask" as const }
      : {
        key: `ft-${p.id}`, plate: "DEC" as const, text: p.text,
        meta: owner(p.owner) || owner(p.owner_hint) || owner(p.speaker_label) || "DECIDED",
      });

  const actionProposals = data.ftProposals.filter((p) => p.kind === "action");
  const proposalOf = (itemId: string) => actionProposals.find((p) => p.action_item_id && p.action_item_id === itemId);
  const toConfirm = (p: FollowThroughProposal): OutcomeRow => ({
    key: `ft-${p.id}`, plate: "ACT", text: p.text,
    meta: p.due_hint ? `TO CONFIRM · BY ${String(p.due_hint).toUpperCase()}` : "TO CONFIRM", tone: "ask",
  });
  const items = data.openActions.length || data.settledActions.length
    ? [...data.openActions, ...data.settledActions]
    : [...intelActions];
  const itemIds = new Set<string>();
  const commitments: OutcomeRow[] = [];
  for (const [index, row] of items.entries()) {
    const id = String(row.id ?? "");
    if (id) itemIds.add(id);
    const status = String(row.status ?? "").toLowerCase();
    if (status === "dismissed") continue;
    const proposal = id ? proposalOf(id) : undefined;
    if (proposal?.state === "dismissed") continue;
    if (proposal?.state === "proposed") {
      commitments.push(toConfirm(proposal));
      continue;
    }
    const text = String(row.task ?? row.text ?? row.title ?? proposal?.text ?? "Action item");
    const who = owner(row.owner) || owner(proposal?.owner);
    const done = status === "done";
    commitments.push({
      key: `item-${id || index}`, plate: "ACT", text,
      meta: done ? (who ? `DONE · ${who}` : "DONE") : who || "UNASSIGNED",
      tone: done ? "ok" : undefined,
    });
  }
  // An action proposal whose item this face did not read is its own row.
  for (const p of live) {
    if (p.kind !== "action" || (p.action_item_id && itemIds.has(p.action_item_id))) continue;
    commitments.push(p.state === "proposed"
      ? toConfirm(p)
      : { key: `ft-${p.id}`, plate: "ACT", text: p.text, meta: owner(p.owner) || owner(p.owner_hint) || "UNASSIGNED" });
  }
  return { decisions, commitments };
}

function OutcomeLedger({ label, rows, testId }: { label: string; rows: OutcomeRow[]; testId: string }) {
  if (!rows.length) return null;
  return (
    <SurfaceSection label={label} count={rows.length || null} data-testid={testId}>
      <SurfaceLedger label={label} cols="kit">
        <ul className="surface-ledger-rows">
          {rows.map((row) => (
            <SurfaceLedgerRow
              key={row.key}
              data-testid={`${testId}-row`}
              kind={row.plate}
              kindTitle={row.plate === "DEC" ? "DECISION" : "ACTION"}
              primary={row.text}
              meta={row.meta}
              metaTone={row.tone}
              trailing={row.verbs}
              wrap
              expands={false}
            />
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
  const verbsFor = (row: OutcomeRow) => {
    const id = row.key.startsWith("ft-") ? row.key.slice(3) : "";
    const pending = id && data.ftProposals.some((p) => p.id === id && p.state === "proposed");
    if (!pending) return undefined;
    return (
      <>
        <Button dense variant="secondary" loading={data.busy} data-testid="proposal-confirm-btn"
          aria-label={`Confirm: ${row.text}`} onClick={() => void data.confirmProposal(id)}>
          Confirm
        </Button>
        <Button dense variant="ghost" loading={data.busy} data-testid="proposal-dismiss-btn"
          aria-label={`Dismiss: ${row.text}`} onClick={() => void data.dismissProposal(id)}>
          Dismiss
        </Button>
      </>
    );
  };
  const withVerbs = (rows: OutcomeRow[]) => rows.map((row) => ({ ...row, verbs: verbsFor(row) }));
  return (
    <>
      <OutcomeLedger label="Decisions" rows={withVerbs(decisions)} testId="meeting-decisions" />
      <OutcomeLedger label="Commitments" rows={withVerbs(commitments)} testId="meeting-commitments" />
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
  onReview,
  onOpenEvidence,
  runRefusal,
  footerRunReceipt,
}: {
  meeting: Record<string, unknown> | null;
  /** "outcomes" (the face), "review" (HS-200-12, posture 4) or "artifacts". */
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
  /** HS-200-12 — the way to the review wing from NEEDS YOU. */
  onReview?: () => void;
  /** HS-200-12 — `Open evidence`: the outcomes face, scrolled to a segment. */
  onOpenEvidence?: (segmentIndex: number | null) => void;
  /** HS-201-04 — the hub's 409 on this record's last run gesture. */
  runRefusal?: SummaryRefusal | null;
  /** PHILO-15-07 (B15): this meeting's summary-run receipt (QUEUED → RAN);
   *  the Review wing draws its own footer, so it shows it there. */
  footerRunReceipt?: Receipt | null;
}) {
  const id = String(meeting?.id ?? "");
  const data = useMeetingData(meeting, onReceipt);
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
      <MeetingHeader meeting={meeting} data={data} compact={view === "review"} />
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
      ) : view === "review" ? (
        <MeetingReview
          meetingId={id}
          onOpenEvidence={(segmentIndex) => onOpenEvidence?.(segmentIndex)}
          onOpenTranscript={() => onOpenEvidence?.(null)}
          onRunIntelligence={
            onRunIntelligence ? () => onRunIntelligence(displayedRoute) : undefined
          }
          onChanged={onDeleted}
          runReceipt={footerRunReceipt ?? null}
        />
      ) : (
        <>
          {/* Phase 16: Decisions · n, Commitments · n (the kit's Sections
              over Ledgers), right under the head. */}
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
            onReview={onReview}
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
          {/* HS-201-04: the summary is shown on the record, with its
              meeting — the result first, the transcript under it. */}
          <MeetingSummarySlab intel={summaryIntel} receipt={runReceipt} />
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
    </SurfaceSection>
  );
}

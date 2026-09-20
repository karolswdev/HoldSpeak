// HS-170-04 — the meeting detail pane (the board's right side).
// Display title + tokens, NEEDS YOU section, TRANSCRIPT well, settled list.
import { SurfaceSection } from "../../../desk/surface/Surface";
import { MeetingConflictRecovery } from "../../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../../meetings/MeetingIntelRecovery";
import {
  MeetingSummarySlab,
  readMeetingIntel,
} from "../../../meetings/MeetingSummarySlab";
import {
  readPlannedRoute,
  readRunReceipt,
  type SummaryRefusal,
} from "../../../meetings/summaryRoute";
import { apiFetch } from "../../../lib/api";
import type { DetailView, Receipt } from "./helpers";
import { MeetingReview } from "./MeetingReview";
import { useMeetingData } from "./useMeetingData";
import { MeetingHeader } from "./MeetingHeader";
import { CaptureSlab } from "./CaptureSlab";
import { ArtifactsLibrary } from "./ArtifactsLibrary";
import { AftercareGadgets } from "./AftercareGadgets";
import { NeedsYouTable } from "./NeedsYouTable";
import { TranscriptWell } from "./TranscriptWell";
import { SettledList } from "./SettledList";

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
  onRunIntelligence?: () => void;
  /** HS-200-12 — the way to the review wing from NEEDS YOU. */
  onReview?: () => void;
  /** HS-200-12 — `Open evidence`: the outcomes face, scrolled to a segment. */
  onOpenEvidence?: (segmentIndex: number | null) => void;
  /** HS-201-04 — the hub's 409 on this record's last run gesture. */
  runRefusal?: SummaryRefusal | null;
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
    settledActions,
    aftercare,
    authority,
    busy,
    proposeSlack,
    timelineRows,
  } = data;

  if (!meeting) return null;

  // HS-201-04: the summary the hub persisted, and the route facts that
  // belong beside every verb that starts a run. The detail read model is
  // the source for all three (`intel`, `planned_route`, `run_receipt`).
  const summaryIntel = readMeetingIntel(detail ?? meeting);
  const plannedRoute = readPlannedRoute(detail ?? meeting);
  const runReceipt = readRunReceipt(detail ?? meeting);

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
          onRunIntelligence={onRunIntelligence}
          onChanged={onDeleted}
        />
      ) : (
        <>
          <NeedsYouTable
            needsRows={needsRows}
            needsCount={needsCount}
            intelOff={intelOff}
            intelState={intelState}
            hasTranscript={hasTranscript}
            plannedRoute={runRefusal?.route ?? plannedRoute}
            refusal={runRefusal}
            onReview={onReview}
            onRunIntelligence={onRunIntelligence}
            onRetryIntelligence={
              (intelState === "error" || intelState === "failed") && onRunIntelligence
                ? onRunIntelligence
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
          <TranscriptWell
            id={id}
            segments={segments}
            momentSegmentIndex={momentSegmentIndex}
          />
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
          <AftercareGadgets
            aftercare={aftercare}
            authority={authority}
            busy={busy}
            proposeSlack={proposeSlack}
          />
          <SettledList settledActions={settledActions} />
        </>
      )}
    </SurfaceSection>
  );
}

// HS-170-04 — the meeting detail pane (the board's right side).
// Display title + tokens, NEEDS YOU section, TRANSCRIPT well, settled list.
import { SurfaceSection } from "../../../desk/surface/Surface";
import { MeetingConflictRecovery } from "../../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../../meetings/MeetingIntelRecovery";
import { apiFetch } from "../../../lib/api";
import type { Receipt } from "./helpers";
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
}: {
  meeting: Record<string, unknown> | null;
  /** "outcomes" (the face) or "artifacts" (the wing). */
  view: "outcomes" | "artifacts";
  /** HS-109-02/05: a resolved decision moment seeks this transcript row. */
  momentSegmentIndex?: number | null;
  onClose(): void;
  onDeleted(): void;
  /** HS-111-03 — outcomes land on the footer receipt bar. */
  onReceipt(receipt: Receipt): void;
  onRunIntelligence?: () => void;
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

  const meetingTitle = String(detail?.title ?? meeting.title ?? "Meeting");
  const hasTranscript = segments.length > 0 || (
    meeting.transcriptWords != null && Number(meeting.transcriptWords) > 0
  );

  return (
    <SurfaceSection>
      <MeetingHeader meeting={meeting} data={data} />
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
          <NeedsYouTable
            needsRows={needsRows}
            needsCount={needsCount}
            intelOff={intelOff}
            intelState={intelState}
            hasTranscript={hasTranscript}
            onRunIntelligence={onRunIntelligence}
            onRetryIntelligence={
              (intelState === "error" || intelState === "failed") && onRunIntelligence
                ? onRunIntelligence
                : undefined
            }
            onSkipIntelligence={
              (intelState === "queued" || intelState === "pending" || intelState === "error" || intelState === "failed")
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

// HS-117-09 — extracted from HistoryCore.tsx (lines 317-781).
// Thin composition shell over useMeetingData + sub-components.
import { SurfaceSection } from "../../../desk/surface/Surface";
import { SurfaceCode, SurfaceWell } from "../../../desk/surface/Surface";
import { FoldGadget } from "../../../desk/surface/gadgets";
import { MeetingConflictRecovery } from "../../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../../meetings/MeetingIntelRecovery";
import { apiFetch } from "../../../lib/api";
import type { Receipt } from "./helpers";
import { useMeetingData } from "./useMeetingData";
import { MeetingHeader } from "./MeetingHeader";
import { CaptureSlab } from "./CaptureSlab";
import { ArtifactsLibrary } from "./ArtifactsLibrary";
import { NeedsYouTable } from "./NeedsYouTable";
import { TranscriptWell } from "./TranscriptWell";
import { SettledList } from "./SettledList";
import { AftercareGadgets } from "./AftercareGadgets";

export function MeetingDetail({
  meeting,
  view,
  momentSegmentIndex,
  onClose,
  onDeleted,
  onReceipt,
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
}) {
  const id = String(meeting?.id ?? "");
  const data = useMeetingData(meeting, onReceipt);
  const {
    detail,
    setDetail,
    segments,
    artifactRows,
    timelineRows,
    aftercare,
    authority,
    busy,
    proposeSlack,
    intelOff,
    hasOutcomes,
    needsRows,
    needsCount,
    settledActions,
  } = data;

  if (!meeting) return null;

  const meetingTitle = String(detail?.title ?? meeting.title ?? "Meeting");

  return (
    <SurfaceSection>
      <MeetingHeader meeting={meeting} data={data} onClose={onClose} />
      {/* 1 — attention slabs, only when real. */}
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
          {/* 2 — what needs you: pending receipts in ONE dense table.
              Intelligence OFF says so as a token, never a sentence. */}
          <NeedsYouTable
            needsRows={needsRows}
            needsCount={needsCount}
            intelOff={intelOff}
            hasOutcomes={hasOutcomes}
          />
          {/* 3 — THE TRANSCRIPT WELL: always visible, never folded. */}
          <TranscriptWell
            id={id}
            segments={segments}
            momentSegmentIndex={momentSegmentIndex}
          />
          {/* 4 — settled: quiet ledger lines. */}
          <SettledList settledActions={settledActions} />
          {/* 5 — the routing receipt stays folded, in its own well. */}
          {timelineRows.length ? (
            <FoldGadget title="RAW · ROUTING">
              <SurfaceWell head={`RAW · ROUTING · ${timelineRows.length}`}>
                <SurfaceCode>
                  {JSON.stringify(timelineRows, null, 2)}
                </SurfaceCode>
              </SurfaceWell>
            </FoldGadget>
          ) : null}
          {/* 6 — aftercare rides the gadget grammar, only when wired. */}
          <AftercareGadgets
            aftercare={aftercare}
            authority={authority}
            busy={busy}
            proposeSlack={proposeSlack}
          />
        </>
      )}
    </SurfaceSection>
  );
}

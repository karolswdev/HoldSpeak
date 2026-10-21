import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Artifact pullout content (HS-117-15). */
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { lineage } from "../lineage";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { humanizeWireValue } from "../../lib/productLanguage";
import { Material } from "../surface/Material";
import type { PulloutContentProps } from "./types";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { Button } from "../../components/signal/Signal";
import { ArtifactSendWells } from "../documentSendsLazy";
import { ActionNotice, FoldGadget, StateChip, SurfaceState, SurfaceWell } from "../surface";
import { presentArtifact } from "./artifactPresentation";
import "./artifact-reading.css";

export function ArtifactPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const { openPullout } = useDesk.getState();
  if (o.ref.kind !== "artifact") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const body = String(ir.bodyMarkdown || "");
  const presentation = presentArtifact({
    title: String(ir.title || o.title || "Artifact"),
    artifactType: String(ir.artifactType || "artifact"),
    bodyMarkdown: body,
    sources: ir.sources,
    items,
  });
  const read = ir.sourceRead;
  const hasMaterial = read?.hasMaterial !== false;
  const hasReadingMaterial = hasMaterial && !presentation.isEmptyResult;
  const reviewState = ir.status === "pending-review" ? { state: "warning" as const, label: "Awaiting review" }
    : ir.status === "rejected" ? { state: "failure" as const, label: "Rejected" } : null;
  const meeting = ir.meetingId ? lineage(items, [{ source_type: "meeting", source_ref: ir.meetingId }]).from[0] : null;
  const openMeeting = meeting?.resolved
    ? () => openPullout(meeting.actionRef ?? qualifiedRef("meeting", String(ir.meetingId)))
    : undefined;

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        {read ? <ActionNotice role="alert" tone="danger" action={{ label: "Retry read", onClick: () => void useDesk.getState().refresh() }}>
          <StateChip state={read.state === "unavailable" ? "unreachable" : "failure"} label={read.state === "unavailable" ? "Source unavailable" : "Read failed"} />
          {hasMaterial ? <StateChip state="warning" label="Last read" /> : null}
          {read.state === "failed" ? <span>{humanizeWireValue(read.message)}</span> : null}
        </ActionNotice> : null}
        {reviewState ? <StateChip {...reviewState} /> : null}
        {hasMaterial ? <section className="artifact-reading-section">
          <div className="artifact-reading">
            {presentation.isEmptyResult
              ? <SurfaceState empty emptyGlyph="" emptyLabel={presentation.emptyLabel} onAction={openMeeting} actionLabel={openMeeting ? "Open meeting" : undefined} />
              : <SurfaceWell><Material>{presentation.body}</Material></SurfaceWell>}
          </div>
        </section> : null}
        {/* PHILO-13-15 (C5, canvas P5): the artifact's SEND well. */}
        {hasReadingMaterial ? <ArtifactSendWells id={o.id} title={String(ir.title || o.title || "Artifact")} type={String(ir.artifactType || "artifact")} /> : null}
        {hasMaterial && presentation.sources.length > 0 ? (
          <FoldGadget title="Sources" className="artifact-sources-fold">
            <div className="artifact-sources" data-testid="artifact-sources">
              {presentation.sources.map((source) => source.resolved ? (
                <Button key={`${source.type}:${source.ref}`} dense variant="ghost" onClick={() => openPullout(source.actionRef ?? source.ref)}>
                  {source.via ? `via ${source.label}` : source.label}
                </Button>
              ) : (
                <span key={`${source.type}:${source.ref}`} className="artifact-source-unresolved" data-testid="artifact-source-unresolved">
                  {source.via ? `via ${source.label}` : source.label}
                </span>
              ))}
            </div>
          </FoldGadget>
        ) : null}
        {hasMaterial ? <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        /> : null}
      </div>
      <SurfaceFooter receipt={copyReceipt} verbs={<>
        {hasMaterial ? <Button dense variant="ghost" onClick={() => void copy(body)}>Copy</Button> : null}
        {hasMaterial ? <Button dense variant="ghost" onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}>
          Dictate about this
        </Button> : null}</>} />
    </>
  );
}

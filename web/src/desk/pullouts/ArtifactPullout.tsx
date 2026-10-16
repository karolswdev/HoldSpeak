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
import { ActionNotice, StateChip, SurfaceWell } from "../surface";
import "./artifact-reading.css";

export function ArtifactPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const { openPullout } = useDesk.getState();
  if (o.ref.kind !== "artifact") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const body = String(ir.bodyMarkdown || "");
  const lin = lineage(items, ir.sources);
  const read = ir.sourceRead;
  const hasMaterial = read?.hasMaterial !== false;
  const reviewState = ir.status === "pending-review" ? { state: "warning" as const, label: "Awaiting review" }
    : ir.status === "rejected" ? { state: "failure" as const, label: "Rejected" } : null;

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        {read ? <ActionNotice role="alert" tone="danger" action={{ label: "Retry read", onClick: () => void useDesk.getState().refresh() }}>
          <StateChip state={read.state === "unavailable" ? "unreachable" : "failure"} label={read.state === "unavailable" ? "Source unavailable" : "Read failed"} />
          {hasMaterial ? <StateChip state="warning" label="Last read" /> : null}
          {read.state === "failed" ? <span>{humanizeWireValue(read.message)}</span> : null}
        </ActionNotice> : null}
        {reviewState ? <StateChip {...reviewState} /> : null}
        {hasMaterial ? <section>
          <h3>{humanizeWireValue(String(ir.artifactType || "artifact"))}</h3>
          <div className="artifact-reading"><SurfaceWell><Material>{body}</Material></SurfaceWell></div>
        </section> : null}
        {/* PHILO-13-15 (C5, canvas P5): the artifact's SEND well. */}
        {hasMaterial ? <ArtifactSendWells id={o.id} title={String(ir.title || o.title || "Artifact")} type={String(ir.artifactType || "artifact")} /> : null}
        {lin.any && (
          <section>
            <h3>Lineage</h3>
            <div className="desk-pullout-lineage">
              {lin.via && (
                <span className="desk-chip quiet">via {lin.via.label}</span>
              )}
              {lin.from.map((f) => (
                <Button key={f.ref} dense variant="ghost" onClick={() => f.resolved && openPullout(f.ref)}>
                  {f.label}
                </Button>
              ))}
            </div>
          </section>
        )}
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

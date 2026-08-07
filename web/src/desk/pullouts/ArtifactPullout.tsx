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

export function ArtifactPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const { openPullout } = useDesk.getState();
  if (o.ref.kind !== "artifact") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const body = String(ir.bodyMarkdown || "");
  const lin = lineage(items, ir.sources);

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <section>
          <h3>{humanizeWireValue(String(ir.artifactType || "artifact"))}</h3>
          <Material>{body}</Material>
        </section>
        {lin.any && (
          <section>
            <h3>Lineage</h3>
            <div className="desk-pullout-lineage">
              {lin.via && (
                <span className="desk-chip quiet">via {lin.via.label}</span>
              )}
              {lin.from.map((f) => (
                <button
                  key={f.ref}
                  type="button"
                  className="desk-chip quiet"
                  onClick={() => f.resolved && openPullout(f.ref)}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </section>
        )}
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      <SurfaceFooter receipt={copyReceipt} verbs={<>
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() => void copy(body)}
        >
          Copy
        </button>
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </button> </>} />
    </>
  );
}

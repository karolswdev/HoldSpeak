/* PHILO-12-02 canvas, board J1 (design section 7; faces F10): the PRODUCT's
 * ArtifactPullout (web/src/desk/pullouts/ArtifactPullout.tsx) with two changes,
 * and nothing else:
 *   1. its three raw <button>s (the lineage chips, Copy, Dictate about this)
 *      are the library Button (UX-CANON A.1);
 *   2. the SEND well composes on `artifact:<id>` after the body, as on every
 *      other document window (Phase 11 R4), labelled `ARTIFACT · <TYPE>`.
 * Story 03 builds this in the product file. */
import { SurfaceFooter } from "@w/desk/surface/SurfaceFooter";
import { useDesk } from "@w/desk/store";
import { openSurfaceOr } from "@w/desk/shell";
import { qualifiedRef } from "@w/desk/api";
import { lineage } from "@w/desk/lineage";
import { DeskFilingStrip } from "@w/desk/components/DeskFilingStrip";
import { humanizeWireValue } from "@w/lib/productLanguage";
import { Material } from "@w/desk/surface/Material";
import type { PulloutContentProps } from "@w/desk/pullouts/types";
import { useCopyReceipt } from "@w/desk/hooks/useCopyReceipt";
import { Button } from "@w/components/signal/Signal";
import { SendWells } from "@w/desk/surface/send";

export function ArtifactPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const { openPullout } = useDesk.getState();
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  if (o.ref.kind !== "artifact") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);
  const body = String(ir.bodyMarkdown || "");
  const lin = lineage(items, ir.sources);
  const type = String(ir.artifactType || "artifact");

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <section>
          <h3>{humanizeWireValue(type)}</h3>
          <Material>{body}</Material>
        </section>
        <div data-seat="artifact" data-p12="seat">
          <SendWells doc={{ ref: `artifact:${o.id}`, title: String(ir.title || "Artifact"), label: `ARTIFACT · ${type.replace(/[_-]+/g, " ").toUpperCase()}` }} />
        </div>
        {lin.any && (
          <section>
            <h3>Lineage</h3>
            <div className="desk-pullout-lineage">
              {lin.via && <span className="desk-chip quiet">via {lin.via.label}</span>}
              {lin.from.map((f) => (
                <Button key={f.ref} dense variant="ghost" data-p12="lineage" onClick={() => f.resolved && openPullout(f.ref)}>
                  {f.label}
                </Button>
              ))}
            </div>
          </section>
        )}
        <DeskFilingStrip objectRef={resourceRef} objectKind={o.kind} objectId={o.id} />
      </div>
      <SurfaceFooter receipt={copyReceipt} verbs={<>
        <Button dense variant="ghost" data-p12="verb" onClick={() => void copy(body)}>Copy</Button>
        <Button dense variant="ghost" data-p12="verb" onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}>Dictate about this</Button>
      </>} />
    </>
  );
}

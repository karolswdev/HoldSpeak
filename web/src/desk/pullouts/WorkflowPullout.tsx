/** Workflow pullout content (HS-117-15). */
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { parseLinearGraph, stepLabel } from "../graph";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { CapabilitySection } from "./shared/CapabilitySection";
import type { PulloutContentProps } from "./types";

export function WorkflowPullout({ object: o }: PulloutContentProps) {
  const { openEditor } = useDesk.getState();
  if (o.ref.kind !== "workflow") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);

  const steps =
    ir.graphJson
      ? (parseLinearGraph(ir.graphJson)?.map(stepLabel) ?? ["Graphed on iPad"])
      : ir.prompt
        ? [ir.prompt]
        : [];

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <section>
          <h3>Steps</h3>
          <ol className="desk-pullout-steps">
            {steps.map((st, i) => (
              <li key={i}>{st}</li>
            ))}
          </ol>
        </section>
        <CapabilitySection object={o} />
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      <footer className="desk-pullout-foot">
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </button>
        <button
          type="button"
          className="desk-chip is-primary"
          onClick={() => openEditor(o.id)}
        >
          Edit
        </button>
      </footer>
    </>
  );
}

/** Chain (Sequence) pullout content (HS-117-15). */
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { CapabilitySection } from "./shared/CapabilitySection";
import type { PulloutContentProps } from "./types";

export function ChainPullout({ object: o }: PulloutContentProps) {
  if (o.ref.kind !== "chain") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <section>
          <h3>Steps</h3>
          <ol className="desk-pullout-steps">
            {((ir.steps as string[]) || []).map((st, i) => (
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
      </footer>
    </>
  );
}

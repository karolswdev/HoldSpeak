import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Chain (Sequence) pullout content (HS-117-15). */
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { AgentAvatar } from "../components/AgentAvatar";
import { SurfaceRow, SurfaceRows, SurfaceState } from "../surface/Surface";
import { CapabilitySection } from "./shared/CapabilitySection";
import type { PulloutContentProps } from "./types";
import { Button } from "../../components/signal/Signal";

export function ChainPullout({ object: o }: PulloutContentProps) {
  const recipes = useDesk((s) => s.items.recipe);
  if (o.ref.kind !== "chain") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <section>
          <h3>Steps</h3>
          {ir.steps.length ? (
            <SurfaceRows>
              {ir.steps.map((stepId, index) => {
                const recipe = recipes.find((candidate) => candidate.id === stepId);
                return (
                  <SurfaceRow
                    key={`${stepId}-${index}`}
                    glyph={
                      recipe?.avatar ? (
                        <AgentAvatar avatar={recipe.avatar} id={recipe.id} size={16} />
                      ) : undefined
                    }
                    title={recipe?.name || `${stepId.slice(0, 6)}…?`}
                  />
                );
              })}
            </SurfaceRows>
          ) : (
            <SurfaceState
              empty
              emptyLabel="No steps"
              emptyGlyph="○"
            />
          )}
        </section>
        <CapabilitySection object={o} />
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      {/* Edit is parked until the existing registry supplies a Sequence editor. */}
      <SurfaceFooter verbs={<Button
          dense
          variant="ghost"
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </Button>} />
    </>
  );
}

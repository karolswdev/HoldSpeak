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

export function ChainPullout({ object: o }: PulloutContentProps) {
  const recipes = useDesk((s) => s.items.recipe);
  const { openEditor } = useDesk.getState();
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
              actionLabel="Edit chain"
              onAction={() => openEditor(o.id)}
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
      <SurfaceFooter verbs={<> <button
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
        </button> </>} />
    </>
  );
}

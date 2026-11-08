/** Chain (Sequence) pullout content (HS-117-15).
 *
 * W2-BUILDER (Window Program, atlas 2026-10-27): on the window grammar.
 * Toolbar (Add mode · Choose engine · Dictate about this), the steps as a
 * quiet list, the material and its Run, the filing fold, a status bar. Add
 * mode really adds: it appends a Mode to the Sequence's steps through the
 * hub's update route (`PUT /api/chains/{id}`). */
import { useRef, useState } from "react";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { AgentAvatar } from "../components/AgentAvatar";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { SurfaceRow, SurfaceRows, SurfaceSection, SurfaceState } from "../surface/Surface";
import { StatusBar, ToolGlyph, Toolbar, countWords } from "../surface/kit";
import { CapabilitySection, openCapabilityEngines } from "./shared/CapabilitySection";
import type { PulloutContentProps } from "./types";
import { Button } from "../../components/signal/Signal";
import "./capability-window.css";

export function ChainPullout({ object: o }: PulloutContentProps) {
  const recipes = useDesk((s) => s.items.recipe);
  const [menuOpen, setMenuOpen] = useState(false);
  const [adding, setAdding] = useState(false);
  const addRef = useRef<HTMLButtonElement | null>(null);
  if (o.ref.kind !== "chain") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);

  const addStep = async (recipeId: string) => {
    setAdding(true);
    const ok = await useDesk.getState().updatePrimitive("chain", o.id, { steps: [...ir.steps, recipeId] });
    // The hub re-reads the Sequence's readiness after the write.
    if (ok) await useDesk.getState().refresh().catch(() => undefined);
    setAdding(false);
  };
  const menuEntries: WorkMenuEntry[] = recipes.length
    ? recipes.map((recipe) => ({
        type: "item" as const,
        id: `sequence-add-${recipe.id}`,
        label: recipe.name || "Mode",
        glyph: recipe.avatar ? <AgentAvatar avatar={recipe.avatar} id={recipe.id} size={16} /> : undefined,
        onSelect: () => void addStep(recipe.id),
      }))
    : [{ type: "note", id: "sequence-add-none", label: "No modes yet. New ▸ Mode makes one." }];

  return (
    <>
      <div className="desk-pullout-body desk-surface-body capw-window" data-interior="editor" data-testid="sequence-window">
        <Toolbar label="Sequence" data-testid="sequence-toolbar">
          <Button
            ref={addRef}
            dense
            variant={ir.steps.length ? "secondary" : "primary"}
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            loading={adding}
            disabled={adding}
            onClick={() => setMenuOpen((open) => !open)}
            data-testid="sequence-add-mode"
          >
            <ToolGlyph kind="new" />Add mode
          </Button>
          <Button dense variant="ghost" onClick={() => openCapabilityEngines(o)}>
            <ToolGlyph kind="engine" />Choose engine
          </Button>
          <Button dense variant="ghost" onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}>
            Dictate about this
          </Button>
        </Toolbar>
        {menuOpen && addRef.current ? (
          <WorkMenu
            label="Add mode"
            x={addRef.current.getBoundingClientRect().left}
            y={addRef.current.getBoundingClientRect().bottom}
            entries={menuEntries}
            onClose={() => setMenuOpen(false)}
          />
        ) : null}
        <div className="capw-page">
          <SurfaceSection label="Steps" data-testid="sequence-steps">
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
                      title={recipe?.name || "Mode not found"}
                      detail={`Step ${index + 1}`}
                    />
                  );
                })}
              </SurfaceRows>
            ) : (
              <SurfaceState
                empty
                emptyLabel="No steps yet. Add mode puts the first one here."
                emptyGlyph="○"
              />
            )}
          </SurfaceSection>
          <CapabilitySection object={o} blocked={ir.steps.length ? undefined : "Add a mode first, then type the material."} />
          <DeskFilingStrip
            objectRef={resourceRef}
            objectKind={o.kind}
            objectId={o.id}
          />
        </div>
      </div>
      <StatusBar
        data-testid="sequence-status"
        items={[{ key: "steps", text: countWords(ir.steps.length, "step") }]}
      />
    </>
  );
}

import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Workflow pullout content (HS-117-15). */
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { parseLinearGraph, stepLabel } from "../graph";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { INLINE_EDITOR_CONTENT } from "./editors";
import { CapabilitySection, openCapabilityEngines } from "./shared/CapabilitySection";
import { SurfaceSection, SurfaceState } from "../surface/Surface";
import { StatusBar, ToolGlyph, Toolbar, countWords } from "../surface/kit";
import "./capability-window.css";
import type { PulloutContentProps } from "./types";
import { useEditorSession } from "./editors/useDebouncedSave";

export function WorkflowPullout({ object: o, registerClose }: PulloutContentProps) {
  const editing = useDesk((s) => s.editingId === o.id);
  const { openEditor, closeEditor } = useDesk.getState();
  const session = useEditorSession(closeEditor, editing ? registerClose : undefined);
  if (o.ref.kind !== "workflow") return null;
  const ir = o.ref;
  const Content = INLINE_EDITOR_CONTENT[o.kind];
  const resourceRef = qualifiedRef(o.kind, o.id);

  const steps =
    ir.graphJson
      ? (parseLinearGraph(ir.graphJson)?.map(stepLabel) ?? ["Graphed on iPad"])
      : ir.prompt
        ? [ir.prompt]
        : [];

  // W2-BUILDER (atlas 2026-10-27): the Workflow on the window grammar.
  // Toolbar (Edit · Choose engine · Dictate about this; Edit left the title
  // bar), the steps as a quiet list, the material and its Run (a greyed Run
  // says why), the filing fold, a status bar.
  if (editing && Content) {
    return (
      <>
        <div className="desk-pullout-body desk-surface-body desk-editor-body">
          <Content object={o} onClose={() => void session.done()} onWriter={session.onWriter} />
        </div>
        <SurfaceFooter receipt={session.receipt} verbs={session.verbs} />
      </>
    );
  }
  return (
    <>
      <div className="desk-pullout-body desk-surface-body capw-window" data-interior="editor" data-testid="workflow-window">
        <Toolbar label="Workflow" data-testid="workflow-toolbar">
          <Button dense variant="secondary" onClick={() => openEditor(o.id)}>
            <ToolGlyph kind="edit" />Edit
          </Button>
          <Button dense variant="ghost" onClick={() => openCapabilityEngines(o)}>
            <ToolGlyph kind="engine" />Choose engine
          </Button>
          <Button dense variant="ghost" onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}>
            Dictate about this
          </Button>
        </Toolbar>
        <div className="capw-page">
          <SurfaceSection label="Steps" data-testid="workflow-steps">
            {steps.length ? (
              <ol className="capw-steps">
                {steps.map((st, i) => (
                  <li key={i}>{st}</li>
                ))}
              </ol>
            ) : (
              <SurfaceState empty emptyLabel="No steps yet. Edit adds the first one." emptyGlyph="○" />
            )}
          </SurfaceSection>
          <CapabilitySection object={o} />
          <DeskFilingStrip
            objectRef={resourceRef}
            objectKind={o.kind}
            objectId={o.id}
          />
        </div>
      </div>
      <StatusBar data-testid="workflow-status" items={[{ key: "steps", text: countWords(steps.length, "step") }]} />
    </>
  );
}

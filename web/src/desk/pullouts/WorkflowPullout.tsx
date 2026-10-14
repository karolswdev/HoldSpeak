import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Workflow pullout content (HS-117-15). */
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { parseLinearGraph, stepLabel } from "../graph";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { INLINE_EDITOR_CONTENT } from "./editors";
import { CapabilitySection } from "./shared/CapabilitySection";
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

  return (
    <>
      <div className="desk-pullout-body desk-surface-body desk-editor-body">
        {editing && Content ? <Content object={o} onClose={() => void session.done()} onWriter={session.onWriter} /> : <>
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
        </>}
      </div>
      <SurfaceFooter receipt={editing ? session.receipt : null} verbs={editing ? session.verbs : <>
        <Button
          dense
          variant="ghost"
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </Button>
        <Button
          dense
          variant="primary"
          onClick={() => openEditor(o.id)}
        >
          Edit
        </Button>
      </>} />
    </>
  );
}

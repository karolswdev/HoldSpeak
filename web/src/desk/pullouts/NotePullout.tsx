import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Note pullout content (HS-117-15). */
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { Material } from "../surface/Material";
import { SurfaceState } from "../surface/Surface";
import { INLINE_EDITOR_CONTENT } from "./editors";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import type { PulloutContentProps } from "./types";

export function NotePullout({ object: o }: PulloutContentProps) {
  const editing = useDesk((s) => s.editingId === o.id);
  const { openEditor, closeEditor } = useDesk.getState();
  if (o.ref.kind !== "note") return null;
  const ir = o.ref;
  const Content = INLINE_EDITOR_CONTENT[o.kind];
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  const body = String(ir.bodyMarkdown || "");

  return (
    <>
      <div className="desk-pullout-body desk-surface-body desk-editor-body">
        {editing && Content ? (
          <Content object={o} onClose={closeEditor} />
        ) : body ? (
          <section>
            <Material>{body}</Material>
          </section>
        ) : (
          <section>
            <SurfaceState
              empty
              emptyLabel="Empty note"
              actionLabel="Start writing"
              onAction={() => openEditor(o.id)}
            />
          </section>
        )}
        {!editing && (
          <DeskFilingStrip
            objectRef={resourceRef}
            objectKind={o.kind}
            objectId={o.id}
          />
        )}
      </div>
      <SurfaceFooter receipt={editing ? null : copyReceipt} verbs={editing ? <>
        <button type="button" className="desk-chip quiet" onClick={closeEditor}>Cancel</button>
        <button type="button" className="desk-chip is-primary" onClick={closeEditor}>Save</button>
      </> : <>
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
        </button>
        <button
          type="button"
          className="desk-chip is-primary"
          onClick={() => openEditor(o.id)}
        >
          Edit
        </button>
      </>} />
    </>
  );
}

// HS-129-08 — editors are desk windows, never a modal layer.
import "./inline-editor.css";
import { useDesk } from "../store";
import type { WorldObject } from "../world";
import type { UnitPos } from "../store";
import { INLINE_EDITOR_CONTENT, EDITOR_LABELS } from "../pullouts/editors";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { DeskWindowFrame } from "./DeskWindow";

export function InlineEditor({ o, u }: { o: WorldObject; u: UnitPos }) {
  const pulloutOpen = useDesk((s) => s.pullouts.some((p) => p.id === o.id));
  const editorOrigin = useDesk((s) => s.editorOrigin);
  const isNew = useDesk((s) => s.newIds.includes(o.id));
  const { closeEditor } = useDesk.getState();
  const Content = INLINE_EDITOR_CONTENT[o.kind];
  const label = EDITOR_LABELS[o.kind] || o.kind;
  const origin = editorOrigin ?? {
    x: Math.round(u.x * window.innerWidth),
    y: Math.round(u.y * window.innerHeight),
  };

  // The object's open pullout owns its editor. The desk only hosts the
  // separate window path when there is no object surface already open.
  if (pulloutOpen || !Content) return null;

  return (
    <DeskWindowFrame
      id={`editor:${o.kind}:${o.id}`}
      glyph="✎"
      label={`Edit ${o.title}`}
      className="desk-pullout is-card desk-editor-window"
      fitContent
      origin={origin}
      title={`Edit ${o.title}`}
      open
      onClose={closeEditor}
    >
      <div className="desk-pullout-body desk-surface-body desk-editor-body">
        <Content object={o} onClose={closeEditor} autoFocusName={isNew} />
      </div>
      <SurfaceFooter
        verbs={
          <>
            <button type="button" className="desk-chip quiet" onClick={closeEditor}>
              Cancel
            </button>
            <button type="button" className="desk-chip is-primary" onClick={closeEditor}>
              Save
            </button>
          </>
        }
      />
    </DeskWindowFrame>
  );
}

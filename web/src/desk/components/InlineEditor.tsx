// HS-129-08 — editors are desk windows, never a modal layer.
import "./inline-editor.css";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import type { WorldObject } from "../world";
import type { UnitPos } from "../store";
import { INLINE_EDITOR_CONTENT, EDITOR_LABELS } from "../pullouts/editors";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { DeskWindowFrame } from "./DeskWindow";
import { qualifiedRef } from "../api";
import { keptReceipt } from "../keptReceipt";

export function InlineEditor({ o, u }: { o: WorldObject; u: UnitPos }) {
  // Pullouts may arrive from older raw-id paths or the canonical qualified
  // path. They are the same object surface, and it alone owns the editor.
  const pulloutOpen = useDesk((s) => s.pullouts.some((p) =>
    p.id === o.id || p.id === qualifiedRef(o.kind, o.id),
  ));
  const editorOrigin = useDesk((s) => s.editorOrigin);
  const isNew = useDesk((s) => s.newIds.includes(o.id));
  /* HS-202-02 — the editor writes through a debounce, so the object is
     kept as the owner types. The foot states WHEN; before this, a saved
     note gave no sign at all (04-sober-eye.md, rank 5). */
  const kept = useDesk((s) => s.keptAt[o.id]);
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
      glyph="E"
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
        receipt={
          keptReceipt(kept) ? (
            <span className="surface-footer-receipt-line" role="status">
              {keptReceipt(kept)}
            </span>
          ) : null
        }
        verbs={
          <>
            <Button dense variant="ghost" onClick={closeEditor}>
              Cancel
            </Button>
            <Button dense variant="primary" onClick={closeEditor}>
              Save
            </Button>
          </>
        }
      />
    </DeskWindowFrame>
  );
}

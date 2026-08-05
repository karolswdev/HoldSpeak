// The inline editor chrome shell (HS-117-15): vignette overlay, positioned
// container, header eyebrow, and Escape handler — body + footer delegated
// to the kind-keyed editor content registry.
import "./inline-editor.css";
import { useEffect, useRef } from "react";
import { useDesk } from "../store";
import type { WorldObject } from "../world";
import type { UnitPos } from "../store";
import { INLINE_EDITOR_CONTENT, EDITOR_LABELS } from "../pullouts/editors";

export function InlineEditor({ o, u }: { o: WorldObject; u: UnitPos }) {
  const { closeEditor } = useDesk.getState();
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeEditor();
    };
    document.addEventListener("keydown", onKey);
    ref.current?.querySelector<HTMLInputElement>("input, textarea")?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const side = u.x > 0.55 ? "left" : "right";
  const style: React.CSSProperties = {
    top: `${Math.min(78, Math.max(8, u.y * 100 - 6)).toFixed(2)}%`,
    [side === "right" ? "left" : "right"]:
      `${(side === "right" ? u.x * 100 + 7 : (1 - u.x) * 100 + 7).toFixed(2)}%`,
  };

  const Content = INLINE_EDITOR_CONTENT[o.kind];

  return (
    <>
      <div
        className="desk-vignette"
        style={
          {
            "--vx": `${u.x * 100}%`,
            "--vy": `${u.y * 100}%`,
          } as React.CSSProperties
        }
        onPointerDown={closeEditor}
      />
      <div
        ref={ref}
        className="desk-inline-editor"
        style={style}
        onPointerDown={(e) => e.stopPropagation()}
      >
        <header className="desk-inline-editor-head">
          <span className="desk-panel-eyebrow">
            {EDITOR_LABELS[o.kind] || o.kind}
          </span>
          <button
            type="button"
            className="desk-pullout-close"
            onClick={closeEditor}
            aria-label="Close editor"
          >
            ✕
          </button>
        </header>
        {Content ? (
          <Content object={o} onClose={closeEditor} />
        ) : null}
      </div>
    </>
  );
}

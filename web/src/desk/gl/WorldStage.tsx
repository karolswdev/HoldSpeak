/** HS-95-01 — the world, GPU-rendered. One canvas draws zones, objects,
 * selection, drag, and ambient motes (see engine.ts); the DOM keeps only
 * text-first overlays above it — the rename row, the inline editor, the
 * pull-out and Ask windows, the honest chips, and a visually-hidden
 * accessibility layer that preserves the DOM world's keyboard contract
 * (Enter/Space opens an object, dives a zone). */
import { useEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../store";
import { useProjections } from "../projections";
import { objectByRef, objUnit } from "../world";
import { InlineEditor } from "../components/InlineEditor";
import { Pullout } from "../components/Pullout";
import { AskBar, AskPanel } from "../components/AskPanel";
import { MicButton } from "../components/MicButton";
import { WorldEngine } from "./engine";
import { buildScene, type WorldScene } from "./sceneModel";

export { MAX_FLOATERS } from "./sceneModel";

export function WorldStage() {
  // Fine-grained subscriptions on purpose: a drag writes `positions` on
  // every pointer move, and this component must NOT re-render for that —
  // per-frame world motion is the engine's, on the GPU. React re-renders
  // only for overlay-relevant changes (open editors, renames, item churn).
  const items = useDesk((s) => s.items);
  const divedZone = useDesk((s) => s.divedZone);
  const editingId = useDesk((s) => s.editingId);
  const pulloutId = useDesk((s) => s.pulloutId);
  const askOpen = useDesk((s) => s.askOpen);
  const renamingZoneId = useDesk((s) => s.renamingZoneId);
  const editorPos = useDesk((s) =>
    s.editingId ? (s.positions[s.editingId] ?? null) : null,
  );
  const renamePos = useDesk((s) =>
    s.renamingZoneId ? (s.positions[`zone:${s.renamingZoneId}`] ?? null) : null,
  );
  const renameWidth = useDesk((s) =>
    s.renamingZoneId ? (s.zoneWidths[s.renamingZoneId] ?? null) : null,
  );
  const subjectCounts = useProjections((s) => s.subject_counts);

  const hostRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const engineRef = useRef<WorldEngine | null>(null);
  const [lasso, setLasso] = useState<{
    left: number;
    top: number;
    w: number;
    h: number;
  } | null>(null);

  // The a11y/chip scene: the same pure projection the engine draws from,
  // fed only the overlay-relevant position slices (see the selectors above).
  const scene: WorldScene = useMemo(
    () =>
      buildScene({
        items,
        divedZone,
        positions:
          renamingZoneId && renamePos
            ? { [`zone:${renamingZoneId}`]: renamePos }
            : {},
        zoneWidths:
          renamingZoneId && renameWidth ? { [renamingZoneId]: renameWidth } : {},
        draggingId: null,
        hoverZoneId: null,
        renamingZoneId,
        newIds: [],
        editingId,
        selectedIds: [],
        subjectCounts: subjectCounts || {},
        compact:
          typeof window !== "undefined" ? window.innerWidth <= 720 : false,
        worldWidth:
          hostRef.current?.clientWidth ??
          (typeof window !== "undefined" ? window.innerWidth : 1280),
      }),
    [
      items,
      divedZone,
      editingId,
      renamingZoneId,
      renamePos,
      renameWidth,
      subjectCounts,
    ],
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    const host = hostRef.current;
    if (!canvas || !host) return;
    const engine = new WorldEngine(canvas, host, {
      onLasso: setLasso,
      onRenameZone: (zoneId) => useDesk.getState().setRenamingZone(zoneId),
    });
    engineRef.current = engine;
    void engine.init();
    return () => {
      engineRef.current = null;
      engine.destroy();
    };
  }, []);

  const { surface } = useDesk.getState();
  const editingIdx = scene.objects.findIndex((o) => o.id === editingId);
  const editingObj =
    editingIdx >= 0 ? objectByRef(items, scene.objects[editingIdx].key) : null;
  const editorU =
    editingObj && editingId
      ? objUnit(
          editingObj,
          editingIdx,
          scene.objects.length,
          editorPos ? { [editingId]: editorPos } : {},
        )
      : null;
  const pullout = pulloutId ? objectByRef(items, pulloutId) : null;
  const renameZone =
    scene.zones.find((z) => z.id === renamingZoneId) || null;

  return (
    <div
      ref={hostRef}
      className={"desk-world" + (divedZone ? " dived" : "")}
      style={{ "--rows": scene.rows } as React.CSSProperties}
    >
      <canvas ref={canvasRef} className="desk-world-canvas" />
      {divedZone && (
        <button
          type="button"
          className="desk-chip desk-surface"
          onClick={surface}
        >
          ← All
        </button>
      )}
      {scene.overflow && (
        <div className="desk-chip desk-scale-chip" role="status">
          Showing {scene.overflow.shown} of {scene.overflow.total}. Search or
          use List view for everything.
        </div>
      )}
      {renameZone && (
        <ZoneRenameOverlay
          key={renameZone.id}
          zoneId={renameZone.id}
          title={renameZone.title}
          x={renameZone.u.x}
          y={renameZone.u.y}
          width={renameZone.width}
        />
      )}
      {editingObj && editorU && (
        <InlineEditor key={editingObj.id} o={editingObj} u={editorU} />
      )}
      {pullout && <Pullout key={pullout.id} o={pullout} />}
      {lasso && (
        <div
          className="desk-lasso"
          style={{
            left: lasso.left,
            top: lasso.top,
            width: lasso.w,
            height: lasso.h,
          }}
        />
      )}
      <AskBar />
      {askOpen && <AskPanel />}
      <div className="desk-world-a11y">
        {scene.zones.map((z) => (
          <button
            key={`zone:${z.id}`}
            type="button"
            data-zone-id={z.id}
            aria-label={`${z.title} zone, ${z.count} ${z.count === 1 ? "item" : "items"}`}
            onClick={() => useDesk.getState().diveInto(z.id)}
          >
            {z.title}
          </button>
        ))}
        {scene.objects.map((o) => (
          <button
            key={o.key}
            type="button"
            data-obj-id={o.selectionRef}
            data-kind={o.kind}
            aria-label={
              o.attention
                ? `${o.title}, ${o.attention} need attention`
                : o.title
            }
            onClick={(e) => {
              if (e.shiftKey || e.metaKey || e.ctrlKey) {
                useDesk.getState().toggleSelected(o.selectionRef);
                return;
              }
              useDesk.getState().openPullout(o.id);
            }}
          >
            {o.title}
          </button>
        ))}
      </div>
    </div>
  );
}

/** The rename row (input + speak-to-fill mic), DOM-anchored over the GL
 * zone through the shared unit-space transform. */
function ZoneRenameOverlay({
  zoneId,
  title,
  x,
  y,
  width,
}: {
  zoneId: string;
  title: string;
  x: number;
  y: number;
  width: number;
}) {
  const [name, setName] = useState(title);
  const { renameZone, setRenamingZone } = useDesk.getState();
  const commit = () => {
    setRenamingZone(null);
    const clean = name.trim();
    if (clean && clean !== title) void renameZone(zoneId, clean);
  };
  const cancel = () => {
    setRenamingZone(null);
  };
  return (
    <span
      className="desk-zone-rename-row is-overlay"
      style={{
        left: `${(x * 100).toFixed(2)}%`,
        top: `${(y * 100).toFixed(2)}%`,
        width,
      }}
      onPointerDown={(e) => e.stopPropagation()}
    >
      <input
        className="desk-zone-rename"
        value={name}
        autoFocus
        onChange={(e) => setName(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") cancel();
        }}
      />
      <MicButton
        draftScope={`zone-rename:${zoneId}`}
        onText={(t) => setName(t)}
      />
    </span>
  );
}

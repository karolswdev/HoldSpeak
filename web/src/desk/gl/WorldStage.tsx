/** HS-95-01 — the world, GPU-rendered. One canvas draws zones, objects,
 * selection, drag, and ambient motes (see engine.ts); the DOM keeps only
 * text-first overlays above it — the rename row, the inline editor, the
 * pull-out and Ask windows, the honest chips, and a visually-hidden
 * accessibility layer that preserves the DOM world's keyboard contract
 * (Enter/Space opens an object, dives a zone). */
import { useEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../store";
import { useProjections } from "../projections";
import { objectByRef, objUnit, type WorldObject } from "../world";
import { InlineEditor } from "../components/InlineEditor";
import { Pullout } from "../components/Pullout";
import { AskBar, AskPanel } from "../components/AskPanel";
import { MicButton } from "../components/MicButton";
import { DeskMenuItem, DeskMenuList } from "../components/DeskMenu";
import { WorldEngine, type WorldMenuTarget } from "./engine";
import { buildScene, type WorldScene } from "./sceneModel";

/** Kinds whose material can be edited (mirrors the Pullout's set). */
const WORLD_EDITABLE = new Set(["note", "kb", "recipe", "workflow"]);

export { MAX_FLOATERS } from "./sceneModel";

export function WorldStage() {
  // Fine-grained subscriptions on purpose: a drag writes `positions` on
  // every pointer move, and this component must NOT re-render for that —
  // per-frame world motion is the engine's, on the GPU. React re-renders
  // only for overlay-relevant changes (open editors, renames, item churn).
  const items = useDesk((s) => s.items);
  const divedZone = useDesk((s) => s.divedZone);
  const editingId = useDesk((s) => s.editingId);
  const pullouts = useDesk((s) => s.pullouts);
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
  // §6.3 — right-click is universal: the world's objects and zones
  // answer with the ONE menu vocabulary.
  const [worldMenu, setWorldMenu] = useState<{
    target: WorldMenuTarget;
    x: number;
    y: number;
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
      onContextMenu: (target, x, y) => setWorldMenu({ target, x, y }),
    });
    engineRef.current = engine;
    void engine.init();
    return () => {
      engineRef.current = null;
      engine.destroy();
    };
  }, []);

  // Escape on the desk (no window focused — focused windows own their
  // own Escape and stop it) closes the FRONT-MOST object card. Capture
  // phase so an open in-world editor keeps its Escape to itself.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape" || e.defaultPrevented) return;
      // A focused window (or field) owns its own Escape.
      const t = e.target as HTMLElement | null;
      if (t?.closest?.(".desk-window-shell, .desk-editor, input, textarea"))
        return;
      const s = useDesk.getState();
      if (s.editingId || s.renamingZoneId || s.askOpen) return;
      if (s.pullouts.length) s.closePullout();
    };
    document.addEventListener("keydown", onKey, true);
    return () => document.removeEventListener("keydown", onKey, true);
  }, []);

  // The world menu dismisses like every desk menu: outside press, Escape.
  useEffect(() => {
    if (!worldMenu) return;
    const close = () => setWorldMenu(null);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close();
      }
    };
    window.addEventListener("pointerdown", close);
    window.addEventListener("keydown", onKey, true);
    return () => {
      window.removeEventListener("pointerdown", close);
      window.removeEventListener("keydown", onKey, true);
    };
  }, [worldMenu]);

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
  const openCards = pullouts
    .map((p) => ({ ...p, obj: objectByRef(items, p.id) }))
    .filter((p): p is typeof p & { obj: WorldObject } => Boolean(p.obj));
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
      {openCards.map((p) => (
        <Pullout key={p.id} o={p.obj} origin={p.origin} />
      ))}
      {worldMenu && (
        <DeskMenuList
          className="desk-world-menu"
          label={
            worldMenu.target.type === "object"
              ? `${worldMenu.target.title} menu`
              : `${worldMenu.target.title} zone menu`
          }
          anchor="below"
          style={{
            position: "fixed",
            left: Math.min(worldMenu.x, window.innerWidth - 184),
            top: Math.min(worldMenu.y, window.innerHeight - 132),
          }}
          onClose={() => setWorldMenu(null)}
        >
          {worldMenu.target.type === "object" ? (
            <>
              <DeskMenuItem
                onSelect={() => {
                  const t = worldMenu.target as Extract<
                    WorldMenuTarget,
                    { type: "object" }
                  >;
                  setWorldMenu(null);
                  useDesk
                    .getState()
                    .openPullout(t.id, { x: worldMenu.x, y: worldMenu.y });
                }}
              >
                Open
              </DeskMenuItem>
              {WORLD_EDITABLE.has(worldMenu.target.kind) && (
                <DeskMenuItem
                  onSelect={() => {
                    const t = worldMenu.target as Extract<
                      WorldMenuTarget,
                      { type: "object" }
                    >;
                    setWorldMenu(null);
                    useDesk.getState().openEditor(t.id);
                  }}
                >
                  Edit
                </DeskMenuItem>
              )}
            </>
          ) : (
            <>
              <DeskMenuItem
                onSelect={() => {
                  const t = worldMenu.target;
                  setWorldMenu(null);
                  useDesk.getState().diveInto(t.id);
                }}
              >
                Open
              </DeskMenuItem>
              <DeskMenuItem
                onSelect={() => {
                  const t = worldMenu.target;
                  setWorldMenu(null);
                  useDesk.getState().setRenamingZone(t.id);
                }}
              >
                Rename
              </DeskMenuItem>
            </>
          )}
        </DeskMenuList>
      )}
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

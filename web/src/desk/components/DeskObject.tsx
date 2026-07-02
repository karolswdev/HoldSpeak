// One floating pixel-art object (HS-71-03/04 parity): sprite + per-kind glow
// pool + detached ground shadow + CSS float with a per-object phase, and the
// pointer drag (fresh world rect per move, unit-space clamp, >4px tap/drag
// threshold — HS-71-04's exact semantics via @use-gesture).
import { useDrag } from "@use-gesture/react";
// @ts-ignore — shared ESM module (see sprites.d.ts); the SAME picker the
// legacy desk uses, for exact per-id sprite parity.
import { spriteUrl } from "../../scripts/desk/sprites.js";
import { objGlow, objMotion, objUnit, type WorldObject } from "../world";
import { useDesk } from "../store";

const EDITABLE = new Set(["note", "kb", "agent"]);

export function DeskObject({
  o, i, n,
}: {
  o: WorldObject;
  i: number;
  n: number;
}) {
  const positions = useDesk((s) => s.positions);
  const draggingId = useDesk((s) => s.draggingId);
  const newIds = useDesk((s) => s.newIds);
  const editingId = useDesk((s) => s.editingId);
  const { setPosition, persistPositions, setDragging, openEditor } = useDesk.getState();

  const u = objUnit(o, i, n, positions);
  const m = objMotion(o);
  const dragging = draggingId === o.id;
  const isNew = newIds.includes(o.id);
  const editing = editingId === o.id;

  const onClick = () => {
    // A completed drag never opens (the HS-71-06 discrimination: the drag
    // state clears next-tick, so a real drag still reads as dragging here).
    if (useDesk.getState().draggingId === o.id) return;
    if (EDITABLE.has(o.kind)) openEditor(o.id);
  };

  const bind = useDrag(
    ({ event, first, last, movement: [mx, my], memo }) => {
      const el = event?.target as HTMLElement | null;
      const world = memo?.world ?? el?.closest(".desk-world");
      if (!world) return memo;
      const moved = memo?.moved || Math.abs(mx) + Math.abs(my) > 4;
      if (first) setDragging(o.id);
      if (moved && event && "clientX" in event) {
        // A FRESH world rect each move, so a mid-drag layout shift can't
        // desync the position (the HS-71-05 robustness fix).
        const r = (world as HTMLElement).getBoundingClientRect();
        setPosition(o.id, {
          x: Math.min(0.96, Math.max(0.04, ((event as PointerEvent).clientX - r.left) / r.width)),
          y: Math.min(0.96, Math.max(0.04, ((event as PointerEvent).clientY - r.top) / r.height)),
        });
      }
      if (last) {
        if (moved) {
          persistPositions();
          // Cleared next tick: the click event fires first and reads the
          // still-set drag state (a real drag never opens — HS-71-06).
          setTimeout(() => setDragging(null), 0);
        } else {
          // A plain tap: clear NOW so the click opens the editor.
          setDragging(null);
        }
      }
      return { world, moved };
    },
    { pointer: { buttons: 1 } },
  );

  return (
    <div
      {...bind()}
      onClick={onClick}
      className={
        "desk-obj" +
        (dragging ? " dragging" : "") +
        (isNew ? " is-new materialize" : "") +
        (editing ? " editing" : "")
      }
      title={o.title}
      style={
        {
          left: `${(u.x * 100).toFixed(2)}%`,
          top: `${(u.y * 100).toFixed(2)}%`,
          "--phase": `${m.phase.toFixed(2)}s`,
          "--tilt": `${m.tilt.toFixed(2)}deg`,
          "--oscale": m.scale.toFixed(3),
          "--k": objGlow(o.kind),
        } as React.CSSProperties
      }
    >
      <div className="desk-obj-shadow" aria-hidden="true" />
      <div className="desk-obj-lift">
        <div className="desk-obj-glow" aria-hidden="true" />
        <div className="desk-obj-ring" aria-hidden="true" />
        {isNew && <span className="desk-obj-new">NEW</span>}
        <img
          className="desk-obj-sprite"
          src={spriteUrl(o.kind, o.id)}
          alt={o.kind}
          draggable={false}
        />
      </div>
      <div className="desk-obj-label">{o.title}</div>
    </div>
  );
}

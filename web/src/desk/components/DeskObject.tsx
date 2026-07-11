// One floating pixel-art object (HS-71-03/04 parity): sprite + per-kind glow
// pool + detached ground shadow + CSS float with a per-object phase, and the
// pointer drag (fresh world rect per move, unit-space clamp, >4px tap/drag
// threshold — HS-71-04's exact semantics via @use-gesture).
import { useDrag } from "@use-gesture/react";
// @ts-ignore — shared ESM module (see sprites.d.ts); the SAME picker the
// legacy desk uses, for exact per-id sprite parity.
import { spriteUrl } from "../sprites";
import { objGlow, objMotion, objUnit, type WorldObject } from "../world";
import { useDesk } from "../store";

export function DeskObject({
  o,
  i,
  n,
}: {
  o: WorldObject;
  i: number;
  n: number;
}) {
  const positions = useDesk((s) => s.positions);
  const draggingId = useDesk((s) => s.draggingId);
  const newIds = useDesk((s) => s.newIds);
  const editingId = useDesk((s) => s.editingId);
  const selectedIds = useDesk((s) => s.selectedIds);
  const {
    setPosition,
    persistPositions,
    setDragging,
    openPullout,
    setHoverZone,
    fileIntoDir,
    toggleSelected,
  } = useDesk.getState();

  const u = objUnit(o, i, n, positions);
  const m = objMotion(o);
  const dragging = draggingId === o.id;
  const isNew = newIds.includes(o.id);
  const editing = editingId === o.id;
  const selected = selectedIds.includes(o.id);

  const onClick = (e: React.MouseEvent) => {
    // A completed drag never opens (the HS-71-06 discrimination: the drag
    // state clears next-tick, so a real drag still reads as dragging here).
    if (useDesk.getState().draggingId === o.id) return;
    // Shift/cmd-click ropes the object into the Ask context (HSM-16-04) —
    // the pointer's word for the lasso's single-object case.
    if (e.shiftKey || e.metaKey || e.ctrlKey) {
      toggleSelected(o.id);
      return;
    }
    openPullout(o.id);
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
        const px = (event as PointerEvent).clientX;
        const py = (event as PointerEvent).clientY;
        const r = (world as HTMLElement).getBoundingClientRect();
        setPosition(o.id, {
          x: Math.min(0.96, Math.max(0.04, (px - r.left) / r.width)),
          y: Math.min(0.96, Math.max(0.04, (py - r.top) / r.height)),
        });
        // The drop affordance: hit-test FRESH zone rects each move.
        const zone = document
          .elementFromPoint(px, py)
          ?.closest<HTMLElement>(".desk-zone");
        const over = zone?.dataset.zoneId || null;
        setHoverZone(over);
      }
      if (last) {
        if (moved) {
          // Dropped onto a zone? File it there (the real PUT) and forget
          // the free position — the object lives on the shelf now.
          const over = useDesk.getState().hoverZoneId;
          setHoverZone(null);
          if (over) {
            void fileIntoDir(o.id, over);
          } else {
            persistPositions();
          }
          // Cleared next tick: the click event fires first and reads the
          // still-set drag state (a real drag never opens — HS-71-06).
          setTimeout(() => setDragging(null), 0);
        } else {
          setHoverZone(null);
          // A plain tap: clear NOW so the click opens the pull-out.
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
      data-obj-id={o.id}
      className={
        "desk-obj" +
        (dragging ? " dragging" : "") +
        (isNew ? " is-new materialize" : "") +
        (editing ? " editing" : "") +
        (selected ? " selected" : "")
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

// The world: every primitive as a floating object + the zone trays, laid out
// by the ported looseHome math (HS-71-03/05 parity). The empty desk is also
// the lasso surface (HSM-16-04): drag on the background to rope objects into
// the Ask atom's context.
import { useRef, useState } from "react";
import { useDesk } from "../store";
import {
  allObjects,
  objGlow,
  objUnit,
  worldObjects,
  worldRows,
  worldZones,
} from "../world";
import { DeskObject } from "./DeskObject";
import { InlineEditor } from "./InlineEditor";
import { Pullout } from "./Pullout";
import { AskBar, AskPanel } from "./AskPanel";
import { MicButton } from "./MicButton";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteUrl, variantIndex } from "../sprites";
import { resolveRef } from "../lineage";

// Per-zone stable tints (variantIndex over the id keeps a zone's color
// forever — the same stable-hash family the sprite picker uses).
const ZONE_TINTS = [
  "#E0A458",
  "#56C7F5",
  "#34D399",
  "#A78BFA",
  "#FF9E64",
  "#FBBF24",
];

export function World() {
  const items = useDesk((s) => s.items);
  const divedZone = useDesk((s) => s.divedZone);
  const positions = useDesk((s) => s.positions);
  const editingId = useDesk((s) => s.editingId);
  const objects = worldObjects(items, divedZone);
  const zones = worldZones(items, divedZone);
  const editingIdx = objects.findIndex((o) => o.id === editingId);
  const editing = editingIdx >= 0 ? objects[editingIdx] : null;
  const pulloutId = useDesk((s) => s.pulloutId);
  const pullout = pulloutId
    ? allObjects(items).find((x) => x.id === pulloutId) || null
    : null;
  const askOpen = useDesk((s) => s.askOpen);

  // The lasso (HSM-16-09's gesture on pointer metal): press the empty desk,
  // drag a rope, release — everything inside is the ask's context. A bare
  // background click (no rope) clears the selection.
  const [lasso, setLasso] = useState<{
    x0: number;
    y0: number;
    x1: number;
    y1: number;
  } | null>(null);
  const lassoRef = useRef<typeof lasso>(null);
  const worldRef = useRef<HTMLDivElement | null>(null);

  const onLassoDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.target !== e.currentTarget || e.button !== 0) return;
    const next = { x0: e.clientX, y0: e.clientY, x1: e.clientX, y1: e.clientY };
    lassoRef.current = next;
    setLasso(next);
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onLassoMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!lassoRef.current) return;
    const next = { ...lassoRef.current, x1: e.clientX, y1: e.clientY };
    lassoRef.current = next;
    setLasso(next);
  };
  const onLassoUp = () => {
    const l = lassoRef.current;
    lassoRef.current = null;
    setLasso(null);
    if (!l) return;
    const left = Math.min(l.x0, l.x1);
    const right = Math.max(l.x0, l.x1);
    const top = Math.min(l.y0, l.y1);
    const bottom = Math.max(l.y0, l.y1);
    const { setSelected, clearSelection } = useDesk.getState();
    if (right - left < 8 && bottom - top < 8) {
      // A bare tap on the desk: the selection settles.
      clearSelection();
      return;
    }
    const roped: string[] = [];
    worldRef.current
      ?.querySelectorAll<HTMLElement>(".desk-obj")
      .forEach((el) => {
        const r = el.getBoundingClientRect();
        const cx = r.left + r.width / 2;
        const cy = r.top + r.height / 2;
        if (cx >= left && cx <= right && cy >= top && cy <= bottom) {
          const id = el.dataset.objId;
          if (id) roped.push(id);
        }
      });
    if (roped.length) setSelected(roped);
  };

  const { surface } = useDesk.getState();
  return (
    <div
      ref={worldRef}
      className={"desk-world" + (divedZone ? " dived" : "")}
      style={{ "--rows": worldRows(objects.length) } as React.CSSProperties}
      onPointerDown={onLassoDown}
      onPointerMove={onLassoMove}
      onPointerUp={onLassoUp}
      onPointerCancel={onLassoUp}
    >
      {divedZone && (
        <button
          type="button"
          className="desk-chip desk-surface"
          onClick={surface}
        >
          ← All
        </button>
      )}
      {zones.map((z, i) => {
        const cols = Math.max(1, Math.min(4, zones.length));
        const wPct = Math.min(30, 84 / cols);
        return (
          <ZoneTray
            key={z.id}
            z={z}
            style={
              {
                left: `${((((i % cols) + 0.5) / cols) * 100).toFixed(2)}%`,
                top: "12%",
                width: `${wPct}%`,
                "--zk": objGlow("directory"),
              } as React.CSSProperties
            }
          />
        );
      })}
      {objects.map((o, i) => (
        <DeskObject key={`${o.kind}:${o.id}`} o={o} i={i} n={objects.length} />
      ))}
      {editing && (
        <InlineEditor
          key={editing.id}
          o={editing}
          u={objUnit(editing, editingIdx, objects.length, positions)}
        />
      )}
      {pullout && <Pullout key={pullout.id} o={pullout} />}
      {lasso && (
        <div
          className="desk-lasso"
          style={{
            left:
              Math.min(lasso.x0, lasso.x1) -
              (worldRef.current?.getBoundingClientRect().left || 0),
            top:
              Math.min(lasso.y0, lasso.y1) -
              (worldRef.current?.getBoundingClientRect().top || 0),
            width: Math.abs(lasso.x1 - lasso.x0),
            height: Math.abs(lasso.y1 - lasso.y0),
          }}
        />
      )}
      <AskBar />
      {askOpen && <AskPanel />}
    </div>
  );
}

/** A landmark zone tray (HS-73-05): stable tint, member mini-sprites,
 * drop affordance, dive on click, rename-in-place, an empty hint. */
function ZoneTray({
  z,
  style,
}: {
  z: ReturnType<typeof worldZones>[number];
  style: React.CSSProperties;
}) {
  const items = useDesk((s) => s.items);
  const hoverZoneId = useDesk((s) => s.hoverZoneId);
  const renamingZoneId = useDesk((s) => s.renamingZoneId);
  const { renameZone, diveInto, setRenamingZone } = useDesk.getState();
  const [renaming, setRenaming] = useState(false);
  const [name, setName] = useState(z.title);
  const focusRename = renamingZoneId === z.id;
  const memberIds = ((z.ref as any).memberIds as string[]) || [];
  const thumbs = memberIds.slice(0, 4).map((mid) => {
    const r = resolveRef(items, mid);
    return { id: mid, kind: r.kind || "note" };
  });
  const commit = () => {
    setRenaming(false);
    setRenamingZone(null);
    const clean = name.trim();
    if (clean && clean !== z.title) void renameZone(z.id, clean);
  };
  const tint = ZONE_TINTS[variantIndex(z.id, ZONE_TINTS.length)];
  return (
    <div
      className={"desk-zone" + (hoverZoneId === z.id ? " drop-ready" : "")}
      data-zone-id={z.id}
      role="button"
      tabIndex={0}
      aria-label={`${z.title} zone, ${memberIds.length} ${memberIds.length === 1 ? "item" : "items"}`}
      style={{ ...style, "--zk": tint } as React.CSSProperties}
      onClick={() => {
        if (!renaming && !focusRename) diveInto(z.id);
      }}
      onKeyDown={(event) => {
        if (event.currentTarget !== event.target) return;
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          if (!renaming && !focusRename) diveInto(z.id);
        }
      }}
    >
      {renaming || focusRename ? (
        <span
          className="desk-zone-rename-row"
          onClick={(e) => e.stopPropagation()}
        >
          <input
            className="desk-zone-rename"
            value={focusRename && !renaming ? z.title : name}
            autoFocus
            onFocus={() => {
              setName(z.title);
              setRenaming(true);
            }}
            onChange={(e) => setName(e.target.value)}
            onBlur={commit}
            onKeyDown={(e) => {
              if (e.key === "Enter") commit();
              if (e.key === "Escape") {
                setName(z.title);
                setRenaming(false);
                setRenamingZone(null);
              }
            }}
          />
          <MicButton onText={(t) => setName(t)} />
        </span>
      ) : (
        <span
          className="desk-zone-title"
          onClick={(e) => {
            e.stopPropagation();
            setName(z.title);
            setRenaming(true);
          }}
        >
          {z.title}
        </span>
      )}
      {thumbs.length > 0 ? (
        <span className="desk-zone-thumbs">
          {thumbs.map((t) => (
            <img
              key={t.id}
              src={spriteUrl(t.kind, t.id)}
              alt=""
              width={22}
              height={22}
            />
          ))}
          {memberIds.length > 4 && (
            <span className="desk-zone-more">+{memberIds.length - 4}</span>
          )}
          <span className="desk-zone-count">
            {memberIds.length === 1 ? "1 item" : `${memberIds.length} items`}
          </span>
        </span>
      ) : (
        <span className="desk-zone-count">drop things here</span>
      )}
    </div>
  );
}

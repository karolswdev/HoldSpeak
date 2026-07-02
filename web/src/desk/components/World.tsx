// The world: every primitive as a floating object + the zone trays, laid out
// by the ported looseHome math (HS-71-03/05 parity).
import { useState } from "react";
import { useDesk } from "../store";
import {
  objGlow, objUnit, worldObjects, worldRows, worldZones,
} from "../world";
import { DeskObject } from "./DeskObject";
import { InlineEditor } from "./InlineEditor";

export function World() {
  const items = useDesk((s) => s.items);
  const divedZone = useDesk((s) => s.divedZone);
  const positions = useDesk((s) => s.positions);
  const editingId = useDesk((s) => s.editingId);
  const objects = worldObjects(items, divedZone);
  const zones = worldZones(items, divedZone);
  const editingIdx = objects.findIndex((o) => o.id === editingId);
  const editing = editingIdx >= 0 ? objects[editingIdx] : null;

  return (
    <div
      className="desk-world"
      style={{ "--rows": worldRows(objects.length) } as React.CSSProperties}
    >
      {zones.map((z, i) => {
        const cols = Math.max(1, Math.min(4, zones.length));
        const wPct = Math.min(30, 84 / cols);
        return (
          <ZoneTray key={z.id} z={z} style={{
            left: `${((((i % cols) + 0.5) / cols) * 100).toFixed(2)}%`,
            top: "12%",
            width: `${wPct}%`,
            "--zk": objGlow("directory"),
          } as React.CSSProperties} />
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
    </div>
  );
}


/** A zone tray with rename-in-place (HS-73-03; HS-73-05 makes it a landmark). */
function ZoneTray({ z, style }: { z: ReturnType<typeof worldZones>[number]; style: React.CSSProperties }) {
  const { renameZone } = useDesk.getState();
  const [renaming, setRenaming] = useState(false);
  const [name, setName] = useState(z.title);
  const commit = () => {
    setRenaming(false);
    const clean = name.trim();
    if (clean && clean !== z.title) void renameZone(z.id, clean);
  };
  return (
    <div className="desk-zone" data-zone-id={z.id} style={style}>
      {renaming ? (
        <input
          className="desk-zone-rename"
          value={name}
          autoFocus
          onChange={(e) => setName(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit();
            if (e.key === "Escape") { setName(z.title); setRenaming(false); }
          }}
        />
      ) : (
        <span
          className="desk-zone-title"
          onClick={() => { setName(z.title); setRenaming(true); }}
        >
          {z.title}
        </span>
      )}
      <span className="desk-zone-count">
        {z.count === 1 ? "1 item" : `${z.count} items`}
      </span>
    </div>
  );
}
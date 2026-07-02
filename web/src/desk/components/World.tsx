// The world: every primitive as a floating object + the zone trays, laid out
// by the ported looseHome math (HS-71-03/05 parity).
import { useDesk } from "../store";
import {
  objGlow, worldObjects, worldRows, worldZones,
} from "../world";
import { DeskObject } from "./DeskObject";

export function World() {
  const items = useDesk((s) => s.items);
  const divedZone = useDesk((s) => s.divedZone);
  const objects = worldObjects(items, divedZone);
  const zones = worldZones(items, divedZone);

  return (
    <div
      className="desk-world"
      style={{ "--rows": worldRows(objects.length) } as React.CSSProperties}
    >
      {zones.map((z, i) => {
        const cols = Math.max(1, Math.min(4, zones.length));
        const wPct = Math.min(30, 84 / cols);
        return (
          <div
            key={z.id}
            className="desk-zone"
            data-zone-id={z.id}
            style={
              {
                left: `${((((i % cols) + 0.5) / cols) * 100).toFixed(2)}%`,
                top: "12%",
                width: `${wPct}%`,
                "--zk": objGlow("directory"),
              } as React.CSSProperties
            }
          >
            <span className="desk-zone-title">{z.title}</span>
            <span className="desk-zone-count">
              {z.count === 1 ? "1 item" : `${z.count} items`}
            </span>
          </div>
        );
      })}
      {objects.map((o, i) => (
        <DeskObject key={`${o.kind}:${o.id}`} o={o} i={i} n={objects.length} />
      ))}
    </div>
  );
}

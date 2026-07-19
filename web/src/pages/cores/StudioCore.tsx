// HS-95-08 — the Studio core: the power-tool launcher as a shell
// dispatcher (every row opens a desk window; nothing navigates).
// HS-98-06 — re-crafted native: launcher rows on the surface material.
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
} from "../../desk/surface/Surface";

const TOOLS: Array<[string, string, string, string]> = [
  ["build-workflow", "/workbench", "Workflow editor", "Build or edit a Workflow."],
  [
    "inspect-personas-and-coders",
    "/companion",
    "Personas and coders",
    "Review Personas and waiting Coder sessions.",
  ],
  ["configure-cadence", "/cadence", "Cadence", "Configure scheduled background work."],
  [
    "configure-commands",
    "/commands",
    "Commands",
    "Map spoken phrases to registered actions.",
  ],
  [
    "configure-runs-on",
    "/profiles",
    "Runs on",
    "Configure model and runtime destinations.",
  ],
  [
    "inspect-activity",
    "/activity",
    "Activity",
    "Inspect work context, sources, rules, and records.",
  ],
];

export function StudioCore({ hero }: CoreProps) {
  return (
    <>
      {hero ? hero(null) : null}
      <SurfaceSection label="Power tools">
        <SurfaceRows>
          {TOOLS.map(([action, href, name, what]) => (
            <SurfaceRow
              key={action}
              glyph="◇"
              title={name}
              detail={what}
              meta="→"
              onOpen={() => openSurfaceOr(action, href)}
            />
          ))}
        </SurfaceRows>
      </SurfaceSection>
    </>
  );
}

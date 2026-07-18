// HS-95-08 — the Studio core: the power-tool launcher as a shell
// dispatcher (every card opens a desk window; nothing navigates).
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";

const TOOLS: Array<[string, string, string, string, string]> = [
  ["build-workflow", "/workbench", "Workflow editor", "Build or edit a Workflow.", "Configure →"],
  [
    "inspect-personas-and-coders",
    "/companion",
    "Personas and coders",
    "Review Personas and waiting Coder sessions.",
    "Open →",
  ],
  ["configure-cadence", "/cadence", "Cadence", "Configure scheduled background work.", "Configure →"],
  [
    "configure-commands",
    "/commands",
    "Commands",
    "Map spoken phrases to registered actions.",
    "Configure →",
  ],
  [
    "configure-runs-on",
    "/profiles",
    "Runs on",
    "Configure model and runtime destinations.",
    "Configure →",
  ],
  [
    "inspect-activity",
    "/activity",
    "Activity",
    "Inspect work context, sources, rules, and records.",
    "Open →",
  ],
];

export function StudioCore({ hero }: CoreProps) {
  return (
    <>
      {hero ? hero(null) : null}
      <div className="studio-grid">
        {TOOLS.map(([action, href, name, what, verb]) => (
          <button
            type="button"
            className="studio-card"
            onClick={() => openSurfaceOr(action, href)}
            key={action}
          >
            <span aria-hidden="true">◇</span>
            <strong>{name}</strong>
            <p>{what}</p>
            <b>{verb}</b>
          </button>
        ))}
      </div>
    </>
  );
}

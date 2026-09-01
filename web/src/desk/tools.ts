/** The Go shelf is a projection of the DeskOS application manifest. */
import { DESK_APPLICATIONS } from "./applications";

export const DESK_TOOLS = DESK_APPLICATIONS.filter(
  (application) => application.group === "app" || application.group === "tool",
)
  .sort((left, right) => {
    if (left.group === right.group) return 0;
    return left.group === "app" ? -1 : 1;
  })
  .map((application) => ({
  href: application.href,
  label: application.toolLabel ?? application.label,
  description: application.description,
  glyph: application.toolGlyph ?? application.glyph,
  action: application.action,
  group: application.group as "app" | "tool",
  subjectRef: application.subjectRef,
  windowId: application.windowId,
  shortcut: application.shortcut,
  }));

/** HS-148-02: unicode kind glyphs for the seven create nouns —
 * geometric/dingbat family matching the DESK_TOOLS deck aesthetic.
 * One glyph per kind, shared by menus, the create face, and the palette. */
export const KIND_GLYPH: Record<string, string> = {
  note: "▤",       // horizontal rules — a written page
  decision: "◈",   // diamond with inner — a weighed gem
  kb: "⬡",         // hexagon — a knowledge cell
  recipe: "◎",     // bullseye — a targeted agent
  workflow: "⟁",   // triangle with dots — a flow graph
  workbench: "⊞",  // boxed plus — a compound workspace
  zone: "◰",       // square with upper-left quadrant — a region
  thread: "◬",     // triangle with left half — a speech ribbon
  project: "▣",    // filled square — a durable container
};

export const KIND_LABEL: Record<string, string> = {
  artifact: "Artifact",
  chain: "Workflow",
  coder: "Coder session",
  kb: "Knowledge",
  meeting: "Meeting",
  note: "Note",
  project: "Project",
  recipe: "Agent",
  workbench: "Workbench",
  workflow: "Workflow",
  thread: "Thread",
};

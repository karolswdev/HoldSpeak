/** HS-111-07 - the program table (data only, a leaf module). The verbs
 * that launch these live in verbRegistry (`go.*`); the palette and the
 * Go menu both derive from that one registry. Moved out of
 * DeskToolShelf so the registry never imports a component. */

export const DESK_TOOLS = [
  // HS-100-11 - the search palette reaches the four applications too.
  // HS-148-02: group "app" = keycapped primary apps; "tool" = config/inspect.
  {
    href: "/dictation",
    label: "Speak",
    description: "Voice typing: speak, see it land, teach it.",
    glyph: "⌁",
    action: "dictate",
    group: "app",
    subjectRef: undefined,
  },
  {
    href: "/ask",
    label: "Ask AI",
    description: "Ask across the work on your desk.",
    glyph: "✦",
    action: "ask",
    group: "app",
    subjectRef: undefined,
  },
  {
    href: "/history",
    label: "Meetings",
    description: "Outcomes, recordings, and the typed record.",
    glyph: "▣",
    action: "review-meetings",
    group: "app",
    subjectRef: undefined,
  },
  {
    href: "/settings",
    label: "Settings",
    description: "Every boundary, stated once.",
    glyph: "⚙",
    action: "configure-settings",
    group: "app",
    subjectRef: undefined,
  },
  {
    href: "/workbenches",
    label: "Workbenches",
    description: "Mission control for your agent workbenches.",
    glyph: "⚒",
    action: "open-workbenches",
    group: "tool",
    subjectRef: undefined,
  },
  {
    href: "/companion",
    label: "Agents and coder sessions",
    description: "Use saved behavior and inspect live sessions.",
    glyph: "◉",
    action: "inspect-personas-and-coders",
    group: "tool",
    subjectRef: undefined,
  },
  {
    href: "/profiles",
    label: "Runs on",
    description: "Configure model and runtime destinations.",
    glyph: "▣",
    action: "configure-runs-on",
    group: "tool",
    subjectRef: undefined,
  },
  {
    href: "/settings",
    label: "Integrations",
    description: "Configure connected destinations and credentials.",
    glyph: "↗",
    action: "configure-integrations",
    group: "tool",
    subjectRef: "integration:destinations",
  },
  {
    href: "/commands",
    label: "Commands",
    description: "Map spoken phrases to registered actions.",
    glyph: "⌘",
    action: "configure-commands",
    group: "tool",
    subjectRef: undefined,
  },
  {
    href: "/cadence",
    label: "Cadence",
    description: "Configure scheduled background work.",
    glyph: "◷",
    action: "configure-cadence",
    group: "tool",
    subjectRef: undefined,
  },
  {
    href: "/context",
    label: "Context",
    description: "The always-on briefing every agent receives.",
    glyph: "§",
    action: "open-constitutional-context",
    group: "tool",
    subjectRef: undefined,
  },
  {
    href: "/activity",
    label: "Activity",
    description: "Inspect work context and source records.",
    glyph: "≋",
    action: "inspect-activity",
    group: "tool",
    subjectRef: undefined,
  },
  {
    href: "/#processes",
    label: "Processes",
    description: "See what the kernel is running.",
    glyph: "∷",
    action: "inspect-processes",
    group: "tool",
    subjectRef: undefined,
  },
] as const;

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
};

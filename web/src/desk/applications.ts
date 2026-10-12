import type { ComponentType } from "react";
import type { CoreProps } from "../pages/cores/core-types";

/**
 * The DeskOS application manifest.
 *
 * Application identity belongs here. Window hosts, the Dock, Go commands,
 * keyboard bindings, aliases, and the mark menu are projections of this
 * table; they must not grow parallel application lists.
 */
export interface DeskSurfaceSpec {
  eyebrow: string;
  minW?: number;
  /** Preferred first-open width (PHILO-17 U24); the band still clamps it. */
  defaultW?: number;
  defaultH?: number;
  maximized?: boolean;
  load: () => Promise<{
    default: ComponentType<CoreProps & { scope?: string }>;
  }>;
}

export interface DeskApplicationAlias {
  key: string;
  scope?: string;
}

export interface DeskApplication {
  action: string;
  windowId: string;
  label: string;
  description: string;
  glyph: string;
  href: string;
  group?: "app" | "tool";
  subjectRef?: string;
  surface?: DeskSurfaceSpec;
  aliases?: readonly DeskApplicationAlias[];
  dock?: { order: number; launch: "surface" | "intelligence" };
  /** PHILO-17 (doors): the row in the menu bar's Go. `app` rows lead Go in
   * `order`; `tools` rows ride Go ▸ Tools. No `go`: not in Go (the palette
   * still finds a grouped application). */
  go?: { order: number; section: "app" | "tools" };
  shortcut?: string;
  /** PHILO-17 (doors): the row in the HoldSpeak menu, in this order. */
  mark?: number;
  toolLabel?: string;
  toolGlyph?: string;
}

export type SurfaceApplication = DeskApplication & {
  surface: DeskSurfaceSpec;
};

export const DESK_APPLICATIONS: readonly DeskApplication[] = [
  {
    action: "change-places",
    windowId: "surface-places",
    label: "Change places",
    description: "Environments, favorites, atmosphere, wallpaper, and room sound.",
    glyph: "▧",
    href: "/",
    group: "tool",
    shortcut: "⌘⇧P",
    surface: {
      eyebrow: "Places to think",
      minW: 600,
      defaultH: 620,
      load: () => import("../pages/cores/ChangePlacesCore").then((module) => ({ default: module.ChangePlacesCore })),
    },
  },
  {
    action: "open-intelligence",
    windowId: "intelligence:desk",
    label: "Today",
    description: "Briefs, follow-through, receipts, and reasons.",
    glyph: "◈",
    href: "/",
    dock: { order: 0, launch: "intelligence" },
    go: { order: 3, section: "app" },
  },
  {
    action: "dictate",
    windowId: "surface-dictation",
    label: "Speak",
    description: "Voice typing: speak, see it land, teach it.",
    glyph: "⌁",
    href: "/dictation",
    group: "app",
    dock: { order: 1, launch: "surface" },
    go: { order: 1, section: "app" },
    shortcut: "⌃1",
    surface: {
      eyebrow: "Daily cockpit",
      minW: 560,
      defaultH: 560,
      load: () =>
        import("../pages/cores/DictationCore").then((module) => ({
          default: module.DictationCore,
        })),
    },
  },
  {
    action: "ask",
    windowId: "ask:desk",
    label: "Ask AI",
    description: "Ask across the work on your desk.",
    glyph: "✦",
    href: "/ask",
    group: "app",
    go: { order: 4, section: "app" },
  },
  {
    action: "review-meetings",
    windowId: "surface-meetings",
    label: "Meetings",
    description: "Outcomes, recordings, and the typed record.",
    glyph: "▣",
    href: "/history",
    group: "app",
    dock: { order: 2, launch: "surface" },
    go: { order: 2, section: "app" },
    shortcut: "⌃2",
    surface: {
      eyebrow: "Meeting memory",
      minW: 640,
      // PHILO-17 (U24): the list strip, the record and the six footer verbs
      // need more than 640 x 600 (the footer took three rows).
      defaultW: 920,
      defaultH: 720,
      load: () =>
        import("../pages/cores/HistoryCore").then((module) => ({
          default: module.HistoryCore,
        })),
    },
  },
  // PHILO-14 C4: the Conductor drawer is where agents live. The Dock's
  // Agents entry became Conductor (the D1 `dock-agents` glyph is drawn as
  // the Conductor); it opens the Conductor window (conductor/), not a
  // hosted surface.
  {
    action: "open-conductor",
    windowId: "conductor",
    label: "Conductor",
    toolLabel: "Conductor",
    description: "Your coding agents: who works, who asks, what they opened.",
    glyph: "◉",
    href: "/conductor",
    group: "tool",
    // PHILO-17 (doors): the Conductor's door is its desk drawer and Go.
    go: { order: 6, section: "app" },
    shortcut: "⌃3",
  },
  // PARKED (PHILO-14 C4): the old Agents application. It folded into the
  // Conductor drawer; its route `/companion` stays alive, but it is in no
  // Dock, Go list, shortcut or mark menu. Nothing links to it.
  {
    action: "inspect-personas-and-coders",
    windowId: "surface-companion",
    label: "Agents",
    toolLabel: "Agents and coder sessions",
    description: "Use saved behavior and inspect live sessions.",
    glyph: "◉",
    href: "/companion",
    surface: {
      eyebrow: "Companion",
      minW: 560,
      load: () =>
        import("../pages/cores/CompanionCore").then((module) => ({
          default: module.CompanionCore,
        })),
    },
  },
  {
    action: "configure-settings",
    windowId: "surface-settings",
    label: "Settings",
    description: "Every boundary, stated once.",
    glyph: "⚙",
    href: "/settings",
    group: "app",
    // PHILO-17 (doors): Settings is in the HoldSpeak menu only.
    shortcut: "⌃4",
    mark: 1,
    aliases: [
      { key: "configure-integrations", scope: "integration:destinations" },
      { key: "configure-integration" },
      // PARKED (HS-170-03): configure-runs-on now opens the Concierge window directly.
      // { key: "configure-runs-on", scope: "models" },
      { key: "read-runtime-docs", scope: "guide" },
    ],
    surface: {
      eyebrow: "Configuration",
      minW: 560,
      defaultH: 600,
      load: () =>
        import("../pages/cores/SettingsCore").then((module) => ({
          default: module.SettingsCore,
        })),
    },
  },
  {
    action: "record-live",
    windowId: "surface-live",
    label: "Live meeting",
    description: "The live meeting room.",
    glyph: "●",
    href: "/live",
    surface: {
      eyebrow: "Meeting room",
      minW: 560,
      load: () =>
        import("../pages/cores/LiveCore").then((module) => ({
          default: module.LiveCore,
        })),
    },
  },
  {
    action: "configure-cadence",
    windowId: "surface-cadence",
    label: "Rhythm",
    description: "Sweep, brief, and notification cadence.",
    glyph: "◷",
    href: "/cadence",
    group: "tool",
    go: { order: 4, section: "tools" },
    surface: {
      eyebrow: "Follow-through",
      minW: 520,
      defaultH: 520,
      load: () =>
        import("../pages/cores/CadenceCore").then((module) => ({
          default: module.CadenceCore,
        })),
    },
  },
  /* HS-202-02 — `configure-setup` UNPARKED. HS-170-02 parked it on the
     claim that "project-setup replaced it", but `project-setup` is the
     New Project door (DoorCore); it shows no readiness check at all. The
     face that reads `/api/setup/status` — and with it the doctor's
     `_check_microphone()` row (holdspeak/commands/doctor.py:1064, carried
     1:1 into the sections by setup_status.py:254-260) — is
     `pages/cores/SetupCore.tsx`, which had ZERO callers and no door at
     any width. The microphone recovery needs it, so it gets its key back
     and a Go/⌘K door with it. */
  {
    action: "configure-setup",
    windowId: "surface-setup",
    label: "Setup",
    description: "What this device is ready for, check by check.",
    glyph: "⚙",
    href: "/",
    // A tool, not a dock primary. PHILO-17 (doors): its door is the
    // HoldSpeak menu; ⌘K still finds it.
    group: "tool",
    mark: 4,
    surface: {
      eyebrow: "Readiness",
      minW: 560,
      defaultH: 560,
      load: () =>
        import("../pages/cores/SetupCore").then((module) => ({
          default: module.SetupCore,
        })),
    },
  },
  {
    action: "open-constitutional-context",
    windowId: "surface-constitutional-context",
    label: "Context",
    description: "The always-on briefing every agent receives.",
    glyph: "§",
    href: "/context",
    group: "tool",
    go: { order: 6, section: "tools" },
    surface: {
      eyebrow: "Owner",
      minW: 480,
      load: () =>
        import("../pages/cores/ConstitutionalContextCore").then((module) => ({
          default: module.ConstitutionalContextCore,
        })),
    },
  },
  {
    action: "open-workbenches",
    windowId: "surface-workbenches",
    label: "Workbenches",
    description: "Mission control for your agent workbenches.",
    glyph: "⚒",
    href: "/workbenches",
    group: "tool",
    go: { order: 1, section: "tools" },
    surface: {
      eyebrow: "Work",
      minW: 560,
      load: () =>
        import("../pages/cores/WorkbenchesHomeCore").then((module) => ({
          default: module.WorkbenchesHomeCore,
        })),
    },
  },
  {
    action: "design-components",
    windowId: "surface-components",
    label: "Components",
    description: "The executable Signal component catalog.",
    glyph: "▦",
    href: "/components",
    surface: {
      eyebrow: "Signal React",
      minW: 640,
      load: () =>
        import("../pages/cores/ComponentsCore").then((module) => ({
          default: module.ComponentsCore,
        })),
    },
  },
  {
    action: "inspect-activity",
    windowId: "surface-activity",
    label: "Activity",
    toolGlyph: "≋",
    description: "Inspect work context and source records.",
    glyph: "⊙",
    href: "/activity",
    group: "tool",
    go: { order: 2, section: "tools" },
    surface: {
      eyebrow: "This-device context",
      minW: 480,
      load: () =>
        import("../pages/cores/ActivityCore").then((module) => ({
          default: module.ActivityCore,
        })),
    },
  },
  {
    action: "open-project-memory",
    windowId: "surface-project-memory",
    // PHILO-17 (doors): one name. The Dock's Missed list is a different thing.
    label: "Memory",
    description: "Search connected evidence across the Desk or within a Project.",
    glyph: "▤",
    href: "/project-memory",
    group: "tool",
    go: { order: 7, section: "app" },
    surface: {
      eyebrow: "Long memory",
      minW: 800,
      load: () =>
        import("../pages/cores/ProjectMemoryCore").then((module) => ({
          default: module.ProjectMemoryCore,
        })),
    },
  },
  // HS-169-02: the streamlined Door (replaces the setup interview)
  // HS-170-03: the Concierge — the Models surface (replaces ModelLibraryCore + CapabilityAssignmentsCore)
  {
    action: "open-concierge",
    windowId: "surface-concierge",
    // PHILO-16 (C): one name, Runs on (product-language.json); the window id
    // and the /models href stay so every caller and saved desk still opens it.
    label: "Runs on",
    description: "What HoldSpeak does, wired to what you have.",
    glyph: "▣",
    href: "/models",
    // HS-200-04 (return-to-task): `configure-runs-on` had no hosted surface, so
    // every "Set up AI" handoff fell back to navigate("/settings") — which
    // unmounts the calling face and loses an unfinished Thought answer. As an
    // alias of the hosted Concierge it opens in-world instead: the task stays
    // mounted underneath and is still there when the window closes.
    aliases: [{ key: "configure-runs-on" }],
    surface: {
      eyebrow: "Settings",
      // The board's three columns (canvas Board 2); a phone draws the list.
      minW: 900,
      defaultH: 680,
      // PHILO-16 (C): the Switchboard replaces the Concierge (parked).
      load: () =>
        import("../features/runson/RunsOnCore").then((module) => ({
          default: module.RunsOnCore,
        })),
    },
  },
  {
    action: "project-setup",
    windowId: "surface-project-setup",
    label: "New Project",
    description: "Create a Project in one screen.",
    glyph: "▣",
    href: "/",
    surface: {
      eyebrow: "Setup",
      minW: 560,
      defaultH: 580,
      load: () =>
        import("../features/project-room/door/DoorCore").then((module) => ({
          default: module.DoorCore,
        })),
    },
  },
  {
    action: "inspect-processes",
    windowId: "surface-processes",
    label: "Processes",
    description: "See what the kernel is running.",
    glyph: "∷",
    href: "/#processes",
    group: "tool",
    go: { order: 3, section: "tools" },
    surface: {
      eyebrow: "Kernel",
      minW: 520,
      load: () =>
        import("../pages/cores/ProcessCore").then((module) => ({
          default: module.ProcessCore,
        })),
    },
  },
  {
    action: "configure-commands",
    windowId: "surface-commands",
    label: "Commands",
    description: "Map spoken phrases to registered actions.",
    glyph: "⌘",
    href: "/commands",
    group: "tool",
    go: { order: 5, section: "tools" },
    surface: {
      eyebrow: "Voice commands",
      minW: 460,
      load: () =>
        import("../pages/cores/CommandsCore").then((module) => ({
          default: module.CommandsCore,
        })),
    },
  },
  {
    action: "open-people",
    windowId: "surface-people",
    label: "People",
    description: "Relationships, commitments, and follow-through.",
    glyph: "♧",
    href: "/",
    // PHILO-17 (doors): the People drawer on the desk, and Go.
    go: { order: 5, section: "app" },
    surface: {
      eyebrow: "Follow-through",
      minW: 560,
      load: () =>
        import("../pages/cores/PeopleCore").then((module) => ({
          default: module.PeopleCore,
        })),
    },
  },
  {
    action: "review-calendar-snapshot",
    windowId: "surface-calendar-snapshot",
    label: "Calendar snapshot",
    description: "Review calendar evidence before it enters the Desk.",
    glyph: "▦",
    href: "/calendar-snapshot",
    surface: {
      eyebrow: "Calendar",
      minW: 640,
      load: () =>
        import("../pages/cores/CalendarSnapshotReviewCore").then((module) => ({
          default: module.CalendarSnapshotReviewCore,
        })),
    },
  },
  // HS-170-03: configure-runs-on now opens the Concierge window.
  {
    action: "configure-runs-on",
    windowId: "surface-concierge",
    label: "Runs on",
    description: "What HoldSpeak does, wired to what you have.",
    glyph: "▣",
    href: "/models",
    group: "tool",
    mark: 2,
  },
  {
    action: "configure-integrations",
    windowId: "surface-settings",
    label: "Connections",
    description: "Configure connected destinations and credentials.",
    glyph: "↗",
    href: "/settings",
    group: "tool",
    mark: 3,
    subjectRef: "integration:destinations",
  },
] as const;

export const SURFACE_APPLICATIONS: readonly SurfaceApplication[] =
  DESK_APPLICATIONS.filter(
    (application): application is (typeof DESK_APPLICATIONS)[number] & {
      surface: DeskSurfaceSpec;
    } => "surface" in application && application.surface !== undefined,
  );

export type DockApplication = DeskApplication & {
  dock: NonNullable<DeskApplication["dock"]>;
};

export const DOCK_APPLICATIONS: readonly DockApplication[] =
  DESK_APPLICATIONS.filter(
    (application): application is DockApplication => Boolean(application.dock),
  ).sort((left, right) => left.dock.order - right.dock.order);

/** The registry verb that opens an application: Intelligence and People
 * open through their desk verbs, every other application through `go.*`. */
export function applicationVerbId(application: DeskApplication): string {
  return application.action === "open-intelligence" || application.action === "open-people"
    ? `desk.${application.action}`
    : `go.${application.action}`;
}

/** PHILO-17 (doors): the HoldSpeak menu holds the setup applications only:
 * Settings, Runs on, Connections, Setup. */
export const MARK_APPLICATION_COMMANDS = DESK_APPLICATIONS.filter(
  (application) => application.mark !== undefined,
)
  .sort((left, right) => (left.mark ?? 0) - (right.mark ?? 0))
  .map(applicationVerbId);

function goRows(section: "app" | "tools"): readonly DeskApplication[] {
  return DESK_APPLICATIONS.filter((application) => application.go?.section === section)
    .sort((left, right) => (left.go?.order ?? 0) - (right.go?.order ?? 0));
}

/** PHILO-17 (doors): Go is the index of the applications. Its lead rows,
 * in order; then Projects ▸; then Tools ▸ with `GO_TOOL_APPLICATIONS`. */
export const GO_APPLICATIONS = goRows("app");
export const GO_TOOL_APPLICATIONS = goRows("tools");

export const DESK_APPLICATION_ALIASES = Object.fromEntries(
  DESK_APPLICATIONS.flatMap((application) =>
    (application.aliases ?? []).map((alias) => [
      alias.key,
      { target: application.action, scope: alias.scope },
    ]),
  ),
) as Record<string, { target: string; scope?: string }>;

export function applicationForAction(action: string): DeskApplication | undefined {
  return DESK_APPLICATIONS.find((application) => application.action === action);
}

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
  shortcut?: string;
  mark?: boolean;
  toolLabel?: string;
  toolGlyph?: string;
}

export type SurfaceApplication = DeskApplication & {
  surface: DeskSurfaceSpec;
};

export const DESK_APPLICATIONS: readonly DeskApplication[] = [
  {
    action: "open-intelligence",
    windowId: "intelligence:desk",
    label: "Intelligence",
    description: "Briefs, follow-through, receipts, and reasons.",
    glyph: "◈",
    href: "/",
    dock: { order: 0, launch: "intelligence" },
    mark: true,
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
    shortcut: "⌘1",
    mark: true,
    surface: {
      eyebrow: "Daily cockpit",
      minW: 560,
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
    shortcut: "⌘2",
    mark: true,
    surface: {
      eyebrow: "Meeting memory",
      minW: 640,
      load: () =>
        import("../pages/cores/HistoryCore").then((module) => ({
          default: module.HistoryCore,
        })),
    },
  },
  {
    action: "inspect-personas-and-coders",
    windowId: "surface-companion",
    label: "Agents",
    toolLabel: "Agents and coder sessions",
    description: "Use saved behavior and inspect live sessions.",
    glyph: "◉",
    href: "/companion",
    group: "tool",
    dock: { order: 3, launch: "surface" },
    shortcut: "⌘3",
    mark: true,
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
    dock: { order: 4, launch: "surface" },
    shortcut: "⌘4",
    mark: true,
    aliases: [
      { key: "configure-integrations", scope: "integration:destinations" },
      { key: "configure-integration" },
      { key: "configure-runs-on", scope: "models" },
      { key: "read-runtime-docs", scope: "guide" },
    ],
    surface: {
      eyebrow: "Configuration",
      minW: 560,
      defaultH: 760,
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
    label: "Cadence",
    description: "Configure scheduled background work.",
    glyph: "◷",
    href: "/cadence",
    group: "tool",
    surface: {
      eyebrow: "Follow-through",
      minW: 520,
      load: () =>
        import("../pages/cores/CadenceCore").then((module) => ({
          default: module.CadenceCore,
        })),
    },
  },
  {
    action: "configure-setup",
    windowId: "surface-setup",
    label: "Setup",
    description: "Configure the first arrival.",
    glyph: "✓",
    href: "/setup",
    surface: {
      eyebrow: "Arrival",
      minW: 520,
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
    label: "Project memory",
    description: "Long-lived project context and evidence.",
    glyph: "▤",
    href: "/project-memory",
    surface: {
      eyebrow: "Long memory",
      minW: 640,
      load: () =>
        import("../pages/cores/ProjectMemoryCore").then((module) => ({
          default: module.ProjectMemoryCore,
        })),
    },
  },
  // HS-159-05: project-setup surface (the interview)
  {
    action: "project-setup",
    windowId: "surface-project-setup",
    label: "New Project",
    description: "Create a Project through the guided interview.",
    glyph: "▣",
    href: "/",
    surface: {
      eyebrow: "Setup",
      minW: 560,
      load: () =>
        import("../features/project-room/setup/SetupRoot").then((module) => ({
          default: module.SetupCore,
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
    mark: true,
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
  {
    action: "configure-runs-on",
    windowId: "surface-settings",
    label: "Runs on",
    description: "Configure model and runtime destinations.",
    glyph: "▣",
    href: "/profiles",
    group: "tool",
    subjectRef: "models",
  },
  {
    action: "configure-integrations",
    windowId: "surface-settings",
    label: "Integrations",
    description: "Configure connected destinations and credentials.",
    glyph: "↗",
    href: "/settings",
    group: "tool",
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

export const MARK_APPLICATION_COMMANDS = DESK_APPLICATIONS.filter(
  (application) => application.mark,
).map((application) =>
  application.action === "open-intelligence" || application.action === "open-people"
    ? `desk.${application.action}`
    : `go.${application.action}`,
);

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

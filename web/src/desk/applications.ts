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
  dock?: { order: number; launch: "surface" | "intelligence"; phone?: number };
  /** Parked surfaces keep their manifest and hub id without a live host. */
  parked?: string;
  /** Betterment shell S1: the row in Go, on the desktop and the phone. Go
   * draws Daily, then Work, then Builder ▸ (only when the Builder tools
   * setting is on), each in `order`. `label` is Go's word when it differs.
   * No `go`: not in Go (Search still finds a grouped application). */
  go?: { group: GoGroup; order: number; label?: string };
  shortcut?: string;
  /** PHILO-17 (doors): the row in the HoldSpeak menu, in this order. */
  mark?: number;
  toolLabel?: string;
  toolGlyph?: string;
}

export type GoGroup = "daily" | "work" | "builder";

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
    // Betterment setup ST1: Wallpaper has one home, Settings ▸ Wallpaper.
    // The row keeps its id, its Search words and ⌘⇧P; each opens Settings
    // there (the `change-places` alias on Settings). ChangePlacesCore stays.
    parked: "settings:wallpaper",
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
    // Betterment shell S1: a group, so Search lists it.
    group: "app",
    dock: { order: 0, launch: "intelligence", phone: 0 },
    go: { group: "daily", order: 0 },
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
    go: { group: "daily", order: 7 },
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
    go: { group: "daily", order: 6 },
  },
  {
    action: "review-meetings",
    windowId: "surface-meetings",
    label: "Meetings",
    description: "Outcomes, recordings, and the typed record.",
    glyph: "▣",
    href: "/history",
    group: "app",
    dock: { order: 2, launch: "surface", phone: 2 },
    go: { group: "daily", order: 2 },
    shortcut: "⌃2",
    surface: {
      eyebrow: "Meeting memory",
      minW: 640,
      // PHILO-17 (windows): the canonical first-open meeting room size.
      defaultW: 720,
      defaultH: 600,
      load: () =>
        import("../pages/cores/HistoryCore").then((module) => ({
          default: module.HistoryCore,
        })),
    },
  },
  // PHILO-14 C4: the Conductor drawer is where agents live. Betterment AG1
  // (DECISIONS #3): its face name is Agents; the action, window id, route
  // and ⌃3 keep the code name.
  {
    action: "open-conductor",
    windowId: "conductor",
    label: "Agents",
    toolLabel: "Agents",
    description: "Your coding agents: who works, who asks you, what they finished.",
    glyph: "◉",
    href: "/conductor",
    group: "tool",
    // PHILO-17 (doors): the Agents door is its desk drawer, Dock and Go.
    dock: { order: 4, launch: "surface" },
    go: { group: "daily", order: 5 },
    shortcut: "⌃3",
  },
  // Betterment AG1: the old Agents application (`/companion`, CompanionCore)
  // is unmapped: no manifest row, its address opens Agents. Its row is
  // parked in desk/_parked/agents/companionApplication.ts.
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
      // The retired Guide alias is parked under _parked/setupGuideAlias.ts.
      // Betterment setup ST1: the parked Rhythm window and Change places.
      { key: "configure-cadence", scope: "rhythm" },
      { key: "change-places", scope: "wallpaper" },
    ],
    surface: {
      eyebrow: "Configuration",
      minW: 880,
      defaultW: 1040,
      defaultH: 720,
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
    // Betterment setup ST1: Rhythm has one home, Settings ▸ Rhythm. The
    // sweep and the loops are under its Advanced fold (CadenceCore, embedded
    // there); the window is parked, its id and Search word open Settings.
    parked: "settings:rhythm",
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
    aliases: [{ key: "read-runtime-docs" }],
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
    go: { group: "builder", order: 2 },
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
    label: "Automations",
    description: "Jobs that run for you on a schedule or when something happens.",
    glyph: "⚒",
    href: "/workbenches",
    go: { group: "work", order: 0 },
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
    // Betterment shell S1: a group, so Search lists it.
    group: "tool",
    go: { group: "builder", order: 3 },
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
    go: { group: "builder", order: 0 },
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
    // PHILO-17 (doors): one name. The Dock's Missed list is a different thing.
    label: "Memory",
    description: "Search connected evidence across the Desk or within a Project.",
    glyph: "▤",
    href: "/project-memory",
    go: { group: "work", order: 1 },
    group: "tool",
    surface: {
      eyebrow: "Long memory",
      minW: 800,
      load: () =>
        import("../pages/cores/MemoryCore").then((module) => ({
          default: module.MemoryCore,
        })),
    },
  },
  // HS-169-02: the streamlined Door (replaces the setup interview)
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
    go: { group: "builder", order: 1 },
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
    go: { group: "work", order: 2, label: "Voice commands" },
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
    // Betterment shell S1: a group, so Search lists it.
    group: "app",
    dock: { order: 3, launch: "surface", phone: 3 },
    // PHILO-17 (doors): the People drawer on the desk, and Go.
    go: { group: "daily", order: 3 },
    surface: {
      eyebrow: "Follow-through",
      minW: 560,
      load: () =>
        import("../pages/cores/PeopleCore").then((module) => ({
          default: module.PeopleCore,
        })),
    },
  },
  // Betterment P4 (projects): every project in one list (where each stands,
  // its next date, its newest update), and the decisions in their one home.
  {
    action: "open-projects",
    windowId: "surface-projects",
    label: "Projects",
    description: "Every project: where it stands, its next date, its newest update.",
    glyph: "▣",
    href: "/",
    group: "app",
    // Its Go door is the first row of Go ▸ Projects ▸ ("All projects"),
    // above each project (GO_EXTRA_ROWS `projects`, DeskMenuBar goEntries).
    surface: {
      eyebrow: "Work in flight",
      minW: 480,
      defaultW: 640,
      defaultH: 520,
      load: () =>
        import("../pages/cores/ProjectsCore").then((module) => ({
          default: module.ProjectsCore,
        })),
    },
  },
  {
    action: "open-decisions",
    windowId: "surface-decisions",
    label: "Decisions",
    description: "Every decision, why it was made and what replaced it.",
    glyph: "◈",
    href: "/",
    group: "app",
    go: { group: "daily", order: 4.5 },
    surface: {
      eyebrow: "Decided",
      minW: 520,
      defaultW: 680,
      defaultH: 600,
      load: () =>
        import("../pages/cores/DecisionsCore").then((module) => ({
          default: module.DecisionsCore,
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
    // Betterment shell S1: a group, so Search lists it.
    group: "tool",
    go: { group: "builder", order: 4 },
    surface: {
      eyebrow: "Calendar",
      minW: 640,
      load: () =>
        import("../pages/cores/CalendarSnapshotReviewCore").then((module) => ({
          default: module.CalendarSnapshotReviewCore,
        })),
    },
  },
  // Betterment ST7: Engines is a real Desk window. The old Concierge id is
  // retained only in the hub's retired registry so saved rows can close; its
  // action is an alias to this canonical host and legacy `/models` links land
  // here too.
  {
    action: "configure-runs-on",
    windowId: "surface-engines",
    label: "Engines",
    description: "What HoldSpeak does, wired to what you have.",
    glyph: "▣",
    href: "/models",
    group: "tool",
    mark: 2,
    aliases: [{ key: "open-concierge" }],
    surface: {
      eyebrow: "Engine assignments",
      minW: 760,
      defaultW: 1040,
      defaultH: 720,
      load: () =>
        import("../features/runson/RunsOnCore").then((module) => ({
          default: module.RunsOnCore,
        })),
    },
  },
  {
    action: "configure-integrations",
    windowId: "surface-settings",
    label: "Accounts",
    description: "Configure connected destinations and credentials.",
    glyph: "↗",
    href: "/settings",
    group: "tool",
    mark: 3,
    subjectRef: "integration:destinations",
    parked: "settings:integrations",
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
  // Betterment shell S1: a parked row that Settings now hosts opens the
  // Settings wing verb (`settings.<wing>`), never its parked surface.
  const wing = parkedSettingsWing(application);
  if (wing) return `settings.${wing}`;
  return application.action === "open-intelligence" || application.action === "open-people"
    ? `desk.${application.action}`
    : `go.${application.action}`;
}

/** The Settings wing a parked row moved to (`parked: "settings:<wing>"`). */
export function parkedSettingsWing(application: DeskApplication): string | null {
  return application.parked?.startsWith("settings:") ? application.parked.slice("settings:".length) : null;
}

/** PHILO-17 (doors): the HoldSpeak menu holds the setup applications only:
 * Settings, Runs on, Connections, Setup. */
export const MARK_APPLICATION_COMMANDS = DESK_APPLICATIONS.filter(
  (application) => application.mark !== undefined,
)
  .sort((left, right) => (left.mark ?? 0) - (right.mark ?? 0))
  .map(applicationVerbId);

/** Betterment shell S1: Go rows that are not applications, in the same
 * grammar as the manifest's `go`: the Chair's Needs you window, the desk's
 * projects and drawers (submenus), the builder launchers and Refresh. */
export type GoExtra =
  | { kind: "verb"; verbId: string; label?: string; phoneVerbId?: string }
  | { kind: "projects" }
  | { kind: "drawers" }
  | { kind: "launcher"; launcherId: string; label: string; glyph: string };

export const GO_EXTRA_ROWS: readonly (GoExtra & { go: { group: GoGroup; order: number } })[] = [
  { kind: "verb", verbId: "chair.window.needs", label: "Needs you", go: { group: "daily", order: 1 } },
  // The Chair's other window: S0 left the Window menu with one line on an
  // empty desk, so Go is its door (PLAN: no app is reachable only by a
  // detour). Daily D5: Brief and The week retired into Today.
  { kind: "verb", verbId: "chair.window.capture", label: "Capture", go: { group: "daily", order: 1.6 } },
  // Betterment P4 (projects): Projects ▸ opens with All projects (the
  // Projects window), then each project; it is drawn on an empty desk too.
  { kind: "projects", go: { group: "daily", order: 4 } },
  { kind: "drawers", go: { group: "work", order: 3 } },
  { kind: "launcher", launcherId: "delivery-board", label: "Delivery board", glyph: "▤", go: { group: "builder", order: 5 } },
  { kind: "launcher", launcherId: "panes", label: "Terminals", glyph: "⧉", go: { group: "builder", order: 6 } },
  { kind: "verb", verbId: "desk.refresh", go: { group: "builder", order: 7 } },
];

/** One Go row: an application or one of the rows above. */
export type GoRow = (GoExtra | { kind: "app"; app: DeskApplication; label: string }) & {
  group: GoGroup;
  order: number;
};

export const GO_GROUPS: readonly GoGroup[] = ["daily", "work", "builder"];

/** Betterment shell S1: the rows of one Go group, in order, from the
 * manifest and GO_EXTRA_ROWS. Go on the desktop, Go on the phone and the
 * phone home draw these and nothing else. */
export function goRows(group: GoGroup): GoRow[] {
  const apps: GoRow[] = DESK_APPLICATIONS.filter((application) => application.go?.group === group)
    .map((app) => ({
      kind: "app" as const, app, label: app.go?.label ?? app.toolLabel ?? app.label,
      group, order: app.go?.order ?? 0,
    }));
  const extras: GoRow[] = GO_EXTRA_ROWS.filter((row) => row.go.group === group)
    .map(({ go, ...row }) => ({ ...row, group, order: go.order }));
  return [...apps, ...extras].sort((left, right) => left.order - right.order);
}

/** The applications Go lists only behind Builder tools. Search gates them too. */
export const BUILDER_APPLICATION_ACTIONS: ReadonlySet<string> = new Set(
  DESK_APPLICATIONS.filter((application) => application.go?.group === "builder").map((a) => a.action),
);

export const DESK_APPLICATION_ALIASES = Object.fromEntries(
  DESK_APPLICATIONS.flatMap((application) =>
    (application.aliases ?? []).map((alias) => [
      alias.key,
      { target: application.action, scope: alias.scope },
    ]),
  ),
) as Record<string, { target: string; scope?: string }>;

/** Compose a wing scope with the object/job that opened it. The first
 * segment selects the hosted face; the remaining segments survive the handoff
 * and reload. `::` is deliberately explicit so a model/job or account/door
 * can never overwrite the Settings wing selection. */
export function composeApplicationScope(
  defaultScope?: string,
  requestedScope?: string,
): string | undefined {
  const base = defaultScope?.trim();
  const request = requestedScope?.trim();
  if (!base) return request || undefined;
  if (!request || request === base) return base;
  return `${base}::${request}`;
}

export function applicationForAction(action: string): DeskApplication | undefined {
  return DESK_APPLICATIONS.find((application) => application.action === action);
}

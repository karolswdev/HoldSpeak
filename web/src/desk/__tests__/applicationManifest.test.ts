import { describe, expect, it } from "vitest";
import {
  DESK_APPLICATION_ALIASES,
  DESK_APPLICATIONS,
  DOCK_APPLICATIONS,
  GO_GROUPS,
  MARK_APPLICATION_COMMANDS,
  goRows,
  SURFACE_APPLICATIONS,
} from "../applications";
import { DESK_TOOLS } from "../tools";
import { PULLOUT_SIZE } from "../pullouts/size";

describe("DeskOS application manifest", () => {
  it("has stable, unique application actions", () => {
    const actions = DESK_APPLICATIONS.map((application) => application.action);
    expect(new Set(actions).size).toBe(actions.length);
  });

  it("derives every shell projection from registered applications", () => {
    const actions = new Set(
      DESK_APPLICATIONS.map((application) => application.action),
    );

    expect(SURFACE_APPLICATIONS.every((application) => actions.has(application.action))).toBe(true);
    expect(DOCK_APPLICATIONS.every((application) => actions.has(application.action))).toBe(true);
    expect(DESK_TOOLS.every((tool) => actions.has(tool.action))).toBe(true);
  });

  it("keeps aliases pointed at hosted surfaces", () => {
    const hosted = new Set(
      SURFACE_APPLICATIONS.map((application) => application.action),
    );
    for (const alias of Object.values(DESK_APPLICATION_ALIASES)) {
      expect(hosted.has(alias.target)).toBe(true);
    }
  });

  it("keeps Dock order and shortcuts declarative", () => {
    // PHILO-17 (doors): the five primary Dock applications.
    expect(DOCK_APPLICATIONS.map((application) => application.label)).toEqual([
      "Today",
      "Speak",
      "Meetings",
      "People",
      "Agents",
    ]);
    expect(
      DESK_APPLICATIONS.filter((application) => application.shortcut).map(
        (application) => application.shortcut,
      ),
    ).toEqual(["⌘⇧P", "⌃1", "⌃2", "⌃3", "⌃4"]); // PHILO-17 U27
  });

  it("keeps the PHILO-17 first-open size matrix declarative", () => {
    expect(PULLOUT_SIZE).toMatchObject({
      note: { w: 520, h: 360 },
      meeting: { w: 720, h: 600 },
      people: { w: 640, h: 560 },
      room: { w: 760, h: 480 },
      settings: { w: 640, h: 600 },
    });

    const meetings = DESK_APPLICATIONS.find((application) => application.action === "review-meetings");
    const settings = DESK_APPLICATIONS.find((application) => application.action === "configure-settings");
    expect(meetings?.surface).toMatchObject({ defaultW: 720, defaultH: 600 });
    expect(settings?.surface).toMatchObject({ defaultW: 640, defaultH: 600 });
  });

  it("Betterment AG1: the old Agents application is unmapped; the Conductor's face name is Agents", () => {
    // The old Agents application (`/companion`) has no manifest row now; its
    // row is parked in desk/_parked/agents/companionApplication.ts.
    expect(DESK_APPLICATIONS.some((application) => application.action === "inspect-personas-and-coders")).toBe(false);
    expect(DESK_APPLICATIONS.some((application) => application.windowId === "surface-companion")).toBe(false);
    const conductor = DESK_APPLICATIONS.find((application) => application.action === "open-conductor");
    // The code name stays (action, window id, route, ⌃3); the face says Agents.
    expect(conductor).toMatchObject({ windowId: "conductor", label: "Agents", toolLabel: "Agents", href: "/conductor", shortcut: "⌃3" });
    expect(conductor?.dock).toMatchObject({ order: 4, launch: "surface" });
  });

  it("derives mark-menu application commands", () => {
    // PHILO-17 (doors): the HoldSpeak menu holds the setup applications.
    // Betterment shell S1: Engines and Accounts open their Settings wings.
    expect(MARK_APPLICATION_COMMANDS).toEqual([
      "go.configure-settings",
      "settings.models",
      "settings.integrations",
      "go.configure-setup",
    ]);
  });

  it("betterment shell S1: Go lists every application, Daily, Work, Builder", () => {
    const names = (group: (typeof GO_GROUPS)[number]) =>
      goRows(group).map((r) => (r.kind === "app" || r.kind === "launcher" ? r.label : r.kind === "verb" ? r.label ?? r.verbId : r.kind));
    expect(names("daily")).toEqual([
      "Today", "Needs you", "Capture", "Meetings", "People", "projects", "Agents", "Ask AI", "Speak",
    ]);
    expect(names("work")).toEqual(["Automations", "Memory", "Voice commands", "drawers"]);
    expect(names("builder")).toEqual([
      "Activity", "Processes", "Context", "Components", "Calendar snapshot", "Delivery board", "Terminals", "desk.refresh",
    ]);
    // A setup application has one door: the HoldSpeak menu. Rhythm's home is Settings ▸ Rhythm.
    for (const action of ["configure-settings", "configure-runs-on", "configure-integrations", "configure-setup", "configure-cadence"]) {
      const application = DESK_APPLICATIONS.find((a) => a.action === action);
      expect(application?.go, action).toBeUndefined();
      expect(application?.dock, action).toBeUndefined();
    }
    // Every live, windowed application with a door to open is in Go, or is a
    // setup row of the HoldSpeak menu, or is opened by its own verb.
    const inGo = new Set(GO_GROUPS.flatMap(goRows).flatMap((r) => (r.kind === "app" ? [r.app.action] : [])));
    const elsewhere = new Set(["configure-settings", "configure-setup", "configure-cadence", "change-places",
      "record-live", "project-setup"]);
    for (const application of DESK_APPLICATIONS) {
      if (application.parked) continue;
      expect(inGo.has(application.action) || elsewhere.has(application.action), application.action).toBe(true);
    }
  });

  it("Betterment setup ST1: Rhythm and Change places are parked; their keys, Search words and ⌘⇧P open Settings at Rhythm and at Wallpaper", () => {
    const rhythm = DESK_APPLICATIONS.find((a) => a.action === "configure-cadence");
    const places = DESK_APPLICATIONS.find((a) => a.action === "change-places");
    // The ids stay (a saved desk names them); the windows are parked.
    expect(rhythm).toMatchObject({ windowId: "surface-cadence", label: "Rhythm", parked: "settings:rhythm" });
    expect(places).toMatchObject({ windowId: "surface-places", label: "Change places", parked: "settings:wallpaper", shortcut: "⌘⇧P" });
    expect(DESK_APPLICATION_ALIASES["configure-cadence"]).toEqual({ target: "configure-settings", scope: "rhythm" });
    expect(DESK_APPLICATION_ALIASES["change-places"]).toEqual({ target: "configure-settings", scope: "wallpaper" });
    // Search keeps their words (a grouped application is a Search row).
    for (const action of ["configure-cadence", "change-places"])
      expect(DESK_TOOLS.some((tool) => tool.action === action), action).toBe(true);
  });

  it("betterment shell S1: Today, People and Components have a group, so Search lists them", () => {
    for (const action of ["open-intelligence", "open-people", "design-components"])
      expect(DESK_TOOLS.some((tool) => tool.action === action), action).toBe(true);
  });

  // The global Desk surface and scoped Project Room share one retrieval face.
  it("pins the Desk Memory registration: action, windowId, label, glyph, surface", () => {
    const projectMemory = DESK_APPLICATIONS.find(
      (application) => application.action === "open-project-memory",
    );
    expect(projectMemory).toBeDefined();
    expect(projectMemory).toMatchObject({
      action: "open-project-memory",
      windowId: "surface-project-memory",
      label: "Memory",
      description: "Search connected evidence across the Desk or within a Project.",
      glyph: "▤",
      href: "/project-memory",
      group: "tool",
    });
    expect(projectMemory!.surface).toBeDefined();
    expect(projectMemory!.surface!.eyebrow).toBe("Long memory");
    // HS-169-03: Room default width changed from 640 to 800.
    expect(projectMemory!.surface!.minW).toBe(800);
  });

  it("includes Project Memory in the surface-application projection", () => {
    expect(
      SURFACE_APPLICATIONS.some(
        (application) => application.action === "open-project-memory",
      ),
    ).toBe(true);
  });
});

import { describe, expect, it } from "vitest";
import {
  DESK_APPLICATION_ALIASES,
  DESK_APPLICATIONS,
  DOCK_APPLICATIONS,
  GO_APPLICATIONS,
  GO_TOOL_APPLICATIONS,
  MARK_APPLICATION_COMMANDS,
  SURFACE_APPLICATIONS,
} from "../applications";
import { DESK_TOOLS } from "../tools";

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
    // PHILO-17 (doors): one primary door per application. The Conductor
    // and People are desk drawers; Settings is in the HoldSpeak menu.
    expect(DOCK_APPLICATIONS.map((application) => application.label)).toEqual([
      "Intelligence",
      "Speak",
      "Meetings",
    ]);
    expect(
      DESK_APPLICATIONS.filter((application) => application.shortcut).map(
        (application) => application.shortcut,
      ),
    ).toEqual(["⌘⇧P", "⌃1", "⌃2", "⌃3", "⌃4"]); // PHILO-17 U27
  });

  it("PHILO-14 C4: the old Agents application is parked: route alive, in no Dock, Go list, shortcut or mark", () => {
    const parked = DESK_APPLICATIONS.find((application) => application.action === "inspect-personas-and-coders");
    expect(parked?.surface).toBeDefined();
    expect(parked?.dock).toBeUndefined();
    expect(parked?.shortcut).toBeUndefined();
    expect(parked?.mark).toBeFalsy();
    expect(parked?.group).toBeUndefined();
    expect(DOCK_APPLICATIONS.some((application) => application.windowId === "surface-companion")).toBe(false);
    const conductor = DESK_APPLICATIONS.find((application) => application.action === "open-conductor");
    expect(conductor).toMatchObject({ windowId: "conductor", label: "Conductor", href: "/conductor", shortcut: "⌃3" });
    expect(conductor?.dock).toBeUndefined();
  });

  it("derives mark-menu application commands", () => {
    // PHILO-17 (doors): the HoldSpeak menu holds the setup applications.
    expect(MARK_APPLICATION_COMMANDS).toEqual([
      "go.configure-settings",
      "go.configure-runs-on",
      "go.configure-integrations",
      "go.configure-setup",
    ]);
  });

  it("PHILO-17 (doors): Go is the application index, then Tools", () => {
    expect(GO_APPLICATIONS.map((application) => application.label)).toEqual([
      "Speak", "Meetings", "Intelligence", "Ask AI", "People", "Conductor", "Memory",
    ]);
    expect(GO_TOOL_APPLICATIONS.map((application) => application.label)).toEqual([
      "Workbenches", "Activity", "Processes", "Rhythm", "Commands", "Context",
    ]);
    // A setup application has one door: the HoldSpeak menu.
    for (const action of ["configure-settings", "configure-runs-on", "configure-integrations", "configure-setup"]) {
      const application = DESK_APPLICATIONS.find((a) => a.action === action);
      expect(application?.go, action).toBeUndefined();
      expect(application?.dock, action).toBeUndefined();
    }
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

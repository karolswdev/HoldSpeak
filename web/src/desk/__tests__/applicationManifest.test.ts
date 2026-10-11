import { describe, expect, it } from "vitest";
import {
  DESK_APPLICATION_ALIASES,
  DESK_APPLICATIONS,
  DOCK_APPLICATIONS,
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
    expect(DOCK_APPLICATIONS.map((application) => application.label)).toEqual([
      "Intelligence",
      "Speak",
      "Meetings",
      // PHILO-14 C4: the Agents entry became the Conductor drawer.
      "Conductor",
      "Settings",
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
    const conductor = DOCK_APPLICATIONS.find((application) => application.action === "open-conductor");
    expect(conductor).toMatchObject({ windowId: "conductor", label: "Conductor", href: "/conductor", shortcut: "⌃3" });
  });

  it("derives mark-menu application commands", () => {
    expect(MARK_APPLICATION_COMMANDS).toEqual([
      "desk.open-intelligence",
      "go.dictate",
      "go.review-meetings",
      "go.open-conductor",
      "go.configure-settings",
      "desk.open-people",
    ]);
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
      label: "Desk memory",
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

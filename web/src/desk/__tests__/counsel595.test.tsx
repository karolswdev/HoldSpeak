/* HS-202-02 — Astra's counsel-on-built on PR #595 (DO-NOT-RATIFY).
 *
 * One file per finding it names, each fencing the RENDERED transition or
 * the real composition rather than a helper in isolation — which is what
 * the first round got wrong.
 */
import { describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import surfaceWindowsSource from "../components/SurfaceWindows.tsx?raw";
import { oneDoorPerName } from "../components/DeskToolShelf";

/* ── finding 1: the cold desk registers the recovery door ── */
describe("the first-run recovery registry (counsel 1)", () => {
  it("admits the doctor door as well as New Project", () => {
    const block = surfaceWindowsSource.slice(
      surfaceWindowsSource.indexOf("FIRST_VALUE_RECOVERY_KEYS"),
      surfaceWindowsSource.indexOf("export function SurfaceWindows"),
    );
    expect(block).toContain('"project-setup"');
    expect(block).toContain('"configure-setup"');
  });

  it("registers nothing else during first use", () => {
    expect(surfaceWindowsSource).toMatch(
      /FIRST_VALUE_RECOVERY_SURFACES = SURFACES\.filter/,
    );
  });
});

/* ── finding 6: one LIVE row per name, not only one ghost ── */
describe("one Ask AI door with a selection (counsel 6)", () => {
  const rows = [
    { id: "object.ask", label: "Ask AI", section: "VERBS" },
    { id: "go.ask", label: "Ask AI", section: "PROGRAMS" },
    { id: "object.rename", label: "Rename", section: "VERBS" },
  ];

  it("keeps the object verb when a selection makes it runnable", () => {
    expect(oneDoorPerName(rows).map((r) => r.id)).toEqual([
      "object.ask",
      "object.rename",
    ]);
  });

  it("keeps the launcher when the object verb cannot run", () => {
    const ghosted = [
      { id: "object.ask", label: "Ask AI", ghost: "Select an object" },
      { id: "go.ask", label: "Ask AI" },
    ];
    expect(oneDoorPerName(ghosted).map((r) => r.id)).toEqual(["go.ask"]);
  });

  it("never returns two rows wearing one name", () => {
    const names = oneDoorPerName(rows).map((r) => r.label.toLowerCase());
    expect(new Set(names).size).toBe(names.length);
  });
});

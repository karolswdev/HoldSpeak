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
import firstWordsSource from "../components/FirstWords.tsx?raw";
import { needsMicrophoneDoctor } from "../../lib/dictationRecovery";

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

/* ── Astra round 2, residual 1: dedupe is a rule about DOORS ──
 * `oneDoorPerName` ran over every palette row, so the desk's own saved
 * objects collapsed by title: three notes and a meeting all called
 * "Thought" left one row, and the other three were unreachable from ⌘K. */
describe("deduplication never hides a saved object (round 2, residual 1)", () => {
  const rows = [
    { id: "note:a", label: "Thought", section: "OBJECTS" },
    { id: "note:b", label: "Thought", section: "OBJECTS" },
    { id: "meeting:c", label: "Thought", section: "MEETINGS" },
    { id: "object.ask", label: "Ask AI", section: "VERBS" },
    { id: "go.ask", label: "Ask AI", section: "PROGRAMS" },
  ];

  it("keeps every object that wears one title", () => {
    expect(
      oneDoorPerName(rows)
        .filter((row) => row.section === "OBJECTS" || row.section === "MEETINGS")
        .map((row) => row.id),
    ).toEqual(["note:a", "note:b", "meeting:c"]);
  });

  it("still collapses the launcher and the object verb to one door", () => {
    expect(
      oneDoorPerName(rows)
        .filter((row) => row.label === "Ask AI")
        .map((row) => row.id),
    ).toEqual(["object.ask"]);
  });

  it("never lets an object's title withdraw a verb of the same name", () => {
    const shadowed = [
      { id: "note:open", label: "Open", section: "OBJECTS" },
      { id: "object.open", label: "Open", section: "VERBS", ghost: "Select an object" },
    ];
    expect(oneDoorPerName(shadowed).map((row) => row.id)).toEqual([
      "note:open",
      "object.open",
    ]);
  });
});

/* ── Astra round 2, residual 2: both microphone failures owe the doctor ──
 * `microphone_unavailable` (NotReadableError / TrackStartError) set
 * `setup: true` but was not routed, so its setup door was New Project —
 * offered as microphone recovery. */
describe("microphone recovery reaches the doctor (round 2, residual 2)", () => {
  it("sends both microphone failures to the readiness face", () => {
    expect(needsMicrophoneDoctor("no_microphone")).toBe(true);
    expect(needsMicrophoneDoctor("microphone_unavailable")).toBe(true);
  });

  it("leaves every other setup failure on the one-screen Door", () => {
    for (const failure of ["missing_model", "rejected_token"] as const)
      expect(needsMicrophoneDoctor(failure)).toBe(false);
  });

  it("is the gate the face itself reads, for the route AND the verb", () => {
    const block = firstWordsSource
      .slice(firstWordsSource.indexOf("setup_selected"))
      .replace(/\s+/g, " ");
    expect(block).toContain(
      'if (needsMicrophoneDoctor(failure)) openSurfaceOr("configure-setup", "/");',
    );
    expect(block).toContain(
      '{needsMicrophoneDoctor(failure) ? "Check the microphone" : "Setup"}',
    );
    expect(block).not.toContain('failure === "no_microphone"');
  });
});

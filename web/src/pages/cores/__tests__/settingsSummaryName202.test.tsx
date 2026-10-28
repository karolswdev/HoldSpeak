/* HS-202-04 (F06) — the Settings hub names the meeting result a Summary.
 *
 * The registry's rule is not Live-only: "What a Meeting produced for a
 * person to read. The wire calls it meeting intelligence. Every face says
 * Summary" (`docs/product-language.json:23`, HS-201-06). The Settings hub
 * is one of the five first-use jobs' screens (job 5, set up an engine),
 * and its Meetings row told the owner about `INTELLIGENCE ON` while the
 * Meetings face two windows over called the same thing a Summary and its
 * verb said `Run summary` (`history/helpers.ts:276`).
 *
 * `Intelligence` stays the name of the durable ledger application (the
 * Brief / Decisions / Follow-through window); it is never the name of
 * what one meeting produced.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PrefsFace, type SettingsHubWire } from "../settingsPrefs";

const hub = (intelligence: boolean): SettingsHubWire => ({
  models: { engines: 1, groupsSet: 1, defaultSet: true },
  connections: { connected: 0 },
  voice: { live: false, target: "" },
  meetings: { intelligence, auto: "room_linked", host: "192.168.1.43" },
  rhythm: { loops: 0 },
  sounds: { on: true },
  system: { host: "this device", mesh: false },
  posture: "neutral",
  writtenAt: null,
});

function face(intelligence: boolean) {
  const view = render(
    <PrefsFace
      onOpen={vi.fn()}
      hub={hub(intelligence)}
      posture="neutral"
      onPosture={vi.fn()}
      precedence={[]}
    />,
  );
  // PHILO-17 REFIT: the Meetings and Voice rows fold under More settings.
  return view;
}

describe("the Settings hub's Meetings row (F06)", () => {
  // PHILO-13-04 (A3): the row names the fact it reads, the configured switch.
  it("says SUMMARY SET ON, never INTELLIGENCE ON", () => {
    face(true);
    expect(
      screen.getByText("Summary set on · After room meetings"),
    ).toBeInTheDocument();
    expect(document.body.textContent ?? "").not.toMatch(/INTELLIGENCE/);
  });

  // PHILO-17: the idle ring read as an empty checkbox beside "AFTER ...".
  it("draws a check, not an empty ring, when the summary runs by itself", () => {
    face(true);
    const chip = screen.getByTestId("settings-hub-summary-chip");
    expect(chip.querySelector(".surface-state-chip-icon")?.textContent).toBe("✓");
  });

  it("says SUMMARY SET OFF, never INTELLIGENCE OFF", () => {
    face(false);
    expect(screen.getByText("Summary set off")).toBeInTheDocument();
    expect(document.body.textContent ?? "").not.toMatch(/INTELLIGENCE/);
  });
});

// Inventory 2026-10-03 (UX-CANON A.10): the hub said "Voice LIVE" and
// "SUMMARY SET ON" with no engine, beside the headline "No default model".
// replaces (with settings.app.test.tsx): tests/e2e/test_honest_faces_glass.py::test_settings_names_the_missing_engine
describe("the Settings hub names a missing engine", () => {
  function faceWith(patch: Partial<ReturnType<typeof hub>>) {
    const view = render(
      <PrefsFace
        onOpen={vi.fn()}
        hub={{ ...hub(true), ...patch }}
        posture="neutral"
        onPosture={vi.fn()}
        precedence={[]}
      />,
    );
    return view;
  }

  it("Meetings: SUMMARY · NO ENGINE when the switch is on and no engine is set", () => {
    faceWith({ meetings: { intelligence: true, engineSet: false, auto: "room_linked" } });
    expect(screen.getByText("Summary · No engine")).toBeInTheDocument();
    expect(document.body.textContent ?? "").not.toMatch(/SUMMARY SET ON/);
  });

  // Betterment ST0: the Voice fact reads whether speech works (the speech
  // model Setup reads), not the pipeline switch.
  it("Voice: Speech is not set up, never LIVE, when the switch is on and no speech model is here", () => {
    faceWith({ voice: { live: true, target: "auto", engineSet: true, speechReady: false } });
    expect(screen.getByText("Speech is not set up")).toBeInTheDocument();
    expect(screen.queryByText("LIVE")).toBeNull();
    expect(screen.queryByText("Works")).toBeNull();
  });

  it("Voice: Works when the speech model is here", () => {
    faceWith({ voice: { live: true, target: "auto", engineSet: false, speechReady: true } });
    expect(screen.getByText("Works")).toBeInTheDocument();
    expect(screen.queryByText("AUTO")).toBeNull();
  });

  it("Voice: Voice typing off when the switch is off", () => {
    faceWith({ voice: { live: false, target: "auto", speechReady: true } });
    expect(screen.getByText("Voice typing off")).toBeInTheDocument();
    expect(screen.queryByText("Works")).toBeNull();
  });
});

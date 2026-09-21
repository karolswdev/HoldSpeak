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
import { render, screen } from "@testing-library/react";
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
  return render(
    <PrefsFace
      onOpen={vi.fn()}
      hub={hub(intelligence)}
      posture="neutral"
      onPosture={vi.fn()}
      precedence={[]}
    />,
  );
}

describe("the Settings hub's Meetings row (F06)", () => {
  it("says SUMMARY ON, never INTELLIGENCE ON", () => {
    face(true);
    expect(
      screen.getByText("SUMMARY ON · AFTER ROOM MEETINGS"),
    ).toBeInTheDocument();
    expect(document.body.textContent ?? "").not.toMatch(/INTELLIGENCE/);
  });

  it("says SUMMARY OFF, never INTELLIGENCE OFF", () => {
    face(false);
    expect(screen.getByText("SUMMARY OFF")).toBeInTheDocument();
    expect(document.body.textContent ?? "").not.toMatch(/INTELLIGENCE/);
  });
});

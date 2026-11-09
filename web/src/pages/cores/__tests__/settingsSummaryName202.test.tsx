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
import { describe, expect, it } from "vitest";
import { sectionHealth, type SettingsHubWire } from "../settings/prefs";

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

// The language (2026-11-11): the drawer face is gone; the rail row of each
// section says the same fact, in one word and one colour.
describe("the Settings rail's Meetings word (F06)", () => {
  it("says Summaries on, never Intelligence", () => {
    expect(sectionHealth(hub(true)).meetings).toEqual({ tone: "moss", word: "Summaries on" });
    expect(JSON.stringify(sectionHealth(hub(true)))).not.toMatch(/ntelligence/);
  });

  it("says Summaries off, never Intelligence off", () => {
    expect(sectionHealth(hub(false)).meetings).toEqual({ tone: "idle", word: "Summaries off" });
  });
});

// Inventory 2026-10-03 (UX-CANON A.10): the hub said "Voice LIVE" and
// "SUMMARY SET ON" with no engine, beside the headline "No default model".
describe("the Settings rail names a missing engine", () => {
  const with_ = (patch: Partial<SettingsHubWire>) => sectionHealth({ ...hub(true), ...patch });

  it("Meetings: No summary engine (brass) when the switch is on and no engine is set", () => {
    expect(with_({ meetings: { intelligence: true, engineSet: false, auto: "room_linked" } }).meetings)
      .toEqual({ tone: "brass", word: "No summary engine" });
  });

  // Betterment ST0: the Speak fact reads whether speech works, not the switch.
  it("Speak: Speech not set up (brass) when the switch is on and no speech model is here", () => {
    expect(with_({ voice: { live: true, target: "auto", engineSet: true, speechReady: false } }).speak)
      .toEqual({ tone: "brass", word: "Speech not set up" });
  });

  it("Speak: On (moss) when the speech model is here", () => {
    expect(with_({ voice: { live: true, target: "auto", engineSet: false, speechReady: true } }).speak)
      .toEqual({ tone: "moss", word: "On" });
  });

  it("Speak: Off when the switch is off", () => {
    expect(with_({ voice: { live: false, target: "auto", speechReady: true } }).speak).toEqual({ tone: "idle", word: "Off" });
  });
});

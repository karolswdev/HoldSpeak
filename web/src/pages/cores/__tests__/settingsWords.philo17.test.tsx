// PHILO-17 U35: Settings reads like an operator console. The words a
// Senior Architect reads first are plain states: the headline says what he
// gets, the rows say who can do what, the back link says where it goes.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PrefStatusBar, hubHeadline, sectionHealth, type SettingsHubWire } from "../settings/prefs";

const hub = (patch: Partial<SettingsHubWire> = {}): SettingsHubWire => ({
  models: { engines: 1, groupsSet: 0, defaultSet: false },
  connections: { connected: 0 },
  voice: { live: false, target: "auto" },
  meetings: { intelligence: true, engineSet: true, engine: "Qwen 27B", summariesOff: false, auto: "every", host: "192.168.1.43" },
  answers: { engineSet: true, engine: "Qwen 27B" },
  rhythm: { loops: 0 },
  sounds: { on: true },
  system: { host: "THIS DEVICE", mesh: false, remote: false },
  posture: "neutral",
  writtenAt: null,
  ...patch,
});

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 503 })));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe("the hub headline is a plain state of what he gets", () => {
  it("names the summary and answer engines", () => {
    expect(hubHeadline(hub())).toEqual({ text: "Summaries: Qwen 27B · Answers: Qwen 27B", warning: false, choose: false });
  });
  it("names the missing engine and offers Choose", () => {
    const h = hubHeadline(hub({ answers: { engineSet: false, engine: null } }));
    expect(h).toEqual({ text: "Summaries: Qwen 27B · Answers: no engine", warning: true, choose: true });
  });
  it("says Summaries: off for the owner's OFF", () => {
    expect(hubHeadline(hub({ meetings: { intelligence: true, engineSet: false, summariesOff: true } })).text)
      .toBe("Summaries: off · Answers: Qwen 27B");
  });
  it("with no assigned job: the Engines rail word keeps the choice, never No engine yet", () => {
    const health = sectionHealth(hub({ meetings: { intelligence: true, engineSet: false }, answers: { engineSet: false } }));
    expect(health.engines).toEqual({ tone: "brass", word: "Choose an engine" });
    expect(health.meetings).toEqual({ tone: "brass", word: "No summary engine" });
  });
  // Astra r1 on #1090: no other ready engine masks these two (no default,
  // no voice engine, no answer engine).
  const bare = { models: { engines: 0, groupsSet: 0, defaultSet: false }, voice: { live: false, target: "auto", engineSet: false } };
  it("the owner's OFF with Answers unknown and nothing else ready: Summaries: off, never No engine yet", () => {
    expect(hubHeadline(hub({ ...bare, meetings: { intelligence: true, engineSet: false, summariesOff: true }, answers: { engineSet: null, engine: null } })))
      .toEqual({ text: "Summaries: off", warning: false, choose: false });
  });
  it("the owner's OFF with no answer engine: Summaries: off · Answers: no engine, and Choose", () => {
    expect(hubHeadline(hub({ ...bare, meetings: { intelligence: true, engineSet: false, summariesOff: true }, answers: { engineSet: false, engine: null } })))
      .toEqual({ text: "Summaries: off · Answers: no engine", warning: true, choose: true });
  });
  it("Answers unknown, summaries on the route only, nothing else ready: names the summary engine, never No engine yet", () => {
    expect(hubHeadline(hub({ ...bare, answers: { engineSet: null, engine: null } })))
      .toEqual({ text: "Summaries: Qwen 27B", warning: false, choose: false });
  });
  it("an unknown answer engine is left out, never called missing", () => {
    expect(hubHeadline(hub({ answers: { engineSet: null, engine: null } })).text).toBe("Summaries: Qwen 27B");
  });
});

describe("the rail says who can reach this hub", () => {
  it("This Mac: This Mac only (was MESH OFF · REMOTE OFF)", () => {
    expect(sectionHealth(hub())["this-mac"]).toEqual({ tone: "idle", word: "This Mac only" });
  });
  it("This Mac: Other devices on (moss) when remote access is on", () => {
    expect(sectionHealth(hub({ system: { host: "THIS DEVICE", mesh: true, remote: true } }))["this-mac"])
      .toEqual({ tone: "moss", word: "Other devices on" });
  });
});

describe("the back link names where it goes", () => {
  it("reads Settings, never PREFS", () => {
    const onBack = vi.fn();
    render(<PrefStatusBar onBack={onBack} receipt={{ saving: false, writtenAt: "", refusal: "" }} />);
    const back = screen.getByRole("button", { name: "Settings" });
    expect(document.body.textContent ?? "").not.toMatch(/PREFS/);
    fireEvent.click(back);
    expect(onBack).toHaveBeenCalled();
  });
});

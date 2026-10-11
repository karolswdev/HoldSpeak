// PHILO-17 U35: Settings reads like an operator console. The words a
// Senior Architect reads first are plain states: the headline says what he
// gets, the rows say who can do what, the back link says where it goes.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PrefsFace, PrefStatusBar, hubHeadline, type SettingsHubWire } from "../settingsPrefs";

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
  it("with no engine for any work: No engine yet, and Choose opens Runs on", () => {
    const onOpen = vi.fn();
    render(
      <PrefsFace
        onOpen={onOpen}
        hub={hub({ meetings: { intelligence: true, engineSet: false }, answers: { engineSet: false } })}
        posture="neutral"
        onPosture={vi.fn()}
        precedence={[]}
      />,
    );
    expect(screen.getByText("No engine yet")).toBeTruthy();
    expect(screen.queryByText("No default model")).toBeNull();
    fireEvent.click(screen.getByTestId("settings-hub-choose"));
    expect(onOpen).toHaveBeenCalledWith("models");
  });
  it("an unknown answer engine is left out, never called missing", () => {
    expect(hubHeadline(hub({ answers: { engineSet: null, engine: null } })).text).toBe("Summaries: Qwen 27B");
  });
});

describe("the hub rows say who can do what", () => {
  it("System: Other devices: off (was MESH OFF · REMOTE OFF)", () => {
    render(<PrefsFace onOpen={vi.fn()} hub={hub()} posture="neutral" onPosture={vi.fn()} precedence={[]} />);
    expect(screen.getByText("Other devices: off")).toBeTruthy();
    expect(document.body.textContent ?? "").not.toMatch(/MESH|REMOTE OFF/);
  });
  it("System: Other devices: on when remote access is on", () => {
    render(<PrefsFace onOpen={vi.fn()} hub={hub({ system: { host: "THIS DEVICE", mesh: true, remote: true } })} posture="neutral" onPosture={vi.fn()} precedence={[]} />);
    expect(screen.getByRole("status", { name: "Other devices: on" })).toBeTruthy();
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

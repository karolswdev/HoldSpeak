/* The Calls app (T2; CALLS-DESIGN-2026-10-28 §6, canvas
 * docs/internal/betterment/canvases/calls-2026-10-28.html).
 *
 * The hub slice is built in parallel, so the answers are the §6 shapes
 * written by hand in desk/calls/__fixtures__/ (each file says so; replace
 * them with recordings when the hub slice lands). Each case drives a press
 * through to the rendered outcome: the idle list, the empty state, a held
 * question decided by Yes, an ended call as a document, the frame that ends
 * a call, Settings ▸ Calls and its write-only passphrase, and a hub without
 * the route (the checklist with every step open). */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { callEnded } from "../calls/__fixtures__/call.ended";
import { callLive } from "../calls/__fixtures__/call.live";
import { callsEmpty } from "../calls/__fixtures__/calls.empty";
import { callsList } from "../calls/__fixtures__/calls.list";
import { frameDecided } from "../calls/__fixtures__/frame.decided";
import { settingsCalls, settingsCallsFresh } from "../calls/__fixtures__/settings.calls";
import { statusNotRunning } from "../calls/__fixtures__/status.notRunning";
import { statusOff } from "../calls/__fixtures__/status.off";
import { statusReady } from "../calls/__fixtures__/status.ready";

type Frame = { type: string; data: unknown };
type Answer = unknown | ((init?: { method?: string; json?: unknown }) => unknown);

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
  apiFetch: vi.fn(),
  openSurfaceOr: vi.fn(),
  openRef: vi.fn(),
}));

vi.mock("../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useOptionalRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));
vi.mock("../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../shell")>()),
  openSurfaceOr: mocks.openSurfaceOr,
}));
vi.mock("../openObject", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../openObject")>()),
  openRef: mocks.openRef,
}));

import { ApiError } from "../../lib/api";
import { CallsCore } from "../calls/CallsWindow";
import { CallsSettingsPane, EGRESS_SENTENCE, INSTALL_COMMAND, RUN_COMMAND, TELNYX_COMMAND } from "../calls/CallsSettings";
import { SETTINGS_SECTIONS } from "../../pages/cores/settingsPrefs";
import { DESK_APPLICATIONS, goRows } from "../applications";

function subscribe(type: string, listener: (frame: Frame) => void) {
  const set = mocks.listeners.get(type) ?? new Set<(frame: Frame) => void>();
  set.add(listener);
  mocks.listeners.set(type, set);
  return () => set.delete(listener);
}
function emit(type: string, data: unknown) {
  act(() => {
    for (const listener of [...(mocks.listeners.get(type) ?? [])]) listener({ type, data });
  });
}

const clone = <T,>(value: T): T => structuredClone(value);
let calls: string[];

/** Answer each `METHOD path` from the table; a path it does not hold is a
 *  404, as on a hub without the route. */
function hub(table: Record<string, Answer>) {
  mocks.apiFetch.mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
    const key = `${(init?.method ?? "GET").toUpperCase()} ${path}`;
    calls.push(init?.json !== undefined ? `${key} ${JSON.stringify(init.json)}` : key);
    if (!(key in table)) throw new ApiError(404, "Not Found", { detail: "Not Found" });
    const answer = table[key];
    return clone(typeof answer === "function" ? (answer as (i?: typeof init) => unknown)(init) : answer);
  });
}

beforeEach(() => {
  calls = [];
  mocks.listeners.clear();
  mocks.apiFetch.mockReset();
  mocks.openSurfaceOr.mockReset();
  mocks.openRef.mockReset();
});
afterEach(() => cleanup());

const status = () => screen.getByTestId("calls-status").textContent ?? "";

describe("the Calls window is in the manifest", () => {
  it("Go ▸ Work ▸ Calls opens surface-calls at 720 x 520; Settings has a Calls section", () => {
    const app = DESK_APPLICATIONS.find((entry) => entry.action === "open-calls");
    expect(app?.windowId).toBe("surface-calls");
    expect(app?.surface).toMatchObject({ defaultW: 720, defaultH: 520 });
    expect(goRows("work").some((row) => row.kind === "app" && row.app.action === "open-calls")).toBe(true);
    expect(SETTINGS_SECTIONS.map((section) => section.id)).toContain("calls");
  });
});

describe("idle: the past calls", () => {
  it("draws a dense list, Call me as the primary, and Ready for calls", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": statusReady,
      "GET /api/calls": callsList,
    });
    render(<CallsCore />);
    const rows = await screen.findAllByTestId("calls-row");
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toContain("“What is on my plate tomorrow?”");
    expect(rows[0].textContent).toContain("You");
    expect(rows[0].textContent).toContain("1:12");
    expect(within(rows[0]).getByTestId("calls-outcome").textContent).toContain("Done");
    expect(within(rows[1]).getByTestId("calls-outcome").textContent).toContain("No answer");
    const callMe = screen.getByTestId("calls-call-me");
    expect(callMe.className).toContain("btn--primary");
    expect(callMe).not.toBeDisabled();
    expect(status()).toContain("Ready for calls");
    expect(status()).toContain("2 calls");
    // No host, number or engine chip on the window (A.9).
    expect(screen.getByTestId("calls-window").textContent).not.toMatch(/qwen|100\.118|tailscale|sip:/i);
  });

  it("empty: one object, one line, one verb, never a zero", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": statusReady,
      "GET /api/calls": callsEmpty,
      "POST /api/calls/place": { ...callLive, transcript: undefined, state: "ringing", hold: null, results: [] },
    });
    render(<CallsCore />);
    expect(await screen.findByText("No calls yet")).toBeInTheDocument();
    expect(screen.getByText("Call me rings your number and HoldSpeak answers.")).toBeInTheDocument();
    expect(status()).not.toMatch(/\b0\b/);
    const verbs = screen.getAllByRole("button", { name: /Call me/ });
    expect(verbs.length).toBe(2);
    fireEvent.click(verbs[1]);
    await waitFor(() => expect(calls).toContain("POST /api/calls/place {}"));
    expect(await screen.findByTestId("calls-hangup")).toBeInTheDocument();
    expect(status()).toContain("On a call");
  });

  it("the daemon down says ai-phone not running", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": statusNotRunning,
      "GET /api/calls": callsList,
    });
    render(<CallsCore />);
    await screen.findAllByTestId("calls-row");
    expect(status()).toContain("ai-phone not running");
    expect(screen.getByTestId("calls-call-me")).toBeDisabled();
  });
});

describe("on a call", () => {
  it("the transcript as a document; the held question decided by Yes; the row settles into Done", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": { ...statusReady, active: { ...callLive, transcript: undefined } },
      "GET /api/calls": { calls: [callLive, ...callsList.calls] },
      "GET /api/calls/c9b1e0": callLive,
      "POST /api/calls/c9b1e0/decide": () => ({ ...frameDecided.call, transcript: undefined }),
    });
    render(<CallsCore />);
    const lines = await screen.findAllByTestId("live-transcript-line");
    expect(lines).toHaveLength(callLive.transcript.length);
    expect(lines[0].getAttribute("data-who")).toBe("holdspeak");
    expect(lines[1].getAttribute("data-who")).toBe("caller");
    expect(lines[1].textContent).toContain("0:05");
    expect(screen.getByTestId("calls-hangup").className).toContain("btn--danger");
    expect(screen.queryByTestId("calls-call-me")).toBeNull();
    expect(status()).toMatch(/On a call.*\d+:\d\d/);
    expect(status()).toContain("Waiting for your answer");

    const hold = screen.getByTestId("calls-hold");
    expect(hold.textContent).toContain("Send Runbook reminder to Platform channel");
    fireEvent.click(within(hold).getByRole("button", { name: "Yes" }));
    await waitFor(() => expect(calls).toContain('POST /api/calls/c9b1e0/decide {"decision":"approve"}'));
    await waitFor(() => expect(screen.queryByTestId("calls-hold")).toBeNull());
    const done = screen.getAllByTestId("calls-result").map((row) => row.textContent);
    expect(done).toContain("Runbook reminder to Platform channelSent on your yes");
    // The transcript stays after the decide (the answer is a summary).
    expect(screen.getAllByTestId("live-transcript-line")).toHaveLength(callLive.transcript.length);
    expect(status()).not.toContain("Waiting for your answer");
  });

  it("No denies; a result row opens its object", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": { ...statusReady, active: { ...callLive, transcript: undefined } },
      "GET /api/calls": { calls: [] },
      "GET /api/calls/c9b1e0": callLive,
      "POST /api/calls/c9b1e0/decide": { ...callLive, hold: null, transcript: undefined },
    });
    render(<CallsCore />);
    fireEvent.click(await screen.findByTestId("calls-no"));
    await waitFor(() => expect(calls).toContain('POST /api/calls/c9b1e0/decide {"decision":"deny"}'));
    fireEvent.click(screen.getAllByTestId("calls-result")[0]);
    expect(mocks.openRef).toHaveBeenCalledWith("note:priya-prep");
  });

  it("the call_state frame that ends the call leaves the call as a document with its note", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": { ...statusReady, active: { ...callLive, transcript: undefined } },
      "GET /api/calls": { calls: [] },
      "GET /api/calls/c9b1e0": callLive,
    });
    render(<CallsCore />);
    await screen.findByTestId("calls-hangup");
    emit("call_state", {
      reason: "ended",
      call: { ...frameDecided.call, state: "ended", ended_at: "2026-10-28T09:12:31Z", duration_sec: 31, note_ref: "note:call-c9b1e0", outcome: "done" },
    });
    expect(await screen.findByTestId("calls-call-me")).toBeInTheDocument();
    expect(screen.queryByTestId("calls-hangup")).toBeNull();
    expect(status()).toContain("Call ended");
    expect(status()).toContain("0:31");
    fireEvent.click(screen.getByTestId("calls-transcript-note"));
    expect(mocks.openRef).toHaveBeenCalledWith("note:call-c9b1e0");
    fireEvent.click(screen.getByTestId("calls-back"));
    expect(await screen.findAllByTestId("calls-row")).toHaveLength(1);
  });
});

describe("an ended call opens as a document", () => {
  it("a press on a past call reads it; its transcript, its results, Open note", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": statusReady,
      "GET /api/calls": callsList,
      "GET /api/calls/c7a2f1": callEnded,
    });
    render(<CallsCore />);
    const rows = await screen.findAllByTestId("calls-row");
    fireEvent.click(rows[0].querySelector(".object-list-open") ?? rows[0], { detail: 1 });
    await waitFor(() => expect(calls).toContain("GET /api/calls/c7a2f1"));
    expect(await screen.findAllByTestId("live-transcript-line")).toHaveLength(callEnded.transcript.length);
    expect(screen.queryByTestId("live-listening")).toBeNull();
    expect(screen.getAllByTestId("calls-result").map((row) => row.textContent)).toEqual([
      "Tomorrow: three meetings, two reviewsWrote",
      "Runbook reminder to Platform channelSent on your yes",
    ]);
    fireEvent.click(screen.getByTestId("calls-open-note"));
    expect(mocks.openRef).toHaveBeenCalledWith("note:call-c7a2f1");
    expect(status()).toContain("Call ended");
  });
});

describe("a hub without the Calls slice", () => {
  it("the window says Calls are off and its link opens Settings ▸ Calls; no status read", async () => {
    hub({ "GET /api/settings": { _revision: "r1" } });
    render(<CallsCore />);
    const link = await screen.findByTestId("calls-open-settings");
    expect(status()).toContain("Calls are off");
    fireEvent.click(link);
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "calls");
    expect(calls).toEqual(["GET /api/settings"]);
  });
});

describe("Settings ▸ Calls", () => {
  it("renders every step in order with its command, the engine row, the egress sentence", async () => {
    hub({ "GET /api/settings": { calls: settingsCallsFresh }, "GET /api/calls/status": statusOff });
    render(<CallsSettingsPane />);
    const steps = await screen.findByTestId("calls-steps");
    await waitFor(() => expect(within(steps).getByTestId("calls-step-state-install").textContent).toBe("Not installed"));
    const order = [...steps.querySelectorAll("[data-step]")].map((node) => node.getAttribute("data-step"));
    expect(order).toEqual(["install", "daemon", "line", "engine", "passphrase", "numbers", "enable"]);
    expect(screen.getByText(INSTALL_COMMAND)).toBeInTheDocument();
    expect(screen.getByText(RUN_COMMAND)).toBeInTheDocument();
    expect(screen.getByText(TELNYX_COMMAND)).toBeInTheDocument();
    expect(within(screen.getByTestId("calls-engine")).getByText("qwen3.8-27b")).toBeInTheDocument();
    expect(screen.getByTestId("calls-egress").textContent).toBe(EGRESS_SENTENCE);
    expect(screen.getAllByRole("button", { name: "Copy" }).length).toBeGreaterThanOrEqual(4);
  });

  it("writes the passphrase as write only: the field clears and shows Set, never the value", async () => {
    hub({
      "GET /api/settings": { calls: settingsCallsFresh },
      "GET /api/calls/status": statusOff,
      "PUT /api/settings": { settings: { calls: { ...settingsCallsFresh, passphrase_set: true } } },
    });
    render(<CallsSettingsPane />);
    const field = await screen.findByLabelText("Passphrase");
    expect(field.getAttribute("type")).toBe("password");
    fireEvent.change(field, { target: { value: "blue heron" } });
    fireEvent.click(screen.getByTestId("calls-passphrase-save"));
    await waitFor(() => expect(calls).toContain('PUT /api/settings {"calls":{"passphrase":"blue heron"}}'));
    expect(await screen.findByTestId("calls-passphrase-set")).toHaveTextContent("Set");
    expect(screen.queryByLabelText("Passphrase")).toBeNull();
    expect(document.body.innerHTML).not.toContain("blue heron");
  });

  it("the switch and a number write the calls section", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": statusReady,
      "PUT /api/settings": (init?: { json?: unknown }) => ({ settings: { calls: { ...settingsCalls, ...((init?.json as { calls: object }).calls) } } }),
    });
    render(<CallsSettingsPane />);
    expect((await screen.findAllByTestId("calls-number"))[0].textContent).toContain("Call me rings this number");
    fireEvent.click(screen.getByRole("checkbox", { name: "Calls on" }));
    await waitFor(() => expect(calls).toContain('PUT /api/settings {"calls":{"enabled":false}}'));
    fireEvent.change(screen.getByLabelText("Add a number"), { target: { value: "+15550100199" } });
    fireEvent.click(screen.getByTestId("calls-number-add"));
    await waitFor(() => expect(calls).toContain('PUT /api/settings {"calls":{"allowed_numbers":["+15550100142","+15550100199"]}}'));
  });

  it("a status read that 404s draws the checklist with every step open", async () => {
    hub({ "GET /api/settings": { calls: settingsCallsFresh } });
    render(<CallsSettingsPane />);
    const steps = await screen.findByTestId("calls-steps");
    await waitFor(() => expect(calls).toContain("GET /api/calls/status"));
    for (const id of ["install", "daemon", "line", "engine", "passphrase", "enable"]) {
      expect(within(steps).getByTestId(`calls-step-${id}`).hasAttribute("data-done"), id).toBe(false);
    }
    expect(screen.getByText(INSTALL_COMMAND)).toBeInTheDocument();
  });

  it("a hub without the calls section: every step open, no status read", async () => {
    hub({ "GET /api/settings": { _revision: "r1" } });
    render(<CallsSettingsPane />);
    const steps = await screen.findByTestId("calls-steps");
    await waitFor(() => expect(screen.getByTestId("calls-settings").getAttribute("aria-busy")).toBeNull());
    expect(steps.querySelectorAll("[data-done]")).toHaveLength(0);
    expect(calls).toEqual(["GET /api/settings"]);
  });
});

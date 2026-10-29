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
import { CallsSettingsPane, EGRESS_SENTENCE, INSTALL_COMMAND, RUN_COMMAND, TELNYX_COMMAND, TWILIO_COMMAND } from "../calls/CallsSettings";
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
    // W6-A (atlas pass 3, defects 14, 15): Twilio is its own code block
    // with its own Copy, whole (no "…"); the number field's placeholder
    // cannot read as a saved number.
    for (const command of [TELNYX_COMMAND, TWILIO_COMMAND]) {
      const code = screen.getByText(command);
      expect(code.tagName).toBe("CODE");
      expect(within(code.parentElement as HTMLElement).getByRole("button", { name: "Copy" })).toBeInTheDocument();
    }
    expect(TWILIO_COMMAND).not.toContain("…");
    const number = screen.getByLabelText("Add a number") as HTMLInputElement;
    expect(number.placeholder).toBe("Your mobile number");
    expect(number.placeholder).not.toMatch(/\d/);
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

/** DELIGHT slice 4 (2026-10-28): the Calls window in the delight system. */
describe("DELIGHT slice 4: the Calls window", () => {
  const motion = (allowed: boolean) => {
    const real = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: allowed && query.includes("no-preference"),
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    })) as typeof window.matchMedia;
    return () => { window.matchMedia = real; };
  };

  it("wears its own object: the desk telephone in the title bar, the empty state and every row", async () => {
    const app = DESK_APPLICATIONS.find((entry) => entry.action === "open-calls");
    expect(app?.surface?.sprite).toBe("call");
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": statusReady,
      "GET /api/calls": callsEmpty,
    });
    const { container, unmount } = render(<CallsCore />);
    await screen.findByText("No calls yet");
    const seat = container.querySelector(".surface-state-object");
    expect(seat?.getAttribute("data-kind")).toBe("call");
    expect(seat?.querySelector("img")?.getAttribute("src")).toMatch(/\/call\.png$/);
    unmount();

    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": statusReady,
      "GET /api/calls": callsList,
    });
    render(<CallsCore />);
    const rows = await screen.findAllByTestId("calls-row");
    expect(rows.map((row) => row.getAttribute("data-kind"))).toEqual(["call", "call"]);
    expect(rows[0].querySelector("img")?.getAttribute("src")).toMatch(/\/call\.png$/);
  });

  it("on a call the status lamp is live (it glows and breathes); the clock counts without a fade", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": { ...statusReady, active: { ...callLive, transcript: undefined } },
      "GET /api/calls": { calls: [] },
      "GET /api/calls/c9b1e0": callLive,
    });
    render(<CallsCore />);
    await screen.findByTestId("calls-hangup");
    const lamp = screen.getByTestId("calls-status-live").querySelector(".kit-dot");
    expect(lamp?.getAttribute("data-tone")).toBe("fail");
    expect(lamp?.hasAttribute("data-live")).toBe(true);
    expect(screen.getByTestId("calls-clock").querySelector(".kit-tick")).toBeNull();
  });

  it("Ready for calls is a lit lamp, not a live one", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": statusReady,
      "GET /api/calls": callsList,
    });
    render(<CallsCore />);
    await screen.findAllByTestId("calls-row");
    const lamp = screen.getByTestId("calls-status-ready").querySelector(".kit-dot");
    expect(lamp?.getAttribute("data-tone")).toBe("ok");
    expect(lamp?.hasAttribute("data-live")).toBe(false);
  });

  it("Yes settles the held row out in green, then the call reads on without it", async () => {
    const restore = motion(true);
    try {
      hub({
        "GET /api/settings": { calls: settingsCalls },
        "GET /api/calls/status": { ...statusReady, active: { ...callLive, transcript: undefined } },
        "GET /api/calls": { calls: [] },
        "GET /api/calls/c9b1e0": callLive,
        "POST /api/calls/c9b1e0/decide": () => ({ ...frameDecided.call, transcript: undefined }),
      });
      render(<CallsCore />);
      fireEvent.click(await screen.findByTestId("calls-yes"));
      await waitFor(() => expect(screen.getByTestId("calls-hold").getAttribute("data-settle")).toBe("yes"));
      // While it settles the verbs keep their words (no spinner in a fading row).
      expect(screen.getByTestId("calls-yes").getAttribute("aria-busy")).not.toBe("true");
      await waitFor(() => expect(screen.queryByTestId("calls-hold")).toBeNull());
      expect(screen.getAllByTestId("calls-result").map((row) => row.textContent)).toContain("Runbook reminder to Platform channelSent on your yes");
    } finally {
      restore();
    }
  });

  it("No settles the held row out in the quiet rule; under reduced motion nothing settles", async () => {
    const restore = motion(true);
    try {
      hub({
        "GET /api/settings": { calls: settingsCalls },
        "GET /api/calls/status": { ...statusReady, active: { ...callLive, transcript: undefined } },
        "GET /api/calls": { calls: [] },
        "GET /api/calls/c9b1e0": callLive,
        "POST /api/calls/c9b1e0/decide": { ...callLive, hold: null, transcript: undefined },
      });
      render(<CallsCore />);
      fireEvent.click(await screen.findByTestId("calls-no"));
      await waitFor(() => expect(screen.getByTestId("calls-hold").getAttribute("data-settle")).toBe("no"));
      await waitFor(() => expect(screen.queryByTestId("calls-hold")).toBeNull());
    } finally {
      restore();
    }
    cleanup();
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": { ...statusReady, active: { ...callLive, transcript: undefined } },
      "GET /api/calls": { calls: [] },
      "GET /api/calls/c9b1e0": callLive,
      "POST /api/calls/c9b1e0/decide": { ...callLive, hold: null, transcript: undefined },
    });
    render(<CallsCore />);
    const hold = await screen.findByTestId("calls-hold");
    fireEvent.click(screen.getByTestId("calls-no"));
    await waitFor(() => expect(screen.queryByTestId("calls-hold")).toBeNull());
    expect(hold.hasAttribute("data-settle")).toBe(false);
  });

  it("a result wears its kind: the row names data-kind for its hue", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": statusReady,
      "GET /api/calls": callsList,
      "GET /api/calls/c7a2f1": callEnded,
    });
    render(<CallsCore />);
    const rows = await screen.findAllByTestId("calls-row");
    fireEvent.click(rows[0].querySelector(".object-list-open") ?? rows[0], { detail: 1 });
    const results = await screen.findAllByTestId("calls-result");
    expect(results.every((row) => row.getAttribute("data-kind"))).toBe(true);
    expect(screen.getByTestId("calls-transcript-note").getAttribute("data-kind")).toBe("note");
  });

  it("the body fades up once per phase: the list replaces the read with a new body; a live call does not", async () => {
    hub({
      "GET /api/settings": { calls: settingsCalls },
      "GET /api/calls/status": statusReady,
      "GET /api/calls": callsList,
    });
    const { container } = render(<CallsCore />);
    await screen.findAllByTestId("calls-row");
    expect(container.querySelector(".calls-body")?.getAttribute("data-phase")).toBe("list");
  });

  it("Settings ▸ Calls: the dots turn only after the first read (data-turns)", async () => {
    hub({ "GET /api/settings": { calls: settingsCallsFresh }, "GET /api/calls/status": statusOff });
    render(<CallsSettingsPane />);
    const pane = await screen.findByTestId("calls-settings");
    await waitFor(() => expect(pane.getAttribute("aria-busy")).toBeNull());
    await waitFor(() => expect(pane.hasAttribute("data-turns")).toBe(true));
    expect(within(pane).getByTestId("calls-step-state-install").classList.contains("kit-dotword")).toBe(true);
  });
});

/* ── Phone (PHONE-DESIGN-2026-10-28 §9, canvas betterment/phone/canvases/
   phone-2026-10-28.html, direction A: the Phone wing of the Calls window).
   Every answer is a RECORDED hub answer (desk/calls/__fixtures__/phone.*.json,
   recorded through the real routes by PH-HUB); the answer to a press is the
   recorded state with the hub's change applied. ── */
import phoneStatus from "../calls/__fixtures__/phone.settings.json";
import phoneThread from "../calls/__fixtures__/phone.thread.json";
import phoneCalls from "../calls/__fixtures__/phone.calls.json";
import phonePair from "../calls/__fixtures__/phone.pair.json";
import needsPhone from "../calls/__fixtures__/needs_you.phone.json";
import { WingSlotContext } from "../surface/wings";
import { PhoneSettingsPane } from "../calls/PhoneSettings";
import { usePhoneFocus } from "../calls/phoneFocus";
import { phoneTodayLine } from "../calls/phoneApi";
import type { PhoneMessage, PhoneStatus } from "../calls/phoneTypes";
import { needFace } from "../needs/needsFace";
import { useState, type ReactNode } from "react";

const P = {
  status: phoneStatus as unknown as PhoneStatus,
  messages: (phoneThread as { messages: PhoneMessage[] }).messages,
  calls: phoneCalls.calls,
};
const lastSeq = Math.max(...P.messages.map((m) => m.seq));

/** The window head: the wings a core publishes, drawn above it. */
function Hosted({ children }: { children: ReactNode }) {
  const [head, setHead] = useState<ReactNode>(null);
  return (
    <WingSlotContext.Provider value={setHead}>
      <div data-testid="head">{head}</div>
      {children}
    </WingSlotContext.Provider>
  );
}

/** The calls section of a hub whose phone is on (`phone_on`, read only). */
const phoneOn = { calls: { ...settingsCalls, phone_on: true } };

function phoneHub(extra: Record<string, Answer> = {}) {
  hub({
    "GET /api/settings": phoneOn,
    "GET /api/calls/status": statusReady,
    "GET /api/calls": callsList,
    "GET /api/phone/status": P.status,
    "GET /api/phone/messages?after_seq=0": phoneThread,
    "GET /api/phone/calls": phoneCalls,
    [`GET /api/phone/messages?after_seq=${lastSeq}`]: { messages: [], last_seq: lastSeq },
    ...extra,
  });
}

async function openPhone() {
  render(<Hosted><CallsCore /></Hosted>);
  await screen.findAllByTestId("calls-row");
  fireEvent.click(within(screen.getByTestId("head")).getByRole("tab", { name: "Phone" }));
  return screen.findByTestId("phone-wing");
}
const line = (id: string) => screen.getAllByTestId("phone-message").find((row) => row.getAttribute("data-message") === id)!;
const callLine = (id: string) => screen.getAllByTestId("phone-call").find((row) => row.getAttribute("data-call") === id)!;

describe("Phone: the wing of the Calls window", () => {
  beforeEach(() => usePhoneFocus.setState({ pending: false, replyTo: null, callId: null }));

  it("the head carries Calls · Phone; Phone draws the recorded thread, the desk calls and the paired phone", async () => {
    phoneHub();
    await openPhone();
    expect(screen.getAllByTestId("phone-message")).toHaveLength(P.messages.length);
    // His reply sits under the line it answers.
    const reply = P.messages.find((m) => m.reply_to)!;
    expect(line(reply.id).hasAttribute("data-reply")).toBe(true);
    const order = screen.getAllByTestId("phone-message").map((row) => row.getAttribute("data-message"));
    expect(order.indexOf(reply.id)).toBe(order.indexOf(reply.reply_to!) + 1);
    // The read line says Read; the agent's ask and the missed call's line wait (ember).
    expect(within(line(reply.reply_to!)).getByTestId("phone-receipt").textContent).toBe("Read");
    const agentAsk = P.messages.find((m) => String(m.origin_ref).startsWith("agent:"))!;
    expect(line(agentAsk.id).hasAttribute("data-waits")).toBe(true);
    expect(within(line(agentAsk.id)).getByTestId("phone-receipt").textContent).toBe("Delivered");
    expect(within(line(agentAsk.id)).getByTestId("phone-message-origin").textContent).toBe("an agent");
    // The three desk calls, each its state in a word.
    const words = Object.fromEntries(P.calls.map((call) => [call.state, within(callLine(call.id)).getByTestId("phone-call-state").textContent]));
    expect(words).toMatchObject({ held: "Waits for your yes", missed: "Missed", ended: "Answered · 0:00" });
    expect(screen.getByTestId("phone-device").textContent).toContain(P.status.devices[0].name);
    expect(status()).toContain("2 replies are waiting on you");
    expect(status()).toContain("3 calls from the desk");
    // No host, number or engine chip on the window (A.9).
    expect(screen.getByTestId("calls-window").textContent).not.toMatch(/tail\d|ts\.net|hub_/i);
  });

  it("Send writes the line to the phone and the thread reads on from the last seq", async () => {
    const sent = { id: "msg_new", seq: lastSeq + 1, direction: "to_phone", text: "Back at 10.", created_at: new Date().toISOString() };
    phoneHub({
      "POST /api/phone/messages": { msg_id: "msg_new" },
      [`GET /api/phone/messages?after_seq=${lastSeq}`]: { messages: [sent], last_seq: lastSeq + 1 },
    });
    await openPhone();
    fireEvent.change(screen.getByLabelText("Message your phone"), { target: { value: "Back at 10." } });
    fireEvent.click(screen.getByTestId("phone-send"));
    await waitFor(() => expect(calls).toContain('POST /api/phone/messages {"text":"Back at 10."}'));
    await waitFor(() => expect(line("msg_new")).toBeTruthy());
    expect(within(line("msg_new")).getByTestId("phone-receipt").textContent).toBe("Sent");
    expect((screen.getByLabelText("Message your phone") as HTMLTextAreaElement).value).toBe("");
  });

  it("Reply on his line threads the answer under it (reply_to)", async () => {
    phoneHub({ "POST /api/phone/messages": { msg_id: "msg_r" } });
    await openPhone();
    const his = P.messages.find((m) => m.direction === "from_phone")!;
    fireEvent.click(within(line(his.id)).getByTestId("phone-reply"));
    expect(screen.getByTestId("phone-replying").textContent).toContain(his.text);
    fireEvent.change(screen.getByLabelText("Message your phone"), { target: { value: "Done." } });
    fireEvent.click(screen.getByTestId("phone-send"));
    await waitFor(() => expect(calls).toContain(`POST /api/phone/messages {"text":"Done.","reply_to":"${his.id}"}`));
    await waitFor(() => expect(screen.queryByTestId("phone-replying")).toBeNull());
  });

  it("a missed call: Call again presses the hub's again verb and the line reads Ringing", async () => {
    const missed = P.calls.find((call) => call.state === "missed")!;
    let pressed = false;
    phoneHub({
      [`POST /api/phone/calls/${missed.id}/again`]: () => { pressed = true; return { call_id: missed.id, state: "ringing" }; },
      "GET /api/phone/calls": () => ({ calls: P.calls.map((call) => call.id === missed.id && pressed ? { ...call, state: "ringing" } : call) }),
    });
    await openPhone();
    fireEvent.click(within(callLine(missed.id)).getByTestId("phone-call-again"));
    await waitFor(() => expect(calls).toContain(`POST /api/phone/calls/${missed.id}/again {}`));
    await waitFor(() => expect(within(callLine(missed.id)).getByTestId("phone-call-state").textContent).toBe("Ringing"));
  });

  it("a held call (an agent asks to call you): Call now rings it through the hub", async () => {
    const held = P.calls.find((call) => call.state === "held")!;
    phoneHub({ [`POST /api/phone/calls/${held.id}/ring`]: { call_id: held.id, state: "ringing" } });
    await openPhone();
    expect(within(callLine(held.id)).getByTestId("phone-call-state").closest("[data-tone]")?.getAttribute("data-tone")).toBe("ask");
    fireEvent.click(within(callLine(held.id)).getByTestId("phone-call-ring"));
    await waitFor(() => expect(calls).toContain(`POST /api/phone/calls/${held.id}/ring {}`));
  });

  it("a desk call by number opens its Calls call as a document (Open transcript)", async () => {
    const ended = { ...P.calls.find((call) => call.state === "ended")!, transport: "number", transcript_ref: "call:c7a2f1" };
    phoneHub({
      "GET /api/phone/calls": { calls: P.calls.map((call) => call.id === ended.id ? ended : call) },
      "GET /api/calls/c7a2f1": callEnded,
    });
    await openPhone();
    fireEvent.click(within(callLine(ended.id)).getByTestId("phone-open-transcript"));
    expect(await screen.findByTestId("calls-document")).toBeInTheDocument();
  });

  it("a phone_changed frame reads the thread on from the last seq: his reply arrives and is marked read", async () => {
    const reply = { id: "msg_frame", seq: lastSeq + 1, direction: "from_phone", text: "main.", reply_to: P.messages.find((m) => String(m.origin_ref).startsWith("agent:"))!.id,
      created_at: new Date().toISOString() };
    phoneHub({
      [`GET /api/phone/messages?after_seq=${lastSeq}`]: { messages: [reply], last_seq: lastSeq + 1 },
      "POST /api/phone/messages/msg_frame/read": { ok: true },
    });
    await openPhone();
    emit("phone_changed", { kind: "message", id: "msg_frame", state: "new" });
    await waitFor(() => expect(line("msg_frame")).toBeTruthy());
    expect(line("msg_frame").hasAttribute("data-reply")).toBe(true);
    await waitFor(() => expect(calls).toContain("POST /api/phone/messages/msg_frame/read {}"));
    // The agent's ask has its reply now: one line still waits.
    await waitFor(() => expect(status()).toContain("A reply is waiting on you"));
  });

  it("no phone and no number: one object, one line, Pair a phone opens Settings ▸ Calls", async () => {
    phoneHub({
      "GET /api/phone/status": { ...P.status, devices: [] },
      "GET /api/phone/messages?after_seq=0": { messages: [], last_seq: 0 },
      "GET /api/phone/calls": { calls: [] },
    });
    render(<Hosted><CallsCore /></Hosted>);
    await screen.findAllByTestId("calls-row");
    fireEvent.click(within(screen.getByTestId("head")).getByRole("tab", { name: "Phone" }));
    expect(await screen.findByText("No phone yet")).toBeInTheDocument();
    expect(screen.getByText("Pair a phone, or add a number in Calls, and the desk can reach you.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Pair a phone/ }));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "calls");
    expect(status()).not.toMatch(/\b0\b/);
  });

  it("a hub without the Phone slice draws No phone yet and reads nothing more", async () => {
    hub({ "GET /api/settings": { calls: settingsCalls }, "GET /api/calls/status": statusReady, "GET /api/calls": callsList });
    render(<Hosted><CallsCore /></Hosted>);
    await screen.findAllByTestId("calls-row");
    fireEvent.click(within(screen.getByTestId("head")).getByRole("tab", { name: "Phone" }));
    expect(await screen.findByText("No phone yet")).toBeInTheDocument();
    // phone_on is not in the calls section: no /api/phone route is read.
    expect(calls.filter((call) => call.includes("/api/phone/"))).toEqual([]);
  });

  it("Answer here (the one-shot ask) opens the window on the Phone wing with the reply set", async () => {
    phoneHub();
    const ask = P.messages.find((m) => String(m.origin_ref).startsWith("phone_call:"))!;
    usePhoneFocus.getState().open(ask.id);
    render(<Hosted><CallsCore /></Hosted>);
    await screen.findByTestId("phone-wing");
    expect(screen.getByTestId("phone-replying").textContent).toContain(ask.text);
    expect(usePhoneFocus.getState().pending).toBe(false);
  });
});

describe("Settings ▸ Calls ▸ Phone", () => {
  it("the recorded status: the paired phone with Remove, Reach you by the level, Rhythm's quiet hours, the line, egress once", async () => {
    hub({ "GET /api/settings": phoneOn, "GET /api/phone/status": P.status, [`DELETE /api/phone/devices/${P.status.devices[0].id}`]: { ok: true } });
    render(<PhoneSettingsPane />);
    const row = await screen.findByTestId("phone-device-row");
    expect(row.textContent).toContain(P.status.devices[0].name);
    expect(row.textContent).toMatch(/Paired \d+ Oct/);
    const reach = screen.getAllByTestId("phone-reach-row");
    expect(reach.map((r) => r.getAttribute("data-kind"))).toEqual(Object.keys(P.status.reach));
    for (const r of reach) expect(r.getAttribute("data-channel")).toBe(P.status.reach[r.getAttribute("data-kind")!].level_word);
    expect(screen.getByTestId("phone-reach-level").textContent).toBe("Set by Control: YOLO");
    expect(screen.queryByTestId("phone-reach-reset")).toBeNull();
    expect(screen.getByTestId("phone-quiet").textContent).toContain("22:00 to 08:00");
    fireEvent.click(screen.getByTestId("phone-quiet-rhythm"));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "rhythm");
    expect(screen.getByTestId("phone-number").textContent).toContain(P.status.line.words);
    expect(screen.getAllByTestId("phone-egress")).toHaveLength(1);
    fireEvent.click(screen.getByTestId("phone-device-remove"));
    await waitFor(() => expect(calls).toContain(`DELETE /api/phone/devices/${P.status.devices[0].id}`));
  });

  it("Pair a phone draws the QR from the recorded pair payload in place; a device frame that pairs it closes the sheet", async () => {
    let paired = false;
    hub({
      "GET /api/settings": phoneOn,
      "GET /api/phone/status": () => (paired ? P.status : { ...P.status, devices: [] }),
      "POST /api/phone/pair": phonePair,
    });
    render(<PhoneSettingsPane />);
    fireEvent.click(await screen.findByTestId("phone-pair"));
    const sheet = await screen.findByTestId("phone-pair-sheet");
    expect(phonePair.qr_png_base64).toBeNull();
    const qr = within(sheet).getByTestId("phone-qr");
    expect(qr.getAttribute("data-qr")).toBe(phonePair.qr_payload);
    expect(qr.querySelector("path")?.getAttribute("d")?.length ?? 0).toBeGreaterThan(500);
    expect(within(sheet).getByTestId("phone-pair-left").textContent).toMatch(/Good for \d+ more minutes?|This code is too old/);
    paired = true;
    emit("phone_changed", { kind: "device", id: P.status.devices[0].id, state: "paired" });
    await waitFor(() => expect(screen.queryByTestId("phone-pair-sheet")).toBeNull());
    expect(screen.getByTestId("phone-device-row")).toBeInTheDocument();
  });

  it("a Reach you choice writes his own word over the level; Use the YOLO set clears it", async () => {
    let own: Record<string, string> = {};
    const withOwn = () => ({ ...P.status, reach: Object.fromEntries(Object.entries(P.status.reach).map(([kind, choice]) =>
      [kind, own[kind] ? { ...choice, word: own[kind], own: true } : choice])) });
    hub({
      "GET /api/settings": phoneOn,
      "GET /api/phone/status": withOwn,
      "PUT /api/settings": (init?: { json?: unknown }) => { own = (init?.json as { calls: { phone_reach: Record<string, string> } }).calls.phone_reach; return {}; },
    });
    render(<PhoneSettingsPane />);
    const row = (await screen.findAllByTestId("phone-reach-row")).find((r) => r.getAttribute("data-kind") === "program_done")!;
    fireEvent.click(within(row).getByLabelText("Nothing"));
    await waitFor(() => expect(calls).toContain('PUT /api/settings {"calls":{"phone_reach":{"program_done":"nothing"}}}'));
    await waitFor(() => expect(row.getAttribute("data-channel")).toBe("nothing"));
    expect(screen.getByTestId("phone-reach-level").textContent).toBe("Your choices over Control: YOLO");
    fireEvent.click(screen.getByTestId("phone-reach-reset"));
    await waitFor(() => expect(calls).toContain('PUT /api/settings {"calls":{"phone_reach":{}}}'));
    await waitFor(() => expect(row.getAttribute("data-channel")).toBe("message"));
  });
});

describe("Phone on Today", () => {
  it("the recorded day reads Reached you 3 times: 1 answered; a day without a reach says nothing", () => {
    expect(phoneTodayLine(P.status)).toBe("Reached you 3 times: 1 answered");
    expect(phoneTodayLine({ ...P.status, today: { reaches: 0, calls: 0, answered: 0 } })).toBe("");
    expect(phoneTodayLine(null)).toBe("");
  });
});

describe("Phone in Needs you (the recorded phone_items)", () => {
  const items = (needsPhone as { items: Array<Record<string, unknown>> }).items;
  const face = (kind: string) => {
    const item = items.find((entry) => (entry.phone as { kind: string }).kind === kind)!;
    return { item, face: needFace({ ref: String(item.ref), kind: "attention", item } as never, { now: new Date(), sessions: [], flights: [] } as never) };
  };
  it("asked: the hub's line, Call now / Let it wait", () => {
    const { item, face: f } = face("asked");
    expect(f.name).toBe(item.title);
    expect(f.fact).toBe("Asked on your phone · now · no reply");
    expect(f.verbs).toMatchObject({ kind: "phone", item: "asked" });
    expect((f.verbs as { verbs: Array<{ label: string }> }).verbs.map((v) => v.label)).toEqual(["Call now", "Let it wait"]);
  });
  it("a missed call: Call again / Answer here (needs his words)", () => {
    const { face: f } = face("missed_call");
    expect(f.name).toBe("Missed call: The deploy waits for your go");
    expect(f.lamp.tone).toBe("fail");
    const verbs = (f.verbs as { verbs: Array<{ label: string; needs_text?: boolean }>; msgId: string }).verbs;
    expect(verbs.map((v) => v.label)).toEqual(["Call again", "Answer here"]);
    expect(verbs[1].needs_text).toBe(true);
  });
  it("a held call: Call you about …? with Call now / Let it wait", () => {
    const { face: f } = face("held_call");
    expect(f.name).toMatch(/^Call you about .+\?$/);
    expect(f.fact).toBe("An agent asks to call you · now");
  });
});

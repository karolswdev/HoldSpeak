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

  it("the device row says why a push will not go (push_state on the wire); a ready phone says its paired fact", async () => {
    expect(P.status.devices[0].push_state).toBe("ready");
    const reasons: Record<string, string> = {
      no_key: "Push not ready: no Apple push key on the hub",
      http2_unavailable: "Push not ready: the hub has no HTTP/2",
      unregistered: "Push not ready: the phone sent no push token",
    };
    for (const [state, words] of Object.entries(reasons)) {
      const device = { ...P.status.devices[0], push_state: state as "no_key" };
      hub({ "GET /api/settings": phoneOn, "GET /api/phone/status": { ...P.status, devices: [device] } });
      const { unmount } = render(<PhoneSettingsPane />);
      const row = await screen.findByTestId("phone-device-row");
      const push = within(row).getByTestId("phone-device-push");
      expect(push.textContent).toBe(words);
      expect(push.getAttribute("data-tone")).toBe("warn");
      expect(push.getAttribute("title")).toMatch(/Paired \d+ Oct/);
      unmount();
    }
    hub({ "GET /api/settings": phoneOn, "GET /api/phone/status": P.status });
    render(<PhoneSettingsPane />);
    const row = await screen.findByTestId("phone-device-row");
    expect(within(row).queryByTestId("phone-device-push")).toBeNull();
    expect(row.textContent).toMatch(/Paired \d+ Oct/);
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

/* ── The Line (LINE-4, 2026-10-29): every answer below is RECORDED from the
   hub's own routes with the Line node on the fake baresip
   (scripts/record_line_fixtures.py → calls/__fixtures__/line.*.json). ── */
import lineSettings from "../calls/__fixtures__/line.settings.json";
import lineSettingsTelnyx from "../calls/__fixtures__/line.settings.telnyxMissing.json";
import lineSettingsStored from "../calls/__fixtures__/line.settings.telnyxStored.json";
import linePut from "../calls/__fixtures__/line.put.password.json";
import lineNotInstalled from "../calls/__fixtures__/line.status.notInstalled.json";
import lineNotRunning from "../calls/__fixtures__/line.status.notRunning.json";
import lineReady from "../calls/__fixtures__/line.status.ready.json";
import lineTelnyxMissing from "../calls/__fixtures__/line.status.telnyxMissing.json";
import lineTelnyxStored from "../calls/__fixtures__/line.status.telnyxStored.json";
import lineCallsReady from "../calls/__fixtures__/line.calls.ready.json";
import lineCallsStarting from "../calls/__fixtures__/line.calls.starting.json";
import lineCallsNotRunning from "../calls/__fixtures__/line.calls.notRunning.json";
import lineCallsNotInstalled from "../calls/__fixtures__/line.calls.notInstalled.json";
import lineTestAnswered from "../calls/__fixtures__/line.test.answered.json";
import lineTestNoAnswer from "../calls/__fixtures__/line.test.noAnswer.json";
import lineTestBusy from "../calls/__fixtures__/line.test.busy.json";
import lineTestRejected from "../calls/__fixtures__/line.test.rejected.json";
import lineTestNotRunning from "../calls/__fixtures__/line.test.notRunning.json";
import lineTestNoNumber from "../calls/__fixtures__/line.test.noNumber.json";
import lineNodesNone from "../calls/__fixtures__/line.nodes.none.json";
import lineNodesEnrolled from "../calls/__fixtures__/line.nodes.enrolled.json";
import lineNodesReady from "../calls/__fixtures__/line.nodes.ready.json";
import lineNodesRevoke from "../calls/__fixtures__/line.nodes.revoke.json";
import lineCodeKarol from "../calls/__fixtures__/line.codes.karol.json";
import lineCodeBadName from "../calls/__fixtures__/line.codes.badName.json";
import lineSettingsKarol from "../calls/__fixtures__/line.settings.karol.json";
import lineStatusKarol from "../calls/__fixtures__/line.status.karol.json";
import linePutWhereKarol from "../calls/__fixtures__/line.put.whereKarol.json";
import { LINE_BREW_COMMAND, LINE_RUN_COMMAND, LINE_VENV_COMMAND, NODE_POLL_MS } from "../calls/LineSettings";

function lineHub(extra: Record<string, Answer> = {}) {
  hub({
    "GET /api/settings": { calls: lineSettings },
    "GET /api/calls/status": lineCallsReady,
    "GET /api/calls/line/status": lineReady,
    ...extra,
  });
}
const lineText = () => screen.getByTestId("line-settings").textContent ?? "";

describe("Settings ▸ Calls ▸ Line", () => {
  it("not running on This Mac (his hub today): the place word, its cost, and the install in its own Python 3.13 with Copy", async () => {
    lineHub({ "GET /api/calls/status": lineCallsNotRunning, "GET /api/calls/line/status": lineNotRunning });
    render(<CallsSettingsPane />);
    const state = await screen.findByTestId("line-place-state");
    await waitFor(() => expect(state.textContent).toBe("Not running"));
    const place = screen.getByTestId("line-place");
    expect(place.textContent).toContain("This Mac");
    expect(place.textContent).toContain("About 0.13 core per call minute");
    const install = screen.getByTestId("line-install");
    expect(install.textContent).toContain(LINE_VENV_COMMAND);
    expect(install.textContent).toContain(LINE_RUN_COMMAND);
    expect(install.textContent).toContain("Python 3.13");
    expect(install.textContent).not.toContain(LINE_BREW_COMMAND);
    expect(within(install).getAllByRole("button", { name: "Copy" })).toHaveLength(2);
    // The checklist's first steps are the Line's, not ai-phone's.
    expect(screen.getByTestId("calls-step-install").textContent).toContain("Install the Line");
    expect(screen.queryByText(INSTALL_COMMAND)).toBeNull();
    expect(screen.getByTestId("calls-step-daemon").textContent).toContain(LINE_RUN_COMMAND);
    expect(screen.getAllByTestId("line-egress")).toHaveLength(1);
  });

  it("not installed: brew install baresip comes first", async () => {
    lineHub({ "GET /api/calls/status": lineCallsNotInstalled, "GET /api/calls/line/status": lineNotInstalled });
    render(<CallsSettingsPane />);
    await waitFor(() => expect(screen.getByTestId("line-place-state").textContent).toBe("Not installed"));
    const install = screen.getByTestId("line-install");
    expect(install.textContent).toContain(LINE_BREW_COMMAND);
    expect(install.textContent).toContain(LINE_VENV_COMMAND);
  });

  it("ready: the free SIP address with Copy; From Calls read only; the Line in use", async () => {
    const writeText = vi.fn(async () => undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    lineHub();
    render(<CallsSettingsPane />);
    await waitFor(() => expect(screen.getByTestId("line-place-state").textContent).toBe("Ready"));
    expect(screen.queryByTestId("line-install")).toBeNull();
    expect(screen.getByTestId("line-address").textContent).toContain(lineReady.address);
    fireEvent.click(screen.getByTestId("line-address-copy"));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(lineReady.address));
    expect(screen.getByTestId("line-address-copy").textContent).toBe("Copied");
    expect(screen.getByTestId("line-codecs").textContent).toBe("Codecs: opus, PCMU, PCMA");
    const from = screen.getByTestId("line-from-calls").textContent ?? "";
    expect(from).toContain(`${lineSettings.daily_limit} placed calls a day`);
    expect(from).toContain("This is HoldSpeak, an AI assistant");
    expect(from).toContain("911, 112, 999, 000");
    const adapter = screen.getByTestId("line-adapter");
    expect(adapter.textContent).toContain("The LineIn use");
    expect(adapter.textContent).toContain("Optional, AGPL, runs as a separate program");
  });

  it("Test call: Ringing while the hub dials, then the recorded result word", async () => {
    let answer: () => void = () => undefined;
    lineHub({ "POST /api/calls/line/test": lineTestAnswered });
    // The hub holds the answer while the line rings (the table clones each
    // answer, so the wait wraps it).
    const table = mocks.apiFetch.getMockImplementation()!;
    mocks.apiFetch.mockImplementation((path: string, init?: { method?: string; json?: unknown }) => path === "/api/calls/line/test"
      ? new Promise((resolve) => { answer = () => resolve(table(path, init)); })
      : table(path, init));
    render(<CallsSettingsPane />);
    const press = await screen.findByTestId("line-test-call");
    await waitFor(() => expect(screen.getByTestId("line-place-state").textContent).toBe("Ready"));
    expect(screen.getByTestId("line-test").textContent).toContain(`Calls ${lineSettings.allowed_numbers[0]}`);
    expect(press.getAttribute("title")).toBe("From the Line on This Mac");
    fireEvent.click(press);
    const ringing = await screen.findByTestId("line-test-state");
    expect(ringing.textContent).toBe("Ringing");
    expect(ringing.closest(".line-live")).not.toBeNull();
    await act(async () => { answer(); });
    await waitFor(() => expect(screen.getByTestId("line-test-state").textContent).toBe("Answered"));
    expect(calls).toContain("POST /api/calls/line/test {}");
  });

  for (const [recorded, word] of [
    [lineTestNoAnswer, "No answer"], [lineTestBusy, "Busy"], [lineTestRejected, "Rejected"],
    [lineTestNotRunning.body, "Line not running"],
  ] as const) {
    it(`Test call: the recorded ${recorded.result} reads ${word}`, async () => {
      lineHub({ "POST /api/calls/line/test": recorded });
      render(<CallsSettingsPane />);
      fireEvent.click(await screen.findByTestId("line-test-call"));
      await waitFor(() => expect(screen.getByTestId("line-test-state").textContent).toBe(word));
    });
  }

  it("Test call: the hub's 409 no_number reads No number; no number at all turns the verb off", async () => {
    lineHub({ "POST /api/calls/line/test": () => { throw new ApiError(lineTestNoNumber.status, "Conflict", lineTestNoNumber.body); } });
    render(<CallsSettingsPane />);
    fireEvent.click(await screen.findByTestId("line-test-call"));
    await waitFor(() => expect(screen.getByTestId("line-test-state").textContent).toBe("No number"));
    cleanup();
    lineHub({ "GET /api/settings": { calls: { ...lineSettings, allowed_numbers: [] } } });
    render(<CallsSettingsPane />);
    const press = await screen.findByTestId("line-test-call");
    expect(press).toBeDisabled();
    expect(screen.getByTestId("line-test").textContent).toContain("No number");
  });

  it("a Telnyx number: the password Missing, the key from the environment; Save writes the keystore and the row says so", async () => {
    let stored = false;
    hub({
      "GET /api/settings": () => ({ calls: stored ? lineSettingsStored : lineSettingsTelnyx }),
      "GET /api/calls/status": lineCallsReady,
      "GET /api/calls/line/status": () => (stored ? lineTelnyxStored : lineTelnyxMissing),
      "PUT /api/settings": () => { stored = true; return linePut; },
    });
    render(<CallsSettingsPane />);
    await waitFor(() => expect(screen.getByTestId("line-place-state").textContent).toBe("Not set up"));
    expect(screen.getByTestId("line-account").getAttribute("data-kind")).toBe("telnyx");
    expect(screen.getByTestId("line-password-place").textContent).toBe("Missing");
    expect(screen.getByTestId("line-telnyx-key-place").textContent).toBe("From the environment: move it to the keystore");
    // The key that is only in his shell: the write field is the way in.
    const keyField = within(screen.getByTestId("line-telnyx-key")).getByLabelText("Telnyx API key");
    expect(keyField).toHaveAttribute("type", "password");
    const field = within(screen.getByTestId("line-password")).getByLabelText("SIP password");
    fireEvent.change(field, { target: { value: "sip-secret" } });
    fireEvent.click(screen.getByTestId("line-password-save"));
    await waitFor(() => expect(screen.getByTestId("line-password-place").textContent).toBe("Stored in your keystore"));
    expect(calls).toContain(`PUT /api/settings ${JSON.stringify({ calls: { line: { account: { password: "sip-secret" } } } })}`);
    expect(screen.getByTestId("line-telnyx-key-place").textContent).toBe("Stored in your keystore");
    expect(screen.getByTestId("line-password-change")).toBeInTheDocument();
    expect(screen.queryByLabelText("SIP password")).toBeNull();
    expect(lineText()).not.toContain("sip-secret");
    expect(screen.getByTestId("line-place-state").textContent).toBe("Starting");
  });

  it("the adapter: a press on ai-phone writes calls.line.adapter", async () => {
    lineHub({ "PUT /api/settings": linePut });
    render(<CallsSettingsPane />);
    const adapter = await screen.findByTestId("line-adapter");
    fireEvent.click(within(adapter).getByRole("radio", { name: /ai-phone/ }));
    await waitFor(() => expect(calls).toContain(`PUT /api/settings ${JSON.stringify({ calls: { line: { adapter: "ai-phone" } } })}`));
  });

  /* LINE-4c: another machine. Install the Line on karol → the one-time code
     sheet → Copy; karol's first hello → Ready; Revoke → gone; pick karol →
     where = node:karol. Every answer is the hub's own (record_line_fixtures). */
  const nodeRow = (node: string) => screen.getAllByTestId("line-place").find((row) => row.getAttribute("data-where") === `node:${node}`);

  it("Install the Line on karol: the hub's one-time code, its life as a word, the whole command with Copy", async () => {
    const writeText = vi.fn(async () => undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    lineHub({ "GET /api/calls/line/nodes": lineNodesNone, "POST /api/calls/line/codes": lineCodeKarol });
    render(<CallsSettingsPane />);
    const add = await screen.findByTestId("line-add");
    const press = within(add).getByTestId("line-install-node");
    expect(press).toBeDisabled();
    expect(press.textContent).toBe("Install the Line");
    fireEvent.change(within(add).getByLabelText("Add a machine"), { target: { value: "karol" } });
    expect(press.textContent).toBe("Install the Line on karol");
    fireEvent.click(press);
    const sheet = await screen.findByTestId("line-code-sheet");
    expect(calls).toContain(`POST /api/calls/line/codes ${JSON.stringify({ node: "karol", hub: window.location.origin })}`);
    expect(within(sheet).getByTestId("line-code").textContent).toBe(lineCodeKarol.code);
    expect(within(sheet).getByTestId("line-code-life").textContent).toBe("Good for 10 more minutes");
    expect(sheet.textContent).toContain("Run this on karol");
    expect(sheet.textContent).toContain(lineCodeKarol.command);
    expect(within(sheet).getByTestId("line-code-wait").textContent).toBe("Waiting for karol");
    expect(screen.queryByTestId("line-add")).toBeNull();
    fireEvent.click(within(sheet).getByRole("button", { name: "Copy" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(lineCodeKarol.command));
    // Cancel closes the sheet; Add a machine is back.
    fireEvent.click(within(sheet).getByTestId("line-code-cancel"));
    expect(screen.queryByTestId("line-code-sheet")).toBeNull();
    expect(screen.getByTestId("line-add")).toBeInTheDocument();
  });

  it("a name the hub refuses: its own reason, and no sheet", async () => {
    lineHub({ "GET /api/calls/line/nodes": lineNodesNone,
      "POST /api/calls/line/codes": () => { throw new ApiError(lineCodeBadName.status, lineCodeBadName.body.error, lineCodeBadName.body); } });
    render(<CallsSettingsPane />);
    const add = await screen.findByTestId("line-add");
    fireEvent.change(within(add).getByLabelText("Add a machine"), { target: { value: "Karol's box!" } });
    fireEvent.click(within(add).getByTestId("line-install-node"));
    await waitFor(() => expect(screen.getByTestId("line-refusal").textContent).toContain(lineCodeBadName.body.error));
    expect(screen.queryByTestId("line-code-sheet")).toBeNull();
  });

  it("karol's first hello closes the sheet, and its row reads Ready with its platform and its cost", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      let nodes: unknown = lineNodesNone;
      lineHub({ "GET /api/calls/line/nodes": () => nodes, "POST /api/calls/line/codes": lineCodeKarol });
      render(<CallsSettingsPane />);
      const add = await screen.findByTestId("line-add");
      fireEvent.change(within(add).getByLabelText("Add a machine"), { target: { value: "karol" } });
      fireEvent.click(within(add).getByTestId("line-install-node"));
      await screen.findByTestId("line-code-sheet");
      // karol redeemed the code; the Line there has not said hello yet.
      nodes = lineNodesEnrolled;
      await act(async () => { vi.advanceTimersByTime(NODE_POLL_MS); });
      await waitFor(() => expect(within(nodeRow("karol")!).getByTestId("line-node-state").textContent).toBe("Not running"));
      expect(screen.getByTestId("line-code-sheet")).toBeInTheDocument();
      // A minute on, the life word counts down.
      await act(async () => { vi.advanceTimersByTime(60_000); });
      expect(screen.getByTestId("line-code-life").textContent).toBe("Good for 9 more minutes");
      // Its first hello.
      nodes = lineNodesReady;
      await act(async () => { vi.advanceTimersByTime(NODE_POLL_MS); });
      await waitFor(() => expect(screen.queryByTestId("line-code-sheet")).toBeNull());
      const row = nodeRow("karol")!;
      expect(within(row).getByTestId("line-node-state").textContent).toBe("Ready");
      expect(row.textContent).toContain("Linux x86_64 · About 0.4 core per call minute");
      expect(screen.getByTestId("line-add")).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("pick karol: where = node:karol, and the place word is the Line's there", async () => {
    let picked = false;
    hub({
      "GET /api/settings": () => ({ calls: picked ? lineSettingsKarol : lineSettings }),
      "GET /api/calls/status": lineCallsReady,
      "GET /api/calls/line/status": () => (picked ? lineStatusKarol : lineReady),
      "GET /api/calls/line/nodes": lineNodesReady,
      "PUT /api/settings": () => { picked = true; return linePutWhereKarol; },
    });
    render(<CallsSettingsPane />);
    await waitFor(() => expect(nodeRow("karol")).toBeTruthy());
    fireEvent.click(within(screen.getByTestId("line-where")).getByRole("radio", { name: /karol/ }));
    await waitFor(() => expect(calls).toContain(`PUT /api/settings ${JSON.stringify({ calls: { line: { where: "node:karol" } } })}`));
    await waitFor(() => expect(within(nodeRow("karol")!).getByTestId("line-place-state").textContent).toBe("Ready"));
    expect(within(screen.getByTestId("line-where")).getByRole("radio", { name: /karol/ })).toBeChecked();
    expect(screen.getByTestId("line-test-call").getAttribute("title")).toBe("From the Line on karol");
  });

  it("Revoke on karol: two presses, the hub's DELETE, and the row is gone", async () => {
    let gone = false;
    lineHub({
      "GET /api/calls/line/nodes": () => (gone ? lineNodesNone : lineNodesReady),
      "DELETE /api/calls/line/nodes/karol": () => { gone = true; return lineNodesRevoke; },
    });
    render(<CallsSettingsPane />);
    await waitFor(() => expect(nodeRow("karol")).toBeTruthy());
    const revoke = within(nodeRow("karol")!).getByTestId("line-node-revoke");
    fireEvent.click(revoke);
    expect(revoke.textContent).toBe("Revoke?");
    expect(calls).not.toContain("DELETE /api/calls/line/nodes/karol");
    // The press is the verb's own: the place stays This Mac.
    expect(within(screen.getByTestId("line-where")).getByRole("radio", { name: /karol/ })).not.toBeChecked();
    fireEvent.click(revoke);
    await waitFor(() => expect(calls).toContain("DELETE /api/calls/line/nodes/karol"));
    await waitFor(() => expect(nodeRow("karol")).toBeUndefined());
    expect(calls.filter((call) => call.startsWith("PUT /api/settings"))).toEqual([]);
  });

  it("a hub without the Line draws no Line section", async () => {
    const { line: _line, ...withoutLine } = lineSettings;
    hub({ "GET /api/settings": { calls: withoutLine }, "GET /api/calls/status": statusReady });
    render(<CallsSettingsPane />);
    await screen.findByTestId("calls-steps");
    await waitFor(() => expect(screen.queryByTestId("calls-line-section")).toBeNull());
    expect(calls).not.toContain("GET /api/calls/line/status");
  });
});

describe("the Calls window on the Line", () => {
  const bar = async (status: unknown) => {
    hub({ "GET /api/settings": { calls: lineSettings }, "GET /api/calls/status": status, "GET /api/calls": callsEmpty });
    render(<CallsCore />);
    await screen.findByTestId("calls-status");
    await waitFor(() => expect(screen.queryByTestId("calls-status")?.textContent).not.toBe(""));
  };

  it("ready: Ready for calls, Call me on, no machine named", async () => {
    await bar(lineCallsReady);
    await waitFor(() => expect(status()).toContain("Ready for calls"));
    expect(screen.getByTestId("calls-call-me")).not.toBeDisabled();
    expect(screen.getByTestId("calls-window").textContent).not.toMatch(/this mac|karol|127\.0|sip:/i);
  });

  it("starting: Line starting on a live lamp", async () => {
    await bar(lineCallsStarting);
    await waitFor(() => expect(status()).toContain("Line starting"));
    expect(screen.getByTestId("calls-status").querySelector(".kit-dot[data-live]")).not.toBeNull();
  });

  it("not running: Line not running; the empty state is No line yet with Set up the Line › to Settings ▸ Calls ▸ Line", async () => {
    await bar(lineCallsNotRunning);
    await waitFor(() => expect(status()).toContain("Line not running"));
    expect(await screen.findByText("No line yet")).toBeInTheDocument();
    expect(screen.getByTestId("calls-call-me")).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Set up the Line ›" }));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "calls::line");
  });

  it("not installed: No line: set one in Settings ▸ Calls ▸ Line", async () => {
    await bar(lineCallsNotInstalled);
    await waitFor(() => expect(status()).toContain("No line: set one in Settings ▸ Calls ▸ Line"));
  });
});

/* ── Set up Telnyx (LINE-3b, 2026-10-29): every answer below is RECORDED from
   the hub's own routes against the fake Telnyx
   (scripts/record_telnyx_fixtures.py → calls/__fixtures__/line.telnyx.*.json). ── */
import tSettingsKey from "../calls/__fixtures__/line.telnyx.settings.keySaved.json";
import tSettingsConnected from "../calls/__fixtures__/line.telnyx.settings.connected.json";
import tSettingsAssigned from "../calls/__fixtures__/line.telnyx.settings.assigned.json";
import tStatusKey from "../calls/__fixtures__/line.telnyx.status.keySaved.json";
import tStatusConnected from "../calls/__fixtures__/line.telnyx.status.connected.json";
import tStatusAssigned from "../calls/__fixtures__/line.telnyx.status.assigned.json";
import tConnect from "../calls/__fixtures__/line.telnyx.connect.json";
import tConnectRefused from "../calls/__fixtures__/line.telnyx.connect.keyRefused.json";
import tNumbers from "../calls/__fixtures__/line.telnyx.numbers.212.json";
import tBuy from "../calls/__fixtures__/line.telnyx.buy.json";
import tBuyNoPress from "../calls/__fixtures__/line.telnyx.buy.noPress.json";
import tAssign from "../calls/__fixtures__/line.telnyx.assign.json";

describe("Settings ▸ Calls ▸ Line ▸ Set up Telnyx", () => {
  /** The hub as the recording left it at each press. */
  function telnyxHub(start: "key" | "connected", extra: Record<string, Answer> = {}) {
    const at = { stage: start as "key" | "connected" | "assigned" };
    hub({
      "GET /api/settings": () => ({ calls: { key: tSettingsKey, connected: tSettingsConnected, assigned: tSettingsAssigned }[at.stage] }),
      "GET /api/calls/status": lineCallsReady,
      "GET /api/calls/line/status": lineTelnyxStored,
      "GET /api/calls/line/telnyx/status": () => ({ key: tStatusKey, connected: tStatusConnected, assigned: tStatusAssigned }[at.stage]),
      "POST /api/calls/line/telnyx/connect": () => { at.stage = "connected"; return tConnect; },
      "GET /api/calls/line/telnyx/numbers?area=212": tNumbers,
      "POST /api/calls/line/telnyx/buy": tBuy,
      "POST /api/calls/line/telnyx/assign": () => { at.stage = "assigned"; return tAssign; },
      ...extra,
    });
    return at;
  }
  const findNumbers = async () => {
    const field = within(await screen.findByTestId("telnyx-step-number")).getByLabelText("Area code");
    await waitFor(() => expect(field).not.toBeDisabled());
    fireEvent.change(field, { target: { value: "212" } });
    fireEvent.click(screen.getByTestId("telnyx-find"));
    await waitFor(() => expect(screen.getAllByTestId("telnyx-number")).toHaveLength(tNumbers.numbers.length));
  };

  it("Connect: the hub makes the SIP account; the row says Connected · sip.telnyx.com · user hs…, the balance is a muted fact", async () => {
    telnyxHub("key");
    render(<CallsSettingsPane />);
    expect((await screen.findByTestId("telnyx-step-key")).textContent).toContain("Stored in your keystore");
    await waitFor(() => expect(screen.getByTestId("telnyx-connect")).not.toBeDisabled());
    expect(screen.queryByTestId("telnyx-connected")).toBeNull();
    fireEvent.click(screen.getByTestId("telnyx-connect"));
    const connected = await screen.findByTestId("telnyx-connected");
    expect(connected.textContent).toBe(`Connected · sip.telnyx.com · user ${tConnect.user}`);
    expect(tConnect.user).toMatch(/^hs/);
    expect(calls).toContain("POST /api/calls/line/telnyx/connect {}");
    // The pane reads the account again: User shows the connection's user.
    await waitFor(() => expect(within(screen.getByTestId("line-user")).getByLabelText("User")).toHaveValue(tConnect.user));
    expect(screen.getByTestId("telnyx-balance").textContent).toBe("Telnyx balance: $20.00");
    expect(lineText()).not.toContain("KEY0123456789");
  });

  it("Find numbers: the area code finds the hub's 10 rows, each with the monthly and upfront cost as Tokens", async () => {
    telnyxHub("connected");
    render(<CallsSettingsPane />);
    await findNumbers();
    const first = screen.getAllByTestId("telnyx-number")[0];
    expect(first.getAttribute("data-number")).toBe("+12125550100");
    expect(first.textContent).toContain("+1 212 555 0100");
    expect(within(first).getByTestId("telnyx-monthly").textContent).toBe("$1.00 a month");
    expect(within(first).getByTestId("telnyx-upfront").textContent).toBe("$1.00 upfront");
    expect(within(first).getByTestId("telnyx-monthly").className).toBe("surface-token");
  });

  it("Buy: the first press only asks; the confirm sends the hub's quote; then Yours · assigned to the line", async () => {
    const at = telnyxHub("connected");
    render(<CallsSettingsPane />);
    await findNumbers();
    const buy = within(screen.getAllByTestId("telnyx-number")[0]).getByTestId("telnyx-buy");
    fireEvent.click(buy);
    expect(buy.textContent).toBe("Buy +1 212 555 0100 for $1.00 a month?");
    expect(calls.some((line) => line.startsWith("POST /api/calls/line/telnyx/buy"))).toBe(false);
    fireEvent.click(buy);
    const yours = await screen.findByTestId("telnyx-yours");
    expect(yours.textContent).toBe("Yours: +1 212 555 0100 · assigned to the line");
    const row = tNumbers.numbers[0];
    expect(calls).toContain(`POST /api/calls/line/telnyx/buy ${JSON.stringify({ phone_number: row.phone_number, quote: row.quote })}`);
    expect(calls).toContain(`POST /api/calls/line/telnyx/assign ${JSON.stringify({ phone_number: row.phone_number })}`);
    expect(at.stage).toBe("assigned");
    expect(screen.queryByTestId("telnyx-number")).toBeNull();
    expect(screen.getByTestId("telnyx-setup").hasAttribute("data-done")).toBe(true);
  });

  it("a refused buy: without the confirm nothing is sent; the hub's refusal says what failed, what is kept, the next action", async () => {
    telnyxHub("connected", {
      "POST /api/calls/line/telnyx/buy": () => { throw new ApiError(tBuyNoPress.status, "Forbidden", tBuyNoPress.body); },
    });
    render(<CallsSettingsPane />);
    await findNumbers();
    const buy = within(screen.getAllByTestId("telnyx-number")[0]).getByTestId("telnyx-buy");
    fireEvent.click(buy);
    expect(calls.some((line) => line.startsWith("POST /api/calls/line/telnyx/buy"))).toBe(false);
    fireEvent.click(buy);
    const failure = await screen.findByTestId("telnyx-failure");
    expect(failure.textContent).toBe(`${tBuyNoPress.body.error} ${tBuyNoPress.body.kept} ${tBuyNoPress.body.next}`);
    expect(failure.textContent).toContain("Nothing was bought.");
    expect(screen.queryByTestId("telnyx-yours")).toBeNull();
    expect(screen.getAllByTestId("telnyx-number")).toHaveLength(tNumbers.numbers.length);
  });

  it("a refused key on Connect: the hub's words, and the key row stays", async () => {
    telnyxHub("key", {
      "POST /api/calls/line/telnyx/connect": () => { throw new ApiError(tConnectRefused.status, "Bad Gateway", tConnectRefused.body); },
    });
    render(<CallsSettingsPane />);
    await waitFor(() => expect(screen.getByTestId("telnyx-connect")).not.toBeDisabled());
    fireEvent.click(screen.getByTestId("telnyx-connect"));
    const failure = await screen.findByTestId("telnyx-failure");
    expect(failure.textContent).toBe(
      "Telnyx did not take the key while it made the SIP connection. Your key is kept. Nothing was made at Telnyx. Check the key in the Telnyx portal, then save it again.");
    expect(screen.queryByTestId("telnyx-connected")).toBeNull();
    expect(screen.getByTestId("line-telnyx-key")).toBeInTheDocument();
  });
});

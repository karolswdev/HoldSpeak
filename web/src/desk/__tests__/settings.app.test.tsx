// The Settings app (the test diet, 2026-10-11): the browser tests of the
// Settings window, moved to the real SettingsCore with its real hooks. Only
// `fetch` is replaced, and it answers with the hub's OWN answers, recorded
// from a live hub by tests/integration/test_desk_settings.py (which also
// proves no fixture carries a field the hub does not send: the scar law).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// The quick check runs this file beside 140 others on a loaded machine; its
// longest walks (the heartbeat's quiet hours, the secret replacement) then
// pass 5 s, while alone they take well under 1 s. 2026-11-01: they timed out
// in every quick check of the day at load 30 to 50.
vi.setConfig({ testTimeout: 20_000 });
import { SettingsCore } from "../../pages/cores/SettingsCore";
import { PREF_MODULES } from "../../pages/cores/settings/prefs";
import connectionsWire from "./fixtures/connections-wire/connections-cold.json";
import destinationsWire from "./fixtures/destinations-wire/list-empty.json";
import authorityWire from "./fixtures/settings-wire/authority-policy.json";
import calendarWire from "./fixtures/settings-wire/calendar-sources.json";
import calendarCandidateWire from "../../test/wire/onboarding-calendar.wire.json";
import calendarUseWire from "../../test/wire/onboarding-calendar.use.wire.json";
import calendarOneWire from "./fixtures/settings-wire/calendar-sources-one.json";
import hubWire from "./fixtures/settings-wire/hub.json";
import heartbeatWire from "./fixtures/settings-wire/heartbeat.json";
import heartbeatPutWire from "./fixtures/settings-wire/heartbeat-put.json";
import peopleWire from "./fixtures/settings-wire/people-access.json";
import projectsWire from "./fixtures/settings-wire/projects.json";
import remoteIssueWire from "./fixtures/settings-wire/remote-issue.json";
import remoteOffWire from "./fixtures/settings-wire/remote-off.json";
import remoteOnWire from "./fixtures/settings-wire/remote-on.json";
import remoteRevokeWire from "./fixtures/settings-wire/remote-revoke.json";
import settingsPutWire from "./fixtures/settings-wire/settings-put.json";
import settingsWire from "./fixtures/settings-wire/settings.json";
import identityWire from "./fixtures/settings-wire/system-identity.json";
import setupFoundWire from "./fixtures/setup-st3-st5/found.json";
import setupStatusWire from "./fixtures/trust-wire/status-virgin.json";
import enginesWire from "./fixtures/runs-on-truth/no-record/0-open_api_concierge_detect.json";
import localAiWire from "./fixtures/runs-on-truth/no-record/0-open_api_setup_local-ai.json";
import downDetect from "./fixtures/runs-on-truth/engine-down/0-down_api_concierge_detect.json";
import downRoster from "./fixtures/runs-on-truth/engine-down/0-down_api_inference_assignments.json";
import downEditor from "./fixtures/runs-on-truth/engine-down/editor-default.json";
import chainRecorded from "../../features/runson/__tests__/fixtures/settings-chain.recorded.json";
import { WHAT_ROWS } from "../../features/runson/whatRows";
import enginesRecorded from "../../features/runson/__tests__/fixtures/engines.recorded.json";
import { WingSlotContext } from "../surface/wings";
import { BackSlotContext, type WindowBack } from "../surface/back";
import { useDesk } from "../store";
import { registerSurface } from "../shell";

type Json = Record<string, any>;
const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value));

/** One hub, its state in memory; every answer starts from a recorded one. */
function hubDouble() {
  const state = {
    settings: clone(settingsWire) as Json,
    hub: clone(hubWire) as Json,
    calendar: clone(calendarWire) as Json,
    remote: clone(remoteOffWire) as Json,
    heartbeat: clone(heartbeatWire) as Json,
    calls: [] as Array<{
      method: string;
      path: string;
      body?: Json;
      keepalive?: boolean;
    }>,
    unknown: [] as string[],
  };
  const answer = (status: number, body: unknown) =>
    new Response(JSON.stringify(body), {
      status,
      headers: { "content-type": "application/json" },
    });
  const fetchStub = vi.fn(async (input: string, init?: RequestInit) => {
    const method = (init?.method ?? "GET").toUpperCase();
    const path = new URL(String(input), "http://hub.test").pathname;
    const body = init?.body ? (JSON.parse(String(init.body)) as Json) : undefined;
    state.calls.push({ method, path, body, keepalive: init?.keepalive });
    const key = `${method} ${path}`;
    switch (key) {
      case "GET /api/settings":
        return answer(200, state.settings);
      case "GET /api/connections":
        return answer(200, connectionsWire);
      case "GET /api/channels/destinations":
        return answer(200, destinationsWire);
      case "PUT /api/settings": {
        // Mirror the producer's required symbol fields instead of accepting
        // the invalid blank row that Add used to send to the live hub.
        const symbols = body?.dictation?.spoken_symbols;
        if (Array.isArray(symbols)) {
          const invalid = symbols.findIndex((entry: Json) => !String(entry.spoken ?? "").trim() || !String(entry.symbol ?? ""));
          if (invalid >= 0)
            return answer(400, {
              error: `spoken_symbols[${invalid}]: the spoken phrase and symbol must not be empty`,
            });
        }
        for (const [k, v] of Object.entries(body ?? {})) {
          if (k.startsWith("_")) continue;
          state.settings[k] = typeof v === "object" && v && !Array.isArray(v) ? { ...state.settings[k], ...v } : v;
        }
        return answer(200, {
          ...clone(settingsPutWire),
          settings: state.settings,
        });
      }
      case "GET /api/settings/hub":
        return answer(200, state.hub);
      // Betterment setup ST1: Settings ▸ Rhythm reads and writes the one
      // quiet-hours store, the heartbeat policy (recorded answers).
      case "GET /api/settings/heartbeat":
        return answer(200, state.heartbeat);
      case "PUT /api/settings/heartbeat": {
        const next = clone(state.heartbeat);
        if (body?.notify) next.notify = body.notify;
        if (body?.quiet_hours) next.quiet_hours = { ...next.quiet_hours, ...body.quiet_hours };
        state.heartbeat = { ...clone(heartbeatPutWire), ...next };
        return answer(200, state.heartbeat);
      }
      case "GET /api/authority/policy":
        return answer(200, authorityWire);
      case "GET /api/calendar/sources":
        return answer(200, state.calendar);
      case "GET /api/settings/people-access":
        return answer(200, peopleWire);
      case "GET /api/settings/remote":
        return answer(200, state.remote);
      case "PUT /api/settings/remote": {
        state.remote = {
          ...clone(remoteOnWire),
          credentials: [],
          total_count: 0,
          active_count: 0,
          enabled: Boolean(body?.enabled),
        };
        state.hub.system.remote = Boolean(body?.enabled);
        return answer(200, { success: true, enabled: Boolean(body?.enabled) });
      }
      case "POST /api/settings/remote/credentials": {
        const issued = {
          ...clone(remoteIssueWire),
          identity: body?.identity,
          id: `id-${body?.identity}`,
        };
        const row = {
          ...clone(remoteOnWire.credentials[0]),
          id: issued.id,
          identity: body?.identity,
          last_used_at: null,
        };
        state.remote.credentials = [...state.remote.credentials, row];
        state.remote.total_count = state.remote.credentials.length;
        state.remote.active_count = state.remote.credentials.length;
        return answer(200, issued);
      }
      case "GET /api/system/identity":
        return answer(200, identityWire);
      case "GET /api/projects":
        return answer(200, projectsWire);
      case "GET /api/setup/found":
        return answer(200, setupFoundWire);
      case "POST /api/setup/lan":
        return answer(200, { rows: [] });
      case "GET /api/setup/status":
        return answer(200, setupStatusWire);
      case "GET /api/setup/local-ai":
        return answer(200, localAiWire.wire);
      case "GET /api/concierge/detect":
        return answer(200, enginesWire.wire);
    }
    if (method === "DELETE" && path.startsWith("/api/settings/remote/credentials/")) {
      const id = decodeURIComponent(path.split("/").pop() ?? "");
      state.remote.credentials = state.remote.credentials.filter((c: Json) => c.id !== id);
      state.remote.total_count = state.remote.credentials.length;
      state.remote.active_count = state.remote.credentials.length;
      return answer(200, { ...clone(remoteRevokeWire), revoked: id });
    }
    state.unknown.push(key);
    return answer(404, { error: "not_found" });
  });
  return { state, fetchStub };
}

let hub: ReturnType<typeof hubDouble>;
let releaseSetup: () => void;
let releaseEngines: () => void;
const openEngines = vi.fn();
beforeEach(() => {
  useDesk.setState({ windowsById: {} });
  openEngines.mockClear();
  releaseEngines = registerSurface("configure-runs-on", openEngines);
  releaseSetup = registerSurface("configure-setup", () => useDesk.getState().openSurfaceWindow("configure-setup"));
  hub = hubDouble();
  vi.stubGlobal("fetch", hub.fetchStub);
});
afterEach(() => {
  cleanup();
  releaseSetup();
  releaseEngines();
  useDesk.setState({ windowsById: {} });
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

/** The library fence: a verb is the library Button (or a kit control). */
const LIBRARY = [
  "btn",
  "btn--chrome",
  "surface-ledger-line",
  "gadget-cycle",
  "desk-mic",
  "gadget-stepper-btn",
  "gadget-table-add",
  "gadget-table-delete",
  "gadget-fold-toggle",
  "surface-edit-in-place",
  "surface-disclosure-trigger",
  "gadget-transport-key",
];
const rawButtons = (root: ParentNode) =>
  Array.from(root.querySelectorAll("button"))
    .filter((b) => !LIBRARY.some((c) => b.classList.contains(c)) && !b.closest(".gadget-stepper, .gadget-table"))
    .map((b) => (b.textContent ?? "").trim().slice(0, 40));

const ledgerRow = (name: string) =>
  Array.from(document.querySelectorAll(".surface-ledger-row")).find((row) => row.querySelector(".surface-ledger-primary")?.textContent === name) as HTMLElement | undefined;

async function openHub() {
  const view = render(<SettingsCore />);
  await screen.findByText("No engine yet");
  // Ordinary preferences are visible on first open.
  await waitFor(() => expect(ledgerRow("Rhythm")?.textContent).toContain("EVERY 15 MIN"));
  return view;
}

/** The real frame publication seam: wing presses must reach this core. */
function SettingsWindow({ scope }: { scope?: string }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <WingSlotContext.Provider value={setWings}>
      <header>{wings}</header>
      <SettingsCore scope={scope} />
    </WingSlotContext.Provider>
  );
}

describe("Settings › People: his name and the other names for him", () => {
  it("edits the name and adds an alias with Enter; both reach the hub; an alias added just before the page hides still goes", async () => {
    // replaces: tests/e2e/test_hs170_settings_hub_glass.py::test_settings_people_edits_name_and_alias_after_setup
    hub.state.settings.owner = { name: "Karl", aliases: [] };
    render(<SettingsCore scope="people" />);
    const name = within(await screen.findByTestId("settings-owner-name")).getByRole("textbox") as HTMLInputElement;
    await waitFor(() => expect(name.value).toBe("Karl"));
    fireEvent.change(name, { target: { value: "Karol Sane" } });
    fireEvent.blur(name);
    const alias = within(screen.getByTestId("settings-owner-aliases")).getByRole("textbox");
    fireEvent.change(alias, { target: { value: "Carol" } });
    fireEvent.keyDown(alias, { key: "Enter" });
    await waitFor(
      () =>
        expect(hub.state.settings.owner).toEqual({
          name: "Karol Sane",
          aliases: ["Carol"],
        }),
      { timeout: 3000 },
    );
    expect(within(screen.getByTestId("settings-owner-aliases")).getByText("Carol")).toBeInTheDocument();

    fireEvent.change(alias, { target: { value: "Karolek" } });
    fireEvent.keyDown(alias, { key: "Enter" });
    act(() => {
      window.dispatchEvent(new Event("pagehide"));
    });
    const leave = hub.state.calls.filter((c) => c.method === "PUT" && c.path === "/api/settings" && c.keepalive);
    expect(leave.at(-1)?.body?.owner).toEqual({
      name: "Karol Sane",
      aliases: ["Carol", "Karolek"],
    });
  });
});

describe("Settings › Meetings", () => {
  const meetingsText = () => document.querySelector("[data-settings-section=meetings]")?.textContent ?? "";
  const summaryRow = () => screen.getByTestId("settings-summary-controls").closest(".gadget-row") as HTMLElement;

  it("groups Summary and Recording in separate tabs with no navigation row", async () => {
    const { container } = render(<SettingsCore scope="meetings" />);
    await screen.findByRole("combobox", { name: "Auto-run the summary" });
    expect(screen.getByTestId("settings-no-model")).toHaveTextContent("No engine");
    expect(screen.queryByTestId("settings-engines-link")).toBeNull();
    expect(screen.getByRole("checkbox", { name: "Auto export" })).toBeInTheDocument();
    fireEvent.click(within(container.querySelector('[data-settings-section="meetings"]') as HTMLElement).getByRole("tab", { name: "Recording" }));
    expect(screen.getByRole("textbox", { name: "Microphone" })).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "Auto-run the summary" })).toBeNull();
    expect(rawButtons(container)).toEqual([]);
  });

  it("names the assigned summary engine without a redundant Engines row", async () => {
    Object.assign(hub.state.hub.meetings, {
      engineSet: true,
      host: "192.168.1.43",
      engine: "Qwen 27B",
    });
    render(<SettingsCore scope="meetings" />);
    await waitFor(() => expect(screen.getByTestId("settings-summary-controls")).toHaveTextContent("Qwen 27B"));
    expect(screen.queryByTestId("settings-no-model")).toBeNull();
    expect(screen.queryByTestId("settings-engines-link")).toBeNull();
  });

  it("keeps calendar management in Accounts and removes cross-app setup rows", async () => {
    const { container } = render(<SettingsCore scope="meetings" />);
    await screen.findByRole("combobox", { name: "Auto-run the summary" });
    const section = container.querySelector('[data-settings-section="meetings"]')!;
    expect(section.querySelector('.prefs-calendar-section, [data-testid="settings-auto-record-link"]')).toBeNull();
  });

  it("Accounts has one tick list for calendars and its actions stay outside rows", async () => {
    hub.state.settings.calendar = {
      ...hub.state.settings.calendar,
      sources: [
        {
          id: "src-work",
          label: "WORK",
          url: "/Users/owner/work.ics",
          enabled: true,
        },
      ],
    };
    hub.state.calendar = { ...clone(calendarOneWire), matched_this_week: 1 };
    render(<SettingsCore scope="integrations" />);
    const row = await screen.findByTestId("calendar-source-src-work");
    fireEvent.click(screen.getByRole("tab", { name: "Calendars" }));
    expect(within(row).getByText("Calendar feed")).toBeInTheDocument();
    expect(within(row).getByRole("checkbox", { name: "Read WORK" })).toBeChecked();
    expect(row.querySelector("button")).toBeNull();
    fireEvent.doubleClick(row);
    expect(screen.getByTestId("calendar-well")).toBeInTheDocument();
  });

  it("Add feed opens the existing editor with microphone, Cancel and Save", async () => {
    render(<SettingsCore scope="integrations" />);
    fireEvent.click(await screen.findByRole("tab", { name: "Calendars" }));
    fireEvent.click(screen.getByRole("button", { name: "Add calendar" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Add feed" }));
    const well = screen.getByTestId("calendar-well");
    expect(within(well).getByRole("textbox", { name: "Calendar URL or file path" }).getAttribute("placeholder")).toMatch(/ICS|file/);
    expect(well.querySelector(".desk-mic")).not.toBeNull();
    expect(within(well).getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    expect(within(well).getByRole("button", { name: "Save" })).toBeInTheDocument();
  });

  it("chooses a Mac calendar through the shared selection list and the declared use operation", async () => {
    const base = hub.fetchStub;
    const writes: Json[] = [];
    const candidate = calendarCandidateWire.wire.candidates[0];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        const path = new URL(String(input), "http://hub.test").pathname;
        let answer: unknown;
        if (path === "/api/onboarding/calendar") answer = calendarCandidateWire.wire;
        else if (path === "/api/onboarding/calendar/use") {
          writes.push(JSON.parse(String(init?.body)));
          hub.state.settings.calendar.sources = [
            {
              id: calendarUseWire.wire.source.id,
              label: candidate.label,
              url: candidate.id,
              enabled: true,
            },
          ];
          answer = calendarUseWire.wire;
        } else return base(input, init);
        return new Response(JSON.stringify(answer), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }),
    );
    render(<SettingsCore scope="accounts" />);
    fireEvent.click(await screen.findByRole("tab", { name: "Calendars" }));
    fireEvent.click(screen.getByRole("button", { name: "Add calendar" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Mac calendars" }));
    const list = await screen.findByRole("grid", {
      name: "Available Mac calendars",
    });
    const use = within(list).getByRole("button", { name: "Use" });
    await within(list).findByText("Work");
    expect(use).toBeDisabled();
    fireEvent.click(within(list).getByText("Work"));
    expect(list.querySelector("[data-object-id] button")).toBeNull();
    fireEvent.click(use);
    await waitFor(() => expect(writes).toEqual([{ id: candidate.id, label: candidate.label }]));
    await waitFor(() => expect(within(list).getByText("Read")).toBeInTheDocument());
  });

  it("opening Meetings leaves auto-record unchanged", async () => {
    hub.state.settings.meeting.auto_record = "off";
    render(<SettingsCore scope="meetings" />);
    await screen.findByRole("combobox", { name: "Auto-run the summary" });
    expect(hub.state.settings.meeting.auto_record).toBe("off");
    expect(hub.state.calls.filter((call) => call.method === "PUT" || call.method === "DELETE")).toEqual([]);
  });
});

describe("Settings repair: ordinary choices and recoverable writes", () => {
  it("uses preference tabs rather than page columns", async () => {
    const { container } = render(<SettingsCore scope="meetings" />);
    await screen.findByRole("combobox", { name: "Auto-run the summary" });
    expect(container.querySelector('[data-settings-section="meetings"] .surface-columns')).toBeNull();
    for (const label of ["Summary", "Recording", "Actions"])
      expect(within(container.querySelector('[data-settings-section="meetings"]') as HTMLElement).getByRole("tab", { name: label })).toBeInTheDocument();
  });

  it("shows owner choices without tuning controls or writes to their config", async () => {
    const before = clone(hub.state.settings);
    render(<SettingsCore scope="meetings" />);
    await screen.findByRole("combobox", {name: "Auto-run the summary"});
    const section = within(document.querySelector('[data-settings-section="meetings"]') as HTMLElement);
    expect(section.queryByRole("tab", {name: "Queue"})).toBeNull();
    expect(section.queryByRole("tab", {name: "Routing"})).toBeNull();
    fireEvent.click(section.getByRole("tab", {name: "Recording"}));
    expect(section.getByRole("textbox", {name: "Microphone"})).toBeInTheDocument();
    expect(section.queryByRole("spinbutton", {name: "Similarity"})).toBeNull();
    expect(section.queryByRole("combobox", {name: "Routing profile"})).toBeNull();
    expect(hub.state.calls.filter((call) => call.path === "/api/settings" && call.method === "PUT")).toEqual([]);
    expect(hub.state.settings).toEqual(before);
  });

  it("keeps incomplete symbols local and edits or removes the selected symbol", async () => {
    render(<SettingsCore scope="speak" />);
    await screen.findByRole("combobox", { name: "Language" });
    const speak = within(document.querySelector('[data-settings-section="speak"]') as HTMLElement);
    fireEvent.click(speak.getByRole("tab", { name: "Symbols" }));
    fireEvent.click(speak.getByRole("button", { name: "Add symbol" }));
    fireEvent.change(speak.getByRole("textbox", { name: "Spoken phrase 1" }), {
      target: { value: "right arrow" },
    });
    await new Promise((resolve) => setTimeout(resolve, 800));
    expect(hub.state.calls.filter((call) => call.method === "PUT")).toEqual([]);
    fireEvent.change(speak.getByRole("textbox", { name: "Symbol 1" }), {
      target: { value: "→" },
    });
    await waitFor(() => expect(hub.state.settings.dictation.spoken_symbols).toEqual([{ spoken: "right arrow", symbol: "→", attach: "none" }]), { timeout: 3000 });
    fireEvent.click(speak.getByRole("button", { name: "Done" }));
    const list = speak.getByRole("grid", { name: "Spoken symbols" });
    expect(list.querySelector('[role="row"] button')).toBeNull();
    const forget = within(list).getByRole("button", { name: "Forget" });
    expect(forget).toBeDisabled();
    fireEvent.click(within(list).getByText("right arrow"));
    fireEvent.click(forget);
    await waitFor(() => expect(hub.state.settings.dictation.spoken_symbols).toEqual([]), { timeout: 3000 });
  });

  it("retains a newer incomplete symbol across a failed save, a tab change and Retry", async () => {
    const base = hub.fetchStub;
    let refuse = true;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        if (refuse && init?.method === "PUT" && String(input).endsWith("/api/settings")) throw new TypeError("Symbols connection lost");
        return base(input, init);
      }),
    );
    render(<SettingsCore scope="speak" />);
    await screen.findByRole("combobox", { name: "Language" });
    const speak = within(document.querySelector('[data-settings-section="speak"]') as HTMLElement);
    fireEvent.click(speak.getByRole("tab", { name: "Symbols" }));
    fireEvent.click(speak.getByRole("button", { name: "Add symbol" }));
    fireEvent.change(speak.getByRole("textbox", { name: "Spoken phrase 1" }), {
      target: { value: "right arrow" },
    });
    fireEvent.change(speak.getByRole("textbox", { name: "Symbol 1" }), {
      target: { value: "→" },
    });
    await screen.findByTestId("settings-save-failure", {}, { timeout: 3000 });
    fireEvent.change(speak.getByRole("textbox", { name: "Symbol 1" }), {
      target: { value: "" },
    });
    fireEvent.change(speak.getByRole("textbox", { name: "Spoken phrase 1" }), {
      target: { value: "new arrow" },
    });
    fireEvent.click(speak.getByRole("tab", { name: "Typing" }));
    fireEvent.click(speak.getByRole("tab", { name: "Symbols" }));
    expect(speak.getByRole("textbox", { name: "Spoken phrase 1" })).toHaveValue("new arrow");
    refuse = false;
    fireEvent.click(
      within(screen.getByTestId("settings-save-failure")).getByRole("button", {
        name: "Retry",
      }),
    );
    await waitFor(() => expect(hub.state.settings.dictation.spoken_symbols).toEqual([{ spoken: "right arrow", symbol: "→", attach: "none" }]), { timeout: 3000 });
    expect(speak.getByRole("textbox", { name: "Symbol 1" })).toHaveValue("");
    fireEvent.change(speak.getByRole("textbox", { name: "Symbol 1" }), {
      target: { value: "⇒" },
    });
    await waitFor(() => expect(hub.state.settings.dictation.spoken_symbols).toEqual([{ spoken: "new arrow", symbol: "⇒", attach: "none" }]), { timeout: 3000 });
  });

  it("keeps hold-key capture active through a preference rerender and Escape cancels it", async () => {
    render(<SettingsCore scope="voice" />);
    await screen.findByRole("combobox", { name: "Language" });
    const typing = screen.getByRole("region", { name: "Voice typing" });
    expect(within(typing).getByRole("checkbox", { name: "Preview before type" })).toBeInTheDocument();
    expect(within(typing).getByRole("checkbox", { name: "Voice commands" })).toBeInTheDocument();
    const key = within(typing).getByRole("button", {
      name: /^Push-to-talk key:/,
    });
    const before = key.getAttribute("aria-label");
    fireEvent.click(key);
    fireEvent.change(within(typing).getByRole("combobox", { name: "Language" }), { target: { value: "pl" } });
    expect(
      within(typing).getByRole("button", {
        name: "Listening for the hold key. Esc cancels.",
      }),
    ).toBe(key);
    fireEvent.keyDown(window, { key: "Escape", code: "Escape" });
    expect(key).toHaveAttribute("aria-label", before);
    fireEvent.click(key);
    fireEvent.keyDown(window, { key: "F8", code: "F8" });
    expect(key).toHaveTextContent("F8");
    await waitFor(() => expect(hub.state.settings.hotkey.key).toBe("f8"));
  });

  it("renames a native calendar without exposing or changing its identifier, preserving every source", async () => {
    const original = clone(hub.state.settings.calendar);
    const native = {
      ...clone(original.sources[0] ?? {}),
      id: "native-work",
      label: "",
      url: "eventkit:6A0B9E7C-1884-4C46-9F90-9A7B1D24B191",
      enabled: true,
    };
    const feed = {
      ...native,
      id: "team-feed",
      label: "Team",
      url: "https://work.example/calendar.ics",
      enabled: false,
    };
    hub.state.settings.calendar = { ...original, sources: [native, feed] };
    hub.state.calendar = {
      ...clone(calendarOneWire),
      sources: [
        {
          ...clone(calendarOneWire.sources[0]),
          id: native.id,
          label: "",
          type: "MACOS",
        },
      ],
    };
    render(<SettingsCore scope="integrations" />);
    fireEvent.click(await screen.findByRole("tab", { name: "Calendars" }));
    const row = await screen.findByTestId("calendar-source-native-work");
    expect(row.textContent).toContain("Mac calendar");
    expect(row.textContent).not.toContain("6A0B9E7C");
    expect(row.textContent).not.toContain("ICS");
    fireEvent.doubleClick(row);
    const well = screen.getByTestId("calendar-well");
    expect(
      within(well).queryByRole("textbox", {
        name: "Calendar URL or file path",
      }),
    ).toBeNull();
    fireEvent.change(within(well).getByRole("textbox", { name: "Calendar name" }), { target: { value: "Work" } });
    fireEvent.click(within(well).getByRole("button", { name: "Save" }));
    await waitFor(() => expect(hub.state.settings.calendar.sources[0].label).toBe("Work"));
    const put = hub.state.calls.find((call) => call.method === "PUT" && call.path === "/api/settings")!;
    expect(Object.keys(put.body!).sort()).toEqual(["_revision", "calendar"]);
    expect(put.body!.calendar).toEqual({
      sources: [{ ...native, label: "Work" }, feed],
    });
    expect(hub.state.settings.calendar.sources[0].url).toBe(native.url);
  });

  it("keeps a refused edit in place and Retry sends only its changed path", async () => {
    hub.state.settings.meeting.auto_export = false;
    const base = hub.fetchStub;
    let refuse = true;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        if (refuse && init?.method === "PUT" && new URL(String(input), "http://hub.test").pathname === "/api/settings") throw new TypeError("Settings connection lost");
        return base(input, init);
      }),
    );
    render(<SettingsCore scope="meetings" />);
    const toggle = await screen.findByRole("checkbox", { name: "Auto export" });
    fireEvent.click(toggle);
    const retry = within(await screen.findByTestId("settings-save-failure", {}, { timeout: 3000 })).getByRole("button", { name: "Retry" });
    expect(toggle).toBeChecked();
    expect(retry.closest('[role="alert"]')?.textContent).toContain("Settings connection lost");
    const footer = document.querySelector<HTMLElement>(".pref-status-bar")!;
    expect(footer.querySelector(".kit-statusbar-items")?.textContent).toContain("Not saved");
    expect(footer.querySelector(".kit-statusbar-verbs")?.textContent).not.toContain("Settings connection lost");
    refuse = false;
    fireEvent.click(retry);
    await waitFor(() => expect(hub.state.settings.meeting.auto_export).toBe(true));
    const put = hub.state.calls.find((call) => call.method === "PUT" && call.path === "/api/settings")!;
    expect(put.body).toEqual({
      _revision: settingsWire._revision,
      meeting: { auto_export: true },
    });
    await waitFor(() => expect(screen.queryByTestId("settings-save-failure")).toBeNull());
    expect(within(footer).queryByRole("button", { name: "Retry" })).toBeNull();
  });

  it("an unrelated accepted edit keeps the earlier failure; a later edit of that field wins", async () => {
    hub.state.settings.meeting.auto_export = false;
    const base = hub.fetchStub;
    let refuse = true;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        if (refuse && init?.method === "PUT" && new URL(String(input), "http://hub.test").pathname === "/api/settings") throw new TypeError("Settings connection lost");
        return base(input, init);
      }),
    );
    render(<SettingsCore scope="meetings" />);
    const toggle = await screen.findByRole("checkbox", { name: "Auto export" });
    fireEvent.click(toggle);
    await screen.findByTestId("settings-save-failure", {}, { timeout: 3000 });
    refuse = false;
    fireEvent.change(screen.getByRole("combobox", { name: "Auto-run the summary" }), { target: { value: "off" } });
    await waitFor(() => expect(hub.state.settings.meeting.intelligence_auto).toBe("off"), { timeout: 3000 });
    expect(toggle).toBeChecked();
    expect(screen.getByTestId("settings-save-failure")).toBeInTheDocument();
    fireEvent.click(toggle);
    await waitFor(() => expect(screen.queryByTestId("settings-save-failure")).toBeNull(), { timeout: 3000 });
    expect(toggle).not.toBeChecked();
    expect(hub.state.settings.meeting.auto_export).toBe(false);
  });

  it("Retry keeps the newer same-field edit made inside the debounce window", async () => {
    const base = hub.fetchStub;
    let refuse = true;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        if (refuse && init?.method === "PUT" && new URL(String(input), "http://hub.test").pathname === "/api/settings") throw new TypeError("Settings connection lost");
        return base(input, init);
      }),
    );
    render(<SettingsCore scope="meetings" />);
    const timing = await screen.findByRole("combobox", {
      name: "Auto-run the summary",
    });
    fireEvent.change(timing, { target: { value: "room_linked" } });
    const failure = await screen.findByTestId("settings-save-failure", {}, { timeout: 3000 });
    refuse = false;
    fireEvent.change(timing, { target: { value: "off" } });
    fireEvent.click(within(failure.parentElement!).getByRole("button", { name: "Retry" }));
    expect(timing).toHaveValue("off");
    await waitFor(() => expect(hub.state.settings.meeting.intelligence_auto).toBe("off"));
    expect(hub.state.calls.filter((call) => call.method === "PUT" && call.path === "/api/settings").at(-1)?.body?.meeting).toEqual({ intelligence_auto: "off" });
  });

  it("a successful secret replacement keeps the earlier preference failure and its Retry", async () => {
    hub.state.settings.meeting.auto_export = false;
    const base = hub.fetchStub;
    let refusePreference = true;
    let secretSaved = false;
    let modeSaved = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        const path = new URL(String(input), "http://hub.test").pathname;
        if (refusePreference && init?.method === "PUT" && path === "/api/settings") throw new TypeError("Preference connection lost");
        if (init?.method === "PUT" && path === "/api/settings/secrets/web_token") {
          secretSaved = true;
          return new Response(JSON.stringify({ success: true }), {
            status: 200,
            headers: { "content-type": "application/json" },
          });
        }
        if (init?.method === "PUT" && path === "/api/authority/control-mode") {
          modeSaved = true;
          return new Response(JSON.stringify({ ...authorityWire, control_mode: "neutral" }), { status: 200, headers: { "content-type": "application/json" } });
        }
        return base(input, init);
      }),
    );
    render(<SettingsWindow scope="meetings" />);
    fireEvent.click(await screen.findByRole("checkbox", { name: "Auto export" }));
    await screen.findByTestId("settings-save-failure", {}, { timeout: 3000 });
    fireEvent.click(screen.getByTestId("settings-index-this-mac"));
    fireEvent.click(screen.getByRole("tab", { name: "Keys" }));
    fireEvent.doubleClick(screen.getByRole("grid", { name: "Device credentials" }).querySelector('[data-object-id="web_token"]')!);
    const credentials = screen.getByRole("region", {
      name: "Web pairing token",
    });
    const replacement = within(credentials).getByLabelText("Replacement Web pairing token");
    expect(replacement).toHaveValue("");
    fireEvent.change(replacement, { target: { value: "fixture-replacement" } });
    fireEvent.click(within(credentials).getByRole("button", {name:"Save"}));
    await waitFor(() => expect(secretSaved).toBe(true));
    await waitFor(() => expect(screen.queryByRole("region", {name:"Web pairing token"})).toBeNull());
    expect(screen.getByTestId("settings-save-failure").textContent).toContain("Preference connection lost");
    expect(document.querySelector(".kit-statusbar-items")?.textContent).toContain("Not saved");
    fireEvent.click(screen.getByTestId("settings-index-agents"));
    fireEvent.change(await screen.findByRole("combobox", { name: "Agents act" }), { target: { value: "neutral" } });
    await waitFor(() => expect(modeSaved).toBe(true));
    expect(screen.getByTestId("settings-save-failure").textContent).toContain("Preference connection lost");
    expect(document.querySelector(".kit-statusbar-items")?.textContent).toContain("Not saved");
    refusePreference = false;
    fireEvent.click(
      within(screen.getByTestId("settings-save-failure")).getByRole("button", {
        name: "Retry",
      }),
    );
    await waitFor(() => expect(hub.state.settings.meeting.auto_export).toBe(true));
  });

  it("offers primary Retry in the footer while a failed preference remains pending", async () => {
    const base = hub.fetchStub;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        if (init?.method === "PUT" && new URL(String(input), "http://hub.test").pathname === "/api/settings") throw new TypeError("Settings connection lost");
        return base(input, init);
      }),
    );
    render(<SettingsCore scope="meetings" />);
    fireEvent.click(await screen.findByRole("checkbox", { name: "Auto export" }));
    await screen.findByTestId("settings-save-failure", {}, { timeout: 3000 });
    const footer = document.querySelector(".pref-status-bar") as HTMLElement;
    expect(within(footer).getByRole("button", { name: "Retry" }).className).toContain("btn--primary");
  });

  it("withholds the redundant Auto-record link", async () => {
    render(<SettingsCore scope="meetings" />);
    await screen.findByRole("combobox", { name: "Auto-run the summary" });
    expect(screen.queryByTestId("settings-auto-record-link")).toBeNull();
  });

  it("a failed runtime read offers a working Retry instead of a false identity", async () => {
    const base = hub.fetchStub;
    let refuse = true;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        if (refuse && new URL(String(input), "http://hub.test").pathname === "/api/system/identity") throw new TypeError("Device details unavailable");
        return base(input, init);
      }),
    );
    render(<SettingsCore scope="system" />);
    fireEvent.click(await screen.findByRole("tab", { name: "Details" }));
    const failure = await screen.findByTestId("runtime-unreadable");
    expect(screen.queryByTestId("runtime-backend")).toBeNull();
    refuse = false;
    fireEvent.click(within(failure.parentElement!).getByRole("button", { name: "Retry" }));
    await screen.findByTestId("runtime-backend");
    expect(screen.queryByTestId("runtime-unreadable")).toBeNull();
  });
});

describe("Settings remote access and identity", () => {
  it("issues a token after a press, retains it across tabs and revokes only the selection", async () => {
    render(<SettingsCore scope="system" />);
    fireEvent.click(await screen.findByRole("tab", { name: "Access" }));
    fireEvent.change(await screen.findByLabelText("Remote transport"), {
      target: { value: "ON" },
    });
    await waitFor(() => expect(screen.getByRole("button", { name: "Issue credential" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "Issue credential" }));
    fireEvent.change(screen.getByLabelText("Credential name"), {
      target: { value: "test-glass-runner" },
    });
    fireEvent.click(screen.getByTestId("issue-submit"));
    expect(await screen.findByTestId("token-value")).toHaveTextContent("hs_agent_fixture_token_shown_once");
    fireEvent.click(screen.getByRole("tab", { name: "Device" }));
    fireEvent.click(screen.getByRole("tab", { name: "Access" }));
    expect(screen.getByTestId("token-value")).toHaveTextContent("hs_agent_fixture_token_shown_once");
    fireEvent.click(within(screen.getByRole("region", { name: "Copy this token now" })).getByRole("button", { name: "Done" }));
    const list = screen.getByRole("grid", { name: "Remote credentials" });
    const revoke = within(list).getByRole("button", {
      name: "Revoke credential",
    });
    expect(revoke).toBeDisabled();
    fireEvent.click(within(list).getByText("test-glass-runner"));
    expect(list.querySelector('[role="row"] button')).toBeNull();
    fireEvent.click(revoke);
    await waitFor(() => expect(within(list).queryByText("test-glass-runner")).toBeNull());
  });
  it("keeps build and storage facts in the Details well", async () => {
    render(<SettingsCore scope="system" />);
    fireEvent.click(await screen.findByRole("tab", { name: "Details" }));
    await screen.findByTestId("runtime-backend");
    expect(screen.getByTestId("runtime-path")).toBeInTheDocument();
    expect(screen.getByTestId("runtime-path")).toHaveTextContent(identityWire.identity.database_path);
    expect(screen.getByTestId("runtime-backend")).not.toBeVisible();
    fireEvent.click(screen.getByText("Device details", {exact: true}));
    expect(screen.getByTestId("runtime-backend")).toBeVisible();
    expect(screen.getByTestId("runtime-backend").closest(".gadget-group")?.querySelector("input, select, button")).toBeNull();
  });
});

describe("W6-A: the save lamp says only this window's writes (atlas pass 3, defect 1)", () => {
  it("at open, with the settings file written just now by another writer, the bar says no Saved; a write here says Saved just now", async () => {
    hub.state.hub.writtenAt = Date.now() / 1000;
    render(<SettingsCore scope="rhythm" />);
    fireEvent.click(await screen.findByRole("tab", { name: "When" }));
    await screen.findByRole("spinbutton", { name: "Quiet from" });
    await waitFor(() => expect(hub.state.calls.some((c) => c.path === "/api/settings/hub")).toBe(true));
    expect(document.querySelector(".pref-status-bar")?.textContent ?? "").not.toMatch(/Saved/);
    fireEvent.click(screen.getByRole("button", { name: "Decrease Quiet from" }));
    await waitFor(() => expect(document.querySelector(".pref-status-bar")?.textContent ?? "").toContain("Saved just now"));
  });

  it("Saved counts per window: a You write says Saved just now on Speak too (owner decision 2026-10-28)", async () => {
    hub.state.settings.owner = { name: "Karl", aliases: [] };
    render(<SettingsCore />);
    const name = within(await screen.findByTestId("settings-owner-name")).getByRole("textbox") as HTMLInputElement;
    await waitFor(() => expect(name.value).toBe("Karl"));
    // No write in this window yet: no bar says Saved.
    expect(document.querySelector(".pref-status-bar")?.textContent ?? "").not.toMatch(/Saved/);
    fireEvent.change(name, { target: { value: "Karol Sane" } });
    fireEvent.blur(name);
    await waitFor(() => expect(hub.state.settings.owner?.name).toBe("Karol Sane"), { timeout: 3000 });
    await waitFor(() => expect(document.querySelector(".pref-status-bar")?.textContent ?? "").toContain("Saved just now"));
    fireEvent.click(screen.getByTestId("settings-index-speak"));
    await waitFor(() => expect(document.querySelector(".pref-status-bar")?.textContent ?? "").toContain("Saved just now"));
  });
});

describe("Settings › Rhythm is Rhythm's one home (Betterment setup ST1)", () => {
  it("Notify and quiet hours read and write the heartbeat; no cadence.quiet_hours row; Saved in the foot", async () => {
    // The hub half: tests/integration/test_desk_settings.py::test_quiet_hours_set_in_settings_are_what_the_heartbeat_and_cadence_read
    expect(heartbeatWire.quiet_hours).toEqual({ start: 22, end: 8 });
    render(<SettingsCore scope="rhythm" />);
    fireEvent.click(await screen.findByRole("tab", { name: "When" }));
    const from = (await screen.findByRole("spinbutton", {
      name: "Quiet from",
    })) as HTMLInputElement;
    await waitFor(() => expect(from.value).toBe("22"));
    expect(
      (
        screen.getByRole("spinbutton", {
          name: "Quiet until",
        }) as HTMLInputElement
      ).value,
    ).toBe("8");
    expect((screen.getByRole("combobox", { name: "Notify" }) as HTMLSelectElement).value).toBe(heartbeatWire.notify);
    fireEvent.click(screen.getByRole("button", { name: "Decrease Quiet from" }));
    await waitFor(() => expect(hub.state.heartbeat.quiet_hours).toEqual({ start: 21, end: 8 }));
    const puts = hub.state.calls.filter((c) => c.method === "PUT");
    expect(puts.map((c) => [c.path, c.body])).toEqual([["/api/settings/heartbeat", { quiet_hours: { start: 21 } }]]);
    fireEvent.change(screen.getByRole("combobox", { name: "Notify" }), {
      target: { value: "off" },
    });
    await waitFor(() => expect(hub.state.heartbeat.notify).toBe("off"));
    // Nothing writes the retired cadence.quiet_hours_* keys.
    expect(hub.state.calls.some((c) => c.path === "/api/settings" && c.method === "PUT")).toBe(false);
    await waitFor(() => expect(document.querySelector(".pref-status-bar")?.textContent ?? "").toMatch(/Saved/));
    expect(rawButtons(document.querySelector(".settings-page")!)).toEqual([]);
  });

  it("opens a moved brief or notice choice when a settings link names it", async () => {
    const view = render(<SettingsCore scope="rhythm::daily-brief" />);
    expect(await screen.findByRole("region", {name: "Morning brief"})).toBeInTheDocument();
    expect(screen.getByRole("spinbutton", {name: "Make at"})).toBeInTheDocument();
    view.rerender(<SettingsCore scope="rhythm::max-nudges" />);
    expect(await screen.findByRole("region", {name: "Notices"})).toBeInTheDocument();
    expect(screen.getByRole("spinbutton", {name: "Max nudges"})).toBeInTheDocument();
    expect(hub.state.calls.filter((call) => call.path === "/api/settings" && call.method === "PUT")).toEqual([]);
  });

  it("reads the sweep only after its tab opens", async () => {
    render(<SettingsCore scope="rhythm" />);
    await screen.findByRole("tab", { name: "Brief" });
    expect(hub.state.calls.some((c) => c.path.startsWith("/api/cadence/"))).toBe(false);
    fireEvent.click(screen.getByRole("tab", { name: "Brief" }));
    fireEvent.doubleClick(screen.getByText("Sweep and loops", {exact: true}));
    await screen.findByTestId("rhythm-sweep-row");
    expect(screen.queryByTestId("rhythm-headline")).toBeNull();
  });
});

describe("Settings › Meetings when the owner turned summaries off", () => {
  it("SUMMARIES OFF, with no NO MODEL and no Choose model", async () => {
    // replaces: tests/e2e/test_philo15_18_rest_of_day_glass.py::TestSummariesOffInSettingsMeetings::test_settings_meetings_says_summaries_off
    // (the hub half: tests/unit/test_philo15_18_engine_words.py::test_settings_hub_says_summaries_off_not_no_engine)
    Object.assign(hub.state.hub.meetings, {
      summariesOff: true,
      engineSet: false,
    });
    render(<SettingsCore scope="meetings" />);
    const off = await screen.findByTestId("settings-summaries-off");
    expect(off.textContent).toContain("Summaries off");
    expect(screen.queryByTestId("settings-no-model")).toBeNull();
    expect(screen.queryByTestId("settings-choose-model")).toBeNull();
  });
});

describe("Settings › Sounds without the speech extra", () => {
  it("shows speech installation on its own tab", async () => {
    const base = hub.fetchStub;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) =>
        String(input).endsWith("/api/tts/status") ? new Response(JSON.stringify({ installed: false, model_ready: false }), { status: 200 }) : base(input, init),
      ),
    );
    render(<SettingsCore scope="sounds" />);
    fireEvent.click(await screen.findByRole("tab", { name: "Speech" }));
    await screen.findByText("Browser voice");
    expect(screen.getByText("Not installed")).toBeInTheDocument();
    expect(screen.getByText("pip install 'holdspeak[line]' ".trim())).toBeVisible();
  });
});

describe("Settings › System › Remote access grants", () => {
  const W = {
    allow: "Allow filing",
    stop: "Stop filing",
    live: "Filing allowed",
    stopped: "Filing stopped",
  };
  const P = {
    allow: "Allow run and publish",
    stop: "Stop run and publish",
    live: "Run and publish allowed",
    stopped: "Run and publish stopped",
  };
  const wires = import.meta.glob("./fixtures/settings-wire/grant-*.json", {
    eager: true,
    import: "default",
  }) as Record<string, Json>;
  const grant = (name: string) => clone(wires[`./fixtures/settings-wire/grant-${name}.json`]);

  /** The grant routes on top of the Settings hub double: each answer is a recorded one. */
  function grantRoutes(routes: Record<string, () => { status: number; body: unknown; remote?: Json }>) {
    const base = hub.fetchStub;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        const method = (init?.method ?? "GET").toUpperCase();
        const path = new URL(String(input), "http://hub.test").pathname;
        const route = Object.keys(routes).find((k) => k === `${method} ${path}` || (k.endsWith("*") && `${method} ${path}`.startsWith(k.slice(0, -1))));
        if (!route) return base(input, init);
        hub.state.calls.push({ method, path });
        const { status, body, remote } = routes[route]();
        if (remote) hub.state.remote = remote;
        return new Response(JSON.stringify(body), {
          status,
          headers: { "content-type": "application/json" },
        });
      }),
    );
  }
  const foot = () => screen.getByTestId("foot-receipt");
  const list = () => screen.getByRole("grid", { name: "Remote credentials" });
  const choose = (identity: string) => fireEvent.click(within(list()).getByText(identity));
  const verb = (name: string) => within(list()).getByRole("button", { name });
  const open = async () => {
    render(<SettingsCore scope="system" />);
    fireEvent.click(await screen.findByRole("tab", { name: "Access" }));
  };

  it("allows and stops only the selected identity; a refused Stop rereads and keeps its receipt", async () => {
    hub.state.remote = grant("remote-never");
    let refuse = false;
    grantRoutes({
      "PUT /api/settings/remote/delegations/desk-agent": () => ({
        status: 200,
        body: grant("allow"),
        remote: grant("remote-live"),
      }),
      "DELETE /api/settings/remote/delegations/desk-agent": () =>
        refuse
          ? {
              status: 409,
              body: grant("stop-refused"),
              remote: grant("remote-stopped"),
            }
          : {
              status: 200,
              body: grant("stop"),
              remote: grant("remote-stopped"),
            },
    });
    await open();
    await within(list()).findByText("desk-agent");
    expect(verb(W.allow)).toBeDisabled();
    choose("desk-agent");
    expect(list().querySelector('[role="row"] button')).toBeNull();
    fireEvent.click(verb(W.allow));
    await waitFor(() => expect(verb(W.stop)).toBeEnabled());
    expect(foot()).toHaveAttribute("data-operation-id", grant("allow").operation_id);
    fireEvent.click(verb(W.stop));
    await waitFor(() => expect(verb(W.allow)).toBeEnabled());
    fireEvent.click(verb(W.allow));
    await waitFor(() => expect(verb(W.stop)).toBeEnabled());
    refuse = true;
    fireEvent.click(verb(W.stop));
    expect(await screen.findByTestId("grant-refused")).toHaveAttribute("data-code", "desk_delegation_required");
    await waitFor(() => expect(verb(W.allow)).toBeEnabled());
    await waitFor(() => expect(foot()).toHaveTextContent("Refused"));
    fireEvent.click(foot());
    expect(await screen.findByTestId("grant-receipt")).toHaveTextContent("desk-agent");
  });

  it("revokes the selected credential and keeps the grant receipt after its row leaves", async () => {
    hub.state.remote = grant("remote-live");
    grantRoutes({
      "DELETE /api/settings/remote/credentials/*": () => ({
        status: 200,
        body: grant("revoke-credential"),
        remote: { ...grant("remote-live"), credentials: [] },
      }),
    });
    await open();
    await within(list()).findByText("desk-agent");
    choose("desk-agent");
    fireEvent.click(verb("Revoke credential"));
    await waitFor(() => expect(within(list()).queryByText("desk-agent")).toBeNull());
    await waitFor(() => expect(foot()).toHaveTextContent("Stopped"));
  });

  it("keeps grants visible with the transport off, including an orphan that can still be stopped", async () => {
    hub.state.remote = grant("remote-orphan-off");
    grantRoutes({
      "DELETE /api/settings/remote/delegations/orphan-agent": () => ({
        status: 200,
        body: grant("stop"),
        remote: { ...grant("remote-orphan-off"), delegations: [] },
      }),
    });
    await open();
    await within(list()).findByText("orphan-agent");
    expect(within(list()).getByText("No credential")).toBeInTheDocument();
    choose("orphan-agent");
    expect(verb("Revoke credential")).toBeDisabled();
    expect(verb("Issue credential")).toBeDisabled();
    fireEvent.click(verb(W.stop));
    await waitFor(() => expect(within(list()).queryByText("orphan-agent")).toBeNull());
    expect(within(list()).getByText("desk-agent")).toBeInTheDocument();
  });

  it("keeps an active stopped grant visible with transport off and can allow it again", async () => {
    hub.state.remote = grant("remote-off-live");
    hub.state.remote.credentials[0].project_delegations = [];
    grantRoutes({
      "DELETE /api/settings/remote/delegations/desk-agent": () => ({
        status: 200,
        body: grant("stop"),
        remote: { ...grant("remote-orphan-off"), delegations: [] },
      }),
      "PUT /api/settings/remote/delegations/desk-agent": () => ({
        status: 200,
        body: grant("allow"),
        remote: grant("remote-off-live"),
      }),
    });
    await open();
    await within(list()).findByText("desk-agent");
    expect(within(list()).queryByText("sweep-runner")).toBeNull();
    choose("desk-agent");
    fireEvent.click(verb(W.stop));
    await waitFor(() => expect(within(list()).getByText("Filing stopped")).toBeInTheDocument());
    choose("desk-agent");
    expect(verb(W.allow)).toBeEnabled();
    expect(within(list()).getByText("Filing stopped")).toBeInTheDocument();
    fireEvent.click(verb(W.allow));
    await waitFor(() => expect(foot()).toHaveTextContent("Allowed"));
    choose("desk-agent");
    expect(verb(W.stop)).toBeEnabled();
  });

  it("an expired grant says Filing stopped and offers Allow only after selection", async () => {
    hub.state.remote = grant("remote-expired");
    await open();
    await within(list()).findByText("desk-agent");
    expect(within(list()).getByText("Filing stopped")).toBeInTheDocument();
    expect(verb(W.allow)).toBeDisabled();
    choose("desk-agent");
    expect(verb(W.allow)).toBeEnabled();
  });

  it("a project choice changes only that project; a refused Stop keeps the acknowledged state", async () => {
    const live = grant("remote-project-live");
    const never = clone(live);
    never.credentials[1].project_delegations = [];
    hub.state.remote = never;
    const [pay, hire] = grant("projects").projects;
    const stopped = clone(live);
    stopped.credentials[1].project_delegations[0].state = "REVOKED";
    grantRoutes({
      "GET /api/projects": () => ({ status: 200, body: grant("projects") }),
      [`PUT /api/settings/remote/delegations/sweep-runner/projects/${pay.id}`]: () => ({ status: 200, body: grant("project-allow"), remote: live }),
      [`DELETE /api/settings/remote/delegations/sweep-runner/projects/${pay.id}`]: () => ({
        status: 409,
        body: grant("project-stop-refused"),
        remote: stopped,
      }),
    });
    await open();
    await within(list()).findByText("sweep-runner");
    choose("sweep-runner");
    expect(verb(W.allow)).toBeDisabled();
    fireEvent.click(verb("Projects…"));
    const access = await screen.findByRole("combobox", {
      name: `${pay.name} access`,
    });
    expect(access).toHaveValue("stop");
    fireEvent.change(access, { target: { value: "allow" } });
    await waitFor(() => expect(access).toHaveValue("allow"));
    expect(screen.getByRole("combobox", { name: `${hire.name} access` })).toHaveValue("stop");
    expect(screen.getByRole("grid", { name: "Project access" }).querySelector('[role="row"] button')).toBeNull();
    fireEvent.change(access, { target: { value: "stop" } });
    expect(await screen.findByTestId("grant-refused")).toHaveAttribute("data-code", "project_delegation_required");
    await waitFor(() => expect(access).toHaveValue("stop"));
  });
});

describe("Settings category face", () => {
  it("opens You, shows one category at a time, and navigates as the owner does", async () => {
    const state = hub.state;
    const { container } = render(<SettingsCore />);
    await screen.findByTestId("settings-page");
    const sections = Array.from(container.querySelectorAll("[data-settings-section]")).map((section) => section.getAttribute("data-settings-section"));
    expect(sections).toEqual(["you", "engines", "speak", "meetings", "notices", "accounts", "calls", "agents", "desk", "this-mac"]);
    expect(screen.getByRole("navigation", { name: "Settings sections" })).toBeInTheDocument();
    expect(screen.getByTestId("settings-index-you")).toHaveAttribute("aria-current", "true");
    expect(container.querySelector('[data-settings-section="you"]')).not.toHaveAttribute("hidden");
    expect(container.querySelector('[data-settings-section="speak"]')).toHaveAttribute("hidden");
    expect(screen.queryByRole("combobox", { name: "Language" })).toBeNull();

    fireEvent.click(screen.getByTestId("settings-index-notices"));
    fireEvent.click(screen.getByRole("tab", {name:"When"}));
    expect(screen.getByText("Quiet from")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("settings-index-this-mac"));
    expect(screen.queryByTestId("settings-engines-page-link")).toBeNull();
    expect(screen.queryByTestId("settings-setup-page-link")).toBeNull();
    expect(container.querySelector('[data-settings-section="notices"]')).toHaveAttribute("hidden");
    expect(screen.getByTestId("settings-index-this-mac")).toHaveAttribute("aria-current", "true");
    await waitFor(() => expect(state.calls.some((call) => call.method === "GET" && call.path === "/api/calendar/sources")).toBe(true));
  });

  it("keeps a local select draft mounted while the owner visits another category", async () => {
    render(<SettingsCore scope="voice" />);
    const language = await screen.findByRole("combobox", { name: "Language" });
    fireEvent.change(language, { target: { value: "pl" } });
    fireEvent.click(screen.getByTestId("settings-index-accounts"));
    expect(screen.queryByRole("combobox", { name: "Language" })).toBeNull();
    fireEvent.click(screen.getByTestId("settings-index-speak"));
    expect(screen.getByRole("combobox", { name: "Language" })).toHaveValue("pl");
  });
  it("opens a legacy Notices row at Quiet hours and lights the row", async () => {
    const { container } = render(<SettingsCore scope="rhythm::quiet-hours" />);
    await screen.findByTestId("settings-page");
    expect(screen.getByTestId("settings-index-notices")).toHaveAttribute("aria-current", "true");
    expect(container.querySelector('[data-settings-section="notices"] .gadget-row[data-highlight]')).toBeTruthy();
  });
});

/** The phone frame's one Back, as SurfaceWindows wires it: a core that holds
 *  the Back gets the press; otherwise the Back closes the window. */
function PhoneSettingsWindow({ scope, onClose }: { scope?: string; onClose: () => void }) {
  const [back, setBack] = useState<WindowBack | null>(null);
  return (
    <BackSlotContext.Provider value={setBack}>
      <button className="btn" data-testid={back?.testId ?? "frame-back"} onClick={back?.onBack ?? onClose}>
        Back
      </button>
      <SettingsCore scope={scope} />
    </BackSlotContext.Provider>
  );
}

describe("Settings at phone width: Back returns where the owner came from", () => {
  const realMatchMedia = window.matchMedia;
  beforeEach(() => {
    window.matchMedia = ((query: string) => ({
      matches: query === "(max-width: 720px)",
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
  });
  afterEach(() => {
    window.matchMedia = realMatchMedia;
  });

  it("a pane opened by a scope (a receipt): the frame's Back closes the window", async () => {
    const onClose = vi.fn();
    render(<PhoneSettingsWindow scope="rhythm::quiet-hours" onClose={onClose} />);
    const page = await screen.findByTestId("settings-page");
    expect(page).toHaveAttribute("data-pane-open", "true");
    await screen.findByText("Quiet from");
    // Settings does not hold the Back: no settings-back, the frame's own Back.
    expect(screen.queryByTestId("settings-back")).toBeNull();
    fireEvent.click(screen.getByTestId("frame-back"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("a pane opened from the rail: the frame's Back returns to the rail, then closes", async () => {
    const onClose = vi.fn();
    render(<PhoneSettingsWindow onClose={onClose} />);
    const page = await screen.findByTestId("settings-page");
    expect(page).not.toHaveAttribute("data-pane-open");
    fireEvent.click(screen.getByTestId("settings-index-notices"));
    expect(page).toHaveAttribute("data-pane-open", "true");
    fireEvent.click(await screen.findByTestId("settings-back"));
    expect(onClose).not.toHaveBeenCalled();
    expect(page).not.toHaveAttribute("data-pane-open");
    expect(screen.queryByTestId("settings-back")).toBeNull();
    fireEvent.click(screen.getByTestId("frame-back"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

/* The language (2026-11-11): Settings › Engines, on the hub's own recorded
 * answers (tests/integration/test_desk_runs_on_hub.py and
 * scripts/record_engines_fixture.py). Only the engine reads are added to
 * the hub double; every other answer is the one above. */
describe("Settings › Engines: the chain, its readiness and the spend limit", () => {
  type Gets = Record<string, unknown>;
  function engines(gets: Gets, posts: Record<string, (body: Json) => { answer: unknown; next?: Gets }> = {}) {
    let now = gets;
    const sent: Array<{ path: string; body: Json }> = [];
    const base = hub.fetchStub;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        const path = new URL(String(input), "http://hub.test").pathname;
        const method = (init?.method ?? "GET").toUpperCase();
        const answer = (body: unknown) =>
          new Response(JSON.stringify(body), {
            status: 200,
            headers: { "content-type": "application/json" },
          });
        if (method === "GET" && path in now) return answer(now[path]);
        if (method === "POST" && posts[path]) {
          const body = JSON.parse(String(init?.body ?? "{}"));
          if (path !== "/api/inference/assignments/editor") sent.push({ path, body });
          const next = posts[path](body);
          if (next.next) now = next.next;
          return answer(next.answer);
        }
        return base(input, init);
      }),
    );
    return sent;
  }

  it("an engine that does not answer is a state cell; no progress strip, Set up plate or row button", async () => {
    engines(
      {
        "/api/concierge/detect": downDetect.wire,
        "/api/inference/assignments": downRoster.wire,
      },
      {
        "/api/inference/assignments/editor": () => ({
          answer: downEditor.wire,
        }),
      },
    );
    const { container } = render(<SettingsCore scope="engines" />);
    await screen.findByText("Not answering");
    expect(screen.queryByTestId("settings-engines-plate")).toBeNull();
    expect(screen.queryByTestId("settings-engines-spine")).toBeNull();
    expect(container.querySelectorAll("[data-settings-section=engines] [role=row] button")).toHaveLength(0);
  });

  it("changing the default order writes the chain and renders the acknowledged order in the mast", async () => {
    let at = chainRecorded.steps[0];
    const reordered = chainRecorded.steps[1];
    const sent = engines(chainRecorded.gets, {
      "/api/inference/assignments/editor": (body) => {
        const row = WHAT_ROWS.find((row) => JSON.stringify(row.scope) === JSON.stringify(body.scope))!;
        return { answer: at.editors[row.id as keyof typeof at.editors] };
      },
      "/api/inference/assignments/set": () => {
        at = reordered;
        return { answer: reordered.answer };
      },
    });
    render(<SettingsCore scope="models" />);
    const choice = await screen.findByRole("combobox", {
      name: "Everything else engines",
    });
    await waitFor(() => expect(within(choice).getByRole("option", { name: "Codex, then Gemini CLI" })).toBeInTheDocument());
    expect(sent).toEqual([]);
    fireEvent.change(choice, { target: { value: "order" } });
    fireEvent.click(within(screen.getByRole("grid", {name:"Engine order"})).getByText("Gemini CLI"));
    fireEvent.click(screen.getByRole("button", { name: "Move up" }));
    await waitFor(() => expect(screen.getByTestId("settings-engines-receipt")).toHaveTextContent("Gemini CLI, then Codex"));
    expect(sent).toHaveLength(1);
    expect(sent[0].body).toMatchObject({
      scope: { kind: "global" },
      entries: reordered.body!.entries,
      expected_revision: reordered.body!.expected_revision,
    });
    expect(screen.getByTestId("settings-engines-receipt")).toHaveTextContent("Everything else → Gemini CLI, then Codex");
  });

  it("an agent CLI's spend limit: Inspect and Spend limit open the field; Save sends the limit; the row says it", async () => {
    type Step = { name: string; gets: Gets; answer?: unknown };
    const steps = enginesRecorded.claude.steps as Step[];
    const step = (name: string) => steps.find((entry) => entry.name === name)!;
    const sent = engines(step("spent").gets, {
      "/api/inference/model-library/connect-cli-engine": () => ({
        answer: step("limit").answer,
        next: step("limit").gets,
      }),
    });
    render(<SettingsCore scope="engines" />);
    fireEvent.click(await screen.findByRole("tab", { name: "Engines" }));
    fireEvent.click(await screen.findByRole("button", { name: "Model library" }));
    const row = await screen.findByTestId("settings-engine-agent-claude");
    fireEvent.doubleClick(row);
    const inspector = screen.getByRole("region", { name: "Claude Code" });
    fireEvent.click(within(inspector).getByRole("button", { name: "Spend limit" }));
    expect(within(inspector).getByLabelText("Spend limit per run")).toHaveValue("");
    fireEvent.change(within(inspector).getByLabelText("Spend limit per run"), {
      target: { value: "0.50" },
    });
    fireEvent.click(within(inspector).getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.getByTestId("settings-engines-receipt")).toHaveTextContent("Spend limit $0.50 per run"));
    await within(inspector).findByRole("button", { name: "No limit" });
    fireEvent.click(within(inspector).getByRole("button", { name: "Spend limit" }));
    fireEvent.click(within(inspector).getByRole("button", { name: "Spend limit" }));
    expect(within(inspector).getByLabelText("Spend limit per run")).toHaveValue("0.50");
    expect(sent[0].body.draft).toMatchObject({
      preset: "claude",
      profile_id: "agent-claude",
      spend_limit_usd: 0.5,
    });
  });
});

describe("Settings: the rail has names and attention dots", () => {
  it("carries reasons in accessible titles, with no status fragments or progress bars", async () => {
    render(<SettingsCore />);
    const rail = await screen.findByRole("navigation", {
      name: "Settings sections",
    });
    expect(rail.textContent).not.toMatch(/engine yet|connected|Up to|Every 15|This Mac only/);
    expect(screen.queryByTestId("settings-index-engines-health")).toBeNull();
    expect(rail.querySelector(".surface-spine")).toBeNull();
  });
});

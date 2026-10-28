// The Settings app (the test diet, 2026-10-11): the browser tests of the
// Settings window, moved to the real SettingsCore with its real hooks. Only
// `fetch` is replaced, and it answers with the hub's OWN answers, recorded
// from a live hub by tests/integration/test_desk_settings.py (which also
// proves no fixture carries a field the hub does not send: the scar law).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SettingsCore } from "../../pages/cores/SettingsCore";
import { PREF_MODULES } from "../../pages/cores/settingsPrefs";
import connectionsWire from "./fixtures/connections-wire/connections-cold.json";
import destinationsWire from "./fixtures/destinations-wire/list-empty.json";
import authorityWire from "./fixtures/settings-wire/authority-policy.json";
import calendarWire from "./fixtures/settings-wire/calendar-sources.json";
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
    calls: [] as Array<{ method: string; path: string; body?: Json; keepalive?: boolean }>,
    unknown: [] as string[],
  };
  const answer = (status: number, body: unknown) =>
    new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
  const fetchStub = vi.fn(async (input: string, init?: RequestInit) => {
    const method = (init?.method ?? "GET").toUpperCase();
    const path = new URL(String(input), "http://hub.test").pathname;
    const body = init?.body ? (JSON.parse(String(init.body)) as Json) : undefined;
    state.calls.push({ method, path, body, keepalive: init?.keepalive });
    const key = `${method} ${path}`;
    switch (key) {
      case "GET /api/settings": return answer(200, state.settings);
      case "GET /api/connections": return answer(200, connectionsWire);
      case "GET /api/channels/destinations": return answer(200, destinationsWire);
      case "PUT /api/settings": {
        // Mirror the producer's required symbol fields instead of accepting
        // the invalid blank row that Add used to send to the live hub.
        const symbols = body?.dictation?.spoken_symbols;
        if (Array.isArray(symbols)) {
          const invalid = symbols.findIndex((entry: Json) => !String(entry.spoken ?? "").trim() || !String(entry.symbol ?? ""));
          if (invalid >= 0) return answer(400, { error: `spoken_symbols[${invalid}]: the spoken phrase and symbol must not be empty` });
        }
        for (const [k, v] of Object.entries(body ?? {})) {
          if (k.startsWith("_")) continue;
          state.settings[k] = typeof v === "object" && v && !Array.isArray(v) ? { ...state.settings[k], ...v } : v;
        }
        return answer(200, { ...clone(settingsPutWire), settings: state.settings });
      }
      case "GET /api/settings/hub": return answer(200, state.hub);
      // Betterment setup ST1: Settings ▸ Rhythm reads and writes the one
      // quiet-hours store, the heartbeat policy (recorded answers).
      case "GET /api/settings/heartbeat": return answer(200, state.heartbeat);
      case "PUT /api/settings/heartbeat": {
        const next = clone(state.heartbeat);
        if (body?.notify) next.notify = body.notify;
        if (body?.quiet_hours) next.quiet_hours = { ...next.quiet_hours, ...body.quiet_hours };
        state.heartbeat = { ...clone(heartbeatPutWire), ...next };
        return answer(200, state.heartbeat);
      }
      case "GET /api/authority/policy": return answer(200, authorityWire);
      case "GET /api/calendar/sources": return answer(200, state.calendar);
      case "GET /api/settings/people-access": return answer(200, peopleWire);
      case "GET /api/settings/remote": return answer(200, state.remote);
      case "PUT /api/settings/remote": {
        state.remote = { ...clone(remoteOnWire), credentials: [], total_count: 0, active_count: 0, enabled: Boolean(body?.enabled) };
        state.hub.system.remote = Boolean(body?.enabled);
        return answer(200, { success: true, enabled: Boolean(body?.enabled) });
      }
      case "POST /api/settings/remote/credentials": {
        const issued = { ...clone(remoteIssueWire), identity: body?.identity, id: `id-${body?.identity}` };
        const row = { ...clone(remoteOnWire.credentials[0]), id: issued.id, identity: body?.identity, last_used_at: null };
        state.remote.credentials = [...state.remote.credentials, row];
        state.remote.total_count = state.remote.credentials.length;
        state.remote.active_count = state.remote.credentials.length;
        return answer(200, issued);
      }
      case "GET /api/system/identity": return answer(200, identityWire);
      case "GET /api/projects": return answer(200, projectsWire);
      case "GET /api/setup/found": return answer(200, setupFoundWire);
      case "POST /api/setup/lan": return answer(200, { rows: [] });
      case "GET /api/setup/status": return answer(200, setupStatusWire);
      case "GET /api/setup/local-ai": return answer(200, localAiWire.wire);
      case "GET /api/concierge/detect": return answer(200, enginesWire.wire);
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
const LIBRARY = ["btn", "btn--chrome", "surface-ledger-line", "gadget-cycle", "desk-mic", "gadget-stepper-btn",
  "gadget-table-add", "gadget-table-delete", "gadget-fold-toggle", "surface-edit-in-place", "surface-disclosure-trigger",
  "gadget-transport-key"];
const rawButtons = (root: ParentNode) =>
  Array.from(root.querySelectorAll("button"))
    .filter((b) => !LIBRARY.some((c) => b.classList.contains(c)) && !b.closest(".gadget-stepper, .gadget-table"))
    .map((b) => (b.textContent ?? "").trim().slice(0, 40));

const ledgerRow = (name: string) =>
  Array.from(document.querySelectorAll(".surface-ledger-row")).find(
    (row) => row.querySelector(".surface-ledger-primary")?.textContent === name,
  ) as HTMLElement | undefined;

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
    await waitFor(() => expect(hub.state.settings.owner).toEqual({ name: "Karol Sane", aliases: ["Carol"] }), { timeout: 3000 });
    expect(within(screen.getByTestId("settings-owner-aliases")).getByText("Carol")).toBeInTheDocument();

    fireEvent.change(alias, { target: { value: "Karolek" } });
    fireEvent.keyDown(alias, { key: "Enter" });
    act(() => { window.dispatchEvent(new Event("pagehide")); });
    const leave = hub.state.calls.filter((c) => c.method === "PUT" && c.path === "/api/settings" && c.keepalive);
    expect(leave.at(-1)?.body?.owner).toEqual({ name: "Karol Sane", aliases: ["Carol", "Karolek"] });
  });
});

describe("Settings › Meetings", () => {
  const meetingsText = () => document.querySelector("[data-settings-section=meetings]")?.textContent ?? "";
  const summaryRow = () => screen.getByTestId("settings-summary-controls").closest(".gadget-row") as HTMLElement;

  it("cold: After every meeting, the cycle, Summaries run on No engine + Engines › and no egress chip; Mic device, Auto export; Summary, never Intelligence", async () => {
    // replaces: tests/e2e/test_hs172_settings_meetings_glass.py::TestSettingsMeetingsAutoRun::test_settings_meetings_nomodel
    const { container } = render(<SettingsCore scope="meetings" />);
    await screen.findByRole("combobox", { name: "Auto-run the summary" });
    expect(screen.queryByTestId("meetings-auto-display")).toBeNull();
    expect(screen.getByRole("option", { name: "Manual" })).toBeInTheDocument();
    await screen.findByTestId("settings-no-model");
    expect(container.querySelectorAll(".gadget-cycle select").length).toBeGreaterThanOrEqual(1);
    expect(summaryRow().querySelector(".surface-state-chip[data-state='warning']")).not.toBeNull();
    expect(summaryRow().querySelector(".gadget-chip-egress")).toBeNull();
    // Betterment setup ST1: the engine is a fact line; Engines is its home.
    expect(summaryRow().querySelector(".gadget-row-label")?.textContent).toBe("Summaries run on");
    expect(screen.getByTestId("settings-no-model").textContent).toContain("No engine");
    expect(screen.getByTestId("settings-engines-link").textContent).toBe("Engines ›");
    for (const word of ["Mic device", "Auto export", "Summary"]) expect(meetingsText()).toContain(word);
    expect(meetingsText()).not.toContain("Intelligence");
    expect(rawButtons(container.querySelector(".settings-page")!)).toEqual([]);
  });

  it("a summary engine on the LAN: its host on the egress chip, no NO MODEL, no Choose model", async () => {
    // replaces: tests/e2e/test_hs172_settings_meetings_glass.py::TestSettingsMeetingsAutoRun::test_settings_meetings_with_host
    Object.assign(hub.state.hub.meetings, { engineSet: true, host: "192.168.1.43", engine: "Qwen 27B" });
    const { container } = render(<SettingsCore scope="meetings" />);
    await waitFor(() => expect(summaryRow().querySelector(".gadget-chip-egress")?.textContent).toBe("192.168.1.43 · LAN"));
    expect(screen.queryByTestId("settings-no-model")).toBeNull();
    expect(summaryRow().textContent).toContain("Qwen 27B");
    fireEvent.click(screen.getByTestId("settings-engines-link"));
    await waitFor(() => expect(openEngines).toHaveBeenCalled());
    expect(meetingsText()).toContain("Mic device");
    expect(rawButtons(container.querySelector(".settings-page")!)).toEqual([]);
  });

  it("Auto-record links to Meetings Record; Meetings has no calendar block (Betterment setup ST1)", async () => {
    // replaces: tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_calendar_section (the auto-record leg)
    hub.state.settings.calendar = { ...hub.state.settings.calendar, sources: [{ id: "src-work", label: "WORK", url: "/Users/owner/work.ics", enabled: true }] };
    hub.state.calendar = { ...clone(calendarOneWire), matched_this_week: 1 };
    hub.state.settings.meeting.auto_record = "room_linked";
    render(<SettingsCore scope="meetings" />);
    const auto = await screen.findByTestId("settings-auto-record");
    expect(within(auto).getByTestId("settings-auto-record-link").textContent).toBe("Meetings › Record");
    expect(auto.querySelector("select")).toBeNull();
    // Betterment setup ST1: Calendar's one home is Accounts.
    const meetings = document.querySelector('[data-settings-section="meetings"]')!;
    expect(meetings.querySelector(".prefs-calendar-section")).toBeNull();
    expect(within(meetings as HTMLElement).queryByTestId("calendar-source-src-work")).toBeNull();
    expect(within(meetings as HTMLElement).queryByTestId("calendar-connect-row")).toBeNull();
    expect(document.querySelectorAll(".prefs-calendar-section")).toHaveLength(1);
  });

  it("Accounts holds the calendar: the source row, Add feed and Import image; no zero counter (Betterment setup ST1)", async () => {
    // replaces: tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_calendar_section (the source rows, moved to Accounts)
    hub.state.settings.calendar = { ...hub.state.settings.calendar, sources: [{ id: "src-work", label: "WORK", url: "/Users/owner/work.ics", enabled: true }] };
    hub.state.calendar = { ...clone(calendarOneWire), matched_this_week: 1 };
    render(<SettingsCore scope="integrations" />);
    const row = await screen.findByTestId("calendar-source-src-work");
    expect(within(row).getByText("Calendar feed")).toBeInTheDocument();
    expect(within(row).queryByText("THIS DEVICE")).toBeNull();
    fireEvent.click(within(row).getByRole("button", { name: "Edit" }));
    for (const verb of ["Disable", "Remove"]) expect(within(row.closest(".surface-ledger-row") as HTMLElement).getByRole("button", { name: verb })).toBeInTheDocument();
    const connect = screen.getByTestId("calendar-connect-row");
    expect(within(connect).getByRole("button", { name: "Add feed" })).toBeInTheDocument();
    expect(within(connect).getByRole("button", { name: "Import image" })).toBeInTheDocument();
    // Accounts' own Calendar row chooses a calendar; no "Add calendar" goes round.
    expect(within(connect).queryByRole("button", { name: "Add calendar" })).toBeNull();
    expect(document.querySelector(".prefs-calendar-section")?.textContent ?? "").not.toMatch(/\b0\s+(SOURCE|CALENDAR|EVENT|RECORDING|MATCHED)/i);
    expect(rawButtons(document.querySelector(".prefs-calendar-section")!)).toEqual([]);
  });

  it("Add unfolds the connect well in Accounts: the field names ICS, carries the mic, Cancel and Save", async () => {
    // replaces: tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_calendar_well_unfold
    render(<SettingsCore scope="integrations" />);
    fireEvent.click(await screen.findByTestId("calendar-add-btn"));
    const well = screen.getByTestId("calendar-well");
    expect(within(well).getByRole("textbox", { name: "Calendar URL or file path" }).getAttribute("placeholder")).toMatch(/ICS|file/);
    expect(well.querySelector(".desk-mic")).not.toBeNull();
    expect(within(well).getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    expect(within(well).getByRole("button", { name: "Save" })).toBeInTheDocument();
  });

  it("Auto-record stays a link when OFF", async () => {
    // replaces: tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_matched_absent_when_zero
    hub.state.calendar = { ...clone(calendarOneWire), auto_record: "off", matched_this_week: 1 };
    render(<SettingsCore scope="meetings" />);
    const auto = await screen.findByTestId("settings-auto-record");
    await waitFor(() => expect(hub.state.calls.some((c) => c.path === "/api/calendar/sources")).toBe(true));
    expect(within(auto).getByTestId("settings-auto-record-link")).toHaveTextContent("Meetings › Record");
  });
});

describe("Settings repair: ordinary choices and recoverable writes", () => {
  it("composes Meetings into related columns while keeping all ordinary groups present", async () => {
    const { container } = render(<SettingsCore scope="meetings" />);
    await screen.findByRole("combobox", { name: "Auto-run the summary" });
    const columns = container.querySelectorAll('[data-settings-section="meetings"] .surface-columns[data-variant="preferences"] > div');
    expect(columns).toHaveLength(2);
    expect(columns[0].textContent).toContain("Summary");
    expect(columns[0].textContent).toContain("Recording");
    // Betterment setup ST1: the calendar block moved to Accounts.
    expect(columns[1].textContent).not.toContain("Calendar");
    expect(columns[1].textContent).toContain("Export");
    expect(screen.getByRole("checkbox", { name: "Auto export" })).toBeInTheDocument();
  });

  it("keeps incomplete symbols local, then sends complete fields and armed Forget through the writer", async () => {
    const { container } = render(<SettingsCore scope="voice" />);
    await screen.findByTestId("settings-index-speak");
    const speak = within(document.querySelector('[data-settings-section="speak"]') as HTMLElement);
    await speak.findByRole("combobox", { name: "Language" });
    vi.useFakeTimers();
    const puts = () => hub.state.calls.filter((call) => call.method === "PUT" && call.path === "/api/settings");
    const symbols = speak.getByRole("region", { name: "Spoken symbols" });
    expect(within(symbols).getAllByRole("button", { name: "Add symbol" })).toHaveLength(1);
    expect(within(symbols).getByRole("button", { name: "Add symbol" }).closest(".gadget-group-actions")).toBeTruthy();
    expect(container.querySelector(".gadget-table-head")).toBeNull();
    fireEvent.click(within(symbols).getByRole("button", { name: "Add symbol" }));
    expect(within(symbols).getByRole("textbox", { name: "Spoken phrase 1" })).toBeInTheDocument();
    expect(container.querySelector('.gadget-table[data-layout="fields"]')).toBeTruthy();
    await act(async () => { await vi.advanceTimersByTimeAsync(800); });
    expect(puts()).toHaveLength(0);
    expect(within(symbols).getByText("Draft")).toBeInTheDocument();
    fireEvent.change(within(symbols).getByRole("textbox", { name: "Spoken phrase 1" }), { target: { value: "right arrow" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(800); });
    expect(puts()).toHaveLength(0);
    fireEvent.change(within(symbols).getByRole("textbox", { name: "Symbol 1" }), { target: { value: "→" } });
    fireEvent.change(within(symbols).getByRole("combobox", { name: "Attachment 1" }), { target: { value: "right" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(800); });
    expect(puts().at(-1)?.body?.dictation).toEqual({ spoken_symbols: [{ spoken: "right arrow", symbol: "→", attach: "right" }] });
    expect(hub.state.settings.dictation.spoken_symbols).toEqual([{ spoken: "right arrow", symbol: "→", attach: "right" }]);
    expect(within(symbols).queryByText("Draft")).toBeNull();
    fireEvent.click(within(symbols).getByRole("button", { name: "Add symbol" }));
    expect(within(symbols).getAllByRole("button", { name: "Add symbol" })).toHaveLength(1);
    expect(within(symbols).getByRole("textbox", { name: "Spoken phrase 1" })).toHaveValue("right arrow");
    expect(within(symbols).getByRole("textbox", { name: "Symbol 2" })).toHaveValue("");
    expect(within(symbols).getByRole("combobox", { name: "Attachment 2" })).toHaveValue("none");
    const forgetBlank = within(symbols).getByRole("button", { name: "Forget symbol 2" });
    fireEvent.click(forgetBlank);
    expect(forgetBlank).toHaveTextContent("Forget?");
    expect(within(symbols).getByRole("textbox", { name: "Spoken phrase 2" })).toBeInTheDocument();
    fireEvent.click(forgetBlank);
    expect(within(symbols).queryByRole("textbox", { name: "Spoken phrase 2" })).toBeNull();
    const forgetSaved = within(symbols).getByRole("button", { name: "Forget symbol 1" });
    fireEvent.click(forgetSaved);
    fireEvent.click(forgetSaved);
    await act(async () => { await vi.advanceTimersByTimeAsync(800); });
    expect(hub.state.settings.dictation.spoken_symbols).toEqual([]);
    expect(puts().at(-1)?.body?.dictation).toEqual({ spoken_symbols: [] });
    expect(within(symbols).queryByText("Draft")).toBeNull();
  });

  it("keeps newer incomplete symbols through another write, refusal, Back, and Retry", async () => {
    const base = hub.fetchStub;
    let refuseSymbols = true;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      const path = new URL(String(input), "http://hub.test").pathname;
      const body = init?.body ? JSON.parse(String(init.body)) as Json : undefined;
      if (refuseSymbols && init?.method === "PUT" && path === "/api/settings" && body?.dictation?.spoken_symbols) throw new TypeError("Symbols connection lost");
      return base(input, init);
    }));
    render(<SettingsCore scope="voice" />);
    await screen.findByTestId("settings-index-speak");
    const speak = within(document.querySelector('[data-settings-section="speak"]') as HTMLElement);
    await speak.findByRole("combobox", { name: "Language" });
    const symbols = speak.getByRole("region", { name: "Spoken symbols" });
    vi.useFakeTimers();
    fireEvent.click(within(symbols).getByRole("button", { name: "Add symbol" }));
    fireEvent.change(within(symbols).getByRole("textbox", { name: "Spoken phrase 1" }), { target: { value: "right arrow" } });
    fireEvent.change(speak.getByRole("combobox", { name: "Language" }), { target: { value: "pl" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(800); });
    expect(hub.state.settings.model.language).toBe("pl");
    expect(within(symbols).getByRole("textbox", { name: "Spoken phrase 1" })).toHaveValue("right arrow");
    expect(within(symbols).getByRole("textbox", { name: "Symbol 1" })).toHaveValue("");
    fireEvent.change(within(symbols).getByRole("textbox", { name: "Symbol 1" }), { target: { value: "→" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(800); });
    expect(screen.getByTestId("settings-save-failure")).toBeInTheDocument();
    fireEvent.change(within(symbols).getByRole("textbox", { name: "Symbol 1" }), { target: { value: "" } });
    fireEvent.change(within(symbols).getByRole("textbox", { name: "Spoken phrase 1" }), { target: { value: "new arrow" } });
    fireEvent.click(screen.getByTestId("settings-index-accounts"));
    fireEvent.click(screen.getByTestId("settings-index-speak"));
    expect(within(symbols).getByRole("textbox", { name: "Spoken phrase 1" })).toHaveValue("new arrow");
    expect(within(symbols).getByRole("textbox", { name: "Symbol 1" })).toHaveValue("");
    refuseSymbols = false;
    fireEvent.click(within(screen.getByTestId("settings-save-failure")).getByRole("button", { name: "Retry" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(800); });
    expect(hub.state.settings.dictation.spoken_symbols).toEqual([{ spoken: "right arrow", symbol: "→", attach: "none" }]);
    expect(within(symbols).getByRole("textbox", { name: "Spoken phrase 1" })).toHaveValue("new arrow");
    expect(within(symbols).getByRole("textbox", { name: "Symbol 1" })).toHaveValue("");
    expect(within(speak.getByRole("region", { name: "Spoken symbols" })).getByText("Draft")).toBeInTheDocument();
    fireEvent.change(within(symbols).getByRole("textbox", { name: "Symbol 1" }), { target: { value: "⇒" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(800); });
    expect(hub.state.settings.dictation.spoken_symbols).toEqual([{ spoken: "new arrow", symbol: "⇒", attach: "none" }]);
    expect(within(symbols).queryByText("Draft")).toBeNull();
  });

  it("keeps hold-key capture active through a preference rerender and Escape cancels it", async () => {
    render(<SettingsCore scope="voice" />);
    await screen.findByRole("combobox", { name: "Language" });
    const typing = screen.getByRole("region", { name: "Voice typing" });
    expect(within(typing).getByRole("checkbox", { name: "Preview before type" })).toBeInTheDocument();
    expect(within(typing).getByRole("checkbox", { name: "Voice commands" })).toBeInTheDocument();
    const key = within(typing).getByRole("button", { name: /^Push-to-talk key:/ });
    const before = key.getAttribute("aria-label");
    fireEvent.click(key);
    fireEvent.change(within(typing).getByRole("combobox", { name: "Language" }), { target: { value: "pl" } });
    expect(within(typing).getByRole("button", { name: "Listening for the hold key. Esc cancels." })).toBe(key);
    fireEvent.keyDown(window, { key: "Escape", code: "Escape" });
    expect(key).toHaveAttribute("aria-label", before);
    fireEvent.click(key);
    fireEvent.keyDown(window, { key: "F8", code: "F8" });
    expect(key).toHaveTextContent("F8");
    await waitFor(() => expect(hub.state.settings.hotkey.key).toBe("f8"));
  });

  it("renames a native calendar without exposing or changing its identifier, preserving every source", async () => {
    const original = clone(hub.state.settings.calendar);
    const native = { ...clone(original.sources[0] ?? {}), id: "native-work", label: "", url: "eventkit:6A0B9E7C-1884-4C46-9F90-9A7B1D24B191", enabled: true };
    const feed = { ...native, id: "team-feed", label: "Team", url: "https://work.example/calendar.ics", enabled: false };
    hub.state.settings.calendar = { ...original, sources: [native, feed] };
    hub.state.calendar = { ...clone(calendarOneWire), sources: [{ ...clone(calendarOneWire.sources[0]), id: native.id, label: "", type: "MACOS" }] };
    render(<SettingsCore scope="integrations" />);
    const row = await screen.findByTestId("calendar-source-native-work");
    expect(row.textContent).toContain("Mac calendar");
    expect(row.textContent).not.toContain("6A0B9E7C");
    expect(row.textContent).not.toContain("ICS");
    fireEvent.click(within(row).getByRole("button", { name: "Edit" }));
    const well = screen.getByTestId("calendar-well");
    expect(within(well).queryByRole("textbox", { name: "Calendar URL or file path" })).toBeNull();
    fireEvent.change(within(well).getByRole("textbox", { name: "Calendar name" }), { target: { value: "Work" } });
    fireEvent.click(within(well).getByRole("button", { name: "Save" }));
    await waitFor(() => expect(hub.state.settings.calendar.sources[0].label).toBe("Work"));
    const put = hub.state.calls.find((call) => call.method === "PUT" && call.path === "/api/settings")!;
    expect(Object.keys(put.body!).sort()).toEqual(["_revision", "calendar"]);
    expect(put.body!.calendar).toEqual({ sources: [{ ...native, label: "Work" }, feed] });
    expect(hub.state.settings.calendar.sources[0].url).toBe(native.url);
  });

  it("keeps a refused edit in place and Retry sends only its changed path", async () => {
    hub.state.settings.meeting.auto_export = false;
    const base = hub.fetchStub;
    let refuse = true;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      if (refuse && init?.method === "PUT" && new URL(String(input), "http://hub.test").pathname === "/api/settings") throw new TypeError("Settings connection lost");
      return base(input, init);
    }));
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
    expect(put.body).toEqual({ _revision: settingsWire._revision, meeting: { auto_export: true } });
    await waitFor(() => expect(screen.queryByTestId("settings-save-failure")).toBeNull());
    expect(within(footer).queryByRole("button", { name: "Retry" })).toBeNull();
  });

  it("an unrelated accepted edit keeps the earlier failure; a later edit of that field wins", async () => {
    hub.state.settings.meeting.auto_export = false;
    const base = hub.fetchStub;
    let refuse = true;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      if (refuse && init?.method === "PUT" && new URL(String(input), "http://hub.test").pathname === "/api/settings") throw new TypeError("Settings connection lost");
      return base(input, init);
    }));
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
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      if (refuse && init?.method === "PUT" && new URL(String(input), "http://hub.test").pathname === "/api/settings") throw new TypeError("Settings connection lost");
      return base(input, init);
    }));
    render(<SettingsCore scope="meetings" />);
    const timing = await screen.findByRole("combobox", { name: "Auto-run the summary" });
    fireEvent.change(timing, { target: { value: "room_linked" } });
    const failure = await screen.findByTestId("settings-save-failure", {}, { timeout: 3000 });
    refuse = false;
    fireEvent.change(timing, { target: { value: "off" } });
    fireEvent.click(within(failure).getByRole("button", { name: "Retry" }));
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
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      const path = new URL(String(input), "http://hub.test").pathname;
      if (refusePreference && init?.method === "PUT" && path === "/api/settings") throw new TypeError("Preference connection lost");
      if (init?.method === "PUT" && path === "/api/settings/secrets/web_token") { secretSaved = true; return new Response(JSON.stringify({ success: true }), { status: 200, headers: { "content-type": "application/json" } }); }
      if (init?.method === "PUT" && path === "/api/authority/control-mode") { modeSaved = true; return new Response(JSON.stringify({ ...authorityWire, control_mode: "neutral" }), { status: 200, headers: { "content-type": "application/json" } }); }
      return base(input, init);
    }));
    render(<SettingsWindow scope="meetings" />);
    fireEvent.click(await screen.findByRole("checkbox", { name: "Auto export" }));
    await screen.findByTestId("settings-save-failure", {}, { timeout: 3000 });
    fireEvent.click(screen.getByTestId("settings-index-accounts"));
    const credentials = screen.getByText("Credentials").closest("details")!;
    fireEvent.click(within(credentials).getByText("Credentials"));
    const secret = Array.from(credentials.querySelectorAll(".gadget-secret")).find((row) => row.textContent?.includes("Web pairing token")) as HTMLElement;
    fireEvent.click(within(secret).getByRole("button", { name: "Replace" }));
    const replacement = within(secret).getByLabelText("Replacement Web pairing token");
    fireEvent.change(replacement, { target: { value: "fixture-replacement" } });
    fireEvent.keyDown(replacement, { key: "Enter" });
    await waitFor(() => expect(secretSaved).toBe(true));
    await waitFor(() => expect(within(secret).getByRole("button", { name: "Replace" })).not.toBeDisabled());
    expect(screen.getByTestId("settings-save-failure").textContent).toContain("Preference connection lost");
    expect(document.querySelector(".kit-statusbar-items")?.textContent).toContain("Not saved");
    fireEvent.click(screen.getByTestId("settings-index-agents"));
    fireEvent.change(await screen.findByRole("combobox", { name: "Agents act" }), { target: { value: "neutral" } });
    await waitFor(() => expect(modeSaved).toBe(true));
    expect(screen.getByTestId("settings-save-failure").textContent).toContain("Preference connection lost");
    expect(document.querySelector(".kit-statusbar-items")?.textContent).toContain("Not saved");
    refusePreference = false;
    fireEvent.click(within(screen.getByTestId("settings-save-failure")).getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(hub.state.settings.meeting.auto_export).toBe(true));
  });

  it("offers primary Retry in the footer while a failed preference remains pending", async () => {
    const base = hub.fetchStub;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      if (init?.method === "PUT" && new URL(String(input), "http://hub.test").pathname === "/api/settings") throw new TypeError("Settings connection lost");
      return base(input, init);
    }));
    render(<SettingsCore scope="meetings" />);
    fireEvent.click(await screen.findByRole("checkbox", { name: "Auto export" }));
    await screen.findByTestId("settings-save-failure", {}, { timeout: 3000 });
    const footer = document.querySelector(".pref-status-bar") as HTMLElement;
    expect(within(footer).getByRole("button", { name: "Retry" }).className).toContain("btn--primary");
  });

  it("Auto-record always points to its Meetings Record home", async () => {
    hub.state.settings.meeting.auto_record = "off";
    hub.state.calendar = { ...clone(calendarOneWire), auto_record: "room_linked" };
    render(<SettingsCore scope="meetings" />);
    expect(await screen.findByTestId("settings-auto-record-link")).toHaveTextContent("Meetings › Record");
  });

  it("a failed runtime read offers a working Retry instead of a false identity", async () => {
    const base = hub.fetchStub;
    let refuse = true;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      if (refuse && new URL(String(input), "http://hub.test").pathname === "/api/system/identity") throw new TypeError("Device details unavailable");
      return base(input, init);
    }));
    render(<SettingsCore scope="system" />);
    const failure = await screen.findByTestId("runtime-unreadable");
    expect(screen.queryByTestId("runtime-backend")).toBeNull();
    refuse = false;
    fireEvent.click(within(failure).getByRole("button", { name: "Retry" }));
    await screen.findByTestId("runtime-backend");
    expect(screen.queryByTestId("runtime-unreadable")).toBeNull();
  });
});

describe("Settings › System › Remote access", () => {
  it("OFF: Other devices with the switch at OFF; no CREDENTIALS, no Issue credential; library verbs only", async () => {
    // replaces: tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_off_state
    const { container } = render(<SettingsCore scope="system" />);
    const toggle = (await screen.findByRole("combobox", { name: "Remote transport" })) as HTMLSelectElement;
    expect(toggle.value).toBe("OFF");
    const text = container.querySelector(".settings-page")?.textContent ?? "";
    expect(text).toContain("Other devices");
    expect(text).not.toContain("Streamable HTTP");
    expect(text).not.toContain("CREDENTIALS");
    expect(screen.queryByRole("button", { name: "Issue credential" })).toBeNull();
    expect(rawButtons(container.querySelector(".settings-page")!)).toEqual([]);
  });

  it("ON, issue: the token shows once with Copy; the row reads NEVER USED; Revoke removes that row only", async () => {
    // replaces: tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke (the face half; the hub half is tests/integration/test_desk_settings.py)
    const view = render(<SettingsCore scope="system" />);
    fireEvent.change(await screen.findByRole("combobox", { name: "Remote transport" }), { target: { value: "ON" } });
    await screen.findByRole("button", { name: "Issue credential" });
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Remote transport" })).toHaveValue("ON"));
    expect(screen.getByTestId("system-hub-chips").textContent).not.toContain("Other devices");

    fireEvent.click(screen.getByRole("button", { name: "Issue credential" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Credential name" }), { target: { value: "test-glass-runner" } });
    fireEvent.click(screen.getByTestId("issue-submit"));
    expect((await screen.findByTestId("token-value")).textContent).toBe("hs_agent_fixture_token_shown_once");
    expect(screen.getByTestId("token-copy")).toBeInTheDocument();
    expect(view.container.textContent).toContain("TOKEN SHOWN ONCE");

    // A second credential, then a fresh window: no token, NEVER USED.
    hub.state.remote.credentials.push({ ...clone(remoteOnWire.credentials[0]), id: "id-other", identity: "other-glass-runner", last_used_at: null });
    view.unmount();
    render(<SettingsCore scope="system" />);
    await screen.findByText("other-glass-runner");
    expect(screen.getByText("test-glass-runner")).toBeInTheDocument();
    expect(screen.queryByTestId("token-value")).toBeNull();
    expect(screen.getAllByText("NEVER USED").length).toBeGreaterThanOrEqual(1);

    const target = screen.getByText("test-glass-runner").closest(".surface-ledger-row") as HTMLElement;
    fireEvent.click(within(target).getByRole("button", { name: /Revoke/ }));
    await waitFor(() => expect(screen.queryByText("test-glass-runner")).toBeNull());
    expect(screen.getByText("other-glass-runner")).toBeInTheDocument();
    expect(hub.state.calls.some((c) => c.method === "DELETE" && c.path.endsWith("/id-test-glass-runner"))).toBe(true);
  });
});

describe("Settings › System › runtime identity", () => {
  it("the live hub's identity: every token in the RAW fold, no repair chip when nothing needs repair", async () => {
    // replaces: tests/e2e/test_hs200_runtime_identity_glass.py::test_runtime_identity_healthy (with
    // web/src/pages/cores/__tests__/runtimeIdentity.test.tsx and tests/unit/test_phase200_runtime_identity.py)
    // The page was built from the bundle the hub serves (Vite compiles this
    // constant in; vitest does not), as on the real desk.
    vi.stubGlobal("__HOLDSPEAK_BUILD__", (identityWire as Json).identity.frontend_build);
    render(<SettingsCore scope="system" />);
    const backend = await screen.findByTestId("runtime-backend");
    const fold = backend.closest("details.gadget-fold") as HTMLElement;
    expect(fold).not.toBeNull();
    expect(screen.getByTestId("runtime-schema").textContent).toMatch(/^SCHEMA /);
    expect(fold.contains(screen.getByTestId("runtime-path"))).toBe(true);
    expect((identityWire as Json).repair).toEqual([]);
    expect(screen.queryByTestId("runtime-repair")).toBeNull();
  });
});

describe("Settings › Rhythm is Rhythm's one home (Betterment setup ST1)", () => {
  it("Notify and quiet hours read and write the heartbeat; no cadence.quiet_hours row; Saved in the foot", async () => {
    // The hub half: tests/integration/test_desk_settings.py::test_quiet_hours_set_in_settings_are_what_the_heartbeat_and_cadence_read
    expect(heartbeatWire.quiet_hours).toEqual({ start: 22, end: 8 });
    render(<SettingsCore scope="rhythm" />);
    const from = await screen.findByRole("spinbutton", { name: "Quiet from" }) as HTMLInputElement;
    await waitFor(() => expect(from.value).toBe("22"));
    expect((screen.getByRole("spinbutton", { name: "Quiet until" }) as HTMLInputElement).value).toBe("8");
    expect((screen.getByRole("combobox", { name: "Notify" }) as HTMLSelectElement).value).toBe(heartbeatWire.notify);
    fireEvent.click(screen.getByRole("button", { name: "Decrease Quiet from" }));
    await waitFor(() => expect(hub.state.heartbeat.quiet_hours).toEqual({ start: 21, end: 8 }));
    const puts = hub.state.calls.filter((c) => c.method === "PUT");
    expect(puts.map((c) => [c.path, c.body])).toEqual([["/api/settings/heartbeat", { quiet_hours: { start: 21 } }]]);
    fireEvent.change(screen.getByRole("combobox", { name: "Notify" }), { target: { value: "off" } });
    await waitFor(() => expect(hub.state.heartbeat.notify).toBe("off"));
    // Nothing writes the retired cadence.quiet_hours_* keys.
    expect(hub.state.calls.some((c) => c.path === "/api/settings" && c.method === "PUT")).toBe(false);
    await waitFor(() => expect(document.querySelector(".pref-status-bar")?.textContent ?? "").toMatch(/Saved/));
    expect(rawButtons(document.querySelector(".settings-page")!)).toEqual([]);
  });

  it("the sweep and the loops are behind Advanced, read only when he opens them", async () => {
    render(<SettingsCore scope="rhythm" />);
    await screen.findByRole("spinbutton", { name: "Quiet from" });
    expect(hub.state.calls.some((c) => c.path.startsWith("/api/cadence/"))).toBe(false);
    const fold = screen.getByText("Sweep and loops").closest("details") as HTMLDetailsElement;
    fold.open = true;
    fireEvent(fold, new Event("toggle"));
    await screen.findByTestId("rhythm-sweep-row");
    expect(screen.getByTestId("rhythm-run-now").textContent).toBe("Run now");
    // The section says Notify once; the embedded face has no headline or foot of its own.
    expect(screen.queryByTestId("rhythm-notify-row")).toBeNull();
    expect(screen.queryByTestId("rhythm-headline")).toBeNull();
    expect(document.querySelectorAll(".kit-statusbar:not(.pref-status-bar), .surface-footer-layout")).toHaveLength(0);
  });
});

describe("Settings › Meetings when the owner turned summaries off", () => {
  it("SUMMARIES OFF, with no NO MODEL and no Choose model", async () => {
    // replaces: tests/e2e/test_philo15_18_rest_of_day_glass.py::TestSummariesOffInSettingsMeetings::test_settings_meetings_says_summaries_off
    // (the hub half: tests/unit/test_philo15_18_engine_words.py::test_settings_hub_says_summaries_off_not_no_engine)
    Object.assign(hub.state.hub.meetings, { summariesOff: true, engineSet: false });
    render(<SettingsCore scope="meetings" />);
    const off = await screen.findByTestId("settings-summaries-off");
    expect(off.textContent).toContain("Summaries off");
    expect(screen.queryByTestId("settings-no-model")).toBeNull();
    expect(screen.queryByTestId("settings-choose-model")).toBeNull();
  });
});

describe("Settings › Sounds without the speech extra", () => {
  it("browser voice names observed support and server installation opens in Details", async () => {
    // replaces: tests/e2e/test_hs154_call_glass.py::test_tts_settings_glass
    // The answer is the hub's own: GET /api/tts/status without the extra
    // (holdspeak/web/routes/tts.py; tests/unit/test_tts_route.py::TestTtsNotInstalled).
    const base = hub.fetchStub;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) =>
      new URL(String(input), "http://hub.test").pathname === "/api/tts/status"
        ? new Response(JSON.stringify({ installed: false, model_ready: false }), { status: 200, headers: { "content-type": "application/json" } })
        : base(input, init)));
    render(<SettingsCore scope="sounds" />);
    const label = await screen.findByText("Browser voice");
    const group = label.closest(".gadget-group") as HTMLElement;
    expect(group.textContent).toContain("Not available");
    expect(within(group).getByText("Not installed")).toBeInTheDocument();
    expect(within(group).queryByRole("checkbox")).toBeNull();
    const details = within(group).getByText("Details").closest("details")!;
    expect(details).not.toHaveAttribute("open");
    expect(within(details).getByRole("button", { name: "Copy", hidden: true })).not.toBeVisible();
    expect(within(details).getByText("pip install 'holdspeak[tts]'")).not.toBeVisible();
    fireEvent.click(within(group).getByText("Details"));
    expect(details).toHaveAttribute("open");
    expect(within(details).getByText("pip install 'holdspeak[tts]'")).toBeInTheDocument();
    expect(within(details).getByRole("button", { name: "Copy" })).toBeVisible();
    expect(within(group).queryByRole("checkbox")).toBeNull();
  });
});

describe("Settings › System › Remote access grants", () => {
  const W = { allow: "Allow filing", stop: "Stop filing", live: "FILING ALLOWED", stopped: "FILING STOPPED" };
  const P = { allow: "Allow run and publish", stop: "Stop run and publish", live: "RUN AND PUBLISH ALLOWED", stopped: "RUN AND PUBLISH STOPPED" };
  const wires = import.meta.glob("./fixtures/settings-wire/grant-*.json", { eager: true, import: "default" }) as Record<string, Json>;
  const grant = (name: string) => clone(wires[`./fixtures/settings-wire/grant-${name}.json`]);

  /** The grant routes on top of the Settings hub double: each answer is a recorded one. */
  function grantRoutes(routes: Record<string, () => { status: number; body: unknown; remote?: Json }>) {
    const base = hub.fetchStub;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      const method = (init?.method ?? "GET").toUpperCase();
      const path = new URL(String(input), "http://hub.test").pathname;
      const route = Object.keys(routes).find((k) => k === `${method} ${path}` || (k.endsWith("*") && `${method} ${path}`.startsWith(k.slice(0, -1))));
      if (!route) return base(input, init);
      hub.state.calls.push({ method, path });
      const { status, body, remote } = routes[route]();
      if (remote) hub.state.remote = remote;
      return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
    }));
  }
  const row = (identity: string) => ledgerRow(identity) as HTMLElement;
  const foot = () => screen.getByTestId("foot-receipt");

  it("Allow, Stop, and a refused Stop on the rendered row; the receipt names it and outlives the act", async () => {
    // replaces: tests/e2e/test_philo7_02_grant_glass.py::TestGrantGlass::test_allow_stop_and_a_refused_stop_on_the_rendered_row
    hub.state.remote = grant("remote-never");
    let refuse = false;
    grantRoutes({
      "PUT /api/settings/remote/delegations/desk-agent": () => ({ status: 200, body: grant("allow"), remote: grant("remote-live") }),
      "DELETE /api/settings/remote/delegations/desk-agent": () => refuse
        ? { status: 409, body: grant("stop-refused"), remote: grant("remote-stopped") }
        : { status: 200, body: grant("stop"), remote: grant("remote-stopped") },
    });
    render(<SettingsCore scope="system" />);
    await screen.findByText("desk-agent");
    expect(within(row("desk-agent")).queryByTestId("grant-chip")).toBeNull();
    expect(within(row("desk-agent")).getByTestId("grant-verb").textContent).toBe(W.allow);
    expect(within(row("desk-agent")).getByTestId("credential-revoke").textContent).toBe("Revoke credential");
    expect(document.querySelector(".surface-ledger-count")?.textContent).toContain("AGENTS");

    fireEvent.click(within(row("desk-agent")).getByTestId("grant-verb"));
    await waitFor(() => expect(within(row("desk-agent")).getByTestId("grant-chip").textContent).toContain(W.live));
    expect(within(row("desk-agent")).getByTestId("grant-chip")).toHaveAttribute("data-state", "success");
    expect(within(row("desk-agent")).getByTestId("grant-verb").textContent).toBe(W.stop);
    await waitFor(() => expect(foot().textContent).toContain("ALLOWED"));
    expect(foot()).toHaveAttribute("data-operation-id", grant("allow").operation_id);

    fireEvent.click(within(row("desk-agent")).getByTestId("grant-verb"));
    await waitFor(() => expect(within(row("desk-agent")).getByTestId("grant-chip").textContent).toContain(W.stopped));
    expect(within(row("desk-agent")).getByTestId("grant-chip")).toHaveAttribute("data-state", "idle");
    expect(within(row("desk-agent")).getByTestId("grant-verb").textContent).toBe(W.allow);
    await waitFor(() => expect(foot().textContent).toContain("STOPPED"));

    // Another owner request revoked the grant first; the face still says LIVE.
    hub.state.remote = grant("remote-live");
    refuse = true;
    cleanup();
    render(<SettingsCore scope="system" />);
    await waitFor(() => expect(within(row("desk-agent")).getByTestId("grant-verb").textContent).toBe(W.stop));
    fireEvent.click(within(row("desk-agent")).getByTestId("grant-verb"));
    const refused = await within(row("desk-agent")).findByTestId("grant-refused");
    expect(refused).toHaveAttribute("data-code", "desk_delegation_required");
    expect(refused.textContent).toContain("CANNOT STOP");
    expect(refused.textContent).toContain("NO GRANT");
    // After the reread the chip agrees with the hub: STOPPED.
    await waitFor(() => expect(within(row("desk-agent")).getByTestId("grant-chip").textContent).toContain(W.stopped));
    await waitFor(() => expect(foot().textContent).toContain("REFUSED"));
    fireEvent.click(foot());
    const well = await screen.findByTestId("grant-receipt");
    for (const word of ["REFUSED", "STOP FILING", "NO GRANT", "desk-agent", "BY OWNER"]) expect(well.textContent).toContain(word);
    expect(well.getAttribute("data-operation-id")).toBe(foot().getAttribute("data-operation-id"));
    expect(well.getAttribute("data-operation-id")).toBe(grant("stop-refused").operation_id);
    expect(document.querySelector("[role=dialog], .modal")).toBeNull();
  });

  it("Revoke credential ends the grant first; the row leaves and its receipt stays", async () => {
    // replaces: tests/e2e/test_philo7_02_grant_glass.py::TestGrantGlass::test_revoke_credential_ends_the_grant_first_and_the_receipt_survives_the_row
    hub.state.remote = grant("remote-live");
    const after = { ...grant("remote-live"), credentials: [], active_count: 0, total_count: 0 };
    grantRoutes({
      "DELETE /api/settings/remote/credentials/*": () => ({ status: 200, body: grant("revoke-credential"), remote: after }),
    });
    render(<SettingsCore scope="system" />);
    await waitFor(() => expect(within(row("desk-agent")).getByTestId("grant-chip").textContent).toContain(W.live));
    fireEvent.click(within(row("desk-agent")).getByTestId("credential-revoke"));
    await waitFor(() => expect(screen.queryByText("desk-agent")).toBeNull());
    expect(document.querySelector('[data-settings-section="this-mac"] .surface-ledger')).toBeNull();
    await waitFor(() => expect(foot().textContent).toContain("STOPPED"));
    fireEvent.click(foot());
    const well = await screen.findByTestId("grant-receipt");
    for (const word of ["SUCCEEDED", W.stopped, "desk-agent", "BY OWNER"]) expect(well.textContent).toContain(word);
  });

  it("a LIVE grant with no credential shows with remote OFF, NO CREDENTIAL, and stops", async () => {
    // replaces: tests/e2e/test_philo7_02_grant_glass.py::TestGrantGlass::test_a_grant_with_no_credential_shows_with_remote_off_and_stops
    // and test_philo9_07_project_grant_glass.py::TestProjectGrantGlass::test_live_grants_with_no_credential_show_on_and_off_and_the_last_stop_keeps_its_receipt (the desk orphan)
    hub.state.remote = grant("remote-orphan-off");
    grantRoutes({
      "DELETE /api/settings/remote/delegations/orphan-agent": () => ({
        status: 200, body: grant("stop"), remote: { ...grant("remote-orphan-off"), delegations: [] },
      }),
    });
    render(<SettingsCore scope="system" />);
    await screen.findByText("orphan-agent");
    const orphan = document.querySelector('[data-testid^="delegation-row-"]') as HTMLElement;
    expect(orphan.textContent).toContain("orphan-agent");
    expect(orphan.textContent).toContain("NO CREDENTIAL");
    expect(within(orphan).getByTestId("grant-chip").textContent).toContain(W.live);
    expect(within(orphan).getByTestId("grant-verb").textContent).toBe(W.stop);
    // Remote OFF hides a credential row with no LIVE grant, and offers no Issue credential.
    expect(screen.queryByText("desk-agent")).toBeNull();
    expect(screen.queryByTestId("issue-credential-btn")).toBeNull();
    fireEvent.click(within(orphan).getByTestId("grant-verb"));
    await waitFor(() => expect(screen.queryByText("orphan-agent")).toBeNull());
    expect(document.querySelector('[data-settings-section="this-mac"] .surface-ledger')).toBeNull();
    await waitFor(() => expect(foot().textContent).toContain("STOPPED"));
  });

  it("a stored LIVE grant past its expiry reads FILING STOPPED, with Allow", async () => {
    // replaces: tests/e2e/test_philo7_02_grant_glass.py::TestGrantGlassRoundTwo::test_an_expired_grant_reads_stopped_on_both_rows (the credential row)
    hub.state.remote = grant("remote-expired");
    expect(hub.state.remote.credentials[0].delegation.state).toBe("EXPIRED");
    render(<SettingsCore scope="system" />);
    await waitFor(() => expect(within(row("desk-agent")).getByTestId("grant-chip").textContent).toContain(W.stopped));
    expect(within(row("desk-agent")).getByTestId("grant-verb").textContent).toBe(W.allow);
  });

  it("remote OFF keeps the credential whose grant is LIVE, with Stop and Revoke; a credential with no grant is hidden", async () => {
    // replaces: tests/e2e/test_philo7_02_grant_glass.py::TestGrantGlassRoundTwo::test_remote_off_keeps_a_credential_with_a_live_grant
    hub.state.remote = grant("remote-off-live");
    expect(hub.state.remote.enabled).toBe(false);
    render(<SettingsCore scope="system" />);
    await waitFor(() => expect(within(row("desk-agent")).getByTestId("grant-chip").textContent).toContain(W.live));
    expect(within(row("desk-agent")).getByTestId("grant-verb").textContent).toBe(W.stop);
    expect(within(row("desk-agent")).getByTestId("credential-revoke").textContent).toBe("Revoke credential");
    expect(screen.queryByText("sweep-runner")).toBeNull();
    expect(screen.queryByTestId("issue-credential-btn")).toBeNull();
  });

  it("project grants: a PROJECT credential has Projects and no desk grant; Allow on one project, the other stays Allow", async () => {
    // replaces: tests/e2e/test_philo9_07_project_grant_glass.py::TestProjectGrantGlass::test_allow_stop_refused_and_two_projects_on_the_rendered_row
    const live = grant("remote-project-live");
    const never = clone(live);
    never.credentials[1].project_delegations = [];
    hub.state.remote = never;
    const [pay, hire] = grant("projects").projects;
    grantRoutes({
      "GET /api/projects": () => ({ status: 200, body: grant("projects") }),
      [`PUT /api/settings/remote/delegations/sweep-runner/projects/${pay.id}`]: () => ({ status: 200, body: grant("project-allow"), remote: live }),
    });
    render(<SettingsCore scope="system" />);
    await screen.findByText("sweep-runner");
    const runner = row("sweep-runner");
    expect(within(runner).queryByTestId("grant-verb")).toBeNull();
    expect(within(runner).getByTestId("palette-token").textContent).toBe("PROJECT");
    expect(within(row("desk-agent")).getByTestId("palette-token").textContent).toBe("DESK");
    expect(within(row("desk-agent")).getByTestId("grant-verb").textContent).toBe(W.allow);
    fireEvent.click(within(runner).getByRole("button", { name: /Projects/ }));
    const line = async (id: string) => await screen.findByTestId(`project-line-${id}`);
    expect(within(await line(pay.id)).queryByTestId("project-grant-chip")).toBeNull();
    expect(within(await line(pay.id)).getByTestId("project-grant-verb").textContent).toBe(P.allow);
    fireEvent.click(within(await line(pay.id)).getByTestId("project-grant-verb"));
    await waitFor(async () => expect(within(await line(pay.id)).getByTestId("project-grant-chip").textContent).toContain(P.live));
    expect(within(await line(pay.id)).getByTestId("project-grant-chip")).toHaveAttribute("data-state", "success");
    expect(within(await line(pay.id)).getByTestId("project-grant-verb").textContent).toBe(P.stop);
    expect(within(await line(hire.id)).queryByTestId("project-grant-chip")).toBeNull();
    expect(within(await line(hire.id)).getByTestId("project-grant-verb").textContent).toBe(P.allow);
    await waitFor(() => expect(foot().textContent).toContain("ALLOWED"));
    const summary = within(row("sweep-runner")).getByTestId("project-grant-summary");
    expect(summary.textContent).toContain(P.live);
    expect(summary.textContent).toContain("PAYMENTS LEDGER CUTOVER");
  });

  it("a refused project Stop is named CANNOT STOP · NO GRANT and the line reads STOPPED after the reread", async () => {
    // replaces: tests/e2e/test_philo9_07_project_grant_glass.py::TestProjectGrantGlass::test_allow_stop_refused_and_two_projects_on_the_rendered_row (the refused Stop)
    const live = grant("remote-project-live");
    const stopped = clone(live);
    stopped.credentials[1].project_delegations[0].state = "REVOKED";
    hub.state.remote = live;
    const [pay] = grant("projects").projects;
    grantRoutes({
      "GET /api/projects": () => ({ status: 200, body: grant("projects") }),
      [`DELETE /api/settings/remote/delegations/sweep-runner/projects/${pay.id}`]: () => ({ status: 409, body: grant("project-stop-refused"), remote: stopped }),
    });
    render(<SettingsCore scope="system" />);
    await screen.findByText("sweep-runner");
    fireEvent.click(within(row("sweep-runner")).getByRole("button", { name: /Projects/ }));
    const line = await screen.findByTestId(`project-line-${pay.id}`);
    fireEvent.click(within(line).getByTestId("project-grant-verb"));
    const refused = await within(line).findByTestId("grant-refused");
    expect(refused).toHaveAttribute("data-code", "project_delegation_required");
    expect(refused.textContent).toContain("CANNOT STOP");
    expect(refused.textContent).toContain("NO GRANT");
    await waitFor(() => expect(within(screen.getByTestId(`project-line-${pay.id}`)).getByTestId("project-grant-chip").textContent).toContain(P.stopped));
    await waitFor(() => expect(foot().textContent).toContain("REFUSED"));
  });
});


describe("Settings category face", () => {
it("opens You, shows one category at a time, and navigates as the owner does", async () => {
    const state = hub.state;
    const { container } = render(<SettingsCore />);
    await screen.findByTestId("settings-page");
    const sections = Array.from(container.querySelectorAll("[data-settings-section]"))
      .map((section) => section.getAttribute("data-settings-section"));
    expect(sections).toEqual(["you", "speak", "meetings", "notices", "accounts", "calls", "agents", "desk", "this-mac"]);
    expect(screen.getByRole("navigation", { name: "Settings sections" })).toBeInTheDocument();
    expect(screen.getByTestId("settings-index-you")).toHaveClass("is-active");
    expect(container.querySelector('[data-settings-section="you"]')).not.toHaveAttribute("hidden");
    expect(container.querySelector('[data-settings-section="speak"]')).toHaveAttribute("hidden");
    expect(screen.queryByRole("combobox", { name: "Language" })).toBeNull();

    fireEvent.click(screen.getByTestId("settings-index-notices"));
    expect(screen.getByText("Quiet from")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("settings-index-this-mac"));
    expect(screen.getByTestId("settings-engines-page-link")).toBeInTheDocument();
    expect(screen.getByTestId("settings-setup-page-link")).toBeInTheDocument();
    expect(container.querySelector('[data-settings-section="notices"]')).toHaveAttribute("hidden");
    expect(screen.getByTestId("settings-index-this-mac")).toHaveClass("is-active");
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
    expect(screen.getByTestId("settings-index-notices")).toHaveClass("is-active");
    expect(container.querySelector('[data-settings-section="notices"] .gadget-row[data-highlight]')).toBeTruthy();
  });
});

/** The phone frame's one Back, as SurfaceWindows wires it: a core that holds
 *  the Back gets the press; otherwise the Back closes the window. */
function PhoneSettingsWindow({ scope, onClose }: { scope?: string; onClose: () => void }) {
  const [back, setBack] = useState<WindowBack | null>(null);
  return (
    <BackSlotContext.Provider value={setBack}>
      <button className="btn" data-testid={back?.testId ?? "frame-back"} onClick={back?.onBack ?? onClose}>Back</button>
      <SettingsCore scope={scope} />
    </BackSlotContext.Provider>
  );
}

describe("Settings at phone width: Back returns where the owner came from", () => {
  const realMatchMedia = window.matchMedia;
  beforeEach(() => {
    window.matchMedia = ((query: string) => ({
      matches: query === "(max-width: 720px)", media: query, onchange: null,
      addEventListener: () => {}, removeEventListener: () => {},
      addListener: () => {}, removeListener: () => {}, dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
  });
  afterEach(() => { window.matchMedia = realMatchMedia; });

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

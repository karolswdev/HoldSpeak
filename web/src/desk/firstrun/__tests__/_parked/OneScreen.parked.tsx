/* First run, option A "One screen" (owner ratified 2026-10-05) — the
 * Calendar and Connections cards and Ready, with the hub faked in the
 * shape of PR #868's onboarding routes.
 *
 * Calendar: found / none / added (a link) / failed (CAN'T READ) / denied
 * (CALENDAR · NOT ALLOWED) / the prompt only on his press.
 * Connections: found / Use it -> CONNECTED (the hub's fact) / refused /
 * none / a row with no verb.
 * Ready: "Ready, <name>", the strip, the three verbs; Record withheld with
 * no meeting. */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { LocalAiStatus } from "../localAi";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  refresh: vi.fn(),
  arm: vi.fn(),
  openAsk: vi.fn(),
  open: vi.fn(),
  start: vi.fn(),
  retry: vi.fn(),
  setup: null as null | { first_run: boolean },
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ApiError: (await importOriginal<typeof import("../../../lib/api")>()).ApiError,
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));
vi.mock("../../store", () => ({
  useDesk: Object.assign(() => undefined, {
    getState: () => ({ refresh: mocks.refresh, armEventRecording: mocks.arm, openAsk: mocks.openAsk, setup: mocks.setup }),
  }),
}));
vi.mock("../../shell", () => ({ openSurfaceOr: mocks.open }));
vi.mock("../../../lib/speakToFill", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/speakToFill")>()),
  retryPendingTranscription: mocks.retry,
}));
vi.mock("../../../lib/micSession", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/micSession")>()),
  closeMicSession: vi.fn(),
}));
vi.mock("../../../lib/micStreamSession", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/micStreamSession")>()),
  micStreamSupported: () => true,
  startStreamSession: mocks.start,
  subscribeCaptureLevel: () => () => undefined,
}));

import { ApiError } from "../../../lib/api";
import { FirstRun } from "../FirstRun";

// These behavior tests enter the optional setup and chat wells explicitly.
function renderExpandedFirstRun() {
 const view = render(<FirstRun />);
 view.container.querySelectorAll<HTMLDetailsElement>(".firstrun-chat, .firstrun-optional").forEach((fold) => { fold.open = true; });
 return view;
}

import { calendarReceipt } from "../CalendarCard";
import { cantReadReason, hostOf, meetingClock, nextMeeting } from "../calendarStep";
import { readyItems } from "../Ready";
import { readDurableDraft, clearDurableDraft } from "../../../lib/durableDraft";
import { clearFirstValueKeepNoteId } from "../../firstValue";
import { openFirstRun, useFirstRunOpen } from "../reopen";
import { inventedFields, recorded } from "../../../test/wireShape";
import LOCAL_AI_WIRE from "../../../test/wire/setup-local-ai.wire.json";
import SETTINGS_WIRE from "../../../test/wire/settings.owner.wire.json";
import NOTE_WIRE from "../../../test/wire/notes-create.wire.json";
import CALENDAR_WIRE from "../../../test/wire/onboarding-calendar.wire.json";
import CONNECTIONS_WIRE from "../../../test/wire/onboarding-connections.wire.json";
import DOOR_WIRE from "../../../test/wire/door.fresh.wire.json";
import SOURCES_WIRE from "../../../test/wire/calendar-sources.wire.json";
import SETTINGS_PUT_WIRE from "../../../test/wire/settings.put.wire.json";
import CHECK_OK_WIRE from "../../../test/wire/onboarding-calendar.check.wire.json";
import CHECK_FAILED_WIRE from "../../../test/wire/onboarding-calendar.check-failed.wire.json";
import WEEK_DOOR_WIRE from "../../__tests__/wire/door.week-strip.wire.json";
import ACCESS_WIRE from "../../../test/wire/onboarding-calendar.access.wire.json";
import USE_CALENDAR_WIRE from "../../../test/wire/onboarding-calendar.use.wire.json";
import USE_CONNECTION_WIRE from "../../../test/wire/onboarding-connections.use.wire.json";

const MB = 1_000_000;
const WORDS = "Send the cutover plan to Priya before Friday.";

/** The hub's own GET /api/setup/local-ai (the recorder pins an Apple-silicon
 *  Mac with mlx-whisper), every file on the device or none. */
function aiStatus(ready: boolean): LocalAiStatus {
  const hub = recorded<LocalAiStatus & Record<string, any>>(LOCAL_AI_WIRE);
  return {
    ...hub,
    state: ready ? "ready" : "not_started",
    files: hub.files.map((f) => ({ ...f, on_device: ready })),
    speech: { ...hub.speech, state: ready ? "on_device" : "will_download", ready } as LocalAiStatus["speech"],
    local_engine: { ...hub.local_engine, ready },
  };
}

/** The hub's own candidate rows (tests/integration/test_face_wire_fences.py:
 *  EventKit granted with one calendar, gh and acli signed in). */
const RECORDED_CANDIDATES = recorded<{ candidates: Record<string, any>[] }>(CONNECTIONS_WIRE).candidates;
const MAC_CAL = recorded<{ candidates: Record<string, any>[] }>(CALENDAR_WIRE).candidates[0];

function gh(over: Record<string, unknown> = {}) {
  return { ...RECORDED_CANDIDATES.find((c) => c.provider === "github"), ...over };
}
function jira(over: Record<string, unknown> = {}) {
  return { ...RECORDED_CANDIDATES.find((c) => c.provider === "jira"), ...over };
}

/** The recorded `tools` block with `installed` set per tool. */
function toolsBlock(installed: { gh?: boolean; acli?: boolean }) {
  const hub = recorded<{ tools: Record<string, any> }>(CONNECTIONS_WIRE).tools;
  return {
    gh: { ...hub.gh, installed: installed.gh ?? false },
    acli: { ...hub.acli, installed: installed.acli ?? false },
  };
}

interface Hub {
  ai: LocalAiStatus;
  owner: { name: string; aliases: string[] };
  calendar: { macos: { state: string; can_request: boolean }; candidates: Record<string, unknown>[]; sources: number };
  access: () => Hub["calendar"];
  check: (url: string) => unknown;
  useCalendar: (id: string) => unknown;
  connections: { candidates: Record<string, unknown>[]; tools: Record<string, { installed: boolean } & Record<string, unknown>> };
  useConnection: (id: string) => unknown;
  door: { upcoming: unknown[]; week?: { total: number } };
  /** calendar.sources in config, as GET /api/settings carries them. */
  sources: { id: string; url: string; enabled: boolean }[];
  /** Per-source read state (GET /api/calendar/sources); default success. */
  status: Record<string, string>;
}

/** One configured source (enabled unless said). */
function source(url: string, enabled = true, id = `src_${url}`) {
  return { id, url, enabled };
}

let hub: Hub;
const calls: { path: string; method: string; json?: unknown }[] = [];
const soon = () => new Date(Date.now() + 2 * 3600_000).toISOString();

beforeEach(() => {
  calls.length = 0;
  mocks.setup = null;
  clearDurableDraft("desk-ask");
  clearFirstValueKeepNoteId();
  hub = {
    ai: aiStatus(false),
    owner: { name: "", aliases: [] },
    calendar: { ...recorded<Hub["calendar"]>(CALENDAR_WIRE), macos: { state: "unavailable", can_request: false }, candidates: [], sources: 0 },
    // The hub's access answer is the detect answer plus what was asked.
    access: () => ({ ...hub.calendar, macos: { ...hub.calendar.macos, requested: hub.calendar.macos.state } }),
    check: () => ({ ...recorded<Record<string, unknown>>(CHECK_FAILED_WIRE), error_class: "calendar_source_http_error", redirect_target: null }),
    useCalendar: (id) => {
      const added = source(id);
      hub.sources = [...hub.sources, added];
      const hubSource = recorded<{ source: Record<string, unknown> }>(USE_CALENDAR_WIRE).source;
      return { ...recorded<Record<string, unknown>>(USE_CALENDAR_WIRE), source: { ...hubSource, id: added.id, url: id } };
    },
    connections: { candidates: [], tools: toolsBlock({}) },
    useConnection: (id) => {
      hub.connections = {
        ...hub.connections,
        candidates: hub.connections.candidates.map((c) => (c.id === id ? { ...c, connected: true } : c)),
      };
      return { ...recorded<Record<string, unknown>>(USE_CONNECTION_WIRE), candidate: id };
    },
    door: { upcoming: [] },
    sources: [],
    status: {},
  };
  mocks.refresh.mockReset().mockResolvedValue(undefined);
  mocks.arm.mockReset().mockResolvedValue(true);
  mocks.openAsk.mockReset();
  mocks.retry.mockReset().mockResolvedValue(null);
  mocks.open.mockReset();
  mocks.start.mockReset().mockResolvedValue({
    stop: vi.fn().mockResolvedValue(WORDS),
    cancel: vi.fn(),
    retained: vi.fn().mockResolvedValue(false),
    audio: () => null,
  });
  mocks.apiFetch.mockReset().mockImplementation(async (path: string, init: { method?: string; json?: unknown } = {}) => {
    const method = init.method ?? "GET";
    calls.push({ path, method, json: init.json });
    const body = (init.json ?? {}) as Record<string, string>;
    switch (path) {
      case "/api/setup/local-ai":
        return hub.ai;
      case "/api/settings":
        return method === "GET" ? { owner: hub.owner, calendar: { sources: hub.sources } } : { settings: {} };
      case "/api/notes":
        return { note: { id: "note_1" } };
      case "/api/onboarding/calendar":
        return hub.calendar;
      case "/api/onboarding/calendar/macos/access":
        return hub.access();
      case "/api/onboarding/calendar/check":
        return hub.check(body.url);
      case "/api/onboarding/calendar/use":
        return hub.useCalendar(body.id);
      case "/api/onboarding/connections":
        return hub.connections;
      case "/api/onboarding/connections/use":
        return hub.useConnection(body.id);
      case "/api/door":
        // The Door's own fact: an ENABLED source (door_service `_calendar_configured`).
        return { ...hub.door, calendar_configured: hub.sources.some((s) => s.enabled) };
      case "/api/calendar/sources":
        return {
          sources: hub.sources.filter((s) => s.enabled).map((s) => ({ id: s.id, status: hub.status[s.id] ?? "success" })),
        };
      default:
        return {};
    }
  });
});

const card = (id: string) => screen.getByTestId(id);

describe("the typed hub bodies carry only the hub's fields (the SCAR LAW)", () => {
  // The hub's own answers: tests/integration/test_face_wire_fences.py::test_first_run_reads.
  // The candidate rows (a Mac calendar, a signed-in GitHub or Jira account)
  // need an account on the machine, so they are not recorded here.
  it("local AI, settings, a kept note, the calendar, the connections, the Door and the sources", async () => {
    const hubLocal = recorded<{ files: unknown[] }>(LOCAL_AI_WIRE);
    for (const ready of [false, true]) {
      const { files, ...rest } = aiStatus(ready);
      expect(inventedFields(rest, hubLocal)).toEqual([]);
      for (const file of files) expect(inventedFields(file, hubLocal.files[0])).toEqual([]);
    }
    hub.sources = [source("https://cal.example.com/a.ics")];
    const get = (path: string, init?: unknown) => mocks.apiFetch(path, init);
    expect(inventedFields(await get("/api/settings"), recorded(SETTINGS_WIRE))).toEqual([]);
    expect(inventedFields(await get("/api/notes", { method: "POST" }), recorded(NOTE_WIRE))).toEqual([]);
    expect(inventedFields(await get("/api/onboarding/calendar"), recorded(CALENDAR_WIRE))).toEqual([]);
    expect(inventedFields(await get("/api/onboarding/connections"), recorded(CONNECTIONS_WIRE))).toEqual([]);
    expect(inventedFields(await get("/api/door"), recorded(DOOR_WIRE))).toEqual([]);
    expect(inventedFields(await get("/api/calendar/sources"), recorded(SOURCES_WIRE))).toEqual([]);
    expect(inventedFields(await get("/api/settings", { method: "PUT" }), recorded(SETTINGS_PUT_WIRE))).toEqual([]);
    expect(inventedFields(await get("/api/onboarding/calendar/check", { method: "POST", json: { url: "x" } }), recorded(CHECK_FAILED_WIRE))).toEqual([]);
    // The typed upcoming rows these tests set, against the Door's recorded calendar rows.
    hub.door = { upcoming: [{ id: "e1", source: "calendar_event", title: "Atlas weekly", starts_at: soon() }], week: { total: 14 } };
    expect(inventedFields(await get("/api/door"), recorded(WEEK_DOOR_WIRE))).toEqual([]);
    hub.connections = { candidates: [gh(), jira()], tools: toolsBlock({ gh: true, acli: true }) };
    expect(inventedFields(await get("/api/onboarding/connections"), recorded(CONNECTIONS_WIRE))).toEqual([]);
    hub.calendar = { macos: { state: "full_access", can_request: false }, candidates: [MAC_CAL], sources: 0 };
    expect(inventedFields(await get("/api/onboarding/calendar"), recorded(CALENDAR_WIRE))).toEqual([]);
    expect(inventedFields(await get("/api/onboarding/calendar/macos/access", { method: "POST" }), recorded(ACCESS_WIRE))).toEqual([]);
    expect(inventedFields(await get("/api/onboarding/calendar/use", { method: "POST", json: { id: "eventkit:CAL-1" } }), recorded(USE_CALENDAR_WIRE))).toEqual([]);
    expect(inventedFields(await get("/api/onboarding/connections/use", { method: "POST", json: { id: "github:github.com:karolswdev" } }), recorded(USE_CONNECTION_WIRE))).toEqual([]);
  });
});

describe("calendar helpers", () => {
  it("reads a typed link's host; webcal reads as https; http is no host", () => {
    expect(hostOf("webcal://p01-caldav.icloud.com/x.ics")).toBe("p01-caldav.icloud.com");
    expect(hostOf("https://outlook.office365.com/owa/calendar/a/calendar.ics")).toBe("outlook.office365.com");
    expect(hostOf("http://example.com/a.ics")).toBe("");
    expect(hostOf("not a link")).toBe("");
  });

  it("names a link it cannot read as one plain token", () => {
    expect(cantReadReason("calendar_source_redirect", "https://new.example.com/a.ics")).toBe("MOVED TO NEW.EXAMPLE.COM");
    expect(cantReadReason("calendar_source_timeout")).toBe("TIMED OUT");
    expect(cantReadReason("calendar_url_invalid")).toBe("NOT A CALENDAR LINK");
    expect(cantReadReason("calendar_feed_unparseable")).toBe("NOT A CALENDAR");
  });

  it("builds the receipt from the week and the next meeting, no zero count", () => {
    const at = new Date();
    at.setHours(23, 59, 0, 0);
    expect(calendarReceipt(14, { title: "Atlas weekly", starts_at: at.toISOString() })).toBe(
      "14 EVENTS · NEXT ATLAS WEEKLY 23:59",
    );
    expect(calendarReceipt(0, null)).toBe("");
    expect(meetingClock("2026-10-06T10:30:00", new Date("2026-10-05T12:00:00"))).toBe("TUE 10:30");
  });

  it("takes the next calendar meeting that has not started", () => {
    const now = new Date("2026-10-05T12:00:00Z");
    const door = {
      upcoming: [
        { id: "s1", source: "scheduled_recording", title: "Armed", starts_at: "2026-10-05T13:00:00Z" },
        { id: "e0", source: "calendar_event", title: "Past", starts_at: "2026-10-05T11:00:00Z" },
        { id: "e1", source: "calendar_event", title: "Atlas weekly", starts_at: "2026-10-05T14:00:00Z" },
      ],
    };
    expect(nextMeeting(door, now)?.id).toBe("e1");
    expect(nextMeeting({ upcoming: [] }, now)).toBeNull();
  });
});

describe("Calendar card", () => {
  it("calendar URL use refusal keeps the typed link for retry", async () => {
    hub.check = () => recorded<Record<string, unknown>>(CHECK_OK_WIRE);
    hub.useCalendar = () => { throw new Error("Calendar use refused"); };
    renderExpandedFirstRun();
    const calendar = await screen.findByTestId("firstrun-calendar");
    const field = await within(calendar).findByRole("textbox", { name: "Calendar URL" });
    const url = recorded<{ url: string }>(CHECK_OK_WIRE).url;
    fireEvent.change(field, { target: { value: url } });
    fireEvent.click(within(calendar).getByRole("button", { name: "Add" }));
    expect(await within(calendar).findByText("Calendar use refused")).toBeTruthy();
    expect(field).toHaveValue(url);
  });

  it("first-use native permission guards stay unchanged when a feed is in use", async () => {
    hub.calendar = { ...hub.calendar, macos: { state: "denied", can_request: false }, candidates: [] };
    hub.sources = [source(recorded<{ url: string }>(CHECK_OK_WIRE).url)];
    renderExpandedFirstRun();
    const calendar = await screen.findByTestId("firstrun-calendar");
    await within(calendar).findByRole("status", { name: "IN USE" });
    expect(within(calendar).queryByRole("button", { name: "Allow calendar access" })).toBeNull();
    expect(within(calendar).queryByRole("button", { name: "Open System Settings" })).toBeNull();
  });
  it("first use shows unread owner identity and retries before editing", async () => {
    const base = mocks.apiFetch.getMockImplementation()!;
    let unread = true;
    hub.owner = { name: "Karol", aliases: ["Carol"] };
    mocks.apiFetch.mockImplementation(async (path: string, options: { method?: string; json?: unknown } = {}) => {
      if (path === "/api/settings" && (options.method ?? "GET") === "GET" && unread) throw new Error("Unavailable");
      return base(path, options);
    });
    renderExpandedFirstRun();
    const you = await screen.findByTestId("firstrun-you");
    const retry = await within(you).findByRole("button", { name: "Try again" });
    expect(within(you).queryByRole("textbox")).toBeNull();
    expect(calls.filter((call) => call.path === "/api/settings" && call.method === "PUT")).toHaveLength(0);
    unread = false;
    fireEvent.click(retry);
    await within(you).findByText("Carol");
    expect(within(you).getByRole("textbox", { name: "Your name" })).toHaveValue("Karol");
  });
  it("found: one Use it per calendar; IN USE is the hub's fact; the receipt follows", async () => {
    hub.calendar = { macos: { state: "full_access", can_request: false }, candidates: [MAC_CAL], sources: 0 };
    renderExpandedFirstRun();
    const cal = await screen.findByTestId("firstrun-calendar");
    await within(cal).findByRole("status", { name: "FOUND · 1" });
    // Speech is not on the device: First words cannot be the next press, so the Calendar is lit.
    expect(cal.getAttribute("data-lit")).toBe("true");
    expect(within(cal).queryByText("THIS DEVICE")).toBeNull();
    expect(within(cal).getByText("karol@acme.com")).toBeTruthy();
    hub.door = { upcoming: [{ id: "e1", source: "calendar_event", title: "Atlas weekly", starts_at: soon() }], week: { total: 14 } };
    await act(async () => {
      fireEvent.click(within(cal).getByRole("button", { name: "Use Work" }));
    });
    expect(calls.find((c) => c.path === "/api/onboarding/calendar/use")?.json).toEqual({ id: "eventkit:CAL-1", label: "Work" });
    await waitFor(() => expect(within(cal).getAllByRole("status", { name: "IN USE" })).toHaveLength(2));
    expect(within(cal).queryByRole("button", { name: /Refresh .* name/ })).toBeNull();
    expect(cal.getAttribute("data-selected")).toBe("true");
    expect(cal.getAttribute("data-lit")).toBeNull();
    await waitFor(() => expect(cal.textContent).toContain("14 EVENTS · NEXT ATLAS WEEKLY"), { timeout: 3000 });
    // The link field goes once a calendar is in use (artboard onb-A-conn).
    expect(within(cal).queryByRole("textbox", { name: "Calendar URL" })).toBeNull();
  });

  it("none: no FOUND chip, no prompt verb; a typed link names its host before Add", async () => {
    renderExpandedFirstRun();
    const cal = await screen.findByTestId("firstrun-calendar");
    const field = await within(cal).findByRole("textbox", { name: "Calendar URL" });
    expect(within(cal).queryByRole("status", { name: /FOUND/ })).toBeNull();
    expect(within(cal).queryByRole("button", { name: "Allow calendar access" })).toBeNull();
    const add = within(cal).getByRole("button", { name: "Add" }) as HTMLButtonElement;
    expect(add.disabled).toBe(true);
    expect(cal.querySelector(".gadget-chip-egress")).toBeNull();
    fireEvent.change(field, { target: { value: "webcal://p01-caldav.icloud.com/published/2/abc" } });
    expect(cal.querySelector(".gadget-chip-egress")?.textContent).toContain("P01-CALDAV.ICLOUD.COM");
    expect(add.disabled).toBe(false);
    // Nothing reached the network on load or on typing: only the detect read.
    expect(calls.filter((c) => c.path.startsWith("/api/onboarding/calendar/"))).toEqual([]);
  });

  it("added: Add reads the link once, then uses it; the row names its host", async () => {
    const url = "https://outlook.office365.com/owa/calendar/a/calendar.ics";
    // The hub's own check answer for this link (a feed named "Work (Outlook)").
    hub.check = (u) => {
      const hubCheck = recorded<Record<string, any>>(CHECK_OK_WIRE);
      return { ...hubCheck, url: u, candidate: { ...hubCheck.candidate, id: u }, events_next_days: 9 };
    };
    renderExpandedFirstRun();
    const cal = await screen.findByTestId("firstrun-calendar");
    fireEvent.change(await within(cal).findByRole("textbox", { name: "Calendar URL" }), { target: { value: url } });
    await act(async () => {
      fireEvent.click(within(cal).getByRole("button", { name: "Add" }));
    });
    const order = calls.filter((c) => c.method === "POST").map((c) => c.path);
    expect(order).toEqual(["/api/onboarding/calendar/check", "/api/onboarding/calendar/use"]);
    expect(calls.find((c) => c.path === "/api/onboarding/calendar/use")?.json).toEqual({ id: url, label: "Work (Outlook)" });
    await within(cal).findByText("Work (Outlook)");
    expect(within(cal).getAllByRole("status", { name: "IN USE" }).length).toBeGreaterThan(0);
    expect(within(cal).getByText("OUTLOOK.OFFICE365.COM")).toBeTruthy();
  });

  it("failed: CAN'T READ and the plain reason, as tokens; a bad link is named too", async () => {
    hub.check = () => ({ ...recorded<Record<string, unknown>>(CHECK_FAILED_WIRE), redirect_target: "https://login.example.com/x" });
    renderExpandedFirstRun();
    const cal = await screen.findByTestId("firstrun-calendar");
    const field = await within(cal).findByRole("textbox", { name: "Calendar URL" });
    fireEvent.change(field, { target: { value: "https://cal.example.com/a.ics" } });
    await act(async () => {
      fireEvent.click(within(cal).getByRole("button", { name: "Add" }));
    });
    const failure = await within(cal).findByTestId("firstrun-calendar-cant-read");
    expect(within(failure).getByRole("status", { name: "CAN'T READ" })).toBeTruthy();
    expect(failure.textContent).toContain("MOVED TO LOGIN.EXAMPLE.COM");
    expect(calls.some((c) => c.path === "/api/onboarding/calendar/use")).toBe(false);

    hub.check = () => {
      throw new ApiError(400, "Give an https:// or webcal:// calendar link.", { code: "calendar_url_invalid" });
    };
    fireEvent.change(field, { target: { value: "https://cal.example.com/b.ics" } });
    await act(async () => {
      fireEvent.click(within(cal).getByRole("button", { name: "Add" }));
    });
    await waitFor(() => expect(within(cal).getByTestId("firstrun-calendar-cant-read").textContent).toContain("NOT A CALENDAR LINK"));
  });

  it("denied: CALENDAR · NOT ALLOWED, then Open System Settings and Check again (PHILO-15 04)", async () => {
    hub.calendar = { macos: { state: "denied", can_request: false }, candidates: [], sources: 0 };
    renderExpandedFirstRun();
    const cal = await screen.findByTestId("firstrun-calendar");
    const denied = await within(cal).findByTestId("firstrun-calendar-denied");
    expect(within(denied).getByRole("status", { name: "CALENDAR · NOT ALLOWED" })).toBeTruthy();
    // The way forward: two verbs, the library Button, on this device.
    expect(within(denied).getAllByRole("button").map((b) => b.textContent)).toEqual([
      "Open System Settings", "Check again",
    ]);
    expect(within(denied).queryByText("THIS DEVICE")).toBeNull();
    expect(within(cal).queryByRole("button", { name: "Allow calendar access" })).toBeNull();
    // A link still works.
    expect(within(cal).getByRole("textbox", { name: "Calendar URL" })).toBeTruthy();

    // His press opens the Calendars pane (one owner-only system open).
    await act(async () => {
      fireEvent.click(within(denied).getByRole("button", { name: "Open System Settings" }));
    });
    expect(calls.filter((c) => c.path === "/api/onboarding/calendar/macos/settings" && c.method === "POST")).toHaveLength(1);
    expect(within(denied).queryByRole("status", { name: "SETTINGS · NOT OPENED" })).toBeNull();

    // He allows it there; Check again reads the new state and the card moves on.
    hub.calendar = { macos: { state: "full_access", can_request: false }, candidates: [MAC_CAL], sources: 0 };
    await act(async () => {
      fireEvent.click(within(denied).getByRole("button", { name: "Check again" }));
    });
    await within(cal).findByRole("status", { name: "FOUND · 1" });
    expect(within(cal).queryByTestId("firstrun-calendar-denied")).toBeNull();
  });

  it("denied: a pane that did not open says so", async () => {
    hub.calendar = { macos: { state: "denied", can_request: false }, candidates: [], sources: 0 };
    const base = mocks.apiFetch.getMockImplementation()!;
    mocks.apiFetch.mockImplementation(async (path: string, init: { method?: string; json?: unknown } = {}) => {
      if (path === "/api/onboarding/calendar/macos/settings") {
        throw new ApiError(409, "System Settings did not open.", { code: "system_settings_not_opened" });
      }
      return base(path, init);
    });
    renderExpandedFirstRun();
    const denied = await screen.findByTestId("firstrun-calendar-denied");
    await act(async () => {
      fireEvent.click(within(denied).getByRole("button", { name: "Open System Settings" }));
    });
    expect(await within(denied).findByRole("status", { name: "SETTINGS · NOT OPENED" })).toBeTruthy();
  });

  it("the macOS prompt shows only on his press; a 409 on Use it reads NOT ALLOWED", async () => {
    hub.calendar = { macos: { state: "not_determined", can_request: true }, candidates: [], sources: 0 };
    hub.access = () => {
      hub.calendar = { macos: { state: "full_access", can_request: false }, candidates: [MAC_CAL], sources: 0 };
      return hub.calendar;
    };
    hub.useCalendar = () => {
      throw new ApiError(409, "HoldSpeak cannot read your calendars yet.", { code: "calendar_permission_required" });
    };
    renderExpandedFirstRun();
    const cal = await screen.findByTestId("firstrun-calendar");
    const allow = await within(cal).findByRole("button", { name: "Allow calendar access" });
    expect(within(cal).queryByText("THIS DEVICE")).toBeNull();
    expect(calls.some((c) => c.path === "/api/onboarding/calendar/macos/access")).toBe(false);
    await act(async () => {
      fireEvent.click(allow);
    });
    expect(calls.filter((c) => c.path === "/api/onboarding/calendar/macos/access")).toHaveLength(1);
    await within(cal).findByRole("status", { name: "FOUND · 1" });
    hub.calendar = { macos: { state: "denied", can_request: false }, candidates: [], sources: 0 };
    await act(async () => {
      fireEvent.click(within(cal).getByRole("button", { name: "Use Work" }));
    });
    expect(await within(cal).findByRole("status", { name: "CALENDAR · NOT ALLOWED" })).toBeTruthy();
  });
});

describe("Connections card", () => {
  it("found: each row names its host; Use it -> CONNECTED only when the hub says so", async () => {
    hub.connections = { candidates: [gh(), jira()], tools: toolsBlock({ gh: true, acli: true }) };
    hub.sources = [source("eventkit:CAL-1")];
    renderExpandedFirstRun();
    const conn = await screen.findByTestId("firstrun-connections");
    await within(conn).findByRole("status", { name: "SIGNED IN · 2" });
    expect(conn.getAttribute("data-lit")).toBe("true");
    const chips = [...conn.querySelectorAll(".gadget-chip-egress")].map((e) => e.textContent);
    expect(chips.join(" ")).toContain("GITHUB.COM");
    expect(chips.join(" ")).toContain("ACME.ATLASSIAN.NET");
    expect(conn.textContent).toContain("gh · karolswdev");
    // replaces (the first-run leg): tests/e2e/test_philo15_18_rest_of_day_glass.py::TestOneSignInTruth::test_first_run_and_connections_say_the_same_sign_in
    // The same words Settings › Connections reads (web/src/desk/__tests__/connections.app.test.tsx).
    expect(within(conn).getByTestId("firstrun-connection-signin").textContent).toContain("Signed in · karolswdev · From gh config");
    await act(async () => {
      fireEvent.click(within(conn).getByRole("button", { name: "Use GitHub karolswdev" }));
    });
    expect(calls.find((c) => c.path === "/api/onboarding/connections/use")?.json).toEqual({ id: "github:github.com:karolswdev" });
    await within(conn).findByRole("status", { name: "CONNECTED" });
    // Jira still waits: not all done, still lit.
    expect(conn.getAttribute("data-selected")).toBeNull();
    expect(within(conn).getByRole("button", { name: "Use Jira karol@acme.com" })).toBeTruthy();
  });

  it("refused: the probe failed -> NOT CONNECTED and its reason; no CONNECTED", async () => {
    hub.connections = { candidates: [gh()], tools: toolsBlock({ gh: true }) };
    hub.useConnection = () => ({ candidate: "x", provider: "github", entry: { state: "owner_action_required", error_detail: "gh is not signed in." } });
    renderExpandedFirstRun();
    const conn = await screen.findByTestId("firstrun-connections");
    await act(async () => {
      fireEvent.click(await within(conn).findByRole("button", { name: "Use GitHub karolswdev" }));
    });
    expect(await within(conn).findByRole("status", { name: "NOT CONNECTED" })).toBeTruthy();
    expect(within(conn).getByText("gh is not signed in.")).toBeTruthy();
    expect(within(conn).queryByRole("status", { name: "CONNECTED" })).toBeNull();
  });

  it("none: NO SIGN-IN FOUND and why, as tokens; a row with no verb says why", async () => {
    const view = renderExpandedFirstRun();
    let conn = await screen.findByTestId("firstrun-connections");
    await within(conn).findByRole("status", { name: "NO SIGN-IN FOUND" });
    expect(conn.textContent).toContain("GH NOT INSTALLED");
    expect(conn.textContent).toContain("ACLI NOT INSTALLED");
    expect(within(conn).queryByRole("button")).toBeNull();
    // PHILO-15 11 (B29): one tool per line, so the tokens never read as one.
    const tools = within(conn).getByTestId("firstrun-connections-tools");
    expect(tools.hasAttribute("data-stack")).toBe(true);
    expect(Array.from(tools.children, (c) => c.textContent)).toEqual(["GH NOT INSTALLED", "ACLI NOT INSTALLED"]);
    view.unmount();

    hub.connections = { candidates: [gh({ active: false, verb: null, id: "github:github.com:other" })], tools: toolsBlock({ gh: true }) };
    renderExpandedFirstRun();
    conn = await screen.findByTestId("firstrun-connections");
    await within(conn).findByText("NOT ACTIVE IN GH");
    expect(within(conn).queryByRole("button", { name: /Use GitHub/ })).toBeNull();
  });

  it("PHILO-17: an installed tool with no sign-in shows its sign-in command with Copy, then Check again", async () => {
    hub.connections = { candidates: [], tools: toolsBlock({ gh: true }) };
    renderExpandedFirstRun();
    const conn = await screen.findByTestId("firstrun-connections");
    const well = await within(conn).findByTestId("firstrun-signin-gh");
    expect(well.textContent).toContain("gh auth login");
    expect(within(well).getByRole("button", { name: /Copy/ })).toBeTruthy();
    expect(conn.textContent).toContain("ACLI NOT INSTALLED");
    expect(conn.textContent).not.toContain("NO SIGN-IN ·");
    expect(conn.textContent).not.toContain("GH · NO SIGN-IN");
    const before = calls.filter((c) => c.path === "/api/onboarding/connections").length;
    await act(async () => {
      fireEvent.click(within(conn).getByRole("button", { name: "Check again" }));
    });
    await waitFor(() => expect(calls.filter((c) => c.path === "/api/onboarding/connections").length).toBe(before + 1));
  });
});

async function finishC1() {
  hub.ai = aiStatus(true);
  hub.owner = { name: "Karol Sane", aliases: ["Karol", "KS"] };
  renderExpandedFirstRun();
  const dictate = await screen.findByRole("button", { name: "◖ Dictate one sentence" });
  // Every first read has landed (the name, the detect reads) before his press.
  await screen.findByRole("status", { name: "SET" });
  await waitFor(() => expect(calls.some((c) => c.path === "/api/onboarding/connections")).toBe(true));
  await act(async () => {
    fireEvent.click(dictate);
  });
  await act(async () => {
    fireEvent.click(await screen.findByRole("button", { name: "Stop listening" }));
  });
  await act(async () => {
    fireEvent.click(await screen.findByRole("button", { name: "Keep as note" }));
  });
}

describe("Ready", () => {
  it("every step done: Ready, Karol; the strip; Record the next meeting; every card selected", async () => {
    hub.calendar = { macos: { state: "full_access", can_request: false }, candidates: [{ ...MAC_CAL, in_use: true }], sources: 1 };
    hub.sources = [source("eventkit:CAL-1")];
    hub.connections = { candidates: [gh({ connected: true }), jira({ connected: true })], tools: toolsBlock({}) };
    hub.door = { upcoming: [{ id: "e1", source: "calendar_event", title: "Atlas weekly", starts_at: soon() }], week: { total: 14 } };
    await finishC1();
    expect(await screen.findByRole("heading", { name: "Ready, Karol" })).toBeTruthy();
    const strip = screen.getByRole("list", { name: "Ready" });
    expect([...strip.querySelectorAll("[role=status]")].map((e) => e.getAttribute("aria-label"))).toEqual([
      "LOCAL AI · ON DEVICE",
      "HEARD · 8 WORDS",
      "CALENDAR · 14 THIS WEEK",
      "SEND TO · GITHUB · JIRA",
    ]);
    const verbs = within(screen.getByRole("group", { name: "Start" })).getAllByRole("button");
    expect(verbs.map((v) => v.textContent)).toEqual([
      `◉Record Atlas weekly · ${meetingClock(hub.door.upcoming[0] ? (hub.door.upcoming[0] as { starts_at: string }).starts_at : "")}`,
      "◖Dictate",
      "✦Ask about this week",
    ]);
    expect(verbs[0].className).toContain("btn--primary");
    for (const id of ["firstrun-local-ai", "firstrun-you", "firstrun-first-words", "firstrun-calendar", "firstrun-connections"]) {
      expect(card(id).getAttribute("data-selected")).toBe("true");
      expect(card(id).getAttribute("data-lit")).toBeNull();
    }
    // The C1 cards fold to their receipts: no inputs left on the You card.
    expect(within(card("firstrun-you")).queryByRole("textbox")).toBeNull();
    expect(within(card("firstrun-you")).getByText("Karol Sane")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Continue later" })).toBeNull();
    // PHILO-17: all set -> "Open my desk"; the start verbs keep the primary.
    expect(screen.getByRole("button", { name: "Open my desk" }).className).not.toContain("btn--primary");
    // One display element: the Ready heading (his words stepped down).
    expect(document.querySelectorAll(".surface-display")).toHaveLength(1);

    await act(async () => {
      fireEvent.click(verbs[0]);
    });
    expect(mocks.arm).toHaveBeenCalledWith("e1");
    await waitFor(() =>
      expect(calls.some((c) => c.path === "/api/setup/onboarding" && (c.json as { disposition: string }).disposition === "completed")).toBe(true),
    );
  });

  it("no meeting: Record is withheld and Dictate leads; Dictate and Ask hand off and open", async () => {
    hub.sources = [source("https://cal.example.com/a.ics")];
    await finishC1();
    await screen.findByRole("heading", { name: "Ready, Karol" });
    const group = screen.getByRole("group", { name: "Start" });
    expect(within(group).queryByRole("button", { name: /Record/ })).toBeNull();
    expect(within(group).getByRole("button", { name: /Dictate/ }).className).toContain("btn--primary");
    expect(screen.getByRole("list", { name: "Ready" }).textContent).toContain("CALENDAR · IN USE");
    expect(screen.getByRole("list", { name: "Ready" }).textContent).not.toContain("SEND TO");
    await act(async () => {
      fireEvent.click(within(group).getByRole("button", { name: /Ask about this week/ }));
    });
    await waitFor(() => expect(mocks.openAsk).toHaveBeenCalled());
    expect(readDurableDraft("desk-ask")?.text).toBe("What is on my calendar this week?");
    expect(calls.some((c) => c.path === "/api/setup/onboarding")).toBe(true);
  });

  it("not ready while the calendar is not in use", async () => {
    await finishC1();
    await screen.findByRole("heading", { name: "Get ready" });
    expect(screen.queryByTestId("firstrun-ready")).toBeNull();
    expect(card("firstrun-calendar").getAttribute("data-lit")).toBe("true");
    // PHILO-17: the C1 cards are done, so the exit is "Open my desk" (primary).
    expect(screen.queryByRole("button", { name: "Continue later" })).toBeNull();
    const open = screen.getByRole("button", { name: "Open my desk" });
    expect(open.className).toContain("btn--primary");
    await act(async () => {
      fireEvent.click(open);
    });
    await waitFor(() =>
      expect(calls.some((c) => c.path === "/api/setup/onboarding" && (c.json as { disposition: string }).disposition === "completed")).toBe(true),
    );
  });

  it("the strip says only what is true", () => {
    expect(
      readyItems({ heardText: "", calendar: { week: 0 }, connections: { providers: [] } }).map((i) => i.label),
    ).toEqual(["LOCAL AI · ON DEVICE", "HEARD", "CALENDAR · IN USE"]);
  });
});

describe("Astra #876 review fences", () => {
  it("P1: a kept sentence's note id is spent — after a reload, the next sentence is a NEW note", async () => {
    await finishC1();
    await screen.findByRole("heading", { name: "Get ready" });
    const first = calls.filter((c) => c.path === "/api/notes").map((c) => (c.json as { id: string }).id);
    expect(first).toHaveLength(1);
    cleanup(); // the reload: the page and its memory are gone; storage stays

    calls.length = 0;
    renderExpandedFirstRun();
    const dictate = await screen.findByRole("button", { name: "◖ Dictate one sentence" });
    await screen.findByRole("status", { name: "SET" });
    await act(async () => {
      fireEvent.click(dictate);
    });
    await act(async () => {
      fireEvent.click(await screen.findByRole("button", { name: "Stop listening" }));
    });
    await act(async () => {
      fireEvent.click(await screen.findByRole("button", { name: "Keep as note" }));
    });
    const second = calls.filter((c) => c.path === "/api/notes").map((c) => (c.json as { id: string }).id);
    expect(second).toHaveLength(1);
    expect(second[0]).not.toBe(first[0]);
  });

  it("P2: Ready waits for the ingest and offers the meeting that is next; Record arms the one next at the press", async () => {
    const tomorrow = new Date(Date.now() + 26 * 3600_000).toISOString();
    const today = new Date(Date.now() + 90 * 60_000).toISOString();
    const earlier = new Date(Date.now() + 30 * 60_000).toISOString();
    hub.calendar = { macos: { state: "full_access", can_request: false }, candidates: [MAC_CAL], sources: 1 };
    hub.sources = [source("https://cal.example.com/team.ics")];
    hub.door = { upcoming: [{ id: "e-tomorrow", source: "calendar_event", title: "Design review", starts_at: tomorrow }], week: { total: 1 } };
    // Today's calendar: its read lands 2 s after Use it.
    hub.useCalendar = (id) => {
      const added = source(id);
      hub.sources = [...hub.sources, added];
      hub.status[added.id] = "idle";
      setTimeout(() => {
        hub.status[added.id] = "success";
        hub.door = {
          upcoming: [
            { id: "e-today", source: "calendar_event", title: "Atlas weekly", starts_at: today },
            ...hub.door.upcoming,
          ],
          week: { total: 2 },
        };
      }, 2000);
      const hubSource = recorded<{ source: Record<string, unknown> }>(USE_CALENDAR_WIRE).source;
      return { ...recorded<Record<string, unknown>>(USE_CALENDAR_WIRE), source: { ...hubSource, id: added.id, url: id } };
    };
    await finishC1();
    await screen.findByRole("button", { name: /Record Design review/ });
    await act(async () => {
      fireEvent.click(within(card("firstrun-calendar")).getByRole("button", { name: "Use Work" }));
    });
    // While today's calendar is read, Ready offers no meeting at all.
    await waitFor(() => expect(screen.queryByTestId("firstrun-ready")).toBeNull());
    await new Promise((r) => setTimeout(r, 1200));
    expect(screen.queryByRole("button", { name: /Record Design review/ })).toBeNull();
    const record = await screen.findByRole("button", { name: /Record Atlas weekly/ }, { timeout: 6000 });
    // A still earlier meeting lands between the render and the press.
    hub.door = {
      upcoming: [{ id: "e-earlier", source: "calendar_event", title: "Standup", starts_at: earlier }, ...hub.door.upcoming],
      week: { total: 3 },
    };
    await act(async () => {
      fireEvent.click(record);
    });
    expect(mocks.arm).toHaveBeenCalledWith("e-earlier");
    expect(mocks.arm).not.toHaveBeenCalledWith("e-tomorrow");
  }, 15_000);

  it("P2: two signed-in GitHub hosts — one connection makes GitHub done; each host shows its true state", async () => {
    const ghe = gh({ id: "github:ghe.acme.com:karol", label: "karol", account: "karol", site: "ghe.acme.com", egress_host: "ghe.acme.com" });
    hub.sources = [source("eventkit:CAL-1")];
    hub.connections = { candidates: [gh(), ghe], tools: toolsBlock({ gh: true }) };
    // The connector stores ONE GitHub connection: the pressed host only.
    hub.useConnection = (id) => {
      hub.connections = {
        ...hub.connections,
        candidates: hub.connections.candidates.map((c) => ({ ...c, connected: c.id === id })),
      };
      return { candidate: id, provider: "github", egress_host: "ghe.acme.com", entry: { state: "connected" } };
    };
    await finishC1();
    const conn = card("firstrun-connections");
    await act(async () => {
      fireEvent.click(within(conn).getByRole("button", { name: "Use GitHub karol" }));
    });
    expect(await screen.findByRole("heading", { name: "Ready, Karol" })).toBeTruthy();
    // The true state per host: ghe connected; github.com still offers Use it.
    expect(within(conn).getAllByRole("status", { name: "CONNECTED" })).toHaveLength(1);
    expect(within(conn).getByRole("button", { name: "Use GitHub karolswdev" })).toBeTruthy();
  });

  it("P2: a disabled calendar is not IN USE and claims no Ready", async () => {
    hub.calendar = { macos: { state: "full_access", can_request: false }, candidates: [{ ...MAC_CAL, in_use: true }], sources: 1 };
    hub.sources = [source("eventkit:CAL-1", false)];
    await finishC1();
    const cal = card("firstrun-calendar");
    await within(cal).findByText("OFF IN SETTINGS");
    expect(within(cal).queryByRole("status", { name: "IN USE" })).toBeNull();
    expect(within(cal).queryByRole("button", { name: "Use Work" })).toBeNull();
    expect(cal.getAttribute("data-selected")).toBeNull();
    expect(screen.queryByTestId("firstrun-ready")).toBeNull();
    expect(screen.getByRole("heading", { name: "Get ready" })).toBeTruthy();
  });
});

describe("PHILO-17 U17/U18 — first run opened again, plain card words", () => {
  it("opened again after a first dictation: First words is done, the exit is Open my desk, and it closes", async () => {
    mocks.setup = { first_run: false };
    hub.ai = aiStatus(true);
    hub.owner = { name: "Karol Sane", aliases: [] };
    openFirstRun();
    renderExpandedFirstRun();
    const open = await screen.findByRole("button", { name: "Open my desk" });
    expect(open.className).toContain("btn--primary");
    expect(screen.queryByRole("button", { name: "Continue later" })).toBeNull();
    expect(card("firstrun-first-words").getAttribute("data-selected")).toBe("true");
    expect(within(card("firstrun-first-words")).getByRole("status", { name: "HEARD" })).toBeTruthy();
    expect(card("firstrun-first-words").getAttribute("data-lit")).toBeNull();
    await act(async () => {
      fireEvent.click(open);
    });
    await waitFor(() =>
      expect(calls.some((c) => c.path === "/api/setup/onboarding" && (c.json as { disposition: string }).disposition === "completed")).toBe(true),
    );
    expect(useFirstRunOpen.getState().open).toBe(false);
  });

  it("not done: the exit stays Continue later", async () => {
    renderExpandedFirstRun();
    await screen.findByRole("heading", { name: "Get ready" });
    expect(screen.getByRole("button", { name: "Continue later" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Open my desk" })).toBeNull();
  });

  it("first use leads with plain labels and keeps optional setup copy in its fold", async () => {
    hub.connections = { candidates: [], tools: toolsBlock({ gh: true, acli: true }) };
    renderExpandedFirstRun();
    await screen.findByTestId("firstrun-signin-acli");
    for (const id of ["firstrun-calendar", "firstrun-connections", "firstrun-agents"]) {
      const lines = card(id).querySelectorAll(".firstrun-card-line");
      expect(lines, id).toHaveLength(1);
      expect((lines[0].textContent ?? "").length, id).toBeGreaterThan(10);
    }
    for (const id of ["firstrun-local-ai", "firstrun-you", "firstrun-first-words"]) expect(card(id).querySelector(".firstrun-card-line")).toBeNull();
    expect(card("firstrun-agents").textContent).toContain("Hooks tell HoldSpeak");
    const face = screen.getByTestId("firstrun").textContent ?? "";
    for (const token of ["MY SERVER", "TOOLS UNKNOWN", "DEFAULT SET", "· NO SIGN-IN", "arrival"]) {
      expect(face).not.toContain(token);
    }
  });

  it("Calendar says OR only when another choice is on the card", async () => {
    const view = renderExpandedFirstRun();
    let cal = await screen.findByTestId("firstrun-calendar");
    expect(within(cal).getByText("CALENDAR URL")).toBeTruthy();
    expect(cal.textContent).not.toContain("OR A CALENDAR URL");
    view.unmount();
    hub.calendar = { macos: { state: "full_access", can_request: false }, candidates: [MAC_CAL], sources: 0 };
    renderExpandedFirstRun();
    cal = await screen.findByTestId("firstrun-calendar");
    await within(cal).findByText("OR A CALENDAR URL");
  });
});

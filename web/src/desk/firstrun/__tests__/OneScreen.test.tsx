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
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ApiError: (await importOriginal<typeof import("../../../lib/api")>()).ApiError,
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));
vi.mock("../../store", () => ({
  useDesk: Object.assign(() => undefined, {
    getState: () => ({ refresh: mocks.refresh, armEventRecording: mocks.arm, openAsk: mocks.openAsk }),
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
import { calendarReceipt } from "../CalendarCard";
import { cantReadReason, hostOf, meetingClock, nextMeeting } from "../calendarStep";
import { readyItems } from "../Ready";
import { readDurableDraft, clearDurableDraft } from "../../../lib/durableDraft";

const MB = 1_000_000;
const WORDS = "Send the cutover plan to Priya before Friday.";

function aiStatus(ready: boolean): LocalAiStatus {
  return {
    state: ready ? "ready" : "not_started",
    files: [
      { key: "whisper", label: "whisper-base", size_bytes: 142 * MB, on_device: ready, url: "https://huggingface.co/a" },
      { key: "starter", label: "Qwen3.5 4B", size_bytes: 2741 * MB, on_device: ready },
    ],
    bytes_total: 0,
    bytes_done: 0,
    egress: { destination: "huggingface.co" },
    speech: { model: "base", backend: "mlx", state: ready ? "on_device" : "will_download" },
    local_engine: { ready },
    error: "",
  };
}

const MAC_CAL = {
  id: "eventkit:CAL-1",
  kind: "macos",
  label: "Work",
  account: "karol@acme.com",
  calendar_kind: "caldav",
  lamp: "local",
  egress_host: null,
  in_use: false,
  verb: "Use it",
};

function gh(over: Record<string, unknown> = {}) {
  return {
    id: "github:github.com:karolswdev", provider: "github", label: "karolswdev", account: "karolswdev",
    site: "github.com", active: true, connected: false, lamp: "cloud", egress_host: "github.com", verb: "Use it",
    ...over,
  };
}
function jira(over: Record<string, unknown> = {}) {
  return {
    id: "jira:acme.atlassian.net|karol@acme.com", provider: "jira", label: "Karol", account: "karol@acme.com",
    site: "acme.atlassian.net", active: true, connected: false, lamp: "cloud", egress_host: "acme.atlassian.net",
    verb: "Use it", ...over,
  };
}

interface Hub {
  ai: LocalAiStatus;
  owner: { name: string; aliases: string[] };
  calendar: { macos: { state: string; can_request: boolean }; candidates: Record<string, unknown>[]; sources: number };
  access: () => Hub["calendar"];
  check: (url: string) => unknown;
  useCalendar: (id: string) => unknown;
  connections: { candidates: Record<string, unknown>[]; tools: Record<string, { installed: boolean }> };
  useConnection: (id: string) => unknown;
  door: { upcoming: unknown[]; week?: { total: number } };
}

let hub: Hub;
const calls: { path: string; method: string; json?: unknown }[] = [];
const soon = () => new Date(Date.now() + 2 * 3600_000).toISOString();

beforeEach(() => {
  calls.length = 0;
  clearDurableDraft("desk-ask");
  hub = {
    ai: aiStatus(false),
    owner: { name: "", aliases: [] },
    calendar: { macos: { state: "unavailable", can_request: false }, candidates: [], sources: 0 },
    access: () => hub.calendar,
    check: () => ({ ok: false, error_class: "calendar_source_http_error" }),
    useCalendar: (id) => {
      hub.calendar = {
        ...hub.calendar,
        sources: 1,
        candidates: hub.calendar.candidates.map((c) => (c.id === id ? { ...c, in_use: true } : c)),
      };
      return { added: true, source: { id: "src_1", url: id } };
    },
    connections: { candidates: [], tools: { gh: { installed: false }, acli: { installed: false } } },
    useConnection: (id) => {
      hub.connections = {
        ...hub.connections,
        candidates: hub.connections.candidates.map((c) => (c.id === id ? { ...c, connected: true } : c)),
      };
      return { candidate: id, provider: "github", entry: { state: "connected" } };
    },
    door: { upcoming: [] },
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
        return method === "GET" ? { owner: hub.owner } : { settings: {} };
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
        return hub.door;
      default:
        return {};
    }
  });
});

const card = (id: string) => screen.getByTestId(id);

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
  it("found: one Use it per calendar on THIS DEVICE; IN USE is the hub's fact; the receipt follows", async () => {
    hub.calendar = { macos: { state: "full_access", can_request: false }, candidates: [MAC_CAL], sources: 0 };
    render(<FirstRun />);
    const cal = await screen.findByTestId("firstrun-calendar");
    await within(cal).findByRole("status", { name: "FOUND · 1" });
    // Speech is not on the device: First words cannot be the next press, so the Calendar is lit.
    expect(cal.getAttribute("data-lit")).toBe("true");
    expect(within(cal).getByText("THIS DEVICE")).toBeTruthy();
    expect(within(cal).getByText("karol@acme.com")).toBeTruthy();
    hub.door = { upcoming: [{ id: "e1", source: "calendar_event", title: "Atlas weekly", starts_at: soon() }], week: { total: 14 } };
    await act(async () => {
      fireEvent.click(within(cal).getByRole("button", { name: "Use Work" }));
    });
    expect(calls.find((c) => c.path === "/api/onboarding/calendar/use")?.json).toEqual({ id: "eventkit:CAL-1", label: "Work" });
    await waitFor(() => expect(within(cal).getAllByRole("status", { name: "IN USE" })).toHaveLength(2));
    expect(cal.getAttribute("data-selected")).toBe("true");
    expect(cal.getAttribute("data-lit")).toBeNull();
    await waitFor(() => expect(cal.textContent).toContain("14 EVENTS · NEXT ATLAS WEEKLY"), { timeout: 3000 });
    // The link field goes once a calendar is in use (artboard onb-A-conn).
    expect(within(cal).queryByRole("textbox", { name: "Calendar URL" })).toBeNull();
  });

  it("none: no FOUND chip, no prompt verb; a typed link names its host before Add", async () => {
    render(<FirstRun />);
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
    hub.check = (u) => ({
      url: u, host: "outlook.office365.com", lamp: "cloud", ok: true,
      candidate: { id: u, kind: "ics", label: "Work (Outlook)", account: "outlook.office365.com", lamp: "cloud",
        egress_host: "outlook.office365.com", in_use: false, verb: "Use it" },
      events_next_days: 9, horizon_days: 14,
    });
    hub.useCalendar = () => {
      hub.calendar = { ...hub.calendar, sources: 1 };
      return { added: true, source: { id: "src_1", url } };
    };
    render(<FirstRun />);
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
    hub.check = () => ({ url: "x", host: "cal.example.com", lamp: "cloud", ok: false, error_class: "calendar_source_redirect",
      redirect_target: "https://login.example.com/x" });
    render(<FirstRun />);
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

  it("denied: CALENDAR · NOT ALLOWED; no verb the desk cannot honour", async () => {
    hub.calendar = { macos: { state: "denied", can_request: false }, candidates: [], sources: 0 };
    render(<FirstRun />);
    const cal = await screen.findByTestId("firstrun-calendar");
    const denied = await within(cal).findByTestId("firstrun-calendar-denied");
    expect(within(denied).getByRole("status", { name: "CALENDAR · NOT ALLOWED" })).toBeTruthy();
    // The desk cannot open System Settings (no-exit law): withheld, never dead.
    expect(within(denied).queryByRole("button")).toBeNull();
    expect(within(cal).queryByRole("button", { name: "Allow calendar access" })).toBeNull();
    // A link still works.
    expect(within(cal).getByRole("textbox", { name: "Calendar URL" })).toBeTruthy();
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
    render(<FirstRun />);
    const cal = await screen.findByTestId("firstrun-calendar");
    const allow = await within(cal).findByRole("button", { name: "Allow calendar access" });
    expect(within(cal).getByText("THIS DEVICE")).toBeTruthy();
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
    hub.connections = { candidates: [gh(), jira()], tools: { gh: { installed: true }, acli: { installed: true } } };
    hub.calendar = { ...hub.calendar, sources: 1 };
    render(<FirstRun />);
    const conn = await screen.findByTestId("firstrun-connections");
    await within(conn).findByRole("status", { name: "SIGNED IN · 2" });
    expect(conn.getAttribute("data-lit")).toBe("true");
    const chips = [...conn.querySelectorAll(".gadget-chip-egress")].map((e) => e.textContent);
    expect(chips.join(" ")).toContain("GITHUB.COM");
    expect(chips.join(" ")).toContain("ACME.ATLASSIAN.NET");
    expect(conn.textContent).toContain("gh · karolswdev");
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
    hub.connections = { candidates: [gh()], tools: { gh: { installed: true } } };
    hub.useConnection = () => ({ candidate: "x", provider: "github", entry: { state: "owner_action_required", error_detail: "gh is not signed in." } });
    render(<FirstRun />);
    const conn = await screen.findByTestId("firstrun-connections");
    await act(async () => {
      fireEvent.click(await within(conn).findByRole("button", { name: "Use GitHub karolswdev" }));
    });
    expect(await within(conn).findByRole("status", { name: "NOT CONNECTED" })).toBeTruthy();
    expect(within(conn).getByText("gh is not signed in.")).toBeTruthy();
    expect(within(conn).queryByRole("status", { name: "CONNECTED" })).toBeNull();
  });

  it("none: NO SIGN-IN FOUND and why, as tokens; a row with no verb says why", async () => {
    const view = render(<FirstRun />);
    let conn = await screen.findByTestId("firstrun-connections");
    await within(conn).findByRole("status", { name: "NO SIGN-IN FOUND" });
    expect(conn.textContent).toContain("GH NOT INSTALLED");
    expect(conn.textContent).toContain("ACLI NOT INSTALLED");
    expect(within(conn).queryByRole("button")).toBeNull();
    view.unmount();

    hub.connections = { candidates: [gh({ active: false, verb: null, id: "github:github.com:other" })], tools: { gh: { installed: true } } };
    render(<FirstRun />);
    conn = await screen.findByTestId("firstrun-connections");
    await within(conn).findByText("NOT ACTIVE IN GH");
    expect(within(conn).queryByRole("button", { name: /Use GitHub/ })).toBeNull();
  });
});

async function finishC1() {
  hub.ai = aiStatus(true);
  hub.owner = { name: "Karol Sane", aliases: ["Karol", "KS"] };
  render(<FirstRun />);
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
    hub.connections = { candidates: [gh({ connected: true }), jira({ connected: true })], tools: {} };
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
    hub.calendar = { ...hub.calendar, sources: 1 };
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
    expect(screen.getByRole("button", { name: "Continue later" })).toBeTruthy();
  });

  it("the strip says only what is true", () => {
    expect(
      readyItems({ heardText: "", calendar: { week: 0 }, connections: { providers: [] } }).map((i) => i.label),
    ).toEqual(["LOCAL AI · ON DEVICE", "HEARD", "CALENDAR · IN USE"]);
  });
});

import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { calendarSourceEgressChips, formatLocalClock, snapshotEgressChip, SettingsCore } from "../SettingsCore";
import type { SettingsResponse } from "../core-types";

const apiFetch = vi.hoisted(() => vi.fn());
const settings = vi.hoisted<SettingsResponse>(() => ({
  _revision: "calendar-r1",
  calendar: {
    sources: [
      { id: "src-work", label: "Work", url: "https://work.example/cal.ics", enabled: true },
      { id: "src-personal", label: "Personal", url: "/home/user/personal.ics", enabled: false },
    ],
  },
  _calendar_sources: [
    {
      id: "src-work", kind: "https", host: "work.example",
      refresh_seconds: 900, egress: true, label: "Work", enabled: true,
    },
    {
      id: "src-personal", kind: "file", host: "",
      refresh_seconds: 900, egress: false, label: "Personal", enabled: false,
    },
  ],
  meeting: { allow_actuators: true },
}));

vi.mock("../../../lib/api", () => ({
  apiFetch,
  readableError: (cause: unknown) => cause instanceof Error ? cause.message : "Request failed",
}));
vi.mock("../../pageSupport", () => ({
  useResource: (url: string) => ({
    data: url === "/api/settings" ? settings : { control_mode: "yolo", precedence: [] },
    setData: vi.fn(), loading: false, error: "", setError: vi.fn(), reload: vi.fn(),
  }),
}));
vi.mock("../core-hooks", () => ({
  useCoreWings: () => ({ view: "settings" }),
}));
vi.mock("../ContextualAssignment", () => ({
  ContextualAssignment: () => null,
}));

const WELL_INPUT = { name: "Calendar URL or file path" };

// HS-175-03: the 146-era GadgetTable became SurfaceLedgerRows (one per
// source: StateChip · label · ICS/SNAPSHOT · host EgressChip or THIS
// DEVICE · verbs Edit / Disable|Enable / Remove) with ONE connect well
// under the Connect calendar row (Add) or under a source row (Edit).
// Every behaviour the old group protected is asserted below on the new DOM.
describe("Meetings calendar source rows", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    apiFetch.mockResolvedValue({ settings: { ...settings, _revision: "calendar-r2" } });
  });

  afterEach(() => vi.useRealTimers());

  it("renders two source rows with label, type, enabled state, the verbs, and the speak-to-fill mic on the well", () => {
    render(<SettingsCore scope="meetings" />);
    const work = screen.getByTestId("calendar-source-src-work");
    expect(within(work).getByText("Work")).toBeInTheDocument();
    expect(within(work).getByText("ICS")).toBeInTheDocument();
    expect(within(work).getByRole("status")).toHaveAttribute("data-state", "idle");
    expect(within(work).getByRole("button", { name: "Edit" })).toBeInTheDocument();
    expect(within(work).getByRole("button", { name: "Disable" })).toBeInTheDocument();
    expect(within(work).getByRole("button", { name: "Remove" })).toBeInTheDocument();

    const personal = screen.getByTestId("calendar-source-src-personal");
    expect(within(personal).getByText("Personal")).toBeInTheDocument();
    // HS-175 counsel H2-2: a file source wears no reassurance chip.
    expect(within(personal).queryByText("THIS DEVICE")).toBeNull();
    // A disabled source: idle StateChip, muted label, Enable verb.
    expect(within(personal).getByRole("status")).toHaveAttribute("data-state", "idle");
    expect(within(personal).getByText("Personal")).toHaveAttribute("data-muted", "true");
    expect(within(personal).getByRole("button", { name: "Enable" })).toBeInTheDocument();

    // The one text well carries the mic (the voice law).
    fireEvent.click(screen.getByTestId("calendar-add-btn"));
    expect(screen.getByRole("textbox", WELL_INPUT)).toHaveValue("");
    expect(screen.getByRole("button", { name: /^Speak Calendar URL/ })).toBeInTheDocument();
  });

  it("names the host on the HTTPS source's egress chip and wears NO chip on the file source (absence is the signal)", () => {
    // HS-175 counsel C9 (H2-2): egress where egress happens; a file source
    // carries no reassurance chip -- THIS DEVICE belongs to the SNAPSHOT
    // verb, where a model runs.
    render(<SettingsCore scope="meetings" />);
    const chip = screen.getByText("work.example");
    expect(chip).toHaveClass("gadget-chip-egress");
    expect(chip).toHaveAttribute("data-scope", "cloud");
    expect(chip).toHaveAttribute("title", expect.stringContaining("Work"));
    const personal = screen.getByTestId("calendar-source-src-personal");
    expect(personal.querySelector(".gadget-chip-egress")).toBeNull();
    expect(within(personal).queryByText("THIS DEVICE")).toBeNull();
  });

  it("writes a changed URL through the sources wire from the row's Edit well", async () => {
    render(<SettingsCore scope="meetings" />);
    const work = screen.getByTestId("calendar-source-src-work");
    fireEvent.click(within(work).getByRole("button", { name: "Edit" }));
    const well = screen.getByTestId("calendar-well");
    const input = within(well).getByRole("textbox", WELL_INPUT);
    expect(input).toHaveValue("https://work.example/cal.ics");
    fireEvent.change(input, { target: { value: "https://new.example/feed.ics" } });
    fireEvent.click(within(well).getByRole("button", { name: "Save" }));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(700);
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/settings", {
      method: "PUT",
      json: expect.objectContaining({
        _revision: "calendar-r1",
        calendar: expect.objectContaining({
          sources: expect.arrayContaining([
            expect.objectContaining({ id: "src-work", url: "https://new.example/feed.ics" }),
          ]),
        }),
      }),
    });
    expect(screen.queryByTestId("calendar-well")).not.toBeInTheDocument();
  });

  it("adds a new source with a minted id from the Connect calendar well", async () => {
    const randomUUID = vi.spyOn(crypto, "randomUUID").mockReturnValue("a1b2c3d4-e5f6-7890-abcd-ef1234567890");
    try {
      render(<SettingsCore scope="meetings" />);
      fireEvent.click(screen.getByTestId("calendar-add-btn"));
      const well = screen.getByTestId("calendar-well");
      fireEvent.change(within(well).getByRole("textbox", WELL_INPUT), {
        target: { value: "https://new.example/feed.ics" },
      });
      fireEvent.click(within(well).getByRole("button", { name: "Save" }));
      await act(async () => {
        await vi.advanceTimersByTimeAsync(700);
      });
      expect(apiFetch).toHaveBeenCalledWith("/api/settings", {
        method: "PUT",
        json: expect.objectContaining({
          calendar: expect.objectContaining({
            sources: expect.arrayContaining([
              expect.objectContaining({
                id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                label: "",
                url: "https://new.example/feed.ics",
                enabled: true,
              }),
            ]),
          }),
        }),
      });
    } finally {
      randomUUID.mockRestore();
    }
  });

  it("keeps the well open and shows the refusal when the wire rejects the URL", async () => {
    const refusal = new Error('calendar source "sources[2]": calendar.subscription must be a file path or HTTPS URL');
    apiFetch.mockImplementation((url: string, init?: { method?: string }) => {
      if (url === "/api/settings" && init?.method === "PUT") return Promise.reject(refusal);
      return Promise.resolve({ settings: { ...settings, _revision: "calendar-r2" } });
    });
    render(<SettingsCore scope="meetings" />);
    fireEvent.click(screen.getByTestId("calendar-add-btn"));
    const well = screen.getByTestId("calendar-well");
    fireEvent.change(within(well).getByRole("textbox", WELL_INPUT), {
      target: { value: "ftp://nope.example/cal.ics" },
    });
    fireEvent.click(within(well).getByRole("button", { name: "Save" }));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(700);
    });
    const stillOpen = screen.getByTestId("calendar-well");
    expect(within(stillOpen).getByRole("status")).toHaveAttribute("data-state", "failure");
    expect(stillOpen.textContent).toContain("must be a file path or HTTPS URL");
  });

  it("removes a source after the in-world confirm step (never a modal)", async () => {
    render(<SettingsCore scope="meetings" />);
    const work = screen.getByTestId("calendar-source-src-work");
    fireEvent.click(within(work).getByRole("button", { name: "Remove" }));
    const confirm = screen.getByTestId("calendar-remove-confirm");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(within(confirm).getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    fireEvent.click(within(confirm).getByRole("button", { name: "Remove" }));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(700);
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/settings", {
      method: "PUT",
      json: expect.objectContaining({
        calendar: expect.objectContaining({
          sources: [expect.objectContaining({ id: "src-personal" })],
        }),
      }),
    });
  });

  it("toggles a source's enabled state through the sources wire", async () => {
    render(<SettingsCore scope="meetings" />);
    const personal = screen.getByTestId("calendar-source-src-personal");
    fireEvent.click(within(personal).getByRole("button", { name: "Enable" }));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(700);
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/settings", {
      method: "PUT",
      json: expect.objectContaining({
        calendar: expect.objectContaining({
          sources: expect.arrayContaining([
            expect.objectContaining({ id: "src-personal", enabled: true }),
          ]),
        }),
      }),
    });
  });
});

describe("Snapshot verb refusal (HS-147-05)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    apiFetch.mockResolvedValue({ settings: { ...settings, _revision: "calendar-r2" } });
  });

  afterEach(() => vi.useRealTimers());

  it("surfaces a 422 upload refusal in the status bar", async () => {
    render(<SettingsCore scope="meetings" />);

    // Intercept the dynamically created file input
    let capturedInput: HTMLInputElement | null = null;
    const originalCreate = document.createElement.bind(document);
    vi.spyOn(document, "createElement").mockImplementation((tag: string, options?: ElementCreationOptions) => {
      const el = originalCreate(tag, options);
      if (tag === "input" && !capturedInput) {
        capturedInput = el as HTMLInputElement;
        // Prevent the real click (no file dialog in JSDOM)
        vi.spyOn(el, "click").mockImplementation(() => {});
      }
      return el;
    });

    // Make the snapshot upload reject with a 422
    const uploadError = new Error("File 1: unsupported type text/plain; use PNG, JPEG, or WebP");
    apiFetch.mockImplementation((url: string) => {
      if (url === "/api/calendar/snapshot") return Promise.reject(uploadError);
      return Promise.resolve({ settings: { ...settings, _revision: "calendar-r2" } });
    });

    // Click the Snapshot verb on the Connect calendar row
    fireEvent.click(screen.getByRole("button", { name: "Snapshot" }));

    expect(capturedInput).not.toBeNull();
    expect(capturedInput!.type).toBe("file");

    // Simulate file selection by calling the onchange handler
    const mockFile = new File(["fake"], "bad.txt", { type: "text/plain" });
    Object.defineProperty(capturedInput!, "files", {
      value: [mockFile],
      writable: false,
    });
    Object.defineProperty(capturedInput!.files!, "length", { value: 1 });

    // Trigger onchange
    await act(async () => {
      capturedInput!.onchange?.(new Event("change"));
      await vi.advanceTimersByTimeAsync(100);
    });

    // The refusal should appear in the status bar (role="alert")
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("unsupported type");
  });
});

describe("calendarSourceEgressChips", () => {
  it("produces one chip per enabled HTTPS source", () => {
    const chips = calendarSourceEgressChips([
      { id: "s1", kind: "https", host: "cal.example", refresh_seconds: 900, egress: true, label: "Main", enabled: true },
      { id: "s2", kind: "file", host: "", refresh_seconds: 900, egress: false, label: "Local", enabled: true },
    ]);
    expect(chips).toHaveLength(1);
    expect(chips[0].label).toContain("MAIN");
    expect(chips[0].label).toContain("CAL.EXAMPLE");
    expect(chips[0].scope).toBe("cloud");
  });

  it("skips disabled HTTPS sources", () => {
    const chips = calendarSourceEgressChips([
      { id: "s1", kind: "https", host: "cal.example", refresh_seconds: 900, egress: true, label: "Off", enabled: false },
    ]);
    expect(chips).toHaveLength(0);
  });

  it.each([
    [{ kind: "file" as const, host: null, refresh_seconds: null, egress: false, enabled: true }],
    [{ kind: "disabled" as const, host: null, refresh_seconds: null, egress: false, enabled: true }],
    [{ kind: "invalid" as const, host: null, refresh_seconds: null, egress: false, enabled: true }],
  ] as const)("does not mint an egress chip for %o", (fact) => {
    expect(calendarSourceEgressChips([fact])).toHaveLength(0);
  });

  it("returns empty array for undefined input", () => {
    expect(calendarSourceEgressChips(undefined)).toEqual([]);
  });
});

// HS-175 counsel C8 / C9(b) / C10 on the Settings rows: N EVENTS, LAST READ in
// the viewer's clock, the snapshot's egress chip beside Snapshot, Edit
// withheld on the SNAPSHOT row.
describe("HS-175 counsel: honest tokens on the calendar rows", () => {
  const snapshotSettings: SettingsResponse = {
    ...settings,
    calendar: {
      sources: [
        ...(settings.calendar as { sources: unknown[] }).sources,
        { id: "src-snap", label: "O365 SNAPSHOT", url: "/home/user/.local/share/holdspeak/calendar-snapshots/x.ics", enabled: true },
      ],
    },
  } as SettingsResponse;
  const calSources = {
    sources: [
      { id: "src-work", label: "Work", type: "ICS", status: "success", host: "work.example", event_count: 40, last_read: "17:47", last_read_at: "2026-09-05T23:47:00Z", egress: true },
      { id: "src-snap", label: "O365 SNAPSHOT", type: "SNAPSHOT", status: "success", host: null, event_count: 1, last_read: null, last_read_at: null, egress: false },
    ],
    auto_record: "off",
    auto_record_lead_minutes: 5,
    matched_this_week: 0,
    snapshot_egress: { scope: "private_network", host: "192.168.1.43" },
  };

  const sourcesOf = (s: SettingsResponse) => (s.calendar as { sources: Array<Record<string, unknown>> }).sources;
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    // The rows come from the settings resource (mocked useResource), so the
    // SNAPSHOT source rides the hoisted settings for this block only.
    sourcesOf(settings).push({ id: "src-snap", label: "O365 SNAPSHOT", url: "/home/user/.local/share/holdspeak/calendar-snapshots/x.ics", enabled: true });
    apiFetch.mockImplementation((url: string) => {
      if (url === "/api/calendar/sources") return Promise.resolve(calSources);
      return Promise.resolve({ settings: { ...snapshotSettings, _revision: "calendar-r2" } });
    });
  });
  afterEach(() => {
    sourcesOf(settings).pop();
    vi.useRealTimers();
  });

  it("counts EVENTS (never CALENDARS) and prints LAST READ in the viewer's local clock", async () => {
    render(<SettingsCore scope="meetings" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(10); });
    const work = screen.getByTestId("calendar-source-src-work");
    expect(within(work).getByTestId("calendar-source-events").textContent).toBe("40 EVENTS");
    expect(within(work).queryByText(/CALENDARS/)).toBeNull();
    const expected = formatLocalClock("2026-09-05T23:47:00Z");
    expect(within(work).getByTestId("calendar-source-last-read").textContent).toBe(`LAST READ ${expected}`);
  });

  it("wears the vision model's egress chip beside Snapshot BEFORE any upload", async () => {
    render(<SettingsCore scope="meetings" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(10); });
    const chip = screen.getByTestId("calendar-snapshot-egress").querySelector(".gadget-chip-egress") as HTMLElement;
    expect(chip).not.toBeNull();
    expect(chip).toHaveAttribute("data-scope", "mixed");
    expect(chip.textContent).toBe("192.168.1.43");
    expect(screen.getByTestId("calendar-snapshot-btn")).toBeInTheDocument();
  });

  it("withholds Edit on the SNAPSHOT row (its path is generated) and keeps Disable / Remove", async () => {
    render(<SettingsCore scope="meetings" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(10); });
    const snap = screen.getByTestId("calendar-source-src-snap");
    expect(within(snap).queryByRole("button", { name: "Edit" })).toBeNull();
    expect(within(snap).getByRole("button", { name: "Disable" })).toBeInTheDocument();
    expect(within(snap).getByRole("button", { name: "Remove" })).toBeInTheDocument();
    expect(within(snap).getByText("SNAPSHOT")).toBeInTheDocument();
    const work = screen.getByTestId("calendar-source-src-work");
    expect(within(work).getByRole("button", { name: "Edit" })).toBeInTheDocument();
  });
});

describe("formatLocalClock (C8)", () => {
  it("prints HH:MM in the viewer's zone from an ISO-UTC instant", () => {
    const d = new Date("2026-09-05T23:47:00Z");
    const pad = (n: number) => String(n).padStart(2, "0");
    expect(formatLocalClock("2026-09-05T23:47:00Z")).toBe(`${pad(d.getHours())}:${pad(d.getMinutes())}`);
    expect(formatLocalClock("2026-09-05T17:47:00-06:00")).toBe(formatLocalClock("2026-09-05T23:47:00Z"));
  });
  it("prints nothing for an empty or unparseable value", () => {
    expect(formatLocalClock(null)).toBeNull();
    expect(formatLocalClock("")).toBeNull();
    expect(formatLocalClock("not a clock")).toBeNull();
  });
});

describe("snapshotEgressChip (C10)", () => {
  it("is THIS DEVICE when the vision model runs locally", () => {
    expect(snapshotEgressChip({ scope: "local" })).toMatchObject({ label: "THIS DEVICE", scope: "local" });
  });
  it("names the LAN / paired / cloud host", () => {
    expect(snapshotEgressChip({ scope: "private_network", host: "192.168.1.43" })).toMatchObject({ label: "192.168.1.43", scope: "mixed" });
    expect(snapshotEgressChip({ scope: "mesh", host: "desktop" })).toMatchObject({ label: "desktop", scope: "mixed" });
    expect(snapshotEgressChip({ scope: "cloud", host: "api.openai.com" })).toMatchObject({ label: "api.openai.com", scope: "cloud" });
  });
  it("is absent when nothing resolves (nothing can leave)", () => {
    expect(snapshotEgressChip(null)).toBeNull();
    expect(snapshotEgressChip(undefined)).toBeNull();
    expect(snapshotEgressChip({ scope: "cloud", host: "" })).toBeNull();
  });
});


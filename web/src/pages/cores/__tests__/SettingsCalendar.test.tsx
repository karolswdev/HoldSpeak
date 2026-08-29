import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { calendarSourceEgressChips, SettingsCore } from "../SettingsCore";
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

describe("Meetings calendar sources list editor", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    apiFetch.mockResolvedValue({ settings: { ...settings, _revision: "calendar-r2" } });
  });

  afterEach(() => vi.useRealTimers());

  it("renders two source rows with label, url, and enabled controls plus speak-to-fill mics", () => {
    render(<SettingsCore scope="meetings" />);
    const workLabel = screen.getByRole("textbox", { name: "Source 1 label" });
    expect(workLabel).toHaveValue("Work");
    const workUrl = screen.getByRole("textbox", { name: "Source 1 URL" });
    expect(workUrl).toHaveValue("https://work.example/cal.ics");
    expect(screen.getByRole("checkbox", { name: "Enable source 1" })).toBeChecked();
    expect(screen.getByRole("textbox", { name: "Source 2 label" })).toHaveValue("Personal");
    expect(screen.getByRole("textbox", { name: "Source 2 URL" })).toHaveValue("/home/user/personal.ics");
    expect(screen.getByRole("checkbox", { name: "Enable source 2" })).not.toBeChecked();
    expect(screen.getByRole("button", { name: /^Speak Source 1 label/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Speak Source 1 URL/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Speak Source 2 label/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Speak Source 2 URL/ })).toBeInTheDocument();
  });

  it("renders one HTTPS egress chip for the enabled source and none for the disabled file source", () => {
    render(<SettingsCore scope="meetings" />);
    const chip = screen.getByText(/FETCHES WORK/);
    expect(chip).toHaveAttribute("data-scope", "cloud");
    expect(chip).toHaveAttribute("title", expect.stringContaining("Work"));
    expect(screen.queryByText(/FETCHES PERSONAL/)).not.toBeInTheDocument();
  });

  it("writes through the sources wire when a URL changes", async () => {
    render(<SettingsCore scope="meetings" />);
    fireEvent.change(screen.getByRole("textbox", { name: "Source 1 URL" }), {
      target: { value: "https://new.example/feed.ics" },
    });
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
  });

  it("adds a new source row with a minted id on ADD click", async () => {
    const randomUUID = vi.spyOn(crypto, "randomUUID").mockReturnValue("a1b2c3d4-e5f6-7890-abcd-ef1234567890");
    try {
      render(<SettingsCore scope="meetings" />);
      fireEvent.click(screen.getByText("+ ADD SOURCE"));
      await act(async () => {
        await vi.advanceTimersByTimeAsync(700);
      });
      expect(apiFetch).toHaveBeenCalledWith("/api/settings", {
        method: "PUT",
        json: expect.objectContaining({
          calendar: expect.objectContaining({
            sources: expect.arrayContaining([
              expect.objectContaining({ id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890", label: "", url: "", enabled: true }),
            ]),
          }),
        }),
      });
    } finally {
      randomUUID.mockRestore();
    }
  });

  it("removes a source row on REMOVE confirmation", async () => {
    render(<SettingsCore scope="meetings" />);
    const deleteButtons = screen.getAllByRole("button", { name: /Delete row/ });
    fireEvent.click(deleteButtons[0]);
    const confirmButton = screen.getByText("REMOVE?");
    fireEvent.click(confirmButton);
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

  it("toggles a source enabled state", async () => {
    render(<SettingsCore scope="meetings" />);
    const checkbox = screen.getByRole("checkbox", { name: "Enable source 2" });
    fireEvent.click(checkbox);
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

describe("IMPORT SCREENSHOT button refusal (HS-147-05)", () => {
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

    // Click the IMPORT SCREENSHOT button
    const importBtn = screen.getByText("IMPORT SCREENSHOT");
    fireEvent.click(importBtn);

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

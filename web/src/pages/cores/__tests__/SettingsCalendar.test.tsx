import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { calendarEgressChipProps, SettingsCore } from "../SettingsCore";
import type { SettingsResponse } from "../core-types";

const apiFetch = vi.hoisted(() => vi.fn());
const settings = vi.hoisted<SettingsResponse>(() => ({
  _revision: "calendar-r1",
  calendar: { subscription: "https://calendar.example/team.ics" },
  _calendar_subscription: {
    kind: "https", host: "calendar.example", refresh_seconds: 900, egress: true,
  },
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

describe("Meetings calendar subscription", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    apiFetch.mockResolvedValue({ settings: { ...settings, _revision: "calendar-r2" } });
  });

  afterEach(() => vi.useRealTimers());

  it("renders the Meetings Calendar input with its speak-to-fill mic and one derived HTTPS egress chip", () => {
    render(<SettingsCore scope="meetings" />);
    expect(screen.getByRole("textbox", { name: "Calendar subscription" })).toHaveAttribute(
      "placeholder", "ICS file path or HTTPS URL",
    );
    expect(screen.getByRole("button", { name: /^Speak Calendar subscription/ })).toBeInTheDocument();
    const chip = screen.getByText("FETCHES CALENDAR.EXAMPLE · 15 MIN");
    expect(chip).toHaveAttribute("data-scope", "cloud");
    expect(chip).toHaveAttribute("title", expect.stringContaining("calendar.example"));
  });

  it("uses the existing revisioned full-document writer and keeps a cleared subscription a string", async () => {
    render(<SettingsCore scope="meetings" />);
    fireEvent.change(screen.getByRole("textbox", { name: "Calendar subscription" }), {
      target: { value: "" },
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(700);
    });
    expect(apiFetch).toHaveBeenCalledWith("/api/settings", {
      method: "PUT",
      json: expect.objectContaining({
        _revision: "calendar-r1",
        calendar: { subscription: "" },
      }),
    });
  });

  it.each([
    [{ kind: "file", host: null, refresh_seconds: null, egress: false }],
    [{ kind: "disabled", host: null, refresh_seconds: null, egress: false }],
    [{ kind: "invalid", host: null, refresh_seconds: null, egress: false }],
  ] as const)("does not mint an egress chip for %o", (fact) => {
    expect(calendarEgressChipProps(fact)).toBeNull();
  });
});

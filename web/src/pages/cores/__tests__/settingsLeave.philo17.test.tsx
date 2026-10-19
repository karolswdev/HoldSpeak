// PHILO-17 words (Astra r2 on #1090): the leave send must not wait behind a
// save in flight. On pagehide the unsent edits go out at once, in the same
// tick, as one keepalive PUT of only the changed paths, with no revision.
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SettingsCore } from "../SettingsCore";
import type { SettingsResponse } from "../core-types";

const apiFetch = vi.hoisted(() => vi.fn());
const settings = vi.hoisted<SettingsResponse>(() => ({
  _revision: "leave-r1",
  calendar: {
    sources: [
      { id: "src-work", label: "Work", url: "https://work.example/cal.ics", enabled: true },
    ],
  },
  _calendar_sources: [],
  meeting: { auto_export: false, export_format: "txt" },
}));

vi.mock("../../../lib/api", () => ({
  apiFetch,
  ApiError: class ApiError extends Error {},
  readableError: (cause: unknown) => cause instanceof Error ? cause.message : "Request failed",
}));
vi.mock("../../pageSupport", () => ({
  useResource: (url: string) => ({
    data: url === "/api/settings" ? settings : { control_mode: "yolo", precedence: [] },
    setData: vi.fn(), loading: false, error: "", setError: vi.fn(), reload: vi.fn(),
  }),
}));
vi.mock("../core-hooks", () => ({
  useCoreWings: () => ({ view: "settings", setView: vi.fn() }),
}));
vi.mock("../ContextualAssignment", () => ({ ContextualAssignment: () => null }));

const puts = () => apiFetch.mock.calls.filter(([url, init]) => url === "/api/settings" && init?.method === "PUT");

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
  // A PUT never answers: the first save stays in flight.
  apiFetch.mockImplementation((url: string, init?: { method?: string }) =>
    url === "/api/settings" && init?.method === "PUT" ? new Promise(() => undefined) : Promise.resolve({}));
});
afterEach(() => vi.useRealTimers());

describe("Settings leave send", () => {
  it("a save in flight + a newer edit + pagehide: the leave PUT goes out in the same tick", async () => {
    // Betterment setup ST1: the calendar rows moved to Accounts; the first
    // (in-flight) edit is Auto export, the newer one Auto-record.
    render(<SettingsCore scope="meetings" />);
    fireEvent.click(screen.getByRole("checkbox", { name: "Auto export" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });
    expect(puts()).toHaveLength(1); // in flight, never answers

    // An unsent edit (debounced), then the page hides before the delay ends.
    fireEvent.change(screen.getByRole("combobox", { name: "Auto-record mode" }), { target: { value: "room_linked" } });
    window.dispatchEvent(new Event("pagehide"));

    expect(puts()).toHaveLength(2);
    const [, init] = puts()[1];
    expect(init.keepalive).toBe(true);
    expect(init.json._revision).toBeUndefined();
    // Only the changed paths (never the whole stale document): the newer
    // unsent edit, plus the in-flight change (newest values win either way).
    expect(Object.keys(init.json).sort()).toEqual(["meeting"]);
    expect(init.json.meeting).toEqual({ auto_export: true, auto_record: "room_linked" });
  });

  it("nothing unsent and nothing queued sends nothing on pagehide", () => {
    render(<SettingsCore scope="meetings" />);
    window.dispatchEvent(new Event("pagehide"));
    expect(puts()).toHaveLength(0);
  });
});

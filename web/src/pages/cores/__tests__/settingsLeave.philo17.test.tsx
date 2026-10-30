// PHILO-17 words (Astra r2 on #1090): the leave send must not wait behind a
// save in flight. On pagehide the unsent edits go out at once, in the same
// tick, as one keepalive PUT of only the changed paths, with no revision.
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SettingsCore } from "../SettingsCore";
import type { SettingsResponse } from "../core-types";
import hubWire from "../../../desk/__tests__/fixtures/settings-wire/hub.json";

const apiFetch = vi.hoisted(() => vi.fn());
const ApiError = vi.hoisted(() => class TestApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
});
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
  ApiError,
  readableError: (cause: unknown) => cause instanceof Error ? cause.message : "Request failed",
}));
vi.mock("../../pageSupport", async () => {
  const React = await import("react");
  const noop = vi.fn();
  return {
    useResource: (url: string) => {
      const [data, setData] = React.useState(
        url === "/api/settings" ? settings : url === "/api/settings/hub" ? hubWire : { control_mode: "yolo", precedence: [] },
      );
      return { data, setData, loading: false, error: "", setError: noop, reload: noop };
    },
  };
});
vi.mock("../core-hooks", () => ({
  useCoreWings: () => ({ view: "settings", setView: vi.fn() }),
}));
vi.mock("../ContextualAssignment", () => ({ ContextualAssignment: () => null }));

// The queries stay cheap. A role query by name computes the accessible name
// of EVERY element of that role on the whole Settings face, and each name
// reads getComputedStyle against every stylesheet (vitest css: true): the
// case "reconciles an old 409 ..." spent 2.4 s of its 2.7 s in those queries
// and went over the 5 s limit under load. A label finds the one control; the
// Retry query looks only in the status bar, where the save refusal puts it.
const control = (label: string) => screen.getByLabelText(label);
const retryButtons = () => within(screen.getByTestId("settings-status")).getAllByRole("button", { name: "Retry" });
const puts = () => apiFetch.mock.calls.filter(([url, init]) => url === "/api/settings" && init?.method === "PUT");
const settingsWithMeeting = (revision: string, meeting: Record<string, unknown>): SettingsResponse => ({
  ...settings,
  _revision: revision,
  meeting: { ...(settings.meeting ?? {}), ...meeting },
});

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
    // (in-flight) edit is Auto export, the newer one summary timing (Auto-record lives in Meetings).
    render(<SettingsCore scope="meetings" />);
    fireEvent.click(control("Auto export"));
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });
    expect(puts()).toHaveLength(1); // in flight, never answers

    // An unsent edit (debounced), then the page hides before the delay ends.
    fireEvent.change(control("Auto-run the summary"), { target: { value: "every" } });
    window.dispatchEvent(new Event("pagehide"));

    expect(puts()).toHaveLength(2);
    const [, init] = puts()[1];
    expect(init.keepalive).toBe(true);
    expect(init.json._revision).toBeUndefined();
    // Only the changed paths (never the whole stale document): the newer
    // unsent edit, plus the in-flight change (newest values win either way).
    expect(Object.keys(init.json).sort()).toEqual(["meeting"]);
    expect(init.json.meeting).toEqual({ auto_export: true, intelligence_auto: "every" });
  });

  it("nothing unsent and nothing queued sends nothing on pagehide", () => {
    render(<SettingsCore scope="meetings" />);
    window.dispatchEvent(new Event("pagehide"));
    expect(puts()).toHaveLength(0);
  });

  it("keeps a new draft and Retry after hide/show and a later revision conflict", async () => {
    let authoritative = settingsWithMeeting("return-r1", { intelligence_auto: "manual" });
    apiFetch.mockImplementation(async (url: string, init?: { method?: string; keepalive?: boolean; json?: Record<string, unknown> }) => {
      if (url === "/api/settings" && init?.method === "PUT") {
        if (init.keepalive) {
          const patch = (init.json?.meeting ?? {}) as Record<string, unknown>;
          authoritative = {
            ...authoritative,
            _revision: "return-r2",
            meeting: { ...(authoritative.meeting ?? {}), ...patch },
          };
          return { settings: authoritative };
        }
        authoritative = { ...authoritative, _revision: "external-r3" };
        throw new ApiError(409, "Settings changed in another session");
      }
      if (url === "/api/settings") return authoritative;
      return {};
    });

    render(<SettingsCore scope="meetings" />);
    fireEvent.click(control("Auto export"));
    await act(async () => {
      window.dispatchEvent(new Event("pagehide"));
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(puts()).toHaveLength(1);
    expect(puts()[0][1].keepalive).toBe(true);

    window.dispatchEvent(new Event("pageshow"));
    fireEvent.change(control("Auto-run the summary"), { target: { value: "every" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });

    expect(puts()).toHaveLength(2);
    expect(control("Auto-run the summary")).toHaveValue("every");
    expect(retryButtons().length).toBeGreaterThan(0);
  });

  it("does not duplicate a successful leave patch across repeated hide/show", async () => {
    apiFetch.mockImplementation(async (url: string, init?: { method?: string; keepalive?: boolean }) => {
      if (url === "/api/settings" && init?.method === "PUT") return { settings: settingsWithMeeting("leave-r2", { auto_export: true }) };
      return {};
    });

    render(<SettingsCore scope="meetings" />);
    fireEvent.click(control("Auto export"));
    await act(async () => {
      window.dispatchEvent(new Event("pagehide"));
      await Promise.resolve();
      await Promise.resolve();
      window.dispatchEvent(new Event("pageshow"));
      window.dispatchEvent(new Event("pagehide"));
      await Promise.resolve();
    });

    expect(puts()).toHaveLength(1);
  });

  it("retains leave edits when the keepalive fails, then retries the latest patch", async () => {
    let authoritative = settingsWithMeeting("failure-r1", { intelligence_auto: "manual" });
    let rejectOld!: (reason?: unknown) => void;
    const oldSave = new Promise<never>((_, reject) => { rejectOld = reject; });
    let ordinaryPuts = 0;
    apiFetch.mockImplementation((url: string, init?: { method?: string; keepalive?: boolean; json?: Record<string, unknown> }) => {
      if (url === "/api/settings" && init?.method === "PUT") {
        if (init.keepalive) return Promise.reject(new ApiError(503, "Leave save failed"));
        ordinaryPuts += 1;
        if (ordinaryPuts === 1) {
          authoritative = { ...authoritative, _revision: "failure-r2" };
          return oldSave;
        }
        const patch = (init.json?.meeting ?? {}) as Record<string, unknown>;
        authoritative = {
          ...authoritative,
          _revision: "failure-r3",
          meeting: { ...(authoritative.meeting ?? {}), ...patch },
        };
        return Promise.resolve({ settings: authoritative });
      }
      if (url === "/api/settings") return Promise.resolve(authoritative);
      return Promise.resolve({});
    });

    render(<SettingsCore scope="meetings" />);
    fireEvent.click(control("Auto export"));
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });
    fireEvent.change(control("Auto-run the summary"), { target: { value: "every" } });
    await act(async () => {
      window.dispatchEvent(new Event("pagehide"));
      await Promise.resolve();
      await Promise.resolve();
      rejectOld(new ApiError(409, "Settings changed in another session"));
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(control("Auto-run the summary")).toHaveValue("every");
    expect(retryButtons().length).toBeGreaterThan(0);

    await act(async () => {
      fireEvent.click(retryButtons()[0]);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(ordinaryPuts).toBe(2);
    expect(puts()[2][1].json.meeting).toEqual({ auto_export: true, intelligence_auto: "every" });
    expect(screen.queryByTestId("settings-save-failure")).toBeNull();
  });

  it("does not show a refusal when a covered old save returns 409 after leave succeeds", async () => {
    let authoritative = settingsWithMeeting("covered-r1", { intelligence_auto: "manual" });
    let rejectOld!: (reason?: unknown) => void;
    const oldSave = new Promise<never>((_, reject) => { rejectOld = reject; });
    apiFetch.mockImplementation((url: string, init?: { method?: string; keepalive?: boolean; json?: Record<string, unknown> }) => {
      if (url === "/api/settings" && init?.method === "PUT") {
        if (init.keepalive) {
          authoritative = settingsWithMeeting("covered-r2", { auto_export: true, intelligence_auto: "every" });
          return Promise.resolve({ settings: authoritative });
        }
        return oldSave;
      }
      if (url === "/api/settings") return Promise.resolve(authoritative);
      return Promise.resolve({});
    });

    render(<SettingsCore scope="meetings" />);
    fireEvent.click(control("Auto export"));
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });
    fireEvent.change(control("Auto-run the summary"), { target: { value: "every" } });
    await act(async () => {
      window.dispatchEvent(new Event("pagehide"));
      await Promise.resolve();
      await Promise.resolve();
      rejectOld(new ApiError(409, "Settings changed in another session"));
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(control("Auto-run the summary")).toHaveValue("every");
    expect(screen.queryByTestId("settings-save-failure")).toBeNull();
  });

  it("keeps a same-value newer draft when its deferred 409 races a leave success", async () => {
    let authoritative = settingsWithMeeting("same-value-r1", { intelligence_auto: "manual" });
    let rejectOld!: (reason?: unknown) => void;
    let rejectNew!: (reason?: unknown) => void;
    let resolveLeave!: (result: { settings: SettingsResponse }) => void;
    const oldSave = new Promise<never>((_, reject) => { rejectOld = reject; });
    const newSave = new Promise<never>((_, reject) => { rejectNew = reject; });
    const leaveSave = new Promise<{ settings: SettingsResponse }>((resolve) => { resolveLeave = resolve; });
    let ordinaryPuts = 0;
    apiFetch.mockImplementation((url: string, init?: { method?: string; keepalive?: boolean; json?: Record<string, unknown> }) => {
      if (url === "/api/settings" && init?.method === "PUT") {
        if (init.keepalive) return leaveSave;
        ordinaryPuts += 1;
        if (ordinaryPuts === 1) return oldSave;
        if (ordinaryPuts === 2) return newSave;
        const patch = (init.json?.meeting ?? {}) as Record<string, unknown>;
        authoritative = {
          ...authoritative,
          _revision: "same-value-r4",
          meeting: { ...(authoritative.meeting ?? {}), ...patch },
        };
        return Promise.resolve({ settings: authoritative });
      }
      if (url === "/api/settings") return Promise.resolve(authoritative);
      return Promise.resolve({});
    });

    render(<SettingsCore scope="meetings" />);
    fireEvent.change(control("Auto-run the summary"), { target: { value: "every" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });
    window.dispatchEvent(new Event("pagehide"));
    // A distinct local write with the same value is still a newer draft.  Its
    // refusal must survive the older leave response's value-equality cleanup.
    fireEvent.change(control("Auto-run the summary"), { target: { value: "every" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });

    authoritative = settingsWithMeeting("same-value-r2", { intelligence_auto: "manual" });
    await act(async () => {
      rejectOld(new ApiError(409, "Settings changed in another session"));
      await Promise.resolve();
      await Promise.resolve();
      rejectNew(new ApiError(409, "Settings changed in another session"));
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(control("Auto-run the summary")).toHaveValue("every");
    expect(retryButtons().length).toBeGreaterThan(0);

    resolveLeave({ settings: settingsWithMeeting("same-value-r3", { intelligence_auto: "every" }) });
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });

    expect(control("Auto-run the summary")).toHaveValue("every");
    expect(retryButtons().length).toBeGreaterThan(0);

    await act(async () => {
      fireEvent.click(retryButtons()[0]);
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(puts()[2][1].json._revision).toBe("same-value-r2");
    expect(control("Auto-run the summary")).toHaveValue("every");
    expect(screen.queryByTestId("settings-save-failure")).toBeNull();
  });

  it("keeps a newer successful job when the older leave response arrives later", async () => {
    let authoritative = settingsWithMeeting("order-r1", { intelligence_auto: "manual" });
    let resolveLeave!: (result: { settings: SettingsResponse }) => void;
    const leaveSave = new Promise<{ settings: SettingsResponse }>((resolve) => { resolveLeave = resolve; });
    apiFetch.mockImplementation((url: string, init?: { method?: string; keepalive?: boolean; json?: Record<string, unknown> }) => {
      if (url === "/api/settings" && init?.method === "PUT") {
        if (init.keepalive) return leaveSave;
        const patch = (init.json?.meeting ?? {}) as Record<string, unknown>;
        authoritative = {
          ...authoritative,
          _revision: "order-r2",
          meeting: { ...(authoritative.meeting ?? {}), ...patch },
        };
        return Promise.resolve({ settings: authoritative });
      }
      if (url === "/api/settings") return Promise.resolve(authoritative);
      return Promise.resolve({});
    });

    render(<SettingsCore scope="meetings" />);
    fireEvent.click(control("Auto export"));
    window.dispatchEvent(new Event("pagehide"));
    fireEvent.change(control("Auto-run the summary"), { target: { value: "every" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });
    expect(control("Auto-run the summary")).toHaveValue("every");

    resolveLeave({ settings: settingsWithMeeting("order-r3", { auto_export: true, intelligence_auto: "manual" }) });
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });

    expect(control("Auto-run the summary")).toHaveValue("every");
  });

  it("reconciles an old 409 before leave success, then keeps a later conflict visible", async () => {
    let authoritative = settingsWithMeeting("before-r1", { intelligence_auto: "manual", export_format: "txt" });
    let rejectOld!: (reason?: unknown) => void;
    let resolveLeave!: (result: { settings: SettingsResponse }) => void;
    const oldSave = new Promise<never>((_, reject) => { rejectOld = reject; });
    const leaveSave = new Promise<{ settings: SettingsResponse }>((resolve) => { resolveLeave = resolve; });
    let ordinaryPuts = 0;
    apiFetch.mockImplementation((url: string, init?: { method?: string; keepalive?: boolean; json?: Record<string, unknown> }) => {
      if (url === "/api/settings" && init?.method === "PUT") {
        if (init.keepalive) return leaveSave;
        ordinaryPuts += 1;
        if (ordinaryPuts === 1) return oldSave;
        authoritative = { ...authoritative, _revision: "before-r4" };
        return Promise.reject(new ApiError(409, "Settings changed in another session"));
      }
      if (url === "/api/settings") return Promise.resolve(authoritative);
      return Promise.resolve({});
    });

    render(<SettingsCore scope="meetings" />);
    fireEvent.click(control("Auto export"));
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });
    fireEvent.change(control("Auto-run the summary"), { target: { value: "every" } });
    window.dispatchEvent(new Event("pagehide"));
    await act(async () => {
      rejectOld(new ApiError(409, "Settings changed in another session"));
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(retryButtons().length).toBeGreaterThan(0);

    authoritative = settingsWithMeeting("before-r3", { auto_export: true, intelligence_auto: "every", export_format: "txt" });
    resolveLeave({ settings: authoritative });
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    expect(screen.queryByTestId("settings-save-failure")).toBeNull();
    expect(control("Auto-run the summary")).toHaveValue("every");

    fireEvent.change(control("Export format"), { target: { value: "json" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });
    expect(control("Export format")).toHaveValue("json");
    expect(retryButtons().length).toBeGreaterThan(0);
  });

  it("does not reintroduce an old leave value when a newer same-path save succeeds", async () => {
    let authoritative = settingsWithMeeting("failure-order-r1", { auto_export: false });
    let rejectLeave!: (reason?: unknown) => void;
    const leaveSave = new Promise<never>((_, reject) => { rejectLeave = reject; });
    apiFetch.mockImplementation((url: string, init?: { method?: string; keepalive?: boolean; json?: Record<string, unknown> }) => {
      if (url === "/api/settings" && init?.method === "PUT") {
        if (init.keepalive) return leaveSave;
        const patch = (init.json?.meeting ?? {}) as Record<string, unknown>;
        authoritative = {
          ...authoritative,
          _revision: "failure-order-r2",
          meeting: { ...(authoritative.meeting ?? {}), ...patch },
        };
        return Promise.resolve({ settings: authoritative });
      }
      if (url === "/api/settings") return Promise.resolve(authoritative);
      return Promise.resolve({});
    });

    render(<SettingsCore scope="meetings" />);
    fireEvent.click(control("Auto export"));
    window.dispatchEvent(new Event("pagehide"));
    fireEvent.click(control("Auto export"));
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });
    expect(control("Auto export")).not.toBeChecked();

    rejectLeave(new ApiError(503, "Leave save failed"));
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    expect(control("Auto export")).not.toBeChecked();
    expect(screen.queryByTestId("settings-save-failure")).toBeNull();
  });
});

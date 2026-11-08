// One writer of /api/settings (2026-11-08): the You fields write through the
// Settings window's one writer. Before, the You fields had their own revision:
// an alias save moved the hub's revision, and the next Language save carried
// the old one, got 409, and the hub kept "auto" while the face said "en".
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SettingsCore } from "../../SettingsCore";
import type { SettingsResponse } from "../../core-types";
import hubWire from "../../../../desk/__tests__/fixtures/settings-wire/hub.json";
import { fakeSettingsHub, STALE } from "./fakeSettingsHub";

const apiFetch = vi.hoisted(() => vi.fn());
const ApiError = vi.hoisted(() => class TestApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(status: number, message: string, payload?: unknown) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
});
const initial = vi.hoisted<SettingsResponse>(() => ({
  _revision: "r1",
  owner: { name: "Karol", aliases: [] },
  model: { language: "auto" },
} as unknown as SettingsResponse));

vi.mock("../../../../lib/api", () => ({
  apiFetch,
  ApiError,
  readableError: (cause: unknown) => cause instanceof Error ? cause.message : "Request failed",
}));
vi.mock("../../../pageSupport", async () => {
  const React = await import("react");
  const noop = vi.fn();
  return {
    useResource: (url: string) => {
      const [data, setData] = React.useState(
        url === "/api/settings" ? initial : url === "/api/settings/hub" ? hubWire : { control_mode: "yolo", precedence: [] },
      );
      return { data, setData, loading: false, error: "", setError: noop, reload: noop };
    },
  };
});
vi.mock("../../core-hooks", () => ({
  useCoreWings: () => ({ view: "settings", setView: vi.fn() }),
}));
vi.mock("../../ContextualAssignment", () => ({ ContextualAssignment: () => null }));

const fakeHub = () => fakeSettingsHub(apiFetch, ApiError, initial as unknown as Record<string, unknown>);

const puts = () => apiFetch.mock.calls.filter(([url, init]) => url === "/api/settings" && init?.method === "PUT");

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
});
afterEach(() => vi.useRealTimers());

async function addAlias(name: string) {
  const alias = within(screen.getByTestId("settings-owner-aliases")).getByLabelText("Also called");
  fireEvent.change(alias, { target: { value: name } });
  fireEvent.keyDown(alias, { key: "Enter" });
  await act(async () => { await vi.advanceTimersByTimeAsync(700); });
}

describe("one writer of /api/settings", () => {
  it("an alias save, then a Language save: both land", async () => {
    const hub = fakeHub();
    const view = render(<SettingsCore scope="you" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    await addAlias("Architect");
    expect((hub.doc.owner as { aliases: string[] }).aliases).toEqual(["Architect"]);

    view.rerender(<SettingsCore scope="speak" />);
    fireEvent.change(screen.getByLabelText("Language"), { target: { value: "en" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(700); });

    expect((hub.doc.model as { language: string }).language).toBe("en");
    expect((hub.doc.owner as { aliases: string[] }).aliases).toEqual(["Architect"]);
    expect(puts().every(([, init]) => init.json._revision !== undefined)).toBe(true);
    expect(screen.queryByTestId("settings-save-failure")).toBeNull();
  });

  it("a change made elsewhere still says the hub's word on You, and Retry lands", async () => {
    const hub = fakeHub();
    render(<SettingsCore scope="you" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    hub.moveElsewhere();
    await addAlias("Architect");

    expect((hub.doc.owner as { aliases: string[] }).aliases).toEqual([]);
    const status = screen.getByTestId("settings-status");
    expect(status.textContent).toContain("Not saved");
    expect(status.textContent).toContain(STALE);
    expect(screen.getByTestId("settings-owner-aliases").getAttribute("data-save-state")).toBe("Not saved");

    fireEvent.click(within(status).getByRole("button", { name: "Retry" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    expect((hub.doc.owner as { aliases: string[] }).aliases).toEqual(["Architect"]);
  });
});

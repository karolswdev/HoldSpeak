import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), openPullout: vi.fn() }));

vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));
vi.mock("../../store", () => ({
  useDesk: Object.assign(() => undefined, { getState: () => ({ openPullout: mocks.openPullout }) }),
}));

import { SetupFace, type SetupInventory } from "../SetupFace";

const inventory = (overrides: Partial<SetupInventory> = {}): SetupInventory => ({
  owner_name: "Astra",
  rows: [
    { id: "speech", kind: "speech", label: "Speech", detail: "Whisper runs on this Mac", state: "found", action: "speech", verb: "Set up speech" },
    { id: "connection:github", kind: "account", label: "GitHub", detail: "owner", state: "found", action: "connection", verb: "Use it" },
  ],
  people: [],
  suggestions: [{ key: "theo-lindqvist", name: "Theo Lindqvist", relationship_kind: "direct_report" }],
  ...overrides,
});

beforeEach(() => {
  mocks.openPullout.mockReset();
  mocks.apiFetch.mockReset().mockImplementation(async (path: string, init: { method?: string; json?: unknown } = {}) => {
    if (path === "/api/settings") return { owner: { name: "Astra", aliases: [] }, _revision: "1" };
    if (path === "/api/setup/lan") return { rows: [] };
    if (path === "/api/setup/use") return { success: true, result: { state: "ready" } };
    if (path === "/api/setup/people") return { relationships: [{ id: "p2", display_name: "Theo Lindqvist", relationship_kind: "direct_report" }] };
    return {};
  });
});

describe("Setup ST3–ST5", () => {
  it("uses a found row and folds it into Works", async () => {
    render(<SetupFace initial={inventory({ rows: [inventory().rows[0]] })} />);

    fireEvent.click(screen.getByRole("button", { name: "Set up speech" }));
    await waitFor(() => expect(screen.getByText("Works")).toBeTruthy());
    expect(screen.getByText("Speech")).toBeTruthy();
    expect(screen.queryByTestId("setup-found")).toBeNull();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/setup/use", expect.objectContaining({
      method: "POST", json: expect.objectContaining({ id: "speech" }),
    }));
  });

  it("uses every found row in display order", async () => {
    render(<SetupFace initial={inventory()} />);

    fireEvent.click(screen.getByRole("button", { name: "Use everything found" }));
    await waitFor(() => expect(screen.getByText("Ready, Astra.")).toBeTruthy());
    const presses = mocks.apiFetch.mock.calls
      .filter(([path]) => path === "/api/setup/use")
      .map(([, init]) => (init as { json: { id: string } }).json.id);
    expect(presses).toEqual(["speech", "connection:github"]);
    expect(screen.queryByRole("button", { name: "Continue later" })).toBeNull();
    expect(screen.getByRole("button", { name: "Open my desk" })).toBeTruthy();
  });

  it("is ready for speech and the desk while an optional account is absent", async () => {
    render(<SetupFace initial={inventory({
      owner_name: "Astra",
      rows: [
        { id: "speech", kind: "speech", label: "Speech", state: "works", action: null },
        { id: "connection:jira:not-found", kind: "account", label: "Jira", detail: "acli is not installed", state: "does_not_work", reason: "Install acli and sign in to use Jira" },
      ],
    })} />);

    expect(screen.getByText("Ready, Astra.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Say one sentence" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open my desk" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Continue later" })).toBeNull();
  });

  it("adds comma-separated direct reports and keeps calendar suggestions visible", async () => {
    render(<SetupFace initial={inventory({ rows: [] })} />);

    expect(screen.getByText(/From your calendar: Theo Lindqvist/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Your people"), { target: { value: "Theo Lindqvist, Ada Lovelace" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));

    await waitFor(() => expect(screen.getByText("People added.")).toBeTruthy());
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/setup/people", expect.objectContaining({
      method: "POST", json: { names: "Theo Lindqvist, Ada Lovelace" },
    }));
  });

  it("keeps an unfinished producer action Working instead of claiming Works", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/settings") return { owner: { name: "Astra", aliases: [] }, _revision: "1" };
      if (path === "/api/setup/lan") return { rows: [] };
      if (path === "/api/setup/use") return { success: true, result: { state: "downloading" } };
      if (path === "/api/setup/found") return { rows: [{ ...inventory().rows[0], state: "works", action: null }] };
      return {};
    });
    render(<SetupFace initial={inventory({ rows: [inventory().rows[0]] })} />);

    fireEvent.click(screen.getByRole("button", { name: "Set up speech" }));
    await waitFor(() => expect(screen.getByTestId("setup-found").textContent).toContain("Working"));
    expect(screen.getByTestId("setup-found").textContent).not.toContain("Works");
  });

  it("does not claim Works for an unrecognised successful HTTP answer", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/settings") return { owner: { name: "Astra", aliases: [] }, _revision: "1" };
      if (path === "/api/setup/lan") return { rows: [] };
      if (path === "/api/setup/use") return { success: true, result: { state: "unknown" } };
      return {};
    });
    render(<SetupFace initial={inventory({ rows: [inventory().rows[0]] })} />);
    fireEvent.click(screen.getByRole("button", { name: "Set up speech" }));
    await waitFor(() => expect(screen.getByText(/Not checked. Try again./)).toBeTruthy());
    expect(screen.queryByText("Works")).toBeNull();
    expect(screen.getByRole("button", { name: "Set up speech" })).toBeTruthy();
  });

  it("renders a degraded producer answer as Does not work", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/settings") return { owner: { name: "Astra", aliases: [] }, _revision: "1" };
      if (path === "/api/setup/lan") return { rows: [] };
      if (path === "/api/setup/use") return {
        success: true,
        result: { entry: { connections: [{ state: "degraded", error_detail: "Account probe failed" }] } },
      };
      return {};
    });
    render(<SetupFace initial={inventory({ rows: [inventory().rows[1]] })} />);

    fireEvent.click(screen.getByRole("button", { name: "Use it" }));
    await waitFor(() => expect(screen.getByText(/Not found/)).toBeTruthy());
    fireEvent.click(screen.getByText(/Not found/));
    await waitFor(() => expect(screen.getByText("Does not work")).toBeTruthy());
    expect(screen.getByText(/Account probe failed/)).toBeTruthy();
    expect(screen.getByText(/Not found/)).toBeTruthy();
  });

  it("keeps a LAN answer when a later row update lands", async () => {
    let releaseLan: ((value: unknown) => void) | undefined;
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/settings") return { owner: { name: "Astra", aliases: [] }, _revision: "1" };
      if (path === "/api/setup/lan") return await new Promise((resolve) => { releaseLan = resolve; });
      if (path === "/api/setup/use") return { success: true, result: { state: "ready" } };
      return {};
    });
    render(<SetupFace initial={inventory({ rows: [inventory().rows[0]] })} />);
    fireEvent.click(screen.getByRole("button", { name: "Set up speech" }));
    await waitFor(() => expect(screen.getByText("Works")).toBeTruthy());
    releaseLan?.({ rows: [{ id: "qwen", name: "qwen3.8-27b", host: "192.168.1.43", baseUrl: "http://192.168.1.43:8080" }] });
    await waitFor(() => expect(screen.getByText("qwen3.8-27b")).toBeTruthy());
  });
});


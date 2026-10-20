import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  openPullout: vi.fn(),
  take: {
    state: "idle",
    take: null,
    failure: null,
    level: 0,
    keeping: false,
    message: "",
    playing: false,
    supported: true,
    kept: false,
    canPlay: false,
    begin: vi.fn(), stop: vi.fn(), play: vi.fn(), again: vi.fn(), keep: vi.fn(), finish: vi.fn(), leave: vi.fn(),
  },
}));

vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));
vi.mock("../../store", () => ({
  useDesk: Object.assign(() => undefined, { getState: () => ({ openPullout: mocks.openPullout }) }),
}));
vi.mock("../useFirstTake", () => ({ useFirstTake: () => mocks.take }));

import { SetupFace, type SetupInventory } from "../SetupFace";
import LAN_USE from "../../__tests__/fixtures/setup-st3-st5/lan-use.json";

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
  Object.assign(mocks.take, {
    state: "idle", take: null, failure: null, level: 0, keeping: false, message: "", playing: false,
    supported: true, kept: false, canPlay: false,
  });
  for (const method of ["begin", "stop", "play", "again", "keep", "finish", "leave"] as const) mocks.take[method].mockReset();
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

  it("uses the recorded LAN producer answer as a ready engine", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/settings") return { owner: { name: "Astra", aliases: [] }, _revision: "1" };
      if (path === "/api/setup/lan") return { rows: [] };
      if (path === "/api/setup/use") return LAN_USE;
      return {};
    });
    render(<SetupFace initial={inventory({
      rows: [
        { id: "speech", kind: "speech", label: "Speech", state: "works", action: null },
        {
          // Setup's LAN consumer prefixes the opaque discovery id once.
          id: "lan:ef47e34f9cba6a6e7c21", kind: "engine", label: "stub-qwen",
          detail: "127.0.0.1", state: "found", action: "lan", verb: "Use it",
          payload: { base_url: "http://127.0.0.1:8099", model: "qwen3.8-27b" },
        },
      ],
    })} />);

    fireEvent.click(screen.getByRole("button", { name: "Use everything found" }));
    await waitFor(() => expect(screen.getByText("Ready, Astra.")).toBeTruthy());
    expect(screen.getByText("stub-qwen")).toBeTruthy();
    const lanRow = screen.getByText("stub-qwen").closest("li");
    expect(lanRow).toBeTruthy();
    expect(within(lanRow as HTMLElement).getByRole("status", { name: "Works" })).toBeTruthy();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/setup/use", expect.objectContaining({
      method: "POST", json: expect.objectContaining({ id: "lan:ef47e34f9cba6a6e7c21" }),
    }));
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
    expect(screen.getByTestId("setup-found").textContent).not.toContain("Works");
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

  it("keeps a Stop control visible while the microphone listens", () => {
    mocks.take.state = "listening";
    render(<SetupFace initial={inventory({ rows: [{ id: "speech", kind: "speech", label: "Speech", state: "works" }] })} />);

    expect(screen.getByRole("button", { name: "Stop listening" })).toBeTruthy();
    expect(screen.getByRole("status", { name: "LISTENING" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Listening" })).toBeNull();
  });

  it("shows the named take failure and its Again recovery", () => {
    mocks.take.state = "failed";
    mocks.take.failure = "no_microphone";
    render(<SetupFace initial={inventory({ rows: [{ id: "speech", kind: "speech", label: "Speech", state: "works" }] })} />);

    expect(screen.getByTestId("setup-take-failure").textContent).toContain("NO DEVICE FOUND");
    expect(screen.getByRole("button", { name: "Check the microphone" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Again" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open my desk" })).toBeTruthy();
  });
});


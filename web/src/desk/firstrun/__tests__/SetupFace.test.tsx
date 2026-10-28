import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { DictationFailure } from "../../../lib/dictationRecovery";
import { DESK_APPLICATION_ALIASES } from "../../applications";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  openPullout: vi.fn(),
  take: {
    state: "idle",
    take: null,
    failure: null as DictationFailure | null,
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
import MICROPHONE from "../../__tests__/fixtures/setup-st3-st5/microphone.json";

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
  it("waits for the owner read before accepting a name, then keeps the typed name", async () => {
    let read!: (value: unknown) => void;
    const original = mocks.apiFetch.getMockImplementation()!;
    mocks.apiFetch.mockImplementation((path: string, init: { method?: string; json?: unknown } = {}) =>
      path === "/api/settings" && !init.method
        ? new Promise((resolve) => { read = resolve; })
        : original(path, init));
    render(<SetupFace initial={inventory({ owner_name: "", rows: [{ ...inventory().rows[0], state: "works" }] })} />);
    const name = screen.getByRole("textbox", { name: "Your name" });
    expect(name).toBeDisabled();
    await act(async () => { read({ owner: { name: "", aliases: [] }, _revision: "1" }); });
    expect(name).toBeEnabled();
    fireEvent.change(name, { target: { value: "Fence owner" } });
    fireEvent.blur(name);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/settings", expect.objectContaining({
      method: "PUT", json: expect.objectContaining({ owner: { name: "Fence owner", aliases: [] } }),
    })));
    expect(screen.getByText("Ready, Fence owner.")).toBeTruthy();
  });
  it("opens the retired readiness alias directly in the one Setup home", () => {
    expect(DESK_APPLICATION_ALIASES["read-runtime-docs"]).toEqual({ target: "configure-setup", scope: undefined });
  });
  it("uses a found row and folds it into Works", async () => {
    render(<SetupFace initial={inventory({ rows: [inventory().rows[0]] })} />);

    fireEvent.click(screen.getByRole("button", { name: "Set up speech" }));
    await waitFor(() => expect(screen.getByTestId("setup-row-state").textContent).toBe("Ready"));
    expect(screen.getByText("Speech")).toBeTruthy();
    // Window grammar: a ready row has no verb left in the status bar.
    expect(screen.queryByTestId("setup-row-verb")).toBeNull();
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

  it("shows each agent's binding facts and stops one agent through the admitted route", async () => {
    const partial = {
      success: false,
      result: {
        state: "degraded",
        results: [
          { agent: "claude", ok: false, code: "mcp_name_taken" },
          { agent: "codex", ok: true },
        ],
      },
    };
    const afterUse = {
      rows: [{
        id: "agents", kind: "agents", label: "Agents", detail: "Claude Code, Codex", state: "found",
        action: "agents", verb: "Let my agents use HoldSpeak",
        payload: {
          agents: ["claude"],
          bindings: [
            { id: "claude", label: "Claude Code", ready: false, facts: { hooks: "installed", tools: "foreign", skill: "missing" }, can_stop: true },
            { id: "codex", label: "Codex", ready: true, facts: { hooks: "installed", tools: "installed", skill: "installed" }, can_stop: true },
          ],
        },
      }],
    } satisfies SetupInventory;
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/settings") return { owner: { name: "Astra", aliases: [] }, _revision: "1" };
      if (path === "/api/setup/lan") return { rows: [] };
      if (path === "/api/onboarding/agents/use") return partial;
      if (path === "/api/onboarding/agents/stop") return { stopped: { agent: "codex" } };
      if (path === "/api/setup/found") return afterUse;
      return {};
    });
    render(<SetupFace initial={afterUse} />);

    fireEvent.click(screen.getByRole("button", { name: "Let my agents use HoldSpeak" }));
    await waitFor(() => expect(screen.getByText(/Claude Code: already has another MCP setup/)).toBeTruthy());
    expect(screen.getByTestId("setup-row-state").textContent).toBe("Failed");
    expect(screen.getByText("Codex · uses your desk")).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "Stop using my desk" })).toHaveLength(2);

    fireEvent.click(screen.getByText("Codex · uses your desk").closest(".setup-agent-binding")!.querySelector("button")!);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/onboarding/agents/stop", expect.objectContaining({
      method: "POST", json: { agent: "codex" },
    })));
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
    const lanRow = screen.getByText("stub-qwen").closest("[data-testid=setup-row]");
    expect(lanRow).toBeTruthy();
    expect(within(lanRow as HTMLElement).getByTestId("setup-row-state").textContent).toBe("Ready");
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
    expect(screen.getByTestId("setup-found").textContent).not.toContain("Ready");
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
    expect(screen.getByTestId("setup-found").textContent).toContain("Not set up");
    expect(screen.getByTestId("setup-found").textContent).not.toContain("Ready");
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
    // Window grammar: the pressed row failed (a dot and a word) and its
    // reason reads in the row's Detail; the verb stays to try again.
    await waitFor(() => expect(screen.getByTestId("setup-row-state").textContent).toBe("Failed"));
    expect(screen.getByText(/Account probe failed/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Use it" })).toBeTruthy();
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
    await waitFor(() => expect(screen.getAllByTestId("setup-row-state")[0].textContent).toBe("Ready"));
    releaseLan?.({ rows: [{ id: "qwen", name: "qwen3.8-27b", host: "192.168.1.43", baseUrl: "http://192.168.1.43:8080" }] });
    await waitFor(() => expect(screen.getByText("qwen3.8-27b")).toBeTruthy());
  });

  it("keeps a Stop control visible while the microphone listens", () => {
    mocks.take.state = "listening";
    render(<SetupFace initial={inventory({ rows: [{ id: "speech", kind: "speech", label: "Speech", state: "works" }] })} />);

    expect(screen.getByRole("button", { name: "Stop listening" })).toBeTruthy();
    expect(screen.getByRole("status", { name: "Listening" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Listening" })).toBeNull();
  });

  it("shows the named take failure and reads the real microphone check in place", async () => {
    const original = mocks.apiFetch.getMockImplementation()!;
    mocks.apiFetch.mockImplementation((path, init) => path === "/api/setup/status"
      ? Promise.resolve(MICROPHONE) : original(path, init));
    mocks.take.state = "failed";
    mocks.take.failure = "no_microphone";
    render(<SetupFace initial={inventory({ rows: [{ id: "speech", kind: "speech", label: "Speech", state: "works" }] })} />);

    expect(screen.getByTestId("setup-take-failure").textContent).toContain("Browser gave no device");
    expect(screen.getByRole("button", { name: "Check the microphone" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Again" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open my desk" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Check the microphone" }));
    expect(await screen.findByText(MICROPHONE.sections[0].detail)).toBeTruthy();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/setup/status");
  });
});


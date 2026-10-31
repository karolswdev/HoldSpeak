import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { TerminalsCore } from "../TerminalsCore";
import { TerminalWindows } from "../TerminalWindows";
import { refreshTerminalInventory, TERMINALS_WINDOW_ID, terminalInventorySnapshot } from "../windows";
import fixture from "./fixtures/sessions.recorded.json";
import connectedFixture from "./fixtures/connected.recorded.json";
import * as api from "../../../lib/api";
import { fromWireDecision } from "../../api";
import { useDesk } from "../../store";
import { queueWorkspaceLaunch, selectWorkspaceFace, setWorkspaceSelection, workspaceSelectionSnapshot } from "../workspaceSelection";

const runtimeBus = vi.hoisted(() => ({
  handlers: new Map<string, Set<(frame: { type: string; data: unknown }) => void>>(),
}));

const terminalHarness = vi.hoisted(() => {
  const listeners = new Set<() => void>();
  let state: Record<string, unknown>;
  const enableTyping = vi.fn(async () => {
    state = { ...state, canType: true };
    listeners.forEach((listener) => listener());
    return true;
  });
  const disableTyping = vi.fn(async () => {
    state = { ...state, canType: false };
    listeners.forEach((listener) => listener());
  });
  const createState = () => ({
    status: "live",
    raw: "$ ",
    lines: ["$ "],
    pane: null,
    changedAt: null,
    canType: false,
    busy: false,
    error: null,
    receipt: null,
    sequence: 0,
    hash: null,
    focused: false,
    visible: true,
    start: vi.fn(),
    stop: vi.fn(),
    setActivity: vi.fn(),
    enableTyping,
    disableTyping,
    sendData: vi.fn(() => false),
    sendText: vi.fn(async () => true),
    sendKeys: vi.fn(async () => true),
  });
  state = createState();
  return {
    store: {
      subscribe: (listener: () => void) => {
        listeners.add(listener);
        return () => listeners.delete(listener);
      },
      getState: () => state,
    },
    enableTyping,
    reset() {
      enableTyping.mockClear();
      disableTyping.mockClear();
      state = createState();
      listeners.clear();
    },
    setSnapshot(next: Record<string, unknown>) {
      state = { ...state, ...next };
      listeners.forEach((listener) => listener());
    },
  };
});

vi.mock("../../../runtime/RuntimeBus", () => {
  const value = {
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: (frame: { type: string; data: unknown }) => void) => {
      const handlers = runtimeBus.handlers.get(type) ?? new Set();
      handlers.add(handler);
      runtimeBus.handlers.set(type, handlers);
      return () => handlers.delete(handler);
    },
  };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

vi.mock("../terminalSession", () => ({
  createTerminalSession: () => terminalHarness.store,
}));

vi.mock("../../components/DeskWindow", () => ({
  DeskWindowFrame: ({ id, className, children }: { id: string; className?: string; children: ReactNode }) => (
    <section id={id} className={className}>{children}</section>
  ),
}));

vi.mock("../../components/window/windowRegistry", () => ({
  useFrontWindowId: () => null,
}));

vi.mock("../useCompactViewport", () => ({
  useCompactViewport: () => false,
}));

vi.mock("../../surface", async () => {
  const actual = await vi.importActual<typeof import("../../surface")>("../../surface");
  return {
    ...actual,
    PaneWell: ({ focusSignal, onFocus }: { focusSignal?: number; onFocus?: () => void }) => (
      <div data-testid="mock-terminal-pane" data-focus-signal={focusSignal ?? ""} onFocus={onFocus} />
    ),
  };
});

vi.mock("../../components/MicButton", () => ({ MicButton: () => <span data-testid="mic" /> }));

const sessions = fixture.sessions;

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    terminalWindows: [],
    drafts: {},
    panelDepth: {},
    panelOrder: [],
    panelMin: [],
    windowsById: {},
  });
  runtimeBus.handlers.clear();
  terminalHarness.reset();
  vi.restoreAllMocks();
  setWorkspaceSelection({ projectId: null, sessionId: null, face: "sessions", pendingLaunch: null, pendingKind: null, pendingProjectId: null, pendingHandoffs: [] });
});

function serveInventory() {
  vi.spyOn(api, "apiFetch").mockResolvedValue({ status: "ok", sessions } as never);
}

describe("Terminals inventory", () => {
  it("searches recorded metadata and opens the stable descriptor without using a pane selector", async () => {
    serveInventory();
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${sessions[0].id}`);

    fireEvent.change(screen.getByRole("textbox", { name: "Find a session or folder" }), { target: { value: "scratch" } });
    expect(screen.queryByTestId(`terminal-row-${sessions[0].id}`)).toBeNull();
    const row = screen.getByTestId(`terminal-row-${sessions[1].id}`);
    expect(row).toHaveClass("kit-listrow");
    expect(screen.getByTitle("/work/scratch")).toBeTruthy();
    fireEvent.click(screen.getByTestId(`terminal-open-${sessions[1].id}`));
    expect(useDesk.getState().terminalWindows).toEqual([{ id: sessions[1].id, origin: null }]);
    expect(workspaceSelectionSnapshot().sessionId).toBe(sessions[1].id);
  });

  it("creates a named shell through the audited factory payload and opens the discovered descriptor", async () => {
    const apiRequest = vi.spyOn(api, "apiRequest");
    apiRequest
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "spawned", pane_id: "%9" }), { status: 200 }))
      .mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    let reads = 0;
    vi.spyOn(api, "apiFetch").mockImplementation(async () => {
      reads += 1;
      return { status: "ok", sessions: reads > 1 ? [{ ...sessions[1], pane_id: "%9", session: "new-shell", label: "new-shell:0.0" }] : sessions } as never;
    });
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${sessions[0].id}`);
    fireEvent.click(screen.getByTestId("terminal-new"));
    fireEvent.change(screen.getByRole("textbox", { name: "Shell name" }), { target: { value: "new-shell" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Folder (optional)" }), { target: { value: "/work/scratch" } });
    fireEvent.click(screen.getByRole("button", { name: "Create shell" }));

    await waitFor(() => expect(useDesk.getState().terminalWindows).toEqual([{ id: sessions[1].id, origin: null }]));
    expect(apiRequest).toHaveBeenCalledWith("/api/coders/factory/spawn", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ name: "new-shell", cwd: "/work/scratch" }),
    }));
  });

  it("refreshes from the producer and keeps an empty response explicit", async () => {
    vi.spyOn(api, "apiFetch").mockResolvedValue({ status: "ok", sessions: [] } as never);
    await refreshTerminalInventory();
    render(<TerminalsCore />);
    expect(await screen.findByText("No terminal sessions")).toBeTruthy();
    expect(screen.getByTestId("terminal-new")).toBeTruthy();
    expect(screen.getByTestId("terminal-start-agent")).toBeTruthy();
  });

  it("follows coder and agent producers from one inventory owner, not window-only frames", async () => {
    vi.spyOn(api, "apiFetch").mockResolvedValue({ status: "ok", sessions } as never);
    await refreshTerminalInventory();
    vi.mocked(api.apiFetch).mockClear();
    useDesk.setState({
      windowsById: {
        [TERMINALS_WINDOW_ID]: {
          id: TERMINALS_WINDOW_ID,
          kind: "surface",
          applicationKey: "open-terminals",
          scope: null,
          persistence: "workspace",
        },
      },
    });

    render(<TerminalWindows />);
    act(() => {
      for (const handler of runtimeBus.handlers.get("intel_status") ?? []) {
        handler({ type: "intel_status", data: { scope: "coder" } });
      }
    });
    await waitFor(() => expect(api.apiFetch).toHaveBeenCalledTimes(1));

    act(() => {
      for (const handler of runtimeBus.handlers.get("desk_changed") ?? []) {
        handler({ type: "desk_changed", data: { kind: "windows", id: TERMINALS_WINDOW_ID } });
      }
    });
    await new Promise((resolve) => setTimeout(resolve, 350));
    expect(api.apiFetch).toHaveBeenCalledTimes(1);

    act(() => {
      for (const handler of runtimeBus.handlers.get("desk_changed") ?? []) {
        handler({ type: "desk_changed", data: { kind: "agent", id: "agent-1" } });
      }
    });
    await waitFor(() => expect(api.apiFetch).toHaveBeenCalledTimes(2));
  });

  it("keeps the last descriptor projection visible when a refresh fails", async () => {
    vi.spyOn(api, "apiFetch").mockResolvedValueOnce({ status: "ok", sessions } as never);
    await refreshTerminalInventory();
    vi.mocked(api.apiFetch).mockRejectedValueOnce(new Error("hub offline"));
    await refreshTerminalInventory();

    expect(terminalInventorySnapshot()).toMatchObject({
      status: "error",
      detail: "hub offline",
      sessions,
    });
  });

  it("focuses on Type before the arm receipt and does not steal focus again on ACK", async () => {
    serveInventory();
    await refreshTerminalInventory();
    useDesk.setState({
      terminalWindows: [{ id: sessions[0].id, origin: null }],
      panelDepth: { [`terminal:${sessions[0].id}`]: 1 },
      panelOrder: [`terminal:${sessions[0].id}`],
    });
    let resolveArm: ((value: boolean) => void) | undefined;
    terminalHarness.enableTyping.mockImplementationOnce(() => new Promise<boolean>((resolve) => {
      resolveArm = (value) => {
        if (value) terminalHarness.setSnapshot({ canType: true });
        resolve(value);
      };
    }));

    render(<TerminalWindows />);
    const enable = await screen.findByTestId("terminal-enable-typing");
    fireEvent.click(enable);
    expect(enable).toBeDisabled();
    expect(enable).toHaveAttribute("aria-busy", "true");
    expect(terminalHarness.enableTyping).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("mock-terminal-pane")).toHaveAttribute("data-focus-signal", "1");

    resolveArm?.(true);
    await waitFor(() => expect(enable).toHaveTextContent("View only"));
    const pane = screen.getByTestId("mock-terminal-pane");
    expect(pane).toHaveAttribute("data-focus-signal", "1");
  });

  it("keeps a Message draft through hide, reopen and a failed send", async () => {
    serveInventory();
    await refreshTerminalInventory();
    useDesk.setState({ terminalWindows: [{ id: sessions[0].id, origin: null }] });
    render(<TerminalWindows />);

    const message = await screen.findByTestId("terminal-message-toggle");
    expect(screen.queryByTestId("terminal-composer")).toBeNull();
    fireEvent.click(message);
    const input = screen.getByRole("textbox", { name: "Message" });
    fireEvent.change(input, { target: { value: "keep this" } });
    fireEvent.click(message);
    expect(screen.queryByTestId("terminal-composer")).toBeNull();
    expect(screen.getByTestId("mock-terminal-pane")).toHaveAttribute("data-focus-signal", "1");
    expect(useDesk.getState().drafts[`terminal:${sessions[0].id}`]).toBe("keep this");

    fireEvent.click(message);
    expect(screen.getByRole("textbox", { name: "Message" })).toHaveValue("keep this");
    fireEvent.click(screen.getByTestId("terminal-find"));
    fireEvent.click(screen.getByTestId("terminal-find"));
    expect(screen.getByTestId("mock-terminal-pane")).toHaveAttribute("data-focus-signal", "2");
    const sendText = vi.fn(async () => false);
    act(() => terminalHarness.setSnapshot({ canType: true, sendText }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Send" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(sendText).toHaveBeenCalledWith("keep this", true));
    expect(screen.getByRole("textbox", { name: "Message" })).toHaveValue("keep this");
  });

  it("opens the workspace app at the exact terminal selected by its Workspace door", async () => {
    serveInventory();
    await refreshTerminalInventory();
    useDesk.setState({ terminalWindows: [{ id: sessions[0].id, origin: null }] });
    render(<TerminalWindows />);

    fireEvent.click(await screen.findByTestId("terminal-workspace"));
    expect(workspaceSelectionSnapshot().sessionId).toBe(sessions[0].id);
    expect(workspaceSelectionSnapshot().face).toBe("files");
  });

  it("opens recorded connected workspace files and shows app bytes before editing", async () => {
    const connectedSessions = connectedFixture.inventory.sessions;
    vi.spyOn(api, "apiFetch").mockImplementation(async (path) => {
      const url = String(path);
      if (url === "/api/delivery/terminal/sessions") return connectedFixture.inventory as never;
      if (url === "/api/projects") return connectedFixture.projects as never;
      if (url.includes("/tree")) return connectedFixture.repository.tree as never;
      if (url.includes("/file/app.txt")) return connectedFixture.repository.file as never;
      if (url.includes("/status")) return connectedFixture.repository.status as never;
      if (url.includes("/diff")) return connectedFixture.repository.diff as never;
      return { status: "ok" } as never;
    });
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${connectedSessions[0].id}`);
    fireEvent.click(screen.getByTestId(`terminal-open-${connectedSessions[0].id}`));
    act(() => selectWorkspaceFace("files"));
    fireEvent.click(await screen.findByRole("row", { name: "app.txt" }));
    expect(await screen.findByTestId("repo-file-content")).toHaveTextContent("review worktree");
    expect(screen.queryByTestId("terminal-file-editor")).toBeTruthy();
    expect(screen.queryByTestId("terminal-file-edit")).toBeTruthy();
  });

  it("leads with the selected job brief and one next action", async () => {
    const connectedSessions = connectedFixture.inventory.sessions;
    vi.spyOn(api, "apiFetch").mockImplementation(async (path) => {
      const url = String(path);
      if (url === "/api/delivery/terminal/sessions") return connectedFixture.inventory as never;
      if (url === "/api/projects") return connectedFixture.projects as never;
      if (url.includes("/notes/note-connected-brief")) return connectedFixture.notes["note-connected-brief"] as never;
      return { status: "ok" } as never;
    });
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${connectedSessions[0].id}`);
    fireEvent.click(screen.getByTestId(`terminal-open-${connectedSessions[0].id}`));

    const overview = await screen.findByTestId("terminal-job-overview");
    expect(overview).toHaveTextContent("Build the connected workspace");
    expect(overview).toHaveTextContent("Workspace fixture");
    expect(overview).toHaveTextContent("Live");
    expect(within(overview).getByRole("button", { name: "Open terminal" })).toBeTruthy();
  });

  it("prepares a real file scope for Start agent without dispatching", async () => {
    const connectedSessions = connectedFixture.inventory.sessions;
    const hand = vi.spyOn(api, "apiFetch").mockImplementation(async (path) => {
      const url = String(path);
      if (url === "/api/delivery/terminal/sessions") return connectedFixture.inventory as never;
      if (url === "/api/projects") return connectedFixture.projects as never;
      if (url.includes("/tree")) return connectedFixture.repository.tree as never;
      if (url.includes("/file/app.txt")) return connectedFixture.repository.file as never;
      return { status: "ok" } as never;
    });
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${connectedSessions[0].id}`);
    fireEvent.click(screen.getByTestId(`terminal-open-${connectedSessions[0].id}`));
    act(() => selectWorkspaceFace("files"));
    fireEvent.click(await screen.findByRole("row", { name: "app.txt" }));
    fireEvent.click(await screen.findByTestId("terminal-file-prepare-agent"));

    expect(await screen.findByTestId("conductor-start-context")).toBeTruthy();
    expect(screen.getByTestId("conductor-start-source")).toHaveTextContent("Workspace fixture · app.txt");
    expect(screen.getByTestId("conductor-start-words")).toHaveValue("Review app.txt");
    expect(hand.mock.calls.some(([path]) => String(path) === "/api/agent/hand")).toBe(false);
  });

  it("offers recorded shell cwd registration before Project binding", async () => {
    const shell = connectedFixture.inventory.sessions[1];
    const unbound = { ...shell, context: { ...shell.context, status: "unbound", project: null, source: null, worktree: null } };
    let registration: { method?: string; body?: string } | undefined;
    vi.spyOn(api, "apiFetch").mockImplementation(async (path, init) => {
      const url = String(path);
      if (url === "/api/delivery/terminal/sessions") return { ...connectedFixture.inventory, sessions: [unbound] } as never;
      if (url === "/api/projects") return connectedFixture.projects as never;
      if (url === "/api/repositories" && init?.method === "POST") {
        registration = { method: init.method, body: String(init.body ?? "") };
        return { repository: { id: "registered-source", name: "Registered shell" } } as never;
      }
      return { status: "ok" } as never;
    });
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${unbound.id}`);
    fireEvent.click(screen.getByTestId(`terminal-open-${unbound.id}`));
    act(() => selectWorkspaceFace("context"));
    const folder = await screen.findByRole("textbox", { name: "Repository folder" });
    expect(folder).toHaveValue(unbound.current_path);
    fireEvent.click(screen.getByRole("button", { name: "Register folder" }));
    await waitFor(() => expect(registration).toEqual({ method: "POST", body: JSON.stringify({ path: unbound.current_path }) }));
    expect(await screen.findByText("Folder registered")).toBeTruthy();
  });

  it("keeps a newer Start agent form open when an older hand returns late", async () => {
    let handResolve: ((answer: unknown) => void) | null = null;
    vi.spyOn(api, "apiFetch").mockImplementation(async (path, init) => {
      const url = String(path);
      if (url === "/api/delivery/terminal/sessions") return connectedFixture.inventory as never;
      if (url === "/api/projects") return connectedFixture.projects as never;
      if (url === "/api/notes" && init?.method === "POST") return { note: { id: "note-late-start" } } as never;
      if (url.includes("/resources/note%3A")) return { status: "ok" } as never;
      if (url === "/api/agent/hand") return new Promise((resolve) => { handResolve = resolve; }) as never;
      return { status: "ok" } as never;
    });
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${connectedFixture.inventory.sessions[0].id}`);
    fireEvent.click(screen.getByTestId("terminal-start-agent"));
    const words = await screen.findByTestId("conductor-start-words");
    fireEvent.change(words, { target: { value: "Late start" } });
    fireEvent.click(screen.getByTestId("conductor-start-go"));
    await waitFor(() => expect(handResolve).toBeTruthy());
    fireEvent.click(screen.getByTestId("terminal-start-agent"));
    await waitFor(() => expect(screen.queryByTestId("conductor-start-form")).toBeNull());
    fireEvent.click(screen.getByTestId("terminal-start-agent"));
    await screen.findByTestId("conductor-start-form");
    await act(async () => { handResolve?.({ launch_id: "launch-late-start" }); });
    expect(screen.getByTestId("conductor-start-form")).toBeTruthy();
  });

  it("keeps a recorded non-note project resource named by the Desk object index", async () => {
    const connectedSessions = connectedFixture.inventory.sessions;
    const decision = fromWireDecision(connectedFixture.decisions.decisions[0]);
    expect(decision?.title).toBe("Keep one Desk");
    useDesk.setState((state) => ({ items: { ...state.items, decision: decision ? [decision] : [] } }));
    vi.spyOn(api, "apiFetch").mockImplementation(async (path) => {
      const url = String(path);
      if (url === "/api/delivery/terminal/sessions") return connectedFixture.inventory as never;
      if (url === "/api/projects") return connectedFixture.projects as never;
      if (url.includes("/resources")) return connectedFixture.resources as never;
      if (url.startsWith("/api/coders/sessions")) return { sessions: [], flights: [] } as never;
      if (url.includes("/notes/")) return connectedFixture.notes["note-connected-brief"] as never;
      return { status: "ok" } as never;
    });
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${connectedSessions[0].id}`);
    fireEvent.click(screen.getByTestId(`terminal-open-${connectedSessions[0].id}`));
    act(() => selectWorkspaceFace("context"));
    expect(await screen.findByText("Keep one Desk")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open decision" })).toBeTruthy();
  });

  it("joins a queued arrival by its captured Note and Project when queue_id is gone", async () => {
    const connectedSessions = connectedFixture.inventory.sessions;
    let arrived = false;
    vi.spyOn(api, "apiFetch").mockImplementation(async (path) => {
      const url = String(path);
      if (url === "/api/delivery/terminal/sessions") return { ...connectedFixture.inventory, sessions: arrived ? connectedSessions : [] } as never;
      if (url === "/api/projects") return connectedFixture.projects as never;
      if (url.includes("/resources")) return connectedFixture.resources as never;
      return { status: "ok" } as never;
    });
    render(<TerminalsCore />);
    await screen.findByText("No terminal sessions");
    const queued = connectedFixture.queued;
    queueWorkspaceLaunch(queued.entry.queue_id, queued.entry.project_id, "queue", workspaceSelectionSnapshot().requestEpoch, queued.flights[0].origin_ref);
    expect(await screen.findByText("Agent queued · waiting for its terminal")).toBeTruthy();
    arrived = true;
    await act(async () => { await refreshTerminalInventory(); });
    await waitFor(() => expect(workspaceSelectionSnapshot().pendingHandoffs).toHaveLength(0));
    expect(workspaceSelectionSnapshot().sessionId).toBe(connectedSessions[0].id);
    expect(useDesk.getState().terminalWindows).toEqual([{ id: connectedSessions[0].id, origin: null }]);
  });

  it.each([
    { status: "live", canType: false, error: "Typing grant expired", words: "View only · Typing grant expired" },
    { status: "live", canType: false, error: "Disarm failed: hub unreachable", words: "View only · Disarm failed: hub unreachable" },
    { status: "live", canType: false, error: "Press Type first", words: "View only · Press Type first" },
    { status: "live", canType: true, error: "pane refused the command", words: "Not sent · pane refused the command" },
    { status: "unreachable", canType: false, error: "hub unreachable", words: "Not connected · hub unreachable" },
  ])("names the current posture for $error", async ({ status, canType, error, words }) => {
    serveInventory();
    await refreshTerminalInventory();
    useDesk.setState({ terminalWindows: [{ id: sessions[0].id, origin: null }] });
    terminalHarness.setSnapshot({ status, canType, error });
    render(<TerminalWindows />);
    expect(screen.getByTestId("terminal-status")).toHaveTextContent(words);
  });

  it("shows one creation form at a time and replaces the inventory while open", async () => {
    serveInventory();
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${sessions[0].id}`);

    fireEvent.click(screen.getByTestId("terminal-new"));
    expect(screen.getByTestId("terminal-new-shell")).toBeTruthy();
    expect(screen.queryByTestId(`terminal-row-${sessions[0].id}`)).toBeNull();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeTruthy();
    fireEvent.change(screen.getByRole("textbox", { name: "Shell name" }), { target: { value: "keep-shell" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Folder (optional)" }), { target: { value: "/work/keep" } });

    fireEvent.click(screen.getByTestId("terminal-start-agent"));
    expect(screen.queryByTestId("terminal-new-shell")).toBeNull();
    expect(screen.getByTestId("conductor-start-form")).toBeTruthy();
    fireEvent.click(screen.getByTestId("terminal-new"));
    expect(screen.getByRole("textbox", { name: "Shell name" })).toHaveValue("keep-shell");
    expect(screen.getByRole("textbox", { name: "Folder (optional)" })).toHaveValue("/work/keep");
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByTestId(`terminal-row-${sessions[0].id}`)).toBeTruthy();
  });
});

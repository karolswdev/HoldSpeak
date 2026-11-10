/** One display protocol (2026-11-08): the hub's `desk_request` frame runs
 * through the one executor and its answer goes back. The frames are the
 * hub's own, recorded from two `desk.mark` calls over MCP
 * (`__fixtures__/desk_request.json`). */
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import recorded from "../__fixtures__/desk_request.json";
import voiceUndo from "../__fixtures__/say_undo.json";

type Listener = (frame: { type: string; data: unknown }) => void;
const mocks = vi.hoisted(() => ({
  speak: vi.fn(async () => true),
  restoreFails: false,
  restoreStatus: 409,
  onRestore: null as (() => void) | null,
  listeners: new Map<string, Listener>(),
  posts: [] as Array<{ path: string; init: unknown }>,
}));

vi.mock("../../../lib/tts", () => ({ speak: mocks.speak }));

vi.mock("../../useDeskChangedRefresh", () => ({
  useBusSubscribe: () => (type: string, listener: Listener) => {
    mocks.listeners.set(type, listener);
    return () => mocks.listeners.delete(type);
  },
}));
vi.mock("../../../lib/api", async (importOriginal) => {
  const real = await importOriginal<typeof import("../../../lib/api")>();
  return {
    ...real,
    apiFetch: vi.fn(async (path: string, init?: unknown) => {
      mocks.posts.push({ path, init });
      if (path === "/api/desk/windows/restore") {
        if (mocks.restoreFails) throw new real.ApiError(mocks.restoreStatus, "window_stale", {});
        mocks.onRestore?.();
        return voiceUndo.restored;
      }
      return { answered: true };
    }),
  };
});

import { DeskRequests } from "../DeskRequests";
import { MARK_MS, executeDeskRequest, noneWords } from "../requests";

/** The owner's desk: the Needs you window with one row. */
function desk(): HTMLElement {
  const window = document.createElement("div");
  window.dataset.layer = "window";
  window.id = "chair:needs";
  const row = document.createElement("div");
  row.dataset.testid = "needs-row";
  row.textContent = "Mira asks for the plan";
  window.appendChild(row);
  document.body.appendChild(window);
  return row;
}

function hear(frame: { type: string; data: unknown }): void {
  const listener = mocks.listeners.get(frame.type);
  if (!listener) throw new Error(`no ${frame.type} listener`);
  act(() => listener(frame));
}

beforeEach(() => {
  const slot = document.createElement("div");
  slot.id = "desk-window-undo-slot";
  document.body.appendChild(slot);
  mocks.posts.length = 0;
  mocks.speak.mockReset().mockResolvedValue(true);
  mocks.restoreFails = false;
  mocks.restoreStatus = 409;
  mocks.onRestore = null;
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  cleanup();
  document.body.innerHTML = "";
  vi.useRealTimers();
});

describe("the hub's display requests", () => {
  it("a declared app identity reaches its retained mounted frame", async () => {
    const frame = document.createElement("section");
    frame.id = "ask";
    frame.dataset.layer = "window";
    const mast = document.createElement("header");
    mast.dataset.testid = "ask-mast";
    frame.appendChild(mast);
    document.body.appendChild(frame);
    const result = await executeDeskRequest({ op: "mark", args: { window: "ask:desk", target: "ask-mast" } });
    expect(result.done).toBe(true);
    expect(result.part?.window).toBe(frame);
    expect(result.part?.target).toBe(mast);
  });

  it("a mark puts the Walk's halo on the part, shows its words and answers done", async () => {
    const row = desk();
    render(<DeskRequests />);
    await act(async () => {
      hear(recorded.mark);
      await vi.waitFor(() => expect(mocks.posts).toHaveLength(1));
    });
    const { request_id: id } = recorded.mark.data;
    expect(mocks.posts[0]).toEqual({
      path: `/api/desk/requests/${id}/result`,
      init: { method: "POST", json: { done: true } },
    });
    expect(row.classList.contains("walk-halo")).toBe(true);
    expect(screen.getByTestId("desk-request-words").textContent).toBe("This one asks you");
    await act(async () => { await vi.advanceTimersByTimeAsync(MARK_MS + 50); });
    expect(row.classList.contains("walk-halo")).toBe(false);
  });

  it("a part that is not there answers not done, in the Walk's words", async () => {
    desk();
    render(<DeskRequests />);
    hear(recorded.missing);
    const { request_id: id } = recorded.missing.data;
    await act(async () => { await vi.advanceTimersByTimeAsync(7000); });
    await vi.waitFor(() => expect(mocks.posts).toHaveLength(1));
    expect(mocks.posts[0]).toEqual({
      path: `/api/desk/requests/${id}/result`,
      init: { method: "POST", json: { done: false, reason: "No people rows here yet" } },
    });
    expect(noneWords("people rows")).toBe("No people rows here yet");
    expect(document.querySelector(".walk-halo")).toBeNull();
  });

  it("a press shows the pressed look, then the real click lands", async () => {
    const row = desk();
    const clicks = vi.fn();
    row.addEventListener("click", clicks);
    const pressed = executeDeskRequest({ op: "press", args: { target: "needs-row", window: "chair:needs" } });
    await vi.waitFor(() => expect(row.hasAttribute("data-walk-pressed")).toBe(true));
    expect(clicks).not.toHaveBeenCalled();
    await expect(pressed).resolves.toMatchObject({ done: true });
    expect(clicks).toHaveBeenCalledTimes(1);
    expect(row.hasAttribute("data-walk-pressed")).toBe(false);
  });
});


describe("say and Undo use the Desk seams", () => {
  it("shows a real say frame, speaks once and posts its voice result", async () => {
    render(<DeskRequests />);
    hear(voiceUndo.say);
    await vi.waitFor(() => expect(mocks.posts).toHaveLength(1));
    expect(screen.getByTestId("desk-request-words")).toHaveTextContent("The update is ready.");
    expect(mocks.speak).toHaveBeenCalledExactlyOnceWith("The update is ready.");
    expect(mocks.posts[0].init).toEqual({ method: "POST", json: { done: true, spoken: true } });
  });

  it("a replay answers again without speaking twice", async () => {
    render(<DeskRequests />);
    hear(voiceUndo.say);
    hear(voiceUndo.say);
    await vi.waitFor(() => expect(mocks.posts).toHaveLength(2));
    expect(mocks.speak).toHaveBeenCalledTimes(1);
  });

  it("keeps the words when no voice can play", async () => {
    mocks.speak.mockResolvedValue(false);
    render(<DeskRequests />);
    hear(voiceUndo.say);
    await vi.waitFor(() => expect(mocks.posts).toHaveLength(1));
    expect(screen.getByTestId("desk-request-words")).toHaveTextContent("The update is ready.");
    expect(mocks.posts[0].init).toEqual({ method: "POST", json: { done: true, spoken: false } });
  });

  it("an agent close then one Undo puts the window back on the Desk", async () => {
    const { createHubWindows } = await import("../hubWindows");
    const { useDesk, forgetLoadRaises } = await import("../../store");
    const { useChairWindows } = await import("../../chair/chairWindows");
    const { before } = voiceUndo.undo.data.args.windows[0];
    let windows = [before];
    let revision = before.revision;
    localStorage.clear();
    forgetLoadRaises();
    useDesk.setState({ windowsById: {}, panelDepth: {}, panelOrder: [], panelMin: [], panelMax: [], panelRects: {}, panelZoom: {} });
    useChairWindows.setState({ closed: { "chair:needs": true, "chair:capture": true }, phone: "" });
    const hub = createHubWindows({ compact: () => false, cacheOpen: [], settleMs: 0,
      view: () => ({ x: 0, y: 0, w: 1440, h: 900 }),
      transport: {
        list: async () => ({ windows, stage_shelf: "left", revision, adopted: true,
          registry: { static: { "surface-projects": "open-projects" }, families: {} } }),
        verb: vi.fn(), arrange: vi.fn(), shelf: vi.fn(),
      },
    });
    function ProjectsWindow() {
      const open = useDesk((state) => Boolean(state.windowsById["surface-projects"]));
      return open ? <section data-testid="projects-window">Projects</section> : null;
    }
    try {
      render(<><DeskRequests /><ProjectsWindow /></>);
      await act(async () => { await hub.start(); });
      expect(screen.getByTestId("projects-window")).toBeInTheDocument();
      windows = [];
      revision = voiceUndo.undo.data.args.after_revision;
      await act(async () => { hub.onFrame({ kind: "windows", id: "surface-projects" }); await hub.idle(); });
      expect(screen.queryByTestId("projects-window")).toBeNull();
      hear(voiceUndo.undo);
      await vi.waitFor(() => expect(screen.getByRole("button", { name: "Undo: Close Projects" })).toBeInTheDocument());
      mocks.onRestore = () => {
        windows = voiceUndo.restored.windows;
        revision = windows[0].revision;
        hub.onFrame({ kind: "windows", id: "surface-projects" });
      };
      await act(async () => { await vi.advanceTimersByTimeAsync(7000); });
      fireEvent.click(screen.getByTestId("desk-window-undo"));
      await act(async () => { await hub.idle(); });
      await vi.waitFor(() => expect(screen.getByTestId("projects-window")).toBeInTheDocument());
      expect(screen.queryByTestId("desk-window-undo")).toBeNull();
      expect(mocks.posts.find((post) => post.path === "/api/desk/windows/restore")?.init)
        .toEqual({ method: "POST", json: { group: "desk", ...voiceUndo.undo.data.args } });
    } finally { hub.stop(); }
  });

  it("removes the strip offer eight seconds after the window act", async () => {
    vi.useFakeTimers();
    render(<DeskRequests />);
    await act(async () => { hear(voiceUndo.undo); });
    expect(screen.getByTestId("desk-window-undo")).toBeInTheDocument();
    expect(screen.getByRole("status").parentElement?.id).toBe("desk-window-undo-slot");
    await act(async () => { await vi.advanceTimersByTimeAsync(7999); });
    expect(screen.getByTestId("desk-window-undo")).toBeInTheDocument();
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(screen.queryByRole("status")).toBeNull();
    expect(mocks.posts.some((post) => post.path === "/api/desk/windows/restore")).toBe(false);
  });

  it.each([409, 500])("a refused Undo (%s) keeps its receipt for retry", async (status) => {
    mocks.restoreFails = true;
    mocks.restoreStatus = status;
    render(<DeskRequests />);
    hear(voiceUndo.undo);
    await vi.waitFor(() => expect(screen.getByTestId("desk-window-undo")).toBeInTheDocument());
    fireEvent.click(screen.getByTestId("desk-window-undo"));
    await vi.waitFor(() => expect(screen.getByText(status === 409 ? "A window changed. Its later state was kept."
      : "Undo could not be checked. Work kept. Try again.")).toBeInTheDocument());
    expect(screen.getByTestId("desk-window-undo")).not.toBeDisabled();
  });
});

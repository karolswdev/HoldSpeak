/** One display protocol (2026-11-08): the hub's `desk_request` frame runs
 * through the one executor and its answer goes back. The frames are the
 * hub's own, recorded from two `desk.mark` calls over MCP
 * (`__fixtures__/desk_request.json`). */
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import recorded from "../__fixtures__/desk_request.json";

type Listener = (frame: { type: string; data: unknown }) => void;
const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Listener>(),
  posts: [] as Array<{ path: string; init: unknown }>,
}));

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
  mocks.posts.length = 0;
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  cleanup();
  document.body.innerHTML = "";
  vi.useRealTimers();
});

describe("the hub's display requests", () => {
  it("a mark puts the Walk's halo on the part, shows its words and answers done", async () => {
    const row = desk();
    render(<DeskRequests />);
    hear(recorded.mark);
    const { request_id: id } = recorded.mark.data;
    await vi.waitFor(() => expect(mocks.posts).toHaveLength(1));
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

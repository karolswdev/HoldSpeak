/** PHILO-8-02 — the Workbench window's Remove under the undo hook's flush
 * semantics (the same `useUndoReceipt` as the Floor's delete): a second
 * Remove commits the first at once; closing the window commits a pending
 * Remove; Undo keeps the item. Changed on purpose: before, the second Remove
 * and a close dropped the pending removal without a word. */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";

type Frame = { type: string; data: unknown };

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
}));

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, listener: (frame: Frame) => void) => {
      const set =
        mocks.listeners.get(type) ?? new Set<(frame: Frame) => void>();
      set.add(listener);
      mocks.listeners.set(type, set);
      return () => set.delete(listener);
    },
  }),
  useRuntimeFrame: () => null,
}));

import { WorkbenchWindow } from "../WorkbenchWindow";

function mockHub() {
  const item = (id: string, title: string) => ({
    id, title, body: "", status: "pending", priority: 3, result: null,
  });
  const wb = {
    id: "wb1", name: "Test WB", recipe_id: null, profile_id: null,
    resolver_profile_id: null, schedule: null, schedule_enabled: false,
    items: [item("i1", "First item"), item("i2", "Second item")], last_run: null,
  };
  const deletes: string[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const json = (body: unknown) =>
      new Response(JSON.stringify(body), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    if (init?.method === "DELETE") {
      deletes.push(url.replace(/^.*\/items\//, ""));
      return json({});
    }
    if (/\/runs$/.test(url)) return json({ runs: [] });
    if (/\/memory$/.test(url)) return json({ entries: [] });
    if (/\/api\/skills/.test(url)) return json({ skills: [] });
    if (/\/api\/workbenches\/wb1$/.test(url)) return json({ workbench: wb });
    return json({});
  });
  vi.stubGlobal("fetch", fetchMock);
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      workbench: [{ kind: "workbench", id: "wb1", name: "Test WB" } as never],
    },
    inferenceTargets: [],
    profiles: [],
  });
  return deletes;
}

async function removeItem(title: string) {
  const head = await screen.findByText(title);
  fireEvent.click(head.closest("button")!);
  const remove = await screen.findByRole("button", { name: "Remove" });
  fireEvent.click(remove);
}

describe("PHILO-8-02 the Workbench window's Remove", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.listeners.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("a second Remove commits the first at once", async () => {
    const deletes = mockHub();
    render(<WorkbenchWindow workbenchId="wb1" />);
    await removeItem("First item");
    expect(await screen.findByText("Removed First item")).toBeInTheDocument();
    expect(deletes).toEqual([]);
    await removeItem("Second item");
    await waitFor(() => expect(deletes).toEqual(["i1"]));
    expect(screen.getByText("Removed Second item")).toBeInTheDocument();
  });

  it("closing the window commits a pending Remove", async () => {
    const deletes = mockHub();
    const view = render(<WorkbenchWindow workbenchId="wb1" />);
    await removeItem("First item");
    await screen.findByText("Removed First item");
    view.unmount();
    await waitFor(() => expect(deletes).toEqual(["i1"]));
  });

  it("Undo keeps the item", async () => {
    const deletes = mockHub();
    const view = render(<WorkbenchWindow workbenchId="wb1" />);
    await removeItem("First item");
    fireEvent.click(await screen.findByRole("button", { name: "Undo" }));
    expect(await screen.findByText("Restored First item")).toBeInTheDocument();
    view.unmount();
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(deletes).toEqual([]);
  });
});

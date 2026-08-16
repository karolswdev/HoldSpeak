// HS-132-03 — a running workbench moves without a reload.
//
// WorkbenchWindow has subscribed to five `workbench.*` frames since
// HS-116-07. Nothing ever sent them: the conductor's broadcast seam was
// wired to the hub and never called, so the window sat still through an
// entire run. WorkbenchRunner now emits at the real transitions; these
// tests hold the window to the payload contract those emitters send.
import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";

type Frame = { type: string; data: unknown };

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
}));

function subscribe(type: string, listener: (frame: Frame) => void) {
  const set = mocks.listeners.get(type) ?? new Set<(frame: Frame) => void>();
  set.add(listener);
  mocks.listeners.set(type, set);
  return () => set.delete(listener);
}

function emit(type: string, data: unknown) {
  act(() => {
    for (const listener of [...(mocks.listeners.get(type) ?? [])])
      listener({ type, data });
  });
}

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));

import { WorkbenchWindow } from "../WorkbenchWindow";

const ITEM = {
  id: "i-1",
  title: "Draft the brief",
  body: "",
  priority: 3,
  status: "pending",
  grounding: {},
  result: null,
  result_egress: null,
  result_artifact_id: null,
  artifact_status: null,
  mint_attempted: false,
  tokens_consumed: 0,
  created_at: "2026-01-01T00:00:00Z",
  completed_at: null,
};

function mockHub(items = [ITEM]) {
  const wb = {
    id: "wb1",
    name: "Daily",
    recipe_id: "r1",
    profile_id: "p1",
    schedule: null,
    schedule_enabled: false,
    items,
    last_run: null,
  };
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const json = (body: unknown) =>
      new Response(JSON.stringify(body), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    if ((init?.method || "GET").toUpperCase() !== "GET") return json({ ok: true });
    if (/\/runs$/.test(url)) return json({ runs: [] });
    if (/\/memory$/.test(url)) return json({ entries: [] });
    if (/\/api\/skills/.test(url)) return json({ skills: [] });
    if (/\/api\/workbenches\/wb1$/.test(url)) return json({ workbench: wb });
    return json({});
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function openWindow(items = [ITEM]) {
  const fetchMock = mockHub(items);
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      workbench: [{ kind: "workbench", id: "wb1", name: "Daily" } as never],
    },
    inferenceTargets: [],
    profiles: [],
  });
  render(<WorkbenchWindow workbenchId="wb1" />);
  await screen.findByText("Draft the brief");
  return fetchMock;
}

/** The exact payloads holdspeak/workbench_conductor.py emit_* helpers send. */
const RUN = { workbench_id: "wb1", run_id: "wbrun_abc" };

describe("HS-132-03 the workbench window hears its own run", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.listeners.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("subscribes to all five run frames", async () => {
    await openWindow();
    for (const type of [
      "workbench.run_start",
      "workbench.item_claimed",
      "workbench.item_done",
      "workbench.item_failed",
      "workbench.run_complete",
    ])
      expect(mocks.listeners.get(type)?.size ?? 0).toBeGreaterThan(0);
  });

  it("shows progress from run_start through the items to complete", async () => {
    await openWindow();
    emit("workbench.run_start", { ...RUN, item_count: 2 });
    expect(await screen.findByText(/Running 0\/2/)).toBeInTheDocument();

    emit("workbench.item_claimed", { ...RUN, item_id: "i-1", index: 1, total: 2 });
    expect(await screen.findByText(/Running 1\/2/)).toBeInTheDocument();

    emit("workbench.item_done", { ...RUN, item_id: "i-1", index: 1, total: 2 });
    emit("workbench.item_claimed", { ...RUN, item_id: "i-2", index: 2, total: 2 });
    expect(await screen.findByText(/Running 2\/2/)).toBeInTheDocument();

    emit("workbench.item_failed", {
      ...RUN,
      item_id: "i-2",
      index: 2,
      total: 2,
      error: "provider refused",
    });
    emit("workbench.run_complete", {
      ...RUN,
      disposition: "succeeded",
      attempted: 2,
      completed: 1,
      failed: 1,
      pending_count: 0,
    });
    await waitFor(() =>
      expect(screen.queryByText(/Running \d\/\d/)).not.toBeInTheDocument(),
    );
  });

  it("ignores a run belonging to a different workbench", async () => {
    await openWindow();
    emit("workbench.run_start", {
      workbench_id: "wb-other",
      run_id: "wbrun_x",
      item_count: 9,
    });
    expect(screen.queryByText(/Running 0\/9/)).not.toBeInTheDocument();
  });
});

// The Parked drawer, the app: the real ParkedDrawer on the hub's OWN answers
// (the test diet, PHILO-17 final lane A, 2026-10-11). The answers were recorded
// on a real hub by tests/integration/test_desk_parked.py (canvas week; a meeting
// and a Project parked through the real DELETE routes), which fences their
// shape on every run. Only apiFetch (the wire) is replaced.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import before from "./fixtures/parked-wire/parked-before.json";
import restored from "./fixtures/parked-wire/restore-project.json";
import after from "./fixtures/parked-wire/parked-after.json";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

import { useDesk } from "../store";
import { ParkedDrawer } from "../drawer/ParkedDrawer";
import { useDrawers } from "../drawer/store";

let stage: "before" | "after" = "before";
const calls: Array<{ method: string; path: string }> = [];
const misses: string[] = [];

beforeEach(() => {
  stage = "before";
  calls.length = 0;
  misses.length = 0;
  apiFetch.mockReset();
  apiFetch.mockImplementation(async (path: string, init?: { method?: string }) => {
    const method = (init?.method ?? "GET").toUpperCase();
    calls.push({ method, path });
    if (method === "GET" && path === "/api/desk/parked") return structuredClone((stage === "before" ? before : after).wire);
    if (method === "POST" && path === "/api/projects/p-hiring/restore") {
      stage = "after";
      return structuredClone(restored.wire);
    }
    misses.push(`${method} ${path}`);
    throw new Error(`not recorded: ${method} ${path}`);
  });
  useDrawers.setState({ drawers: [], infos: [], parked: null, revision: 0, receipts: {} });
});
afterEach(() => vi.restoreAllMocks());

describe("the Parked drawer on the hub's recorded answers", () => {
  it("lists the parked meeting and the parked Project; Restore of the Project says Restored and its row leaves", async () => {
    // replaces: tests/e2e/test_philo15_04_small_gaps_glass.py::TestParkedDrawer::test_park_a_meeting_and_a_project_see_both_restore_one
    // (hub half: tests/integration/test_desk_parked.py::test_park_a_meeting_and_a_project_see_both_restore_one)
    vi.spyOn(useDesk.getState(), "refresh").mockResolvedValue(undefined as never);
    render(<ParkedDrawer origin={null} />);
    const list = await screen.findByRole("grid", { name: "Archive" });
    await screen.findByRole("button", { name: /^Architecture review: tracing, Meeting/ });
    const project = screen.getByRole("button", { name: /^Staff hiring loop, Project/ });
    expect(within(list).getAllByRole("row")).toHaveLength(3); // the head + two rows

    fireEvent.click(project);
    await act(async () => {
      fireEvent.click(screen.getByTestId("parked-restore"));
    });
    expect(calls.filter((c) => c.method === "POST").map((c) => c.path)).toEqual(["/api/projects/p-hiring/restore"]);
    await waitFor(() => expect(screen.getByTestId("parked-receipt").textContent).toMatch(/^Restored at/));
    await waitFor(() => expect(screen.queryByRole("button", { name: /^Staff hiring loop/ })).toBeNull());
    expect(screen.getByRole("button", { name: /^Architecture review: tracing, Meeting/ })).toBeTruthy();
    expect(within(screen.getByRole("grid", { name: "Archive" })).getAllByRole("row")).toHaveLength(2);
    expect(misses).toEqual([]);
  });
});

// Conductor K3: the agents store and Needs you re-read on a `scope:"coder"`
// frame, not only on mount (ChairHome fetched the agents once). PHILO-14 C4:
// the AGENTS section is parked; ChairHome keeps the store live for the
// screen's agent objects and the Conductor drawer.
import { act, render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { ChairHome } from "../ChairHome";
import { openChairWindows } from "./fixtures/openChairWindows";

// PHILO-14 A1: the Chair is the screen; these specs read its windows, so they open them first.
beforeEach(() => openChairWindows());

const bus = vi.hoisted(() => ({ handlers: new Map<string, Set<(frame: unknown) => void>>() }));

vi.mock("../../../lib/api", async (original) => ({
  ...await original<typeof import("../../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../../../runtime/RuntimeBus", () => {
  const value = {
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      const set = bus.handlers.get(type) ?? new Set();
      set.add(handler);
      bus.handlers.set(type, set);
      return () => set.delete(handler);
    },
  };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));

function emit(frame: { type: string; data: unknown }) {
  for (const handler of bus.handlers.get(frame.type) ?? []) handler(frame);
}

const calls = (path: string) =>
  vi.mocked(apiFetch).mock.calls.filter(([url]) => url === path).length;

describe("the agents store follows the coder frame (Conductor K3; C4: no AGENTS section)", () => {
  beforeEach(() => {
    bus.handlers.clear();
    vi.mocked(apiFetch).mockReset();
    vi.mocked(apiFetch).mockImplementation(async () => null);
  });

  it("re-reads the agents and Needs you on a coder frame", async () => {
    render(<ChairHome />);
    await waitFor(() => expect(calls("/api/coders/sessions?include_ended=false")).toBe(1));
    // PERF-DOCK 2026-10-28: the agent rows are read live on every read, so
    // the coder frame reads plainly; it never forces the hub's rebuild.
    const readsBefore = calls("/api/desk/needs-you");

    act(() => emit({ type: "intel_status", data: { scope: "belt" } }));
    expect(calls("/api/coders/sessions?include_ended=false")).toBe(1);

    act(() => emit({ type: "intel_status", data: { state: "ready", scope: "coder" } }));
    await waitFor(() => expect(calls("/api/coders/sessions?include_ended=false")).toBe(2));
    await waitFor(() => expect(calls("/api/desk/needs-you")).toBeGreaterThan(readsBefore));
    expect(calls("/api/desk/needs-you?fresh=1")).toBe(0);
  });

  // PERF-DOCK (owner 2026-10-28: a window open waited 2-3 s): a frame of
  // window changes only reads nothing; any other desk change reads plainly.
  it("reads Needs you on a desk change, never on a window change, and never with fresh=1", async () => {
    render(<ChairHome />);
    await waitFor(() => expect(calls("/api/desk/needs-you")).toBeGreaterThan(0));
    await new Promise((resolve) => setTimeout(resolve, 400));
    const before = calls("/api/desk/needs-you");

    act(() => emit({ type: "desk_changed", data: {
      kind: "windows", id: "today", op: "open",
      changes: [{ kind: "windows", id: "today", op: "open" }],
    } }));
    await new Promise((resolve) => setTimeout(resolve, 450));
    expect(calls("/api/desk/needs-you")).toBe(before);

    act(() => emit({ type: "desk_changed", data: {
      kind: "note", id: "n1", op: "update", changes: [{ kind: "note", id: "n1", op: "update" }],
    } }));
    await waitFor(() => expect(calls("/api/desk/needs-you")).toBeGreaterThan(before));
    expect(calls("/api/desk/needs-you?fresh=1")).toBe(0);
  });
});

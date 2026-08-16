// HS-132-03 — the desk hears intelligence live.
//
// Four frames the hub had broadcast to nobody now land on the live surface:
// `intel_token` (progressive text), `intel_complete` (the window that
// landed), `bookmark` (the dropped moment's confirmation), and
// `capture_recovery`. Article XI.5 rides along: a token is display material
// and must never reach the wire.
import { render, screen, waitFor, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

type Frame = { type: string; data: unknown };

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
  apiFetch: vi.fn(),
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
    for (const listener of [...(mocks.listeners.get("*") ?? [])])
      listener({ type, data });
  });
}

vi.mock("../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) =>
    error instanceof Error ? error.message : "Request failed",
}));

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));

import { LiveCore } from "./LiveCore";

describe("LiveCore hears the live meeting frames", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    mocks.apiFetch.mockResolvedValue({});
  });

  async function mount() {
    const view = render(<LiveCore />);
    // let the four useResource fetches settle before frames arrive
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());
    return view;
  }

  it("renders intelligence arriving token by token", async () => {
    await mount();
    emit("intel_token", "The team ");
    emit("intel_token", "agreed to ");
    emit("intel_token", "ship Friday.");
    // The burst is coalesced into one paint, so the whole run appears at once.
    expect(
      await screen.findByText(/The team agreed to ship Friday\./),
    ).toBeInTheDocument();
  });

  it("accepts a token frame carried as an object", async () => {
    await mount();
    emit("intel_token", { token: "chunked" });
    expect(await screen.findByText(/chunked/)).toBeInTheDocument();
  });

  it("replaces the stream with the window that landed", async () => {
    await mount();
    emit("intel_token", "partial thought");
    expect(await screen.findByText(/partial thought/)).toBeInTheDocument();
    emit("intel_complete", {
      summary: "Shipping is on for Friday.",
      topics: ["release", "staffing"],
      action_items: [{ task: "cut the branch" }],
      final: true,
    });
    expect(
      await screen.findByText("Shipping is on for Friday."),
    ).toBeInTheDocument();
    expect(screen.getByText("release")).toBeInTheDocument();
    expect(screen.queryByText(/partial thought/)).not.toBeInTheDocument();
    expect(screen.getByText(/1 action item · final/)).toBeInTheDocument();
  });

  it("never puts a token on the wire (Article XI.5)", async () => {
    await mount();
    const before = mocks.apiFetch.mock.calls.length;
    emit("intel_token", "secret words nobody may journal");
    await screen.findByText(/secret words nobody may journal/);
    expect(mocks.apiFetch.mock.calls.length).toBe(before);
    expect(JSON.stringify(mocks.apiFetch.mock.calls)).not.toContain("secret");
  });

  it("confirms a dropped bookmark", async () => {
    await mount();
    emit("bookmark", { label: "the decision", formatted_time: "00:12:04" });
    expect(
      await screen.findByText(/the decision · 00:12:04/),
    ).toBeInTheDocument();
  });

  it("confirms an unlabelled bookmark too", async () => {
    await mount();
    emit("bookmark", {});
    expect(await screen.findByText(/Bookmark dropped/)).toBeInTheDocument();
  });

  it("shows capture recovery instead of swallowing it", async () => {
    await mount();
    emit("capture_recovery", {
      status: "recoverable",
      error: "Checkpoint failed: disk full",
    });
    expect(
      await screen.findByText(/Checkpoint failed: disk full/),
    ).toBeInTheDocument();
  });
});

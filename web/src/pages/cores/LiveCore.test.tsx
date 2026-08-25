// HS-132-03 — the desk hears intelligence live.
//
// Complete meeting intelligence, bookmarks, and capture recovery land on the
// live surface. Phase 143 C1 deliberately does not expose provider token frames.
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
    // Let the resource fetches settle before frames arrive.
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());
    return view;
  }

  it("renders an elected complete intelligence result", async () => {
    await mount();
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
    expect(screen.getByText(/1 action item · final/)).toBeInTheDocument();
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

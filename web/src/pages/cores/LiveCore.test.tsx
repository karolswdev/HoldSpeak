// HS-132-03 — the desk hears intelligence live.
//
// Complete meeting intelligence, bookmarks, and capture recovery land on the
// live surface. Phase 143 C1 deliberately does not expose provider token frames.
import { fireEvent, render, screen, waitFor, act } from "@testing-library/react";
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

  it("stops the live room without claiming a failed save is a saved Meeting", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path.endsWith("/api/meeting/stop")) {
        return {
          success: true,
          status: "stopped",
          meeting: { id: "meeting-live" },
          save: { database_saved: false, json_saved: true },
          save_error: "Database write failed",
        };
      }
      return {};
    });
    render(<LiveCore meetingId="meeting-live" />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "Stop meeting" }));
    await waitFor(() => expect(screen.getByText("STOPPED · PARTLY SAVED")).toBeInTheDocument());
    expect(screen.queryByText("Meeting saved")).toBeNull();
    expect(screen.queryByRole("button", { name: "Return to saved Meeting" })).toBeNull();
    expect(screen.getByTitle(/Database write failed/)).toBeInTheDocument();
  });

  it("keeps an Open Meeting door for a durable DB row with a partial save", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path.endsWith("/api/meeting/stop")) {
        return {
          success: true,
          status: "stopped",
          meeting: { id: "meeting-retained" },
          save: { database_saved: true, json_saved: false },
          save_error: "JSON export failed",
        };
      }
      return {};
    });
    render(<LiveCore meetingId="meeting-retained" />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "Stop meeting" }));
    await waitFor(() => expect(screen.getByText("STOPPED · PARTLY SAVED")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Open Meeting" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Return to saved Meeting" })).toBeNull();
  });

  it("keeps the live room active when Stop explicitly says capture continues", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path.endsWith("/api/meeting/stop")) {
        return { success: true, status: "recording", meeting: { id: "meeting-still-live" } };
      }
      return {};
    });
    render(<LiveCore meetingId="meeting-still-live" />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "Stop meeting" }));
    await waitFor(() => expect(screen.getByText("Recording")).toBeInTheDocument());
    expect(screen.queryByText(/STOPPED/)).toBeNull();
  });

  it("offers recovery only for a recoverable database save and returns to that Meeting", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path.endsWith("/api/meeting/stop")) {
        return {
          success: true,
          status: "stopped",
          meeting: { id: "meeting-recoverable", capture_status: "recoverable" },
          save: { database_saved: false, json_saved: true },
          save_error: "database unavailable",
        };
      }
      if (path.endsWith("/capture/recover")) return { recovered: true };
      return {};
    });
    render(<LiveCore meetingId="meeting-recoverable" />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "Stop meeting" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Retry recovery" })).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Retry recovery" }));
    await waitFor(() => expect(screen.getByText("Meeting saved")).toBeInTheDocument());
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/api/meetings/meeting-recoverable/capture/recover",
      { method: "POST" },
    );
  });

  it("keeps the saved Meeting return after a confirmed complete stop", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path.endsWith("/api/meeting/stop")) {
        return {
          success: true,
          status: "stopped",
          meeting: { id: "meeting-saved" },
          save: { database_saved: true, json_saved: true },
        };
      }
      return {};
    });
    render(<LiveCore meetingId="meeting-saved" />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "Stop meeting" }));
    await waitFor(() => expect(screen.getByText("Meeting saved")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Return to saved Meeting" })).toBeInTheDocument();
  });
});

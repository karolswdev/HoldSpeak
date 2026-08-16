import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AmbientLayer } from "./AmbientLayer";
import { dismissAftercare } from "../desk/intelligenceAttention";

/**
 * HS-132-08 — a finished meeting is visible without the mascot.
 *
 * `aftercare_ready` used to reach exactly one subscriber: the Qlippy block,
 * gated on presence + mascot (off by default). With the mascot off, the desk
 * still seats the signal and reaches the meeting's proposals in one click.
 */

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  openSurfaceWhenReady: vi.fn(),
  listeners: new Map<string, (frame: { type: string; data: unknown }) => void>(),
}));

vi.mock("../lib/api", () => ({
  ApiError: class ApiError extends Error {},
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) =>
    error instanceof Error ? error.message : "Request failed",
}));

vi.mock("../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, listener: (frame: { type: string; data: unknown }) => void) => {
      mocks.listeners.set(type, listener);
      return () => mocks.listeners.delete(type);
    },
  }),
  useRuntimeFrame: () => null,
}));

vi.mock("../desk/shell", () => ({
  openSurfaceWhenReady: mocks.openSurfaceWhenReady,
}));

vi.mock("../desk/projections", () => {
  const state = { ambient: [], refreshAmbient: vi.fn(), present: vi.fn() };
  const useProjections = Object.assign(
    (selector: (value: typeof state) => unknown) => selector(state),
    { getState: () => state },
  );
  return { useProjections };
});

const aftercare = {
  meeting_id: "meeting-42",
  title: "Launch review",
  open_total: 3,
  decided_total: 1,
  top_items: [],
};

function broadcastAftercare(data: unknown = aftercare) {
  act(() => {
    mocks.listeners.get("aftercare_ready")?.({ type: "aftercare_ready", data });
  });
}

describe("aftercare without the mascot", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listeners.clear();
    dismissAftercare();
    // The mascot is off, which is the default posture.
    mocks.apiFetch.mockImplementation((path: string) =>
      path === "/api/settings"
        ? Promise.resolve({ presence: { enabled: false, mascot: false } })
        : Promise.resolve({}),
    );
  });

  afterEach(() => dismissAftercare());

  it("seats the finished meeting on the desk with the mascot off", () => {
    render(<AmbientLayer />);
    expect(screen.queryByLabelText("Meeting aftercare")).toBeNull();

    broadcastAftercare();

    expect(screen.getByLabelText("Meeting aftercare")).toBeInTheDocument();
    expect(screen.getByText("Launch review")).toBeInTheDocument();
    expect(screen.getByText("3 open · 1 decided")).toBeInTheDocument();
  });

  it("reaches the meeting's proposals in one click", () => {
    render(<AmbientLayer />);
    broadcastAftercare();

    fireEvent.click(screen.getByRole("button", { name: "Open proposals" }));

    expect(mocks.openSurfaceWhenReady).toHaveBeenCalledWith(
      "review-meetings",
      "meeting:meeting-42",
    );
    expect(screen.queryByLabelText("Meeting aftercare")).toBeNull();
  });

  it("dismisses without opening anything", () => {
    render(<AmbientLayer />);
    broadcastAftercare();

    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));

    expect(mocks.openSurfaceWhenReady).not.toHaveBeenCalled();
    expect(screen.queryByLabelText("Meeting aftercare")).toBeNull();
  });

  it("ignores a frame that names no meeting", () => {
    render(<AmbientLayer />);

    broadcastAftercare({ title: "Nothing addressable" });

    expect(screen.queryByLabelText("Meeting aftercare")).toBeNull();
  });
});

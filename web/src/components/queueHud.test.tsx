// HS-132-03 — the queue HUD renders the queue that exists.
//
// The HUD had subscribed to `plugin_jobs` / `plugin_job` since it was
// written; nothing in the hub has ever broadcast either name, so the HUD
// had never once rendered. `runtime_queue` is the frame the hub actually
// sends (holdspeak/runtime/plugin_queue.py), carrying the deferred-intel
// jobs and their queued/running/failed counts.
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  frames: {} as Record<string, unknown>,
}));

vi.mock("../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) =>
    error instanceof Error ? error.message : "Request failed",
}));

vi.mock("../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
  useRuntimeFrame: (type: string) => mocks.frames[type] ?? null,
}));

vi.mock("../desk/projections", () => {
  const state = { ambient: [], refreshAmbient: vi.fn(), present: vi.fn() };
  const useProjections = Object.assign(
    (selector: (value: typeof state) => unknown) => selector(state),
    { getState: () => state },
  );
  return { useProjections };
});

import { AmbientLayer } from "./AmbientLayer";

const QUEUE = {
  jobs: [
    { id: "intelq:m1", meeting_id: "m1", label: "Roadmap sync", status: "queued" },
    { id: "intelq:m2", meeting_id: "m2", label: "Standup", status: "running" },
  ],
  queued: 2,
  running: 1,
  failed: 1,
  scheduled_retries: 0,
  next_retry_at: null,
};

describe("the queue HUD consumes runtime_queue", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    for (const key of Object.keys(mocks.frames)) delete mocks.frames[key];
    mocks.apiFetch.mockResolvedValue({ presence: { enabled: false } });
  });

  it("stays silent with no queue frame", () => {
    render(<AmbientLayer />);
    expect(screen.queryByText(/pending ·/)).not.toBeInTheDocument();
  });

  it("ignores the retired plugin_jobs vocabulary", () => {
    mocks.frames.plugin_jobs = { pending: 4, running: 1, failed: 0 };
    mocks.frames.plugin_job = { pending: 4, running: 1, failed: 0 };
    render(<AmbientLayer />);
    expect(screen.queryByText(/1 running/)).not.toBeInTheDocument();
  });

  it("renders the lamp and the jobs behind it", () => {
    mocks.frames.runtime_queue = QUEUE;
    render(<AmbientLayer />);
    const toggle = screen.getByRole("button", { expanded: false });
    expect(toggle).toHaveTextContent("1 running");
    fireEvent.click(toggle);
    expect(screen.getByText("Intelligence queue")).toBeInTheDocument();
    expect(screen.getByText(/2 pending · 1 running · 1 failed/)).toBeInTheDocument();
    expect(screen.getByText("Roadmap sync")).toBeInTheDocument();
    expect(screen.getByText("Standup")).toBeInTheDocument();
  });

  it("stays silent when the queue is genuinely empty", () => {
    mocks.frames.runtime_queue = {
      jobs: [],
      queued: 0,
      running: 0,
      failed: 0,
      scheduled_retries: 0,
    };
    render(<AmbientLayer />);
    expect(screen.queryByRole("button", { expanded: false })).toBeNull();
  });

  it("speaks up for a queue that is only retrying", () => {
    mocks.frames.runtime_queue = {
      jobs: [],
      queued: 0,
      running: 0,
      failed: 0,
      scheduled_retries: 3,
    };
    render(<AmbientLayer />);
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    expect(screen.getByText(/3 retrying/)).toBeInTheDocument();
  });
});

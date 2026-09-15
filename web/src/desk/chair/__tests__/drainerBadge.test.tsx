// HS-200-42 (counsel N1) — the Chair's meeting row stops being optimistic.
//
// A meeting whose server-side intel status is `queued` used to read QUEUED
// whether or not anything in the hub would ever execute it: for three months
// nothing did. The `runtime_queue` frame — the one the ambient HUD chip
// already consumes — now carries the hub drainer's state, so the row can say
// NOT DRAINING durably instead of flashing the click receipt for a second.
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  frames: {} as Record<string, unknown>,
}));

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
  useRuntimeFrame: (type: string) => mocks.frames[type] ?? null,
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));

import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { ChairHome } from "../ChairHome";

const QUEUED_MEETING = {
  kind: "meeting" as const,
  id: "m-budget",
  title: "Quarterly budget review",
  startedAt: new Date().toISOString(),
  endedAt: new Date().toISOString(),
  segmentCount: 3,
  actionItemCount: 0,
  durationSeconds: 1920,
  tags: [],
  intelStatus: "queued",
  calendarEventId: null,
  calendarEventTitle: null,
  calendarSourceLabel: null,
  transcriptWords: 38,
};

function seed(frame: Record<string, unknown> | null) {
  mocks.frames.runtime_queue = frame;
  useDesk.setState({
    items: { ...EMPTY_ITEMS, meeting: [QUEUED_MEETING] } as never,
  });
}

describe("the Chair row reads the drainer, not just the queue", () => {
  beforeEach(() => {
    vi.mocked(mocks.apiFetch).mockReset();
    mocks.apiFetch.mockResolvedValue(null);
    mocks.frames.runtime_queue = null;
  });

  it("a queued row with an ABSENT drainer reads NOT DRAINING", async () => {
    seed({ jobs: [], queued: 1, running: 0, failed: 0, drainer: "absent" });
    render(<ChairHome />);
    const badge = await screen.findByTestId("arrival-meeting-badge");
    await waitFor(() => expect(badge.textContent).toBe("NOT DRAINING"));
    expect(badge.getAttribute("data-badge")).toBe("not-draining");
  });

  it("a queued row with a RUNNING drainer reads QUEUED", async () => {
    seed({ jobs: [], queued: 1, running: 0, failed: 0, drainer: "running" });
    render(<ChairHome />);
    const badge = await screen.findByTestId("arrival-meeting-badge");
    await waitFor(() => expect(badge.textContent).toBe("QUEUED"));
    expect(badge.getAttribute("data-badge")).toBe("queued");
  });

  it("no frame is UNKNOWN, never reported as absent", async () => {
    seed(null);
    render(<ChairHome />);
    const badge = await screen.findByTestId("arrival-meeting-badge");
    await waitFor(() => expect(badge.textContent).toBe("QUEUED"));
  });
});

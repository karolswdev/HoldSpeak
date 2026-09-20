// HS-201-11 — `HAS OPEN ACTIONS` only when open actions exist.
//
// The rehearsal's desk held ONE meeting with ZERO actions and the Meetings
// face still offered the `HAS OPEN ACTIONS` filter
// (audits/rehearsal-07-opus.md, LANGUAGE row; shot
// assets/story-07-rehearsal/03-meetings-list-393.png). A filter that can
// match nothing says nothing.
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../../lib/api";
import { HistoryCore } from "../../HistoryCore";
import { hasOpenMeetingActions } from "../helpers";

vi.mock("../../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

const mockedApiFetch = vi.mocked(apiFetch);

const MEETING = {
  id: "m-1",
  title: "Sprint planning rehearsal",
  started_at: "2026-09-19T09:00:00Z",
  duration_seconds: 3,
  capture_status: "finalized",
  intel_status: { state: "ready" },
  transcriptWords: 9,
  action_item_count: 0,
};

const OPEN_ACTION = {
  id: "a-1",
  task: "Send the freeze window",
  owner: "Priya",
  status: "pending",
  meeting_id: "m-1",
};

/** A thread's action item: open, but no meeting facet can reach it. */
const THREAD_ACTION = { ...OPEN_ACTION, id: "a-2", meeting_id: null };

function wire(actionItems: Record<string, unknown>[]) {
  mockedApiFetch.mockImplementation(async (path: string) => {
    const url = String(path);
    if (url.startsWith("/api/meetings?")) return { meetings: [MEETING] } as never;
    if (url === "/api/all-action-items") return { action_items: actionItems } as never;
    return {} as never;
  });
}

describe("HS-201-11 the open-actions filter is drawn only when it can find one", () => {
  beforeEach(() => mockedApiFetch.mockReset());

  it("reads an OPEN action attached to a meeting", () => {
    expect(hasOpenMeetingActions([OPEN_ACTION])).toBe(true);
    expect(hasOpenMeetingActions([])).toBe(false);
    expect(hasOpenMeetingActions([THREAD_ACTION])).toBe(false);
    expect(hasOpenMeetingActions(undefined)).toBe(false);
    expect(hasOpenMeetingActions({ action_items: [OPEN_ACTION] })).toBe(false);
  });

  it("draws no filter over a meeting with zero actions", async () => {
    wire([]);
    render(<HistoryCore />);
    await screen.findByTestId("meetings-headline");
    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenCalledWith("/api/all-action-items"),
    );
    await waitFor(() => expect(screen.queryByTestId("meetings-facets")).toBeNull());
    expect(screen.queryByText("HAS OPEN ACTIONS")).toBeNull();
  });

  it("draws the filter once an open action exists", async () => {
    wire([OPEN_ACTION]);
    render(<HistoryCore />);
    await screen.findByTestId("meetings-headline");
    await waitFor(() => expect(screen.getByTestId("meetings-facets")).toBeTruthy());
    expect(screen.getByText("HAS OPEN ACTIONS")).toBeTruthy();
  });
});

// The canonical meeting host and its requested Send well.
import { act, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../../lib/api";
import { HistoryCore } from "../../HistoryCore";
import { MeetingRecord } from "../MeetingRecord";
import { WindowIdContext } from "../../../../desk/components/window/windowIdContext";
import { useDesk } from "../../../../desk/store";
import { SEND_OPEN, resetSendTo } from "../../../../desk/windowSend";
import { resetSendStore } from "../../../../desk/surface/send";

vi.mock("../../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));
vi.mock("../../connections/api", async (original) => ({
  ...(await original<typeof import("../../connections/api")>()),
  fetchConnections: () => Promise.resolve({ tools: [] }),
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

function wire(actionItems: Record<string, unknown>[]) {
  mockedApiFetch.mockImplementation(async (path: string) => {
    const url = String(path);
    if (url.startsWith("/api/meetings?")) return { meetings: [MEETING] } as never;
    if (/^\/api\/meetings\/m-1(?:\?|$)/.test(url)) return MEETING as never;
    if (url === "/api/all-action-items") return { action_items: actionItems } as never;
    return {} as never;
  });
}

describe("the canonical meeting host", () => {
  beforeEach(() => mockedApiFetch.mockReset());

  it("mounts the real meeting record for a canonical scope and returns to the selected row", async () => {
    wire([]);
    const view = render(<HistoryCore />);
    await screen.findByTestId("meeting-row-m-1");

    // This is the same scope transition SurfaceWindows gives the real core;
    // the host and MeetingRecord are not replaced with a test double.
    view.rerender(<HistoryCore scope="meeting:m-1" />);
    await screen.findByTestId("meeting-toolbar");
    expect(screen.queryByTestId("meeting-decide-well")).toBeNull();
    // The language: the rail stays beside the picked meeting, its row marked.
    expect(screen.queryByTestId("meeting-row-m-1")).toBeNull();
    expect(screen.getByTestId("meetings-pane")).toContainElement(screen.getByTestId("meeting-record"));

    // Back clears the canonical scope (the narrow window's way to the rail).
    // The rail keeps the last meeting marked so the owner returns to it.
    view.rerender(<HistoryCore />);
    await screen.findByTestId("meeting-row-m-1");
    expect(screen.getByTestId("meeting-row-m-1").getAttribute("data-selected")).toBe("true");
  });

  it("opens the requested Send well only on the event's scoped meeting record", async () => {
    resetSendTo();
    resetSendStore();
    useDesk.setState({ windowsById: {
      "surface-meetings": { id: "surface-meetings", kind: "surface", applicationKey: "meetings", scope: "meeting:m-1", persistence: "workspace" },
    } } as never);
    mockedApiFetch.mockImplementation(async (path: string) => {
      const url = String(path);
      const record = /^\/api\/meetings\/(m-[12])(?:\?|$)/.exec(url);
      if (record) return { ...MEETING, id: record[1], intel: { summary: "Saved summary." } } as never;
      if (url.startsWith("/api/meetings?")) return { meetings: [MEETING] } as never;
      if (url === "/api/all-action-items") return { action_items: [] } as never;
      if (url === "/api/channels/destinations") return { destinations: [{
        id: "holdspeak-folder", name: "HoldSpeak folder", channel: "file", account: {},
        target: { folder: "/tmp/canvas-sent", display: "~/Documents/HoldSpeak/Sent" },
        builtin: true, synced: false, state: "active", created_at: "2026-10-14T12:00:00Z", parked_at: null,
      }] } as never;
      if (url.startsWith("/api/channels/sends")) return { sends: [] } as never;
      if (url === "/api/channels/preview") return { payload_digest: "saved-digest", preview: { text: "Saved summary." } } as never;
      return {} as never;
    });
    render(<>
      <WindowIdContext.Provider value="surface-meetings"><div data-testid="current-record"><HistoryCore scope="meeting:m-1" /></div></WindowIdContext.Provider>
      <WindowIdContext.Provider value="pullout:meeting:m-2"><div data-testid="other-record"><MeetingRecord meetingId="m-2" onClose={() => {}} /></div></WindowIdContext.Provider>
    </>);
    const current = within(screen.getByTestId("current-record"));
    const other = within(screen.getByTestId("other-record"));
    await current.findByTestId("meeting-toolbar");
    await other.findByTestId("meeting-toolbar");
    expect(screen.queryByTestId("meeting-send-well")).toBeNull();
    act(() => window.dispatchEvent(new CustomEvent(SEND_OPEN, { detail: { winId: "surface-unrelated" } })));
    expect(screen.queryByTestId("meeting-send-well")).toBeNull();
    act(() => window.dispatchEvent(new CustomEvent(SEND_OPEN, { detail: { winId: "surface-meetings" } })));
    await current.findByTestId("meeting-send-well");
    await waitFor(() => expect(current.getByTestId("send-well").getAttribute("data-doc")).toBe("meeting_summary:m-1"));
    expect(other.queryByTestId("meeting-send-well")).toBeNull();
    expect(screen.getAllByTestId("meeting-send-well")).toHaveLength(1);
  });
});

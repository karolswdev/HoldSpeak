// PHILO-13-02 (A1-F) — Park, never delete, on the Meetings face (C1 artboard
// "Parked and Restore", boards C1-5a–e). Park is ONE press with no confirm
// (Restore undoes it); the receipt says PARKED, never DELETED; the PARKED
// token is absent at zero; Restore brings the meeting back, marked; a refused
// Restore names it with Retry.
//
// PHILO-17 ("A meeting opens in one window"): Park is on the meeting's own
// window (MeetingRecord), the PARKED token and Restore are on the Meetings
// list (HistoryCore). The hub's desk change re-reads the list; here a window
// focus stands in for it.
//
// Rehomed fence: the old `Delete` / `Delete?` confirm verb and the
// `DELETED hh:mm` receipt are retired with the words (the hub's DELETE route
// now parks; H-A1, #727).
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "../../../../lib/api";
import { HistoryCore } from "../../HistoryCore";
import { MeetingRecord } from "../MeetingRecord";

vi.mock("../../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

const mockedApiFetch = vi.mocked(apiFetch);

const meeting = (id: string, title: string) => ({
  id,
  title,
  started_at: "2026-09-29T09:00:00Z",
  duration_seconds: 1800,
  capture_status: "finalized",
  intel_status: { state: "ready" },
  transcriptWords: 9,
  action_item_count: 0,
});

type Hub = { calls: Array<{ path: string; method: string }>; refuseRestore: boolean };

function wireHub(): Hub {
  const active = new Map([
    ["m-1", meeting("m-1", "Ledger cutover sync")],
    ["m-2", meeting("m-2", "Hiring debrief")],
  ]);
  const parked = new Map<string, ReturnType<typeof meeting>>();
  const hub: Hub = { calls: [], refuseRestore: false };
  mockedApiFetch.mockImplementation(async (path: string, init?: RequestInit) => {
    const url = String(path);
    const method = init?.method ?? "GET";
    hub.calls.push({ path: url, method });
    if (url === "/api/meetings?parked=true") return { meetings: [...parked.values()] } as never;
    if (url.startsWith("/api/meetings?") || url === "/api/meetings")
      return { meetings: [...active.values()] } as never;
    const del = url.match(/^\/api\/meetings\/([^/?]+)$/);
    if (del && method === "DELETE") {
      const row = active.get(del[1]);
      if (row) {
        active.delete(del[1]);
        parked.set(del[1], row);
      }
      return { parked: del[1] } as never;
    }
    const restore = url.match(/^\/api\/meetings\/([^/?]+)\/restore$/);
    if (restore && method === "POST") {
      if (hub.refuseRestore) throw new ApiError(500, "refused", {});
      const row = parked.get(restore[1]);
      if (row) {
        parked.delete(restore[1]);
        active.set(restore[1], row);
      }
      return { meeting: row } as never;
    }
    const read = url.match(/^\/api\/meetings\/([^/?]+)(\?include_parked=true)?$/);
    if (read) return (active.get(read[1]) ?? parked.get(read[1]) ?? {}) as never;
    return {} as never;
  });
  return hub;
}

/** The Meetings list and Hiring debrief's own window, side by side. */
function renderDesk() {
  return render(<><HistoryCore /><MeetingRecord meetingId="m-2" onClose={() => undefined} /></>);
}

/** The hub's desk change after a write: the list reads again. */
function hubChanged() {
  window.dispatchEvent(new Event("focus"));
}

async function selectAndPark(title: string) {
  await screen.findAllByText(title);
  fireEvent.click(await screen.findByRole("button", { name: "More actions" }));
  fireEvent.click(await screen.findByRole("menuitem", { name: "Park" }));
  const receipt = await screen.findByTestId("meeting-park-receipt");
  hubChanged();
  return receipt;
}

describe("PHILO-13-02 Park and Restore on Meetings", () => {
  beforeEach(() => mockedApiFetch.mockReset());

  it("Park is one press: no confirm, the hub parks, the receipt says PARKED + Restore", async () => {
    const hub = wireHub();
    renderDesk();
    expect(screen.queryByRole("button", { name: /Delete/ })).toBeNull();
    const receipt = await selectAndPark("Hiring debrief");
    expect(hub.calls.filter((c) => c.method === "DELETE").map((c) => c.path)).toEqual([
      "/api/meetings/m-2",
    ]);
    expect(within(receipt).getByRole("status").textContent).toMatch(/^PARKED \d\d:\d\d$/);
    expect(within(receipt).getByRole("button", { name: "Restore" })).toBeTruthy();
    expect(screen.queryByText(/DELETED/)).toBeNull();
    expect(screen.queryByRole("button", { name: "Delete?" })).toBeNull();
    // The row leaves the list.
    await waitFor(() => expect(screen.queryByTestId("meeting-row-m-2")).toBeNull());
  });

  it("the PARKED token is absent at zero; on, it lists the parked rows with Restore", async () => {
    wireHub();
    renderDesk();
    await screen.findAllByText("Hiring debrief");
    expect(screen.queryByText(/^PARKED \d+$/)).toBeNull();
    await selectAndPark("Hiring debrief");
    const token = await screen.findByText("PARKED 1");
    fireEvent.click(token);
    const row = await screen.findByTestId("parked-row");
    expect(row.textContent).toContain("Hiring debrief");
    expect(row.closest("li")?.textContent).toContain("PARKED");
    // The list gives way to the parked rows.
    expect(screen.queryByTestId("meeting-row-m-1")).toBeNull();
  });

  it("Restore brings the meeting back, marked, with RESTORED hh:mm; the token goes", async () => {
    const hub = wireHub();
    renderDesk();
    await selectAndPark("Hiring debrief");
    fireEvent.click(await screen.findByText("PARKED 1"));
    const row = await screen.findByTestId("parked-row");
    fireEvent.click(within(row.closest("li")!).getByRole("button", { name: "Restore" }));
    await waitFor(() =>
      expect(screen.getByTestId("meetings-park-receipt").textContent).toMatch(/^RESTORED \d\d:\d\d$/),
    );
    expect(hub.calls.some((c) => c.path === "/api/meetings/m-2/restore" && c.method === "POST")).toBe(true);
    const back = await screen.findByTestId("meeting-row-m-2");
    await waitFor(() => expect(back.getAttribute("data-restored")).toBe("true"));
    await waitFor(() => expect(screen.queryByText(/^PARKED \d+$/)).toBeNull());
  });

  it("a refused Restore names it with Retry; Retry restores", async () => {
    const hub = wireHub();
    renderDesk();
    const receipt = await selectAndPark("Hiring debrief");
    hub.refuseRestore = true;
    fireEvent.click(within(receipt).getByRole("button", { name: "Restore" }));
    await waitFor(() =>
      expect(screen.getByTestId("meeting-park-receipt").textContent).toContain(
        "NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE",
      ),
    );
    const failed = screen.getByTestId("meeting-park-receipt");
    expect(within(failed).getByRole("status").getAttribute("data-tone")).toBe("danger");
    hub.refuseRestore = false;
    fireEvent.click(within(failed).getByRole("button", { name: "Retry" }));
    await waitFor(() =>
      expect(screen.getByTestId("meeting-park-receipt").textContent).toMatch(/^RESTORED \d\d:\d\d$/),
    );
    hubChanged();
    await screen.findByTestId("meeting-row-m-2");
  });
});

// The test diet (2026-10-11): the reload half of the park glass. A reload is
// a fresh mount of the Meetings list over a hub that already holds the
// meeting parked: the row is absent, PARKED 1 comes from the hub's parked
// read, and Restore from the filter brings it back. The DB half (kept, parked,
// every retained row) is tests/unit/test_philo13_meeting_parking.py::
// test_real_import_route_parks_reads_retained_detail_and_restores.
// replaces: tests/e2e/test_philo13_02_park_glass.py::TestParkGlass::test_meeting_park_parked_filter_restore_and_reload
describe("PHILO-13-02 Meetings after a reload", () => {
  beforeEach(() => mockedApiFetch.mockReset());

  it("a fresh mount over a parked meeting: no row, PARKED 1, the parked row, Restore brings it back marked", async () => {
    const hub = wireHub();
    await apiFetch("/api/meetings/m-2", { method: "DELETE" });   // parked before the reload
    hub.calls.length = 0;
    render(<HistoryCore />);
    await screen.findByTestId("meeting-row-m-1");
    expect(screen.queryByTestId("meeting-row-m-2")).toBeNull();
    fireEvent.click(await screen.findByText("PARKED 1"));
    const row = await screen.findByTestId("parked-row");
    expect(row.textContent).toContain("Hiring debrief");
    expect(hub.calls.some((c) => c.path === "/api/meetings?parked=true")).toBe(true);
    fireEvent.click(within(row.closest("li")!).getByRole("button", { name: "Restore" }));
    await waitFor(() =>
      expect(screen.getByTestId("meetings-park-receipt").textContent).toMatch(/^RESTORED \d\d:\d\d$/),
    );
    const back = await screen.findByTestId("meeting-row-m-2");
    await waitFor(() => expect(back.getAttribute("data-restored")).toBe("true"));
    await waitFor(() => expect(screen.queryByText(/^PARKED \d+$/)).toBeNull());
    expect(hub.calls.filter((c) => c.method !== "GET")).toEqual([{ path: "/api/meetings/m-2/restore", method: "POST" }]);
  });
});

// PHILO-13-02 (A1-F) — Park, never delete, on the Meetings face (C1 artboard
// "Parked and Restore", boards C1-5a–e). Park is ONE press with no confirm
// (Restore undoes it); the receipt says PARKED, never DELETED; the PARKED
// token is absent at zero; Restore brings the meeting back, marked; a refused
// Restore names it with Retry.
//
// Rehomed fence: the old `Delete` / `Delete?` confirm verb and the
// `DELETED hh:mm` receipt are retired with the words (the hub's DELETE route
// now parks; H-A1, #727).
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "../../../../lib/api";
import { HistoryCore } from "../../HistoryCore";

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
    if (url.match(/^\/api\/meetings\/[^/?]+$/)) return { meeting: active.get(url.split("/").pop()!) } as never;
    return {} as never;
  });
  return hub;
}

async function selectAndPark(title: string) {
  fireEvent.click(await screen.findByText(title));
  fireEvent.click(await screen.findByRole("button", { name: "Park" }));
  return screen.findByTestId("meetings-park-receipt");
}

describe("PHILO-13-02 Park and Restore on Meetings", () => {
  beforeEach(() => mockedApiFetch.mockReset());

  it("Park is one press: no confirm, the hub parks, the receipt says PARKED + Restore", async () => {
    const hub = wireHub();
    render(<HistoryCore />);
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
    render(<HistoryCore />);
    await screen.findByText("Hiring debrief");
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
    render(<HistoryCore />);
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
    render(<HistoryCore />);
    const receipt = await selectAndPark("Hiring debrief");
    hub.refuseRestore = true;
    fireEvent.click(within(receipt).getByRole("button", { name: "Restore" }));
    await waitFor(() =>
      expect(screen.getByTestId("meetings-park-receipt").textContent).toContain(
        "NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE",
      ),
    );
    const failed = screen.getByTestId("meetings-park-receipt");
    expect(within(failed).getByRole("status").getAttribute("data-tone")).toBe("danger");
    hub.refuseRestore = false;
    fireEvent.click(within(failed).getByRole("button", { name: "Retry" }));
    await waitFor(() =>
      expect(screen.getByTestId("meetings-park-receipt").textContent).toMatch(/^RESTORED \d\d:\d\d$/),
    );
    await screen.findByTestId("meeting-row-m-2");
  });
});

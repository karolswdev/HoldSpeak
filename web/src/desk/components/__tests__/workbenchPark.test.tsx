/** PHILO-13-02 (A1-F) — the Workbench window's Park (C1 artboard "Parked and
 * Restore", boards C1-5f–j).
 *
 * Rehomed from workbenchUndoFlush.test.tsx (PHILO-8-02): Remove + an 8 s Undo
 * window that ended in a hard delete is retired. Park now sends at once (one
 * press, no countdown), the item is kept and parked by the hub, and Restore
 * undoes it. The old fence's three laws carry over onto park:
 *   - a second press never drops the first (each park is sent at once);
 *   - closing the window loses nothing (nothing is pending);
 *   - the undo verb keeps the item (Restore restores it).
 * New: the claimed refusal in place, bulk "Clear done", the PARKED filter. */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";

type Frame = { type: string; data: unknown };

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
}));

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, listener: (frame: Frame) => void) => {
      const set =
        mocks.listeners.get(type) ?? new Set<(frame: Frame) => void>();
      set.add(listener);
      mocks.listeners.set(type, set);
      return () => set.delete(listener);
    },
  }),
  useRuntimeFrame: () => null,
}));

import { WorkbenchWindow } from "../WorkbenchWindow";

type Item = { id: string; title: string; body: string; status: string; priority: number; result: null; parked?: boolean; last_modified?: string };

function mockHub(statuses: Record<string, string> = {}) {
  const item = (id: string, title: string): Item => ({
    id, title, body: "", status: statuses[id] ?? "pending", priority: 3, result: null,
  });
  const items: Item[] = [item("i1", "First item"), item("i2", "Second item"), item("i3", "Third item")];
  const hub = {
    requests: [] as Array<{ method: string; url: string; body?: unknown }>,
    claimed: new Set<string>(),
    refuseRestore: false,
  };
  const wb = () => ({
    id: "wb1", name: "Test WB", recipe_id: null, profile_id: null,
    resolver_profile_id: null, schedule: null, schedule_enabled: false,
    items: items.filter((i) => !i.parked), last_run: null,
  });
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    if (method !== "GET" && url.includes("/api/workbenches/")) hub.requests.push({ method, url: url.replace(/^.*\/api\//, "/api/"), body });
    const park = (ids: string[], parked: boolean) => {
      for (const id of ids) {
        const it = items.find((i) => i.id === id);
        if (it) { it.parked = parked; it.last_modified = new Date().toISOString(); }
      }
    };
    let m = url.match(/\/api\/workbenches\/wb1\/items\/([^/]+)$/);
    if (m && method === "DELETE") {
      if (hub.claimed.has(m[1])) return json({ error: "Workbench item is claimed by a run" }, 409);
      park([m[1]], true);
      return json({ success: true, parked: m[1] });
    }
    if (/\/items\/park$/.test(url)) { park(body.item_ids, true); return json({ parked: body.item_ids }); }
    if (/\/items\/restore$/.test(url)) {
      if (hub.refuseRestore) return json({ error: "no" }, 500);
      park(body.item_ids, false);
      return json({ restored: body.item_ids });
    }
    m = url.match(/\/items\/([^/]+)\/restore$/);
    if (m) { park([m[1]], false); return json({ item: items.find((i) => i.id === m![1]) }); }
    if (/\/runs$/.test(url)) return json({ runs: [] });
    if (/\/memory$/.test(url)) return json({ entries: [] });
    if (/\/api\/skills/.test(url)) return json({ skills: [] });
    if (/\/api\/workbenches\/wb1\?parked=true$/.test(url))
      return json({ workbench: { ...wb(), items: items.filter((i) => i.parked) } });
    if (/\/api\/workbenches\/wb1$/.test(url)) return json({ workbench: wb() });
    return json({});
  });
  vi.stubGlobal("fetch", fetchMock);
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      workbench: [{ kind: "workbench", id: "wb1", name: "Test WB" } as never],
    },
    inferenceTargets: [],
    profiles: [],
  });
  return hub;
}

async function parkItem(title: string) {
  const head = await screen.findByText(title);
  fireEvent.click(head.closest("button")!);
  fireEvent.click(await screen.findByRole("button", { name: "Park" }));
}

const receipt = () => screen.findByTestId("wb-park-receipt");

describe("PHILO-13-02 the Workbench window's Park", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.listeners.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("Park sends at once (no Remove, no Undo countdown) and says PARKED + Restore", async () => {
    const hub = mockHub();
    render(<WorkbenchWindow workbenchId="wb1" />);
    await screen.findByText("First item");
    expect(screen.queryByRole("button", { name: "Remove" })).toBeNull();
    await parkItem("First item");
    await waitFor(() =>
      expect(hub.requests).toEqual([{ method: "DELETE", url: "/api/workbenches/wb1/items/i1", body: undefined }]),
    );
    const r = await receipt();
    expect(within(r).getByRole("status").textContent).toMatch(/^PARKED \d\d:\d\d$/);
    expect(within(r).getByRole("button", { name: "Restore" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Undo" })).toBeNull();
    await waitFor(() => expect(screen.queryByText("First item")).toBeNull());
  });

  it("a second Park never drops the first; closing the window loses nothing", async () => {
    const hub = mockHub();
    const view = render(<WorkbenchWindow workbenchId="wb1" />);
    await parkItem("First item");
    await waitFor(() => expect(hub.requests.length).toBe(1));
    await parkItem("Second item");
    await waitFor(() =>
      expect(hub.requests.map((r) => r.url)).toEqual([
        "/api/workbenches/wb1/items/i1",
        "/api/workbenches/wb1/items/i2",
      ]),
    );
    view.unmount();
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(hub.requests.length).toBe(2);
  });

  it("Restore keeps the item: RESTORED hh:mm, the item back in the list, marked", async () => {
    const hub = mockHub();
    render(<WorkbenchWindow workbenchId="wb1" />);
    await parkItem("First item");
    fireEvent.click(within(await receipt()).getByRole("button", { name: "Restore" }));
    await waitFor(async () =>
      expect((await receipt()).textContent).toMatch(/^RESTORED \d\d:\d\d$/),
    );
    expect(hub.requests.at(-1)).toEqual({
      method: "POST", url: "/api/workbenches/wb1/items/restore", body: { item_ids: ["i1"] },
    });
    const back = await screen.findByText("First item");
    await waitFor(() => expect(back.closest(".wb-card")?.getAttribute("data-restored")).toBe("true"));
  });

  it("the PARKED token is absent at zero; on, the parked rows with Restore replace the items", async () => {
    mockHub();
    render(<WorkbenchWindow workbenchId="wb1" />);
    await screen.findByText("First item");
    expect(screen.queryByText(/^PARKED \d+$/)).toBeNull();
    await parkItem("First item");
    fireEvent.click(await screen.findByText("PARKED 1"));
    const row = await screen.findByTestId("parked-row");
    expect(row.textContent).toContain("First item");
    expect(screen.queryByText("Second item")).toBeNull();
    fireEvent.click(within(row.closest("li")!).getByRole("button", { name: "Restore" }));
    await screen.findByText("Second item");
    await screen.findByText("First item");
    await waitFor(() => expect(screen.queryByText(/^PARKED \d+$/)).toBeNull());
  });

  it("a claimed item is refused in place: NOT PARKED · CLAIMED BY A RUN, no Restore", async () => {
    const hub = mockHub();
    hub.claimed.add("i1");
    render(<WorkbenchWindow workbenchId="wb1" />);
    await parkItem("First item");
    const r = await receipt();
    const line = within(r).getByRole("status");
    expect(line.textContent).toBe("NOT PARKED · CLAIMED BY A RUN");
    expect(line.getAttribute("data-tone")).toBe("danger");
    expect(within(r).queryByRole("button", { name: "Restore" })).toBeNull();
    expect(screen.getByText("First item")).toBeTruthy();
  });

  it("Clear done parks every done item at once: one bulk request, PARKED 2 · hh:mm, Restore restores all", async () => {
    const hub = mockHub({ i1: "done", i3: "dismissed" });
    render(<WorkbenchWindow workbenchId="wb1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Clear done" }));
    await waitFor(() =>
      expect(hub.requests).toEqual([
        { method: "POST", url: "/api/workbenches/wb1/items/park", body: { item_ids: ["i1", "i3"] } },
      ]),
    );
    const r = await receipt();
    expect(within(r).getByRole("status").textContent).toMatch(/^PARKED 2 · \d\d:\d\d$/);
    await waitFor(() => expect(screen.queryByRole("button", { name: "Clear done" })).toBeNull());
    fireEvent.click(within(r).getByRole("button", { name: "Restore" }));
    await waitFor(() =>
      expect(hub.requests.at(-1)).toEqual({
        method: "POST", url: "/api/workbenches/wb1/items/restore", body: { item_ids: ["i1", "i3"] },
      }),
    );
  });

  it("a refused Restore names it with Retry", async () => {
    const hub = mockHub();
    render(<WorkbenchWindow workbenchId="wb1" />);
    await parkItem("First item");
    hub.refuseRestore = true;
    fireEvent.click(within(await receipt()).getByRole("button", { name: "Restore" }));
    await waitFor(async () =>
      expect((await receipt()).textContent).toContain("NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE"),
    );
    hub.refuseRestore = false;
    fireEvent.click(within(await receipt()).getByRole("button", { name: "Retry" }));
    await waitFor(async () => expect((await receipt()).textContent).toMatch(/^RESTORED/));
  });
});

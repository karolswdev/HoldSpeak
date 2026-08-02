/** HS-112-03 — the reset-to-seed store contract: the wire call first,
 * and ONLY on success the ghost-layout sweep (every localStorage key
 * the pre-charter survey named) + the in-memory settle + refresh. A
 * refused reset touches nothing. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GHOST_LAYOUT_KEYS, useDesk } from "../store";

const ok = (body: Record<string, unknown>) =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });

describe("resetDesk / seedDesk (HS-112-03)", () => {
  const refresh = vi.fn(async () => {});

  beforeEach(() => {
    localStorage.clear();
    refresh.mockClear();
    useDesk.setState({ refresh });
  });
  afterEach(() => vi.unstubAllGlobals());

  it("names every ghost layout key the survey found", () => {
    expect([...GHOST_LAYOUT_KEYS]).toEqual([
      "hs.diorama.pos",
      "hs.desk.panels",
      "hs.desk.zonew",
      "hs.desk.zone-views",
      "hs.desk.zone-windows",
      "hs.desk.open-windows",
    ]);
  });

  it("a successful reset sweeps the keys, settles the store, refreshes", async () => {
    for (const key of GHOST_LAYOUT_KEYS)
      localStorage.setItem(key, JSON.stringify({ ghost: true }));
    useDesk.setState({
      positions: { dead: { x: 0.1, y: 0.2 } },
      panelOrder: ["surface-dead"],
      selectedIds: ["dead"],
      divedZone: "dead-zone",
    });
    const fetchMock = vi.fn(async () =>
      ok({ success: true, tombstoned_total: 7, seeded_total: 8 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const counts = await useDesk.getState().resetDesk();

    expect(counts).toEqual({ tombstoned: 7, seeded: 8 });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/desk/reset",
      expect.objectContaining({ method: "POST" }),
    );
    for (const key of GHOST_LAYOUT_KEYS)
      expect(localStorage.getItem(key)).toBeNull();
    const state = useDesk.getState();
    expect(state.positions).toEqual({});
    expect(state.panelOrder).toEqual([]);
    expect(state.selectedIds).toEqual([]);
    expect(state.divedZone).toBeNull();
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("a refused reset touches nothing", async () => {
    localStorage.setItem("hs.diorama.pos", "{}");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("{}", { status: 401 })),
    );
    expect(await useDesk.getState().resetDesk()).toBeNull();
    expect(localStorage.getItem("hs.diorama.pos")).toBe("{}");
    expect(refresh).not.toHaveBeenCalled();
  });

  it("seedDesk posts the seed and refreshes (additive; no sweep)", async () => {
    localStorage.setItem("hs.diorama.pos", "{}");
    const fetchMock = vi.fn(async () => ok({ success: true, total: 8 }));
    vi.stubGlobal("fetch", fetchMock);
    expect(await useDesk.getState().seedDesk()).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/desk/seed",
      expect.objectContaining({ method: "POST" }),
    );
    expect(localStorage.getItem("hs.diorama.pos")).toBe("{}"); // untouched
    expect(refresh).toHaveBeenCalledTimes(1);
  });
});

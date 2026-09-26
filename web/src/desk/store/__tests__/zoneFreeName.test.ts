/** PHILO-8-01 — the free default zone name (the owner's Q1 (a)).
 *
 * The hub refuses a second live zone whose name matches after strip, collapse
 * whitespace, NFC and casefold (holdspeak/db/primitives.py:60-68). New Zone
 * posted "New zone" every time, so the second press answered 409 (FINDING S1).
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../../../lib/api";

vi.mock("../../../lib/api", () => ({
  apiRequest: vi.fn(),
  apiFetch: vi.fn(() => Promise.resolve({})),
  newDeliveryId: vi.fn(() => "d"),
}));

import { useDesk } from "../../store";
import { currentWriteFailure } from "../../hooks/useWriteReceipt";
import { nextFreeZoneName, normalizeZoneName, noteFaceChange } from "../../zoneName";

const zone = (name: string, nameNormalized = "") =>
  ({ kind: "directory", id: `dir_${name}`, name, nameNormalized, memberIds: [], createdAt: "" }) as const;

function posted(): Array<Record<string, unknown>> {
  return vi
    .mocked(apiRequest)
    .mock.calls.filter(([url, init]) => url === "/api/directories" && init?.method === "POST")
    .map(([, init]) => JSON.parse(String(init!.body)));
}

const ok = (id: string) =>
  Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ directory: { id } }) } as Response);
const taken = () =>
  Promise.resolve({
    ok: false,
    status: 409,
    json: () => Promise.resolve({ error: "zone_name_taken", existing_name: "New zone" }),
    text: () => Promise.resolve('{"error":"zone_name_taken"}'),
    clone() { return this; },
  } as unknown as Response);

describe("nextFreeZoneName — the hub's rule in full", () => {
  it("names the first zone 'New zone'", () => {
    expect(nextFreeZoneName([])).toBe("New zone");
  });
  it("names the next one 'New zone 2', then 3", () => {
    expect(nextFreeZoneName([zone("New zone")])).toBe("New zone 2");
    expect(nextFreeZoneName([zone("New zone"), zone("New zone 2")])).toBe("New zone 3");
  });
  it("counts case and whitespace variants as taken ('  new   ZONE ')", () => {
    expect(nextFreeZoneName([zone("  new   ZONE ")])).toBe("New zone 2");
    expect(nextFreeZoneName([zone("New zone"), zone("new\tzone  2")])).toBe("New zone 3");
  });
  it("counts the hub's own name_normalized", () => {
    expect(nextFreeZoneName([zone("anything", "new zone")])).toBe("New zone 2");
  });
  it("fills a gap: a zone named 'New zone 2' by the owner is skipped, not renamed", () => {
    expect(nextFreeZoneName([zone("New zone 2")])).toBe("New zone");
    expect(nextFreeZoneName([zone("New zone"), zone("New zone 2"), zone("New zone 4")])).toBe("New zone 3");
  });
  it("matches normalize_zone_name on NFC and casefold", () => {
    expect(normalizeZoneName("  Café   ZONE ")).toBe("café zone");
    expect(normalizeZoneName("Straße")).toBe(normalizeZoneName("STRASSE"));
  });
});

describe("createPrimitive('zone') — the free name, the passed name, the Retry", () => {
  let refresh: ReturnType<typeof vi.fn<() => Promise<void>>>;
  beforeEach(() => {
    vi.mocked(apiRequest).mockReset();
    refresh = vi.fn<() => Promise<void>>(() => Promise.resolve());
    useDesk.setState({
      refresh,
      renamingZoneId: null,
      items: { ...useDesk.getState().items, directory: [zone("New zone")] as never },
    });
  });

  it("posts the next free name when a 'New zone' exists", async () => {
    vi.mocked(apiRequest).mockImplementation(() => ok("dir_new"));
    await useDesk.getState().createPrimitive("zone");
    expect(posted()).toEqual([{ name: "New zone 2" }]);
    expect(useDesk.getState().renamingZoneId).toBe("dir_new");
  });

  it("two quick presses (the first refresh still running) post two names", async () => {
    // The rig measured the post-create refresh at ~4.7 s at 1440: a second
    // press inside it read a store without the first zone and posted the
    // same name (409).
    let landFirst: () => void = () => undefined;
    refresh.mockImplementationOnce(() => new Promise<void>((resolve) => { landFirst = resolve; }));
    vi.mocked(apiRequest).mockImplementation(() => ok("dir_q"));
    const first = useDesk.getState().createPrimitive("zone");
    await vi.waitFor(() => expect(refresh).toHaveBeenCalled());
    await useDesk.getState().createPrimitive("zone");
    landFirst();
    await first;
    expect(posted()).toEqual([{ name: "New zone 2" }, { name: "New zone 3" }]);
  });

  it("a face change while the create lands starts no rename on the new face", async () => {
    let land: () => void = () => undefined;
    refresh.mockImplementationOnce(() => new Promise<void>((resolve) => { land = resolve; }));
    vi.mocked(apiRequest).mockImplementation(() => ok("dir_late"));
    const pending = useDesk.getState().createPrimitive("zone");
    await vi.waitFor(() => expect(refresh).toHaveBeenCalled());
    noteFaceChange();
    land();
    await pending;
    expect(useDesk.getState().renamingZoneId).toBeNull();
  });

  it("never replaces a name the caller passed", async () => {
    vi.mocked(apiRequest).mockImplementation(() => ok("dir_x"));
    await useDesk.getState().createPrimitive("zone", { name: "X" });
    await useDesk.getState().createPrimitive("zone", { name: "New zone" });
    expect(posted()).toEqual([{ name: "X" }, { name: "New zone" }]);
  });

  it("after a 409, Retry refreshes the store BEFORE it picks again", async () => {
    // A zone made outside the store (MCP, another tab): the hub holds
    // "New zone 2", the store does not know it yet.
    vi.mocked(apiRequest).mockImplementationOnce(() => taken());
    await useDesk.getState().createPrimitive("zone");
    expect(posted()).toEqual([{ name: "New zone 2" }]);
    const failure = currentWriteFailure();
    expect(failure?.verb).toBe("CREATE ZONE");
    expect(failure?.retry).toBeTypeOf("function");

    // Refresh brings the outside zone in; Retry must pick after it.
    refresh.mockImplementation(() => {
      useDesk.setState({
        items: { ...useDesk.getState().items, directory: [zone("New zone"), zone("New zone 2")] as never },
      });
      return Promise.resolve();
    });
    refresh.mockClear();
    vi.mocked(apiRequest).mockImplementation(() => ok("dir_3"));
    failure!.retry!();
    await vi.waitFor(() => expect(posted()).toHaveLength(2));
    expect(refresh.mock.invocationCallOrder[0]).toBeLessThan(
      vi.mocked(apiRequest).mock.invocationCallOrder.at(-1)!,
    );
    expect(posted()[1]).toEqual({ name: "New zone 3" });
  });
});

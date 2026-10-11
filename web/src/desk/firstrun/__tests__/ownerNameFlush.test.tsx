// PHILO-17 words: a reload inside the 600 ms save delay lost the edit. When
// the page hides, the pending edit goes out at once, with keepalive.
import { act, cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useOwnerName } from "../ownerName";

let owner: ReturnType<typeof useOwnerName>;
function Probe() {
  owner = useOwnerName();
  return null;
}

let calls: Array<{ method: string; body: unknown; keepalive?: boolean }>;
beforeEach(() => {
  calls = [];
  vi.stubGlobal("fetch", vi.fn(async (_url: string, init?: RequestInit) => {
    const method = (init?.method || "GET").toUpperCase();
    calls.push({ method, body: init?.body ? JSON.parse(String(init.body)) : null, keepalive: init?.keepalive });
    const body = method === "PUT" ? { settings: JSON.parse(String(init!.body)) } : { owner: { name: "Karl", aliases: [] } };
    return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });

const puts = () => calls.filter((c) => c.method === "PUT");

describe("useOwnerName flushes on page leave", () => {
  it("pagehide inside the delay sends the pending edit at once, with keepalive", async () => {
    render(<Probe />);
    await act(async () => { await Promise.resolve(); });
    act(() => { owner.setName("Karol Sane"); owner.addAliases("Carol"); });
    expect(puts()).toEqual([]);
    await act(async () => { window.dispatchEvent(new Event("pagehide")); });
    expect(puts()).toEqual([{ method: "PUT", body: { owner: { name: "Karol Sane", aliases: ["Carol"] } }, keepalive: true }]);
  });

  it("a hidden tab flushes too; nothing pending sends nothing", async () => {
    render(<Probe />);
    await act(async () => { await Promise.resolve(); });
    const hide = () => {
      Object.defineProperty(document, "visibilityState", { configurable: true, get: () => "hidden" });
      document.dispatchEvent(new Event("visibilitychange"));
    };
    await act(async () => { hide(); });
    expect(puts()).toEqual([]);
    act(() => { owner.setName("Karol"); });
    await act(async () => { hide(); });
    expect(puts()).toHaveLength(1);
    expect(puts()[0].keepalive).toBe(true);
    // Sent once: a second hide has nothing pending.
    await act(async () => { hide(); });
    expect(puts()).toHaveLength(1);
    Object.defineProperty(document, "visibilityState", { configurable: true, get: () => "visible" });
  });
});

describe("Astra r2 on #1090: owner saves are newest-wins", () => {
  it("A in flight → edit B → hide → A lands after B: the hub keeps B", async () => {
    // A tiny hub: last-writer-wins without a revision, 409 on a stale one.
    const hub = { owner: { name: "Karl", aliases: [] as string[] }, revision: "r1" };
    let rev = 1;
    const held: Array<() => void> = [];
    vi.stubGlobal("fetch", vi.fn((_url: string, init?: RequestInit) => {
      const method = (init?.method || "GET").toUpperCase();
      if (method === "GET") {
        return Promise.resolve(new Response(JSON.stringify({ owner: hub.owner, _revision: hub.revision }),
          { status: 200, headers: { "content-type": "application/json" } }));
      }
      const body = JSON.parse(String(init!.body));
      calls.push({ method, body, keepalive: init?.keepalive });
      const apply = () => {
        if (body._revision && body._revision !== hub.revision) {
          return new Response(JSON.stringify({ success: false, error: "stale", revision: hub.revision }),
            { status: 409, headers: { "content-type": "application/json" } });
        }
        hub.owner = body.owner;
        hub.revision = `r${++rev}`;
        return new Response(JSON.stringify({ settings: { owner: hub.owner, _revision: hub.revision } }),
          { status: 200, headers: { "content-type": "application/json" } });
      };
      // The first PUT (A) is held until the test releases it; later ones land at once.
      if (calls.filter((c) => c.method === "PUT").length === 1) {
        return new Promise<Response>((resolve) => held.push(() => resolve(apply())));
      }
      return Promise.resolve(apply());
    }));
    vi.useFakeTimers();
    render(<Probe />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });

    act(() => { owner.setName("Karol A"); });
    await act(async () => { await vi.advanceTimersByTimeAsync(600); }); // A sent, held
    expect(puts()).toHaveLength(1);
    act(() => { owner.setName("Karol B"); });
    await act(async () => { window.dispatchEvent(new Event("pagehide")); }); // B sent now
    expect(puts()[1]).toMatchObject({ body: { owner: { name: "Karol B" } }, keepalive: true });
    expect(hub.owner.name).toBe("Karol B");

    await act(async () => { held[0](); await vi.advanceTimersByTimeAsync(0); }); // A lands after B
    expect(hub.owner.name).toBe("Karol B");
  });

  it("a new edit while a save is in flight waits, then sends only the newest value", async () => {
    const releases: Array<() => void> = [];
    vi.stubGlobal("fetch", vi.fn((_url: string, init?: RequestInit) => {
      const method = (init?.method || "GET").toUpperCase();
      const ok = (body: unknown) => new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
      if (method === "GET") return Promise.resolve(ok({ owner: { name: "Karl", aliases: [] } }));
      const body = JSON.parse(String(init!.body));
      calls.push({ method, body, keepalive: init?.keepalive });
      return new Promise<Response>((resolve) => releases.push(() => resolve(ok({ settings: body }))));
    }));
    vi.useFakeTimers();
    render(<Probe />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    act(() => { owner.setName("One"); });
    await act(async () => { await vi.advanceTimersByTimeAsync(600); });
    act(() => { owner.setName("Two"); });
    await act(async () => { await vi.advanceTimersByTimeAsync(600); });
    act(() => { owner.setName("Three"); });
    await act(async () => { await vi.advanceTimersByTimeAsync(600); });
    expect(puts()).toHaveLength(1); // one in flight
    await act(async () => { releases[0](); await vi.advanceTimersByTimeAsync(0); });
    expect(puts().map((c) => (c.body as { owner: { name: string } }).owner.name)).toEqual(["One", "Three"]);
  });

  it("Enter an alias, then leave the editor at once (« Settings): the alias is sent", async () => {
    const view = render(<Probe />);
    await act(async () => { await Promise.resolve(); });
    act(() => { owner.addAliases("Carol"); });
    expect(puts()).toEqual([]);
    view.unmount();
    expect(puts()).toEqual([{ method: "PUT", body: { owner: { name: "Karl", aliases: ["Carol"] } }, keepalive: true }]);
  });
});

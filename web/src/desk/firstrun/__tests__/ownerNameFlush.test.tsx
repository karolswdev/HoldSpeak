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

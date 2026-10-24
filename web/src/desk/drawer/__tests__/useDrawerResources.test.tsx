import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { useAgentFlights } from "../../agentFlights";
import { useDrawers } from "../store";
import { useDrawerMembers, useProjectResourceRefs } from "../useDrawerData";
import type { useProjectRoomController } from "../../../features/project-room/useProjectRoomController";

const apiFetch = vi.hoisted(() => vi.fn());
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../runtime/RuntimeBus", () => {
  const bus = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => bus, useOptionalRuntimeBus: () => bus, useRuntimeFrame: () => null };
});

type Controller = ReturnType<typeof useProjectRoomController>;
const ctrl = {
  projectName: "Atlas Review", room: null, meetings: [], decisions: [], artifacts: [],
  error: null, detailStatus: "ready", loadStatus: "ready", load: vi.fn(),
} as unknown as Controller;

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

beforeEach(() => {
  apiFetch.mockReset();
  apiFetch.mockImplementation((url: string) => {
    if (url.endsWith("/people")) return Promise.resolve({ people: [] });
    if (url.startsWith("/api/coders/sessions")) return Promise.resolve({ sessions: [], flights: [] });
    return Promise.resolve({ resources: [] });
  });
  useDesk.setState({ items: EMPTY_ITEMS });
  useAgentFlights.setState({ sessions: [], flights: [], settled: true, loaded: true });
  useDrawers.setState({ revision: 0 });
});

describe("Project resource read boundary", () => {
  it("exposes live raw filed refs even when the derived Desk members omit an uncached Note", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.endsWith("/resources")) return Promise.resolve({ resources: [
        { resource_ref: "note:uncached" }, { resource_ref: "note:old", deleted: true },
      ] });
      if (url.endsWith("/people")) return Promise.resolve({ people: [] });
      return Promise.resolve({ sessions: [], flights: [] });
    });
    const { result } = renderHook(() => useDrawerMembers("atlas", ctrl));
    await waitFor(() => expect(result.current.resourcesState).toBe("ok"));
    expect(result.current.resourceRefs).toEqual(["note:uncached"]);
    expect(result.current.members.find((row) => row.ref === "note:uncached")).toBeUndefined();
  });

  it("retains the last successful resource refs on failure, then recovers with Retry", async () => {
    let resources: unknown = { resources: [{ resource_ref: "note:kept" }] };
    apiFetch.mockImplementation((url: string) => {
      if (url.endsWith("/resources")) return resources instanceof Error ? Promise.reject(resources) : Promise.resolve(resources);
      if (url.endsWith("/people")) return Promise.resolve({ people: [] });
      return Promise.resolve({ sessions: [], flights: [] });
    });
    const { result } = renderHook(() => useDrawerMembers("atlas", ctrl));
    await waitFor(() => expect(result.current.resourceRefs).toEqual(["note:kept"]));
    resources = new Error("offline");
    await act(async () => { expect((await result.current.refreshResources()).state).toBe("failed"); });
    expect(result.current.resourcesState).toBe("failed");
    expect(result.current.resourceRefs).toEqual(["note:kept"]);
    expect(result.current.failed).toContain("RESOURCES");
    resources = { resources: [{ resource_ref: "note:new" }] };
    await act(async () => { expect((await result.current.refreshResources()).state).toBe("ok"); });
    expect(result.current.resourcesState).toBe("ok");
    expect(result.current.resourceRefs).toEqual(["note:new"]);
  });

  it("fences an old Project's late resource response after the Room scope changes", async () => {
    const old = deferred<{ resources: { resource_ref: string }[] }>();
    apiFetch.mockImplementation((url: string) => {
      if (url === "/api/projects/old/resources") return old.promise;
      if (url === "/api/projects/new/resources") return Promise.resolve({ resources: [{ resource_ref: "note:new" }] });
      if (url.endsWith("/people")) return Promise.resolve({ people: [] });
      return Promise.resolve({ sessions: [], flights: [] });
    });
    const { result, rerender } = renderHook(({ projectId }) => useDrawerMembers(projectId, ctrl),
      { initialProps: { projectId: "old" } });
    rerender({ projectId: "new" });
    await waitFor(() => expect(result.current.resourceRefs).toEqual(["note:new"]));
    await act(async () => old.resolve({ resources: [{ resource_ref: "note:old" }] }));
    expect(result.current.resourceRefs).toEqual(["note:new"]);
    expect(result.current.resourcesState).toBe("ok");
  });

  it("follows two superseded resource reads to the current successful membership", async () => {
    const first = deferred<{ resources: { resource_ref: string }[] }>();
    const second = deferred<{ resources: { resource_ref: string }[] }>();
    const third = deferred<{ resources: { resource_ref: string }[] }>();
    let calls = 0;
    apiFetch.mockImplementation((url: string) => {
      if (!url.endsWith("/resources")) return Promise.resolve({ resources: [] });
      calls += 1;
      return calls === 1 ? Promise.resolve({ resources: [] })
        : calls === 2 ? first.promise : calls === 3 ? second.promise : third.promise;
    });
    const { result } = renderHook(() => useProjectResourceRefs("atlas"));
    await waitFor(() => expect(result.current.resourcesState).toBe("ok"));
    let followed!: Promise<Awaited<ReturnType<typeof result.current.refreshResources>>>;
    await act(async () => {
      followed = result.current.refreshResources().then(result.current.followCurrentResources);
      void result.current.refreshResources();
    });
    await act(async () => first.resolve({ resources: [{ resource_ref: "note:old" }] }));
    await act(async () => { void result.current.refreshResources(); });
    await act(async () => second.resolve({ resources: [{ resource_ref: "note:also-old" }] }));
    await act(async () => third.resolve({ resources: [{ resource_ref: "note:current" }] }));
    await expect(followed).resolves.toEqual({ state: "ok", refs: ["note:current"] });
    expect(result.current.resourceRefs).toEqual(["note:current"]);
  });
});

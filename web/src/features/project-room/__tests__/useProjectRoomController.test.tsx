// HS-158-05 — controller state discrimination tests.  Verifies the
// discriminated loadStatus lifecycle (WEB-ARC-003) without duplicating
// the rendered-UI coverage in projectMemoryCore.test.tsx.

import { renderHook, waitFor, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useProjectRoomController, type LoadStatus } from "../useProjectRoomController";

const apiFetchMock = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual =
    await vi.importActual<typeof import("../../../lib/api")>(
      "../../../lib/api",
    );
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetchMock(...args) };
});

vi.mock("../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/shell")>(
    "../../../desk/shell",
  );
  return { ...actual, openPrimitive: vi.fn(), openSurfaceOr: vi.fn() };
});

vi.mock("../../../desk/surface/wings", async () => {
  const actual =
    await vi.importActual<typeof import("../../../desk/surface/wings")>(
      "../../../desk/surface/wings",
    );
  return { ...actual, useWindowWings: vi.fn() };
});

function response(url: string) {
  if (url.includes("/projects/") && !url.includes("/meetings") && !url.includes("/artifacts") && !url.includes("/since"))
    return { id: "p1", name: "Test project" };
  if (url.includes("/meetings")) return { meetings: [{ id: "m1", title: "Review", started_at: "2026-07-29T10:00:00Z" }] };
  if (url.startsWith("/api/decisions")) return { decisions: [{ id: "d1", text: "Keep it", lifecycle: "recorded" }] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting")) return { current_meeting: { id: "m1" } };
  return {};
}

beforeEach(() => {
  apiFetchMock.mockImplementation((url: string) => Promise.resolve(response(url)));
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("useProjectRoomController — loadStatus discrimination", () => {
  it("starts idle when no scope is provided", () => {
    const { result } = renderHook(() => useProjectRoomController(undefined, undefined));
    expect(result.current.loadStatus).toBe("idle" satisfies LoadStatus);
    expect(result.current.projectId).toBe("");
  });

  it("starts loading when a scope is provided", () => {
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    // On mount, before the effect fires, loadStatus is already "loading"
    expect(result.current.loadStatus).toBe("loading" satisfies LoadStatus);
  });

  it("transitions to ready after a successful load", async () => {
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    await waitFor(() => expect(result.current.loadStatus).toBe("ready" satisfies LoadStatus));
    expect(result.current.error).toBe("");
    expect(result.current.projectName).toBe("Test project");
    expect(result.current.timeline.length).toBeGreaterThan(0);
    expect(result.current.readAt).toBeGreaterThan(0);
  });

  it("transitions to ready with error on a failed load", async () => {
    apiFetchMock.mockRejectedValue(new Error("Server down"));
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    await waitFor(() => expect(result.current.loadStatus).toBe("ready" satisfies LoadStatus));
    expect(result.current.error).toBe("Server down");
  });

  it("calls all five endpoints in the fan-out", async () => {
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    await waitFor(() => expect(result.current.loadStatus).toBe("ready"));
    expect(apiFetchMock).toHaveBeenCalledTimes(5);
    const urls = apiFetchMock.mock.calls.map((c: unknown[]) => c[0] as string);
    expect(urls).toContainEqual(expect.stringContaining("/api/projects/p1"));
    expect(urls).toContainEqual(expect.stringContaining("/meetings"));
    expect(urls).toContainEqual(expect.stringContaining("/decisions"));
    expect(urls).toContainEqual(expect.stringContaining("/artifacts"));
    expect(urls).toContainEqual(expect.stringContaining("/since-last-meeting"));
  });

  it("computes timeline from loaded data", async () => {
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    await waitFor(() => expect(result.current.loadStatus).toBe("ready"));
    const kinds = result.current.timeline.map((e) => e.kind);
    expect(kinds).toContain("meeting");
    expect(kinds).toContain("decision");
  });

  it("exposes view and setView from the wings", async () => {
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    expect(result.current.view).toBe("timeline");
    act(() => result.current.setView("decisions"));
    expect(result.current.view).toBe("decisions");
  });
});

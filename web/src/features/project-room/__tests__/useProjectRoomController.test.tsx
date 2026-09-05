// HS-158-05 — controller state discrimination tests. Verifies the
// discriminated loadStatus lifecycle (WEB-ARC-003) and that the first
// render uses /room (one request), with legacy detail fetches as
// progressive follow-ups.

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

/** A well-formed /room response. */
function roomResponse() {
  return {
    project_id: "p1",
    revision: 1,
    observed_at: "2026-08-31T10:00:00",
    project: {
      id: "p1",
      name: "Test project",
      description: null,
      is_archived: false,
      meeting_count: 1,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-08-31T10:00:00",
      purpose: null,
      outcome_text: null,
      owner_ref: null,
      lifecycle: "active",
      posture: null,
      posture_reason: null,
      start_at: null,
      target_at: null,
      revision: 1,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 1, latest: { id: "m1", title: "Review" } },
    resources: { state: "ok", count: 0, latest: null },
    changes: { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    // HS-169-04: the four questions
    needsYou: { state: "ok", items: [], count: 0 },
    sources: { state: "ok", items: [], count: 0 },
    health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
    sinceRead: { state: "ok", readAt: null, groups: [] },
    decisions: { state: "ok", items: [] },
    commitments: { state: "ok", items: [] },
    target: { state: "absent", reason: "none" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

function detailResponse(url: string) {
  if (url.includes("/meetings")) return { meetings: [{ id: "m1", title: "Review", started_at: "2026-07-29T10:00:00Z" }] };
  if (url.startsWith("/api/decisions")) return { decisions: [{ id: "d1", text: "Keep it", lifecycle: "recorded" }] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting")) return { current_meeting: { id: "m1" } };
  return {};
}

function response(url: string) {
  if (url.includes("/room")) return roomResponse();
  return detailResponse(url);
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
    // HS-169-03: readAt is now a string (ISO) or null from the wire.
    // When sinceRead is absent on the wire, readAt stays null.
    expect(result.current.readAt).toBeNull();
  });

  it("transitions to ready with error on a failed load", async () => {
    apiFetchMock.mockRejectedValue(new Error("Server down"));
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    await waitFor(() => expect(result.current.loadStatus).toBe("ready" satisfies LoadStatus));
    expect(result.current.error).toBe("Server down");
  });

  it("exposes view and setView from the wings", async () => {
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    // HS-169-03 SELECTOR EDIT: wings changed from timeline/decisions/search/ask to room/history
    expect(result.current.view).toBe("room");
    act(() => result.current.setView("history"));
    expect(result.current.view).toBe("history");
  });
});

describe("useProjectRoomController — /room first render (HS-158-05)", () => {
  it("first render uses one /room request, not the five-request fan-out", async () => {
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    await waitFor(() => expect(result.current.loadStatus).toBe("ready"));

    // The FIRST call must be to /room
    const firstUrl = apiFetchMock.mock.calls[0][0] as string;
    expect(firstUrl).toContain("/room");

    // /room is called exactly once
    const roomCalls = apiFetchMock.mock.calls.filter(
      (c: unknown[]) => (c[0] as string).includes("/room"),
    );
    expect(roomCalls).toHaveLength(1);
  });

  it("populates room snapshot from /room response", async () => {
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    await waitFor(() => expect(result.current.loadStatus).toBe("ready"));
    expect(result.current.room).not.toBeNull();
    expect(result.current.room?.projectId).toBe("p1");
    expect(result.current.room?.project.name).toBe("Test project");
    expect(result.current.room?.project.lifecycle).toBe("active");
  });

  it("progressive detail fetches follow /room (meetings/decisions/artifacts/since)", async () => {
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    await waitFor(() => expect(result.current.detailStatus).toBe("ready"));

    // After everything completes: /room + 4 detail + 2 HS-172 calls = 7 total
    // HS-172-03/06: proposals (proposed) + suggested-sources
    expect(apiFetchMock).toHaveBeenCalledTimes(7);
    const urls = apiFetchMock.mock.calls.map((c: unknown[]) => c[0] as string);
    expect(urls).toContainEqual(expect.stringContaining("/room"));
    expect(urls).toContainEqual(expect.stringContaining("/meetings"));
    expect(urls).toContainEqual(expect.stringContaining("/decisions"));
    expect(urls).toContainEqual(expect.stringContaining("/artifacts"));
    expect(urls).toContainEqual(expect.stringContaining("/since-last-meeting"));
    expect(urls).toContainEqual(expect.stringContaining("/proposals"));
    expect(urls).toContainEqual(expect.stringContaining("/suggested-sources"));
  });

  it("initial paint is ready before detail fetches complete", async () => {
    // Make detail fetches slow
    let resolveDetails: (() => void) | undefined;
    const detailPromise = new Promise<void>((r) => { resolveDetails = r; });
    apiFetchMock.mockImplementation((url: string) => {
      if ((url as string).includes("/room")) return Promise.resolve(roomResponse());
      // Detail fetches hang until we release them
      return detailPromise.then(() => detailResponse(url));
    });

    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));

    // loadStatus should become ready after /room alone
    await waitFor(() => expect(result.current.loadStatus).toBe("ready"));
    expect(result.current.room).not.toBeNull();
    expect(result.current.projectName).toBe("Test project");

    // Detail is still loading
    expect(result.current.detailStatus).toBe("loading");
    expect(result.current.timeline).toHaveLength(0);

    // Now release the detail fetches
    resolveDetails!();
    await waitFor(() => expect(result.current.detailStatus).toBe("ready"));
    expect(result.current.timeline.length).toBeGreaterThan(0);
  });

  it("detail failure does not blank the room face (WEB-STA-002)", async () => {
    apiFetchMock.mockImplementation((url: string) => {
      if ((url as string).includes("/room")) return Promise.resolve(roomResponse());
      return Promise.reject(new Error("Detail failed"));
    });

    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));

    // Room loads ok
    await waitFor(() => expect(result.current.loadStatus).toBe("ready"));
    expect(result.current.room).not.toBeNull();
    expect(result.current.projectName).toBe("Test project");

    // Detail failed but room data intact
    await waitFor(() => expect(result.current.detailStatus).toBe("ready"));
    expect(result.current.error).toBe("Detail failed");
    expect(result.current.room?.project.name).toBe("Test project");
  });

  it("computes timeline from detail data after progressive load", async () => {
    const { result } = renderHook(() => useProjectRoomController("project:p1", "Test"));
    await waitFor(() => expect(result.current.detailStatus).toBe("ready"));
    const kinds = result.current.timeline.map((e) => e.kind);
    expect(kinds).toContain("meeting");
    expect(kinds).toContain("decision");
  });
});

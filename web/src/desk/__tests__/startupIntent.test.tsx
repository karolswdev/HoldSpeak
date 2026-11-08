// HS-S12 (D12 / G-OPEN, ruled 2026-11-07): the desk keeps ONE startup
// intent, the latest explicit one, not a queue replayed in registration
// order. The surface host's one flush decides what opens first; a proposal
// target reveals exactly that proposal; recovery keeps the normal arrival.
import { act, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  __resetSurfaces,
  flushStartupIntent,
  openSurface,
  openSurfaceWhenReady,
  pendingStartupIntent,
  registerSurface,
  stageSurfaceOpen,
} from "../shell";
import { SurfaceWindows } from "../components/SurfaceWindows";
import {
  openProjectProposal,
  openProjectRoomAt,
  requestRoomAt,
  takeRoomAtRequest,
  takeRoomProposalRequest,
} from "../openObject";
import { useDesk } from "../store";

const ROOM = "surface-project-memory";
const MEETINGS = "surface-meetings";

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  useDesk.setState({
    windowsById: {},
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelDepth: {},
    panelMin: [],
    panelMax: [],
    zoneWindows: [],
    zoneViewPrefs: {},
  });
  __resetSurfaces();
  for (const id of ["p-a", "p-b", "p-w"]) {
    takeRoomAtRequest(id);
    takeRoomProposalRequest(id);
  }
});

afterEach(() => {
  vi.restoreAllMocks();
  __resetSurfaces();
});

/** Session storage refuses one call; local storage (the workspace) works. */
function refuseSession(method: "setItem" | "removeItem") {
  const real = Storage.prototype[method] as (...args: string[]) => void;
  vi.spyOn(Storage.prototype, method).mockImplementation(function (this: Storage, ...args: string[]) {
    if (this === sessionStorage) throw new Error("refused");
    return real.apply(this, args);
  } as never);
}

const registered = (container: HTMLElement) =>
  waitFor(() =>
    expect(container.querySelector("[data-surface-registry-state]"))
      .toHaveAttribute("data-surface-registry-state", "registered"));

describe("HS-S12: one explicit latest startup intent", () => {
  it("A then B for the same window before readiness: B is the scope the window opens on", async () => {
    // Red on main: the per-key queue drained backwards, so B opened first and
    // the older A was the final scope.
    openSurfaceWhenReady("open-project-memory", "project:p-a");
    openSurfaceWhenReady("open-project-memory", "project:p-b");
    const { container } = render(<SurfaceWindows />);
    await registered(container);
    expect(useDesk.getState().windowsById[ROOM]?.scope).toBe("project:p-b");
    expect(pendingStartupIntent()).toBeNull();
  });

  it("A then B for different windows before readiness: only the latest opens", async () => {
    openSurfaceWhenReady("review-meetings");
    openSurfaceWhenReady("open-project-memory", "project:p-a");
    const { container } = render(<SurfaceWindows />);
    await registered(container);
    expect(Object.keys(useDesk.getState().windowsById)).toEqual([ROOM]);
  });

  it("cold entry: a request after the staged route arrival is the intent that opens", async () => {
    stageSurfaceOpen("review-meetings");
    openSurfaceWhenReady("open-project-memory", "project:p-a");
    const { container } = render(<SurfaceWindows />);
    await registered(container);
    expect(Object.keys(useDesk.getState().windowsById)).toEqual([ROOM]);
    // The stored arrival is spent with it: a remount opens nothing more.
    expect(sessionStorage.getItem("hs.desk.staged-surface-open")).toBeNull();
  });

  it("a press that already landed is the latest: the older waiting request never replays over it", async () => {
    const opened: Array<string | undefined> = [];
    const off = registerSurface("dictate", (scope) => opened.push(scope));
    openSurfaceWhenReady("review-meetings", "meeting:older");
    expect(openSurface("dictate", "note:n1")).toBe(true);
    expect(pendingStartupIntent()).toBeNull();
    off();
    const { container } = render(<SurfaceWindows />);
    await registered(container);
    expect(useDesk.getState().windowsById[MEETINGS]).toBeUndefined();
    expect(opened).toEqual(["note:n1"]);
  });

  it("the restored window set opens as it was when no explicit intent exists", async () => {
    useDesk.getState().openSurfaceWindow("open-project-memory", "project:p-a");
    useDesk.getState().openSurfaceWindow("review-meetings");
    const before = useDesk.getState().windowsById;
    const { container } = render(<SurfaceWindows />);
    await registered(container);
    expect(useDesk.getState().windowsById).toEqual(before);
    expect(flushStartupIntent("normal")).toBe(false);
  });

  it("storage that refuses the stage keeps the same order: the newer in-memory arrival wins", async () => {
    sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({ key: "review-meetings" }));
    refuseSession("setItem");
    stageSurfaceOpen("open-project-memory", "project:p-b");
    const { container } = render(<SurfaceWindows />);
    await registered(container);
    expect(Object.keys(useDesk.getState().windowsById)).toEqual([ROOM]);
    expect(useDesk.getState().windowsById[ROOM]?.scope).toBe("project:p-b");
  });

  it("storage that cannot remove the arrival does not replay it on a host remount", async () => {
    stageSurfaceOpen("review-meetings");
    refuseSession("removeItem");
    const first = render(<SurfaceWindows />);
    await registered(first.container);
    expect(useDesk.getState().windowsById[MEETINGS]).toBeDefined();
    useDesk.getState().closeSurfaceWindow("review-meetings");
    first.unmount();
    const second = render(<SurfaceWindows />);
    await registered(second.container);
    expect(useDesk.getState().windowsById[MEETINGS]).toBeUndefined();
  });

  it("invalid stored JSON does not block startup", async () => {
    sessionStorage.setItem("hs.desk.staged-surface-open", "{not json");
    const { container } = render(<SurfaceWindows />);
    await registered(container);
    expect(useDesk.getState().windowsById).toEqual({});
  });

  it("recovery keeps the normal arrival through a pressed door; leaving recovery opens it", async () => {
    stageSurfaceOpen("review-meetings", "meeting:m-1");
    const recovery = render(<SurfaceWindows firstValueRecoveryOnly />);
    await waitFor(() =>
      expect(recovery.container.querySelector("[data-surface-registry-state]"))
        .toHaveAttribute("data-surface-registry-state", "recovery-only"));
    act(() => {
      expect(openSurface("configure-setup")).toBe(true);
    });
    expect(useDesk.getState().windowsById[MEETINGS]).toBeUndefined();
    expect(pendingStartupIntent()).toMatchObject({ key: "review-meetings", staged: true });
    recovery.unmount();
    const desk = render(<SurfaceWindows />);
    await registered(desk.container);
    expect(useDesk.getState().windowsById[MEETINGS]?.scope).toBe("meeting:m-1");
  });

  it("recovery admits a request for its own door and leaves others waiting", async () => {
    openSurfaceWhenReady("configure-runs-on", "models");
    const recovery = render(<SurfaceWindows firstValueRecoveryOnly />);
    await waitFor(() =>
      expect(useDesk.getState().windowsById["surface-engines"]?.scope).toBe("models"));
    recovery.unmount();
    openSurfaceWhenReady("review-meetings");
    const again = render(<SurfaceWindows firstValueRecoveryOnly />);
    await waitFor(() =>
      expect(again.container.querySelector("[data-surface-registry-state]"))
        .toHaveAttribute("data-surface-registry-state", "recovery-only"));
    expect(useDesk.getState().windowsById[MEETINGS]).toBeUndefined();
    expect(pendingStartupIntent()).toMatchObject({ key: "review-meetings" });
  });
});

describe("HS-S12: a proposal target reveals exactly that proposal", () => {
  it("cold entry with a proposal target opens the Room on that project and reveals it once", async () => {
    openProjectProposal("p-a", "prop-7");
    const { container } = render(<SurfaceWindows />);
    await registered(container);
    expect(useDesk.getState().windowsById[ROOM]?.scope).toBe("project:p-a");
    expect(takeRoomProposalRequest("p-a")).toBe("prop-7");
    expect(takeRoomProposalRequest("p-a")).toBeNull();
  });

  it("a repeat target is the same reveal in the same window, never a second window", async () => {
    const { container } = render(<SurfaceWindows />);
    await registered(container);
    const reveals: string[] = [];
    const take = () => {
      const proposal = takeRoomProposalRequest("p-a");
      if (proposal) reveals.push(proposal);
    };
    window.addEventListener("holdspeak:room-proposal", take);
    try {
      openProjectProposal("p-a", "prop-7");
      openProjectProposal("p-a", "prop-7");
    } finally {
      window.removeEventListener("holdspeak:room-proposal", take);
    }
    expect(reveals).toEqual(["prop-7", "prop-7"]);
    expect(Object.keys(useDesk.getState().windowsById)).toEqual([ROOM]);
    expect(useDesk.getState().windowsById[ROOM]?.scope).toBe("project:p-a");
  });

  it("the latest Room target wins: a proposal after Room-at is the one the Room applies", () => {
    // Red on main: two request maps, so a late-mounting Room applied the
    // stale History place and the proposal.
    openProjectRoomAt("p-a", "history");
    openProjectProposal("p-a", "prop-7");
    expect(takeRoomAtRequest("p-a")).toBeNull();
    expect(takeRoomProposalRequest("p-a")).toBe("prop-7");
    openProjectProposal("p-b", "prop-8");
    requestRoomAt("p-b", "steward");
    expect(takeRoomProposalRequest("p-b")).toBeNull();
    expect(takeRoomAtRequest("p-b")).toBe("steward");
  });

  it("a ?walk= link keeps the walk's intent first: an older target for the same Room does not apply", async () => {
    const { container } = render(<SurfaceWindows />);
    await registered(container);
    // Needs you asked for a proposal before the Room mounted; the walk then
    // opens the same Room on the Room itself.
    openProjectProposal("p-w", "prop-old");
    const { openWalkApp } = await import("../walk/walk");
    expect(await openWalkApp("open-project-memory", "project:p-w")).toBe(true);
    expect(takeRoomProposalRequest("p-w")).toBeNull();
    expect(takeRoomAtRequest("p-w")).toBe("room");
    expect(useDesk.getState().windowsById[ROOM]?.scope).toBe("project:p-w");
  });
});

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createRecordingSlice } from "../../store/recordingSlice";
import type { DeskState } from "../../store/types";

const mocks = vi.hoisted(() => {
  type RuntimeListener = (frame: { type: string; data: unknown }) => void;
  const runtimeListeners = new Map<string, Set<RuntimeListener>>();
  const durable = { readyRows: [] as Record<string, unknown>[] };
  const people = {
    readiness: { readiness: "ready" as string },
    readinessError: null as Error | null,
  };
  const subscribe = (type: string, listener: RuntimeListener) => {
    const listeners = runtimeListeners.get(type) ?? new Set<RuntimeListener>();
    listeners.add(listener);
    runtimeListeners.set(type, listeners);
    // The live bus normally delivers a first invalidation soon after mount.
    // Give this isolated fixture the same read kick while retaining the
    // listener map used by the frame assertions below.
    queueMicrotask(() => listener({ type: "dock_test_mount", data: {} }));
    return () => listeners.delete(listener);
  };
  const emitRuntime = (type: string, data: unknown = {}) => {
    for (const listener of runtimeListeners.get(type) ?? []) listener({ type, data });
  };
  const desk = {
    panelMin: [] as string[],
    panelOrder: [] as string[],
    windowsById: {},
    recording: "idle",
    recordingStartedAt: null as number | null,
    projects: [
      { id: "p1", name: "Alpha", is_archived: false },
      { id: "p0", name: "Quiet", is_archived: false },
    ],
    // These are the client-side Meeting rows produced from the real list wire.
    // They are historical summaries, not producer-created unread readiness.
    items: { meeting: [
      { id: "historical-1", title: "Yesterday's review", hasSummary: true, intelStatus: "ready" },
      { id: "historical-2", title: "Last week's review", hasSummary: true, intelStatus: "complete" },
    ] },
  };
  const shortcut = { open: false, setOpen: vi.fn() };
  const settle = { settled: false };
  const runtime = { state: "connected", subscribe };
  const focusPanel = vi.fn((id: string) => {
    desk.panelOrder = [...desk.panelOrder.filter((entry) => entry !== id), id];
  });
  const restorePanel = vi.fn((id: string) => {
    desk.panelMin = desk.panelMin.filter((entry) => entry !== id);
    focusPanel(id);
  });
  const useDesk = (selector: (state: typeof desk) => unknown) => selector(desk);
  useDesk.getState = () => ({
    ...desk,
    restorePanel,
    focusPanel,
    closeSurfaceWindow: vi.fn(),
    resetLayout: vi.fn(),
  });
  const defaultApiFetch = async (path: string): Promise<unknown> => {
      if (path === "/api/meetings/ready") return { meetings: durable.readyRows };
      if (path === "/api/people/readiness") {
        if (people.readinessError) throw people.readinessError;
        return people.readiness;
      }
      if (path === "/api/people/relationships") return { relationships: [{ id: "r1" }] };
      return { brief: { next_one_on_one: "2026-10-03T15:00:00Z" } };
  };
  return {
    apiFetch: vi.fn(defaultApiFetch),
    defaultApiFetch,
    apiRequest: vi.fn(),
    refreshNeedsYou: vi.fn(async () => {}),
    useNeedsYou: vi.fn(() => ({
      count: 1,
      unmutedItems: [{ projectId: "p1" }],
    })),
    useDesk,
    desk,
    shortcut,
    settle,
    runtime,
    runtimeListeners,
    emitRuntime,
    durable,
    people,
    compact: false,
    front: null as string | null,
    windows: [] as Array<{ id: string; label: string; glyph: string; close: () => void; dock: boolean }>,
    openIntelligence: vi.fn(),
  };
});

vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  apiRequest: mocks.apiRequest,
}));
vi.mock("../../needsYou", async (original) => ({
  // The Dock suite owns its store mock. Importing the real project helper
  // also imports arming, which expects the Zustand subscribe surface that
  // this focused fixture intentionally does not provide.
  projectOpenHere: () => false,
  refreshNeedsYou: mocks.refreshNeedsYou,
  useNeedsYou: mocks.useNeedsYou,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({ useOptionalRuntimeBus: () => mocks.runtime }));
vi.mock("../../../components/signal/Signal", () => ({
  Button: ({ children, ...props }: { children: ReactNode; [key: string]: unknown }) => (
    <button {...props}>{children}</button>
  ),
}));
vi.mock("../../intelligenceNavigation", () => ({ openIntelligence: mocks.openIntelligence }));
vi.mock("../../systemSprites", () => ({ DOCK_SPRITES: {}, SYSTEM: { floorGrid: "floor.svg" } }));
vi.mock("../../store", () => ({ useDesk: mocks.useDesk }));
vi.mock("../../settleState", () => ({
  useSettleState: (selector: (state: typeof mocks.settle) => unknown) => selector(mocks.settle),
}));
vi.mock("../../chromeState", () => ({
  useShortcutSheet: Object.assign(
    (selector: (state: typeof mocks.shortcut) => unknown) => selector(mocks.shortcut),
    { getState: () => mocks.shortcut },
  ),
}));
vi.mock("../../keymap", () => ({ useKeymap: vi.fn() }));
vi.mock("../DeskMenu", () => ({ WorkMenu: () => null }));
vi.mock("../../windowMenuAdapter", () => ({ dockChipMenuEntries: () => [] }));
vi.mock("./windowRegistry", () => ({
  useOpenWindows: () => mocks.windows,
  useFrontWindowId: () => mocks.front,
  useShownName: (_id: string, label: string) => label,
  registrySnapshot: [],
  chipEls: { set: vi.fn(), delete: vi.fn() },
}));
vi.mock("../../useCompactViewport", () => ({
  COMPACT_VIEWPORT_QUERY: "(max-width: 720px)",
  useCompactViewport: () => mocks.compact,
}));
vi.mock("../../screen/nextOneOnOne", () => ({
  useNextOneOnOneRead: () => ({ label: "1:1 15:00", reading: false }),
}));
// Keep the real Chair lifecycle below; the Dock does not mount its body.
vi.mock("../../needs/NeedsDrawer", () => ({ NeedsDrawer: () => null }));
const dockLaunchers = vi.hoisted(() => ({ list: [] as Array<{ id: string; label: string; glyph: string; open: boolean; activate: () => void }> }));
vi.mock("./launcherRegistry", () => ({ useLaunchers: () => dockLaunchers.list }));
vi.mock("./Expose", () => ({ toggleExpose: vi.fn() }));
vi.mock("./VerbGlyph", () => ({ VerbGlyph: () => null }));
vi.mock("./ShortcutSheet", () => ({ ShortcutSheet: () => null }));
vi.mock("../../applications", async (original) => {
  const applications = [
    { windowId: "intelligence:desk", action: "open-intelligence", href: "/intelligence", label: "Today", glyph: "I", surface: false, dock: { order: 0, launch: "intelligence", phone: 0 } },
    { windowId: "surface-meetings", action: "open-meetings", href: "/meetings", label: "Meetings", glyph: "M", surface: true, dock: { order: 1, launch: "surface", phone: 2 } },
    { windowId: "surface-people", action: "open-people", href: "/people", label: "People", glyph: "P", surface: true, dock: { order: 2, launch: "surface", phone: 3 } },
    { windowId: "conductor", action: "open-conductor", href: "/conductor", label: "Agents", glyph: "A", surface: true, dock: { order: 3, launch: "surface", phone: 4 } },
    { windowId: "surface-dictation", action: "dictate", href: "/dictation", label: "Speak", glyph: "S", surface: true, dock: { order: 4, launch: "surface" } },
  ];
  const phoneApplications = [
    applications[0],
    { windowId: "chair:capture", action: "chair-capture", href: "/", label: "Capture", glyph: "●", phoneOnly: true, dock: { order: 5, launch: "chair", phone: 1 } },
    applications[1],
    applications[2],
    applications[3],
  ];
  return {
    ...(await original<typeof import("../../applications")>()),
    DOCK_APPLICATIONS: applications,
    PHONE_DOCK_APPLICATIONS: phoneApplications,
  };
});
vi.mock("./RoomActions", () => ({ RoomActions: () => null }));

import { Dock } from "./Dock";
import { __resetSurfaces, registerSurface } from "../../shell";
import { useChairWindows } from "../../chair/chairWindows";
import { chipEls } from "./windowRegistry";

afterEach(() => {
  mocks.compact = false;
  mocks.front = null;
  mocks.desk.panelMin = [];
  mocks.desk.panelOrder = [];
  mocks.desk.windowsById = {};
  mocks.windows = [];
  mocks.openIntelligence.mockReset();
  vi.unstubAllGlobals();
});

describe("phone Today Dock door", () => {
  it.each([false, true])("keeps Brief selected when an existing Today is behind or minimized=%s", (minimized) => {
    mocks.compact = true;
    const winId = "pullout:intelligence:desk";
    mocks.windows = [{ id: winId, label: "Today", glyph: "I", close: vi.fn(), dock: true }];
    mocks.desk.panelOrder = [winId, "surface-meetings"];
    mocks.desk.panelMin = minimized ? [winId] : [];
    let selectedView = "brief";
    mocks.openIntelligence.mockImplementation(({ view }: { view: string }) => { selectedView = view; });
    const view = render(<Dock />);
    const today = screen.getByRole("button", { name: minimized ? /Today, .*iconified/ : /Today/ });
    expect(today).toHaveAttribute("data-app", "intelligence:desk");
    expect(chipEls.set).toHaveBeenCalledWith(winId, today);
    expect(today).toHaveClass(minimized ? "is-seated" : "is-run");

    fireEvent.click(today);
    view.rerender(<Dock />);

    expect(mocks.desk.panelOrder.at(-1)).toBe(winId);
    expect(mocks.desk.panelMin).not.toContain(winId);
    expect(screen.getByRole("button", { name: /Today/ })).toHaveClass("is-run");
    expect(selectedView).toBe("brief");
    expect(mocks.openIntelligence).not.toHaveBeenCalled();
  });

  it("launches the day view when Today is closed", () => {
    mocks.compact = true;
    render(<Dock />);

    fireEvent.click(screen.getByRole("button", { name: /Today/ }));

    expect(mocks.openIntelligence).toHaveBeenCalledTimes(1);
    expect(mocks.openIntelligence).toHaveBeenCalledWith({ view: "today" });
  });
});

describe("phone Capture Dock door", () => {
  it.each([false, true])("returns an already open Capture to the phone when minimized=%s", (minimized) => {
    mocks.compact = true;
    vi.stubGlobal("matchMedia", () => ({ matches: true }));
    mocks.desk.panelOrder = ["chair:capture", "chair:needs"];
    mocks.desk.panelMin = minimized ? ["chair:capture"] : [];
    useChairWindows.setState({
      closed: { "chair:capture": false, "chair:needs": false },
      phone: "chair:needs", captureInRing: true,
    });
    function PhoneDock() {
      const phone = useChairWindows((state) => state.phone);
      return <><Dock /><output data-testid="phone-pane">{phone}</output></>;
    }
    render(<PhoneDock />);
    expect(screen.getByTestId("phone-pane")).toHaveTextContent("chair:needs");

    fireEvent.click(screen.getByRole("button", { name: minimized ? "Capture, iconified" : "Capture" }));

    expect(screen.getByTestId("phone-pane")).toHaveTextContent("chair:capture");
    expect(useChairWindows.getState().closed["chair:capture"]).toBe(false);
    expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
    expect(mocks.desk.panelMin).not.toContain("chair:capture");
    expect(mocks.desk.panelOrder.at(-1)).toBe("chair:capture");
  });
});

function makeRecordingProducer() {
  const state: Record<string, unknown> = {
    items: { meeting: [] },
    refresh: vi.fn().mockResolvedValue(undefined),
  };
  const set = (partial: Partial<DeskState> | ((s: DeskState) => Partial<DeskState>)) => {
    Object.assign(
      state,
      typeof partial === "function"
        ? partial(state as unknown as DeskState)
        : partial,
    );
  };
  const get = () => state as unknown as DeskState;
  Object.assign(
    state,
    createRecordingSlice(set, get, { setState: set, getState: get } as never),
  );
  return state as unknown as ReturnType<typeof createRecordingSlice>;
}

function mirrorRecording(producer: ReturnType<typeof makeRecordingProducer>) {
  mocks.desk.recording = producer.recording;
  mocks.desk.recordingStartedAt = producer.recordingStartedAt;
}

describe("H-C3 Dock rendering", () => {
  beforeEach(() => {
    mocks.apiFetch.mockReset();
    mocks.apiFetch.mockImplementation(mocks.defaultApiFetch);
    mocks.apiRequest.mockReset();
    mocks.refreshNeedsYou.mockClear();
    mocks.runtimeListeners.clear();
    mocks.durable.readyRows.length = 0;
    mocks.people.readiness = { readiness: "ready" };
    mocks.people.readinessError = null;
    mocks.desk.recording = "idle";
    mocks.desk.recordingStartedAt = null;
    __resetSurfaces();
  });

  it("keeps live attention marks out of the application tiles (PHILO-17)", () => {
    render(<Dock />);

    // PHILO-17 (doors): projects left the Dock (desk drawers and Go ▸ Projects).
    expect(screen.queryByRole("button", { name: /^Alpha/ })).toBeNull();
    expect(screen.queryByRole("button", { name: "Quiet" })).toBeNull();
    expect(document.querySelector(".desk-dock-project")).toBeNull();
    // PHILO-17 (needsyou): the one number is on the Needs-you icon and the
    // bell only; the Intelligence tile carries no copy of it.
    expect(screen.getByRole("button", { name: /Today/ })).toBeTruthy();
    expect(screen.queryByText("0")).toBeNull();
    // PHILO-17: one desk. The dock has no Floor (or Chair) toggle.
    expect(screen.queryByTestId("chair-floor-toggle")).toBeNull();
    expect(screen.queryByRole("button", { name: "Floor" })).toBeNull();

    // Send and meeting-ready marks have one home in the system chrome. The
    // Dock keeps only its application seats and the confirmed REC mark.
    expect(screen.queryByTestId("desk-dock-send-state")).toBeNull();
    expect(screen.queryByTestId("desk-dock-meetings-state")).toBeNull();
    // PHILO-17 (doors): People left the Dock; its 1:1 read moved to the People drawer (screen/nextOneOnOne.ts).
    expect(screen.getByTestId("desk-dock-people-state")).toHaveTextContent("1:1 15:00");
    expect(mocks.apiFetch).not.toHaveBeenCalledWith("/api/people/readiness");
  });

  // Betterment send S1: nothing in the Dock draws a send, so it reads none.
  it("reads no sends on its refresh", async () => {
    render(<Dock />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/meetings/ready"));
    expect(mocks.apiFetch.mock.calls.some(([path]) => String(path).startsWith("/api/channels/sends"))).toBe(false);
  });

  // PHILO-15-09 (B11, Astra r2): the shared seed (an item with a folded
  // question, an unread source, an arming recording) reads one number.
  // PHILO-17 (needsyou): the Dock shows no copy of it on Intelligence.
  it("shows no copy of the Needs drawer's number on Intelligence for the one-number seed", async () => {
    const { ONE_NUMBER_SEED, ONE_NUMBER_ROWS } = await import("../../../test/oneNumberSeed");
    const real = await vi.importActual<typeof import("../../needsYou")>("../../needsYou");
    const snapshot = real.readNeedsYouAnswer(ONE_NUMBER_SEED as never);
    expect(snapshot.count).toBe(ONE_NUMBER_ROWS);
    mocks.useNeedsYou.mockImplementation((() => snapshot) as never);
    try {
      render(<Dock />);
      expect(screen.getByRole("button", { name: `Today, ${ONE_NUMBER_ROWS} needs you` })).toBeTruthy();
    } finally {
      mocks.useNeedsYou.mockImplementation((() => ({ count: 1, unmutedItems: [{ projectId: "p1" }] })) as never);
    }
  });

  it("shows REC only after the real recording producer receives hub confirmation", async () => {
    const producer = makeRecordingProducer();
    mocks.apiRequest.mockReturnValue(new Promise<Response>(() => {}));
    void producer.startRecording();
    await waitFor(() => expect(producer.recording).toBe("busy"));
    mirrorRecording(producer);

    const view = render(<Dock />);
    expect(screen.queryByTestId("desk-dock-meetings-state")).toBeNull();

    producer.applyRecordingActivity({ state: "meeting_live" });
    mirrorRecording(producer);
    view.rerender(<Dock />);

    expect(screen.getByTestId("desk-dock-meetings-state")).toHaveTextContent(/^REC/);
  });

  it("does not duplicate a ready meeting mark in the Dock", () => {
    render(<Dock />);

    // Historical summary rows and aftercare frames are handled by the one
    // attention bell. The Dock must not grow a second READY badge.
    expect(screen.queryByTestId("desk-dock-meetings-state")).toBeNull();
  });

  it("marks the Dock tile from the compositor front snapshot", () => {
    mocks.front = "surface-meetings";
    mocks.desk.windowsById = { "surface-meetings": {} };
    render(<Dock />);

    expect(screen.getByRole("button", { name: "Meetings" })).toHaveClass("is-front");
    expect(screen.getByRole("button", { name: "Today, 1 needs you" })).not.toHaveClass("is-front");
  });

  it("does not mark an open Dock tile when the live front is empty", () => {
    mocks.front = null;
    mocks.desk.panelOrder = ["surface-meetings"];
    mocks.desk.windowsById = { "surface-meetings": {} };
    mocks.windows = [{ id: "surface-meetings", label: "Meetings", glyph: "M", close: vi.fn(), dock: true }];
    render(<Dock />);

    expect(screen.getByRole("button", { name: "Meetings" })).not.toHaveClass("is-front");
  });
});

describe("C3-W the AppIcon face (boards C1-1, C1-8a-c)", () => {
  beforeEach(() => {
    mocks.apiFetch.mockReset();
    mocks.apiFetch.mockImplementation(mocks.defaultApiFetch);
    mocks.runtimeListeners.clear();
    mocks.durable.readyRows.length = 0;
    mocks.people.readiness = { readiness: "ready" };
    mocks.people.readinessError = null;
    mocks.runtime.state = "connected";
    mocks.apiRequest.mockReset();
    mocks.desk.recording = "idle";
    mocks.desk.recordingStartedAt = null;
    __resetSurfaces();
  });

  it("does not duplicate a sent mark in the Dock", () => {
    render(<Dock />);
    expect(screen.queryByTestId("desk-dock-send-state")).toBeNull();
  });

  it("does not duplicate a failed send mark in the Dock", () => {
    render(<Dock />);
    expect(screen.queryByTestId("desk-dock-send-state")).toBeNull();
  });

  it("names the five daily seats in the phone manifest and omits the old gadget", () => {
    mocks.compact = true;
    render(<Dock />);
    expect(screen.getByRole("button", { name: /Today/ })).toHaveAttribute("data-app", "intelligence:desk");
    expect(screen.getByRole("button", { name: "Capture" })).toHaveAttribute("data-app", "chair:capture");
    expect(screen.getByRole("button", { name: "Meetings" })).toHaveAttribute("data-app", "surface-meetings");
    expect(screen.getByRole("button", { name: /People/ })).toHaveAttribute("data-app", "surface-people");
    expect(screen.getByRole("button", { name: "Agents" })).toHaveAttribute("data-app", "conductor");
    expect(screen.queryByRole("button", { name: "Speak" })).toBeNull();
    expect(screen.queryByRole("button", { name: /More AppIcons/ })).toBeNull();
  });

  // replaces: tests/e2e/test_philo13_13_dock_glass.py::TestLiveDock::test_the_dock_shows_his_day_live_and_stays_through_an_outage (the REC leg)
  it("a refused start (the hub's 501) shows no REC; the start the hub confirms shows REC hh:mm in the rec tone", async () => {
    const producer = makeRecordingProducer();
    Object.assign(producer, { openPullout: vi.fn() });
    mocks.apiRequest.mockResolvedValueOnce(
      new Response(JSON.stringify({ success: false, error: "No microphone is available" }), { status: 501 }),
    );
    await producer.startRecording();
    mirrorRecording(producer);
    const view = render(<Dock />);
    expect(producer.recording).toBe("idle");
    expect(screen.queryByTestId("desk-dock-meetings-state")).toBeNull();

    mocks.apiRequest.mockResolvedValueOnce(new Response(JSON.stringify({
      success: true,
      meeting: { id: "c3w-live", title: "Live", started_at: new Date().toISOString() },
    }), { status: 200 }));
    await producer.startRecording();
    mirrorRecording(producer);
    view.rerender(<Dock />);
    const tag = screen.getByTestId("desk-dock-meetings-state");
    expect(tag.textContent).toMatch(/^REC \d\d:\d\d$/);
    expect(tag).toHaveAttribute("data-tone", "rec");
  });

  // replaces: tests/e2e/test_philo13_13_dock_glass.py::TestLiveDock::test_the_dock_shows_his_day_live_and_stays_through_an_outage (the OFFLINE leg)
  it("keeps send and ready marks absent while offline", () => {
    const view = render(<Dock />);
    mocks.runtime.state = "offline";
    view.rerender(<Dock />);
    for (const id of ["desk-dock-meetings-state", "desk-dock-send-state"])
      expect(screen.queryByTestId(id), id).toBeNull();
    expect(screen.getByTestId("desk-dock-today-count")).toHaveTextContent("1");
  });

  it("does not render a second status line for offline reads", () => {
    const view = render(<Dock />);
    mocks.runtime.state = "offline";
    view.rerender(<Dock />);
    expect(screen.queryByTestId("desk-dock-send-state")).toBeNull();
    expect(screen.getByTestId("desk-dock-today-count")).toHaveTextContent("1");
  });
});

describe("the Missed launcher (HS-200-07)", () => {
  beforeEach(() => {
    mocks.apiFetch.mockReset();
    mocks.apiFetch.mockImplementation(mocks.defaultApiFetch);
    __resetSurfaces();
  });

  it("does not duplicate the Missed launcher in the Dock", () => {
    // replaces: tests/e2e/test_hs200_coverage_glass.py::TestCoverageGlass::test_shade_coverage_1440 (the open-the-shade leg;
    // AttentionDrawer announces `activate: () => setShadeOpen(true)`, and
    // shadeCoverage.test.tsx draws the shade that activation opens)
    dockLaunchers.list = [{ id: "attention", label: "Missed", glyph: "◎", open: false, activate: vi.fn() }];
    try {
      render(<Dock />);
      expect(document.querySelector("[data-launcher='attention']")).toBeNull();
    } finally {
      dockLaunchers.list = [];
    }
  });
});

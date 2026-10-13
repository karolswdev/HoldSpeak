import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
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
    return () => listeners.delete(listener);
  };
  const emitRuntime = (type: string, data: unknown = {}) => {
    for (const listener of runtimeListeners.get(type) ?? []) listener({ type, data });
  };
  const desk = {
    panelMin: [],
    panelOrder: [],
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
  const useDesk = (selector: (state: typeof desk) => unknown) => selector(desk);
  useDesk.getState = () => ({
    ...desk,
    restorePanel: vi.fn(),
    focusPanel: vi.fn(),
    closeSurfaceWindow: vi.fn(),
    resetLayout: vi.fn(),
  });
  const defaultApiFetch = async (path: string): Promise<unknown> => {
      if (path === "/api/channels/sends") {
        return { sends: [{ state: "failed", dispatch_seq: 7 }] };
      }
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
  };
});

vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  apiRequest: mocks.apiRequest,
}));
vi.mock("../../needsYou", async (original) => ({
  // PHILO-14 A1 (#939): the Dock reads each Project's Room count through
  // the real `projectOpenHere`.
  projectOpenHere: (await original<typeof import("../../needsYou")>()).projectOpenHere,
  refreshNeedsYou: mocks.refreshNeedsYou,
  useNeedsYou: mocks.useNeedsYou,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({ useOptionalRuntimeBus: () => mocks.runtime }));
vi.mock("../../../components/signal/Signal", () => ({
  Button: ({ children, ...props }: { children: ReactNode; [key: string]: unknown }) => (
    <button {...props}>{children}</button>
  ),
}));
vi.mock("../../intelligenceNavigation", () => ({ openIntelligence: vi.fn() }));
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
  useOpenWindows: () => [],
  chipEls: { set: vi.fn(), delete: vi.fn() },
}));
const dockLaunchers = vi.hoisted(() => ({ list: [] as Array<{ id: string; label: string; glyph: string; open: boolean; activate: () => void }> }));
vi.mock("./launcherRegistry", () => ({ useLaunchers: () => dockLaunchers.list }));
vi.mock("./Expose", () => ({ toggleExpose: vi.fn() }));
vi.mock("./VerbGlyph", () => ({ VerbGlyph: () => null }));
vi.mock("./ShortcutSheet", () => ({ ShortcutSheet: () => null }));
vi.mock("../../applications", () => {
  const applications = [
    { windowId: "intelligence:desk", action: "open-intelligence", href: "/intelligence", label: "Intelligence", glyph: "I", surface: false, dock: { order: 1, launch: "intelligence" } },
    { windowId: "surface-meetings", action: "open-meetings", href: "/meetings", label: "Meetings", glyph: "M", surface: true, dock: { order: 2, launch: "surface" } },
  ];
  // PHILO-17 (doors): the Dock seats Intelligence, Speak and Meetings only.
  return { DOCK_APPLICATIONS: applications };
});
vi.mock("./RoomActions", () => ({ RoomActions: () => null }));

import { Dock } from "./Dock";
import { __resetSurfaces, registerSurface } from "../../shell";

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

  it("renders durable state marks and no needs-you badge on Intelligence (PHILO-17)", async () => {
    render(<Dock />);

    // PHILO-17 (doors): projects left the Dock (desk drawers and Go ▸ Projects).
    expect(screen.queryByRole("button", { name: /^Alpha/ })).toBeNull();
    expect(screen.queryByRole("button", { name: "Quiet" })).toBeNull();
    expect(document.querySelector(".desk-dock-project")).toBeNull();
    // PHILO-17 (needsyou): the one number is on the Needs-you icon and the
    // bell only; the Intelligence tile carries no copy of it.
    expect(screen.getByRole("button", { name: "Intelligence" })).toBeTruthy();
    expect(screen.queryByText("0")).toBeNull();
    // PHILO-17: one desk. The dock has no Floor (or Chair) toggle.
    expect(screen.queryByTestId("chair-floor-toggle")).toBeNull();
    expect(screen.queryByRole("button", { name: "Floor" })).toBeNull();

    await waitFor(() => expect(screen.getByTestId("desk-dock-send-state")).toHaveTextContent("SEND FAILED"));
    expect(screen.queryByTestId("desk-dock-meetings-state")).toBeNull();
    expect(mocks.refreshNeedsYou).toHaveBeenCalledWith(true);
    // PHILO-17 (doors): People left the Dock; its 1:1 read moved to the People drawer (screen/nextOneOnOne.ts).
    expect(screen.queryByTestId("desk-dock-people-state")).toBeNull();
    expect(mocks.apiFetch).not.toHaveBeenCalledWith("/api/people/readiness");
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
      expect(screen.getByRole("button", { name: "Intelligence" })).toBeTruthy();
      expect(screen.queryByRole("button", { name: `Intelligence, ${ONE_NUMBER_ROWS} need you` })).toBeNull();
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

  it("renders the durable readiness transition and reconciles an acknowledged stale frame", async () => {
    const view = render(<Dock />);

    // Historical summary rows do not create a READY mark. The endpoint below
    // is the durable read; this test does not claim that a producer emitted it.
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/meetings/ready"));
    expect(screen.queryByTestId("desk-dock-meetings-state")).toBeNull();
    expect(mocks.runtimeListeners.get("aftercare_ready")?.size).toBeGreaterThan(0);

    // Simulate the two observable halves of a producer completion: its frame
    // carries the same id as the mutable durable read.
    mocks.durable.readyRows.push({
      id: "meeting-new",
      title: "Newly summarized meeting",
      ready_at: "2026-10-03T12:00:00Z",
    });
    act(() => {
      mocks.emitRuntime("aftercare_ready", { meeting_id: "meeting-new" });
    });
    expect(await screen.findByTestId("desk-dock-meetings-state")).toHaveTextContent("READY 1");

    // Opening the record ACKs readiness. The hub's read frame must remove the
    // mark immediately, and a replayed completion frame must not leave it up.
    mocks.durable.readyRows.length = 0;
    act(() => {
      mocks.emitRuntime("desk_changed", { kind: "meeting_ready_read", id: "meeting-new" });
    });
    await waitFor(() => expect(screen.queryByTestId("desk-dock-meetings-state")).toBeNull());

    act(() => {
      mocks.emitRuntime("aftercare_ready", { meeting_id: "meeting-new" });
    });
    await waitFor(() => expect(screen.queryByTestId("desk-dock-meetings-state")).toBeNull(), {
      timeout: 1500,
    });

    // A remount reads the same durable empty snapshot; no frame-only state is
    // allowed to survive the face lifecycle.
    view.unmount();
    render(<Dock />);
    await waitFor(() => expect(screen.queryByTestId("desk-dock-meetings-state")).toBeNull());
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

  it("SENT carries its settle time and the ok tone", async () => {
    const at = new Date(2026, 9, 3, 14, 2).toISOString();
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/channels/sends") return { sends: [{ state: "sent", settled_at: at }] };
      return mocks.defaultApiFetch(path);
    });
    render(<Dock />);
    const tag = await screen.findByTestId("desk-dock-send-state");
    await waitFor(() => expect(tag).toHaveTextContent("SENT 14:02"));
    expect(tag).toHaveAttribute("data-tone", "ok");
  });

  it("SEND FAILED wears the fail tone and keeps its short form for the phone", async () => {
    render(<Dock />);
    const tag = await screen.findByTestId("desk-dock-send-state");
    await waitFor(() => expect(tag).toHaveTextContent("SEND FAILED"));
    expect(tag).toHaveAttribute("data-tone", "fail");
    // 1440 reads SEND FAILED; 393 reads the ratified short label FAILED.
    // Both are whole words (no zero-size text); the stylesheet shows one.
    expect(tag.querySelector(".desk-dock-state-wide")?.textContent).toBe("SEND FAILED");
    expect(tag.querySelector(".desk-dock-state-short")?.textContent).toBe("FAILED");
    expect(tag.querySelector(".desk-dock-state-long")).toBeNull();
    // The Intelligence AppIcon carries the full words as its description.
    const icon = screen.getByRole("button", { name: /^Intelligence/ });
    expect(icon).toHaveAccessibleDescription("Send failed");
  });

  it("names each daily seat for the phone order and carries the More AppIcons gadget", () => {
    render(<Dock />);
    expect(screen.getByRole("button", { name: /^Intelligence/ })).toHaveAttribute("data-app", "intelligence:desk");
    expect(screen.getByRole("button", { name: "Meetings" })).toHaveAttribute("data-app", "surface-meetings");
    expect(screen.getByRole("button", { name: "More AppIcons" })).toBeTruthy();
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
  it("offline: READY and REC leave with the hub; no tag and no count claims freshness", async () => {
    mocks.durable.readyRows.push({ id: "c3w-ready", title: "Ledger cutover sync", ready_at: "2026-10-03T12:00:00Z" });
    const view = render(<Dock />);
    expect(await screen.findByTestId("desk-dock-meetings-state")).toHaveTextContent("READY 1");
    mocks.runtime.state = "offline";
    view.rerender(<Dock />);
    expect(await screen.findByTestId("desk-dock-offline")).toHaveTextContent(/^OFFLINE · AS OF \d\d:\d\d$/);
    for (const id of ["desk-dock-meetings-state", "desk-dock-send-state", "desk-dock-people-state"])
      expect(screen.queryByTestId(id), id).toBeNull();
    expect(document.querySelectorAll(".desk-dock .desk-dock-badge")).toHaveLength(0);
  });

  it("offline: one OFFLINE · AS OF status heads the shelf; no tag, no count", async () => {
    const view = render(<Dock />);
    await waitFor(() => expect(screen.getByTestId("desk-dock-send-state")).toBeTruthy());
    mocks.runtime.state = "offline";
    view.rerender(<Dock />);
    const offline = await screen.findByRole("status");
    expect(offline).toHaveTextContent(/^OFFLINE · AS OF \d\d:\d\d$/);
    expect(offline.parentElement?.firstElementChild).toBe(offline);
    expect(screen.queryByTestId("desk-dock-send-state")).toBeNull();
    expect(screen.queryByText("1")).toBeNull();
  });
});

describe("the Missed launcher (HS-200-07)", () => {
  beforeEach(() => {
    mocks.apiFetch.mockReset();
    mocks.apiFetch.mockImplementation(mocks.defaultApiFetch);
    __resetSurfaces();
  });

  it("a press on [data-launcher=attention] runs the launcher the shade announced", () => {
    // replaces: tests/e2e/test_hs200_coverage_glass.py::TestCoverageGlass::test_shade_coverage_1440 (the open-the-shade leg;
    // AttentionDrawer announces `activate: () => setShadeOpen(true)`, and
    // shadeCoverage.test.tsx draws the shade that activation opens)
    const activate = vi.fn();
    dockLaunchers.list = [{ id: "attention", label: "Missed", glyph: "◎", open: false, activate }];
    try {
      render(<Dock />);
      const launcher = document.querySelector<HTMLElement>("[data-launcher='attention']");
      expect(launcher?.textContent).toContain("Missed");
      fireEvent.click(launcher!);
      expect(activate).toHaveBeenCalledTimes(1);
    } finally {
      dockLaunchers.list = [];
    }
  });
});

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createRecordingSlice } from "../../store/recordingSlice";
import type { DeskState } from "../../store/types";

const mocks = vi.hoisted(() => {
  const desk = {
    panelMin: [],
    panelOrder: [],
    windowsById: {},
    recording: "idle",
    recordingStartedAt: null,
    projects: [
      { id: "p1", name: "Alpha", is_archived: false },
      { id: "p0", name: "Quiet", is_archived: false },
    ],
    items: { meeting: [{ id: "meeting-1", hasSummary: true, intelStatus: "ready" }] },
  };
  const shortcut = { open: false, setOpen: vi.fn() };
  const settle = { settled: false };
  const runtime = { state: "connected", subscribe: () => () => {} };
  const useDesk = (selector: (state: typeof desk) => unknown) => selector(desk);
  useDesk.getState = () => ({
    ...desk,
    restorePanel: vi.fn(),
    focusPanel: vi.fn(),
    closeSurfaceWindow: vi.fn(),
    resetLayout: vi.fn(),
  });
  return {
    apiFetch: vi.fn(async (path: string): Promise<unknown> => {
      if (path === "/api/channels/sends") {
        return { sends: [{ state: "failed", dispatch_seq: 7 }] };
      }
      if (path === "/api/people/relationships") return { relationships: [{ id: "r1" }] };
      return { brief: { next_one_on_one: "2026-10-03T15:00:00Z" } };
    }),
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
  };
});

vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  apiRequest: mocks.apiRequest,
}));
vi.mock("../../needsYou", () => ({
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
vi.mock("../../chairState", () => ({
  useChairState: (selector: (state: { surface: string; toggle: () => void }) => unknown) =>
    selector({ surface: "chair", toggle: vi.fn() }),
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
vi.mock("./launcherRegistry", () => ({ useLaunchers: () => [] }));
vi.mock("./Expose", () => ({ toggleExpose: vi.fn() }));
vi.mock("./VerbGlyph", () => ({ VerbGlyph: () => null }));
vi.mock("./ShortcutSheet", () => ({ ShortcutSheet: () => null }));
vi.mock("../../applications", () => {
  const applications = [
    { windowId: "intelligence:desk", action: "open-intelligence", href: "/intelligence", label: "Intelligence", glyph: "I", surface: false, dock: { order: 1, launch: "intelligence" } },
    { windowId: "surface-meetings", action: "open-meetings", href: "/meetings", label: "Meetings", glyph: "M", surface: true, dock: { order: 2, launch: "surface" } },
    { windowId: "surface-agents", action: "open-agents", href: "/agents", label: "Agents", glyph: "A", surface: true, dock: { order: 3, launch: "surface" } },
    { windowId: "surface-settings", action: "open-settings", href: "/settings", label: "Settings", glyph: "S", surface: true, dock: { order: 4, launch: "surface" } },
  ];
  return {
    DOCK_APPLICATIONS: applications,
    applicationForAction: (action: string) => action === "open-people"
      ? { windowId: "surface-people", action, href: "/people", label: "People", glyph: "P", surface: true, dock: { order: 5, launch: "surface" } }
      : undefined,
  };
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
    mocks.apiFetch.mockClear();
    mocks.apiRequest.mockReset();
    mocks.refreshNeedsYou.mockClear();
    mocks.desk.recording = "idle";
    mocks.desk.recordingStartedAt = null;
    __resetSurfaces();
  });

  it("renders durable state marks and one membership badge while suppressing zero", async () => {
    render(<Dock />);

    expect(screen.getByRole("button", { name: "Alpha, 1 need you" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Quiet" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Intelligence, 1 need you" })).toBeTruthy();
    expect(screen.queryByText("0")).toBeNull();

    await waitFor(() => expect(screen.getByTestId("desk-dock-send-state")).toHaveTextContent("SEND FAILED"));
    expect(screen.getByTestId("desk-dock-meetings-state")).toHaveTextContent("READY 1");
    expect(screen.getByTestId("desk-dock-people-state")).toHaveTextContent("1:1");
    expect(mocks.refreshNeedsYou).toHaveBeenCalledWith(true);
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/people/relationships/r1/brief");
  });

  it("passes the explicit Dock origin when an active project opens", async () => {
    const opened = vi.fn();
    const off = registerSurface("open-project-memory", (_scope, options) => {
      opened(options?.origin);
    });
    render(<Dock />);

    fireEvent.click(screen.getByRole("button", { name: "Alpha, 1 need you" }));
    await waitFor(() => expect(opened).toHaveBeenCalledWith("dock"));
    off();
  });

  it("keeps a successful Send snapshot when the People projection fails", async () => {
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/channels/sends") {
        return { sends: [{ state: "sent", settled_at: "2026-10-03T12:00:00Z" }] };
      }
      throw new Error("people unavailable");
    });
    render(<Dock />);

    await waitFor(() => expect(screen.getByTestId("desk-dock-send-state")).toHaveTextContent("SENT"));
    expect(screen.queryByTestId("desk-dock-people-state")).toBeNull();
  });

  it("shows REC only after the real recording producer receives hub confirmation", async () => {
    const producer = makeRecordingProducer();
    mocks.apiRequest.mockReturnValue(new Promise<Response>(() => {}));
    void producer.startRecording();
    await waitFor(() => expect(producer.recording).toBe("busy"));
    mirrorRecording(producer);

    const view = render(<Dock />);
    expect(screen.getByTestId("desk-dock-meetings-state")).toHaveTextContent("READY 1");
    expect(screen.getByTestId("desk-dock-meetings-state")).not.toHaveTextContent("REC");

    producer.applyRecordingActivity({ state: "meeting_live" });
    mirrorRecording(producer);
    view.rerender(<Dock />);

    expect(screen.getByTestId("desk-dock-meetings-state")).toHaveTextContent(/^REC/);
  });
});

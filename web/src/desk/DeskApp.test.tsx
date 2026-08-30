import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import DeskApp from "./DeskApp";
import { stageFirstValueNoteOpen } from "./firstValue";

const state = vi.hoisted(() => ({
  setupResolved: true,
  setupAvailable: true,
  arrivalRequired: true,
  refreshFails: false,
  surface: "floor" as "chair" | "floor",
  askOpen: false,
  refresh: vi.fn(),
  openPullout: vi.fn(),
  pullouts: [] as Array<{ id: string; origin: { x: number; y: number } | null }>,
}));

const { marker } = vi.hoisted(() => ({
  marker: (name: string) => () => <div data-testid={name} />,
}));

vi.mock("./store", () => {
  const desk = {
    items: {},
    updatedAt: Date.now() as number | null,
    loading: false,
    chatPersonaId: null,
    roadmapWindows: [],
    repositoryWindows: [],
    workbenchWindows: [],
    setup: null as { arrival_required: boolean } | null,
    error: "",
    viewMode: "unset",
    editingId: null,
    askOpen: false,
    pullouts: [] as Array<{ id: string; origin: { x: number; y: number } | null }>,
  };
  state.refresh.mockImplementation(() =>
    state.refreshFails
      ? Promise.reject(new Error("Connection refused"))
      : Promise.resolve(undefined),
  );
  const useDesk = (selector: any) => {
    desk.updatedAt = state.setupResolved ? Date.now() : null;
    desk.loading = !state.setupResolved;
    desk.setup = state.setupAvailable
      ? { arrival_required: state.arrivalRequired }
      : null;
    desk.askOpen = state.askOpen;
    desk.pullouts = state.pullouts;
    return selector(desk);
  };
  useDesk.getState = () => ({ ...desk, refresh: state.refresh, openPullout: state.openPullout });
  return { useDesk, defaultViewFor: () => "spatial" };
});

vi.mock("./chairState", () => ({
  useChairState: (selector: any) => selector({ surface: state.surface }),
}));
vi.mock("./chair", () => ({
  ChairHome: ({ arrivalRequired }: { arrivalRequired?: boolean }) => (
    <div data-testid={arrivalRequired ? "first-value-chair" : "normal-chair"} />
  ),
}));
vi.mock("./gl/Atmosphere", () => ({ Atmosphere: marker("atmosphere") }));
vi.mock("./gl/WorldStage", () => ({ WorldStage: marker("world-stage") }));
vi.mock("./components/DeskListView", () => ({ DeskListView: marker("desk-list") }));
vi.mock("./components/DeskChrome", () => ({ DeskChrome: marker("desk-chrome") }));
vi.mock("./components/EmptyDesk", () => ({ EmptyDesk: marker("empty-desk") }));
vi.mock("./components/RecordOrb", () => ({ RecordOrb: marker("record-orb") }));
vi.mock("./hooks/useChatImport", () => ({ useChatImport: () => ({ receipt: "" }) }));
vi.mock("./components/MissionControlConveyor", () => ({ MissionControlConveyor: marker("mission-control") }));
vi.mock("./components/SessionPullout", () => ({
  SessionPullout: marker("session-pullout"),
  PanePicker: marker("pane-picker"),
}));
vi.mock("./components/DeliveryBoard", () => ({ DeliveryBoard: marker("delivery-board") }));
vi.mock("./components/DeliveryDossierWindow", () => ({ DeliveryDossierWindow: marker("delivery-dossier") }));
vi.mock("./components/DeliveryTerminalWindow", () => ({ DeliveryTerminalWindow: marker("delivery-terminal") }));
vi.mock("./components/RoadmapWindow", () => ({ RoadmapWindow: marker("roadmap-window") }));
vi.mock("./components/RepoWindow", () => ({ RepoWindow: marker("repo-window") }));
vi.mock("./components/WorkbenchWindow", () => ({ WorkbenchWindow: marker("workbench-window") }));
vi.mock("./components/NewWorkbenchChooser", () => ({ NewWorkbenchChooser: marker("workbench-chooser") }));
vi.mock("./components/ScheduleCreateWindow", () => ({ ScheduleCreateWindow: marker("schedule-create") }));
vi.mock("./components/AttentionDrawer", () => ({ AttentionDrawer: marker("attention-drawer") }));
vi.mock("./components/AskPanel", () => ({ AskPanel: marker("ask-panel") }));
vi.mock("./components/GlassDropLayer", () => ({ GlassDropLayer: marker("glass-drop") }));
vi.mock("./components/DeskToolInspector", () => ({ DeskToolInspector: marker("tool-inspector") }));
vi.mock("./components/DeskWindow", () => ({
  Dock: ({ center }: { center?: ReactNode }) => <div data-testid="dock">{center}</div>,
  Expose: marker("expose"),
  SnapGhost: marker("snap-ghost"),
  Switcher: marker("switcher"),
}));
vi.mock("./components/SurfaceWindows", () => ({
  SurfaceWindows: ({ firstValueRecoveryOnly }: { firstValueRecoveryOnly?: boolean }) => (
    <div
      data-testid="surface-windows"
      data-recovery-only={String(Boolean(firstValueRecoveryOnly))}
    />
  ),
}));
vi.mock("./components/TrustWindow", () => ({ TrustWindow: marker("trust-window") }));
vi.mock("./components/InlineEditor", () => ({ InlineEditor: marker("inline-editor") }));
vi.mock("./components/Pullout", () => ({
  Pullout: ({ o }: { o: { title: string } }) => <div data-testid="chair-pullout">{o.title}</div>,
}));
vi.mock("./world", () => ({
  objectByRef: (_items: unknown, id: string) =>
    id === "note:kept-first-sentence"
      ? { id, kind: "note", title: "First dictation", ref: { id, kind: "note" } }
      : null,
}));
vi.mock("./projections", () => ({
  useProjections: { getState: () => ({ refresh: vi.fn().mockResolvedValue(undefined) }) },
}));

describe("DeskApp arrival state", () => {
  afterEach(() => {
    state.setupResolved = true;
    state.setupAvailable = true;
    state.arrivalRequired = true;
    state.refreshFails = false;
    state.surface = "floor";
    state.askOpen = false;
    state.refresh.mockClear();
    state.openPullout.mockClear();
    state.pullouts = [];
    sessionStorage.clear();
    window.history.replaceState({}, "", "/");
  });

  it("makes first value the only Chair composition and suppresses Desk chrome", () => {
    render(<DeskApp />);

    expect(screen.getByTestId("first-value-chair")).toBeInTheDocument();
    expect(screen.getByTestId("surface-windows")).toBeInTheDocument();
    expect(screen.getByTestId("surface-windows")).toHaveAttribute(
      "data-recovery-only",
      "true",
    );
    expect(screen.queryByTestId("desk-chrome")).not.toBeInTheDocument();
    expect(screen.queryByTestId("world-stage")).not.toBeInTheDocument();
    expect(screen.queryByTestId("dock")).not.toBeInTheDocument();
    expect(screen.queryByTestId("record-orb")).not.toBeInTheDocument();
    expect(screen.queryByTestId("mission-control")).not.toBeInTheDocument();
    expect(screen.queryByTestId("pane-picker")).not.toBeInTheDocument();
  });

  it("keeps the initial unresolved setup state neutral until the server answers", () => {
    state.setupResolved = false;
    render(<DeskApp />);

    expect(screen.getByLabelText("Preparing HoldSpeak")).toBeInTheDocument();
    expect(screen.queryByTestId("first-value-chair")).not.toBeInTheDocument();
    expect(screen.queryByTestId("normal-chair")).not.toBeInTheDocument();
    expect(screen.queryByTestId("desk-chrome")).not.toBeInTheDocument();
    expect(screen.queryByTestId("dock")).not.toBeInTheDocument();
    expect(screen.queryByTestId("surface-windows")).not.toBeInTheDocument();
  });

  it("keeps a failed initial refresh quiet and gives the owner a retry", async () => {
    state.setupResolved = false;
    state.refreshFails = true;
    render(<DeskApp />);

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent("Your Desk is still unchanged. Connection refused Retry to check it again.");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.queryByTestId("desk-chrome")).not.toBeInTheDocument();
    expect(screen.queryByTestId("normal-chair")).not.toBeInTheDocument();
    expect(screen.queryByTestId("dock")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(state.refresh).toHaveBeenCalledTimes(2));
  });

  it("keeps a resolved but missing setup snapshot quiet and retryable", () => {
    state.setupAvailable = false;
    render(<DeskApp />);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Your Desk is still unchanged. HoldSpeak could not read setup status. Retry to check it again.",
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.queryByTestId("first-value-chair")).not.toBeInTheDocument();
    expect(screen.queryByTestId("normal-chair")).not.toBeInTheDocument();
    expect(screen.queryByTestId("desk-chrome")).not.toBeInTheDocument();
    expect(screen.queryByTestId("dock")).not.toBeInTheDocument();
  });

  it("keeps the normal Chair and chrome when the server no longer requires arrival", () => {
    state.arrivalRequired = false;
    state.surface = "chair";
    render(<DeskApp />);

    expect(screen.getByTestId("normal-chair")).toBeInTheDocument();
    expect(screen.getByTestId("desk-chrome")).toBeInTheDocument();
    expect(screen.getByTestId("dock")).toBeInTheDocument();
    expect(screen.getByTestId("mission-control")).toBeInTheDocument();
    expect(screen.getByTestId("pane-picker")).toBeInTheDocument();
  });

  it("mounts the existing Ask panel when the normal Chair opens it", () => {
    state.arrivalRequired = false;
    state.surface = "chair";
    state.askOpen = true;
    render(<DeskApp />);

    expect(screen.getByTestId("ask-panel")).toBeInTheDocument();
  });

  it("reveals one normal Chair and staged note once after the server flip while preserving a queued deep link", async () => {
    window.history.replaceState({}, "", "/?open=note:queued-deep-link");
    stageFirstValueNoteOpen("note:kept-first-sentence");
    const view = render(<DeskApp />);
    expect(state.openPullout).not.toHaveBeenCalled();

    state.arrivalRequired = false;
    state.surface = "chair";
    view.rerender(<DeskApp />);
    await waitFor(() =>
      expect(state.openPullout).toHaveBeenCalledWith("note:kept-first-sentence"),
    );
    await waitFor(() =>
      expect(state.openPullout).toHaveBeenCalledWith("note:queued-deep-link"),
    );
    view.rerender(<DeskApp />);
    expect(screen.getAllByTestId("normal-chair")).toHaveLength(1);
    expect(screen.getAllByTestId("desk-chrome")).toHaveLength(1);
    expect(screen.queryByTestId("first-value-chair")).not.toBeInTheDocument();
    expect(
      state.openPullout.mock.calls.filter(([ref]) => ref === "note:kept-first-sentence"),
    ).toHaveLength(1);
    expect(
      state.openPullout.mock.calls.filter(([ref]) => ref === "note:queued-deep-link"),
    ).toHaveLength(1);
    expect(new URLSearchParams(window.location.search).get("open")).toBe(
      "note:queued-deep-link",
    );
  });

  it("mounts staged pullouts on the normal Chair, never during arrival", () => {
    state.pullouts = [{ id: "note:kept-first-sentence", origin: null }];
    const arrival = render(<DeskApp />);
    expect(screen.queryByTestId("chair-pullout")).not.toBeInTheDocument();

    state.arrivalRequired = false;
    state.surface = "chair";
    arrival.rerender(<DeskApp />);
    expect(screen.getByTestId("chair-pullout")).toHaveTextContent("First dictation");
  });
});

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { lazy } from "react";
import { MemoryRouter } from "react-router-dom";
import { AmbientLayer } from "./AmbientLayer";
import { ChairHome } from "../desk/chair/ChairHome";
import {
  dismissAftercare,
  publishAftercare,
} from "../desk/intelligenceAttention";
import { useChairState } from "../desk/chairState";
import { EMPTY_ITEMS } from "../desk/api";
import { useDesk } from "../desk/store";
import {
  SurfaceWindowHost,
  type SurfaceRow,
} from "../desk/components/SurfaceWindows";
import { DeskListView } from "../desk/components/DeskListView";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
}));

vi.mock("../lib/api", async (original) => ({
  ...(await original<typeof import("../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));

vi.mock("../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
  useRuntimeFrame: () => null,
}));

vi.mock("../desk/thoughts", () => ({
  unfinishedThoughts: async () => ({ items: [] }),
}));

vi.mock("../desk/components/MicButton", () => ({ MicButton: () => null }));

vi.mock("../desk/projections", () => {
  const state = {
    ambient: [],
    subject_counts: {},
    refreshAmbient: vi.fn(),
    present: vi.fn(),
  };
  const useProjections = Object.assign(
    (selector: (value: typeof state) => unknown) => selector(state),
    { getState: () => state },
  );
  return { useProjections };
});

function publish(
  meetingId = "meeting-placement",
  title = "Architecture review",
) {
  act(() => {
    publishAftercare({
      meeting_id: meetingId,
      title,
      open_total: 3,
      decided_total: 0,
    });
  });
}

beforeEach(() => {
  mocks.apiFetch.mockImplementation(async (path: string) => {
    if (path === "/api/desk/needs-you")
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true };
    if (path === "/api/door")
      return { board: {}, upcoming: [], counts: {}, calendar_configured: false };
    if (path === "/api/inference/assignments")
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 };
    if (path === "/api/settings") return { presence: { enabled: false } };
    return null;
  });
  useChairState.setState({ surface: "chair" });
  useDesk.setState({
    items: EMPTY_ITEMS,
    divedZone: null,
    selectedIds: [],
    pullouts: [],
    editingId: null,
    askOpen: false,
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
  });
  act(() => dismissAftercare());
});

afterEach(() => {
  act(() => dismissAftercare());
  vi.restoreAllMocks();
  document.body.innerHTML = "";
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
});

describe("PHILO-6-03 aftercare rendered placement", () => {
  it.each([1440, 393])("publishes into the actual ChairHome slot and Dismiss clears it at %i", async (width) => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
    render(
      <>
        <AmbientLayer />
        <ChairHome />
      </>,
    );
    const slot = await screen.findByTestId("arrival-aftercare-slot");

    publish();

    await waitFor(() => expect(slot.querySelector("aside")).toBeTruthy());
    const card = slot.querySelector("aside")!;
    expect(card).toHaveTextContent("Meeting ready");
    expect(card).toHaveTextContent("Architecture review");
    expect(card).toHaveTextContent("3 open");
    expect(card).toHaveClass("ambient-aftercare-flow");
    expect(card).not.toHaveStyle({ bottom: "104px" });
    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
    await waitFor(() => expect(slot.querySelector("aside")).toBeNull());
    expect(screen.queryByRole("complementary", { name: "Meeting aftercare" })).toBeNull();
  });

  it("renders into the actual active SurfaceWindowHost slot", async () => {
    useChairState.setState({ surface: "chair" });
    const arrivalSlot = document.createElement("div");
    arrivalSlot.dataset.aftercareSlot = "before-capture";
    document.body.append(arrivalSlot);
    const row: SurfaceRow = {
      key: "test-aftercare-window",
      id: "test-aftercare-window",
      title: "Meetings",
      glyph: "M",
      eyebrow: "Test",
      Core: lazy(async () => ({ default: () => <p>Window body</p> })),
    };
    const { container } = render(
      <>
        <AmbientLayer />
        <SurfaceWindowHost row={row} scope={undefined} items={EMPTY_ITEMS} />
      </>,
    );
    publish();

    await waitFor(() =>
      expect(
        container.querySelector('[data-aftercare-window-slot="top"] aside'),
      ).toBeTruthy(),
    );
    const slot = container.querySelector('[data-aftercare-window-slot="top"]')!;
    expect(slot.querySelector("aside")).toHaveClass("ambient-aftercare-flow");
    expect(document.querySelector('[data-aftercare-floor-slot="top"]')).toBeNull();
  });

  it("renders into the actual Floor list host when no window is open", async () => {
    useChairState.setState({ surface: "floor" });
    const { container } = render(
      <MemoryRouter>
        <AmbientLayer />
        <DeskListView />
      </MemoryRouter>,
    );
    publish();

    await waitFor(() =>
      expect(
        container.querySelector('[data-aftercare-floor-slot="top"] aside'),
      ).toBeTruthy(),
    );
    const slot = container.querySelector('[data-aftercare-floor-slot="top"]')!;
    expect(slot.querySelector("aside")).toHaveClass("ambient-aftercare-flow");
    expect(slot.querySelector("aside")).not.toHaveStyle({ bottom: "104px" });
  });

  it("keeps the fixed fallback only when the spatial Floor has no slot", async () => {
    useChairState.setState({ surface: "floor" });
    render(<AmbientLayer />);
    publish();

    await waitFor(() =>
      expect(document.querySelector(".ambient-aftercare")).toBeTruthy(),
    );
    const card = document.querySelector(".ambient-aftercare")!;
    expect(card.closest("[data-aftercare-slot], [data-aftercare-window-slot], [data-aftercare-floor-slot]")).toBeNull();
    expect(card).toHaveTextContent("Architecture review");
    expect(document.querySelectorAll(".ambient-aftercare")).toHaveLength(1);
  });

  it("scrolls an obscured phone slot once and does not scroll a desktop slot", async () => {
    useChairState.setState({ surface: "chair" });
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 393,
    });
    const slot = document.createElement("div");
    slot.dataset.aftercareSlot = "before-capture";
    const capture = document.createElement("footer");
    capture.dataset.testid = "arrival-capture-bar";
    document.body.append(slot, capture);
    vi.spyOn(slot, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 600,
      top: 600,
      left: 0,
      right: 393,
      bottom: 780,
      width: 393,
      height: 180,
      toJSON: () => ({}),
    });
    vi.spyOn(capture, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 573,
      top: 573,
      left: 0,
      right: 393,
      bottom: 711,
      width: 393,
      height: 138,
      toJSON: () => ({}),
    });
    const scroll = vi.fn();
    slot.scrollIntoView = scroll;
    render(<AmbientLayer />);
    publish("meeting-placement-phone", "Architecture review phone");

    await waitFor(() => expect(scroll).toHaveBeenCalledTimes(1));
    expect(scroll).toHaveBeenCalledWith({ block: "nearest", behavior: "auto" });
    publish("meeting-placement-phone", "Architecture review phone");
    await waitFor(() => expect(scroll).toHaveBeenCalledTimes(1));

    act(() => dismissAftercare());
    publish("meeting-placement-phone", "Architecture review phone");
    await waitFor(() => expect(scroll).toHaveBeenCalledTimes(2));
    act(() => dismissAftercare());
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
    publish("meeting-placement-desktop", "Architecture review desktop");
    await waitFor(() => expect(document.querySelector(".ambient-aftercare")).toBeTruthy());
    expect(scroll).toHaveBeenCalledTimes(2);
  });

  it("scrolls an off-Arrival phone slot once even when it is already visible", async () => {
    useChairState.setState({ surface: "floor" });
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 393,
    });
    const { container } = render(
      <MemoryRouter>
        <AmbientLayer />
        <DeskListView />
      </MemoryRouter>,
    );
    const slot = await waitFor(() => {
      const found = container.querySelector<HTMLElement>(
        '[data-aftercare-floor-slot="top"]',
      );
      expect(found).toBeTruthy();
      return found!;
    });
    const scroll = vi.fn();
    slot.scrollIntoView = scroll;
    publish("meeting-placement-floor", "Architecture review floor");

    await waitFor(() => expect(scroll).toHaveBeenCalledTimes(1));
    expect(scroll).toHaveBeenCalledWith({ block: "nearest", behavior: "auto" });
    await waitFor(() => expect(scroll).toHaveBeenCalledTimes(1));
  });

  it("scrolls an active window phone slot once", async () => {
    useChairState.setState({ surface: "chair" });
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 393,
    });
    const arrivalSlot = document.createElement("div");
    arrivalSlot.dataset.aftercareSlot = "before-capture";
    document.body.append(arrivalSlot);
    const row: SurfaceRow = {
      key: "test-aftercare-phone-window",
      id: "test-aftercare-phone-window",
      title: "Meetings",
      glyph: "M",
      eyebrow: "Test",
      Core: lazy(async () => ({ default: () => <p>Window body</p> })),
    };
    const { container } = render(
      <>
        <AmbientLayer />
        <SurfaceWindowHost row={row} scope={undefined} items={EMPTY_ITEMS} />
      </>,
    );
    const slot = await waitFor(() => {
      const found = container.querySelector<HTMLElement>(
        '[data-aftercare-window-slot="top"]',
      );
      expect(found).toBeTruthy();
      return found!;
    });
    const scroll = vi.fn();
    slot.scrollIntoView = scroll;
    publish("meeting-placement-window", "Architecture review window");

    await waitFor(() => expect(scroll).toHaveBeenCalledTimes(1));
    expect(scroll).toHaveBeenCalledWith({ block: "nearest", behavior: "auto" });
    await waitFor(() => expect(scroll).toHaveBeenCalledTimes(1));
  });

  it("does not move the owner while a field has focus", async () => {
    useChairState.setState({ surface: "chair" });
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 393,
    });
    const slot = document.createElement("div");
    slot.dataset.aftercareSlot = "before-capture";
    const capture = document.createElement("footer");
    capture.dataset.testid = "arrival-capture-bar";
    document.body.append(slot, capture);
    vi.spyOn(slot, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 600,
      top: 600,
      left: 0,
      right: 393,
      bottom: 780,
      width: 393,
      height: 180,
      toJSON: () => ({}),
    });
    vi.spyOn(capture, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 573,
      top: 573,
      left: 0,
      right: 393,
      bottom: 711,
      width: 393,
      height: 138,
      toJSON: () => ({}),
    });
    const scroll = vi.fn();
    slot.scrollIntoView = scroll;
    const field = document.createElement("input");
    document.body.append(field);
    field.focus();
    render(<AmbientLayer />);
    publish();

    await waitFor(() => expect(slot.querySelector("aside")).toBeTruthy());
    expect(scroll).not.toHaveBeenCalled();
  });
});
